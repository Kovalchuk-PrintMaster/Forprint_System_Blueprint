"""Non-authorizing unit tests for pinned cgroup witness → retained systemd → terminal bridge."""
from pathlib import Path
from types import SimpleNamespace
import os
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kw
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_terminal_bridge_v0_1 as bridge
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route

UNIT='forprint-cf10-worker-'+'a'*24+'.service'
INV='b'*32

def rows(*,active='active',sub='running',pid='2468',inv=INV,load='loaded',result='success',exit='0'):
    return dict(Id=UNIT,LoadState=load,ActiveState=active,SubState=sub,MainPID=pid,
                ControlGroup='/system.slice/'+UNIT,InvocationID=inv,RemainAfterExit='yes',
                ExitType='cgroup',User='forprint-runner',Group='forprint-runner',
                KillMode='control-group',Result=result,ExecMainStatus=exit)

def runner(data):
    def run(args):
        assert args[:3]==['/usr/bin/systemctl','show','--no-pager']
        return SimpleNamespace(returncode=0, stdout=('\n'.join(f'{k}={v}' for k,v in data.items())+'\n').encode())
    return run

def fs(tmp_path,raw=b'populated 1\nfrozen 0\n'):
    root=tmp_path/'system.slice';root.mkdir()
    group=root/UNIT;group.mkdir()
    (group/'cgroup.events').write_bytes(raw)
    return root,group

def test_arm_is_pinned_to_same_inode(tmp_path):
    root,group=fs(tmp_path)
    w=kw.arm(UNIT,runner(rows()),kernel_root=root)
    try:
        (group/'cgroup.events').unlink()
        (group/'cgroup.events').write_bytes(b'populated 1\n')
        # FD is pinned to the removed inode, not the new path.
        # In Linux procfs/cgroupfs the inode stays readable while the group exists.
        assert kw.read_fd(w.fd)=='1'
    finally:w.close()

def test_actual_one_to_zero(tmp_path):
    root,group=fs(tmp_path)
    w=kw.arm(UNIT,runner(rows()),kernel_root=root)
    try:
        (group/'cgroup.events').write_bytes(b'populated 0\nfrozen 0\n')
        proof=w.wait_zero(timeout_seconds=1)
        assert proof['transition']=='1_TO_0'
        assert proof['invocation_id']==INV
    finally:w.close()

def test_retained_systemd_accepts_only_exact_invocation(tmp_path):
    root,group=fs(tmp_path)
    w=kw.arm(UNIT,runner(rows()),kernel_root=root)
    try:
        result=w.retained_terminal(runner(rows(active='active',sub='exited',pid='0')))
        assert result['retained'] is True
        with pytest.raises(kw.WitnessBlocked,match='INVOCATION_DRIFT'):
            w.retained_terminal(runner(rows(active='active',sub='exited',pid='0',inv='e'*32)))
    finally:w.close()

@pytest.mark.parametrize('mutation,expected',[
    ({'ExitType':'main'},'HELD_IDENTITY'),
    ({'RemainAfterExit':'no'},'HELD_IDENTITY'),
    ({'User':'root'},'HELD_IDENTITY'),
    ({'InvocationID':'x'},'HELD_IDENTITY'),
    ({'ControlGroup':'/broken'},'HELD_IDENTITY'),
    ({'MainPID':'0'},'HELD_IDENTITY'),
    ({'ActiveState':'inactive'},'HELD_IDENTITY'),
])
def test_unsafe_arm_fails(tmp_path,mutation,expected):
    root,_=fs(tmp_path)
    r=rows();r.update(mutation)
    with pytest.raises(kw.WitnessBlocked,match=expected):
        kw.arm(UNIT,runner(r),kernel_root=root)

@pytest.mark.parametrize('raw',[
    b'',b'populated 2\n',b'populated 1\npopulated 0\n',b'populated 1 0\n',
    b'populated -1\n',b'populated 1\nzzz=4\n',b'populated 1\x00\n',
])
def test_malformed_events_fail(tmp_path,raw):
    root,_=fs(tmp_path,raw)
    with pytest.raises(kw.WitnessBlocked):kw.arm(UNIT,runner(rows()),kernel_root=root)

def test_missing_or_forged_unit_rejected(tmp_path):
    root,_=fs(tmp_path)
    with pytest.raises(kw.WitnessBlocked):kw.arm('bad.service',runner(rows()),kernel_root=root)
    forged=rows();forged['Id']='other'
    with pytest.raises(kw.WitnessBlocked):kw.arm(UNIT,runner(forged),kernel_root=root)

def test_cgroup_missing_not_success(tmp_path):
    root=tmp_path/'system.slice';root.mkdir()
    with pytest.raises(kw.WitnessBlocked,match='GROUP_UNAVAILABLE'):
        kw.arm(UNIT,runner(rows()),kernel_root=root)

def test_terminal_bridge_real_witness(tmp_path):
    root,group=fs(tmp_path)
    w=kw.arm(UNIT,runner(rows()),kernel_root=root)
    attempt=tmp_path/'cf10-test-a034';attempt.mkdir()
    logs=attempt/'logs';logs.mkdir(mode=0o700)
    (logs/'stdout.log').write_bytes(b'ok\n');(logs/'stderr.log').write_bytes(b'')
    try:
        (group/'cgroup.events').write_bytes(b'populated 0\n')
        result=bridge.witnessed_terminal(unit=UNIT,attempt_root=attempt,
            stdout_path=logs/'stdout.log',stderr_path=logs/'stderr.log',
            witness=w,runner=runner(rows(active='active',sub='exited',pid='0')),
            timeout_seconds=1)
        assert result['return_code']==0
        assert result['worker_result_accepted'] is False
        assert result['systemd_invocation_id']==INV
        assert result['quiescence_observation'].startswith('PINNED_KERNEL_1_TO_0')
    finally:w.close()

