"""r037 strict pre-finalizer seam: read-only candidate, never acceptance."""
from pathlib import Path
import ast
import pytest
from scripts.coordination.control_plane import cf10_r037_finalizer_boundary_v0_1 as gate
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery

ATT='cf10-r037fixture-a037'
HEAD='a'*40
HAND='b'*64
BASE='c'*64

def args(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir()
    runtime=tmp_path/'runtime';runtime.mkdir()
    monkeypatch.setattr(gate,'ROOT',root)
    monkeypatch.setattr(gate,'RUNTIME',runtime)
    attempt=runtime/'forprint_system_blueprint'/'worker-01'/ATT
    attempt.mkdir(parents=True)
    return dict(canonical=root,attempt=attempt,attempt_id=ATT,
                source_state={'git_head':HEAD},
                baseline={'baseline_fingerprint_sha256':BASE},
                origin_manifest={'handoff_manifest_sha256':HAND},
                governed_context={'handoff_manifest_sha256':HAND},
                ledger_rows=[{'attempt_id':ATT,'attempt_stage':'STARTED','result_state':'PENDING'}])

def setup(monkeypatch):
    monkeypatch.setattr(gate.recovery,'read_root_claim',lambda **k:({'trusted':True},True))
    monkeypatch.setattr(gate.trusted,'collect',lambda ident:{
        'kernel':{'cgroup_state':'REMOVED_NOT_PROOF'},
        'systemctl':{'service':'verified'},
    })
    monkeypatch.setattr(gate.crosscheck,'inspect',lambda **k:{
        'status':gate.EXPECTED,'existing_verifier_checked':True,
        'worker_result_accepted':False,'automatic_retry':False,
        'release_allowed':False,'pre_record_sha256':'a'*64,
        'terminal_record_sha256':'b'*64})

def test_exact_candidate_only(tmp_path,monkeypatch):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    result=gate.review(**kw)
    assert result['status']==gate.EXPECTED
    assert result['worker_result_accepted'] is False
    assert result['automatic_retry'] is False
    assert result['release_allowed'] is False
    assert result['read_only'] is True

def test_root_required(tmp_path,monkeypatch):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    monkeypatch.setattr(gate.os,'geteuid',lambda:1000)
    with pytest.raises(gate.FinalizerBoundaryBlocked,match='ROOT_REQUIRED'):
        gate.review(**kw)

@pytest.mark.parametrize('change,expected',[
    ({'attempt_id':'cf10-other-a038'},'ATTEMPT_ROOT'),
    ({'source_state':{'git_head':'bad'}},'IDENTITY'),
    ({'governed_context':{'handoff_manifest_sha256':'f'*64}},'HANDOFF_CONTEXT_DRIFT'),
    ({'ledger_rows':[]},'STARTED_PENDING_REQUIRED'),
    ({'ledger_rows':[{'attempt_id':ATT,'attempt_stage':'FINISHED','result_state':'SUCCEEDED'}]},'STARTED_PENDING_REQUIRED')
])
def test_identity_scope_drift(tmp_path,monkeypatch,change,expected):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch);kw.update(change)
    with pytest.raises(gate.FinalizerBoundaryBlocked,match=expected):gate.review(**kw)

@pytest.mark.parametrize('state', ['POPULATED','INACTIVE_BUT_POPULATED'])
def test_live_kernel_always_denied(tmp_path,monkeypatch,state):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    monkeypatch.setattr(gate.trusted,'collect',lambda i:{
        'kernel':{'cgroup_state':state},'systemctl':{}})
    with pytest.raises(gate.FinalizerBoundaryBlocked,match='LIVE_CGROUP_NOT_TERMINAL'):
        gate.review(**kw)

def test_absent_claim_blocked(tmp_path,monkeypatch):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    monkeypatch.setattr(gate.recovery,'read_root_claim',lambda **k:(None,True))
    with pytest.raises(gate.FinalizerBoundaryBlocked,match='CLAIM_NOT_VERIFIABLE'):
        gate.review(**kw)

def test_untrusted_result_blocked(tmp_path,monkeypatch):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    monkeypatch.setattr(gate.crosscheck,'inspect',lambda **k:{
        'status':'BLOCKED_TERMINAL_NOT_DURABLE', 'existing_verifier_checked':False})
    with pytest.raises(gate.FinalizerBoundaryBlocked,match='CANDIDATE_NOT_VERIFIED'):
        gate.review(**kw)

