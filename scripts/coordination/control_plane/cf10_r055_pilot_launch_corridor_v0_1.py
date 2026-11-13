"""CF10 r055: exact Task70 pilot source corridor; not a proof issuer.

This does not activate an alternate global Worker launcher. A source-bound pilot
may use the existing owner-PAM/no-retry route only with exact root-owned sealed
PRECLAIM and the four externally reviewed, raw-byte-bound proof records.
Root operator is in the trusted computing base; the r047 raw format alone does
NOT authenticate an external proof producer, and must be independently reviewed.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
WORKER = 'worker-01'
ATTEMPT = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')
SCHEMA = 'cf10_r055_exact_pilot_launch_corridor_v0_1'
# This source list is independently compared against the published Git HEAD.
CRITICAL = (
    'Makefile',
    'scripts/coordination/control_plane/cf10_r055_pilot_launch_corridor_v0_1.py',
    'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py',
    'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py',
    'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py',
    'scripts/coordination/control_plane/cf10_r052_owner_launch_guard_v0_1.py',
    'scripts/coordination/control_plane/cf10_r053_dormant_pilot_bridge_v0_1.py',
    'scripts/coordination/control_plane/cf10_r051_root_preclaim_receipt_v0_1.py',
    'scripts/coordination/control_plane/cf10_r046_pilot_cutover_review_v0_1.py',
    'scripts/coordination/control_plane/cf10_r047_pilot_proof_lineage_v0_1.py',
    'scripts/coordination/control_plane/cf10_r045_pilot_admission_v0_1.py',
    'scripts/coordination/control_plane/cf10_r050_two_phase_pilot_v0_1.py',
    'scripts/coordination/control_plane/cf10_r054_pilot_postworker_gate_v0_1.py',
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/cf10_pilot_cycle_v0_1.py',
    'scripts/coordination/control_plane/worker_runtime/cf10_r083_frozen_epoch_gate_v0_1.py',
    'scripts/coordination/control_plane/cf10_r037_finalizer_boundary_v0_1.py',
    'scripts/coordination/execution_attempt_writer_lock_v0_1.py',
    'scripts/coordination/execution_attempt_ledger_v0_1.py',
)

class PilotLaunchBlocked(RuntimeError):
    pass


def _deny(reason: str) -> None:
    raise PilotLaunchBlocked('CF10_R055_' + reason)


def _source(*, root: Path, runtime: Path, task: str, attempt: str, head: str) -> None:
    """A root-only, exact-attempt corridor; no environment or boolean override."""
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    if (os.geteuid() != 0 or root.resolve() != PROJECT or runtime.resolve() != RUNTIME
            or task != TASK or not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None
            or not isinstance(head, str) or re.fullmatch('[0-9a-f]{40}', head) is None):
        _deny('ROOT_OR_EXACT_TASK70_ATTEMPT_REQUIRED')
    # The legacy global live flag must remain OFF for this exact pilot branch.
    if backend.LIVE_CUTOVER_ENABLED is not False:
        _deny('GLOBAL_BACKEND_STATE_NOT_PILOT_SEALED')
    if console.source_guard(root) != head:
        _deny('PUBLISHED_HEAD_DRIFT')
    for rel in CRITICAL:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            _deny('SOURCE_MISSING_OR_SYMLINK')
        try:
            cp = subprocess.run(['git', 'show', head + ':' + rel], cwd=root,
                                stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=25, check=False)
        except (OSError, subprocess.SubprocessError):
            _deny('GIT_SOURCE_UNAVAILABLE')
        if cp.returncode != 0 or cp.stdout != path.read_bytes():
            _deny('SOURCE_BYTES_NOT_EQUAL_PUBLISHED_HEAD')
    # R083: direct owner/PAM route may not bypass the prepared provider freeze.
    # This path is invoked before password and again after root owner claim.
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination.control_plane.worker_runtime import cf10_r083_frozen_epoch_gate_v0_1 as epoch
    inp = runtime / 'forprint_system_blueprint' / WORKER / attempt / 'input'
    try:
        source = cycle._load_yaml(inp / 'governed_worker_cycle_source_state_v0_1.yaml', 'source state')
        prepared = cycle._load_yaml(inp / 'governed_worker_cycle_prepared_execution_v0_1.yaml', 'prepared execution')
        decision = cycle._load_yaml(inp / 'governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml', 'dispatch decision')
        cycle._assert_frozen_source_state_current(root, source, boundary='R083 owner-PAM provider freeze')
        epoch.assert_launch_epoch(root=root, source_state=source, prepared=prepared,
                                  decision=decision, attempt_id=attempt, worker_id=WORKER)
    except Exception as exc:
        # Do not expose source, argv, prompts, secrets or frozen content.
        _deny('PROVIDER_EPOCH_GATE_BLOCKED:' + type(exc).__name__)


def assert_before_password(*, root: Path, runtime: Path, task: str, attempt: str, head: str) -> None:
    """Read-only readiness, never consumes a claim or triggers PAM."""
    _source(root=root, runtime=runtime, task=task, attempt=attempt, head=head)
    from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as bound
    bound.assert_pre_password(root=root, runtime_root=runtime,
                              task=task, attempt=attempt, head=head)


def assert_after_owner_claim(*, root: Path, runtime: Path, task: str, attempt: str,
                             head: str) -> None:
    """Recheck immutable root state after PAM+claim and before any systemd start.

    Caller cannot inject facts; reads source, contextvar, claim, proof, writer,
    frozen context, ledger and systemd state from existing canonical code.
    """
    _source(root=root, runtime=runtime, task=task, attempt=attempt, head=head)
    from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
    from scripts.coordination.control_plane import cf10_r054_pilot_postworker_gate_v0_1 as post
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as proof
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    session = owner._SESSION.get()
    if (session is None or session.phase != 'INNER_ENTERED' or
            (session.task, session.attempt, session.head) != (task, attempt, head)):
        _deny('OWNER_PAM_INNER_SESSION_REQUIRED')
    post._consumed_owner_claim(task=task, attempt=attempt, head=head)
    snap = preclaim.inspect(root=root, task=task, attempt=attempt, head=head)
    if snap.get('preclaim_root_receipt_verified') is not True or snap.get('blockers') != []:
        _deny('ROOT_PRECLAIM_INVALID')
    release = proof.inspect(root=root, task=task, attempt=attempt, phase='LAUNCH_WINDOW')
    if (release.get('status') != 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED'
            or release.get('checks', {}).get('r047_source_lineage') != 'EXACT_RAW_BYTES_BOUND'
            or release.get('blockers') != [] or release.get('launch_allowed') is not False):
        _deny('INDEPENDENT_PROOF_CANDIDATE_INVALID')
    owner._cycle_preclaim(root, runtime, task, attempt)
    if writer.load_enforced_protocol(required=True) is None:
        _deny('WRITER_LOCK_NOT_ENFORCED')
    current = cycle.status(root=root, runtime_root=runtime,
                           task_prompt_id=task, attempt_id=attempt, worker_id=WORKER)
    if (current.get('state') != 'READY_FOR_WORKER_LAUNCH' or
            current.get('derived_non_authoritative') is not True or current.get('contradictions')):
        _deny('CANONICAL_ATTEMPT_NO_LONGER_READY')
    store = ledger.store_root(root, ledger.load_contract(root), None)
    if ledger.records_for_attempt(store, attempt):
        _deny('CANONICAL_LEDGER_ALREADY_STARTED')
    if admission._systemd_quiescent()[0] is not True:
        _deny('SYSTEMD_WORKER_NOT_QUIESCENT')


def requirements() -> dict:
    return {'schema_version': SCHEMA,
            'status': 'SOURCE_BOUND_PILOT_BRANCH_IMPLEMENTED_PROOFS_NOT_ISSUED',
            'legacy_make_quarantine_unchanged': True,
            'global_backend_live_flag': False,
            'pre_password_guard': True,
            'post_claim_pre_systemd_guard': True,
            'root_technical_proofs_issued_by_this_module': False,
            'root_preclaim_issued_by_this_module': False,
            'production_worker_launched': False,
            'automatic_retry': False,
            'launch_allowed': False,
            'next_action': 'OBTAIN_INDEPENDENTLY_VERIFIED_ORIGINAL_EXPERIMENT_PROOFS_AND_EXACT_ATTEMPT_BEFORE_OWNER_PAM'}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=('requirements',), required=True)
    ap.parse_args(argv)
    print(json.dumps(requirements(), sort_keys=True, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
