"""Executed by systemd as forprint-runner. Never run work before a root-owned release.

Standalone stdlib entry point; -I -B, no PYTHONPATH, no shell, no root secrets.
An absent/invalid gate ALWAYS means no user-provided Worker argv is executed.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

ROOT=Path('/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/control_plane/launch_gates')
HEX=re.compile(r'[0-9a-f]{64}\Z')

class GateBlocked(RuntimeError):
    pass

def _deny(s):raise GateBlocked('CF10_GATE_'+s)

def _safe_file(path:Path, maxlen=16384)->bytes:
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o644 or st.st_nlink!=1:
            _deny('UNTRUSTED_ROOT_FILE')
        data=os.read(fd,maxlen+1)
        if len(data)>maxlen:_deny('ROOT_FILE_TOO_LARGE')
        return data
    finally:os.close(fd)

def _read_manifest(path:Path, *, root:Path=ROOT, check_uid=True):
    if not isinstance(path,Path) or path.parent!=root or not re.fullmatch(r'manifest-[0-9a-f]{64}\.json',path.name):
        _deny('MANIFEST_PATH_SCOPE')
    if not root.is_absolute() or root.is_symlink() or root.resolve()!=root:
        _deny('GATE_DIR_PATH')
    st=root.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o711:
        _deny('GATE_DIR_OWNER_MODE')
    if check_uid and os.geteuid()==0:_deny('RUNNER_NOT_ROOT_REQUIRED')
    raw=_safe_file(path)
    try:obj=json.loads(raw)
    except (ValueError,UnicodeError):_deny('MANIFEST_JSON')
    keys={'schema','attempt_id','source_head','argv','argv_sha256','cwd','unit','gate_nonce','expires_unix','runner_uid','runner_gid'}
    if not isinstance(obj,dict) or set(obj)!=keys or obj['schema']!='cf10_systemd_launch_manifest_v0_1':
        _deny('MANIFEST_SCHEMA')
    if not HEX.fullmatch(obj['gate_nonce']):_deny('GATE_NONCE')
    if not isinstance(obj['argv'],list) or not obj['argv'] or len(obj['argv'])>50 or not all(
        isinstance(s,str) and 0<len(s)<2000 and not any(c in s for c in ('\0','\r','\n')) for s in obj['argv']):
        _deny('ARGV')
    if hashlib.sha256('\0'.join(obj['argv']).encode()).hexdigest()!=obj['argv_sha256']:_deny('ARGV_DIGEST')
    if not re.fullmatch(r'cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}',obj['attempt_id']):_deny('ATTEMPT')
    if not re.fullmatch(r'[0-9a-f]{40}',obj['source_head']):_deny('HEAD')
    expected='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+obj['attempt_id']+'/workspace/repo'
    if obj['cwd']!=expected or not Path(expected).is_dir():_deny('WORKSPACE')
    cursor=Path('/')
    for component in Path(expected).parts[1:]:
        cursor=cursor/component
        if cursor.is_symlink():_deny('WORKSPACE_SYMLINK')
    if not isinstance(obj['expires_unix'],(float,int)) or isinstance(obj['expires_unix'],bool):_deny('EXPIRY')
    if obj['expires_unix']-time.time()>180 or time.time()>=obj['expires_unix']:_deny('EXPIRED')
    if type(obj['runner_uid'])!=int or type(obj['runner_gid'])!=int or obj['runner_uid']<1 or obj['runner_gid']<1:
        _deny('RUNNER_ID')
    if check_uid and (os.geteuid()!=obj['runner_uid'] or os.getegid()!=obj['runner_gid']):
        _deny('RUNNER_UID_GID')
    if not re.fullmatch(r'forprint-cf10-worker-[0-9a-f]{24}\.service',obj['unit']):_deny('UNIT')
    if not os.path.isabs(obj['argv'][0]) or '..' in Path(obj['argv'][0]).parts or not obj['argv'][0].startswith(('/usr/bin/','/usr/local/bin/','/bin/')):
        _deny('EXECUTABLE')
    return raw,obj

def wait_and_exec(path:Path,*,root:Path=ROOT,poll=0.2):
    """Fail closed on release absent/mismatch; successful release replaces process via execv."""
    raw,doc=_read_manifest(path,root=root)
    digest=hashlib.sha256(raw).hexdigest()
    release=root/('release-'+doc['gate_nonce']+'.json')
    while time.time()<doc['expires_unix']:
        try:blob=_safe_file(release,maxlen=512)
        except FileNotFoundError:
            time.sleep(poll)
            continue
        try:record=json.loads(blob)
        except ValueError:_deny('RELEASE_JSON')
        if record!={'schema':'cf10_root_release_v0_1','manifest_sha256':digest}:
            _deny('RELEASE_BINDING')
        # no shell; process stays in same systemd cgroup and UID/GID.
        os.chdir(doc['cwd'])
        os.execv(doc['argv'][0],doc['argv'])
    _deny('RELEASE_NOT_SEEN_BEFORE_DEADLINE')

def main(argv:list[str])->int:
    if len(argv)!=1:_deny('CLI_ARGS')
    try:wait_and_exec(Path(argv[0]))
    except (GateBlocked,OSError) as exc:
        # No credentials or contents of manifest to logs.
        print('CF10_WORKER_GATE_BLOCKED='+type(exc).__name__,file=sys.stderr,flush=True)
        return 73
    return 73

if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
