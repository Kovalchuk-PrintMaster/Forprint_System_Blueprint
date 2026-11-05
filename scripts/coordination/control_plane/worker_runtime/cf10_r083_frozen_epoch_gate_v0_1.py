"""CF-10 R083: fail-closed provider-freeze epoch check for canonical launch.

Neither the absence of both R082 markers nor a digest that an untrusted actor
recomputed can turn a post-R082 attempt into a historical Copilot attempt.
This is read-only provenance validation, NOT approval, claim, or execution.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import re
import subprocess

from scripts.coordination.control_plane.worker_runtime import cf10_r082_frozen_assignment_v0_1 as frozen

SCHEMA = 'cf10_r083_frozen_provider_epoch_gate_v0_1'
R082_BASE = '0282218d998b5d0687323016339081a68724b558'
HEX40 = re.compile(r'[a-f0-9]{40}\Z')


class EpochGateBlocked(ValueError):
    pass


def deny(code: str) -> None:
    raise EpochGateBlocked('CF10_R083_' + code)


def _git(root: Path, *args: str) -> int:
    try:
        process = subprocess.run(
            ['git', '-C', str(root), *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        deny('GIT_PROVENANCE_UNAVAILABLE')
    return process.returncode


def source_epoch(root: Path, source_head: str) -> str:
    """Classify the frozen git commit as before/after the R082 cutover.

    Divergent/unverifiable histories are not legacy and cannot be routed.
    """
    if not isinstance(source_head, str) or not HEX40.fullmatch(source_head):
        deny('SOURCE_HEAD_INVALID')
    if not isinstance(root, Path) or not root.is_dir() or root.is_symlink():
        deny('CANONICAL_REPOSITORY_INVALID')
    if _git(root, 'cat-file', '-e', R082_BASE + '^{commit}') != 0:
        deny('MIGRATION_BASE_NOT_IN_REPO')
    if _git(root, 'cat-file', '-e', source_head + '^{commit}') != 0:
        deny('SOURCE_COMMIT_NOT_IN_REPO')
    if _git(root, 'merge-base', '--is-ancestor', R082_BASE, source_head) == 0:
        return 'FROZEN_REQUIRED_AFTER_R082'
    if _git(root, 'merge-base', '--is-ancestor', source_head, R082_BASE) == 0:
        return 'LEGACY_ANCESTOR_BEFORE_R082'
    deny('DIVERGENT_SOURCE_CANNOT_CLAIM_LEGACY')


def assert_launch_epoch(
    *, root: Path, source_state: Mapping, prepared: Mapping,
    decision: Mapping, attempt_id: str, worker_id: str,
) -> dict:
    """Read-only check before owner claim and immediately before execution.

    For new source commits, both independent frozen markers are compulsory.
    The historic branch is for genuine Git ancestors ONLY and remains Copilot-only.
    This check does not bypass the canonical source-state, ACK, dispatch, root
    receipts, PAM, kernel witness, or independent finalizer gates.
    """
    if not all(isinstance(x, Mapping) for x in (source_state, prepared, decision)):
        deny('BOUND_DOCUMENT_MAPPING_REQUIRED')
    binding = decision.get('binding')
    if not isinstance(binding, Mapping):
        deny('EXPLICIT_DECISION_BINDING_MISSING')
    if (prepared.get('attempt_id') != attempt_id
        or prepared.get('worker_id') != worker_id
        or binding.get('attempt_id') != attempt_id
        or binding.get('worker_id') != worker_id):
        deny('ATTEMPT_WORKER_IDENTITY_DRIFT')
    head = source_state.get('git_head')
    fingerprint = source_state.get('fingerprint_sha256')
    if not isinstance(fingerprint, str) or not frozen.HEX64.fullmatch(fingerprint):
        deny('FROZEN_FINGERPRINT_MISSING')
    epoch = source_epoch(Path(root), head)
    has_frozen = frozen.KEY in prepared
    has_decision_sha = 'cf10_frozen_provider_assignment_sha256' in binding
    if epoch == 'FROZEN_REQUIRED_AFTER_R082':
        if not has_frozen or not has_decision_sha:
            deny('POST_R082_PROVIDER_FREEZE_DOWNGRADE_BLOCKED')
    else:
        if has_frozen or has_decision_sha:
            # A historic attempt must not be silently upgraded to the new
            # routing contract without a new exact source/attempt freeze.
            deny('HISTORICAL_ATTEMPT_MIXED_FROZEN_SCHEMA')
    report = frozen.verify_decision(
        root=Path(root), prepared=prepared, decision=decision,
        source_head=head, source_fingerprint=fingerprint,
        attempt_id=attempt_id, worker_id=worker_id,
    )
    if epoch == 'FROZEN_REQUIRED_AFTER_R082':
        if report.get('new_assignment_verified') is not True or report.get('legacy_copilot_only') is not False:
            deny('NEW_FROZEN_ASSIGNMENT_NOT_VERIFIED')
    elif report.get('legacy_copilot_only') is not True or report.get('new_assignment_verified') is not False:
        deny('LEGACY_PROVIDER_NOT_ALLOWED')
    return {
        'schema_version': SCHEMA,
        'source_epoch': epoch,
        'provider': binding.get('runtime_provider'),
        'frozen_verified': bool(report.get('new_assignment_verified')),
        'launch_authorized': False,
        'owner_claim_consumed': False,
        'worker_launched': False,
        'result_accepted': False,
        'automatic_fallback': False,
        'automatic_retry': False,
    }
