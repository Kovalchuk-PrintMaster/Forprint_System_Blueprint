"""CF10 r054: source-bound Task70 post-worker S3/Make bridge.

Only a *previously launched*, root-claimed, independent-proof-bound Task70
attempt may reach the canonical advance_cycle. No Worker launch, retry,
acceptance, promotion, publication or new authority store lives here.

The legacy Make release quarantine remains intact; this is a separate gate
for the already-started single-owner pilot, never a fallback for other tasks.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

SCHEMA = 'cf10_r054_postworker_pilot_gate_v0_1'
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
WORKER = 'worker-01'
ATTEMPT = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')
PINNED = (
    'Makefile',
    'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py',
    'scripts/coordination/control_plane/cf10_owner_operator_console_v0_1.py',
    'scripts/coordination/control_plane/cf10_s3_worker_workflow_v0_1.py',
    'scripts/coordination/control_plane/cf10_r054_pilot_postworker_gate_v0_1.py',
    'scripts/coordination/control_plane/cf10_r051_root_preclaim_receipt_v0_1.py',
    'scripts/coordination/control_plane/cf10_r046_pilot_cutover_review_v0_1.py',
    'scripts/coordination/control_plane/cf10_r047_pilot_proof_lineage_v0_1.py',
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/cf10_r037_finalizer_boundary_v0_1.py',
)

class PilotPostworkerBlocked(RuntimeError):
    pass


def _deny(reason: str) -> None:
    raise PilotPostworkerBlocked('CF10_R054_' + reason)


def _json_no_duplicates(raw: bytes) -> dict:
    def unique(pairs):
        doc = {}
        for k, v in pairs:
            if k in doc:
                _deny('ROOT_CLAIM_DUPLICATE_JSON_KEY')
            doc[k] = v
        return doc
    try:
        doc = json.loads(raw, object_pairs_hook=unique)
    except (UnicodeDecodeError, ValueError, TypeError):
        _deny('ROOT_CLAIM_INVALID_JSON')
    if not isinstance(doc, dict):
        _deny('ROOT_CLAIM_NOT_OBJECT')
    return doc


def _pinned_source(root: Path, head: str) -> None:
    if not isinstance(head, str) or re.fullmatch('[0-9a-f]{40}', head) is None:
        _deny('SOURCE_HEAD_INVALID')
    for rel in PINNED:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            _deny('CRITICAL_SOURCE_FILE_UNSAFE')
        try:
            cp = subprocess.run(['git', 'show', head + ':' + rel], cwd=root,
                                stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=25, check=False)
        except (OSError, subprocess.SubprocessError):
            _deny('SOURCE_GIT_BLOB_UNAVAILABLE')
        if cp.returncode != 0 or cp.stdout != path.read_bytes():
            _deny('SOURCE_DRIFT')


def _consumed_owner_claim(*, task: str, attempt: str, head: str) -> None:
    """Exact source-bound root marker written by existing PAM owner._owner_claim."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    folder = once.open_root_owned_state_dir()
    try:
        key = hashlib.sha256((WORKER + '\0' + attempt).encode()).hexdigest()
        name = 'owner_attempt_' + key + '.json'
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            fd = os.open(name, flags, dir_fd=folder)
        except (FileNotFoundError, OSError):
            _deny('ROOT_OWNER_CLAIM_UNAVAILABLE')
        try:
            st = os.fstat(fd)
            if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or
                    stat.S_IMODE(st.st_mode) != 0o600 or not 0 < st.st_size <= 8192):
                _deny('ROOT_OWNER_CLAIM_INODE_UNSAFE')
            raw = os.read(fd, st.st_size + 1)
            if len(raw) != st.st_size:
                _deny('ROOT_OWNER_CLAIM_BYTES_CHANGED')
        finally:
            os.close(fd)
    finally:
        os.close(folder)
    doc = _json_no_duplicates(raw)
    requirements = {
        'schema_version': 'cf10_owner_pam_attempt_claim_v0_1',
        'status': 'CONSUMED_BEFORE_SPAWN_NO_RETRY',
        'worker_id': WORKER,
        'task_prompt_id': task,
        'attempt_id': attempt,
        'source_head': head,
        'authority_is_password_and_operator_policy': True,
        'automatic_retry': False,
    }
    if set(doc) != set(requirements) | {'time_utc'}:
        _deny('ROOT_OWNER_CLAIM_FIELD_SET')
    for key, value in requirements.items():
        if type(doc.get(key)) is not type(value) or doc[key] != value:
            _deny('ROOT_OWNER_CLAIM_SCOPE_OR_STATUS_MISMATCH')
    if not isinstance(doc.get('time_utc'), str) or not doc['time_utc']:
        _deny('ROOT_OWNER_CLAIM_TIME_INVALID')


