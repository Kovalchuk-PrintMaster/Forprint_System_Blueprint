"""Root-only isolated transaction tests. No production systemd/attempts touched."""
from __future__ import annotations
import json,os,time
from pathlib import Path
from types import SimpleNamespace
import hashlib
import pytest

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as supervisor
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launch
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_gate_entry_v0_1 as gate

HEAD='a'*40
HANDOFF='b'*64
BASELINE='c'*64
ATTEMPT='cf10-test-gated-a027'

class Driver:
    def __init__(self,unit):self.unit=unit;self.live=False;self.stop_count=0;self.commands=[];self.fail_run=False;self.invalid_active=False
    def __call__(self,args):
        self.commands.append(args)
        if args[0]==launch.SYSTEMD_RUN:
            if self.fail_run:return SimpleNamespace(returncode=1,stdout=b'',stderr=b'')
            self.live=True
            return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
        if args[:2]==[launch.SYSTEMCTL,'stop']:
            self.stop_count+=1;self.live=False
            return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
        assert args[:2]==[launch.SYSTEMCTL,'show']
        out={
            'Id':self.unit,'LoadState':'loaded' if self.live else 'not-found',
            'ActiveState':'active' if self.live else 'inactive','MainPID':'23456' if self.live else '0',
            'ControlGroup':'/system.slice/'+self.unit if self.live else '',
            'User':'forprint-runner' if self.live else '',
            'Group':'forprint-runner' if self.live else '',
            'KillMode':'control-group','Result':'success','ExecMainStatus':'0'}
        if self.invalid_active and self.live:out['User']='root'
        return SimpleNamespace(returncode=0,stdout=('\n'.join(k+'='+v for k,v in out.items())+'\n').encode(),stderr=b'')

@pytest.fixture
def transaction(tmp_path):
    if os.geteuid()!=0:pytest.skip('Root-only disposable test; no production mutations')
    p=tmp_path/'fixture';p.mkdir()
    store=p/'receipts';store.mkdir(mode=0o700)
    gates=p/'gates';gates.mkdir(mode=0o711)
    # BoundedInput and hash validation only; fixture cwd need not exist for launcher tests.
    workspace='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+ATTEMPT+'/workspace/repo'
    spec=supervisor.BoundedInput('cf10-task-gated',ATTEMPT,HEAD,HANDOFF,BASELINE,workspace,
        str(launch.RUNTIME),('/usr/bin/true',),15)
    plan=supervisor.bind_plan(spec)
    driver=Driver(plan['identity']['unit'])
    return p,store,gates,spec,plan,driver

def do(transaction,callback=None):
    p,store,gates,spec,plan,driver=transaction
    return launch._core(spec=spec,plan=plan,started_callback=callback or (lambda row:None),
         runner=driver,root=p,gate_dir=gates,store=store,require_real_roots=False,sleep=lambda _:None)

def test_production_rejects_without_cutover(transaction):
    _,_,_,spec,plan,_=transaction
    with pytest.raises(launch.SystemdLaunchBlocked,match='CUTOVER_NOT_AUTHORIZED'):
        launch.launch_after_owner_claim(spec=spec,plan=plan,started_callback=lambda _:None)

def test_no_worker_root_in_systemd_command(transaction):
    _,_,_,spec,plan,_=transaction
    cmd=launch.build_command(spec,plan,launch.GATES/('manifest-'+'f'*64+'.json'))
    assert '--property=User=forprint-runner' in cmd
    assert '--property=Group=forprint-runner' in cmd
    assert '--property=KillMode=control-group' in cmd
    assert '--property=Restart=no' in cmd
    assert '--property=ProtectSystem=strict' in cmd
    assert cmd[-5:-3]==[launch.PYTHON,'-I']
    assert cmd[-1].startswith(str(launch.GATES))
    assert '/usr/bin/true' not in cmd  # argv is sealed inside root-owned manifest

def test_release_is_after_started_ledger_callback(transaction):
    p,store,gates,spec,plan,driver=transaction
    sequence=[]
    def callback(row):
        sequence.append('started-ledger')
        assert row['unit']==plan['identity']['unit']
        assert len(list(gates.glob('manifest-*.json')))==1
        assert list(gates.glob('release-*.json'))==[]
    result=do(transaction,callback)
    assert sequence==['started-ledger']
    assert result['state']=='SYSTEMD_RELEASED_OBSERVE_WORKER'
    assert result['release_allowed'] is False
    manifest=list(gates.glob('manifest-*.json'))[0]
    release=list(gates.glob('release-*.json'))[0]
    assert json.loads(release.read_text())['manifest_sha256']==hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert len(list((store/spec.attempt_id).glob('event_*.json')))==2
    assert len([c for c in driver.commands if c[0]==launch.SYSTEMD_RUN])==1

