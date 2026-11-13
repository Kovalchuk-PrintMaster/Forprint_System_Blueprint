"""Blueprint global tmp-independence and durable storage path contract.

Non-authorizing path validation only. Importable from Git-controlled source.
It never creates directories or grants execution authority.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat

RUNTIME_ROOT = Path('/srv/software_development/forprint-worker-runtime')
BLUEPRINT_ID = 'forprint_system_blueprint'
WORKER_ID = 'worker-01'

class StorageBoundaryBlocked(ValueError):
    pass

def deny(code: str) -> None:
    raise StorageBoundaryBlocked('BLUEPRINT_STORAGE_' + code)

def _normalized_absolute(raw: str | Path) -> Path:
    if not isinstance(raw, (str, Path)):
        deny('PATH_TYPE')
    value = str(raw)
    if (not value.startswith('/') or value == '/' or len(value) > 1024
            or '\x00' in value or '\r' in value or '\n' in value
            or '//' in value or any(c in ('.', '..') for c in value.split('/')[1:])):
        deny('PATH_AMBIGUOUS')
    path = Path(value)
    if str(path) != value:
        deny('PATH_NOT_CANONICAL')
    # Do not trust lexical containment if any existing ancestor is a symlink.
    cursor = Path('/')
    for part in path.parts[1:]:
        cursor = cursor / part
        if cursor.is_symlink():
            deny('SYMLINK_ANCESTOR')
    return path

def require_persistent_path(raw: str | Path, *, blueprint_root: str | Path) -> Path:
    """Reject temporary paths and aliasing; no filesystem changes."""
    path = _normalized_absolute(raw)
    project = _normalized_absolute(blueprint_root)
    if path == project:
        deny('PROJECT_ROOT_IS_NOT_STATE')
    if 'tmp' in path.parts or 'temp' in path.parts:
        deny('TEMP_DIRECTORY')
    if path.parts[:2] == ('/', 'var') and len(path.parts) > 2 and path.parts[2] == 'tmp':
        deny('TEMP_DIRECTORY')
    # The repository itself is for code/config, not mutable state.
    if path.is_relative_to(project):
        deny('RUNTIME_STATE_INSIDE_SOURCE_REPO')
    return path

def require_runtime_root(raw: str | Path, *, blueprint_root: str | Path) -> Path:
    path = require_persistent_path(raw, blueprint_root=blueprint_root)
    if path != RUNTIME_ROOT:
        deny('UNAPPROVED_RUNTIME_ROOT')
    return path

def require_worker_workspace(raw: str | Path, *, blueprint_root: str | Path,
                             attempt_id: str, worker_id: str = WORKER_ID) -> Path:
    if not isinstance(attempt_id, str) or not re.fullmatch(r'cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}', attempt_id):
        deny('ATTEMPT_ID')
    if worker_id != WORKER_ID:
        deny('WORKER_ID')
    path = require_persistent_path(raw, blueprint_root=blueprint_root)
    expected = RUNTIME_ROOT / BLUEPRINT_ID / WORKER_ID / attempt_id / 'workspace' / 'repo'
    if path != expected:
        deny('WORKSPACE_OUT_OF_SCOPE')
    return path

def require_root_receipt_store(raw: str | Path, *, blueprint_root: str | Path) -> Path:
    path = require_persistent_path(raw, blueprint_root=blueprint_root)
    # A dedicated root-controlled subtree of the existing runtime, not a new runtime.
    # Only validates the intended scope: owner/mode checks remain with the receipt writer.
    expected = RUNTIME_ROOT / BLUEPRINT_ID / 'control_plane' / 'root_receipts'
    if path != expected:
        deny('RECEIPT_STORE_OUT_OF_SCOPE')
    return path

def require_existing_private_store(raw: str | Path, *, blueprint_root: str | Path) -> Path:
    path = require_root_receipt_store(raw, blueprint_root=blueprint_root)
    try:
        st = path.lstat()
    except FileNotFoundError:
        deny('RECEIPT_STORE_MISSING')
    if (not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o700):
        deny('RECEIPT_STORE_PERMISSIONS')
    return path
