from __future__ import annotations
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_terminal_bridge_v0_1 as bridge

UNIT='forprint-cf10-worker-'+'a'*24+'.service'

class Driver:
    def __init__(self,**kw):
        self.kw=kw;self.calls=[]
    def __call__(self,args):
        self.calls.append(args)
        row=dict(Id=UNIT,LoadState='loaded',ActiveState='inactive',MainPID='0',ControlGroup='',
                 User='forprint-runner',Group='forprint-runner',KillMode='control-group',
                 Result='success',ExecMainStatus='0')
        row.update(self.kw)
        return SimpleNamespace(returncode=0,stdout=('\n'.join(f'{k}={v}' for k,v in row.items())+'\n').encode())

def data(tmp_path,**kw):
    attempt=tmp_path/'cf10-r028fixture-a028';logs=attempt/'logs';logs.mkdir(parents=True)
    out=logs/'stdout.log';err=logs/'stderr.log';out.write_text('{}\n');err.write_text('')
    return dict(unit=UNIT,attempt_root=attempt,stdout_path=out,stderr_path=err,
                runner=Driver(**kw),cgroup_state=lambda _: '0')

def test_terminal_complete_requires_all_facts(tmp_path):
    x=data(tmp_path)
    r=bridge.terminal_once(**x)
    assert r['return_code']==0 and not r['worker_result_accepted'] and not r['release_allowed']
    assert r['stdout_path']==str(x['stdout_path'])
    assert '--' in x['runner'].calls[0] and 'show' in x['runner'].calls[0]

@pytest.mark.parametrize('field,value',[
    ('Id','other.service'),('LoadState','not-found'),('ActiveState','unknown'),
    ('MainPID','7'),('User','root'),('Group','root'),('KillMode','process'),
    ('Result','exit-code'),('ExecMainStatus','1')])
def test_terminal_tamper_quarantined(tmp_path,field,value):
    with pytest.raises(bridge.TerminalReadbackBlocked):bridge.terminal_once(**data(tmp_path,**{field:value}))

@pytest.mark.parametrize('state',['1','unknown',''])
def test_nonempty_or_unknown_cgroup_quarantined(tmp_path,state):
    x=data(tmp_path);x['cgroup_state']=lambda _:state
    with pytest.raises(bridge.TerminalReadbackBlocked):bridge.terminal_once(**x)

def test_active_not_misreported_as_complete(tmp_path):
    x=data(tmp_path,ActiveState='active',MainPID='1299',ControlGroup='/system.slice/'+UNIT)
    assert bridge.terminal_once(**x) is None

def test_active_bad_pid_fails_closed(tmp_path):
    x=data(tmp_path,ActiveState='active',MainPID='0',ControlGroup='/system.slice/'+UNIT)
    with pytest.raises(bridge.TerminalReadbackBlocked):bridge.terminal_once(**x)

def test_symlink_log_rejected(tmp_path):
    x=data(tmp_path);p=x['stdout_path'];p.unlink();p.symlink_to('/etc/passwd')
    with pytest.raises(bridge.TerminalReadbackBlocked):bridge.terminal_once(**x)

def test_log_path_outside_attempt_rejected(tmp_path):
    x=data(tmp_path);x['stderr_path']=tmp_path/'stderr.log';x['stderr_path'].write_text('')
    with pytest.raises(bridge.TerminalReadbackBlocked):bridge.terminal_once(**x)

def test_no_fabricated_completion_at_deadline(tmp_path):
    x=data(tmp_path,ActiveState='active',MainPID='1299',ControlGroup='/system.slice/'+UNIT)
    ticks=iter([0.,1.,2.])
    with pytest.raises(bridge.TerminalReadbackBlocked,match='TIMEOUT'):
        bridge.wait_terminal(**x,timeout_seconds=1,clock=lambda:next(ticks),sleep=lambda _:None)

def test_missing_unit_quarantined(tmp_path):
    x=data(tmp_path);x['unit']='forprint-cf10-worker-evil.service'
    with pytest.raises(bridge.TerminalReadbackBlocked):bridge.terminal_once(**x)