def test_missing_terminal_hash_blocked(tmp_path,monkeypatch):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    monkeypatch.setattr(gate.crosscheck,'inspect',lambda **k:{
        'status':gate.EXPECTED, 'existing_verifier_checked':True,
        'worker_result_accepted':False,'automatic_retry':False,
        'release_allowed':False,'pre_record_sha256':'a'*64})
    with pytest.raises(gate.FinalizerBoundaryBlocked,match='CANDIDATE_NOT_VERIFIED'):
        gate.review(**kw)

def test_readback_exception_fail_closed(tmp_path,monkeypatch):
    kw=args(tmp_path,monkeypatch);setup(monkeypatch)
    def crash(_):raise RuntimeError('readback lost')
    monkeypatch.setattr(gate.trusted,'collect',crash)
    with pytest.raises(gate.FinalizerBoundaryBlocked,match='TRUSTED_READBACK_RuntimeError'):
        gate.review(**kw)

def test_canonical_finalizer_guard_precedes_terminal_append_and_replay_excluded():
    text=(Path(gate.__file__).parent/'governed_worker_cycle.py').read_text('utf-8')
    tree=ast.parse(text)
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='advance_cycle')
    assert text.count('R037_INDEPENDENT_RESULT_GUARD:')==1
    assert text.index('R037_INDEPENDENT_RESULT_GUARD:')<text.index('finalize_cf10_workspace_result_artifact(')
    assert 'if not terminal_already_present:\n            from scripts.coordination.control_plane import cf10_r037_finalizer_boundary_v0_1' in text
    assert 'if verification.get("valid") is not True:' in text
    assert 'if terminal_already_present:' in text
    assert node is not None

def test_canonical_launch_remains_sealed():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launch
    assert launch.LIVE_CUTOVER_ENABLED is False

def test_retained_systemd_unit_retired_only_with_exact_identity(monkeypatch):
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    class CP:
        returncode=0
    calls=[]
    def runner(args,**kwargs):
        calls.append(args)
        return CP()
    monkeypatch.setattr(route.subprocess,'run',runner)
    monkeypatch.setattr(route.backend,'_show',lambda unit,call:{
        'Id':unit,'LoadState':'not-found','ActiveState':'inactive','MainPID':'0'})
    unit='forprint-cf10-worker-'+'a'*24+'.service'
    route._retire_after_durable_terminal(unit)
    assert calls==[['/usr/bin/systemctl','stop','--',unit]]
    for invalid in ('ssh.service','forprint-cf10-worker-fake.service',unit+'extra'):
        with pytest.raises(route.CanonicalCutoverBlocked,match='RETIRE_UNIT_IDENTITY'):
            route._retire_after_durable_terminal(invalid)
    assert len(calls)==1

@pytest.mark.parametrize('observation',[
    {'LoadState':'loaded','ActiveState':'active','MainPID':'0'},
    {'LoadState':'not-found','ActiveState':'active','MainPID':'0'},
    {'LoadState':'not-found','ActiveState':'inactive','MainPID':'1234'},
])
def test_retired_systemd_must_be_inactive_unloaded(monkeypatch,observation):
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    class CP:returncode=0
    monkeypatch.setattr(route.subprocess,'run',lambda *a,**k:CP())
    unit='forprint-cf10-worker-'+'a'*24+'.service'
    monkeypatch.setattr(route.backend,'_show',lambda u,call:{'Id':u,**observation})
    with pytest.raises(route.CanonicalCutoverBlocked,match='RETAINED_UNIT_NOT_STOPPED'):
        route._retire_after_durable_terminal(unit)

def test_retire_command_failure_blocks(monkeypatch):
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    class CP:returncode=1
    monkeypatch.setattr(route.subprocess,'run',lambda *a,**k:CP())
    with pytest.raises(route.CanonicalCutoverBlocked,match='RETAINED_UNIT_STOP_FAILED'):
        route._retire_after_durable_terminal('forprint-cf10-worker-'+'a'*24+'.service')

def test_durable_terminal_record_before_service_retirement():
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
    text=Path(route.__file__).read_text('utf-8')
    assert 'durable.record_terminal(spec=spec,unit=unit,outcome=outcome)\n        # Only after durable success' in text
    assert text.index('durable.record_terminal(spec=spec,unit=unit,outcome=outcome)')<text.index('_retire_after_durable_terminal(unit)',text.index('durable.record_terminal(spec=spec,unit=unit,outcome=outcome)'))
