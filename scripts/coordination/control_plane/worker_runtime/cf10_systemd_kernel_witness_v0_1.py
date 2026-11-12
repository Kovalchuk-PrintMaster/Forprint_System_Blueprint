"""Root-side pinned kernel witness for CF10 systemd terminal observation.

Non-authorizing. The FD is armed while the unit is held, before STARTED
callback returns and BEFORE root release. A missing cgroup is never success.
This is an in-process witness; controller death still requires independent
recovery/quarantine. No production-live switch or Worker Result acceptance.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
import os
import re
import select
import stat
import subprocess
import time

UNIT=re.compile(r'forprint-cf10-worker-[0-9a-f]{24}\.service\Z')
INVOKE=re.compile(r'[0-9a-f]{32}\Z')
CGROUP_ROOT=Path('/sys/fs/cgroup/system.slice')
PROPS=('Id','LoadState','ActiveState','SubState','MainPID','ControlGroup',
       'InvocationID','RemainAfterExit','ExitType','User','Group','KillMode',
       'Result','ExecMainStatus')

class WitnessBlocked(RuntimeError):
    pass

def deny(reason):
    raise WitnessBlocked('CF10_WITNESS_'+reason)

def show(unit:str,runner:Callable)->dict[str,str]:
    if type(unit)!=str or not UNIT.fullmatch(unit):deny('UNIT')
    args=['/usr/bin/systemctl','show','--no-pager',
          *('--property='+s for s in PROPS),'--',unit]
    try:cp=runner(args)
    except (OSError,subprocess.SubprocessError) as exc:deny('SHOW_UNAVAILABLE_'+type(exc).__name__)
    if cp.returncode!=0:deny('SHOW_FAILED')
    if type(cp.stdout)!=bytes or len(cp.stdout)>8192 or b'\0' in cp.stdout:deny('SHOW_BYTES')
    try: lines=cp.stdout.decode('utf-8','strict').splitlines()
    except UnicodeDecodeError:deny('SHOW_ENCODING')
    rows={}
    for line in lines:
        if line.count('=')!=1:deny('SHOW_MALFORMED')
        key,value=line.split('=',1)
        if key not in PROPS or key in rows or len(value)>1024:deny('SHOW_KEYS')
        rows[key]=value
    if set(rows)!=set(PROPS) or rows['Id']!=unit:deny('SHOW_IDENTITY')
    return rows

def parse_events(raw:bytes)->str:
    if type(raw)!=bytes or len(raw)>1024 or b'\0' in raw:deny('EVENT_BYTES')
    try:lines=raw.decode('ascii','strict').splitlines()
    except UnicodeDecodeError:deny('EVENT_ENCODING')
    fields={}
    for line in lines:
        parts=line.split(' ')
        if len(parts)!=2 or not parts[0].isidentifier() or parts[0] in fields \
                or parts[1] not in ('0','1'):deny('EVENT_MALFORMED')
        fields[parts[0]]=parts[1]
    if 'populated' not in fields:deny('POPULATED_ABSENT')
    return fields['populated']

def read_fd(fd:int)->str:
    if type(fd)!=int or fd<0:deny('FD_INVALID')
    try:
        os.lseek(fd,0,os.SEEK_SET)
        return parse_events(os.read(fd,1025))
    except OSError as exc:deny('FD_LOST_'+type(exc).__name__)

@dataclass
class KernelWitness:
    unit:str
    invocation_id:str
    fd:int
    armed_populated:str='1'
    closed:bool=False
    anchor_fd:int|None=None  # pinned cgroup directory inode; never proof by itself

    def close(self)->None:
        if not self.closed:
            self.closed=True
            try:
                os.close(self.fd)
            finally:
                if self.anchor_fd is not None:
                    os.close(self.anchor_fd)
                    self.anchor_fd=None

    def wait_zero(self,*,timeout_seconds:int,clock=time.monotonic,sleep=time.sleep)->dict:
        if self.closed:deny('CLOSED')
        if type(timeout_seconds)!=int or not 1<=timeout_seconds<=7200:deny('TIMEOUT')
        if read_fd(self.fd)!='1' and self.armed_populated!='1':deny('NOT_ARMED')
        until=clock()+timeout_seconds
        samples=['1']
        poller=select.poll()
        poller.register(self.fd,select.POLLPRI|select.POLLERR)
        while clock()<until:
            current=read_fd(self.fd)
            if current!=samples[-1]:samples.append(current)
            if current=='0':
                return {'kernel_observation':'PINNED_FD_READ',
                        'transition':'1_TO_0','samples':samples,
                        'unit':self.unit,'invocation_id':self.invocation_id}
            poller.poll(50)
        deny('ZERO_NOT_OBSERVED_MANUAL_RECONCILIATION')

    def retained_terminal(self,runner:Callable)->dict:
        if self.closed:deny('CLOSED')
        rows=show(self.unit,runner)
        if rows['InvocationID']!=self.invocation_id:deny('INVOCATION_DRIFT')
        if rows['LoadState']!='loaded' or rows['RemainAfterExit']!='yes' or rows['ExitType']!='cgroup':
            deny('UNIT_NOT_RETAINED')
        if (rows['User']!='forprint-runner' or rows['Group']!='forprint-runner'
                or rows['KillMode']!='control-group'):deny('RUNNER_IDENTITY')
        if (rows['ActiveState']!='active' or rows['SubState']!='exited'
                or rows['MainPID'] not in ('0','') or rows['Result']!='success'
                or rows['ExecMainStatus']!='0'):
            deny('TERMINAL_NOT_SUCCESSFUL')
        return {'systemd_result':'success','exec_main_status':'0',
                'invocation_id':self.invocation_id,'unit':self.unit,
                'retained':True}

def arm(unit:str,runner:Callable,*,kernel_root:Path=CGROUP_ROOT,
        require_root:bool=True)->KernelWitness:
    if require_root and os.geteuid()!=0:deny('ROOT_REQUIRED')
    rows=show(unit,runner)
    if (rows['LoadState']!='loaded' or rows['ActiveState']!='active'
            or rows['MainPID'] in ('','0') or not rows['MainPID'].isdigit()
            or int(rows['MainPID'])<2 or rows['ControlGroup']!='/system.slice/'+unit
            or rows['User']!='forprint-runner' or rows['Group']!='forprint-runner'
            or rows['KillMode']!='control-group'
            or rows['RemainAfterExit']!='yes' or rows['ExitType']!='cgroup'
            or not INVOKE.fullmatch(rows['InvocationID'])):
        deny('HELD_IDENTITY_NOT_PROVEN')
    path=kernel_root/unit
    anchor_fd=None
    fd=None
    success=False
    try:
        st=path.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or path.is_symlink():deny('GROUP_INODE')
        # Hold the cgroup directory inode before opening its events file.
        # O_NOFOLLOW and a matching inode block path substitution races.
        anchor_fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC|os.O_NOFOLLOW)
        anchor_stat=os.fstat(anchor_fd)
        if (not stat.S_ISDIR(anchor_stat.st_mode) or anchor_stat.st_uid!=0
                or (anchor_stat.st_dev,anchor_stat.st_ino)!=(st.st_dev,st.st_ino)):
            deny('GROUP_ANCHOR_INODE_DRIFT')
        fd=os.open('cgroup.events',os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK,
                   dir_fd=anchor_fd)
        fst=os.fstat(fd)
        if not stat.S_ISREG(fst.st_mode) or fst.st_uid!=0:deny('EVENT_INODE')
        if read_fd(fd)!='1':deny('NOT_POPULATED_AT_ARM')
        # Only after the held-profile and populated=1 proof may this be returned.
        success=True
        return KernelWitness(unit,rows['InvocationID'],fd,anchor_fd=anchor_fd)
    except (OSError,FileNotFoundError) as exc:
        deny('GROUP_UNAVAILABLE_'+type(exc).__name__)
    finally:
        # Ownership transfers to KernelWitness only on successful return.
        if not success:
            if fd is not None:os.close(fd)
            if anchor_fd is not None:os.close(anchor_fd)
