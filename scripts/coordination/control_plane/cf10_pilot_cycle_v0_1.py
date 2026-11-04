"""CF-10 Task70 project-native orchestration (no independent launch authority).

Uses existing governed_worker_cycle, owner-PAM console, r045/r046/r051,
S3 and canonical Make targets.  Never treats a projection or historical proof
as an authorization.  A consumed owner claim is permanently non-retryable.

No production dependency on tmp/.  No acceptance, promotion, commit, push or
release implementation.  The independent 22-proof reviewer is not reproduced.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
WORKER = 'worker-01'
ATTEMPT_RE = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')
SCHEMA = 'cf10_project_native_pilot_cycle_v0_1'
MAX_STEPS = 7

class PilotBlocked(RuntimeError):
    pass


def deny(reason: str) -> None:
    raise PilotBlocked(reason)


def validate_selector(root: Path, runtime: Path, task: str, attempt: str) -> None:
    if root.resolve() != PROJECT or runtime.resolve() != RUNTIME:
        deny('EXACT_CANONICAL_ROOT_RUNTIME_REQUIRED')
    if task != TASK or not ATTEMPT_RE.fullmatch(attempt):
        deny('EXACT_TASK70_ATTEMPT_REQUIRED')


def _head(root: Path) -> str:
    cp = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root,
                        capture_output=True, text=True, timeout=20, check=True)
    value = cp.stdout.strip()
    if not re.fullmatch('[0-9a-f]{40}', value):
        deny('CURRENT_GIT_HEAD_INVALID')
    return value


def frozen_head(runtime: Path, attempt: str) -> str | None:
    """Only the frozen source-state record may declare this attempt's HEAD."""
    import yaml
    path = (runtime / 'forprint_system_blueprint' / WORKER / attempt /
            'input/governed_worker_cycle_source_state_v0_1.yaml')
    if path.is_symlink() or not path.is_file():
        return None
    doc = yaml.safe_load(path.read_bytes())
    if not isinstance(doc, dict):
        deny('FROZEN_SOURCE_STATE_MALFORMED')
    value = doc.get('git_head')
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value):
        deny('FROZEN_SOURCE_HEAD_MALFORMED')
    return value


def _root_store_health(runtime: Path) -> str:
    """Never provision a root-owned state store implicitly during a launch."""
    store = runtime / 'forprint_system_blueprint/control_plane/root_receipts'
    if store.is_symlink() or not store.is_dir():
        return 'ROOT_RECEIPT_STORE_MISSING_OR_UNSAFE'
    st = store.stat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o700:
        return 'ROOT_RECEIPT_STORE_NOT_ROOT_0700'
    return 'PASS'


def _logs_health(runtime: Path, attempt: str) -> str:
    folder = runtime / 'forprint_system_blueprint' / WORKER / attempt / 'logs'
    if folder.is_symlink():
        return 'LOG_DIRECTORY_SYMLINK_UNTRUSTED'
    if not folder.exists():
        return 'LOG_DIRECTORY_MISSING'
    if not folder.is_dir():
        return 'LOG_DIRECTORY_NOT_DIRECTORY'
    st = folder.stat()
    if st.st_uid != 0 or stat.S_IMODE(st.st_mode) & 0o022:
        return 'LOG_DIRECTORY_PERMISSIONS_UNTRUSTED'
    for name in ('stdout.log', 'stderr.log'):
        path = folder / name
        if path.exists() or path.is_symlink():
            return 'LOG_FILE_ALREADY_PRESENT_NO_RETRY'
    return 'PASS'


def assert_owner_preclaim_runtime(*, root: Path, runtime: Path,
                                  task: str, attempt: str, head: str) -> None:
    """Canonical owner invokes this both before PAM and inside its lock.

    Read-only; no claim, privilege grant, tmp dependency or proof issuance.
    """
    validate_selector(root, runtime, task, attempt)
    if _head(root) != head or frozen_head(runtime, attempt) != head:
        deny('FROZEN_HEAD_SOURCE_CHANGED_NO_CLAIM')
    if _root_store_health(runtime) != 'PASS':
        deny('ROOT_RECEIPT_STORE_NOT_PROVISIONED_NO_CLAIM')
    if _logs_health(runtime, attempt) != 'PASS':
        deny('LOGS_NOT_READY_BEFORE_CLAIM:' + _logs_health(runtime, attempt))
    _assert_static_argv_boundary(attempt, head, runtime)
    _assert_actual_frozen_invocation(root, runtime, task, attempt, head)


