"""R029 source-bound output and terminal consistency; no production launch."""
from pathlib import Path
from types import SimpleNamespace
import os
import pytest
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bounds
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_terminal_bridge_v0_1 as bridge
ATTEMPT='cf10-r029test-a029'
UNIT='forprint-cf10-worker-'+'f'*24+'.service'
def spec():
    return bounds.BoundedInput('cf10-r029test',ATTEMPT,'a'*40,'b'*64,'c'*64,
      str(launcher.RUNTIME/'forprint_system_blueprint/worker-01'/ATTEMPT/'workspace/repo'),
      str(launcher.RUNTIME),('/usr/bin/true',),30)
def test_stream_paths_are_bound_not_caller_controlled():
    s=spec();plan=bounds.bind_plan(s)
    cmd=launcher.build_command(s,plan,launcher.GATES/('manifest-'+'a'*64+'.json'))
    root=str(launcher.RUNTIME/'forprint_system_blueprint/worker-01'/ATTEMPT/'logs')
    assert '--property=StandardOutput=append:'+root+'/stdout.log' in cmd
    assert '--property=StandardError=append:'+root+'/stderr.log' in cmd
    assert '--property=ReadWritePaths='+s.workspace+' '+root in cmd
    assert not any('/tmp/' in part for part in cmd)
def test_no_trusted_claim_of_removed_cgroup(tmp_path):
    attempt=tmp_path/'cf10-r029test-a029';logs=attempt/'logs';logs.mkdir(parents=True)
    (logs/'stdout.log').write_text('hello\n');(logs/'stderr.log').write_text('')
    props=dict(Id=UNIT,LoadState='loaded',ActiveState='inactive',MainPID='0',ControlGroup='',
         User='forprint-runner',Group='forprint-runner',KillMode='control-group',
         Result='success',ExecMainStatus='0')
    def systemctl(_):return SimpleNamespace(returncode=0,stdout=('\n'.join(k+'='+v for k,v in props.items())+'\n').encode())
    kwargs=dict(unit=UNIT,attempt_root=attempt,stdout_path=logs/'stdout.log',
        stderr_path=logs/'stderr.log',runner=systemctl)
    with pytest.raises(bridge.TerminalReadbackBlocked,match='CGROUP'):
        bridge.terminal_once(**kwargs,cgroup_state=lambda _: 'removed')
    assert bridge.terminal_once(**kwargs,cgroup_state=lambda _: '0')['return_code']==0
def test_log_directory_symlink_rejected(tmp_path):
    attempt=tmp_path/'cf10-r029test-a029';attempt.mkdir()
    outer=tmp_path/'elsewhere';outer.mkdir()
    (outer/'stdout.log').write_text('x')
    (outer/'stderr.log').write_text('')
    (attempt/'logs').symlink_to(outer,target_is_directory=True)
    with pytest.raises(bridge.TerminalReadbackBlocked,match='LOG_NOT_REGULAR'):
        bridge._log(attempt/'logs/stdout.log',attempt/'logs')
def test_log_directory_world_writable_rejected(tmp_path):
    logs=tmp_path/'logs';logs.mkdir();logs.chmod(0o777)
    file=logs/'stdout.log';file.write_text('x')
    with pytest.raises(bridge.TerminalReadbackBlocked,match='LOG_DIRECTORY_UNTRUSTED'):
        bridge._log(file,logs)
def test_log_file_group_writable_rejected(tmp_path):
    logs=tmp_path/'logs';logs.mkdir();file=logs/'stdout.log';file.write_text('x');file.chmod(0o666)
    with pytest.raises(bridge.TerminalReadbackBlocked,match='LOG_INODE'):
        bridge._log(file,logs)
def test_unprivileged_live_backend_stays_sealed():
    assert launcher.LIVE_CUTOVER_ENABLED is False

@pytest.mark.skipif(os.geteuid()!=0,reason='root log inode integration fixture')
def test_root_log_reservation_exclusive_and_empty(tmp_path,monkeypatch):
    runtime=tmp_path/'runtime';logs=runtime/'forprint_system_blueprint/worker-01'/ATTEMPT/'logs';logs.mkdir(parents=True)
    monkeypatch.setattr(launcher,'RUNTIME',runtime)
    monkeypatch.setattr(launcher.storage,'require_persistent_path',lambda *a,**kw:logs)
    launcher._reserve_root_logs(spec())
    assert (logs/'stdout.log').stat().st_uid==0
    assert (logs/'stdout.log').read_bytes()==b''
    assert (logs/'stderr.log').read_bytes()==b''
    with pytest.raises(launcher.SystemdLaunchBlocked,match='LOG_ALREADY_PRESENT'):
        launcher._reserve_root_logs(spec())

@pytest.mark.skipif(os.geteuid()!=0,reason='root log inode integration fixture')
def test_root_log_reservation_rejects_symlink(tmp_path,monkeypatch):
    runtime=tmp_path/'runtime';logs=runtime/'forprint_system_blueprint/worker-01'/ATTEMPT/'logs';logs.mkdir(parents=True)
    secret=tmp_path/'unrelated';secret.write_text('sensitive')
    (logs/'stdout.log').symlink_to(secret)
    monkeypatch.setattr(launcher,'RUNTIME',runtime)
    monkeypatch.setattr(launcher.storage,'require_persistent_path',lambda *a,**kw:logs)
    with pytest.raises(launcher.SystemdLaunchBlocked,match='LOG_ALREADY_PRESENT'):
        launcher._reserve_root_logs(spec())
    assert secret.read_text()=='sensitive'

@pytest.mark.skipif(os.geteuid()!=0,reason='root log inode integration fixture')
def test_root_log_reservation_rejects_nonroot_dir(tmp_path,monkeypatch):
    runtime=tmp_path/'runtime';logs=runtime/'forprint_system_blueprint/worker-01'/ATTEMPT/'logs';logs.mkdir(parents=True)
    logs.chmod(0o777)
    monkeypatch.setattr(launcher,'RUNTIME',runtime)
    monkeypatch.setattr(launcher.storage,'require_persistent_path',lambda *a,**kw:logs)
    with pytest.raises(launcher.SystemdLaunchBlocked,match='LOG_DIRECTORY_UNTRUSTED'):
        launcher._reserve_root_logs(spec())
    assert not list(logs.iterdir())
