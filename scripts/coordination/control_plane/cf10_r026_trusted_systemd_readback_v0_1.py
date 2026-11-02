"""CF-10 r026: root-side systemd and cgroup readback for canonical recovery.

Read-only and non-authorizing: does not start, stop, reset, reload, write a
receipt/ledger, retry an attempt, prove production quiescence, or accept results.
A root caller must independently authorize any later action. No worker-supplied
service status is accepted by this collector.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import subprocess
from typing import Callable

from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as review

SYSTEMCTL = '/usr/bin/systemctl'
CGROUP_ROOT = Path('/sys/fs/cgroup/system.slice')
PROPS = ('Id','LoadState','ActiveState','MainPID','ControlGroup','User','Group','KillMode')
PROVENANCE = 'ROOT_SYSTEMCTL_SHOW_READBACK'

class ReadbackBlocked(RuntimeError):
    pass

def block(reason: str):
    raise ReadbackBlocked('CF10_R026_' + reason)

def _decode_show(raw: bytes, unit: str) -> dict[str,str]:
    if not isinstance(raw,bytes) or len(raw)>8192 or b'\0' in raw:
        block('SHOW_SIZE_OR_ENCODING')
    try:
        content=raw.decode('utf-8',errors='strict')
    except UnicodeError:
        block('SHOW_ENCODING')
    values={}
    for line in content.splitlines():
        if '=' not in line:
            block('SHOW_MALFORMED')
        key,value=line.split('=',1)
        if key not in PROPS or key in values or any(c in value for c in '\r\n\0'):
            block('SHOW_FIELDS')
        if len(value)>2048:
            block('SHOW_FIELD_LENGTH')
        values[key]=value
    if set(values)!=set(PROPS):
        block('SHOW_INCOMPLETE')
    if values['Id']!=unit:
        block('UNIT_ID_DRIFT')
    return values

def _read_file_nofollow(path: Path, max_bytes: int) -> bytes:
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid!=0:
            block('KERNEL_FILE_NOT_ROOT_OWNED')
        raw=os.read(fd,max_bytes+1)
        if len(raw)>max_bytes:
            block('KERNEL_FILE_OVERSIZE')
        return raw
    finally:
        os.close(fd)

def _kernel_snapshot(unit: str,group: str, *, kernel_root: Path) -> dict:
    """No absence-of-process inference from a missing cgroup directory."""
    if group != '/system.slice/'+unit:
        if group=='':
            return {'cgroup_state':'UNKNOWN_NO_CONTROL_GROUP','sampled_populated':None}
        block('CGROUP_BINDING')
    # The caller supplies kernel_root only in verified tests; production API pins it.
    path=kernel_root / unit
    try:
        st=path.lstat()
    except FileNotFoundError:
        return {'cgroup_state':'REMOVED_NOT_PROOF','sampled_populated':None}
    if not stat.S_ISDIR(st.st_mode) or st.st_uid!=0 or path.is_symlink():
        block('CGROUP_INODE')
    try:
        raw=_read_file_nofollow(path/'cgroup.events',1024)
    except FileNotFoundError:
        return {'cgroup_state':'UNKNOWN_NO_EVENTS','sampled_populated':None}
    fields={}
    for line in raw.decode('ascii','strict').splitlines():
        pair=line.split()
        if len(pair)!=2 or pair[0] in fields or pair[1] not in ('0','1'):
            block('CGROUP_EVENTS_MALFORMED')
        fields[pair[0]]=pair[1]
    if 'populated' not in fields:
        block('CGROUP_POPULATED_ABSENT')
    populated=fields['populated']
    return {'cgroup_state':'POPULATED' if populated=='1' else 'EMPTY_AT_SAMPLE',
            'sampled_populated':populated}

def _collect(identity: review.ReadbackIdentity,
             *, runner: Callable[[list[str]], subprocess.CompletedProcess],
             kernel_root: Path) -> dict:
    identity.validate()
    args=[SYSTEMCTL,'show','--no-pager',
          *('--property='+prop for prop in PROPS),'--',identity.unit]
    try:
        cp=runner(args)
    except (OSError,subprocess.SubprocessError) as exc:
        block('SHOW_UNAVAILABLE_'+type(exc).__name__)
    if cp.returncode!=0:
        block('SYSTEMCTL_RETURN_CODE')
    vals=_decode_show(cp.stdout,identity.unit)
    try:
        pid=int(vals['MainPID'])
    except ValueError:
        block('MAIN_PID_NOT_INTEGER')
    if str(pid)!=vals['MainPID'] or pid<0:
        block('MAIN_PID_INVALID')
    status={'unit':identity.unit,'attempt_id':identity.attempt_id,
            'source_head':identity.head,'load_state':vals['LoadState'],
            'active_state':vals['ActiveState'],'main_pid':pid,
            'control_group':vals['ControlGroup'],'user':vals['User'],
            'group':vals['Group'],'kill_mode':vals['KillMode'],
            'provenance':PROVENANCE}
    # Independently validate observation under strict r025 contract.
    review._trusted_service(identity,status)
    kernel=_kernel_snapshot(identity.unit,vals['ControlGroup'],kernel_root=kernel_root)
    if status['active_state'] in ('active','activating','deactivating') and kernel['cgroup_state']!='POPULATED':
        block('ACTIVE_UNIT_WITHOUT_POPULATED_CGROUP')
    if status['active_state'] in ('inactive','failed') and kernel['cgroup_state']=='POPULATED':
        kernel['cgroup_state']='INACTIVE_BUT_POPULATED'
    return {'schema_version':'cf10_r026_root_systemd_readback_v0_1',
            'systemctl':status,'kernel':kernel,
            'read_only':True,'automatic_retry':False,'release_allowed':False,
            'production_quiescence_proven':False}

def collect(identity: review.ReadbackIdentity) -> dict:
    """Only root can call the production read-only collector (no injected runner)."""
    if os.geteuid()!=0:
        block('ROOT_REQUIRED')
    def runner(args):
        return subprocess.run(args,capture_output=True,check=False,timeout=8,
                              stdin=subprocess.DEVNULL,env={'PATH':'/usr/bin:/bin','LANG':'C'})
    return _collect(identity,runner=runner,kernel_root=CGROUP_ROOT)

def reconcile_without_side_effects(*,identity:review.ReadbackIdentity,
                                   receipt_summary:dict|None,ledger_rows:list[dict],
                                   claim_path_occupied:bool)->dict:
    """Trusted readback into r025. Caller supplies independently checked ledger/receipt."""
    captured=collect(identity)
    report=review.decide(identity=identity,receipt_summary=receipt_summary,
                         ledger_rows=ledger_rows,service=captured['systemctl'],
                         claim_path_occupied=claim_path_occupied)
    # A potentially populated cgroup is ALWAYS manual review, including when
    # systemctl itself reports inactive. Never infer successful completion.
    if captured['kernel']['cgroup_state'] in ('POPULATED','INACTIVE_BUT_POPULATED'):
        report={**report,'state':'BLOCKED_CGROUP_MAY_CONTAIN_PROCESSES'}
    return {'schema_version':'cf10_r026_systemd_ledger_receipt_readonly_join_v0_1',
            'readback':captured,'recovery':report,'automatic_retry':False,
            'production_launch_allowed':False,'release_allowed':False}
