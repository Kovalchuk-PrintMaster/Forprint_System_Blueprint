"""AE: one physical, synthetic Worker in a delegated leaf cgroup.

AD proved actual systemd process, root IPC, and task-bound synthetic result,
but pinned cgroup.events vanished when the entire unit exited. AE keeps a
separate systemd-main anchor alive, then migrates the child Worker to a root-
created delegated leaf. Only a genuine 1->0 read from that leaf FD, while
systemd remains active and anchor stays populated, is accepted. No provider,
network, credentials, production launch/claim/ledger/dispatcher mutation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import stat
import struct
import time
from collections.abc import Mapping
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_rehearsal_v0_1 as ad
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_anchor_v0_1 as anchor
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kernel

SCHEMA='cf10_ae_physical_delegated_leaf_v0_1'
GATES=['G1','G2','G3','G4','G5']
ROOT=Path('/sys/fs/cgroup/system.slice')
RUN_ROOT=Path('/run')
LEAF='cf10-actual-worker'
UNIT=ad.UNIT_RE

class AEHold(RuntimeError):pass

def deny(code):raise AEHold('CF10_AE_HOLD_'+code)

def _exact(obj, expected, label):
    if not isinstance(obj,Mapping) or obj != expected or set(obj)!=set(expected):deny(label+'_BINDING')

def recv(sock:socket.socket):
    try:return anchor.recv(sock)
    except (OSError,ValueError,TypeError,UnicodeError):deny('FRAME_READ')

def send(sock:socket.socket,obj:dict):
    try:anchor.send(sock,obj)
    except (OSError,ValueError,TypeError,UnicodeError):deny('FRAME_WRITE')

def peer(sock:socket.socket, *, claimed_pid:int|None=None)->int:
    try:pid,uid,gid=struct.unpack('3i',sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i')))
    except (OSError,struct.error):deny('SO_PEERCRED')
    if pid<2 or (uid,gid)!=(996,992) or (claimed_pid is not None and pid!=claimed_pid):deny('PEER_IDENTITY')
    return pid

def proc_parent(pid:int)->int:
    if type(pid) is not int or pid<2:deny('CHILD_PID')
    try:
        b=(Path('/proc')/str(pid)/'stat').read_bytes()
        if len(b)>4096 or b'\x00' in b:deny('PROC_STAT_SIZE')
        tail=b.rsplit(b') ',1)[1].split()
        # /proc/PID/stat: state=field 3 (tail[0]); ppid=field 4 (tail[1]).
        if len(tail)<20 or not tail[1].isdigit():deny('PROC_STAT_FORMAT')
        return int(tail[1])
    except (OSError,IndexError,ValueError):deny('PROC_STAT_UNAVAILABLE')

def proc_cgroup(pid:int, expected:str)->None:
    try:
        raw=(Path('/proc')/str(pid)/'cgroup').read_bytes()
        if len(raw)>4096 or b'\x00' in raw:deny('PROC_CGROUP_SIZE')
        lines=raw.decode('ascii','strict').splitlines()
    except (OSError,UnicodeError):deny('PROC_CGROUP_UNAVAILABLE')
    if lines!=['0::'+expected]:deny('PROC_CGROUP_MISMATCH')

def _root_dir_inode(path:Path):
    st=path.lstat()
    # systemd Delegate=yes can chown the unit cgroup to its verified User=996.
    # The new leaf below it is always root-created and root-owned.
    if (not stat.S_ISDIR(st.st_mode) or st.st_uid not in (0,996) or
            (st.st_mode & 0o022) or path.is_symlink()):deny('CGROUP_INODE')
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC|os.O_NOFOLLOW)
    after=os.fstat(fd)
    if (after.st_dev,after.st_ino)!=(st.st_dev,st.st_ino) or after.st_uid!=st.st_uid:
        os.close(fd);deny('CGROUP_PATH_SWAP')
    return fd

def delegate_child(unit:str, worker_pid:int, anchor_pid:int, *,root:Path=ROOT):
    """Root-only: move exact child PID to a *new* leaf in a disposable delegated unit."""
    if not UNIT.fullmatch(unit) or type(worker_pid) is not int or worker_pid<2 or anchor_pid<2:
        deny('DELEGATION_ARGS')
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    parent=root/unit
    proc_cgroup(anchor_pid,'/system.slice/'+unit)
    proc_cgroup(worker_pid,'/system.slice/'+unit)
    if proc_parent(worker_pid)!=anchor_pid:deny('CHILD_NOT_OF_ANCHOR')
    groupfd=_root_dir_inode(parent)
    leaffd=None;eventfd=None;made=False
    try:
        path=parent/LEAF
        if path.exists() or path.is_symlink():deny('LEAF_COLLISION')
        os.mkdir(LEAF,mode=0o755,dir_fd=groupfd);made=True
        leaffd=os.open(LEAF,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC|os.O_NOFOLLOW,dir_fd=groupfd)
        leafst=os.fstat(leaffd)
        if not stat.S_ISDIR(leafst.st_mode) or leafst.st_uid!=0:deny('LEAF_UNTRUSTED')
        cfd=os.open('cgroup.procs',os.O_WRONLY|os.O_CLOEXEC|os.O_NOFOLLOW,dir_fd=leaffd)
        try:os.write(cfd,str(worker_pid).encode('ascii'))
        finally:os.close(cfd)
        proc_cgroup(worker_pid,'/system.slice/'+unit+'/'+LEAF)
        proc_cgroup(anchor_pid,'/system.slice/'+unit)
        eventfd=os.open('cgroup.events',os.O_RDONLY|os.O_CLOEXEC|os.O_NONBLOCK|os.O_NOFOLLOW,dir_fd=leaffd)
        ev=os.fstat(eventfd)
        if not stat.S_ISREG(ev.st_mode) or ev.st_uid!=0:deny('EVENT_INODE')
        if kernel.read_fd(eventfd)!='1':deny('LEAF_NOT_POPULATED_1')
        return eventfd,leaffd,groupfd
    except BaseException:
        if eventfd is not None:os.close(eventfd)
        if leaffd is not None:os.close(leaffd)
        if made:
            try:os.rmdir(LEAF,dir_fd=groupfd)
            except OSError:pass
        os.close(groupfd)
        raise

def observe_zero(fd:int,groupfd:int,unit:str,invocation_id:str, *,timeout:float=18):
    """No process-exit surrogate: pinned leaf cgroup.events must actually read 0."""
    deadline=time.monotonic()+timeout
    if kernel.read_fd(fd)!='1':deny('LEAF_NOT_INITIAL_1')
    while time.monotonic()<deadline:
        try:v=kernel.read_fd(fd)
        except (OSError,kernel.WitnessBlocked):deny('PINNED_LEAF_FD_LOST')
        if v=='0':
            # The parent still has the anchor. A removed parent is never success.
            parent_events=os.open('cgroup.events',os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW,dir_fd=groupfd)
            try:parent_state=kernel.read_fd(parent_events)
            finally:os.close(parent_events)
            if parent_state!='1':deny('ANCHOR_PARENT_NOT_POPULATED')
            return {'observation':'PINNED_DELEGATED_LEAF_FD','transition':'1_TO_0',
                    'samples':['1','0'],'unit':unit,'invocation_id':invocation_id,
                    'parent_anchor_populated':'1','leaf_name':LEAF}
        if v!='1':deny('LEAF_POPULATED_INVALID')
        time.sleep(.02)
    deny('PINNED_LEAF_ZERO_TIMEOUT')

def attest(*,task:Mapping,anchor_pid:int,worker_pid:int,held:Mapping,result:Mapping,
            proof:Mapping,retained:Mapping,stop:Mapping,unit:str,invocation_id:str,nonce:str)->dict:
    if not UNIT.fullmatch(unit) or type(worker_pid) is not int or type(anchor_pid) is not int or worker_pid<2 or anchor_pid<2 or worker_pid==anchor_pid:
        deny('PROCESS_IDENTITIES')
    if not isinstance(task,Mapping) or task.get('worker_claim_consumed') is not False or task.get('production_dispatch_performed') is not False:
        deny('CANONICAL_TASK_SCOPE')
    resultcheck=ad.check_phase(held,result,unit=unit,nonce=nonce)
    if proof!={'observation':'PINNED_DELEGATED_LEAF_FD','transition':'1_TO_0',
          'samples':['1','0'],'unit':unit,'invocation_id':invocation_id,
          'parent_anchor_populated':'1','leaf_name':LEAF}:deny('REAL_LEAF_KERNEL_PROOF')
    if retained.get('retained_systemd_proven') is not True or retained.get('invocation_id')!=invocation_id:
        deny('RETAINED_NOT_VERIFIED')
    if stop.get('ActiveState')!='inactive' or stop.get('MainPID')!='0' or stop.get('Result')!='success':
        deny('FINAL_SYSTEMD')
    return {'schema':SCHEMA,'status':'PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL',
        'unit':unit,'anchor_pid':anchor_pid,'worker_pid':worker_pid,
        'held_invocation_id':invocation_id,'canonical_task_binding':task['task_id'],
        'result_sha256':resultcheck['synthetic_result_digest'],
        'worker_result_verified_by_root':True,
        'kernel_leaf_transition':'1_TO_0','root_pinned_leaf':True,
        'parent_anchor_held_until_kernel_zero':True,'retained_systemd':True,
        'stopped_readback':True,'canonical_dispatcher_release':False,
        'production_result_acceptance':False,'production_claim_consumed':False,
        'production_ledger_written':False,'provider_inference':False,
        'provider_credentials':False,'external_egress':False,'gates_open':list(GATES)}

def _socket(path:Path)->socket.socket:
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    s.bind(str(path));os.chown(path,0,992);os.chmod(path,0o660)
    s.listen(1);s.settimeout(19)
    return s

def _read_delegate(rows:dict,unit:str,anchor_pid:int)->dict:
    ans=ad.validate_held(rows,unit,anchor_pid)
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    if backend.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH')
    # Delegate=yes grants root a controlled nested leaf without modifying global
    # services, /etc or persistent production cgroup configuration.
    cp=ad.call(['/usr/bin/systemctl','show','--property=Delegate','--value','--',unit],timeout=8)
    if cp.returncode or cp.stdout.strip()!=b'yes':deny('SYSTEMD_DELEGATION_UNAVAILABLE')
    return ans

def _canonical():
    return ad.inspect_canonical()

def run_once()->dict:
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    task=_canonical()
    unit='forprint-cf10-batchad-'+secrets.token_hex(8)+'.service'
    nonce=secrets.token_hex(32)
    path=RUN_ROOT/unit.removesuffix('.service')
    ad.runtime_dir(path)
    # The service only executes durable Git-tracked AE source copied to /run.
    copies={'anchor.py':Path(anchor.__file__),'child.py':Path(child.__file__)}
    for name,source in copies.items():
        target=path/name;shutil.copyfile(source,target);os.chmod(target,0o444)
        if hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256(target.read_bytes()).digest():deny('SOURCE_COPY')
    anchor_listener=_socket(path/'anchor.sock')
    worker_listener=_socket(path/'control.sock')
    fd=None;leaffd=None;groupfd=None;leaf_made=False;unit_started=False
    report={'schema':SCHEMA,'status':'HOLD_UNSTARTED','unit':unit,'canonical_binding':task,
        'stage':'PREPARED','gates_open':list(GATES),
        'authority':{'production_worker':False,'provider_auth_used':False,
          'external_egress':False,'canonical_claim_consumed':False,'automatic_retry':False}}
    try:
        props=['User=forprint-runner','Group=forprint-runner','Type=exec',
           'ExitType=cgroup','RemainAfterExit=yes','Restart=no','Delegate=yes',
           'RuntimeMaxSec=110s','PrivateNetwork=yes','IPAddressDeny=any',
           'RestrictAddressFamilies=AF_UNIX','NoNewPrivileges=yes',
           'ProtectSystem=strict','ProtectHome=yes','PrivateDevices=yes',
           'ProtectControlGroups=yes','RestrictNamespaces=yes',
           'CapabilityBoundingSet=','AmbientCapabilities=','KillMode=control-group',
           'StandardOutput=null','StandardError=null','WorkingDirectory=/',
           'InaccessiblePaths=/var/lib/forprint-runner']
        args=['/usr/bin/systemd-run','--no-block','--quiet','--remain-after-exit',
              '--unit='+unit,*['--property='+v for v in props],
              '/usr/bin/python3','-I','-B',str(path/'anchor.py'),unit,
              str(path/'anchor.sock'),str(path/'control.sock'),str(path/'child.py'),
              nonce,child.TASK]
        start=ad.call(args,timeout=18)
        if start.returncode:deny('SYSTEMD_RUN_'+str(start.returncode))
        unit_started=True;report['stage']='SYSTEMD_ANCHOR_STARTED'
        with anchor_listener,worker_listener:
            try:aconn,_=anchor_listener.accept()
            except socket.timeout:deny('ANCHOR_ACCEPT_TIMEOUT')
            with aconn:
                aconn.settimeout(25)
                anchor_pid=peer(aconn)
                held=ad.validate_held(ad.show(unit),unit,anchor_pid)
                invocation_id=held['invocation_id']
                proc_cgroup(anchor_pid,'/system.slice/'+unit)
                _read_delegate(ad.show(unit),unit,anchor_pid)
                _exact(recv(aconn),{'schema':anchor.SCHEMA,'event':'ANCHOR_HELD','unit':unit,
                    'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()},'ANCHOR_HELD')
                report['anchor']={'held':True,'pid':anchor_pid,'invocation_id':invocation_id}
                report['stage']='ANCHOR_MAINPID_VERIFIED_AND_DELEGATED'
                send(aconn,{'schema':anchor.SCHEMA,'event':'SPAWN_ONE','unit':unit,'nonce':nonce})
                spawned=recv(aconn)
                if (not isinstance(spawned,Mapping) or set(spawned)!={'schema','event','unit','pid'} or
                    spawned.get('schema')!=anchor.SCHEMA or spawned.get('event')!='WORKER_SPAWNED' or
                    spawned.get('unit')!=unit or type(spawned.get('pid')) is not int or spawned['pid']<2):
                    deny('ANCHOR_SPAWN_REPLY')
                worker_pid=spawned['pid'];report['worker_pid']=worker_pid
                try:wconn,_=worker_listener.accept()
                except socket.timeout:deny('WORKER_ACCEPT_TIMEOUT')
                with wconn:
                    wconn.settimeout(25)
                    peer(wconn,claimed_pid=worker_pid)
                    if proc_parent(worker_pid)!=anchor_pid:deny('WORKER_PARENT')
                    proc_cgroup(worker_pid,'/system.slice/'+unit)
                    held_frame=ad.frame_in(wconn)
                    if held_frame!={'schema':child.VERSION,'phase':'HELD','unit':unit,
                         'task_id':child.TASK,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()}:
                        deny('WORKER_HELD_FRAME')
                    report['stage']='WORKER_PEER_PARENT_AND_HELD_VERIFIED'
                    fd,leaffd,groupfd=delegate_child(unit,worker_pid,anchor_pid)
                    leaf_made=True
                    report['stage']='DELEGATED_WORKER_CGROUP_POPULATED_1'
                    ad.frame_out(wconn,{'schema':child.VERSION,'phase':'RELEASE_ONE_DISPOSABLE',
                           'unit':unit,'nonce':nonce,'task_id':child.TASK})
                    result_frame=ad.frame_in(wconn)
                    result_check=ad.check_phase(held_frame,result_frame,unit=unit,nonce=nonce)
                    report['result']=result_check;report['stage']='SYNTHETIC_RESULT_VERIFIED'
                    ad.frame_out(wconn,{'schema':child.VERSION,'phase':'RESULT_RECEIVED',
                           'unit':unit,'result_sha256':result_frame['result_sha256']})
                proof=observe_zero(fd,groupfd,unit,invocation_id)
                report['kernel']=proof;report['stage']='DELEGATED_KERNEL_1_TO_0'
                # The root-created leaf stays alive until the authenticated pinned
                # read observes zero, while anchor remains in systemd parent.
                os.close(fd);fd=None;os.close(leaffd);leaffd=None
                os.rmdir(LEAF,dir_fd=groupfd);leaf_made=False
                os.close(groupfd);groupfd=None
                send(aconn,{'schema':anchor.SCHEMA,'event':'FINALIZE_AFTER_PINNED_ZERO',
                            'unit':unit,'pid':worker_pid})
                _exact(recv(aconn),{'schema':anchor.SCHEMA,'event':'WORKER_REAPED',
                       'unit':unit,'pid':worker_pid,'exit_code':0},'ANCHOR_REAP')
                report['stage']='WORKER_REAPED_AFTER_KERNEL_ZERO'
        deadline=time.monotonic()+8
        while True:
            rows=ad.show(unit)
            if rows['SubState']=='exited' and rows['MainPID']=='0':break
            if time.monotonic()>deadline:deny('RETAINED_EXIT_TIMEOUT')
            time.sleep(.05)
        retained=ad.validate_terminal(rows,unit,invocation_id)
        report['retained']=retained;report['stage']='RETAINED_SYSTEMD_VERIFIED'
        stopped=ad.call(['/usr/bin/systemctl','stop','--',unit],timeout=15)
        if stopped.returncode:deny('STOP_RC')
        unit_started=False
        final=ad.show(unit)
        report['poststop']={'active':final['ActiveState'],'main_pid':final['MainPID'],'result':final['Result']}
        report['terminal']=attest(task=task,anchor_pid=anchor_pid,worker_pid=worker_pid,
                held=held_frame,result=result_frame,proof=proof,retained=retained,
                stop=final,unit=unit,invocation_id=invocation_id,nonce=nonce)
        report['stage']='STOPPED_AND_TERMINAL_VERIFIED'
        report['status']='PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL'
        return report
    except BaseException as exc:
        report['status']=str(exc) if isinstance(exc,AEHold) else 'CF10_AE_HOLD_'+type(exc).__name__
        report['error']={'kind':type(exc).__name__}
        if isinstance(exc,OSError):report['error']['errno']=exc.errno
        return report
    finally:
        if fd is not None:os.close(fd)
        if leaffd is not None:os.close(leaffd)
        if groupfd is not None:os.close(groupfd)
        anchor_listener.close();worker_listener.close()
        if unit_started:
            try:ad.call(['/usr/bin/systemctl','stop','--',unit],timeout=12)
            except BaseException:pass
        try:
            post=ad.show(unit)
            if post['ActiveState']=='inactive' and post['MainPID']=='0':
                # Drop owned disposable leaves only if systemd fully reaped;
                # unknown structures remain quarantined for operator review.
                inner=ROOT/unit/LEAF
                if inner.exists() and inner.is_dir() and not inner.is_symlink():
                    eventfd=os.open(inner/'cgroup.events',os.O_RDONLY|os.O_NOFOLLOW)
                    try:status=kernel.read_fd(eventfd)
                    finally:os.close(eventfd)
                    if status=='0':inner.rmdir()
                cleanup_run(path)
                report['runtime_cleanup']='PASS_DISPOSABLE_ONLY'
            else:report['runtime_cleanup']='HOLD_QUARANTINE_RUN_PATH'
        except BaseException:
            report['runtime_cleanup']='HOLD_QUARANTINE_RUN_PATH'
        if report.get('status','').startswith('PASS_') and report.get('runtime_cleanup')!='PASS_DISPOSABLE_ONLY':
            report['status']='CF10_AE_HOLD_DISPOSABLE_RUNTIME_CLEANUP'


def cleanup_run(path:Path):
    if (path.parent!=RUN_ROOT or not UNIT.fullmatch(path.name+'.service') or
         path.is_symlink() or not path.is_dir() or path.lstat().st_uid!=0):deny('CLEANUP_SCOPE')
    expected={'anchor.py','child.py','anchor.sock','control.sock'}
    found={p.name for p in path.iterdir()}
    if found!=expected:deny('CLEANUP_FILES')
    for p in path.iterdir():
        if p.is_dir() or p.is_symlink():deny('CLEANUP_NODE')
        p.unlink()
    path.rmdir()

def source_check()->dict:
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_launcher_v0_1 as launcher,
        cf10_first_worker_crossplane_gate_v0_1 as cross)
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH')
    review=cross.current_readonly(ad.REPO)
    if review['gates_open']!=GATES or review['worker_started'] is not False:deny('CROSSPLANE')
    if not hasattr(kernel,'read_fd') or not hasattr(ad,'inspect_canonical'):deny('EXISTING_SOURCE_MISSING')
    return {'source':'PASS_DISPOSABLE_DELEGATED_LEAF_SOURCE_ONLY',
            'uses_existing_ad':True,'live_worker':False,'gates_open':list(GATES)}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=('source-check','run-once'),required=True)
    a=p.parse_args(argv)
    try:
        r=source_check() if a.mode=='source-check' else run_once()
        print(json.dumps(r,sort_keys=True,separators=(',',':')))
        return 0 if a.mode=='source-check' or r.get('status','').startswith('PASS_') else 3
    except BaseException as exc:
        print(json.dumps({'schema':SCHEMA,'status':str(exc) if isinstance(exc,AEHold) else 'HOLD_'+type(exc).__name__,
             'gates_open':list(GATES)},sort_keys=True,separators=(',',':')))
        return 3

if __name__=='__main__':raise SystemExit(main())
