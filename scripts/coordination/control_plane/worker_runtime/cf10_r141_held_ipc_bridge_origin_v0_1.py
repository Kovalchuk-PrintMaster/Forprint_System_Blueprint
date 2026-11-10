#!/usr/bin/env python3
"""CF10 R141: root-pinned backend BRIDGE identity and held IPC review.

Source-only, disposable R125 lease only. No process creation, unit activation,
owner/claim/ledger writes, release or Copilot. A socket's SO_PEERCRED cannot
prove the canonical MCP child behind a bridge; neither can a root-owned file
prove effective provider/credential/egress isolation. Both remain open gates.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import os
from pathlib import Path
import re
import select
import socket
import stat
from typing import Mapping

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r135_ipc_session_fence_v0_1 as session,
    cf10_r140_root_ipc_broker_adapter_v0_1 as broker,
    cf10_systemd_kernel_witness_v0_1 as kernel,
    cf10_systemd_launcher_v0_1 as systemd,
)

SCHEMA='cf10_r141_held_ipc_bridge_origin_v0_1'
HASH=re.compile(r'[0-9a-f]{64}\Z')
INVOCATION=re.compile(r'[0-9a-f]{32}\Z')
ROOT_SCOPE=re.compile(r'/run/forprint-cf10-r125-[0-9a-f]{16}/(?:bridge\.py|source_capsule/(?:[A-Za-z0-9_./-]+\.py))\Z')
MAX_SOURCE=1048576
MAX_ARGV=16384

class OriginHold(RuntimeError):
    pass

def deny(why:str)->None:
    raise OriginHold('CF10_R141_HOLD_'+why)


def _start_ticks(pid:int)->str:
    """Kernel process start time (field 22); parentheses may occur in comm."""
    try:
        fd=os.open(f'/proc/{pid}/stat',os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try: raw=os.read(fd,8193)
        finally:os.close(fd)
    except OSError:deny('PROC_START_UNAVAILABLE')
    if not raw or len(raw)>8192 or not raw.startswith(str(pid).encode()+b' ('):
        deny('PROC_STAT_FORMAT')
    pos=raw.rfind(b') ')
    if pos<1:deny('PROC_STAT_FORMAT')
    fields=raw[pos+2:].split()
    if len(fields)<20 or not fields[19].isdigit():deny('PROC_START_FORMAT')
    return fields[19].decode('ascii')


def _proc_argv(pid:int)->tuple[str,...]:
    try:
        fd=os.open(f'/proc/{pid}/cmdline',os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try:raw=os.read(fd,MAX_ARGV+1)
        finally:os.close(fd)
    except OSError:deny('PROC_ARGV_UNAVAILABLE')
    if not raw or len(raw)>MAX_ARGV or not raw.endswith(b'\0'):
        deny('PROC_ARGV_FORMAT')
    try:return tuple(s.decode('utf8','strict') for s in raw[:-1].split(b'\0'))
    except UnicodeError:deny('PROC_ARGV_ENCODING')


def _source_identity(path:Path,expected_sha:str)->tuple[int,int,int,str]:
    if (not isinstance(path,Path) or not ROOT_SCOPE.fullmatch(str(path))
            or '..' in path.parts or type(expected_sha) is not str
            or not HASH.fullmatch(expected_sha)):
        deny('SOURCE_SCOPE_OR_HASH')
    for parent in (Path('/run'),path.parents[1] if path.name=='bridge.py' else path.parents[2]):
        try:s=parent.lstat()
        except OSError:deny('SOURCE_PARENT')
        if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022 or parent.is_symlink():
            deny('SOURCE_PARENT_OWNER')
    # Check every component below the nonce directory, not just the endpoint.
    ancestor=path.parent
    while ancestor!=Path('/run'):
        try:s=ancestor.lstat()
        except OSError:deny('SOURCE_PARENT')
        if (not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or
                stat.S_IMODE(s.st_mode)&0o022 or ancestor.is_symlink()):
            deny('SOURCE_PARENT_OWNER')
        ancestor=ancestor.parent
    try:fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
    except OSError:deny('SOURCE_UNAVAILABLE')
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=0 or
            stat.S_IMODE(before.st_mode)&0o022 or before.st_nlink!=1 or
            not 0<before.st_size<=MAX_SOURCE):
            deny('SOURCE_INODE')
        raw=os.read(fd,MAX_SOURCE+1)
        after=os.fstat(fd)
        t=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mode,s.st_uid,s.st_mtime_ns,s.st_ctime_ns)
        if t(before)!=t(after) or len(raw)!=before.st_size:
            deny('SOURCE_CHANGED_WHILE_READ')
        if hashlib.sha256(raw).hexdigest()!=expected_sha:deny('SOURCE_SHA')
        return (before.st_dev,before.st_ino,before.st_size,expected_sha)
    finally:os.close(fd)


def _exe_inode(pid:int,expected_exe:Path)->tuple[int,int]:
    if (not isinstance(expected_exe,Path) or not expected_exe.is_absolute()
        or not str(expected_exe).startswith(('/usr/bin/','/usr/local/bin/'))):
        deny('EXECUTABLE_SCOPE')
    try:
        expected=expected_exe.resolve(strict=True)
        st=expected.stat()
        observed=os.stat(f'/proc/{pid}/exe')
    except OSError:deny('EXECUTABLE_UNAVAILABLE')
    if (not stat.S_ISREG(st.st_mode) or st.st_uid!=0 or st.st_mode&0o022
       or (st.st_dev,st.st_ino)!=(observed.st_dev,observed.st_ino)):
        deny('EXECUTABLE_IDENTITY')
    return st.st_dev,st.st_ino


def _pid_alive(pidfd:int)->bool:
    try:
        poll=select.poll();poll.register(pidfd,select.POLLIN|select.POLLERR|select.POLLHUP)
        return poll.poll(0)==[]
    except (OSError,ValueError):return False


@dataclass
class BridgePin:
    pid:int
    pidfd:int
    unit:str
    start_ticks:str
    executable:Path
    executable_dev_ino:tuple[int,int]
    source:Path
    source_inode:tuple[int,int,int,str]
    source_sha256:str
    argv:tuple[str,...]
    closed:bool=False

    def close(self)->None:
        if not self.closed:
            os.close(self.pidfd);self.closed=True


def pin_backend_bridge(*,backend_socket:socket.socket,expected_pid:int,
                       unit:str,expected_executable:Path,source:Path,
                       source_sha256:str,argv:tuple[str,...])->BridgePin:
    """Root joins independently started bridge PID with actual kernel socket peer.

    Caller MUST supply PID and source SHA from its own root-controlled spawn
    inventory, not from an MCP request or Worker-produced report.
    """
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if type(expected_pid) is not int or expected_pid<2:deny('PIN_PID')
    if (type(argv) is not tuple or len(argv)<3 or len(argv)>32
        or any(type(a) is not str or not a or '\0' in a for a in argv)
        or sum(len(a.encode('utf8'))+1 for a in argv)>MAX_ARGV
        or str(source) not in argv or argv[0]!=str(expected_executable)):
        deny('FROZEN_BRIDGE_ARGV')
    if not hasattr(os,'pidfd_open'):deny('PIDFD_UNAVAILABLE')
    try:fd=os.pidfd_open(expected_pid,0)
    except OSError:deny('PIDFD_OPEN_FAILED')
    try:
        source_inode=_source_identity(source,source_sha256)
        exe_id=_exe_inode(expected_pid,expected_executable)
        start=_start_ticks(expected_pid)
        if not _pid_alive(fd):deny('PID_ALREADY_EXITED')
        if _proc_argv(expected_pid)!=argv:deny('BRIDGE_ARGV_CHANGED')
        try:
            pid,uid,gid=session._peer_kernel(backend_socket)
            session.verify_peer(backend_socket,unit=unit)
        except (session.SessionHold,OSError,TypeError,ValueError):
            deny('KERNEL_PEER_NOT_VERIFIED')
        if pid!=expected_pid or uid!=binding.UID or gid!=binding.GID:
            deny('BRIDGE_PEER_NOT_SPAWNED_PID')
        if _start_ticks(pid)!=start or not _pid_alive(fd):deny('BRIDGE_PID_REUSED_OR_EXITED')
        return BridgePin(pid=pid,pidfd=fd,unit=unit,start_ticks=start,
            executable=expected_executable,executable_dev_ino=exe_id,
            source=source,source_inode=source_inode,source_sha256=source_sha256,argv=argv)
    except BaseException:
        os.close(fd)
        raise


def verify_bridge_pin(pin:BridgePin,backend_socket:socket.socket)->dict:
    if not isinstance(pin,BridgePin) or pin.closed or not _pid_alive(pin.pidfd):
        deny('PIN_CLOSED_OR_EXITED')
    try:
        pid,uid,gid=session._peer_kernel(backend_socket)
        session.verify_peer(backend_socket,unit=pin.unit)
    except (session.SessionHold,OSError,TypeError,ValueError):
        deny('PEER_AFTER_PIN')
    if pid!=pin.pid or uid!=binding.UID or gid!=binding.GID:
        deny('PIN_PEER_REBOUND')
    if (_start_ticks(pin.pid)!=pin.start_ticks or
        _exe_inode(pin.pid,pin.executable)!=pin.executable_dev_ino or
        _proc_argv(pin.pid)!=pin.argv or
        _source_identity(pin.source,pin.source_sha256)!=pin.source_inode or
        not _pid_alive(pin.pidfd)):
        deny('PIN_LINEAGE_CHANGED')
    return {'schema_version':SCHEMA,'state':'DISPOSABLE_BRIDGE_PIDFD_AND_SOCKET_PINNED',
        'unit':pin.unit,'backend_bridge_pid':pin.pid,'bridge_source_sha256':pin.source_sha256,
        'kernel_peer_verified':True,'pidfd_alive_verified':True,
        'canonical_mcp_child_independently_proven':False,'copilot_egress_attested':False,
        'credential_isolation_attested':False,'live_worker_authorized':False,
        'worker_result_accepted':False,'automatic_retry':False}


def _frozen_witness(witness:kernel.KernelWitness,unit:str)->None:
    if (witness is None or type(witness) is not kernel.KernelWitness or
        witness.closed or witness.unit!=unit or witness.armed_populated!='1' or
        not INVOCATION.fullmatch(witness.invocation_id)):
        deny('HELD_WITNESS_IDENTITY')


def review_held_handoff(*,spec:binding.BoundedInput,plan:dict,
                         invocation:Mapping,candidate:Mapping,lease:Path,
                         witness:kernel.KernelWitness)->dict:
    """PRE-release: verify root HELD unit and frozen lease, NOT a backend PID.

    The R030 gate can only spawn the Worker after release. Requiring a backend
    PID inside that unit BEFORE release would deadlock the canonical route.
    """
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if type(spec) is not binding.BoundedInput or type(plan) is not dict:deny('BOUND_SPEC')
    try:
        binding.validate_plan(plan,spec)
        identity=session.verify_binding(invocation=invocation,candidate=candidate,
            expected_attempt=spec.attempt_id,expected_epoch=candidate['epoch'],
            expected_head=spec.source_head,lease_path=lease)
        session.check_lease(lease_path=lease,identity=identity)
        from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
        held=systemd._verify_held(plan['identity']['unit'],route._trusted_runner)
        observed=kernel.show(plan['identity']['unit'],route._trusted_runner)
    except (binding.BoundaryBlocked,session.SessionHold,KeyError,
            ValueError,TypeError,OSError,systemd.SystemdLaunchBlocked,kernel.WitnessBlocked):
        deny('FROZEN_HELD_LEASE_JOIN')
    unit=plan['identity']['unit']
    _frozen_witness(witness,unit)
    if (identity['unit']!=unit or held['ControlGroup']!='/system.slice/'+unit or
        observed['InvocationID']!=witness.invocation_id or
        observed['ControlGroup']!='/system.slice/'+unit or
        observed['ActiveState']!='active' or observed['MainPID']!=held['MainPID']):
        deny('HELD_SYSTEMD_INVOCATION_CHANGED')
    return {'schema_version':SCHEMA,
        'state':'HELD_R030_R135_PRE_RELEASE_REVIEW_ONLY',
        'attempt_id':spec.attempt_id,'source_head':spec.source_head,'unit':unit,
        'systemd_invocation_id':witness.invocation_id,'bridge_pid':None,
        'backend_bridge_origin_pinned':False,'canonical_mcp_child_independently_proven':False,
        'r035_terminal_receipt_proven':False,'terminal_ledger_written':False,
        'g1_g5_closed':False,'live_worker_authorized':False,
        'worker_result_accepted':False,'automatic_retry':False}


def review_post_release_bridge(*,held_review:dict,spec:binding.BoundedInput,
                               plan:dict,witness:kernel.KernelWitness,
                               bridge_pin:BridgePin,backend_socket:socket.socket)->dict:
    """POST-release: exact same invocation AND pinned backend bridge before IPC.

    No claim/release/IPC forwarding is performed. Caller must separately prove
    release decision, child MCP process, root receipts and kernel terminal.
    """
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    if type(held_review) is not dict or type(spec) is not binding.BoundedInput or type(plan) is not dict:
        deny('POST_INPUT_TYPE')
    unit=plan.get('identity',{}).get('unit')
    _frozen_witness(witness,unit)
    expected_keys={'schema_version','state','attempt_id','source_head','unit',
        'systemd_invocation_id','bridge_pid','backend_bridge_origin_pinned',
        'canonical_mcp_child_independently_proven','r035_terminal_receipt_proven',
        'terminal_ledger_written','g1_g5_closed','live_worker_authorized',
        'worker_result_accepted','automatic_retry'}
    if set(held_review)!=expected_keys:deny('POST_HELD_FIELDS')
    if (held_review.get('schema_version')!=SCHEMA or
        held_review.get('state')!='HELD_R030_R135_PRE_RELEASE_REVIEW_ONLY' or
        held_review.get('attempt_id')!=spec.attempt_id or
        held_review.get('source_head')!=spec.source_head or
        held_review.get('unit')!=unit or
        held_review.get('systemd_invocation_id')!=witness.invocation_id or
        held_review.get('bridge_pid') is not None or
        any(held_review[k] is not False for k in ('backend_bridge_origin_pinned',
            'canonical_mcp_child_independently_proven','r035_terminal_receipt_proven',
            'terminal_ledger_written','g1_g5_closed','live_worker_authorized',
            'worker_result_accepted','automatic_retry'))):
        deny('POST_HELD_RECORD_BINDING')
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    try:
        observed=kernel.show(unit,route._trusted_runner)
        populated=kernel.read_fd(witness.fd)
    except (kernel.WitnessBlocked,OSError,TypeError,ValueError):
        deny('POST_KERNEL_READBACK')
    if type(bridge_pin) is not BridgePin:deny('POST_BRIDGE_PIN_TYPE')
    if (observed['Id']!=unit or observed['InvocationID']!=witness.invocation_id or
        observed['ControlGroup']!='/system.slice/'+unit or
        observed['ActiveState']!='active' or observed['User']!='forprint-runner' or
        observed['Group']!='forprint-runner' or observed['KillMode']!='control-group' or
        populated!='1' or bridge_pin.unit!=unit):
        deny('POST_SYSTEMD_INVOCATION_OR_CGROUP')
    bridge=verify_bridge_pin(bridge_pin,backend_socket)
    return {**held_review,'state':'POST_RELEASE_BRIDGE_PINNED_PRE_IPC_REVIEW_ONLY',
        'bridge_pid':bridge['backend_bridge_pid'],
        'root_release_readback_proven':False,
        'backend_bridge_origin_pinned':True,
        'canonical_mcp_child_independently_proven':False,
        'terminal_ledger_written':False,'g1_g5_closed':False,
        'live_worker_authorized':False,'worker_result_accepted':False,
        'automatic_retry':False}


def source_check()->int:
    if systemd.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_CUTOVER_DRIFT')
    if broker.SOCKET_NAME!='mcp.sock' or not hasattr(os,'pidfd_open'):
        deny('CANONICAL_BROKER_OR_KERNEL_SUPPORT_DRIFT')
    print('CF10_R141_HELD_BRIDGE=PIDFD_SOCKET_SOURCE_ANCHOR_REVIEW_ONLY')
    print('CF10_R141_CANONICAL_MCP_CHILD=NOT_YET_PROVEN')
    print('CF10_R141_R030_RELEASE=NOT_MODIFIED')
    print('CF10_R141_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0


def main():
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('source-check',),required=True)
    p.parse_args()
    try:return source_check()
    except OriginHold as exc:
        print(str(exc));return 3

if __name__=='__main__':raise SystemExit(main())
