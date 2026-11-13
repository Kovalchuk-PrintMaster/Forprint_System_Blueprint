"""CF10 r051: root-owned create-once PRECLAIM witness, never launch authority.

PRECLAIM is collected while Make/backend quarantine is intact. At LAUNCH_WINDOW
only this exact sealed record is verified; r045.collect must not be re-run.
Source SHA, Work Front, running worker, lock, ledger, proof and PAM are checked
separately at actual launch. This is a provenance boundary, not cutover wiring.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Mapping

from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase

SCHEMA = 'cf10_r051_root_preclaim_receipt_v0_1'
PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
WORKER = 'worker-01'
ISSUE_CONFIRM = 'SEAL_CF10_TASK70_ROOT_PRECLAIM_NONAUTHORIZING'
MAX_BYTES = 32768
SOURCE_GUARDS = (
    'Makefile',
    'scripts/coordination/control_plane/cf10_r045_pilot_admission_v0_1.py',
    'scripts/coordination/control_plane/cf10_r046_pilot_cutover_review_v0_1.py',
    'scripts/coordination/control_plane/cf10_r050_two_phase_pilot_v0_1.py',
    'scripts/coordination/control_plane/cf10_r051_root_preclaim_receipt_v0_1.py',
)
EXPECTED_FIELDS = frozenset({
    'schema_version', 'status', 'profile', 'worker_id', 'task_prompt_id',
    'attempt_id', 'source_head', 'captured_utc', 'r045_report', 'snapshot',
    'permission_consumed', 'root_receipt_is_launch_authority',
    'automatic_retry', 'production_cutover', 'worker_launched',
})

class PreclaimBlocked(RuntimeError):
    pass


def _deny(code: str) -> None:
    raise PreclaimBlocked(code)


def _canonical(doc: Mapping) -> bytes:
    return (json.dumps(dict(doc), sort_keys=True, separators=(',', ':'),
                       ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')


def _decode(raw: bytes) -> dict:
    def unique(pairs):
        output = {}
        for k, v in pairs:
            if k in output:
                _deny('DUPLICATE_RECEIPT_FIELD')
            output[k] = v
        return output
    try:
        obj = json.loads(raw, object_pairs_hook=unique,
                         parse_constant=lambda value: _deny('INVALID_JSON_CONSTANT'))
    except (ValueError, UnicodeDecodeError):
        _deny('INVALID_RECEIPT_JSON')
    if not isinstance(obj, dict) or raw != _canonical(obj):
        _deny('RECEIPT_NON_CANONICAL_BYTES')
    return obj


def _name(attempt: str) -> str:
    if not isinstance(attempt, str) or phase.ATTEMPT.fullmatch(attempt) is None:
        _deny('ATTEMPT_ID_INVALID')
    key = hashlib.sha256((WORKER + '\0' + attempt).encode('utf-8')).hexdigest()
    return 'owner_preclaim_' + key + '.json'


def _exact_source_bytes(root: Path, head: str) -> None:
    """Pin r051 and all dependent code to published HEAD (not just console.CRITICAL)."""
    if not isinstance(head, str) or phase.HEAD.fullmatch(head) is None:
        _deny('PUBLISHED_SOURCE_HEAD_INVALID')
    for rel in SOURCE_GUARDS:
        file = root / rel
        if not file.is_file() or file.is_symlink():
            _deny('PRECLAIM_CRITICAL_SOURCE_UNAVAILABLE')
        try:
            cp = subprocess.run(['git', 'show', head + ':' + rel],
                                cwd=root, check=False, capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            _deny('PRECLAIM_GIT_OBJECT_UNAVAILABLE')
        if cp.returncode != 0 or file.read_bytes() != cp.stdout:
            _deny('PRECLAIM_CRITICAL_SOURCE_DRIFT')


def _state_fd() -> int:
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    return once.open_root_owned_state_dir()


def _record_fd(folder: int, name: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    fd = os.open(name, flags, dir_fd=folder)
    try:
        st = os.fstat(fd)
        if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or
                stat.S_IMODE(st.st_mode) != 0o600 or
                st.st_size <= 0 or st.st_size > MAX_BYTES or st.st_nlink != 1):
            _deny('ROOT_PRECLAIM_RECORD_UNTRUSTED')
        raw = os.read(fd, st.st_size + 1)
        if len(raw) != st.st_size:
            _deny('ROOT_PRECLAIM_RECORD_READ_RACE')
        after = os.fstat(fd)
        if (st.st_ino, st.st_dev, st.st_size, st.st_mtime_ns) != (
                after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns):
            _deny('ROOT_PRECLAIM_RECORD_CHANGED_DURING_READ')
        return raw
    finally:
        os.close(fd)


def _verify_document(doc: Mapping, *, task: str, attempt: str, head: str) -> dict:
    if not isinstance(doc, Mapping) or set(doc) != EXPECTED_FIELDS:
        _deny('PRECLAIM_RECEIPT_FIELDS_INVALID')
    expected = {'schema_version': SCHEMA, 'status': 'SEALED_PRECLAIM_NON_AUTHORIZING',
                'profile': phase.PROFILE, 'worker_id': WORKER,
                'task_prompt_id': phase.TASK, 'attempt_id': attempt,
                'source_head': head, 'permission_consumed': False,
                'root_receipt_is_launch_authority': False,
                'automatic_retry': False, 'production_cutover': False,
                'worker_launched': False}
    for key, value in expected.items():
        if type(doc.get(key)) is not type(value) or doc[key] != value:
            _deny('ROOT_PRECLAIM_' + key.upper() + '_INVALID')
    if task != phase.TASK or phase.ATTEMPT.fullmatch(attempt) is None or \
            phase.HEAD.fullmatch(head) is None:
        _deny('EXACT_TASK70_HEAD_ATTEMPT_REQUIRED')
    captured = doc.get('captured_utc')
    if not isinstance(captured, str) or len(captured) > 45:
        _deny('CAPTURE_TIMESTAMP_INVALID')
    try:
        stamp = datetime.fromisoformat(captured)
        if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
            _deny('CAPTURE_TIMESTAMP_NOT_UTC')
    except ValueError:
        _deny('CAPTURE_TIMESTAMP_INVALID')
    report, snapshot = doc.get('r045_report'), doc.get('snapshot')
    if not isinstance(report, dict) or not isinstance(snapshot, dict):
        _deny('PRECLAIM_REPORT_OR_SNAPSHOT_MISSING')
    independently_derived = phase.preclaim(report=report, source_head=head,
                                          task=task, attempt=attempt)
    if independently_derived.get('status') != 'PRECLAIM_SNAPSHOT_CANDIDATE_NON_AUTHORIZING':
        _deny('R045_PRECLAIM_REPORT_INVALID')
    if snapshot != independently_derived:
        _deny('ROOT_PRECLAIM_SNAPSHOT_HASH_OR_FIELDS_MISMATCH')
    return dict(snapshot)


def read_verified(*, folder: int, task: str, attempt: str, head: str) -> dict:
    """Verify exact immutable root-owned bytes. Never call r045.collect."""
    if task != phase.TASK or not isinstance(head, str) or phase.HEAD.fullmatch(head) is None:
        _deny('EXACT_TASK70_SOURCE_REQUIRED')
    raw = _record_fd(folder, _name(attempt))
    return _verify_document(_decode(raw), task=task, attempt=attempt, head=head)


def inspect(*, root: Path, task: str, attempt: str, head: str | None = None) -> dict:
    """Read-only, fail-closed; this is not release or worker authority."""
    blockers: list[str] = []
    current_head = ''
    try:
        if root.resolve(strict=True) != PROJECT:
            _deny('NON_CANONICAL_PROJECT_ROOT')
        if head is None:
            from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
            current_head = console.source_guard(root)
        else:
            current_head = head
        _exact_source_bytes(root, current_head)
        folder = _state_fd()
        try:
            snapshot = read_verified(folder=folder, task=task, attempt=attempt, head=current_head)
        finally:
            os.close(folder)
        if snapshot.get('r045_quarantine_fact_frozen') is not True:
            _deny('QUARANTINE_FACT_NOT_FROZEN')
    except (OSError, ValueError, TypeError, KeyError, PreclaimBlocked) as exc:
        code = str(exc) if isinstance(exc, PreclaimBlocked) else 'ROOT_PRECLAIM_UNAVAILABLE_OR_UNTRUSTED'
        blockers.append(code)
    return {
        'schema_version': SCHEMA,
        'status': ('PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING' if not blockers
                   else 'BLOCKED_PRECLAIM_ROOT_RECEIPT'),
        'task_prompt_id': task,
        'attempt_id': attempt,
        'source_head': current_head,
        'blockers': blockers,
        'preclaim_root_receipt_verified': not blockers,
        'r045_recollected_after_cutover': False,
        'launch_allowed': False,
        'permission_consumed': False,
        'worker_launched': False,
        'production_cutover': False,
    }


def _lock_fd(folder: int) -> int:
    """Share the existing owner launch mutex; do not create a second authority."""
    flags = (os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
             | getattr(os, 'O_CLOEXEC', 0))
    fd = os.open('owner_launch.lock', flags, 0o600, dir_fd=folder)
    st = os.fstat(fd)
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or
            stat.S_IMODE(st.st_mode) != 0o600 or st.st_nlink != 1):
        os.close(fd)
        _deny('OWNER_LAUNCH_LOCK_UNTRUSTED')
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd


def _write_create_once(folder: int, name: str, raw: bytes) -> None:
    if not 0 < len(raw) <= MAX_BYTES:
        _deny('PRECLAIM_RECEIPT_TOO_LARGE')
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
             | getattr(os, 'O_CLOEXEC', 0))
    try:
        fd = os.open(name, flags, 0o600, dir_fd=folder)
    except FileExistsError:
        _deny('PRECLAIM_ALREADY_EXISTS_NO_REWRITE')
    try:
        with os.fdopen(fd, 'wb', closefd=True) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(folder)
    except OSError:
        # No deletion: even a partial file remains a deliberate fail-closed boundary.
        _deny('PRECLAIM_WRITE_UNCERTAIN_NO_RETRY')


def issue(*, root: Path, task: str, attempt: str, confirm: str) -> dict:
    """Privileged evidence capture ONLY; never authenticate launch or consume claim."""
    if (confirm != ISSUE_CONFIRM or os.geteuid() != 0 or
            root.resolve(strict=True) != PROJECT or task != phase.TASK):
        _deny('ROOT_CANONICAL_EXPLICIT_CONFIRM_REQUIRED')
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
    if phase.ATTEMPT.fullmatch(attempt) is None:
        _deny('NEW_ATTEMPT_ID_REQUIRED')
    head = console.source_guard(root)
    _exact_source_bytes(root, head)
    folder = _state_fd()
    try:
        lock = _lock_fd(folder)
        try:
            name = _name(attempt)
            # Do not call r045 or create credentials if an attempt already sealed.
            try:
                os.stat(name, dir_fd=folder, follow_symlinks=False)
                _deny('PRECLAIM_ALREADY_EXISTS_NO_REWRITE')
            except FileNotFoundError:
                pass
            report = r045.collect(root, task, attempt)
            snapshot = phase.preclaim(report=report, source_head=head, task=task, attempt=attempt)
            if snapshot.get('status') != 'PRECLAIM_SNAPSHOT_CANDIDATE_NON_AUTHORIZING':
                _deny('R045_PRECLAIM_NOT_READY')
            if console.source_guard(root) != head:
                _deny('SOURCE_DRIFT_DURING_PRECLAIM')
            _exact_source_bytes(root, head)
            doc = {
                'schema_version': SCHEMA, 'status': 'SEALED_PRECLAIM_NON_AUTHORIZING',
                'profile': phase.PROFILE, 'worker_id': WORKER, 'task_prompt_id': task,
                'attempt_id': attempt, 'source_head': head,
                'captured_utc': datetime.now(timezone.utc).isoformat(),
                'r045_report': report, 'snapshot': snapshot,
                'permission_consumed': False, 'root_receipt_is_launch_authority': False,
                'automatic_retry': False, 'production_cutover': False, 'worker_launched': False,
            }
            _verify_document(doc, task=task, attempt=attempt, head=head)
            _write_create_once(folder, name, _canonical(doc))
            # Root-owned bytes are independently read back; no trust in in-memory doc.
            read_verified(folder=folder, task=task, attempt=attempt, head=head)
        finally:
            os.close(lock)
    finally:
        os.close(folder)
    return {'schema_version': SCHEMA, 'status': 'SEALED_ROOT_PRECLAIM_NON_AUTHORIZING',
            'task_prompt_id': task, 'attempt_id': attempt, 'source_head': head,
            'preclaim_root_receipt_verified': True, 'worker_launched': False,
            'permission_consumed': False, 'launch_allowed': False,
            'production_cutover': False,
            'next_action': 'SEPARATE_PILOT_PROOF_AND_LAUNCH_WINDOW_REVIEW'}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=('issue', 'inspect'))
    ap.add_argument('--root', type=Path, default=Path('.'))
    ap.add_argument('--task-prompt-id', default='')
    ap.add_argument('--attempt-id', default='')
    ap.add_argument('--confirm', default='')
    args = ap.parse_args(argv)
    try:
        if args.action == 'issue':
            result = issue(root=args.root, task=args.task_prompt_id,
                           attempt=args.attempt_id, confirm=args.confirm)
        else:
            result = inspect(root=args.root, task=args.task_prompt_id,
                             attempt=args.attempt_id)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0 if not result.get('blockers') else 2
    except (OSError, ValueError, TypeError, KeyError, PreclaimBlocked) as exc:
        print('CF10_R051_BLOCKED=' + (str(exc) if isinstance(exc, PreclaimBlocked)
                                      else 'ROOT_PRECLAIM_UNAVAILABLE_OR_UNTRUSTED'),
              file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
