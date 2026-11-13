#!/usr/bin/env python3
"""R131: non-authorizing canonical terminal-review fence for CF10 IPC.

The source review checks R127/R129 candidate consistency. The optional root
readback uses the EXISTING R126 lease inspector and canonical systemd terminal
bridge/KernelWitness. It never manufactures a kernel witness, a ledger event,
a worker claim, root release, launch, or acceptance. A missing observation is
HOLD. No synthetic event may be promoted to runtime evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
)

SCHEMA = 'cf10_r131_terminal_review_fence_v0_1'
WORKER_ROOT = Path('/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01')
LEASE = re.compile(r'/run/forprint-cf10-r125-[a-f0-9]{16}/lease\.json\Z')
UNIT = re.compile(r'forprint-cf10-worker-[a-f0-9]{24}\.service\Z')
INVOKE = re.compile(r'[a-f0-9]{32}\Z')


class R131Hold(RuntimeError):
    pass


def deny(reason: str) -> None:
    raise R131Hold('CF10_R131_HOLD_' + reason)


def _digest(value: Mapping) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode('ascii')).hexdigest()


def review_source(*, candidate: Mapping, synthetic_events: Sequence[Mapping],
                  live_cutover_enabled: bool = False) -> dict[str, Any]:
    """Check R129 candidate + ordering, explicitly NOT proof of real events."""
    try:
        report = r129.convergence(candidate, synthetic_events,
                                  live_cutover_enabled=live_cutover_enabled)
    except (r129.ConvergenceHold, KeyError, TypeError, ValueError) as exc:
        deny('SOURCE_' + type(exc).__name__)
    if report.get('mode') != 'SYNTHETIC_ONLY_NON_AUTHORIZING':
        deny('NOT_SYNTHETIC')
    if report.get('authority', {}).get('live_worker_allowed') is not False:
        deny('SOURCE_AUTHORITY')
    # R129's derived unit is a synthetic fixture. Never use it as a real
    # launch unit: only the retained systemd kernel witness can provide that.
    result = {
        'schema_version': SCHEMA,
        'stage': 'SOURCE_ONLY_NOT_TERMINAL_EVIDENCE',
        'candidate_sha256': candidate['candidate_sha256'],
        'attempt_id': candidate['attempt_id'],
        'epoch': candidate['epoch'],
        'source_head': candidate['source_head'],
        'synthetic_trace_sha256': report['report_sha256'],
        'synthetic_unit_is_not_canonical': True,
        'runtime_evidence_verified': False,
        'live_worker_authorized': False,
        'terminal_ledger_written': False,
        'result_accepted': False,
        'authority': {'claim': False, 'release': False, 'retry': False,
                      'commit': False, 'push': False, 'terminal_acceptance': False},
    }
    result['report_sha256'] = _digest(result)
    return result


def witnessed_review_candidate(*, candidate: Mapping, synthetic_events: Sequence[Mapping],
                               attempt_root: Path, lease_path: Path,
                               witness: Any, runner: Any, timeout_seconds: int) -> dict[str, Any]:
    """Read real existing root lease and typed kernel witness, with no ledger mutation.

    This helper is deliberately NOT called by the live Worker launcher. It can
    only produce a review candidate; the canonical launch-manifest/decision
    join and ledger transition are still separate, mandatory prerequisites.
    """
    if os.geteuid() != 0:
        deny('ROOT_ONLY')
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 7200:
        deny('TIMEOUT')
    source = review_source(candidate=candidate, synthetic_events=synthetic_events)
    if not isinstance(attempt_root, Path) or not attempt_root.is_absolute() or attempt_root.is_symlink():
        deny('ATTEMPT_ROOT')
    expected = WORKER_ROOT / source['attempt_id']
    if attempt_root != expected or not attempt_root.is_dir():
        deny('ATTEMPT_SCOPE')
    spec = candidate['candidate_mcp_config']['mcpServers']['ForPrintValidation']
    if spec['cwd'] != str(expected/'workspace'/'repo'):
        deny('WORKSPACE_BINDING')
    if not isinstance(lease_path, Path) or not LEASE.fullmatch(str(lease_path)):
        deny('LEASE_SCOPE')
    if type(source['source_head']) is not str or type(source['epoch']) is not str:
        deny('SOURCE_IDENTITY')
    # No code below may inspect arbitrary paths or accept caller-supplied
    # fake lease dictionaries in place of R126's root-owned inode readback.
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_r126_root_external_revoke_v0_1 as revoke,
        cf10_systemd_terminal_bridge_v0_1 as terminal,
        cf10_systemd_kernel_witness_v0_1 as kernel,
    )
    if type(witness) is not kernel.KernelWitness or witness.closed:
        deny('TYPED_KERNEL_WITNESS_REQUIRED')
    if type(witness.unit) is not str or not UNIT.fullmatch(witness.unit):
        deny('UNIT')
    if type(witness.invocation_id) is not str or not INVOKE.fullmatch(witness.invocation_id):
        deny('INVOCATION_ID')
    if not callable(runner):
        deny('SYSTEMD_READER')
    try:
        lease = revoke.inspect_lease(
            lease_path, attempt=source['attempt_id'], epoch=source['epoch'],
            source_head=source['source_head'], capsule_id=r129.CAPSULE,
        )
    except (revoke.ExternalRevokeHold, OSError, ValueError, TypeError, KeyError):
        deny('ROOT_REVOKE_NOT_PROVEN')
    if type(lease) is not dict or lease.get('revoked') is not True:
        deny('ACTIVE_LEASE_NOT_TERMINAL')
    try:
        observed = terminal.witnessed_terminal(
            unit=witness.unit, attempt_root=attempt_root,
            stdout_path=attempt_root/'logs'/'stdout.log',
            stderr_path=attempt_root/'logs'/'stderr.log',
            witness=witness, runner=runner, timeout_seconds=timeout_seconds,
        )
    except (terminal.TerminalReadbackBlocked, kernel.WitnessBlocked,
            OSError, ValueError, TypeError, KeyError):
        deny('CANONICAL_KERNEL_TERMINAL_NOT_PROVEN')
    if (type(observed) is not dict or observed.get('systemd_unit') != witness.unit or
            observed.get('systemd_invocation_id') != witness.invocation_id or
            observed.get('quiescence_observation') !=
            'PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING' or
            observed.get('return_code') != 0 or observed.get('timed_out') is not False or
            observed.get('worker_result_accepted') is not False or
            observed.get('release_allowed') is not False or
            observed.get('automatic_retry') is not False):
        deny('TERMINAL_EVIDENCE_DRIFT')
    result = {
        'schema_version': SCHEMA,
        'stage': 'ROOT_REVOKE_AND_KERNEL_TERMINAL_READBACK_REVIEW_ONLY',
        'attempt_id': source['attempt_id'],
        'epoch': source['epoch'],
        'source_head': source['source_head'],
        'candidate_sha256': source['candidate_sha256'],
        'unit': witness.unit,
        'systemd_invocation_id': witness.invocation_id,
        'root_lease_revoked': True,
        'pinned_kernel_transition': '1_TO_0',
        'retained_systemd_terminal': True,
        'canonical_manifest_decision_join_attested': False,
        'terminal_ledger_written': False,
        'result_accepted': False,
        'live_worker_authorized': False,
        'authority': {'claim': False, 'release': False, 'retry': False,
                      'commit': False, 'push': False, 'terminal_acceptance': False},
    }
    result['report_sha256'] = _digest(result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='CF10 R131 non-authorizing terminal fence')
    parser.add_argument('--mode', choices=['source-check'], required=True)
    args = parser.parse_args(argv)
    try:
        # This command never opens a lease, starts or kills systemd, or grants
        # a Worker claim. Runtime evidence is only checked through the Python
        # API when a genuine future canonical witness is independently present.
        r129.verify_pinned_seams(r129.REPO)
        candidate, events = r129.synthetic_fixture()
        report = review_source(candidate=candidate, synthetic_events=events)
        if report['runtime_evidence_verified'] is not False:
            deny('FALSE_RUNTIME_ATTESTATION')
        print('CF10_R131_SOURCE_REVIEW=PASS_CANONICAL_R127_R129_BOUND')
        print('CF10_R131_RUNTIME_WITNESS=NOT_CLAIMED')
        print('CF10_R131_LIVE_CUTOVER=SEALED_FALSE')
        print('CF10_R131_G1_G5=OPEN_NO_LIVE_ADMISSION')
        return 0
    except (R131Hold, r129.ConvergenceHold, OSError, KeyError, ValueError, TypeError) as exc:
        print('CF10_R131=HOLD_' + type(exc).__name__)
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