def test_nonzero_retained_result_blocked(tmp_path):
    root,group=fs(tmp_path)
    w=kw.arm(UNIT,runner(rows()),kernel_root=root)
    try:
        (group/'cgroup.events').write_bytes(b'populated 0\n')
        with pytest.raises(kw.WitnessBlocked,match='TERMINAL_NOT_SUCCESSFUL'):
            w.retained_terminal(runner(rows(active='active',sub='exited',pid='0',result='exit-code',exit='2')))
    finally:w.close()

def test_closed_witness_rejected(tmp_path):
    root,group=fs(tmp_path)
    w=kw.arm(UNIT,runner(rows()),kernel_root=root)
    w.close()
    with pytest.raises(bridge.TerminalReadbackBlocked,match='WITNESS_IDENTITY'):
        bridge.witnessed_terminal(unit=UNIT,attempt_root=tmp_path,stdout_path=tmp_path/'stdout.log',
          stderr_path=tmp_path/'stderr.log',witness=w,runner=runner(rows()),timeout_seconds=1)

def test_backend_has_retained_cgroup_lifecycle():
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    spec=bound.BoundedInput('test-r034','cf10-r034-test-a034','a'*40,'b'*64,'c'*64,
        str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/workspace/repo'),
        str(backend.RUNTIME),('/usr/bin/true',),10)
    plan=bound.bind_plan(spec)
    cmd=backend.build_command(spec,plan,backend.GATES/('manifest-'+'f'*64+'.json'))
    assert '--remain-after-exit' in cmd
    assert '--property=ExitType=cgroup' in cmd
    assert backend.LIVE_CUTOVER_ENABLED is False

def test_route_closes_witness_if_backend_fails(monkeypatch):
    class Probe:
        def __init__(self):self.closed=False
        def close(self):self.closed=True
    p=Probe()
    args={
        'root':backend.BLUEPRINT,'runtime_root':backend.RUNTIME,
        'task_prompt_id':'test-r034','attempt_id':'cf10-r034-test-a034',
        'source_head':'a'*40,'baseline_sha256':'b'*64,'handoff_sha256':'c'*64,
        'launch_values':{'argv':['/usr/bin/true'],
          'cwd':str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/workspace/repo'),
          'stdout_path':str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/logs/stdout.log'),
          'stderr_path':str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/logs/stderr.log'),
          'timeout_seconds':15},'started_callback':lambda _:None}
    monkeypatch.setattr(route,'assert_cutover_ready',lambda:None)
    monkeypatch.setattr(route.os,'geteuid',lambda:0)
    monkeypatch.setattr(route.witness,'arm',lambda *_:p)
    monkeypatch.setattr(route.durable,'record_pre',lambda **kw:None)
    monkeypatch.setattr(route.durable,'record_terminal',lambda **kw:None)
    def fail_after_callback(**kw):
        kw['started_callback']({'unit':UNIT})
        raise RuntimeError('LEDGER_FAIL')
    monkeypatch.setattr(backend,'launch_after_owner_claim',fail_after_callback)
    with pytest.raises(RuntimeError,match='LEDGER_FAIL'):route.run_once(**args)
    assert p.closed is True

def test_terminal_observer_armed_before_ledger(monkeypatch):
    states=[]
    class Probe:
        def __init__(self):self.closed=False
        def close(self):self.closed=True
    p=Probe()
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
    def arm(*_):states.append('arm');return p
    monkeypatch.setattr(route,'assert_cutover_ready',lambda:None)
    monkeypatch.setattr(route.os,'geteuid',lambda:0)
    monkeypatch.setattr(route.witness,'arm',arm)
    monkeypatch.setattr(route.durable,'record_pre',lambda **kw:states.append('persist_pre'))
    monkeypatch.setattr(route.durable,'record_terminal',lambda **kw:states.append('persist_terminal'))
    monkeypatch.setattr(route,'_retire_after_durable_terminal',lambda unit:states.append('retire_after_durable'))
    def launch(**kw):
        kw['started_callback']({'unit':UNIT})
        states.append('release')
        return {'state':'SYSTEMD_RELEASED_OBSERVE_WORKER',
                'unit':bound.unit_for('cf10-r034-test-a034','a'*40),'process_started':True}
    monkeypatch.setattr(backend,'launch_after_owner_claim',launch)
    monkeypatch.setattr(route.terminal,'witnessed_terminal',lambda **_:dict(return_code=0,worker_result_accepted=False))
    args=dict(root=backend.BLUEPRINT,runtime_root=backend.RUNTIME,task_prompt_id='test-r034',
              attempt_id='cf10-r034-test-a034',source_head='a'*40,baseline_sha256='b'*64,
              handoff_sha256='c'*64,started_callback=lambda _:states.append('ledger'),
              launch_values={'argv':['/usr/bin/true'],
                'cwd':str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/workspace/repo'),
                'stdout_path':str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/logs/stdout.log'),
                'stderr_path':str(backend.RUNTIME/'forprint_system_blueprint/worker-01/cf10-r034-test-a034/logs/stderr.log'),
                'timeout_seconds':15})
    route.run_once(**args)
    assert states==['arm','persist_pre','ledger','release','persist_terminal','retire_after_durable']
    assert p.closed
