"""Opt-in, operator-provisioned shared writer guard for canonical attempt ledger.

The repository cannot enable itself as a ledger writer protocol. If the external,
root-controlled configuration is absent, existing append behavior stays unchanged
and Closeout Apply must fail closed. A present but invalid configuration always
raises; it never silently falls back to unlocked writes.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import stat
from pathlib import Path
from typing import Iterator

import yaml

PROTOCOL_PATH = Path('/etc/forprint/execution_attempt_writer_protocol_v0_1.yaml')
APPROVED_LOCK_DIRECTORY = Path('/run/forprint')
TRUSTED_OWNER_UID = 0
SCHEMA = 'forprint_execution_attempt_writer_protocol_v0_1'

class WriterProtocolError(RuntimeError):
    pass


def _checked_regular(path: Path, *, owner: int, label: str) -> bytes:
    try:
        st = path.lstat()
    except FileNotFoundError as exc:
        raise WriterProtocolError(label + '_MISSING') from exc
    if not stat.S_ISREG(st.st_mode) or st.st_uid != owner or (st.st_mode & 0o022):
        raise WriterProtocolError(label + '_UNSAFE')
    # Refuse symlink substitution between lstat and open.
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
    fd = os.open(path, flags)
    try:
        st_fd = os.fstat(fd)
        if (st.st_dev, st.st_ino) != (st_fd.st_dev, st_fd.st_ino):
            raise WriterProtocolError(label + '_REPLACED')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def load_enforced_protocol(*, required: bool = False) -> dict | None:
    """Load external policy, never from the repository/CLI/Worker output."""
    try:
        PROTOCOL_PATH.lstat()
    except FileNotFoundError:
        if required:
            raise WriterProtocolError('SHARED_WRITER_PROTOCOL_NOT_PROVISIONED')
        return None
    # The configuration directory itself must not be replaceable by a
    # non-root principal. Absent config is legacy; unsafe config is blocking.
    config_dir = PROTOCOL_PATH.parent
    try:
        parent_st = config_dir.lstat()
    except FileNotFoundError as exc:
        raise WriterProtocolError('SHARED_WRITER_CONFIG_DIRECTORY_MISSING') from exc
    if (not stat.S_ISDIR(parent_st.st_mode) or parent_st.st_uid != TRUSTED_OWNER_UID
            or (parent_st.st_mode & 0o022)):
        raise WriterProtocolError('SHARED_WRITER_CONFIG_DIRECTORY_UNSAFE')
    raw = _checked_regular(PROTOCOL_PATH, owner=TRUSTED_OWNER_UID,
                           label='SHARED_WRITER_PROTOCOL')
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise WriterProtocolError('SHARED_WRITER_PROTOCOL_INVALID_YAML') from exc
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA or data.get('state') != 'ENFORCED':
        raise WriterProtocolError('SHARED_WRITER_PROTOCOL_INVALID')
    named = data.get('lock_path')
    if not isinstance(named, str) or not named:
        raise WriterProtocolError('SHARED_WRITER_LOCK_PATH_INVALID')
    path = Path(named)
    if (not path.is_absolute() or path.parent != APPROVED_LOCK_DIRECTORY
            or path.name in ('.', '..') or path.name.startswith('.')):
        raise WriterProtocolError('SHARED_WRITER_LOCK_PATH_NOT_APPROVED')
    parent = path.parent
    try:
        st_dir = parent.lstat()
    except FileNotFoundError as exc:
        raise WriterProtocolError('SHARED_WRITER_LOCK_DIRECTORY_MISSING') from exc
    if not stat.S_ISDIR(st_dir.st_mode) or st_dir.st_uid != TRUSTED_OWNER_UID or (st_dir.st_mode & 0o022):
        raise WriterProtocolError('SHARED_WRITER_LOCK_DIRECTORY_UNSAFE')
    # If file exists, refuse symlinks and directories; never replace it.
    try:
        st_lock = path.lstat()
    except FileNotFoundError:
        pass
    else:
        if not stat.S_ISREG(st_lock.st_mode):
            raise WriterProtocolError('SHARED_WRITER_LOCK_FILE_UNSAFE')
    return {'lock_path': path, 'sha256': hashlib.sha256(raw).hexdigest(), 'raw': raw}


@contextlib.contextmanager
def guarded_canonical_append() -> Iterator[None]:
    """Serialize scan/validate/create across all correctly enrolled writers."""
    active = load_enforced_protocol()
    if active is None:
        yield
        return
    path = active['lock_path']
    fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
                 | getattr(os, 'O_CLOEXEC', 0), 0o660)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise WriterProtocolError('SHARED_WRITER_LOCK_DESCRIPTOR_UNSAFE')
        fcntl.flock(fd, fcntl.LOCK_EX)
        # A mid-flight protocol replacement cannot silently change lock identity.
        current = load_enforced_protocol(required=True)
        if current['sha256'] != active['sha256'] or current['lock_path'] != path:
            raise WriterProtocolError('SHARED_WRITER_PROTOCOL_CHANGED_UNDER_LOCK')
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
