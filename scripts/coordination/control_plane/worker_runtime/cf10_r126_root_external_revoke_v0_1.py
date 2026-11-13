#!/usr/bin/env python3
"""CF10 R126: root-only *external* termination of a disposable R125 IPC lease.

Never creates an authority or a Worker process. A revoke only narrows access.
R125's in-broker readback is reused, with additional root/path/owner checks.
The scope is /run/forprint-cf10-r125-*/lease.json and the R125 lab schema ONLY.
Non-authorizing. Does not cancel an already forwarded operation.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import pwd
import re
import stat
import sys
if __package__:
    from scripts.coordination.control_plane.worker_runtime import cf10_r125_attempt_ipc_contract_v0_1 as r125
else:
    import importlib.util
    dep=Path(__file__).resolve().with_name('cf10_r125_attempt_ipc_contract_v0_1.py')
    if dep.is_symlink() or not dep.is_file():raise RuntimeError('CF10_R126_HOLD_DEPENDENCY')
    spec=importlib.util.spec_from_file_location('cf10_r126_pinned_r125',dep)
    if spec is None or spec.loader is None:raise RuntimeError('CF10_R126_HOLD_DEPENDENCY_SPEC')
    r125=importlib.util.module_from_spec(spec);spec.loader.exec_module(r125)

CAPSULE_ID = 'git-12c668e0cc30-sha256-5877e4f4e16fefecf16a6e50ea9e9a712d288c7e35fb726b05950226ab416de9'
LEASE_RE = re.compile(r'/run/forprint-cf10-r125-[a-f0-9]{16}/lease\.json\Z')
ID_RE = re.compile(r'[a-zA-Z0-9_.:-]{1,160}\Z')
EPOCH_RE = re.compile(r'[a-zA-Z0-9_.:-]{1,80}\Z')
SHA_RE = re.compile(r'[a-f0-9]{40}\Z')

class ExternalRevokeHold(RuntimeError): pass

def deny(code): raise ExternalRevokeHold('CF10_R126_HOLD_'+code)

def runner_gid(): return pwd.getpwnam('forprint-runner').pw_gid

def _binding(attempt,epoch,source_head,capsule_id):
    if not all(type(x) is str for x in (attempt,epoch,source_head,capsule_id)): deny('BINDING_TYPE')
    if not ID_RE.fullmatch(attempt) or not EPOCH_RE.fullmatch(epoch): deny('BINDING_ATTEMPT_EPOCH')
    if not SHA_RE.fullmatch(source_head) or capsule_id != CAPSULE_ID: deny('BINDING_SOURCE_CAPSULE')

def _safe_parent(path:Path,expected_gid:int):
    if os.geteuid()!=0: deny('ROOT_REQUIRED')
    if not isinstance(path,Path) or not path.is_absolute() or not LEASE_RE.fullmatch(str(path)): deny('LEASE_PATH')
    if type(expected_gid) is not int or expected_gid < 0: deny('RUNNER_GID')
    parent=path.parent
    try:
        st=parent.lstat()
        base=Path('/run').lstat()
    except OSError: deny('PARENT_MISSING')
    if not (stat.S_ISDIR(st.st_mode) and st.st_uid==0 and st.st_gid==expected_gid and
            stat.S_IMODE(st.st_mode)==0o710 and stat.S_ISDIR(base.st_mode) and base.st_uid==0):
        deny('PARENT_OWNER_MODE')
    try: fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    except OSError: deny('PARENT_OPEN')
    fst=os.fstat(fd)
    if (fst.st_dev,fst.st_ino)!=(st.st_dev,st.st_ino):
        os.close(fd);deny('PARENT_RACE')
    return fd

def _read_from_dir(fd):
    try: filefd=os.open('lease.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK,dir_fd=fd)
    except OSError: deny('LEASE_OPEN')
    try:
        st=os.fstat(filefd)
        if not (stat.S_ISREG(st.st_mode) and st.st_uid==0 and st.st_gid==0 and
                stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1 and 0<st.st_size<=r125.LEASE_MAX):
            deny('LEASE_OWNER_MODE')
        raw=os.read(filefd,r125.LEASE_MAX+1)
    finally: os.close(filefd)
    if len(raw)>r125.LEASE_MAX: deny('LEASE_TOO_LARGE')
    try: obj=json.loads(raw.decode('utf-8','strict'),object_pairs_hook=r125.unique)
    except (ValueError,UnicodeError,r125.BoundaryHold): deny('LEASE_FORMAT')
    if type(obj) is not dict or set(obj)!={'schema','attempt_id','epoch','source_head','capsule_id','revoked'}:
        deny('LEASE_FIELDS')
    if obj['schema']!='cf10_r125_disposable_lease_v0_1' or type(obj['revoked']) is not bool:
        deny('LEASE_SCHEMA')
    return obj

def inspect_lease(path:Path,*,attempt:str,epoch:str,source_head:str,capsule_id:str=CAPSULE_ID,
                  expected_gid:int|None=None):
    _binding(attempt,epoch,source_head,capsule_id)
    if expected_gid is None: expected_gid=runner_gid()
    fd=_safe_parent(path,expected_gid)
    try:
        obj=_read_from_dir(fd)
        if any(obj[k]!=v for k,v in {'attempt_id':attempt,'epoch':epoch,'source_head':source_head,'capsule_id':capsule_id}.items()):
            deny('LEASE_BINDING_DRIFT')
        return obj
    finally:os.close(fd)

def revoke_lease(path:Path,*,attempt:str,epoch:str,source_head:str,capsule_id:str=CAPSULE_ID,
                 expected_gid:int|None=None):
    """A separate root process may only revoke an already trusted lease.

    Not a release, claim, retry, or writer elevation. Never changes revoked back.
    The broker MUST recheck the lease before every new request; in-flight calls
    are NOT canceled by this primitive.
    """
    _binding(attempt,epoch,source_head,capsule_id)
    if expected_gid is None: expected_gid=runner_gid()
    fd=_safe_parent(path,expected_gid)
    tmpname='lease-revoke-'+str(os.getpid())+'.json'
    try:
        obj=_read_from_dir(fd)
        if any(obj[k]!=v for k,v in {'attempt_id':attempt,'epoch':epoch,'source_head':source_head,'capsule_id':capsule_id}.items()):
            deny('LEASE_BINDING_DRIFT')
        if obj['revoked'] is not False: deny('ALREADY_REVOKED')
        obj['revoked']=True
        data=r125.encode(obj)
        try:
            newfd=os.open(tmpname,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=fd)
        except OSError: deny('REVOKE_COLLISION')
        try:
            os.write(newfd,data);os.fsync(newfd)
            mode=os.fstat(newfd)
            if not (mode.st_uid==0 and mode.st_gid==0 and stat.S_IMODE(mode.st_mode)==0o600):
                deny('REVOKE_FILE_MODE')
        finally:os.close(newfd)
        # Fail closed if an external controller raced and changed the original.
        # A complete runtime broker later needs lock + fence at its call boundary.
        current=_read_from_dir(fd)
        if current!=dict(obj,revoked=False):deny('REVOKE_RACE')
        os.rename(tmpname,'lease.json',src_dir_fd=fd,dst_dir_fd=fd)
        os.fsync(fd)
        if _read_from_dir(fd)!=obj:deny('REVOKE_READBACK')
        return {'revoked':True,'authority_granted':False,'worker_launched':False,
                'new_calls_allowed':False,'attempt_id':attempt,'epoch':epoch}
    finally:
        try: os.unlink(tmpname,dir_fd=fd)
        except FileNotFoundError: pass
        os.close(fd)

def main(argv=None):
    p=argparse.ArgumentParser(description='CF10 R126 explicit root-only disposable lease revocation')
    p.add_argument('--mode',choices=['revoke'],required=True)
    p.add_argument('--lease',required=True)
    p.add_argument('--attempt',required=True)
    p.add_argument('--epoch',required=True)
    p.add_argument('--source-head',required=True)
    p.add_argument('--capsule-id',default=CAPSULE_ID)
    a=p.parse_args(argv)
    try:
        result=revoke_lease(Path(a.lease),attempt=a.attempt,epoch=a.epoch,
                            source_head=a.source_head,capsule_id=a.capsule_id)
        if result['revoked'] is not True:deny('NO_REVOKE')
    except (ExternalRevokeHold,OSError,ValueError,KeyError,TypeError) as exc:
        print('CF10_R126=HOLD_'+(str(exc) if isinstance(exc,ExternalRevokeHold) else type(exc).__name__),file=sys.stderr)
        return 3
    print('CF10_R126_EXTERNAL_ROOT_REVOKE=PASS_EXPLICIT_SEPARATE_PROCESS')
    print('CF10_R126_NO_WORKER_NO_CLAIM_NO_LIVE_RELEASE=true')
    return 0

if __name__=='__main__':raise SystemExit(main())
