"""CF-10 single-owner PAM launch: exact-attempt, one password, no static signer leases.

This is a root-TTY, project-native bridge to the existing governed_worker_cycle.
It deliberately does NOT mint an activation, release, proof, or acceptance event.
A persistent O_EXCL marker prevents retrying the same attempt after any failure
past the irreversible claim. Canonical worker/ledger validators remain in charge.
It is not a security boundary against hostile Python already executing as root.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import yaml
import subprocess
from typing import Any

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
WORKER = 'worker-01'
_SHA40 = re.compile(r'[a-f0-9]{40}\Z')

class OwnerLaunchBlocked(RuntimeError):
    pass

@dataclass
class _Session:
    task: str
    attempt: str
    head: str
    phase: str = 'READY'

_SESSION: ContextVar[_Session | None] = ContextVar('cf10_owner_pam_bounded_launch', default=None)

def active() -> bool:
    return _SESSION.get() is not None

def _fail(reason: str) -> None:
    raise OwnerLaunchBlocked(reason)

def _assert_live_source(root: Path) -> str:
    """All live code-bearing guard paths must exactly match the remote HEAD."""
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    head = console.source_guard(root)
    for rel in ('coordination/continuity/cf10_sole_owner_pam_launch_policy_v0_1.yaml',
                'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py',
                'scripts/coordination/control_plane/cf10_s01_root_controlled_single_use_v0_2.py',
                'scripts/coordination/execution_attempt_writer_lock_v0_1.py',
                'scripts/coordination/execution_attempt_ledger_v0_1.py',
                'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py',
                'scripts/coordination/control_plane/worker_runtime/launcher.py'):
        live = root / rel
        if not live.is_file() or live.is_symlink():
            _fail('OWNER_CRITICAL_SOURCE_UNAVAILABLE')
        try:
            committed = subprocess.run(['git', 'show', f'{head}:{rel}'], cwd=root,
                                       capture_output=True, timeout=25, check=True).stdout
        except (OSError, subprocess.SubprocessError):
            _fail('OWNER_CRITICAL_GIT_BLOB_UNAVAILABLE')
        if live.read_bytes() != committed:
            _fail('OWNER_CRITICAL_SOURCE_DRIFT')
    policy_file = root / 'coordination/continuity/cf10_sole_owner_pam_launch_policy_v0_1.yaml'
    policy = yaml.safe_load(policy_file.read_bytes())
    expected = 'OWNER_APPROVED_EXPLICIT_TERMINAL_PASSWORD'
    if (not isinstance(policy, dict) or policy.get('status') != expected or
            policy.get('operation_mode') != 'SINGLE_OWNER_PAM_PROJECT_NATIVE' or
            policy.get('scope', {}).get('operator_unprivileged_account') != console.OPERATOR_ACCOUNT or
            policy.get('control', {}).get('nopasswd_sudo_forbidden') is not True or
            policy.get('control', {}).get('canonical_writer_lock_remains_enforced') is not True or
            policy.get('control', {}).get('claim_before_spawn_no_auto_retry') is not True):
        _fail('OWNER_ACCEPTED_POLICY_INVALID')
    return head

def require_owner_session(*, root: Path | str, task_prompt_id: str,
                          attempt_id: str, worker_id: str, route: str) -> None:
    """Both canonical Python launch entrypoints must use the same private session."""
    s = _SESSION.get()
    if s is None or os.geteuid() != 0:
        _fail('OWNER_ROOT_BOUNDED_SESSION_REQUIRED')
    if (Path(root).resolve() != PROJECT or worker_id != WORKER or
            task_prompt_id != s.task or attempt_id != s.attempt):
        _fail('OWNER_SESSION_SCOPE_MISMATCH')
    if _assert_live_source(PROJECT) != s.head:
        _fail('OWNER_SOURCE_CHANGED_INSIDE_SESSION')
    if route == 'launch_cycle' and s.phase == 'READY':
        s.phase = 'OUTER_ENTERED'
    elif route == 'launch_authorized_worker_cycle' and s.phase == 'OUTER_ENTERED':
        s.phase = 'INNER_ENTERED'
    else:
        _fail('OWNER_UNEXPECTED_LAUNCH_ROUTE')

def _cycle_preclaim(root: Path, runtime: Path, task: str, attempt: str) -> None:
    """Read-only readiness and immutable source-bound input validation."""
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    status = cycle.status(root=root, runtime_root=runtime, task_prompt_id=task,
                          attempt_id=attempt, worker_id=WORKER)
    if (status.get('derived_non_authoritative') is not True or
            status.get('state') != 'READY_FOR_WORKER_LAUNCH' or status.get('contradictions')):
        _fail('OWNER_ATTEMPT_NOT_READY_FOR_LAUNCH')
    if writer.load_enforced_protocol(required=True) is None:
        _fail('OWNER_WRITER_LOCK_PROTOCOL_NOT_ENFORCED')
    attempt_root = runtime / 'forprint_system_blueprint' / WORKER / attempt
    source_path = attempt_root / 'input/governed_worker_cycle_source_state_v0_1.yaml'
    if source_path.is_symlink() or not source_path.is_file():
        _fail('OWNER_SOURCE_STATE_UNAVAILABLE')
    source = cycle._load_yaml(source_path, 'source state')
    cycle._assert_frozen_source_state_current(root, source, boundary='owner PAM preclaim')

def _owner_claim(root: Path, task: str, attempt: str, head: str) -> str:
    """Immutable per-attempt marker; the state directory was provisioned on s01."""
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    folder = once.open_root_owned_state_dir()
    try:
        fingerprint = hashlib.sha256(f'{WORKER}\0{attempt}'.encode('utf-8')).hexdigest()
        name = 'owner_attempt_' + fingerprint + '.json'
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
        try:
            fd = os.open(name, flags, 0o600, dir_fd=folder)
        except FileExistsError:
            _fail('OWNER_ATTEMPT_ALREADY_CONSUMED_NO_RETRY')
        except OSError:
            _fail('OWNER_CLAIM_CREATE_FAILED')
        try:
            doc = {'schema_version':'cf10_owner_pam_attempt_claim_v0_1',
                   'status':'CONSUMED_BEFORE_SPAWN_NO_RETRY',
                   'worker_id':WORKER,'task_prompt_id':task,'attempt_id':attempt,
                   'source_head':head,'time_utc':datetime.now(timezone.utc).isoformat(),
                   'authority_is_password_and_operator_policy':True,
                   'automatic_retry':False}
            raw = (json.dumps(doc,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
            while raw:
                written = os.write(fd,raw)
                if written <= 0:_fail('OWNER_CLAIM_WRITE_FAILED_NO_RETRY')
                raw = raw[written:]
            os.fsync(fd)
            os.fsync(folder)
            return name
        finally:
            os.close(fd)
    finally:
        os.close(folder)

def launch_once(*, root: Path, runtime_root: Path, task_prompt_id: str,
                attempt_id: str) -> dict[str, Any]:
    """Explicit terminal password precedes claim and canonical synchronous launch.

    No injectable password callback: source-level unit tests monkeypatch the
    named canonical authentication function, not a production CLI argument.
    """
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    if os.geteuid() != 0 or Path(root).resolve() != PROJECT or Path(runtime_root).resolve() != RUNTIME:
        _fail('OWNER_ROOT_CANONICAL_ROOT_REQUIRED')
    console.ids(task_prompt_id, attempt_id)
    head = _assert_live_source(PROJECT)
    _cycle_preclaim(PROJECT, RUNTIME, task_prompt_id, attempt_id)
    print(f'CF10 / WORKER LAUNCH\nTask: {task_prompt_id}\nAttempt: {attempt_id}\nHEAD: {head[:12]}', flush=True)
    print('One attempt, no automatic retry. System operator password required.',flush=True)
    console.authenticate_operator()
    # Use root-owned existing 0700 directory; no r016 tmp artifacts are authority.
    folder = once.open_root_owned_state_dir()
    lock_flags = os.O_RDWR | os.O_CREAT | getattr(os,'O_NOFOLLOW',0) | getattr(os,'O_CLOEXEC',0)
    try:
        lock = os.open('owner_launch.lock', lock_flags, 0o600, dir_fd=folder)
        try:
            stat_lock = os.fstat(lock)
            if not stat.S_ISREG(stat_lock.st_mode) or stat_lock.st_uid != 0 or stat.S_IMODE(stat_lock.st_mode) != 0o600:
                _fail('OWNER_LOCK_FILE_UNSAFE')
            fcntl.flock(lock, fcntl.LOCK_EX)
            if _assert_live_source(PROJECT) != head:
                _fail('OWNER_SOURCE_CHANGED_AFTER_PASSWORD')
            _cycle_preclaim(PROJECT, RUNTIME, task_prompt_id, attempt_id)
            _owner_claim(PROJECT, task_prompt_id, attempt_id, head)
            session = _Session(task_prompt_id,attempt_id,head)
            token = _SESSION.set(session)
            try:
                result = cycle.launch_cycle(root=PROJECT, runtime_root=RUNTIME,
                                            task_prompt_id=task_prompt_id,
                                            attempt_id=attempt_id, worker_id=WORKER, confirm=True)
                if session.phase != 'INNER_ENTERED':
                    _fail('OWNER_INNER_ROUTE_NOT_VERIFIED_NO_RETRY')
                return {'state':'LAUNCH_RETURNED_REQUIRES_WORKER_RESULT_REVIEW',
                        'worker_spawn_claimed_by_console':False,
                        'automatic_retry':False,
                        'canonical_cycle_result_state':result.get('state') if isinstance(result,dict) else None}
            finally:
                _SESSION.reset(token)
        finally:
            os.close(lock)
    finally:
        os.close(folder)
