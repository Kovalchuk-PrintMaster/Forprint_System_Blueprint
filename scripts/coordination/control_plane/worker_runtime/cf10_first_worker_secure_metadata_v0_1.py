#!/usr/bin/env python3
"""CF-10 AA: root-only credential metadata audit, no contents or authority.

Only directory file descriptors are opened (O_DIRECTORY | O_NOFOLLOW), never
credential files. Follows no ancestor symlinks; verifies root-owned, immutable
for unprivileged users, and exact mode/ownership/regular-file link count.
A PASS is not usable authentication, release, or provider non-exposure proof.
"""
from __future__ import annotations
import os
from pathlib import Path
import stat
from typing import Optional

SCHEMA = 'cf10_first_worker_secure_metadata_v0_1'
FORBIDDEN_TOP = frozenset(('tmp', 'run', 'proc', 'sys', 'dev'))

class MetadataHold(ValueError):
    pass

def deny(reason: str) -> None:
    raise MetadataHold('CF10_AA_METADATA_HOLD_' + reason)

def empty_record() -> dict:
    return {'source':'UNCONFIGURED','root_owns_material':False,
            'group_or_world_access':False,'material_read':False,
            'passed_to_cli_env':False,'passed_to_child_tools':False,
            'credential_exchange_attested':False}

def _validate_path(raw: Path, *, project_root: Path) -> tuple[str,...]:
    if not isinstance(raw, Path) or not raw.is_absolute() or not isinstance(project_root,Path):
        deny('ABSOLUTE_PATH_REQUIRED')
    name = str(raw)
    if len(name)>400 or '\x00' in name or '\n' in name or '\r' in name or '\\' in name:
        deny('PATH_ENCODING')
    parts = raw.parts
    if len(parts)<3 or parts[0]!='/' or any(p in ('', '.', '..') for p in parts[1:]):
        deny('PATH_COMPONENTS')
    if parts[1] in FORBIDDEN_TOP or (parts[1]=='var' and len(parts)>2 and parts[2] in ('tmp','run')):
        deny('EPHEMERAL_OR_DEVICE_SCOPE')
    root = str(project_root).rstrip('/')
    if name==root or name.startswith(root+'/'):
        deny('REPOSITORY_SCOPE')
    return parts[1:]

def inspect_credential_metadata(path: Optional[Path], *, project_root: Path) -> dict:
    """No credential bytes are opened, read, copied, hashed or serialized."""
    if path is None:
        return empty_record()
    path=Path(path)
    parts=_validate_path(path,project_root=project_root)
    fd=None
    try:
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        base=os.fstat(fd)
        if not stat.S_ISDIR(base.st_mode) or base.st_uid!=0 or (stat.S_IMODE(base.st_mode)&0o022):
            deny('ROOT_DIRECTORY_OWNER_MODE')
        for segment in parts[:-1]:
            newer=os.open(segment,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
            os.close(fd);fd=newer
            info=os.fstat(fd)
            if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or (stat.S_IMODE(info.st_mode)&0o022):
                deny('ANCESTOR_OWNER_OR_WRITE_PERMISSION')
        parent=os.fstat(fd)
        if stat.S_IMODE(parent.st_mode)&0o077:
            deny('DIRECT_PARENT_NOT_PRIVATE')
        fileinfo=os.stat(parts[-1],dir_fd=fd,follow_symlinks=False)
        if (not stat.S_ISREG(fileinfo.st_mode) or fileinfo.st_uid!=0 or fileinfo.st_gid!=0
                or stat.S_IMODE(fileinfo.st_mode)!=0o600 or fileinfo.st_nlink!=1
                or not 0<fileinfo.st_size<16384):
            deny('HANDLE_OWNER_MODE_TYPE_SIZE')
    except MetadataHold:
        raise
    except (OSError,ValueError,TypeError,NotImplementedError):
        deny('PATH_INODE_UNVERIFIED')
    finally:
        if fd is not None:
            os.close(fd)
    return {'source':'ROOT_EXTERNAL_HANDLE_REVIEW_ONLY','root_owns_material':True,
            'group_or_world_access':False,'material_read':False,
            'passed_to_cli_env':False,'passed_to_child_tools':False,
            'credential_exchange_attested':False}


def source_check() -> dict:
    if empty_record()['credential_exchange_attested'] is not False:
        deny('AUTHORITY')
    for p in (Path('/tmp/a'),Path('/run/a'),Path('/var/tmp/a'),Path('/dev/a'),
              Path('relative'),Path('/root/../etc/example')):
        try:inspect_credential_metadata(p,project_root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'))
        except MetadataHold:pass
        else:deny('PATH_REJECTION_FAIL')
    return {'schema':SCHEMA,'source_audit':'PASS_METADATA_ONLY',
            'credential_bytes_read':False,'provider_auth_proven':False,
            'live_worker_authorized':False,'g1_g5_open':True}

if __name__ == '__main__':
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-check'],required=True);p.parse_args()
    print(json.dumps(source_check(),sort_keys=True))
