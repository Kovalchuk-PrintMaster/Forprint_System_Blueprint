"""CF-10 guarded systemd terminal result bridge, read-only until canonical cutover.

The original launcher returns a synchronous process result. A transient systemd
launch is not equivalent: STARTED/service active is not worker completion.
This bridge converts trustworthy terminal systemd + kernel observations to the
same minimum result fields, or fails closed with no claim of completion.

Non-authorizing: does not start, stop, retry, release, or accept a Worker.
"""
from __future__ import annotations
from collections.abc import Callable
from pathlib import Path
import os
import re
import stat
import subprocess
import time

UNIT=re.compile(r'forprint-cf10-worker-[a-f0-9]{24}\.service\Z')
PROPS=('Id','LoadState','ActiveState','MainPID','ControlGroup','User','Group','KillMode','Result','ExecMainStatus')

class TerminalReadbackBlocked(RuntimeError):
    pass

def deny(reason):
    raise TerminalReadbackBlocked('CF10_TERMINAL_'+reason)

def _read(unit:str, runner:Callable)->dict[str,str]:
    if not isinstance(unit,str) or not UNIT.fullmatch(unit):deny('UNIT_IDENTITY')
    args=['/usr/bin/systemctl','show','--no-pager',*['--property='+x for x in PROPS],'--',unit]
    data=runner(args)
    if data.returncode!=0:deny('SYSTEMCTL_FAILED')
    try:
        raw=data.stdout.decode('utf-8','strict')
        if len(raw)>8192:deny('SHOW_TOO_LARGE')
        rows={}
        for line in raw.splitlines():
            if line.count('=')!=1:deny('SHOW_MALFORMED')
            key,value=line.split('=',1)
            if key not in PROPS or key in rows:deny('SHOW_KEYS')
            rows[key]=value
    except (AttributeError,UnicodeDecodeError):deny('SHOW_ENCODING')
    if set(rows)!=set(PROPS) or rows['Id']!=unit:deny('SHOW_IDENTITY')
    return rows

def _log(path:Path,expected:Path)->str:
    if not isinstance(path,(str,Path)):deny('LOG_PATH')
    p=Path(path)
    if not p.is_absolute() or '..' in p.parts or p.name not in ('stdout.log','stderr.log') or p.parent!=expected:
        deny('LOG_SCOPE')
    if p.is_symlink() or p.parent.is_symlink() or not p.is_file():deny('LOG_NOT_REGULAR')
    s=p.lstat()
    d=p.parent.lstat()
    if (not stat.S_ISDIR(d.st_mode) or d.st_uid!=0 or
            stat.S_IMODE(d.st_mode)&0o022):deny('LOG_DIRECTORY_UNTRUSTED')
    if (not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_uid not in (0,996)
            or stat.S_IMODE(s.st_mode)&0o022):deny('LOG_INODE')
    return str(p)

def terminal_once(*,unit:str,attempt_root:Path,stdout_path:Path,stderr_path:Path,
                  runner:Callable,cgroup_state:Callable[[str],str]) -> dict|None:
    """Return completed result only for proven terminal unit AND empty cgroup.

    None means still active; all missing/inconsistent facts are quarantine errors.
    """
    unit_rows=_read(unit,runner)
    if unit_rows['LoadState']!='loaded':deny('UNIT_UNLOADED_OR_UNKNOWN')
    active=unit_rows['ActiveState']
    if unit_rows['User']!='forprint-runner' or unit_rows['Group']!='forprint-runner' or unit_rows['KillMode']!='control-group':
        deny('RUNNER_OR_GROUP_MISMATCH')
    if active in ('active','activating','deactivating'):
        if (not unit_rows['MainPID'].isdigit() or int(unit_rows['MainPID'])<2 or
            unit_rows['ControlGroup']!='/system.slice/'+unit):deny('ACTIVE_UNIT_UNTRUSTED')
        return None
    if active not in ('inactive','failed'):deny('ACTIVE_STATE_UNKNOWN')
    if unit_rows['MainPID'] not in ('0',''):deny('TERMINAL_PID_NOT_REAPED')
    state=cgroup_state(unit)
    # Missing cgroup is NOT kernel proof of emptiness (r026 invariant).
    # A trusted observer must have witnessed populated=0; unknown/unloaded
    # stays in manual reconciliation rather than claiming Worker success.
    if state != '0':deny('CGROUP_NOT_EMPTY_OR_UNKNOWN')
    if unit_rows['Result']!='success':deny('SYSTEMD_NON_SUCCESS_RESULT')
    if unit_rows['ExecMainStatus']!='0':deny('NONZERO_EXIT_OR_UNKNOWN')
    # A successful systemd result is not proof of a valid Worker Result. It is
    # merely eligible for independent materialization/verification upstream.
    attempt=Path(attempt_root)
    if not attempt.is_absolute() or attempt.is_symlink() or not attempt.name.startswith('cf10-'):
        deny('ATTEMPT_ROOT')
    logs=attempt/'logs'
    out=_log(stdout_path,logs)
    err=_log(stderr_path,logs)
    return {'return_code':0,'timed_out':False,'outcome':'completed',
            'stdout_path':out,'stderr_path':err,'systemd_unit':unit,
            'process_started':True,'automatic_retry':False,
            'worker_result_accepted':False,'release_allowed':False,
            'quiescence_observation':'KERNEL_CGROUP_EMPTY_NON_AUTHORIZING'}

def wait_terminal(*,unit:str,attempt_root:Path,stdout_path:Path,stderr_path:Path,
                  runner:Callable,cgroup_state:Callable[[str],str],
                  timeout_seconds:int, clock:Callable=time.monotonic,
                  sleep:Callable=time.sleep, interval:float=.25)->dict:
    if type(timeout_seconds)!=int or timeout_seconds<=0 or timeout_seconds>7200:deny('TIMEOUT')
    if not (.01<=interval<=1):deny('INTERVAL')
    until=clock()+timeout_seconds
    while True:
        result=terminal_once(unit=unit,attempt_root=attempt_root,
            stdout_path=stdout_path,stderr_path=stderr_path,
            runner=runner,cgroup_state=cgroup_state)
        if result is not None:return result
        if clock()>=until:deny('TIMEOUT_MANUAL_RECONCILIATION_REQUIRED')
        sleep(interval)
