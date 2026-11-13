"""CF-10 candidate: derive content delta without consulting worker-controlled Git.

This module does not grant authority, authorize attempts, terminate processes,
read ledger secrets or promote changes. All candidate bytes are untrusted.
A caller MUST independently prove process-tree quiescence before using results.
No Git subprocess, Git index or .git metadata is read from the worker checkout.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = 'cf10_untrusted_worktree_snapshot_v0_1'
MAX_ENTRIES = 20000
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_FILE_BYTES = 32 * 1024 * 1024
SKIP_ROOT_GIT = '.git'
GIT_ALLOW = frozenset(('.gitignore', '.gitattributes', '.github', '.gitmodules'))

class UntrustedTreeBlocked(RuntimeError):
    pass


def _deny(msg: str) -> None:
    raise UntrustedTreeBlocked('CF10_UNTRUSTED_TREE_' + msg)


def _name_ok(name: str, *, root: bool = False) -> None:
    if (not name or name in ('.', '..') or '/' in name or '\x00' in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)):
        _deny('UNSAFE_NAME')
    if name == '.git':
        _deny('NESTED_GIT_METADATA' if not root else 'ROOT_GIT_NOT_SKIPPED')
    if name.startswith('.git') and name not in GIT_ALLOW:
        _deny('GIT_METADATA_RENAMED_OR_RESERVED')


@dataclass
class _Budget:
    count: int = 0
    total_bytes: int = 0


def _read_file_at(fd: int, name: str, expected: os.stat_result,
                  budget: _Budget) -> str:
    if (expected.st_size > MAX_FILE_BYTES or expected.st_size < 0
            or budget.total_bytes + expected.st_size > MAX_TOTAL_BYTES):
        _deny('SIZE_LIMIT')
    if expected.st_nlink != 1:
        _deny('HARDLINK_FORBIDDEN')
    if stat.S_IMODE(expected.st_mode) & 0o7000:
        _deny('SPECIAL_PERMISSION_BITS')
    if stat.S_IMODE(expected.st_mode) & 0o002:
        _deny('WORLD_WRITABLE_FILE')
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
    f = os.open(name, flags, dir_fd=fd)
    try:
        observed = os.fstat(f)
        if (not stat.S_ISREG(observed.st_mode) or
                (observed.st_dev, observed.st_ino) !=
                (expected.st_dev, expected.st_ino) or observed.st_nlink != 1):
            _deny('FILE_RACED_OR_UNSAFE')
        h = hashlib.sha256()
        seen = 0
        while True:
            chunk = os.read(f, 1024 * 1024)
            if not chunk:
                break
            seen += len(chunk)
            if seen > MAX_FILE_BYTES or budget.total_bytes + seen > MAX_TOTAL_BYTES:
                _deny('FILE_BUDGET_EXCEEDED')
            h.update(chunk)
        after = os.fstat(f)
        if ((after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                != (observed.st_dev, observed.st_ino, observed.st_size,
                    observed.st_mtime_ns, observed.st_ctime_ns)
                or seen != observed.st_size):
            _deny('FILE_CHANGED_DURING_SCAN')
        budget.total_bytes += seen
        return h.hexdigest()
    finally:
        os.close(f)


def snapshot_tree(worktree: Path | str) -> dict[str, Any]:
    """Fail-closed path-anchored scan; ignores only the root .git entry.

    Not race-proof against *other* surviving writers. Use only after separately
    proven process quiescence. This deliberate limitation blocks production use.
    """
    root = Path(worktree)
    if not root.is_absolute() or root == Path('/'):
        _deny('UNBOUND_ROOT')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    root_fd = os.open(str(root), flags)
    items: dict[str, dict[str, Any]] = {}
    budget = _Budget()
    try:
        def walk(fd: int, prefix: str, *, depth: int = 0) -> None:
            if depth > 64:
                _deny('DEPTH_LIMIT')
            names = os.listdir(fd)
            for name in sorted(names):
                if not prefix and name == SKIP_ROOT_GIT:
                    # Do not inspect, execute, traverse or trust metadata, regardless
                    # of its current type or content.
                    continue
                _name_ok(name, root=(not prefix))
                budget.count += 1
                if budget.count > MAX_ENTRIES:
                    _deny('ENTRY_LIMIT')
                path = f'{prefix}/{name}' if prefix else name
                st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                mode = stat.S_IMODE(st.st_mode)
                if stat.S_ISDIR(st.st_mode):
                    if mode & (0o7000 | 0o002):
                        _deny('UNSAFE_DIR_MODE')
                    child_fd = os.open(name, flags, dir_fd=fd)
                    try:
                        observed = os.fstat(child_fd)
                        if (observed.st_dev, observed.st_ino) != (st.st_dev, st.st_ino):
                            _deny('DIRECTORY_RACED')
                        walk(child_fd, path, depth=depth + 1)
                    finally:
                        os.close(child_fd)
                elif stat.S_ISREG(st.st_mode):
                    digest = _read_file_at(fd, name, st, budget)
                    items[path] = {'sha256': digest, 'executable': bool(mode & 0o111)}
                else:
                    _deny('SYMLINK_OR_SPECIAL_FILE')
        walk(root_fd, '')
    finally:
        os.close(root_fd)
    payload = {'schema_version': SCHEMA, 'files': items,
               'entry_count': budget.count, 'total_file_bytes': budget.total_bytes,
               'git_metadata_consulted': False, 'authority_granted': False}
    payload['content_sha256'] = hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
    ).encode()).hexdigest()
    return payload


def compare_snapshots(trusted_baseline: dict[str, Any],
                      candidate: dict[str, Any], *,
                      process_quiescence_proven: bool = False) -> dict[str, Any]:
    """Diff two independent file snapshots, never grant promotion authority.

    The caller-supplied quiescence flag alone is not itself reliable evidence;
    a later governed integration must bind a root-controlled process receipt.
    """
    if process_quiescence_proven is not True:
        _deny('PROCESS_TREE_QUIESCENCE_NOT_PROVEN')
    for data in (trusted_baseline, candidate):
        if not isinstance(data, dict) or data.get('schema_version') != SCHEMA:
            _deny('SCHEMA_MISMATCH')
        fields = dict(data)
        digest = fields.pop('content_sha256', None)
        check = hashlib.sha256(json.dumps(
            fields, sort_keys=True, separators=(',', ':'), ensure_ascii=False
        ).encode()).hexdigest()
        if digest != check or fields.get('git_metadata_consulted') is not False:
            _deny('SNAPSHOT_INTEGRITY_INVALID')
    before = trusted_baseline['files']
    after = candidate['files']
    if not isinstance(before, dict) or not isinstance(after, dict):
        _deny('FILES_INVALID')
    created = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    modified = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
    return {
        'schema_version': 'cf10_independent_worktree_delta_candidate_v0_1',
        'created_paths': created,
        'removed_paths': removed,
        'modified_paths': modified,
        'changed_paths': sorted(created + removed + modified),
        'baseline_sha256': trusted_baseline['content_sha256'],
        'post_sha256': candidate['content_sha256'],
        'candidate_metadata_trusted': False,
        'external_process_quiescence_required': True,
        'root_git_invoked_in_candidate': False,
        'authority_granted': False,
        'promotion_allowed': False,
    }
