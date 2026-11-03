"""CF10 r052: source-bound launch guard attached to the existing owner PAM seam.

Fail closed BEFORE password and again while owner_launch.lock is held before
irreversible claim. It reuses r051 PRECLAIM (never recollects r045), r046/r047
proof lineage, current canonical source/ledger/writer/systemd checks, and the
unchanged canonical backend/Make release boundaries.

Only cf10_owner_pam_launch.launch_once can perform PAM and invoke Worker. This
module has NO issue/provision/launch operation, no trust in a supplied all-true
observation dict and no separate state store. Current Make/backend are sealed;
this code cannot enable them. A distinct source-reviewed cutover is necessary.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SCHEMA = 'cf10_r052_owner_launch_guard_v0_1'
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
WORKER = 'worker-01'
ATTEMPT = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')
PINNED_FILES = (
    'Makefile',
    'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py',
    'scripts/coordination/control_plane/cf10_r052_owner_launch_guard_v0_1.py',
    'scripts/coordination/control_plane/cf10_r051_root_preclaim_receipt_v0_1.py',
    'scripts/coordination/control_plane/cf10_r046_pilot_cutover_review_v0_1.py',
    'scripts/coordination/control_plane/cf10_r050_two_phase_pilot_v0_1.py',
    'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py',
    'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py',
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/cf10_r037_finalizer_boundary_v0_1.py',
    'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py',
)

class LaunchGuardBlocked(RuntimeError):
    pass


def _deny(code: str):
    raise LaunchGuardBlocked('CF10_R052_' + code)


def _source_exact(root: Path, head: str) -> None:
    """Hash-relevant source identity uses Git blobs, not untrusted flags."""
    if not isinstance(head, str) or re.fullmatch(r'[0-9a-f]{40}', head) is None:
        _deny('SOURCE_HEAD_INVALID')
    for rel in PINNED_FILES:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            _deny('SOURCE_MISSING_OR_SYMLINK')
        try:
            result = subprocess.run(['git', 'show', f'{head}:{rel}'], cwd=root,
                                    capture_output=True, check=False, timeout=20)
        except (OSError, subprocess.SubprocessError):
            _deny('GIT_BLOB_UNAVAILABLE')
        if result.returncode != 0 or path.read_bytes() != result.stdout:
            _deny('CRITICAL_SOURCE_DRIFT')


def _make_has_guarded_pilot_route(root: Path) -> bool:
    """A separate pilot route must leave the legacy Make quarantine literal.

    r045 PRECLAIM pins the quarantine text. A future cutover must be compiled
    into source *before* the attempt is frozen; no Git HEAD change may occur
    between r051 sealing and launch. This r052 patch deliberately leaves the
    pilot route absent until that source change is reviewed and published.
    """
    text = (root / 'Makefile').read_text('utf-8')
    legacy = ('cf10-s01-runtime-launch-preflight:\n'
              '\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2')
    if legacy not in text:
        return False
    match = re.search(r'(?m)^cf10-s01-pilot-launch-preflight:[ \t]*\n((?:^[ \t]+[^\n]*\n)+)', text)
    if match is None:
        return False
    recipe = match.group(1)
    return ('cf10_r052_owner_launch_guard_v0_1' in recipe
            and '--mode guarded-preflight' in recipe
            and 'QUARANTINED_NEEDS_INDEPENDENT_REBIND' not in recipe)


def _backend_has_guarded_pilot_route(root: Path) -> bool:
    """Require future exact source-bound pilot branch; never flip legacy bool."""
    code = (root / 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text('utf-8')
    return ('LIVE_CUTOVER_ENABLED=False' in code
            and '# CF10_SOURCE_BOUND_PILOT_BACKEND_BRANCH_VERIFIED' in code
            and 'cf10_r052_owner_launch_guard_v0_1' in code)


def _observe(*, root: Path, runtime_root: Path, task: str, attempt: str, head: str) -> dict[str, bool]:
    """Read from existing canonical observers; never accept caller booleans."""
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as release
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase
    from scripts.coordination.control_plane import cf10_training_dispatch as training

    if (root.resolve() != PROJECT or runtime_root.resolve() != RUNTIME
            or task != TASK or not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None
            or os.geteuid() != 0):
        _deny('ROOT_TASK_ATTEMPT_OR_PRIVILEGE_INVALID')
    if console.source_guard(root) != head or owner._assert_live_source(root) != head:
        _deny('SOURCE_GUARD_INVALID')
    _source_exact(root, head)
    candidate, blockers = admission._task70(root)
    if blockers or len(candidate) != 1 or candidate[0]['task_prompt_id'] != task:
        _deny('CANONICAL_TASK70_NOT_VERIFIED')
    bound = training.resolve_training_task(root=root, task_prompt_id=task)
    if bound.get('work_front_id') != candidate[0]['work_front_id']:
        _deny('WORK_FRONT_MISMATCH')

    facts = {}
    sealed = preclaim.inspect(root=root, task=task, attempt=attempt, head=head)
    facts['preclaim_root_receipt_verified'] = (
        sealed.get('preclaim_root_receipt_verified') is True and sealed.get('blockers') == []
    )
    proof = release.inspect(root=root, task=task, attempt=attempt, phase='LAUNCH_WINDOW')
    facts['release_candidate_raw_lineage_verified'] = (
        proof.get('status') == 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED'
        and proof.get('checks', {}).get('r047_source_lineage') == 'EXACT_RAW_BYTES_BOUND'
        and proof.get('blockers') == []
        and proof.get('launch_allowed') is False
    )
    # Existing owner preclaim checks frozen Handoff/source and cycle state.
    try:
        owner._cycle_preclaim(root, runtime_root, task, attempt)
        state = cycle.status(root=root, runtime_root=runtime_root,task_prompt_id=task,
                             attempt_id=attempt, worker_id=WORKER)
        facts['canonical_cycle_ready'] = state.get('state') == 'READY_FOR_WORKER_LAUNCH' and not state.get('contradictions')
        facts['frozen_input_current'] = facts['canonical_cycle_ready']
    except Exception:
        facts['canonical_cycle_ready'] = False
        facts['frozen_input_current'] = False
    try:
        facts['writer_protocol_enforced'] = writer.load_enforced_protocol(required=True) is not None
    except Exception:
        facts['writer_protocol_enforced'] = False
    try:
        facts['root_one_shot_claim_unconsumed'] = admission._claim_unconsumed(attempt)[0] is True
    except Exception:
        facts['root_one_shot_claim_unconsumed'] = False
    try:
        store = ledger.store_root(root, ledger.load_contract(root), None)
        facts['canonical_ledger_unstarted'] = not ledger.records_for_attempt(store, attempt)
    except Exception:
        facts['canonical_ledger_unstarted'] = False
    try:
        facts['systemd_worker_quiescent'] = admission._systemd_quiescent()[0] is True
    except Exception:
        facts['systemd_worker_quiescent'] = False
    facts['source_guard_verified'] = True
    facts['source_bound_pilot_make_route_verified'] = _make_has_guarded_pilot_route(root)
    # Legacy backend remains disabled; future pilot branch is separately
    # source-pinned and exact-attempt scoped. No runtime boolean toggle.
    facts['source_bound_pilot_systemd_backend_verified'] = (
        backend.LIVE_CUTOVER_ENABLED is False and _backend_has_guarded_pilot_route(root)
    )
    # These source semantics remain mandatory and separate from release/PAM.
    # Exact source-pinned r037 is still invoked BEFORE terminal ledger appends.
    cycle_src = (root / 'scripts/coordination/control_plane/governed_worker_cycle.py').read_text('utf-8')
    facts['independent_finalizer_required'] = (
        'cf10_r037_finalizer_boundary_v0_1 as boundary' in cycle_src
        and 'boundary.' in cycle_src
    )
    # This is the existing owner's O_EXCL claim/no-retry implementation, not
    # a caller-provided assertion. Both owner and route bytes are pinned above.
    owner_src = (root / 'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py').read_text('utf-8')
    facts['automatic_retry_disabled'] = (
        'os.O_EXCL' in owner_src and 'OWNER_ATTEMPT_ALREADY_CONSUMED_NO_RETRY' in owner_src
    )
    old_release = (root / 'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py').read_bytes()
    facts['legacy_signed_release_separate'] = (
        hashlib.sha256(old_release).hexdigest()
        == 'f8d6cb94079233d04a7b5f92b6418cd6393485d8565a44338f2fcf210eac0eec'
    )
    required = set(phase.REQUIRED_LAUNCH_OBSERVATIONS) - {'owner_pam_session_authenticated'}
    if set(facts) != required:
        _deny('OBSERVER_FIELD_CONTRACT_DRIFT')
    return facts


def _assert_stage(*, stage: str, root: Path, runtime_root: Path,
                  task: str, attempt: str, head: str) -> None:
    if stage not in ('PRE_PASSWORD', 'POST_PASSWORD_PRE_CLAIM'):
        _deny('INVALID_BOUNDARY_STAGE')
    facts = _observe(root=root, runtime_root=runtime_root, task=task,
                     attempt=attempt, head=head)
    from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase
    required = set(phase.REQUIRED_LAUNCH_OBSERVATIONS) - {'owner_pam_session_authenticated'}
    failed = sorted(key for key in required if type(facts.get(key)) is not bool or facts.get(key) is not True)
    if set(facts) != required:
        failed.append('OBSERVER_FIELD_CONTRACT_DRIFT')
    if failed:
        _deny('BOUNDARY_INCOMPLETE_' + '_'.join(failed))
    if stage == 'POST_PASSWORD_PRE_CLAIM':
        from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase
        from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as release
        doc = release.inspect(root=root, task=task, attempt=attempt, phase='LAUNCH_WINDOW')
        from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as sealed
        # The sealed read is independently repeated under the owner mutex.
        snap = sealed.inspect(root=root, task=task, attempt=attempt, head=head)
        if snap.get('preclaim_root_receipt_verified') is not True:
            _deny('POST_PASSWORD_PRECLAIM_CHANGED')
        # r050 evaluates supplied observations, but only facts above are read
        # directly from canonical observers. PAM success is guaranteed by the
        # owner's call ordering; r052 has no password API of its own.
        # r050 needs the full sealed PRECLAIM snapshot, not an inspect summary.
        from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
        from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
        folder = once.open_root_owned_state_dir()
        try:
            snapshot = preclaim.read_verified(folder=folder, task=task,attempt=attempt,head=head)
        finally:
            os.close(folder)
        assessment = phase.launch_window(snapshot=snapshot, release=doc,
                                          observations={**facts,'owner_pam_session_authenticated': True},
                                          task=task, attempt=attempt, source_head=head)
        if assessment['status'] != 'PILOT_LAUNCH_CANDIDATE_NON_AUTHORIZING' or assessment['blockers']:
            _deny('CANONICAL_TWO_PHASE_LAUNCH_WINDOW_FAILED')


def assert_pre_password(*, root: Path, runtime_root: Path, task: str, attempt: str, head: str) -> None:
    _assert_stage(stage='PRE_PASSWORD', root=root, runtime_root=runtime_root,
                  task=task, attempt=attempt, head=head)


def assert_post_password_pre_claim(*, root: Path, runtime_root: Path, task: str, attempt: str, head: str) -> None:
    _assert_stage(stage='POST_PASSWORD_PRE_CLAIM', root=root, runtime_root=runtime_root,
                  task=task, attempt=attempt, head=head)


def requirements() -> dict:
    return {'schema_version': SCHEMA,
            'status': 'GUARD_WIRED_PILOT_RELEASE_NOT_ACTIVATED',
            'pre_password_guarded': True,
            'post_password_pre_claim_guarded': True,
            'root_preclaim_recollected': False,
            'production_worker_launched': False,
            'production_cutover': False,
            'launch_allowed': False,
            'remaining': ['SOURCE_BOUND_MAKE_CUTOVER', 'SOURCE_BOUND_BACKEND_CUTOVER',
                          'COMPLETE_ATTEMPT_BOUND_ROOT_PROOFS', 'OWNER_PAM'],
            'next_action': 'SEPARATE_GOVERNED_CUTOVER_AFTER_PROOF_AND_SOURCE_REVIEW'}


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('requirements',),required=True)
    ns=parser.parse_args(argv)
    print(json.dumps(requirements(),ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