def test_consumed_attempt_never_retried(transaction):
    do(transaction)
    _,store,_,spec,_,driver=transaction
    before=len(driver.commands)
    with pytest.raises(Exception,match='ALREADY_CONSUMED'):
        do(transaction)
    assert len(driver.commands)==before  # fail before even observing systemd
    assert list((store/spec.attempt_id).glob('0000_claim.json'))

def test_ledger_failure_never_releases(transaction):
    def fail(_):raise RuntimeError('LEDGER_FAILED')
    with pytest.raises(RuntimeError,match='LEDGER_FAILED'):do(transaction,fail)
    _,store,gates,spec,_,driver=transaction
    assert list(gates.glob('manifest-*.json'))
    assert not list(gates.glob('release-*.json'))
    assert driver.stop_count==1
    assert (store/spec.attempt_id/'0000_claim.json').exists()

def test_systemd_failure_is_consumed_and_no_release(transaction):
    _,store,gates,spec,plan,driver=transaction
    driver.fail_run=True
    with pytest.raises(launch.SystemdLaunchBlocked,match='SYSTEMD_RUN_FAILED'):do(transaction)
    assert (store/spec.attempt_id/'0000_claim.json').exists()
    assert not list(gates.glob('release-*.json'))

def test_held_service_identity_failure_stops(transaction):
    _,store,gates,spec,plan,driver=transaction
    driver.invalid_active=True
    with pytest.raises(launch.SystemdLaunchBlocked,match='HELD_SERVICE_NOT_VERIFIED'):do(transaction)
    assert driver.stop_count==1
    assert not list(gates.glob('release-*.json'))

def test_preexisting_unit_blocks_before_claim(transaction):
    _,store,_,spec,plan,driver=transaction
    driver.live=True
    with pytest.raises(launch.SystemdLaunchBlocked,match='UNIT_ALREADY_EXISTS'):do(transaction)
    assert not (store/spec.attempt_id).exists()

def test_manifest_release_bound_to_digest(transaction,monkeypatch):
    p,store,gates,spec,plan,driver=transaction
    do(transaction)
    manifest=list(gates.glob('manifest-*.json'))[0]
    monkeypatch.setattr(gate.Path,'is_dir',lambda self: True if str(self).endswith('/workspace/repo') else Path.is_dir.__wrapped__(self) if hasattr(Path.is_dir,'__wrapped__') else True)
    monkeypatch.setattr(gate.os,'geteuid',lambda:supervisor.UID)
    monkeypatch.setattr(gate.os,'getegid',lambda:supervisor.GID)
    def deny_exec(*_):raise RuntimeError('EXEC_CALLED')
    monkeypatch.setattr(gate.os,'execv',deny_exec)
    monkeypatch.setattr(gate.os,'chdir',lambda _:None)
    with pytest.raises(RuntimeError,match='EXEC_CALLED'):
        gate.wait_and_exec(manifest,root=gates)
    # Digest mismatch must fail before executing Worker.
    release=list(gates.glob('release-*.json'))[0]
    release.write_text('{"schema":"cf10_root_release_v0_1","manifest_sha256":"'+'0'*64+'"}\n')
    # root-owned mode is still correct because it was created as root.
    with pytest.raises(gate.GateBlocked,match='RELEASE_BINDING'):
        gate.wait_and_exec(manifest,root=gates)

def test_malformed_manifest_fail_closed(transaction,monkeypatch):
    _,_,gates,_,_,_=transaction
    wrong=gates/('manifest-'+'e'*64+'.json')
    wrong.write_text('{BAD')
    wrong.chmod(0o644)
    monkeypatch.setattr(gate.os,'geteuid',lambda:supervisor.UID)
    monkeypatch.setattr(gate.os,'getegid',lambda:supervisor.GID)
    with pytest.raises(gate.GateBlocked,match='MANIFEST_JSON'):
        gate.wait_and_exec(wrong,root=gates)

def test_gated_entry_forbids_root_execution(transaction):
    p,store,gates,spec,plan,driver=transaction
    do(transaction)
    manifest=list(gates.glob('manifest-*.json'))[0]
    if os.geteuid()==0:
        with pytest.raises(gate.GateBlocked,match='RUNNER_NOT_ROOT_REQUIRED'):
            gate.wait_and_exec(manifest,root=gates)

def test_root_owned_gate_mode_required(transaction):
    p,store,gates,spec,plan,driver=transaction
    do(transaction)
    gates.chmod(0o777)
    manifest=list(gates.glob('manifest-*.json'))[0]
    with pytest.raises(gate.GateBlocked,match='GATE_DIR_OWNER_MODE'):
        gate.wait_and_exec(manifest,root=gates)
