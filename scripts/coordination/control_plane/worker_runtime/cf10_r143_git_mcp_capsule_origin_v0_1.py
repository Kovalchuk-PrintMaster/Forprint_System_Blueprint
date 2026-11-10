#!/usr/bin/env python3
"""R143 root-only review: exact Git commit -> root capsule -> R142 MCP pidfd.

Never launches a worker, creates a lease, authorizes IPC, appends a terminal
fact, or changes the canonical R030 release gate. A caller MUST obtain the
source commit from a separately validated canonical attempt/owner boundary.
Git data is read from that exact commit, not from a mutable working tree.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Mapping

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r141_held_ipc_bridge_origin_v0_1 as bridge_api,
    cf10_r142_canonical_mcp_child_lineage_v0_1 as child_api,
    cf10_systemd_launcher_v0_1 as launcher,
)

SCHEMA='cf10_r143_git_mcp_capsule_origin_v0_1'
ROOT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
SHA40=re.compile(r'[a-f0-9]{40}\Z')
SHA64=re.compile(r'[a-f0-9]{64}\Z')
LAB=re.compile(r'/run/forprint-cf10-r125-[0-9a-f]{16}\Z')
MAX_OBJECT=2_000_000
MAX_ALL=6_000_000
CAPSULE_FILES=(
    'scripts/__init__.py',
    'scripts/coordination/__init__.py',
    'scripts/coordination/control_plane/__init__.py',
    'scripts/coordination/control_plane/worker_runtime/__init__.py',
    'scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py',
    'scripts/coordination/control_plane/worker_runtime/structured_command_executor.py',
    'scripts/coordination/control_plane/worker_runtime/launcher.py',
    'scripts/coordination/control_plane/worker_runtime/completed_validation_discovery_v0_1.py',
    'scripts/coordination/control_plane/worker_runtime/completed_execution_readback_v0_1.py',
    'scripts/validation/__init__.py',
    'scripts/validation/run_validation_suite_v0_1.py',
    'scripts/validation/run_non_mutating_make_check.py',
    'coordination/registry/structured_command_capabilities_v0_1.yaml',
    'coordination/standards/automation/validation_suite_registry_v0_1.yaml',
)
MCP='scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py'
assert len(CAPSULE_FILES)==len(set(CAPSULE_FILES))==14
assert child_api.REL_MCP=='source_capsule/'+MCP

class CapsuleHold(RuntimeError):
    pass

def deny(why):
    raise CapsuleHold('CF10_R143_HOLD_'+why)

def _git(root:Path,*argv:str,limit:int=MAX_OBJECT)->bytes:
    if not isinstance(root,Path) or root!=ROOT or root.is_symlink() or not root.is_dir():
        deny('REPO_ROOT_NOT_PINNED')
    env={'PATH':'/usr/bin:/bin','LANG':'C','HOME':'/nonexistent',
         'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',
         'GIT_TERMINAL_PROMPT':'0','GIT_NO_REPLACE_OBJECTS':'1',
         'GIT_OPTIONAL_LOCKS':'0'}
    try:
        cp=subprocess.run(('/usr/bin/git','-C',str(root),*argv),
             stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
             env=env,timeout=8,check=False)
    except (OSError,subprocess.TimeoutExpired):
        deny('GIT_READ_UNAVAILABLE')
    if cp.returncode or len(cp.stdout)>limit:
        deny('GIT_OBJECT_UNAVAILABLE_OR_OVERSIZE')
    return cp.stdout

def _blob(root:Path,commit:str,rel:str)->tuple[bytes,str]:
    # Exact, allowlisted paths only. -- prevents pathname option injection.
    if rel not in CAPSULE_FILES or not SHA40.fullmatch(commit):
        deny('BLOB_SCOPE')
    tree=_git(root,'ls-tree','-r','-z',commit,'--',rel,limit=512)
    entries=[entry for entry in tree.split(b'\0') if entry]
    if len(entries)!=1:
        deny('BLOB_MISSING_OR_AMBIGUOUS')
    try:
        meta,name=entries[0].split(b'\t',1)
        mode,kind,blob=meta.decode('ascii').split(' ')
    except (UnicodeError,ValueError):
        deny('BLOB_TREE_FORMAT')
    if (name!=rel.encode('utf8') or kind!='blob' or mode not in ('100644','100755')
            or not SHA40.fullmatch(blob)):
        deny('BLOB_NOT_CANONICAL_REGULAR')
    data=_git(root,'cat-file','blob',blob,limit=MAX_OBJECT)
    header=('blob '+str(len(data))+'\0').encode('ascii')
    # Also independently check Git SHA-1 object encoding, including EMPTY files.
    if hashlib.sha1(header+data).hexdigest()!=blob:
        deny('BLOB_BYTES_NOT_OBJECT')
    return data,blob

def _owned_dir(p:Path)->None:
    try: s=p.lstat()
    except OSError: deny('CAPSULE_PARENT_UNAVAILABLE')
    if (not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or
            stat.S_IMODE(s.st_mode)&0o022 or p.is_symlink()):
        deny('CAPSULE_PARENT_UNSAFE')

def _capsule_path(bridge_pin:bridge_api.BridgePin)->Path:
    if type(bridge_pin) is not bridge_api.BridgePin or bridge_pin.closed:
        deny('BRIDGE_PIN_REQUIRED')
    lab=bridge_pin.source.parent
    if (not LAB.fullmatch(str(lab)) or bridge_pin.source != lab/'bridge.py'
            or str(lab.resolve()) != str(lab)):
        deny('LAB_SCOPE')
    for d in (Path('/run'),lab): _owned_dir(d)
    return lab/'source_capsule'

def _file(p:Path,cap:Path)->tuple[bytes,tuple[int,int,int,int,int,int,int]]:
    if not p.is_relative_to(cap):
        deny('FILE_ESCAPE')
    ancestor=p.parent
    while True:
        _owned_dir(ancestor)
        if ancestor==cap:break
        if ancestor==Path('/run'):
            deny('FILE_PARENT_ESCAPE')
        ancestor=ancestor.parent
    try:
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    except OSError:deny('CAPSULE_FILE_OPEN')
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=0 or
                stat.S_IMODE(before.st_mode)&0o022 or before.st_nlink!=1 or
                before.st_size>MAX_OBJECT or before.st_size<0):
            deny('CAPSULE_FILE_INODE')
        raw=os.read(fd,MAX_OBJECT+1)
        after=os.fstat(fd)
        stable=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mode,s.st_uid,s.st_mtime_ns,s.st_ctime_ns)
        if len(raw)!=before.st_size or stable(before)!=stable(after):
            deny('CAPSULE_FILE_CHANGED')
        return raw,stable(after)
    finally:os.close(fd)

def _exact_capsule_entries(cap:Path)->None:
    _owned_dir(cap)
    expected=set(CAPSULE_FILES)
    got=set()
    stack=[cap]
    visits=0
    while stack:
        current=stack.pop()
        for e in os.scandir(current):
            visits+=1
            if visits>128:deny('CAPSULE_UNBOUNDED_TREE')
            p=Path(e.path)
            if e.is_symlink():deny('CAPSULE_SYMLINK')
            if e.is_dir(follow_symlinks=False):
                _owned_dir(p)
                stack.append(p)
            elif e.is_file(follow_symlinks=False):
                rel=p.relative_to(cap).as_posix()
                if rel not in expected:deny('CAPSULE_EXTRA_FILE')
                got.add(rel)
            else:deny('CAPSULE_NONREGULAR')
    if got!=expected:deny('CAPSULE_FILESET')

def _verify_capsule(*,root:Path,commit:str,cap:Path)->dict[str,str]:
    if type(commit) is not str or not SHA40.fullmatch(commit):deny('SOURCE_COMMIT')
    if _git(root,'rev-parse','HEAD',limit=64).strip().decode('ascii')!=commit:
        deny('SOURCE_COMMIT_NOT_CURRENT_HEAD')
    if _git(root,'rev-parse','--verify',commit+'^{commit}',limit=64).strip().decode('ascii')!=commit:
        deny('SOURCE_COMMIT_NOT_GIT_COMMIT')
    _exact_capsule_entries(cap)
    sha={};total=0
    for rel in CAPSULE_FILES:
        canonical,blob=_blob(root,commit,rel)
        real,_=_file(cap/rel,cap)
        if real!=canonical:deny('CAPSULE_CONTENT_DIFFERS_FROM_GIT_'+Path(rel).name)
        sha[rel]=hashlib.sha256(real).hexdigest()
        total+=len(real)
        if total>MAX_ALL:deny('CAPSULE_TOTAL_TOO_LARGE')
    return sha

def review_git_pinned_mcp(*,bridge_pin:bridge_api.BridgePin,
       child_pin:child_api.MCPChildPin,backend_socket,
       frozen_source_commit:str,root:Path=ROOT)->dict:
    """Call in root-owned pre-IPC flow; no permission to release/forward."""
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    cap=_capsule_path(bridge_pin)
    if (type(child_pin) is not child_api.MCPChildPin or child_pin.closed or
            child_pin.bridge_pid!=bridge_pin.pid or child_pin.unit!=bridge_pin.unit or
            child_pin.source!=cap/MCP):
        deny('CHILD_PIN_SCOPE')
    # Independently re-read the kernel transport BEFORE and AFTER Git-object readback.
    try:
        first=child_api.verify_mcp_child(child_pin=child_pin,
              bridge_pin=bridge_pin,backend_socket=backend_socket)
    except (child_api.ChildHold,bridge_api.OriginHold,OSError,ValueError,TypeError):
        deny('CHILD_PRE_GIT_RECHECK')
    if (first.get('mcp_process_transport_lineage_proven') is not True or
            first.get('unit')!=bridge_pin.unit or first.get('mcp_pid')!=child_pin.pid or
            first.get('git_object_source_verified_by_independent_caller') is not False):
        deny('CHILD_TRANSPORT_UNTRUSTED')
    hashes=_verify_capsule(root=root,commit=frozen_source_commit,cap=cap)
    if hashes[MCP]!=child_pin.source_inode[3] or not SHA64.fullmatch(hashes[MCP]):
        deny('CHILD_SOURCE_NOT_GIT_BLOB')
    try:
        second=child_api.verify_mcp_child(child_pin=child_pin,
              bridge_pin=bridge_pin,backend_socket=backend_socket)
    except (child_api.ChildHold,bridge_api.OriginHold,OSError,ValueError,TypeError):
        deny('CHILD_POST_GIT_RECHECK')
    if second!=first:deny('CHILD_CHANGED_DURING_GIT_READBACK')
    return {'schema_version':SCHEMA,
       'state':'ROOT_GIT_OBJECT_TO_CAPSULE_TO_PIDFD_CHILD_REVIEW_ONLY',
       'source_commit':frozen_source_commit,'unit':bridge_pin.unit,
       'bridge_pid':bridge_pin.pid,'mcp_pid':child_pin.pid,
       'mcp_blob_sha256':hashes[MCP],
       'capsule_file_count':len(hashes),
       'capsule_manifest_sha256':hashlib.sha256(('\n'.join(k+':'+hashes[k] for k in sorted(hashes))+'\n').encode()).hexdigest(),
       'mcp_process_transport_lineage_proven':True,
       'git_object_source_verified_by_independent_caller':True,
       'root_release_readback_proven':False,
       'copilot_process_tree_proven':False,'copilot_egress_attested':False,
       'credential_isolation_attested':False,'g1_g5_closed':False,
       'live_worker_authorized':False,'worker_result_accepted':False,
       'terminal_ledger_written':False,'automatic_retry':False}

def review_post_release_git_child(*,post_review:dict,
       bridge_pin:bridge_api.BridgePin,child_pin:child_api.MCPChildPin,
       backend_socket,frozen_source_commit:str,root:Path=ROOT)->dict:
    """Compose R141 and R142 reviews; never call R030 release or IPC forward."""
    try:
        transport=child_api.review_post_release_child(post_review=post_review,
           bridge_pin=bridge_pin,child_pin=child_pin,backend_socket=backend_socket)
    except (child_api.ChildHold,bridge_api.OriginHold,OSError,TypeError,ValueError):
        deny('R141_R142_POST_JOIN')
    joined=review_git_pinned_mcp(bridge_pin=bridge_pin,child_pin=child_pin,
                  backend_socket=backend_socket,frozen_source_commit=frozen_source_commit,root=root)
    if (transport.get('root_release_readback_proven') is not False or
            transport.get('mcp_pid')!=joined['mcp_pid'] or
            transport.get('unit')!=joined['unit']):
        deny('POST_REVIEW_IDENTITY_DRIFT')
    return {'schema_version':SCHEMA,'state':'POST_RELEASE_GIT_PINNED_MCP_REVIEW_ONLY',
            'origin':joined,'root_release_readback_proven':False,
            'live_worker_authorized':False,'worker_result_accepted':False,
            'terminal_ledger_written':False,'automatic_retry':False,'g1_g5_closed':False}

def source_check()->int:
    if (launcher.LIVE_CUTOVER_ENABLED is not False or
            not hasattr(os,'pidfd_open') or len(CAPSULE_FILES)!=14):
        deny('SEALED_SOURCE_CHECK')
    print('CF10_R143_GIT_MCP=SOURCE_OBJECT_CAPSULE_CHILD_PIDFD_JOIN_REVIEW_ONLY')
    print('CF10_R143_R030_RELEASE=UNCHANGED_NO_LIVE_ADMISSION')
    print('CF10_R143_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('source-check',),required=True)
    p.parse_args()
    try:return source_check()
    except CapsuleHold as e:
        print(e);return 3

if __name__=='__main__':raise SystemExit(main())
