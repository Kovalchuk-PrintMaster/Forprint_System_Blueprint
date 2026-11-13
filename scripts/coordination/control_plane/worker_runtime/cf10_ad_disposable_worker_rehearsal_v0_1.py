"""CF10 AD: first REAL disposable systemd subprocess + result + terminal observation.

Non-authorizing laboratory. Uses the existing canonical training resolver and
AB crossplane review to bind the task; does NOT call production Dispatcher
release or launcher. No owner/PAM claim, root receipts, durable terminal ledger,
Copilot, credentials, upstream or production Worker. This is a physical process
rehearsal to learn which G4/G5 integration remains, never a G1-G5 gate closure.
Only executable source in git; /run is disposable data/staging for this lab.
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
import subprocess
import time
from collections.abc import Mapping
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child

SCHEMA='cf10_ad_disposable_physical_lifecycle_v0_1'
OPEN=['G1','G2','G3','G4','G5']
UNIT_RE=re.compile(r'forprint-cf10-batchad-[a-f0-9]{16}\.service\Z')
RUN_ROOT=Path('/run')
REPO=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
EXPECTED_BRANCH='audit/blueprint-inventory-refresh-2026-07-29'
EXPECTED_TASK=child.TASK
ALLOWED_PHASES=('HELD','RELEASE_ONE_DISPOSABLE','RESULT','RESULT_RECEIVED')

class RehearsalHold(RuntimeError):pass

def deny(code):raise RehearsalHold('CF10_AD_HOLD_'+code)

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()

def exact(obj,keys,label):
    if not isinstance(obj,Mapping) or set(obj)!=set(keys):deny(label+'_SHAPE')
    return obj

def validate_task(*,task:Mapping,crossplane:Mapping,backend_closed:bool)->dict:
    if (not isinstance(task,Mapping) or task.get('task_prompt_id')!=EXPECTED_TASK or
         task.get('work_id')!='u180j' or task.get('module')!='forprint_system_blueprint' or
         task.get('candidate_only') is not True):deny('TASK_NOT_CANONICAL')
    if (not isinstance(crossplane,Mapping) or
         crossplane.get('canonical_task_resolved') is not True or
         crossplane.get('canonical_synthetic_11_step_lifecycle_passed') is not True or
         crossplane.get('owner_claim_consumed') is not False or
         crossplane.get('worker_started') is not False or
         crossplane.get('gates_open')!=OPEN):deny('CROSSPLANE_DRIFT')
    if backend_closed is not True:deny('LIVE_SWITCH_DRIFT')
    return {'schema':SCHEMA,'task_id':EXPECTED_TASK,'work_id':'u180j',
      'binding_source':'CANONICAL_TRAINING_RESOLVER_READ_ONLY',
      'crossplane_sha256':crossplane['report_sha256'],
      'worker_claim_consumed':False,'production_dispatch_performed':False,
      'gates_open':list(OPEN)}

def check_phase(held:Mapping,result:Mapping,*,unit:str,nonce:str)->dict:
    if type(unit) is not str or UNIT_RE.fullmatch(unit) is None:deny('UNIT')
    exact(held,{'schema','phase','unit','task_id','nonce_sha256'},'HELD')
    if held!={'schema':child.VERSION,'phase':'HELD','unit':unit,'task_id':EXPECTED_TASK,
             'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()}:deny('HELD_BINDING')
    exact(result,{'schema','phase','unit','task_id','result_kind','result_sha256'},'RESULT')
    if result!={'schema':child.VERSION,'phase':'RESULT','unit':unit,'task_id':EXPECTED_TASK,
               'result_kind':'SYNTHETIC_READONLY_NON_AI',
               'result_sha256':child.worker_digest(EXPECTED_TASK,nonce)}:deny('RESULT_BINDING')
    return {'synthetic_result_digest':result['result_sha256'],
            'result_verified_by_root':True,'worker_result_accepted':False,
            'model_inference_executed':False,'canonical_result_ledger_written':False}

def show(unit:str,*,timeout=12)->dict:
    if type(unit) is not str or UNIT_RE.fullmatch(unit) is None:deny('SHOW_UNIT')
    keys=('Id','LoadState','ActiveState','SubState','MainPID','ControlGroup','InvocationID',
          'User','Group','KillMode','ExitType','RemainAfterExit','PrivateNetwork',
          'NoNewPrivileges','Result','ExecMainStatus')
    cp=call(['/usr/bin/systemctl','show','--no-pager',*('--property='+x for x in keys),'--',unit],timeout=timeout)
    if cp.returncode:deny('SHOW_RC')
    if len(cp.stdout)>8192 or b'\x00' in cp.stdout:deny('SHOW_SIZE')
    rows={}
    try:
        for line in cp.stdout.decode('utf8','strict').splitlines():
            if line.count('=')!=1:deny('SHOW_FORMAT')
            k,v=line.split('=',1)
            if k in rows or k not in keys:deny('SHOW_FIELDS')
            rows[k]=v
    except UnicodeError:deny('SHOW_ENCODING')
    if set(rows)!=set(keys) or rows['Id']!=unit:deny('SHOW_IDENTITY')
    return rows

def validate_held(rows:Mapping,unit:str,pid:int)->dict:
    if (rows.get('LoadState')!='loaded' or rows.get('ActiveState')!='active' or
        rows.get('SubState')!='running' or rows.get('MainPID')!=str(pid) or
        rows.get('ControlGroup')!='/system.slice/'+unit or
        rows.get('User')!='forprint-runner' or rows.get('Group')!='forprint-runner' or
        rows.get('KillMode')!='control-group' or rows.get('ExitType')!='cgroup' or
        rows.get('RemainAfterExit')!='yes' or rows.get('PrivateNetwork')!='yes' or
        rows.get('NoNewPrivileges')!='yes' or
        not re.fullmatch(r'[a-f0-9]{32}',rows.get('InvocationID',''))):deny('HELD_SYSTEMD_PROFILE')
    return {'pid':pid,'invocation_id':rows['InvocationID'],'held_profile_pass':True}

def validate_terminal(rows:Mapping,unit:str,invocation_id:str)->dict:
    if (rows.get('Id')!=unit or rows.get('InvocationID')!=invocation_id or
       rows.get('LoadState')!='loaded' or rows.get('ActiveState')!='active' or
       rows.get('SubState')!='exited' or rows.get('MainPID')!='0' or
       rows.get('Result')!='success' or rows.get('ExecMainStatus')!='0' or
       rows.get('ExitType')!='cgroup' or rows.get('RemainAfterExit')!='yes'):
        deny('RETAINED_TERMINAL_NOT_PROVEN')
    return {'retained_systemd_proven':True,'invocation_id':invocation_id}

def check_finish(*,proof:Mapping,retained:Mapping,final:Mapping,unit:str)->dict:
    if proof.get('samples')!=['1','0'] or proof.get('kernel_observation')!='PINNED_FD_READ':
        deny('KERNEL_TRANSITION_UNPROVEN')
    if retained.get('retained_systemd_proven') is not True:deny('RETAINED_UNPROVEN')
    if final.get('ActiveState')!='inactive' or final.get('MainPID')!='0':deny('STOP_READBACK')
    return {'status':'PASS_DISPOSABLE_SYSTEMD_RESULT_AND_KERNEL_TERMINAL',
      'schema':SCHEMA,'unit':unit,'kernel_samples':['1','0'],
      'synthetic_worker_result_verified':True,'model_inference_executed':False,
      'provider_credentials_read':False,'real_provider_egress':False,
      'worker_claim_consumed':False,'production_launcher_called':False,
      'production_ledger_written':False,'canonical_dispatcher_released':False,
      'gates_open':list(OPEN)}

def scrubbed_env():
    return {'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LANG':'C','LC_ALL':'C',
            'PYTHONDONTWRITEBYTECODE':'1','GIT_TERMINAL_PROMPT':'0'}

def call(args,timeout=15):
    try:
        return subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,timeout=timeout,check=False,env=scrubbed_env())
    except (OSError,subprocess.TimeoutExpired) as exc:deny('SUBPROCESS_'+type(exc).__name__)

def frame_in(sock):
    try:return child.recv(sock)
    except (ValueError,OSError,UnicodeError,TypeError):deny('IPC_FRAME')

def frame_out(sock,obj):
    try:child.send(sock,obj)
    except (ValueError,OSError,UnicodeError,TypeError):deny('IPC_SEND')

def peer(sock):
    raw=sock.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize('3i'))
    pid,uid,gid=struct.unpack('3i',raw)
    if pid<2 or (uid,gid)!=(996,992):deny('PEER_CREDENTIALS')
    return pid

def proc_cgroup(pid:int,unit:str):
    try:raw=Path('/proc')/str(pid)/'cgroup';lines=raw.read_text('ascii').splitlines()
    except OSError:deny('PEER_PROC_CGROUP')
    if f'0::/system.slice/{unit}' not in lines:deny('PEER_CGROUP')

def pin_cgroup(unit:str,invocation_id:str):
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kw
    # The canonical witness deliberately accepts ONLY real worker-unit names.
    # AD keeps its batch namespace separate: root uses the same validated
    # pinned-directory + openat cgroup.events primitive in this disposable lab.
    path=Path('/sys/fs/cgroup/system.slice')/unit
    try:
        st=path.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or path.is_symlink():deny('CGROUP_PATH')
        anchor=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        fs=os.fstat(anchor)
        if (fs.st_dev,fs.st_ino)!=(st.st_dev,st.st_ino):deny('CGROUP_INODE_CHANGED')
        fd=os.open('cgroup.events',os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=anchor)
        if kw.read_fd(fd)!='1':deny('CGROUP_NOT_POPULATED')
    except BaseException:
        if 'fd' in locals():os.close(fd)
        if 'anchor' in locals():os.close(anchor)
        raise
    return (fd,anchor)

def wait_zero(fd:int,unit:str,invocation_id:str,timeout:int=22)->dict:
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kw
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        try:state=kw.read_fd(fd)
        except (OSError,kw.WitnessBlocked) as exc:deny('KERNEL_PIN_READ_'+type(exc).__name__)
        if state=='0':
            return {'kernel_observation':'PINNED_FD_READ','samples':['1','0'],
                    'invocation_id':invocation_id,'unit':unit}
        if state!='1':deny('KERNEL_STATE')
        time.sleep(.07)
    deny('KERNEL_ZERO_TIMEOUT')

def runtime_dir(path:Path):
    if path.exists() or path.is_symlink():deny('RUNTIME_COLLISION')
    path.mkdir(mode=0o700)
    os.chown(path,0,992)
    os.chmod(path,0o750)
    st=path.lstat()
    if st.st_uid!=0 or st.st_gid!=992 or stat.S_IMODE(st.st_mode)!=0o750:deny('RUNTIME_MODE')

def safe_delete_run_path(path:Path):
    if (path.parent!=RUN_ROOT or
        not re.fullmatch(r'forprint-cf10-batchad-[a-f0-9]{16}',path.name) or
        path.is_symlink() or not path.is_dir() or path.lstat().st_uid!=0):
        deny('CLEANUP_PATH_SCOPE')
    for p in path.iterdir():
        if p.is_symlink() or p.is_dir():deny('CLEANUP_LAYOUT')
        if p.name not in ('control.sock','child.py'):deny('CLEANUP_UNEXPECTED_FILE')
        p.unlink()
    path.rmdir()

def inspect_canonical()->dict:
    from scripts.coordination.control_plane import cf10_training_dispatch as dispatcher
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_first_worker_crossplane_gate_v0_1 as cross,
        cf10_systemd_launcher_v0_1 as backend)
    task=dispatcher.resolve_training_task(root=REPO,task_prompt_id=EXPECTED_TASK)
    review=cross.current_readonly(REPO)
    return validate_task(task=task,crossplane=review,
                         backend_closed=backend.LIVE_CUTOVER_ENABLED is False)

def run_once()->dict:
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    canonical=inspect_canonical()
    unit='forprint-cf10-batchad-'+secrets.token_hex(8)+'.service'
    path=RUN_ROOT/unit.removesuffix('.service')
    nonce=secrets.token_hex(32)
    runtime_dir(path)
    rootpid=os.getpid()
    childfile=path/'child.py'
    source=Path(child.__file__)
    shutil.copyfile(source,childfile)
    os.chmod(childfile,0o444)
    if hashlib.sha256(source.read_bytes()).digest()!=hashlib.sha256(childfile.read_bytes()).digest():
        deny('CHILD_COPY_DRIFT')
    socket_path=path/'control.sock'
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    listener.bind(str(socket_path));os.chown(socket_path,0,992);os.chmod(socket_path,0o660)
    listener.listen(1);listener.settimeout(18)
    fd=None;anchor=None;started=False;released=False;proof=None
    report={'schema':SCHEMA,'unit':unit,'canonical_binding':canonical,'root_controller_pid':rootpid,
        'child_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'gates_open':OPEN,'status':'HOLD_NOT_COMPLETED','stage':'UNIT_PREPARED','authority':{
          'production_worker_launched':False,'worker_claim_consumed':False,
          'provider_credentials':False,'provider_egress':False,'model_inference':False,
          'automatic_retry':False}}
    try:
        props=['User=forprint-runner','Group=forprint-runner','Type=exec',
            'ExitType=cgroup','RemainAfterExit=yes','Restart=no',
            'RuntimeMaxSec=90s','PrivateNetwork=yes','IPAddressDeny=any',
            'RestrictAddressFamilies=AF_UNIX','NoNewPrivileges=yes',
            'ProtectSystem=strict','ProtectHome=yes','PrivateDevices=yes',
            'ProtectControlGroups=yes','RestrictNamespaces=yes',
            'CapabilityBoundingSet=','AmbientCapabilities=','KillMode=control-group',
            'StandardOutput=null','StandardError=null','WorkingDirectory=/',
            'InaccessiblePaths=/var/lib/forprint-runner']
        command=['/usr/bin/systemd-run','--no-block','--quiet','--remain-after-exit',
           '--unit='+unit,*['--property='+x for x in props],
           '/usr/bin/python3','-I','-B',str(childfile),unit,str(socket_path),nonce,EXPECTED_TASK]
        rc=call(command,18)
        if rc.returncode:deny('SYSTEMD_RUN_RC_'+str(rc.returncode))
        started=True
        report['stage']='SYSTEMD_STARTED'
        with listener:
            try:conn,_=listener.accept()
            except socket.timeout:deny('IPC_HELD_TIMEOUT')
            with conn:
                conn.settimeout(15)
                pid=peer(conn)
                proc_cgroup(pid,unit)
                rows=show(unit)
                profile=validate_held(rows,unit,pid)
                report['held']=profile
                report['stage']='HELD_IDENTITY_VERIFIED'
                fd,anchor=pin_cgroup(unit,profile['invocation_id'])
                held=frame_in(conn)
                exact(held,{'schema','phase','unit','task_id','nonce_sha256'},'HELD')
                if held['phase']!='HELD' or held['unit']!=unit or held['task_id']!=EXPECTED_TASK or held['nonce_sha256']!=hashlib.sha256(nonce.encode()).hexdigest():deny('HELD_INVALID')
                report['ipc_held']=True
                report['stage']='KERNEL_PINNED_1'
                frame_out(conn,{'schema':child.VERSION,'phase':'RELEASE_ONE_DISPOSABLE',
                     'unit':unit,'nonce':nonce,'task_id':EXPECTED_TASK})
                released=True
                report['stage']='DISPOSABLE_RELEASED'
                result=frame_in(conn)
                result_check=check_phase(held,result,unit=unit,nonce=nonce)
                report['result']=result_check
                report['stage']='SYNTHETIC_RESULT_VERIFIED'
                frame_out(conn,{'schema':child.VERSION,'phase':'RESULT_RECEIVED',
                                'unit':unit,'result_sha256':result['result_sha256']})
        proof=wait_zero(fd,unit,profile['invocation_id'])
        report['kernel']=proof
        report['stage']='KERNEL_ZERO_OBSERVED'
        retained=validate_terminal(show(unit),unit,profile['invocation_id'])
        report['retained']=retained
        report['stage']='RETAINED_TERMINAL_VERIFIED'
        stop=call(['/usr/bin/systemctl','stop','--',unit],timeout=15)
        if stop.returncode:deny('STOP_RC')
        started=False
        final=show(unit)
        report['poststop']={'active':final['ActiveState'],'main_pid':final['MainPID'],
                           'unit_result':final['Result']}
        report['terminal']=check_finish(proof=proof,retained=retained,final=final,unit=unit)
        report['stage']='STOPPED_VERIFIED'
        report['status']=report['terminal']['status']
        return report
    except BaseException as exc:
        report['status']='CF10_AD_HOLD_'+type(exc).__name__ if not isinstance(exc,RehearsalHold) else str(exc)
        return report
    finally:
        if fd is not None:os.close(fd)
        if anchor is not None:os.close(anchor)
        listener.close()
        if started:
            try:call(['/usr/bin/systemctl','stop','--',unit],timeout=12)
            except BaseException:pass
        # Never delete a run directory when there is no verified stop readback.
        try:
            post=show(unit)
            if post['ActiveState']=='inactive' and post['MainPID']=='0':
                safe_delete_run_path(path)
                report['runtime_cleanup']='PASS_DISPOSABLE_ONLY'
            else:
                report['runtime_cleanup']='HOLD_QUARANTINE_RUN_PATH'
        except BaseException:
            report['runtime_cleanup']='HOLD_QUARANTINE_RUN_PATH'

def source_check():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('PRODUCTION_SWITCH_OPEN')
    if not hasattr(child,'worker_digest'):deny('SYNTHETIC_CHILD_MISSING')
    if not getattr(launcher,'launch_after_owner_claim',None):deny('CANONICAL_SEAM_MISSING')
    return {'source':'PASS_DISPOSABLE_NON_AUTHORIZING_REHEARSAL',
            'production_dispatch':False,'claim_consumed':False,'gates_open':list(OPEN)}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=('source-check','run-once'))
    a=p.parse_args(argv)
    try:
        if a.mode=='source-check':
            print(json.dumps(source_check(),sort_keys=True))
            return 0
        result=run_once()
        print(json.dumps(result,sort_keys=True))
        return 0 if result['status'].startswith('PASS_') else 3
    except BaseException as exc:
        print(json.dumps({'schema':SCHEMA,'status':str(exc) if isinstance(exc,RehearsalHold) else 'HOLD_'+type(exc).__name__,
                          'gates_open':list(OPEN)},sort_keys=True))
        return 3
if __name__=='__main__':raise SystemExit(main())
