#!/usr/bin/env python3
"""CF10 R145: independent root-side manifest/release readback before IPC.

Only the canonical R030 root actor can mint a release marker. This module
reconstructs its bounded manifest identity from root-owned on-disk inodes,
then rereads the *same* pinned systemd/cgroup invocation. It cannot prove
that the gate-entry actually exec'd Copilot, nor does it permit a launch,
open a socket, accept Worker Result or terminalize a ledger.

R140's public IPC forwarding MUST call this live proof, never trust a
worker-supplied dict. The existing disposable R125 laboratory relay remains
private; no production listener or G1-G5 authority is created.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kernel
from scripts.coordination.control_plane.worker_runtime import cf10_r141_held_ipc_bridge_origin_v0_1 as r141

SCHEMA='cf10_r145_canonical_root_release_readback_v0_1'
NONCE=re.compile(r'[0-9a-f]{64}\Z')
SHA256=NONCE
MANIFEST=re.compile(r'manifest-([0-9a-f]{64})\.json\Z')
ROOT_RELEASE=re.compile(r'release-([0-9a-f]{64})\.json\Z')
MAX_ENTRIES=512
MANIFEST_KEYS={
    'schema','attempt_id','source_head','argv','argv_sha256','cwd','unit',
    'gate_nonce','expires_unix','runner_uid','runner_gid',
}
RELEASE_KEYS={'schema','manifest_sha256'}

class ReleaseHold(RuntimeError):
    pass

def deny(why:str)->None:
    raise ReleaseHold('CF10_R145_HOLD_'+why)


def _canonical(doc:dict)->bytes:
    return (json.dumps(doc,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')


def _trusted_record(dirfd:int,name:str,limit:int,owner_uid:int)->tuple[bytes,dict]:
    """Root-owned single-link regular inode, no symlinks, no partial read."""
    if not (MANIFEST.fullmatch(name) or ROOT_RELEASE.fullmatch(name)):
        deny('RECORD_NAME')
    try:
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=dirfd)
    except OSError:
        deny('RECORD_MISSING_OR_SYMLINK')
    try:
        a=os.fstat(fd)
        if (not stat.S_ISREG(a.st_mode) or a.st_uid!=owner_uid or
            stat.S_IMODE(a.st_mode)!=0o644 or a.st_nlink!=1 or
            not 1<=a.st_size<=limit):
            deny('RECORD_INODE')
        raw=os.read(fd,limit+1)
        b=os.fstat(fd)
        props=lambda st:(st.st_dev,st.st_ino,st.st_uid,st.st_gid,st.st_mode,st.st_nlink,
            st.st_size,st.st_mtime_ns,st.st_ctime_ns)
        if props(a)!=props(b) or len(raw)!=a.st_size:
            deny('RECORD_CHANGED_WHILE_READ')
        try:
            obj=json.loads(raw)
        except (ValueError,UnicodeError):
            deny('RECORD_JSON')
        if type(obj) is not dict or raw!=_canonical(obj):
            deny('RECORD_NONCANONICAL_OR_DUPLICATE_JSON')
        return raw,obj
    finally:
        os.close(fd)


def _inspect_root_release_files(*,spec:binding.BoundedInput,unit:str,
                                gate_root:Path,owner_uid:int)->dict:
    """Private pure disk readback; fixture use never constitutes root authority.

    Public production review always supplies launcher.GATES and uid=0.
    Tests may supply a disposable directory/owner to exercise real inode rules.
    """
    if (type(spec) is not binding.BoundedInput or type(unit) is not str or
        not isinstance(gate_root,Path) or not gate_root.is_absolute() or
        type(owner_uid) is not int or owner_uid<0):
        deny('INPUT_TYPE')
    try:
        dfd=os.open(gate_root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    except OSError:
        deny('GATE_DIRECTORY_UNAVAILABLE')
    try:
        ds=os.fstat(dfd)
        pathstat=gate_root.lstat()
        if (not stat.S_ISDIR(ds.st_mode) or ds.st_uid!=owner_uid or
            stat.S_IMODE(ds.st_mode)!=0o711 or gate_root.is_symlink() or
            (ds.st_dev,ds.st_ino)!=(pathstat.st_dev,pathstat.st_ino)):
            deny('GATE_DIRECTORY_OWNER_MODE')
        entries=os.listdir(dfd)
        if len(entries)>MAX_ENTRIES:
            deny('GATE_DIRECTORY_UNBOUNDED')
        matches=[]
        for filename in entries:
            named=MANIFEST.fullmatch(filename)
            if named is None:
                continue
            raw,doc=_trusted_record(dfd,filename,launcher.MANIFEST_MAX_BYTES,owner_uid)
            if set(doc)!=MANIFEST_KEYS or doc.get('schema')!='cf10_systemd_launch_manifest_v0_1':
                deny('MANIFEST_SCHEMA')
            nonce=named.group(1)
            if doc['gate_nonce']!=nonce or not NONCE.fullmatch(nonce):
                deny('MANIFEST_NONCE')
            # Unrelated historical attempts are ignored only AFTER root-owned
            # inode and strict canonical record format have been checked.
            if doc['attempt_id']!=spec.attempt_id:
                continue
            if (doc['source_head']!=spec.source_head or doc['unit']!=unit or
                doc['cwd']!=spec.workspace or doc['argv']!=list(spec.argv) or
                doc['argv_sha256']!=hashlib.sha256('\0'.join(spec.argv).encode()).hexdigest() or
                type(doc['expires_unix']) not in (int,float) or
                not math.isfinite(doc['expires_unix']) or doc['expires_unix']<=0 or
                doc['runner_uid']!=binding.UID or doc['runner_gid']!=binding.GID):
                deny('MANIFEST_FROZEN_IDENTITY_DRIFT')
            matches.append((nonce,hashlib.sha256(raw).hexdigest()))
        if len(matches)!=1:
            deny('MANIFEST_ABSENT_OR_AMBIGUOUS')
        nonce,digest=matches[0]
        filename='release-'+nonce+'.json'
        _,release=_trusted_record(dfd,filename,512,owner_uid)
        if (set(release)!=RELEASE_KEYS or release.get('schema')!='cf10_root_release_v0_1'
                or release.get('manifest_sha256')!=digest):
            deny('RELEASE_MARKER_NOT_BOUND_TO_MANIFEST')
        return {'gate_nonce_sha256':hashlib.sha256(nonce.encode('ascii')).hexdigest(),
            'manifest_sha256':digest,'release_marker_sha256':hashlib.sha256(_canonical(release)).hexdigest(),
            'root_owned_manifest_and_release_readback':True}
    finally:
        os.close(dfd)


def review_pre_forward(*,spec:binding.BoundedInput,plan:dict,
                       witness:kernel.KernelWitness,held_review:dict)->dict:
    """Independently reread R030 release marker AND live kernel invocation.

    The caller must supply the in-process canonical R030 witness, NOT a
    serialized Worker report. This method is the mandatory public R140 gate.
    """
    if os.geteuid()!=0:
        deny('ROOT_REQUIRED')
    if type(spec) is not binding.BoundedInput or type(plan) is not dict or type(held_review) is not dict:
        deny('FROZEN_INPUT_TYPES')
    try:
        binding.validate_plan(plan,spec)
    except (binding.BoundaryBlocked,TypeError,KeyError,ValueError):
        deny('FROZEN_PLAN')
    unit=plan.get('identity',{}).get('unit')
    if (type(witness) is not kernel.KernelWitness or witness.closed or
        witness.armed_populated!='1' or witness.unit!=unit or
        type(witness.invocation_id) is not str or
        not kernel.INVOKE.fullmatch(witness.invocation_id)):
        deny('WITNESS_NOT_PINNED')
    if (held_review.get('schema_version')!=r141.SCHEMA or
        held_review.get('state')!='HELD_R030_R135_PRE_RELEASE_REVIEW_ONLY' or
        held_review.get('attempt_id')!=spec.attempt_id or
        held_review.get('source_head')!=spec.source_head or
        held_review.get('unit')!=unit or
        held_review.get('systemd_invocation_id')!=witness.invocation_id or
        any(held_review.get(k) is not False for k in ('live_worker_authorized',
            'worker_result_accepted','terminal_ledger_written','g1_g5_closed',
            'automatic_retry'))):
        deny('HELD_REVIEW_NOT_EXACT')
    proof=_inspect_root_release_files(spec=spec,unit=unit,gate_root=launcher.GATES,owner_uid=0)
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    try:
        observed=kernel.show(unit,route._trusted_runner)
        populated=kernel.read_fd(witness.fd)
    except (kernel.WitnessBlocked,OSError,ValueError,TypeError):
        deny('POST_RELEASE_KERNEL_READBACK')
    if (observed.get('Id')!=unit or observed.get('InvocationID')!=witness.invocation_id or
        observed.get('ControlGroup')!='/system.slice/'+unit or
        observed.get('ActiveState')!='active' or
        observed.get('User')!='forprint-runner' or observed.get('Group')!='forprint-runner' or
        observed.get('KillMode')!='control-group' or populated!='1'):
        deny('POST_RELEASE_SYSTEMD_INVOCATION_DRIFT')
    return {'schema_version':SCHEMA,
        'state':'R030_ROOT_RELEASE_MARKER_AND_PINNED_INVOCATION_REVIEW_ONLY',
        'attempt_id':spec.attempt_id,'source_head':spec.source_head,
        'unit':unit,'systemd_invocation_id':witness.invocation_id,
        **proof,'worker_executed_proven':False,'copilot_process_tree_proven':False,
        'credential_isolation_attested':False,'copilot_egress_attested':False,
        'g1_g5_closed':False,'live_worker_authorized':False,
        'worker_result_accepted':False,'terminal_ledger_written':False,
        'automatic_retry':False}


def source_check()->int:
    if (launcher.LIVE_CUTOVER_ENABLED is not False or
        launcher.GATES!=Path('/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/control_plane/launch_gates') or
        launcher.MANIFEST_MAX_BYTES!=131072):
        deny('SOURCE_CANONICAL_RELEASE_GATE_DRIFT')
    print('CF10_R145_ROOT_RELEASE=READ_ONLY_CANONICAL_MANIFEST_RELEASE_INODE_AND_KERNEL')
    print('CF10_R145_WORKER_EXEC=UNPROVEN_NO_ADMISSION')
    print('CF10_R145_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('source-check',),required=True)
    p.parse_args()
    try:return source_check()
    except ReleaseHold as exc:
        print(str(exc));return 3

if __name__=='__main__':raise SystemExit(main())