def inspect(*, root: Path, runtime: Path, task: str, attempt: str) -> dict:
    """Independent read-only observations; a positive report isn't authority."""
    try:
        if (root.resolve() != PROJECT or runtime.resolve() != RUNTIME or
                os.geteuid() != 0 or task != TASK or
                not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None):
            _deny('CANONICAL_ROOT_OR_SCOPE_REQUIRED')
        from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
        from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as sealed
        from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as release
        from scripts.coordination.control_plane import cf10_s3_worker_workflow_v0_1 as s3
        from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
        from scripts.coordination.control_plane import governed_worker_cycle as cycle
        head = console.source_guard(root)
        _pinned_source(root, head)
        # Root-owned inputs are authoritative only for their exact attempt;
        # sealed PRECLAIM is checked by r046 again in LAUNCH_WINDOW mode.
        witness = sealed.inspect(root=root, task=task, attempt=attempt, head=head)
        if witness.get('preclaim_root_receipt_verified') is not True or witness.get('blockers') != []:
            _deny('SEALED_PRECLAIM_NOT_VERIFIED')
        release_doc = release.inspect(root=root, task=task, attempt=attempt, phase='LAUNCH_WINDOW')
        if (release_doc.get('status') != 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED' or
                release_doc.get('checks', {}).get('r047_source_lineage') != 'EXACT_RAW_BYTES_BOUND' or
                release_doc.get('blockers') != [] or release_doc.get('launch_allowed') is not False):
            _deny('ROOT_RELEASE_PROOF_LINEAGE_UNVERIFIED')
        _consumed_owner_claim(task=task, attempt=attempt, head=head)
        if writer.load_enforced_protocol(required=True) is None:
            _deny('WRITER_LOCK_NOT_ENFORCED')
        state = cycle.status(root=root, runtime_root=runtime,
                             task_prompt_id=task, attempt_id=attempt, worker_id=WORKER)
        if (state.get('derived_non_authoritative') is not True or
                state.get('state') not in s3.ADVANCE_STATES or state.get('contradictions')):
            _deny('CANONICAL_POSTWORKER_STATE_UNAVAILABLE')
        candidate = s3.inspect(root, runtime, task, attempt)
        if (candidate.get('classification') != 'READY_FOR_BOUND_POSTWORKER_ADVANCE' or
                candidate.get('governed_state') != state.get('state') or
                candidate.get('mutating_advance_allowed') is not True or
                candidate.get('attempt_id') != attempt or
                candidate.get('task_prompt_id') != task):
            _deny('S3_POSTWORKER_READINESS_UNVERIFIED')
        return {'schema_version': SCHEMA,
                'status': 'EXACT_PILOT_POSTWORKER_READY_NON_AUTHORIZING',
                'blockers': [], 'task_prompt_id': task, 'attempt_id': attempt,
                'source_head': head, 'owner_claim_consumed': True,
                'mutating_advance_executed': False, 'worker_launched_by_this_module': False,
                'automatic_retry': False, 'automatic_accept': False,
                'automatic_publication': False, 'release_authority_issued': False}
    except Exception as exc:
        return {'schema_version': SCHEMA, 'status': 'BLOCKED_PILOT_POSTWORKER',
                'blockers': [type(exc).__name__ + ':' + str(exc)[:150]],
                'task_prompt_id': task, 'attempt_id': attempt,
                'mutating_advance_executed': False, 'worker_launched_by_this_module': False,
                'automatic_retry': False, 'automatic_accept': False,
                'automatic_publication': False, 'release_authority_issued': False}


