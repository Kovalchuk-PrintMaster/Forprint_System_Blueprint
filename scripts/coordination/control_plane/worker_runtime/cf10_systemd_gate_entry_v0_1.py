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
MANIFEST_MAX_BYTES=131072
ARG_VECTOR_MAX_BYTES=98304

# R116: source-frozen Copilot PILOT only. Keep this standalone: systemd invokes
# this gate with python -I -B and without the repository on sys.path.
# The R115 preclaim pin MUST match; tests enforce constant synchronization.
PILOT_EXEC_PATH=Path('/usr/local/bin/forprint-copilot-1.0.107')
PILOT_EXEC_SHA256='985f0e1b1b3e734bc996324651307a076ae3deae21e3fa9f9af917983ce309c4'
PILOT_EXEC_BYTES=205458240

class GateBlocked(RuntimeError):
    pass

def _deny(s):raise GateBlocked('CF10_GATE_'+s)

def _safe_file(path:Path, maxlen=MANIFEST_MAX_BYTES)->bytes:
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or stat.S_IMODE(st.st_mode)!=0o644 or st.st_nlink!=1:
            _deny('UNTRUSTED_ROOT_FILE')
        data=os.read(fd,maxlen+1)
        if len(data)>maxlen:_deny('ROOT_FILE_TOO_LARGE')
        return data
    finally:os.close(fd)

def validate_manifest_argv(argv):
    """R013-compatible limits for the isolated gate. Do not weaken nonprompt argv."""
    if not isinstance(argv,list) or not (1 <= len(argv) <= 50):
        _deny('ARGV')
    total = 0
    for i, value in enumerate(argv):
        if not isinstance(value,str) or not value:
            _deny('ARGV')
        previous = argv[i-1] if i > 0 else ''
        prompt = previous in ('-p','--prompt')
        mcp = previous == '--additional-mcp-config'
        cap = 65536 if prompt else (8192 if mcp else 2000)
        forbidden = ('\0','\r') if prompt else ('\0','\r','\n')
        encoded = value.encode('utf-8')
        if len(encoded) > cap or any(x in value for x in forbidden):
            _deny('ARGV')
        total += len(encoded) + 1
    if total > ARG_VECTOR_MAX_BYTES:
        _deny('ARGV')
    return True


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
    validate_manifest_argv(obj['argv'])
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

def _pinned_exec_fd(path:Path, sha256:str, expected_bytes:int, *, require_root_parents:bool=True)->int:
    """Verify exact bytes on an open FD, then retain THAT FD for execve.

    The non-production arguments are for isolated unit testing only. The only
    caller from the production gate uses source-frozen constants, not manifest
    data, environment variables, CLI options or Worker-controlled policy.
    """
    if not isinstance(path,Path) or not HEX.fullmatch(sha256) or type(expected_bytes) is not int or expected_bytes<=0:
        _deny('PIN_SPEC_INVALID')
    if require_root_parents:
        if path!=PILOT_EXEC_PATH:_deny('PILOT_EXEC_SCOPE')
        for parent in (Path('/'),Path('/usr'),Path('/usr/local'),Path('/usr/local/bin')):
            try:s=parent.lstat()
            except OSError:_deny('PILOT_PARENT_UNAVAILABLE')
            if (not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or stat.S_IMODE(s.st_mode)&0o022):
                _deny('PILOT_PARENT_NOT_ROOT_CONTROLLED')
    try:fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
    except OSError:_deny('PILOT_EXEC_UNAVAILABLE_OR_LINKED')
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_size!=expected_bytes
                or not stat.S_IMODE(before.st_mode)&0o100 or stat.S_IMODE(before.st_mode)&0o022
                or before.st_nlink!=1 or (require_root_parents and before.st_uid!=0)):
            _deny('PILOT_EXEC_INODE_OR_MODE_DRIFT')
        sha=hashlib.sha256()
        remaining=expected_bytes
        while remaining:
            chunk=os.read(fd,min(1024*1024,remaining))
            if not chunk:_deny('PILOT_EXEC_SHORT_READ')
            sha.update(chunk)
            remaining-=len(chunk)
        after=os.fstat(fd)
        fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mode,s.st_uid,
                         s.st_nlink,s.st_mtime_ns,s.st_ctime_ns)
        if fields(before)!=fields(after):_deny('PILOT_EXEC_INODE_CHANGED_DURING_SHA')
        if sha.hexdigest()!=sha256:_deny('PILOT_EXEC_SHA256_MISMATCH')
        os.lseek(fd,0,os.SEEK_SET)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _exec_pinned_pilot(argv:list[str])->None:
    """No pathname re-resolution: the already verified descriptor is executed.

    An exec failure is fail-closed, never a fallback to os.execv(path) or shell.
    Passing the existing systemd environment preserves the prior execv behavior.
    """
    if argv[0]!=str(PILOT_EXEC_PATH):_deny('PILOT_EXEC_PATH_NOT_FROZEN')
    fd=_pinned_exec_fd(PILOT_EXEC_PATH,PILOT_EXEC_SHA256,PILOT_EXEC_BYTES)
    try:
        os.execve(fd,argv,dict(os.environ))
        _deny('PILOT_EXEC_RETURNED_UNEXPECTEDLY')
    finally:
        os.close(fd)


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
        # No shell; process stays in the same systemd cgroup and UID/GID.
        # Production MUST execute the source-pinned, SHA-verified OPEN FILE
        # DESCRIPTOR, never resolve the executable pathname after verification.
        # Fixture-only alternative preserves historical non-authorizing tests.
        os.chdir(doc['cwd'])
        if root==ROOT:
            _exec_pinned_pilot(doc['argv'])
        else:
            os.execv(doc['argv'][0],doc['argv'])
        _deny('EXEC_RETURNED_UNEXPECTEDLY')
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
