"""CF-10 r046: verify an *external* exact single-owner pilot release candidate.

This module never issues approval, prepares an attempt, launches a Worker, adds
ledger records, interprets synthetic fixtures as live evidence, or changes the
legacy 8-proof signed-release corridor.  A complete candidate is NOT launch
permission: a separate source-controlled cutover must explicitly adopt it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Mapping

SCHEMA = "cf10_r046_pilot_cutover_review_v0_1"
RELEASE_SCHEMA = "cf10_single_owner_bounded_pilot_release_v0_1"
PROOF_SCHEMA = "cf10_single_owner_technical_proof_v0_1"
ATTEMPT = re.compile(r"cf10-u180j-a[0-9]{3,}\Z")
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
TASK70 = "cf10-validation-check-pipeline-profile-and-optimization-v0-1"
WORKER = "worker-01"
TRUSTED_ROOT = Path('/var/lib/forprint/cf10_s01_single_use')  # existing root-owned state, no new store
PROOF_TYPES = (
    'DISPOSABLE_SYSTEMD_CONTROLLER_LOSS_RECOVERY',
    'TMP_UNAVAILABLE_END_TO_END',
    'INDEPENDENT_FINALIZER_GATE_FIXTURE',
    'SOURCE_AND_WRITER_BOUNDARY',
)

class CutoverReviewBlocked(RuntimeError):
    pass


def _deny(code: str) -> None:
    raise CutoverReviewBlocked(code)


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _valid_sha(value: object, pattern: re.Pattern) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _attempt_key(attempt: str) -> str:
    return hashlib.sha256((WORKER + '\0' + attempt).encode('utf-8')).hexdigest()


def _proof_name(kind: str, attempt: str) -> str:
    return 'proof_' + _attempt_key(attempt) + '_' + kind.lower() + '.json'


def validate_candidate(candidate: Mapping, proofs: Mapping[str, Mapping], * ,
                       head: str, task: str, attempt: str) -> list[str]:
    """Pure, deterministic validation; no bytes on disk and no authority minted."""
    bad: list[str] = []
    if not _valid_sha(head, SHA40):
        bad.append('SOURCE_HEAD_INVALID')
    if task != TASK70 or not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None:
        bad.append('EXACT_TASK70_ATTEMPT_REQUIRED')
    if not isinstance(candidate, Mapping):
        return sorted(set(bad + ['PILOT_RELEASE_DOCUMENT_MISSING']))
    required = {
        'schema_version': RELEASE_SCHEMA,
        'status': 'EXPLICIT_OWNER_PILOT_CANDIDATE_NON_AUTHORIZING',
        'profile': 'SINGLE_OWNER_BOUNDED_TASK70',
        'owner': 'forprint_system_blueprint',
        'worker_id': WORKER,
        'task_prompt_id': TASK70,
        'attempt_id': attempt,
        'source_head': head,
        'automatic_retry': False,
        'automatic_acceptance': False,
        'automatic_publication': False,
        'legacy_signed_release_replaced': False,
        'independent_human_signer_required': False,
        'root_owned_one_shot_claim_required': True,
        'pam_operator_confirmation_required': True,
        'strict_finalizer_required': True,
    }
    if set(candidate) != (set(required) | {'proofs'}):
        bad.append('EXACT_RELEASE_FIELDS_REQUIRED')
    for key, expected in required.items():
        value = candidate.get(key)
        if type(value) is not type(expected) or value != expected:
            bad.append('RELEASE_' + key.upper() + '_MISMATCH')
    bindings = candidate.get('proofs')
    if not isinstance(bindings, Mapping) or set(bindings) != set(PROOF_TYPES):
        bad.append('EXACT_FOUR_PROOF_BINDINGS_REQUIRED')
        bindings = {}
    if not isinstance(proofs, Mapping) or set(proofs) != set(PROOF_TYPES):
        bad.append('EXACT_FOUR_PROOF_DOCUMENTS_REQUIRED')
        proofs = {}
    seen_digests: set[str] = set()
    for kind in PROOF_TYPES:
        binding = bindings.get(kind)
        doc = proofs.get(kind)
        if not isinstance(binding, Mapping) or set(binding) != {'sha256', 'relative_file'}:
            bad.append('PROOF_BINDING_INVALID:' + kind)
            continue
        relative = binding.get('relative_file')
        digest = binding.get('sha256')
        if (not isinstance(relative, str) or relative != _proof_name(kind, attempt)
                or not _valid_sha(digest, SHA64)):
            bad.append('PROOF_PATH_OR_SHA_INVALID:' + kind)
        if isinstance(digest, str):
            if digest in seen_digests:
                bad.append('DUPLICATE_PROOF_DIGEST')
            seen_digests.add(digest)
        if not isinstance(doc, Mapping):
            bad.append('PROOF_DOCUMENT_MISSING:' + kind)
            continue
        expected_proof = {
            'schema_version': PROOF_SCHEMA,
            'status': 'VERIFIED_TECHNICAL_EVIDENCE',
            'proof_type': kind,
            'source_head': head,
            'task_prompt_id': TASK70,
            'attempt_id': attempt,
            'worker_id': WORKER,
            'fixture_only': kind in ('DISPOSABLE_SYSTEMD_CONTROLLER_LOSS_RECOVERY', 'TMP_UNAVAILABLE_END_TO_END', 'INDEPENDENT_FINALIZER_GATE_FIXTURE'),
            'production_worker_launched': False,
            'independently_reviewed': True,
        }
        # Evidence references must be explicit and not stored in project tmp.
        if set(doc) != (set(expected_proof) | {'source_evidence_sha256'}):
            bad.append('PROOF_FIELDS_INVALID:' + kind)
        for key, value in expected_proof.items():
            if type(doc.get(key)) is not type(value) or doc.get(key) != value:
                bad.append('PROOF_' + kind + '_' + key.upper() + '_MISMATCH')
        if not _valid_sha(doc.get('source_evidence_sha256'), SHA64):
            bad.append('PROOF_SOURCE_EVIDENCE_DIGEST_INVALID:' + kind)
        elif isinstance(digest, str):
            blob = (json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()
            if _sha(blob) != digest:
                bad.append('PROOF_BYTES_SHA_MISMATCH:' + kind)
    return sorted(set(bad))


def _trusted_file(folder_fd: int, name: str) -> bytes:
    if not re.fullmatch(r'[a-z0-9_]+\.json', name):
        _deny('INVALID_DURABLE_FILE_NAME')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    fd = os.open(name, flags, dir_fd=folder_fd)
    try:
        st = os.fstat(fd)
        if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or
                stat.S_IMODE(st.st_mode) != 0o600 or st.st_size <= 0 or st.st_size > 32768):
            _deny('UNTRUSTED_DURABLE_FILE:' + name)
        raw = os.read(fd, st.st_size + 1)
        if len(raw) != st.st_size:
            _deny('DURABLE_FILE_READ_RACE:' + name)
        return raw
    finally:
        os.close(fd)


def _trusted_folder(path: Path) -> int:
    if path != TRUSTED_ROOT:
        _deny('NON_CANONICAL_ROOT_STATE')
    # Re-use existing canonical root-owned 0700 store, including its parent
    # identity, no-symlink and inode checks. No new release ledger is created.
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    return once.open_root_owned_state_dir()


def _json_checked(raw: bytes) -> dict:
    def no_duplicate(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                _deny('DUPLICATE_JSON_KEY')
            result[name] = value
        return result
    doc = json.loads(raw, object_pairs_hook=no_duplicate)
    if not isinstance(doc, dict):
        _deny('JSON_OBJECT_REQUIRED')
    return doc


def inspect(*, root: Path, task: str, attempt: str, phase: str = 'PRECLAIM') -> dict:
    """Read only source-pinned, root-controlled proof; never create state."""
    problems = []
    checks = {}
    head = ''
    if root.resolve() != Path('/srv/software_development/forprint-project/forprint_system_blueprint'):
        problems.append('NON_CANONICAL_PROJECT_ROOT')
    else:
        try:
            from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
            from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
            head = console.source_guard(root)
            if phase == 'PRECLAIM':
                prior = admission.collect(root, task, attempt)
                if prior.get('preclaim_evidence_complete') is not True:
                    problems.append('R045_PRECLAIM_UNVERIFIED')
                checks['r045'] = prior.get('status', 'UNKNOWN')
            elif phase == 'LAUNCH_WINDOW':
                # The active Make/backend state differs from PRECLAIM. Rechecking
                # r045 here is both impossible and semantically incorrect.
                from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as sealed
                prior = sealed.inspect(root=root, task=task, attempt=attempt, head=head)
                if prior.get('preclaim_root_receipt_verified') is not True:
                    problems.append('R051_ROOT_PRECLAIM_UNVERIFIED')
                checks['r051'] = prior.get('status', 'UNKNOWN')
            else:
                problems.append('UNKNOWN_PILOT_REVIEW_PHASE')
        except Exception:
            problems.append('CANONICAL_SOURCE_OR_PRECLAIM_CHECK_FAILED')
    try:
        fd = _trusted_folder(TRUSTED_ROOT)
        try:
            key = _attempt_key(attempt)
            release = _json_checked(_trusted_file(fd, 'owner_pilot_release_' + key + '.json'))
            proofs = {}
            bindings = release.get('proofs')
            if not isinstance(bindings, dict):
                _deny('RELEASE_PROOF_MAP_INVALID')
            for typ in PROOF_TYPES:
                binding = bindings.get(typ)
                if not isinstance(binding, dict):
                    _deny('RELEASE_BINDING_MISSING:' + typ)
                path = binding.get('relative_file', '')
                if not isinstance(path, str):
                    _deny('INVALID_RELATIVE_PROOF_FILE')
                raw = _trusted_file(fd, path)
                if _sha(raw) != binding.get('sha256'):
                    _deny('DURABLE_PROOF_DIGEST_MISMATCH:' + typ)
                proofs[typ] = _json_checked(raw)
            # r047: source_evidence_sha256 must reference real, exact root-owned
            # raw bytes. A declaration of independent review alone is not proof.
            from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as lineage
            lineage_blockers = lineage.verify_sources(
                folder_fd=fd, proofs=proofs, head=head, task=task,
                attempt=attempt, worker=WORKER, read=_trusted_file, decode=_json_checked,
            )
            problems.extend(lineage_blockers)
            checks['r047_source_lineage'] = ('EXACT_RAW_BYTES_BOUND' if not lineage_blockers
                                              else 'UNPROVEN_OR_BLOCKED')
        finally:
            os.close(fd)
        problems.extend(validate_candidate(release, proofs, head=head, task=task, attempt=attempt))
        checks['root_owned_release'] = 'READ_ONLY_EXACT_SCOPE_VERIFIED'
    except (OSError, ValueError, TypeError, KeyError, CutoverReviewBlocked):
        problems.append('DURABLE_PILOT_PROOF_OR_RELEASE_UNAVAILABLE')
    if not problems:
        # Caller must separately perform frozen source and exact Work Front
        # verification immediately before any future owner-PAM launch.
        status = 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED'
        next_action = 'SEPARATE_CUTOVER_DECISION_AND_LIVE_WIRING_REQUIRED'
    else:
        status = 'BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE'
        next_action = 'COLLECT_AND_INDEPENDENTLY_REVIEW_EXACT_TECHNICAL_PROOFS'
    return {
        'schema_version': SCHEMA,
        'status': status,
        'task_prompt_id': task,
        'attempt_id': attempt,
        'checks': checks,
        'blockers': sorted(set(problems)),
        'required_proof_types': list(PROOF_TYPES),
        'operator_claim_consumed': False,
        'launch_allowed': False,
        'production_cutover': False,
        'worker_launched': False,
        'automatic_retry': False,
        'next_action': next_action,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('requirements', 'inspect'))
    ap.add_argument('--root', type=Path, default=Path('.'))
    ap.add_argument('--task-prompt-id', default='')
    ap.add_argument('--attempt-id', default='')
    ap.add_argument('--phase', choices=('PRECLAIM', 'LAUNCH_WINDOW'), default='PRECLAIM')
    ns = ap.parse_args(argv)
    if ns.action == 'requirements':
        data = {'schema_version': SCHEMA, 'required_proof_types': list(PROOF_TYPES),
                'release_root': str(TRUSTED_ROOT), 'production_cutover': False,
                'next_action': 'RUN_DISPOSABLE_PROOFS_AND_SEPARATE_OPERATOR_CUTOVER'}
    else:
        data = inspect(root=ns.root, task=ns.task_prompt_id, attempt=ns.attempt_id, phase=ns.phase)
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if ns.action == 'requirements' or not data['blockers'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