def ready(*, root: Path, runtime: Path, task: str, attempt: str) -> bool:
    return inspect(root=root, runtime=runtime, task=task, attempt=attempt)['status'] == 'EXACT_PILOT_POSTWORKER_READY_NON_AUTHORIZING'


def advance(*, root: Path, runtime: Path, task: str, attempt: str) -> dict:
    """Only the existing canonical advance may modify terminal ledger.

    A new (not cached) canonical and root-owned review precedes the call;
    internal r037 independently checks Worker Result BEFORE the terminal ledger.
    """
    report = inspect(root=root, runtime=runtime, task=task, attempt=attempt)
    if report['status'] != 'EXACT_PILOT_POSTWORKER_READY_NON_AUTHORIZING':
        _deny('PRE_MUTATION_GATE_REFUSED')
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    result = cycle.advance_cycle(root=root, runtime_root=runtime, task_prompt_id=task,
                                 attempt_id=attempt, worker_id=WORKER)
    if not isinstance(result, dict) or result.get('state') != 'AWAITING_OPERATOR_REVIEW':
        _deny('CANONICAL_ADVANCE_NOT_TERMINAL_OPERATOR_REVIEW')
    # The native governed cycle owns all state progression and failure/terminal
    # evidence. Never infer ACCEPT or publication from this returned dict.
    return {'schema_version': SCHEMA,
            'status': 'CANONICAL_ADVANCE_CALLED_RESULT_REQUIRES_FRESH_STATUS',
            'canonical_result': result, 'automatic_retry': False,
            'automatic_accept': False, 'automatic_publication': False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('requirements', 'inspect', 'advance'), required=True)
    parser.add_argument('--root', type=Path, default=PROJECT)
    parser.add_argument('--runtime-root', type=Path, default=RUNTIME)
    parser.add_argument('--task', default='')
    parser.add_argument('--attempt', default='')
    parser.add_argument('--confirm', default='')
    ns = parser.parse_args(argv)
    if ns.mode == 'requirements':
        result = {'schema_version': SCHEMA, 'status': 'SOURCE_POSTWORKER_BRIDGE_PRESENT',
                  'production_cutover': False, 'worker_launched': False,
                  'legacy_make_quarantine_unchanged': True,
                  'preclaim_and_attempt_proofs_required': True,
                  'one_shot_claim_consumed_required': True,
                  'canonical_advance_only': True,
                  'next_action': 'VERIFY_EXACT_TASK70_PROOFS_BEFORE_PILOT_LAUNCH'}
    elif ns.mode == 'inspect':
        result = inspect(root=ns.root, runtime=ns.runtime_root, task=ns.task, attempt=ns.attempt)
    elif ns.confirm != 'ADVANCE_EXACT_SOURCE_BOUND_TASK70_POSTWORKER_ONCE':
        result = {'schema_version': SCHEMA, 'status': 'BLOCKED_CONFIRM_REQUIRED',
                  'blockers': ['EXPLICIT_CANONICAL_ADVANCE_CONFIRMATION_MISSING']}
    else:
        try:
            result = advance(root=ns.root, runtime=ns.runtime_root, task=ns.task, attempt=ns.attempt)
        except Exception as exc:
            result = {'schema_version': SCHEMA, 'status': 'BLOCKED_CANONICAL_ADVANCE',
                      'blockers': [type(exc).__name__ + ':' + str(exc)[:150]]}
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
    return 0 if result['status'] in ('SOURCE_POSTWORKER_BRIDGE_PRESENT',
                                     'EXACT_PILOT_POSTWORKER_READY_NON_AUTHORIZING',
                                     'CANONICAL_ADVANCE_CALLED_RESULT_REQUIRES_FRESH_STATUS') else 2

if __name__ == '__main__':
    raise SystemExit(main())
