"""CF-10 single-operator CLI over canonical governed_worker_cycle.

This first source migration automates safe PREPARE/ACK/DISPATCH boundaries and
keeps production launch and post-worker mutation behind existing canonical
quarantines. User-approved future policy migration is NOT simulated here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import Any, Callable

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
WORKER = 'worker-01'
OPERATOR_ACCOUNT = 's01'  # from r015 intake; deliberately not an arbitrary caller flag
ID_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\Z')
ATTEMPT_RE = re.compile(r'cf10-[A-Za-z0-9][A-Za-z0-9_.-]{1,159}\Z')
ROOT_TMP = Path('tmp/cf10_operator_console')
CRITICAL = (
    'Makefile',
    'scripts/coordination/control_plane/governed_worker_cycle.py',
    'scripts/coordination/control_plane/cf10_s01_live_pilot_corridor_v0_1.py',
    'scripts/coordination/control_plane/cf10_owner_operator_console_v0_1.py',
    'scripts/coordination/control_plane/cf10_training_dispatch.py',
)
GATES = {
    'AWAITING_ASSISTANT_ACK': ('ack', '--confirm-ack', 'ACK: підтвердити узгоджений Handoff'),
    'READY_FOR_EXPLICIT_DISPATCH': (
        'authorize-dispatch', '--confirm-dispatch-authorization',
        'DISPATCH: санкціонувати підготовлене завдання для одного Worker',
    ),
}
STOP = {
    'READY_FOR_WORKER_LAUNCH': 'WORKER_LAUNCH_REQUIRES_SEPARATE_ACCEPTED_AUTHORITY_MIGRATION',
    'OBSERVE_WORKER': 'WORKER_PROCESS_STATUS_REVIEW_REQUIRED',
    'VALIDATE_CANDIDATE': 'POST_WORKER_BOUNDARY_REQUIRES_ACCEPTED_AUTHORITY_MIGRATION',
    'FINALIZE_HANDOFF': 'POST_WORKER_BOUNDARY_REQUIRES_ACCEPTED_AUTHORITY_MIGRATION',
    'ATTEMPT_TERMINAL': 'POST_WORKER_BOUNDARY_REQUIRES_ACCEPTED_AUTHORITY_MIGRATION',
    'AWAITING_OPERATOR_REVIEW': 'EXPLICIT_OPERATOR_RESULT_REVIEW_REQUIRED',
    'PROMOTE_CANDIDATE': 'SEPARATE_PROMOTION_AUTHORITY_REQUIRED',
    'CANONICAL_VALIDATION': 'SEPARATE_CANONICAL_VALIDATION_REQUIRED',
    'AWAITING_PUBLICATION_APPROVAL': 'EXPLICIT_PUBLICATION_AUTHORITY_REQUIRED',
    'VERIFY_REMOTE_CONTAINMENT': 'SEPARATE_PUBLICATION_VERIFICATION_REQUIRED',
    'PUBLISHED': 'ALREADY_PUBLISHED_NO_ACTION',
    'BLOCKED': 'GOVERNED_STATE_BLOCKED_NO_AUTOMATIC_RETRY',
    'UNKNOWN': 'GOVERNED_STATE_UNKNOWN_NO_AUTOMATIC_RETRY',
}

class ConsoleBlocked(RuntimeError):
    pass

def require(ok: bool, label: str) -> None:
    if not ok:
        raise ConsoleBlocked(label)

def _git(root: Path, *args: str) -> str:
    p = subprocess.run(['git', *args], cwd=root, capture_output=True, timeout=25, check=True)
    return p.stdout.decode('utf-8').strip()

def source_guard(root: Path) -> str:
    require(root.resolve() == PROJECT, 'CANONICAL_ROOT_REQUIRED')
    require(_git(root, 'branch', '--show-current') == BRANCH, 'WRONG_BRANCH')
    require(not _git(root, 'diff', '--cached', '--name-only'), 'STAGED_CHANGES_PRESENT')
    head = _git(root, 'rev-parse', 'HEAD')
    require(re.fullmatch('[0-9a-f]{40}', head) is not None, 'HEAD_INVALID')
    remote = _git(root, 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + BRANCH).split()[0]
    require(remote == head, 'REMOTE_HEAD_DRIFT')
    for rel in CRITICAL:
        live = root / rel
        require(live.is_file() and not live.is_symlink(), 'MISSING_CRITICAL_SOURCE:' + rel)
        frozen = subprocess.run(['git', 'show', head + ':' + rel], cwd=root,
                                capture_output=True, timeout=25, check=True).stdout
        require(frozen == live.read_bytes(), 'SOURCE_DRIFT:' + rel)
    return head

def ids(task: str, attempt: str) -> None:
    require(bool(ID_RE.fullmatch(task)) and bool(ATTEMPT_RE.fullmatch(attempt)), 'INVALID_TASK_OR_ATTEMPT_ID')

def temp_root(root: Path) -> Path:
    p = root / ROOT_TMP
    require(p.resolve().is_relative_to(root.resolve()), 'TEMP_PATH_ESCAPES_PROJECT')
    for node in (root / 'tmp', p):
        if node.is_symlink():
            raise ConsoleBlocked('TEMP_SYMLINK_NOT_ALLOWED')
    return p

def _private_dir(path: Path) -> None:
    if path.is_symlink():
        raise ConsoleBlocked('TEMP_SYMLINK_NOT_ALLOWED')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise ConsoleBlocked('TEMP_SYMLINK_NOT_ALLOWED')
    # Never broaden permissions if directory is already present.
    require(not stat.S_IMODE(path.stat().st_mode) & 0o022, 'TEMP_DIRECTORY_UNSAFE')

def selection_path(root: Path) -> Path:
    return temp_root(root) / 'selection.json'

def save_selection(root: Path, task: str, attempt: str) -> None:
    ids(task, attempt)
    folder = temp_root(root)
    _private_dir(folder)
    path = folder / 'selection.json'
    require(not path.exists() and not path.is_symlink() or (path.is_file() and not path.is_symlink()),
            'SELECTION_PATH_UNSAFE')
    data = json.dumps({'schema_version': 'cf10_operator_selection_v0_1',
                       'task_prompt_id': task, 'attempt_id': attempt,
                       'role': 'TEMPORARY_SELECTION_NOT_AUTHORITY'}, sort_keys=True) + '\n'
    dest = folder / ('selection.' + str(os.getpid()) + '.new')
    try:
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(dest, path)
    finally:
        if dest.exists(): dest.unlink()

def resolve_selection(root: Path, task: str, attempt: str) -> tuple[str, str]:
    if task or attempt:
        require(bool(task) and bool(attempt), 'TASK_AND_ATTEMPT_REQUIRED_TOGETHER')
        ids(task, attempt)
        return task, attempt
    path = selection_path(root)
    require(path.is_file() and not path.is_symlink(), 'NO_SELECTION_USE_CF10_CONSOLE_SELECT')
    require(path.stat().st_size <= 2048, 'SELECTION_FILE_OVERSIZE')
    doc = json.loads(path.read_bytes())
    require(isinstance(doc, dict) and doc.get('schema_version') == 'cf10_operator_selection_v0_1'
            and doc.get('role') == 'TEMPORARY_SELECTION_NOT_AUTHORITY', 'INVALID_TEMPORARY_SELECTION')
    task, attempt = doc.get('task_prompt_id'), doc.get('attempt_id')
    require(isinstance(task, str) and isinstance(attempt, str), 'INVALID_TEMPORARY_SELECTION')
    ids(task, attempt)
    return task, attempt

def status(root: Path, runtime: Path, task: str, attempt: str) -> dict[str, Any]:
    """Re-use authoritative status projection; never derive our own lifecycle facts."""
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    return cycle.status(root=root, runtime_root=runtime, task_prompt_id=task,
                        attempt_id=attempt, worker_id=WORKER)

def _step(root: Path, runtime: Path, task: str, attempt: str,
          action: str, option: str | None = None) -> dict[str, Any]:
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    kw = dict(root=root, runtime_root=runtime, attempt_id=attempt, worker_id=WORKER)
    if action == 'prepare':
        return cycle.prepare_cycle(**kw, task_prompt_id=task)
    if action == 'ack':
        return cycle.confirm_assistant_ack(**kw, confirm=True)
    if action == 'authorize-dispatch':
        return cycle.authorize_dispatch(**kw, confirm=True)
    raise ConsoleBlocked('UNSUPPORTED_CANONICAL_STEP')

def authenticate_operator(*, process: Callable[..., Any] = subprocess.run,
                          geteuid: Callable[[], int] = os.geteuid,
                          isatty: Callable[[int], bool] = os.isatty) -> None:
    """Root TTY via runuser -> unprivileged sudo/PAM prompt, never read password.

    sudo NOPASSWD is explicitly rejected because this gate must require a
    password; no sudoers mutation and no environment-supplied credentials.
    """
    require(geteuid() == 0, 'ROOT_TTY_ORCHESTRATOR_REQUIRED')
    require(isatty(0) and isatty(1), 'INTERACTIVE_TTY_REQUIRED')
    check = ['runuser', '-u', OPERATOR_ACCOUNT, '--', 'sudo', '-k', '-n', '-v']
    silent = process(check, check=False, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    require(silent.returncode != 0, 'PASSWORDLESS_SUDO_POLICY_REJECTED')
    interactive = ['runuser', '-u', OPERATOR_ACCOUNT, '--', 'sudo', '-k', '-v']
    verified = process(interactive, check=False)
    require(verified.returncode == 0, 'OPERATOR_PAM_AUTHENTICATION_FAILED')

def decision(action: str, task: str, attempt: str, head: str,
             *, authenticate: Callable[[], None] = authenticate_operator) -> None:
    """Stage-specific explicit confirmation through the system PAM password.

    This does not ask for or store a second phrase and does not grant any
    production Worker launch authority. Ctrl-C cancels the gate.
    """
    print(f'\nCF10 / {action}\nTask: {task}\nAttempt: {attempt}\nHEAD: {head[:12]}', flush=True)
    print('Для підтвердження цього етапу введи системний пароль оператора.', flush=True)
    authenticate()

def record(root: Path, task: str, attempt: str, report: dict[str, Any]) -> Path:
    """Disposable diagnostics only; source of authority remains canonical."""
    ids(task, attempt)
    folder = temp_root(root) / 'reports'
    _private_dir(temp_root(root))
    _private_dir(folder)
    document = {
        'schema_version': 'cf10_owner_console_disposable_report_v0_1',
        'task_prompt_id': task,
        'attempt_id': attempt,
        'recorded_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'authority_granted_by_report': False,
        'password_or_credential_collected': False,
        'worker_launch_performed_by_console': False,
        **report,
    }
    key = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = folder / f'{key}_{attempt}_{os.getpid()}.json'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(document, stream, sort_keys=True, ensure_ascii=False, indent=2)
        stream.write('\n')
    return path

def cleanup(root: Path, days: int = 7, now: dt.datetime | None = None) -> int:
    require(1 <= days <= 90, 'INVALID_RETENTION_DAYS')
    report_dir = temp_root(root) / 'reports'
    if not report_dir.exists(): return 0
    require(report_dir.is_dir() and not report_dir.is_symlink(), 'REPORT_DIRECTORY_UNSAFE')
    now = now or dt.datetime.now(dt.timezone.utc)
    expired = now.timestamp() - days * 86400
    count = 0
    for path in report_dir.iterdir():
        if (not path.is_file() or path.is_symlink()
                or not re.fullmatch(r'\d{8}T\d{12}Z_cf10-[A-Za-z0-9_.-]+_\d+\.json', path.name)):
            continue
        if path.stat().st_mtime < expired:
            path.unlink()
            count += 1
    return count

def transition(root: Path, runtime: Path, task: str, attempt: str, head: str,
               *, state_fn: Callable = status, step_fn: Callable = _step,
               auth_fn: Callable = authenticate_operator,
               max_steps: int = 4) -> dict[str, Any]:
    """Bounded progress; never launch, terminalize, accept or repeat a Worker."""
    completed: list[str] = []
    previous: set[str] = set()
    for _ in range(max_steps):
        current = state_fn(root, runtime, task, attempt)
        require(isinstance(current, dict) and current.get('derived_non_authoritative') is True,
                'UNTRUSTED_CYCLE_STATUS')
        state = current.get('state')
        require(isinstance(state, str), 'STATUS_STATE_MISSING')
        if state in previous:
            return dict(state='BLOCKED', blocker='NO_PROGRESS_OR_REPEATED_STATE', completed=completed)
        previous.add(state)
        print(f'CF10_STATE={state}; NEXT={current.get("next_boundary")}')
        if state in STOP:
            return dict(state=state, blocker=STOP[state], completed=completed)
        if state in ('RESOLVE_TASK', 'PREPARE_WORKSPACE'):
            attempt_folder = runtime / 'forprint_system_blueprint' / WORKER / attempt
            # Do not retry a partial prepare that might have created durable state.
            if attempt_folder.exists() and any(attempt_folder.iterdir()):
                return dict(state='BLOCKED', blocker='PARTIAL_ATTEMPT_REQUIRES_OPERATOR_REVIEW', completed=completed)
            step_fn(root, runtime, task, attempt, 'prepare')
            completed.append('prepare')
            continue
        if state in GATES:
            action, _, label = GATES[state]
            decision(label, task, attempt, head, authenticate=auth_fn)
            step_fn(root, runtime, task, attempt, action)
            completed.append(action)
            continue
        return dict(state='BLOCKED', blocker='UNRECOGNIZED_GOVERNED_STATE', completed=completed)
    return dict(state='PAUSED', blocker='MAX_BOUNDED_STEPS_REACHED', completed=completed)

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=('select', 'plan', 'status', 'run', 'resume', 'cleanup'))
    ap.add_argument('--root', type=Path, default=PROJECT)
    ap.add_argument('--runtime-root', type=Path, default=RUNTIME)
    ap.add_argument('--task-prompt-id', default='')
    ap.add_argument('--attempt-id', default='')
    ap.add_argument('--days', type=int, default=7)
    args = ap.parse_args(argv)
    root, runtime = args.root.resolve(), args.runtime_root.resolve()
    report = None
    try:
        head = source_guard(root)
        require(runtime == RUNTIME, 'CANONICAL_RUNTIME_REQUIRED')
        if args.command == 'cleanup':
            removed = cleanup(root, days=args.days)
            print('CF10_REPORTS_CLEANED=' + str(removed))
            return 0
        task, attempt = resolve_selection(root, args.task_prompt_id, args.attempt_id)
        if args.command == 'select':
            # Selection never grants launch authority.
            save_selection(root, task, attempt)
            print('CF10_SELECTION_SAVED=' + attempt)
            return 0
        initial = status(root, runtime, task, attempt)
        report = {'initial_state': initial.get('state'), 'source_head': head}
        if args.command in ('status', 'plan'):
            print(json.dumps({'task_prompt_id':task, 'attempt_id':attempt,
                              'state':initial.get('state'), 'next_boundary':initial.get('next_boundary'),
                              'plan': 'BOUNDED_OWNER_FLOW_NO_LAUNCH'}, ensure_ascii=False, sort_keys=True, indent=2))
            return 0
        # r016 deliberately does not cross the Worker launch/postworker authority migration.
        outcome = transition(root, runtime, task, attempt, head)
        report.update(outcome)
        print('CF10_CONSOLE_STATUS=' + str(outcome['state']))
        print('CF10_CONSOLE_NEXT=' + str(outcome['blocker']))
        if outcome['state'] in ('BLOCKED', 'UNKNOWN'):
            return 2
        return 0
    except (ConsoleBlocked, OSError, ValueError, RuntimeError) as exc:
        report = (report or {}) | {'state': 'BLOCKED', 'blocker':
            str(exc) if isinstance(exc, ConsoleBlocked) else 'CANONICAL_OPERATION_FAILED_REVIEW_REQUIRED'}
        print('CF10_CONSOLE_BLOCKED=' + report['blocker'], file=sys.stderr)
        return 2
    finally:
        if report and args.command in ('run', 'resume'):
            try:
                task, attempt = resolve_selection(root, args.task_prompt_id, args.attempt_id)
                path = record(root, task, attempt, report)
                print('CF10_DISPOSABLE_REPORT=' + str(path))
            except (OSError, ConsoleBlocked, ValueError):
                print('CF10_DISPOSABLE_REPORT_UNAVAILABLE', file=sys.stderr)

if __name__ == '__main__':
    raise SystemExit(main())