def _safe_runtime_parent(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        deny('RUNTIME_PARENT_UNTRUSTED')
    st = path.stat()
    if st.st_uid != 0 or st.st_mode & 0o022:
        deny('RUNTIME_PARENT_NOT_ROOT_CONTROLLED')


def provision_runtime(root: Path, runtime: Path, task: str, attempt: str,
                      confirm: str) -> dict[str, Any]:
    """One idempotent pre-claim operation, explicitly entered via Make.

    Creates only two named missing directories. Does not modify any existing
    receipt, worker process, ledger, claim, unit, identity, PAM or sudoers.
    """
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    validate_selector(root, runtime, task, attempt)
    if (os.geteuid() != 0 or confirm != 'PROVISION_EXACT_CF10_PILOT_RUNTIME_PRECLAIM'
            or not os.isatty(0) or not os.isatty(1)):
        deny('EXPLICIT_ROOT_TTY_RUNTIME_PROVISION_REQUIRED')
    head = console.source_guard(root)
    state = snapshot(root, runtime, task, attempt)
    if (state['source_head'] != head or state['frozen_head'] != head or
            state['state'] != 'READY_FOR_WORKER_LAUNCH' or
            state['claim'] != 'UNCONSUMED' or state['ledger_records'] != 0):
        deny('PRECLAIM_RUNTIME_PROVISION_NOT_SAFE')
    store_parent = runtime / 'forprint_system_blueprint/control_plane'
    _safe_runtime_parent(store_parent)
    attempt_root = runtime / 'forprint_system_blueprint' / WORKER / attempt
    _safe_runtime_parent(attempt_root)
    store = store_parent / 'root_receipts'
    logs = attempt_root / 'logs'
    created = []
    for directory, label in ((store, 'root_receipts'), (logs, 'logs')):
        if not directory.exists() and not directory.is_symlink():
            os.mkdir(directory, 0o700)
            created.append(label)
        if directory.is_symlink() or not directory.is_dir():
            deny('RUNTIME_PROVISION_DIRECTORY_UNTRUSTED:' + label)
    if _root_store_health(runtime) != 'PASS' or _logs_health(runtime, attempt) != 'PASS':
        deny('RUNTIME_PROVISION_READBACK_FAILED')
    return {'status': 'RUNTIME_PRECLAIM_PROVISIONED_NON_AUTHORIZING',
            'created': created, 'attempt_id': attempt,
            'claim_consumed': False, 'worker_launched': False}


def _claim_status(attempt: str) -> str:
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    unused, reason = admission._claim_unconsumed(attempt)
    if unused is True and reason == 'NOT_CONSUMED':
        return 'UNCONSUMED'
    if unused is False and reason == 'ALREADY_CONSUMED':
        return 'CONSUMED_NO_RETRY'
    return 'UNTRUSTED:' + str(reason)


def _ledger_count(root: Path, attempt: str) -> int:
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    contract = ledger.load_contract(root)
    store = ledger.store_root(root, contract, None)
    return len(ledger.records_for_attempt(store, attempt))


def snapshot(root: Path, runtime: Path, task: str, attempt: str) -> dict[str, Any]:
    """Read-only canonical facts. Unavailable observations stay UNKNOWN, not false."""
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as proof

    validate_selector(root, runtime, task, attempt)
    head = _head(root)
    frozen = frozen_head(runtime, attempt)
    projected = cycle.status(root=root, runtime_root=runtime, task_prompt_id=task,
                             attempt_id=attempt, worker_id=WORKER)
    if projected.get('derived_non_authoritative') is not True:
        deny('CANONICAL_STATUS_NOT_MARKED_DERIVED')
    if projected.get('contradictions'):
        deny('CANONICAL_STATUS_CONTRADICTIONS')
    result: dict[str, Any] = {
        'schema_version': SCHEMA, 'task_prompt_id': task, 'attempt_id': attempt,
        'source_head': head, 'frozen_head': frozen,
        'frozen_source_current': frozen is None or frozen == head,
        'state': projected.get('state'),
        'next_boundary': projected.get('next_boundary'),
        'worker_process_started': projected.get('facts', {}).get('worker_process_started'),
        'worker_process_finished': projected.get('facts', {}).get('worker_process_finished'),
        'claim': 'UNKNOWN', 'ledger_records': None,
        'root_receipt_store': _root_store_health(runtime),
        'logs': _logs_health(runtime, attempt),
        'preclaim': 'UNKNOWN', 'proof': 'UNKNOWN',
        'automatic_retry': False, 'launch_allowed_by_report': False,
        'automatic_accept': False, 'automatic_publish': False,
    }
    # Fail closed on a source mismatch even for post-dispatch a052 after a new commit.
    try:
        result['claim'] = _claim_status(attempt)
    except Exception as exc:
        result['claim'] = 'UNKNOWN:' + type(exc).__name__
    try:
        result['ledger_records'] = _ledger_count(root, attempt)
    except Exception as exc:
        result['ledger_error'] = type(exc).__name__
    try:
        item = preclaim.inspect(root=root, task=task, attempt=attempt, head=head)
        result['preclaim'] = item.get('status', 'UNKNOWN')
        result['preclaim_blockers'] = item.get('blockers', [])
    except Exception as exc:
        result['preclaim'] = 'UNKNOWN:' + type(exc).__name__
    try:
        item = proof.inspect(root=root, task=task, attempt=attempt, phase='LAUNCH_WINDOW')
        result['proof'] = item.get('status', 'UNKNOWN')
        result['proof_blockers'] = item.get('blockers', [])
        result['proof_lineage'] = item.get('checks', {}).get('r047_source_lineage')
    except Exception as exc:
        result['proof'] = 'UNKNOWN:' + type(exc).__name__
    return result


def classify(s: dict[str, Any], *, launch_once: bool = False) -> str:
    """One universal decision table; no mutating command in this function."""
    if not s.get('frozen_source_current'):
        return 'FROZEN_SOURCE_HEAD_MISMATCH_CREATE_NEW_ATTEMPT_AFTER_PUBLICATION'
    state = s.get('state')
    if state in ('VALIDATE_CANDIDATE', 'FINALIZE_HANDOFF', 'ATTEMPT_TERMINAL',
                 'AWAITING_OPERATOR_REVIEW'):
        if s.get('worker_process_started') is True and (s.get('ledger_records') or 0) > 0:
            return 'EXISTING_S3_POSTWORKER_RESUME'
        return 'POSTWORKER_PROVENANCE_UNAVAILABLE_NO_RETRY'
    if state == 'OBSERVE_WORKER':
        return 'WAIT_FOR_WORKER_RESULT_NO_RELAUNCH'
    if s.get('claim') != 'UNCONSUMED':
        return ('OWNER_CLAIM_CONSUMED_NO_RETRY' if s.get('claim') == 'CONSUMED_NO_RETRY'
                else 'OWNER_CLAIM_UNKNOWN_FAIL_CLOSED')
    if s.get('ledger_records') is None:
        return 'CANONICAL_LEDGER_UNAVAILABLE'
    if s.get('ledger_records') != 0:
        return 'LEDGER_ALREADY_HAS_RECORDS_INSPECT_NO_RETRY'
    if state in ('RESOLVE_TASK', 'PREPARE_WORKSPACE', 'AWAITING_ASSISTANT_ACK',
                 'READY_FOR_EXPLICIT_DISPATCH'):
        return str(state)
    if state == 'READY_FOR_WORKER_LAUNCH':
        if s.get('root_receipt_store') != 'PASS' or s.get('logs') != 'PASS':
            return 'RUNTIME_PRECLAIM_PROVISION_REQUIRED'
        if s.get('preclaim') != 'PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING':
            return 'PRECLAIM_INSPECTION_REQUIRED'
        if (s.get('proof') != 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED' or
                s.get('proof_lineage') != 'EXACT_RAW_BYTES_BOUND' or s.get('proof_blockers') != []):
            return 'INDEPENDENT_ROOT_PROOF_REVIEW_REQUIRED'
        return 'EXPLICIT_CANONICAL_PAM_LAUNCH' if launch_once else 'READY_CONFIRM_LAUNCH_ONCE'
    return 'MANUAL_GOVERNANCE_REVIEW:' + str(state)


def _run_make(root: Path, runtime: Path, task: str, attempt: str,
              target: str, extra_env: dict[str, str] | None = None) -> None:
    """Mutations only through an exact, previously existing canonical target."""
    allowed = {
        'governed-worker-cycle-prepare', 'governed-worker-cycle-ack',
        'governed-worker-cycle-authorize-dispatch',
        'cf10-r051-preclaim-issue', 'cf10-s01-pilot-launch-preflight',
        'cf10-s01-pilot-owner-run', 'cf10-resume',
        'cf10-pilot-runtime-provision',
    }
    if target not in allowed:
        deny('NONCANONICAL_MAKE_TARGET')
    env = os.environ.copy()
    env.update({'PYTHONDONTWRITEBYTECODE': '1', 'GOVERNED_WORKER_TASK': task,
                'GOVERNED_WORKER_ATTEMPT': attempt,
                'GOVERNED_WORKER_RUNTIME_ROOT': str(runtime),
                'CF10_TASK': task, 'CF10_ATTEMPT': attempt})
    env.update(extra_env or {})
    cp = subprocess.run(['make', '-s', target], cwd=root, env=env, check=False)
    if cp.returncode:
        deny('CANONICAL_MAKE_FAILED:' + target + ':RC=' + str(cp.returncode))


def _prompt_gate(root: Path, task: str, attempt: str, head: str, label: str) -> None:
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    console.decision(label, task, attempt, head)


def _preclaim_absent(attempt: str) -> bool:
    """Only a verified missing file permits issuing an O_EXCL preclaim."""
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    fd = once.open_root_owned_state_dir()
    try:
        try:
            os.stat(preclaim._name(attempt), dir_fd=fd, follow_symlinks=False)
            return False
        except FileNotFoundError:
            return True
    finally:
        os.close(fd)


def _assert_static_argv_boundary(attempt: str, head: str, runtime: Path) -> None:
    """Exercise the actual r013 parser using multiline provider-shaped argv.

    A contract regression is caught BEFORE PRECLAIM/PAM/claim. This is NOT an
    actual frozen invocation plan and cannot replace the canonical backend.
    """
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013
    src = str(runtime / 'forprint_system_blueprint' / WORKER / attempt / 'workspace/repo')
    spec = r013.BoundedInput(task_prompt_id=TASK, attempt_id=attempt, source_head=head,
        handoff_sha256='a'*64, baseline_sha256='b'*64, workspace=src,
        runtime_root=str(runtime),
        argv=('/usr/bin/env', '-p', 'BOUND_COPILOT_TEST\n' + 'x'*3000,
              '--additional-mcp-config', '{"mcpServers":{}}'), timeout_seconds=60)
    r013.validate_plan(r013.bind_plan(spec), spec)


def _assert_actual_frozen_invocation(root: Path, runtime: Path, task: str,
                                     attempt: str, head: str) -> None:
    """Rebuild and validate the ACTUAL frozen Copilot invocation before claim.

    Uses the canonical launch-cycle's read-only Handoff/context/binding helpers.
    Nothing is written, launched, logged, claimed, or authorized here; sensitive
    argv/prompt and MCP configuration never enter reports or exception text.
    The real launch rebuilds this invocation under its own authority gates.
    """
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    from scripts.coordination.control_plane.worker_runtime import invocation_adapter
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger

    validate_selector(root, runtime, task, attempt)
    if _head(root) != head or frozen_head(runtime, attempt) != head:
        deny('FROZEN_SOURCE_HEAD_MISMATCH_ACTUAL_INVOCATION')
    attempt_root = runtime / 'forprint_system_blueprint' / WORKER / attempt
    inp = attempt_root / 'input'
    try:
        source = cycle._load_yaml(
            inp / 'governed_worker_cycle_source_state_v0_1.yaml', 'source state')
        prepared = cycle._load_yaml(
            inp / 'governed_worker_cycle_prepared_execution_v0_1.yaml',
            'prepared execution')
        decision = cycle._load_yaml(
            inp / 'governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml',
            'explicit dispatch decision')
        cycle._assert_frozen_source_state_current(
            root, source, boundary='CF10 project-native preclaim invocation')
        cycle._load_verified_original_handoff_manifest(
            attempt=attempt_root, prepared_execution=prepared,
            source_state=source)
        transport = cycle._resolve_stage4c_trusted_transport(
            root=root, prepared_execution=prepared,
            explicit_dispatch_decision=decision,
            expected_task_prompt_id=task, expected_attempt_id=attempt)
        readback = cycle._resolve_b3_trusted_readback(
            root=root, prepared_execution=prepared,
            explicit_dispatch_decision=decision,
            expected_task_prompt_id=task, expected_attempt_id=attempt)
        started, task_context = cycle._project_native_started_record(
            canonical=root, attempt=attempt_root,
            task_prompt_id=task, attempt_id=attempt, worker_id=WORKER,
            source_state=source, prepared_execution=prepared,
            explicit_dispatch_decision=decision)
        governed_context = cycle._validated_project_native_governed_worker_context(
            prepared_execution=prepared, explicit_dispatch_decision=decision)
        # This is the same provider adapter and exact argument set used by
        # governed_worker_cycle.launch_cycle; no synthetic/pinned argv fixture.
        plan = invocation_adapter.build_launch_invocation(
            root=root, task_context=task_context,
            explicit_dispatch_decision=decision,
            attempt_root=attempt_root,
            governed_worker_context=governed_context,
            result_transport=transport,
            validation_readback_selection=readback)
        if not isinstance(plan, dict) or plan.get('attempt_id') != attempt:
            deny('ACTUAL_INVOCATION_ATTEMPT_BINDING_INVALID')
        contract = ledger.load_contract(root)
        if ledger.validate_record_data(started, contract):
            deny('ACTUAL_STARTED_LEDGER_CONTRACT_INVALID')
        baseline = cycle._load_yaml(
            attempt_root / 'evidence/worker_baseline_v0_1.yaml',
            'Worker baseline')
        launch_values = cycle._b2_find_launch_mapping(plan)
        # The real systemd canonical contract checks actual argv byte limits,
        # cwd/log paths, hashes and exact source/attempt scope.  No systemd call.
        spec, systemd_plan = route.bind_contract(
            root=root, runtime_root=runtime, task_prompt_id=task,
            attempt_id=attempt, source_head=head,
            baseline_sha256=baseline.get('baseline_fingerprint_sha256'),
            handoff_sha256=prepared.get('handoff_manifest_sha256'),
            launch_values=launch_values)
        # R075: the actual frozen provider argv MUST pass the isolated systemd
        # manifest/runner preflight before owner PAM and irreversible O_EXCL claim.
        from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
        backend.assert_frozen_manifest_preclaim(spec, systemd_plan)
    except PilotBlocked:
        raise
    except Exception as exc:
        # No raw exception text: it can contain the provider prompt/MCP JSON.
        deny('ACTUAL_FROZEN_INVOCATION_PREFLIGHT_FAILED:' + type(exc).__name__)


def advance(root: Path, runtime: Path, task: str, attempt: str,
            *, launch_once: bool = False) -> dict[str, Any]:
    """Bounded authority-aware progress. Never retries an already consumed claim."""
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    validate_selector(root, runtime, task, attempt)
    if os.geteuid() != 0 or not os.isatty(0) or not os.isatty(1):
        deny('ROOT_INTERACTIVE_TTY_REQUIRED')
    head = console.source_guard(root)
    visited: set[str] = set()
    completed: list[str] = []
    for _ in range(MAX_STEPS):
        s = snapshot(root, runtime, task, attempt)
        if s['source_head'] != head:
            deny('SOURCE_CHANGED_DURING_CYCLE')
        action = classify(s, launch_once=launch_once)
        if action in visited:
            deny('NO_PROGRESS_REPEAT_BOUNDARY:' + action)
        visited.add(action)
        if action in ('OWNER_CLAIM_CONSUMED_NO_RETRY', 'OWNER_CLAIM_UNKNOWN_FAIL_CLOSED',
                      'CANONICAL_LEDGER_UNAVAILABLE', 'LEDGER_ALREADY_HAS_RECORDS_INSPECT_NO_RETRY',
                      'FROZEN_SOURCE_HEAD_MISMATCH_CREATE_NEW_ATTEMPT_AFTER_PUBLICATION'):
            deny(action)
        if action in ('RESOLVE_TASK', 'PREPARE_WORKSPACE'):
            folder = runtime / 'forprint_system_blueprint' / WORKER / attempt
            if folder.is_symlink() or (folder.is_dir() and any(folder.iterdir())):
                deny('PARTIAL_PREPARE_REQUIRES_REVIEW')
            _run_make(root, runtime, task, attempt, 'governed-worker-cycle-prepare')
            completed.append('prepare')
        elif action == 'AWAITING_ASSISTANT_ACK':
            _prompt_gate(root, task, attempt, head, 'ACK')
            _run_make(root, runtime, task, attempt, 'governed-worker-cycle-ack',
                      {'CONFIRM_ACK': '1'})
            completed.append('ack')
        elif action == 'READY_FOR_EXPLICIT_DISPATCH':
            _prompt_gate(root, task, attempt, head, 'EXPLICIT DISPATCH')
            _run_make(root, runtime, task, attempt, 'governed-worker-cycle-authorize-dispatch',
                      {'CONFIRM_DISPATCH': '1'})
            completed.append('dispatch')
        elif action == 'RUNTIME_PRECLAIM_PROVISION_REQUIRED':
            _run_make(root, runtime, task, attempt, 'cf10-pilot-runtime-provision')
            completed.append('runtime-provision')
        elif action == 'PRECLAIM_INSPECTION_REQUIRED':
            if not _preclaim_absent(attempt):
                deny('PRECLAIM_OCCUPIED_OR_UNTRUSTED_NO_REWRITE')
            _assert_static_argv_boundary(attempt, head, runtime)
            _assert_actual_frozen_invocation(root, runtime, task, attempt, head)
            _run_make(root, runtime, task, attempt, 'cf10-r051-preclaim-issue')
            completed.append('preclaim')
        elif action == 'EXPLICIT_CANONICAL_PAM_LAUNCH':
            _assert_static_argv_boundary(attempt, head, runtime)
            _run_make(root, runtime, task, attempt, 'cf10-s01-pilot-launch-preflight')
            # Exactly one invocation: a nonzero return never triggers retry.
            _run_make(root, runtime, task, attempt, 'cf10-s01-pilot-owner-run')
            completed.append('canonical-owner-launch-once')
            return {'status': 'LAUNCH_ROUTE_RETURNED_REQUIRES_CANONICAL_READBACK',
                    'completed': completed, 'automatic_retry': False}
        elif action == 'EXISTING_S3_POSTWORKER_RESUME':
            _run_make(root, runtime, task, attempt, 'cf10-resume')
            return {'status': 'S3_RESUME_RETURNED_REVIEW_CANONICAL_RESULT',
                    'completed': completed}
        else:
            return {'status': 'PAUSED', 'next_action': action,
                    'completed': completed, 'automatic_retry': False}
    return {'status': 'PAUSED', 'next_action': 'MAX_BOUNDED_STEPS_REACHED',
            'completed': completed}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=('status', 'plan', 'run', 'resume', 'report', 'provision-runtime'))
    ap.add_argument('--root', type=Path, default=PROJECT)
    ap.add_argument('--runtime-root', type=Path, default=RUNTIME)
    ap.add_argument('--task', required=True)
    ap.add_argument('--attempt', required=True)
    ap.add_argument('--confirm-runtime', default='')
    ap.add_argument('--launch-once', action='store_true', default=False,
                    help='Enter the existing PAM/Make owner launch exactly once if all gates pass')
    args = ap.parse_args(argv)
    try:
        if args.action == 'provision-runtime':
            result = provision_runtime(args.root, args.runtime_root, args.task,
                                       args.attempt, args.confirm_runtime)
            print(json.dumps({'schema_version': SCHEMA, **result}, sort_keys=True,
                             ensure_ascii=False, indent=2))
            return 0
        s = snapshot(args.root, args.runtime_root, args.task, args.attempt)
        if args.action in ('status', 'plan', 'report'):
            if args.action != 'status':
                s['next_action'] = classify(s, launch_once=False)
            s['execution_performed'] = False
            print(json.dumps(s, sort_keys=True, ensure_ascii=False, indent=2))
            return 0
        result = advance(args.root, args.runtime_root, args.task, args.attempt,
                         launch_once=args.launch_once)
        print(json.dumps({'schema_version': SCHEMA, 'attempt_id': args.attempt,
                          **result}, sort_keys=True, ensure_ascii=False, indent=2))
        return 0
    except (PilotBlocked, RuntimeError, ValueError, OSError,
            subprocess.SubprocessError) as exc:
        # Never expose command lines; prompt/MCP JSON may contain private data.
        error = str(exc) if isinstance(exc, PilotBlocked) else type(exc).__name__
        print(json.dumps({'schema_version': SCHEMA, 'attempt_id': args.attempt,
                          'status': 'BLOCKED', 'reason': error,
                          'automatic_retry': False, 'claim_reset_performed': False},
                         ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
