"""r055 fail-closed exact source-bound conditional corridor, no real production Worker."""
import ast
import inspect
from pathlib import Path
import re
import types
import sys
import importlib
import pytest

from scripts.coordination.control_plane import cf10_r055_pilot_launch_corridor_v0_1 as guard
from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
from scripts.coordination.control_plane import cf10_r053_dormant_pilot_bridge_v0_1 as dormant

@pytest.fixture(autouse=True)
def missing_audit_dependency_compat(monkeypatch):
    """In the truncated offline audit snapshot only, stub missing cycle imports.

    The real server regression imports the full module and these tests then
    exercise its actual .status through monkeypatching, not a stand-in runtime.
    """
    name='scripts.coordination.control_plane.governed_worker_cycle'
    try:
        importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name != 'scripts.coordination.continuity':
            raise
        from scripts.coordination import control_plane
        stub=types.ModuleType(name)
        stub.status=lambda **kw: None
        monkeypatch.setitem(sys.modules,name,stub)
        monkeypatch.setattr(control_plane,'governed_worker_cycle',stub,raising=False)
    # The audit snapshot omits historical durable writer/ledger sources too.
    # Production s01 imports real versions; isolated tests patch their methods.
    from scripts import coordination as coordination_pkg
    for short in ('execution_attempt_writer_lock_v0_1','execution_attempt_ledger_v0_1'):
        try:
            importlib.import_module('scripts.coordination.'+short)
        except ModuleNotFoundError as exc:
            if exc.name != 'scripts.coordination.'+short:
                raise
            full='scripts.coordination.'+short
            stub=types.ModuleType(full)
            stub.load_enforced_protocol=lambda **kw:None
            stub.store_root=lambda *args:None
            stub.load_contract=lambda *args:None
            stub.records_for_attempt=lambda *args:[]
            monkeypatch.setitem(sys.modules,full,stub)
            monkeypatch.setattr(coordination_pkg,short,stub,raising=False)

ROOT = Path(__file__).resolve().parents[3]
ATTEMPT = 'cf10-u180j-a995'
HEAD = 'b'*40


def test_requirements_never_report_started_or_authorized():
    r=guard.requirements()
    assert r['launch_allowed'] is False
    assert r['production_worker_launched'] is False
    assert r['root_technical_proofs_issued_by_this_module'] is False
    assert r['root_preclaim_issued_by_this_module'] is False
    assert r['legacy_make_quarantine_unchanged'] is True
    assert guard.main(['--mode','requirements'])==0


def test_non_root_or_other_task_refused_before_source(monkeypatch):
    monkeypatch.setattr(guard.os,'geteuid',lambda:1000)
    with pytest.raises(guard.PilotLaunchBlocked,match='ROOT_OR_EXACT'):
        guard._source(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD)
    monkeypatch.setattr(guard.os,'geteuid',lambda:0)
    with pytest.raises(guard.PilotLaunchBlocked,match='ROOT_OR_EXACT'):
        guard._source(root=guard.PROJECT,runtime=guard.RUNTIME,task='other-task',attempt=ATTEMPT,head=HEAD)


@pytest.mark.parametrize('attempt',[None,'','cf10-u180j-a02','cf10-u180j-a999;true','cf10-u180j-a000/../x','cf10-z999-a999'])
def test_invalid_attempt_refuses(monkeypatch,attempt):
    monkeypatch.setattr(guard.os,'geteuid',lambda:0)
    with pytest.raises(guard.PilotLaunchBlocked,match='ROOT_OR_EXACT'):
        guard._source(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=attempt,head=HEAD)


def test_before_password_checks_source_then_live_guards(monkeypatch):
    from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as r052
    hits=[]
    monkeypatch.setattr(guard,'_source',lambda **kw:hits.append('source'))
    monkeypatch.setattr(r052,'assert_pre_password',lambda **kw:hits.append('r052'))
    guard.assert_before_password(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD)
    assert hits==['source','r052']


def test_before_password_source_error_does_not_call_other_guards(monkeypatch):
    from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as r052
    monkeypatch.setattr(guard,'_source',lambda **kw:(_ for _ in ()).throw(guard.PilotLaunchBlocked('STOP')))
    monkeypatch.setattr(r052,'assert_pre_password',lambda **kw:pytest.fail('must not call'))
    with pytest.raises(guard.PilotLaunchBlocked,match='STOP'):
        guard.assert_before_password(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD)


def test_postclaim_requires_private_inner_session_before_claim(monkeypatch):
    monkeypatch.setattr(guard,'_source',lambda **kw:None)
    token=owner._SESSION.set(None)
    try:
        with pytest.raises(guard.PilotLaunchBlocked,match='OWNER_PAM_INNER_SESSION_REQUIRED'):
            guard.assert_after_owner_claim(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD)
    finally:owner._SESSION.reset(token)


def test_postclaim_invalid_phase_refuses(monkeypatch):
    monkeypatch.setattr(guard,'_source',lambda **kw:None)
    token=owner._SESSION.set(owner._Session(guard.TASK,ATTEMPT,HEAD,phase='OUTER_ENTERED'))
    try:
        with pytest.raises(guard.PilotLaunchBlocked,match='OWNER_PAM_INNER_SESSION_REQUIRED'):
            guard.assert_after_owner_claim(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD)
    finally:owner._SESSION.reset(token)


def _postclaim_mocks(monkeypatch):
    from scripts.coordination.control_plane import cf10_r054_pilot_postworker_gate_v0_1 as post
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as preclaim
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as proof
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    monkeypatch.setattr(guard,'_source',lambda **kw:None)
    monkeypatch.setattr(post,'_consumed_owner_claim',lambda **kw:None)
    monkeypatch.setattr(preclaim,'inspect',lambda **kw:{'preclaim_root_receipt_verified':True,'blockers':[]})
    monkeypatch.setattr(proof,'inspect',lambda **kw:{'status':'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED','checks':{'r047_source_lineage':'EXACT_RAW_BYTES_BOUND'},'blockers':[],'launch_allowed':False})
    monkeypatch.setattr(owner,'_cycle_preclaim',lambda *a,**kw:None)
    monkeypatch.setattr(writer,'load_enforced_protocol',lambda **kw:object())
    monkeypatch.setattr(cycle,'status',lambda **kw:{'state':'READY_FOR_WORKER_LAUNCH','derived_non_authoritative':True,'contradictions':[]})
    monkeypatch.setattr(ledger,'store_root',lambda *a,**kw:'/test/fixture')
    monkeypatch.setattr(ledger,'load_contract',lambda *a,**kw:{})
    monkeypatch.setattr(ledger,'records_for_attempt',lambda *a,**kw:[])
    monkeypatch.setattr(admission,'_systemd_quiescent',lambda:(True,'QUIESCENT'))
    return post,preclaim,proof,admission,cycle,writer,ledger


def test_postclaim_exact_facts_verified_with_injected_mock_canonical_observers(monkeypatch):
    _postclaim_mocks(monkeypatch)
    token=owner._SESSION.set(owner._Session(guard.TASK,ATTEMPT,HEAD,phase='INNER_ENTERED'))
    try:
        assert guard.assert_after_owner_claim(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD) is None
    finally:owner._SESSION.reset(token)


@pytest.mark.parametrize('untrusted', ['preclaim','release','ledger','systemd','writer','cycle'])
def test_postclaim_negative_source_consistency_blocks(monkeypatch,untrusted):
    post,preclaim,proof,admission,cycle,writer,ledger=_postclaim_mocks(monkeypatch)
    if untrusted=='preclaim':monkeypatch.setattr(preclaim,'inspect',lambda **kw:{'preclaim_root_receipt_verified':False,'blockers':['BAD']})
    elif untrusted=='release':monkeypatch.setattr(proof,'inspect',lambda **kw:{'status':'BLOCKED','checks':{},'blockers':['BAD'],'launch_allowed':False})
    elif untrusted=='ledger':monkeypatch.setattr(ledger,'records_for_attempt',lambda *a,**kw:[{'state':'STARTED'}])
    elif untrusted=='systemd':monkeypatch.setattr(admission,'_systemd_quiescent',lambda:(False,'ACTIVE'))
    elif untrusted=='writer':monkeypatch.setattr(writer,'load_enforced_protocol',lambda **kw:None)
    else:monkeypatch.setattr(cycle,'status',lambda **kw:{'state':'BLOCKED','derived_non_authoritative':True,'contradictions':[]})
    token=owner._SESSION.set(owner._Session(guard.TASK,ATTEMPT,HEAD,phase='INNER_ENTERED'))
    try:
        with pytest.raises(guard.PilotLaunchBlocked):
            guard.assert_after_owner_claim(root=guard.PROJECT,runtime=guard.RUNTIME,task=guard.TASK,attempt=ATTEMPT,head=HEAD)
    finally:owner._SESSION.reset(token)


def test_old_cutover_without_owner_context_remains_blocked(monkeypatch):
    assert backend.LIVE_CUTOVER_ENABLED is False
    token=owner._SESSION.set(None)
    try:
        with pytest.raises(route.CanonicalCutoverBlocked,match='LIVE_SYSTEMD_ROUTE_NOT_RELEASED'):
            route.assert_cutover_ready()
    finally:owner._SESSION.reset(token)


def test_postclaim_route_called_only_when_inner_session(monkeypatch):
    token=owner._SESSION.set(owner._Session(guard.TASK,ATTEMPT,HEAD,phase='INNER_ENTERED'))
    calls=[]
    monkeypatch.setattr(guard,'assert_after_owner_claim',lambda **kw:calls.append(kw))
    try:
        route.assert_cutover_ready()
    finally:owner._SESSION.reset(token)
    assert len(calls)==1 and calls[0]['task']==guard.TASK and calls[0]['attempt']==ATTEMPT


def test_backend_fails_before_core_on_dormant_rejection(monkeypatch):
    monkeypatch.setattr(guard,'assert_after_owner_claim',lambda **kw:(_ for _ in ()).throw(guard.PilotLaunchBlocked('NO_PROOFS')))
    monkeypatch.setattr(dormant,'refuse_backend_launch',lambda **kw:(_ for _ in ()).throw(dormant.PilotDormantBlocked('NO')))
    monkeypatch.setattr(backend,'_core',lambda **kw:pytest.fail('CORE MUST NOT EXECUTE'))
    spec=types.SimpleNamespace(task_prompt_id=guard.TASK,attempt_id=ATTEMPT,source_head=HEAD)
    with pytest.raises(backend.SystemdLaunchBlocked,match='PRODUCTION_CUTOVER_NOT_AUTHORIZED'):
        backend.launch_after_owner_claim(spec=spec,plan={},started_callback=lambda _:None)


def test_backend_even_mock_positive_cannot_spawn_without_owner_session(monkeypatch):
    monkeypatch.setattr(guard,'assert_after_owner_claim',lambda **kw:None)
    monkeypatch.setattr(backend,'_core',lambda **kw:pytest.fail('CORE MUST NOT EXECUTE'))
    spec=types.SimpleNamespace(task_prompt_id=guard.TASK,attempt_id=ATTEMPT,source_head=HEAD)
    token=owner._SESSION.set(None)
    try:
        with pytest.raises(backend.SystemdLaunchBlocked,match='OWNER_PAM_CONTEXT_REQUIRED'):
            backend.launch_after_owner_claim(spec=spec,plan={},started_callback=lambda _:None)
    finally:owner._SESSION.reset(token)


def test_make_legacy_quarantine_and_r055_scope():
    make=(ROOT/'Makefile').read_text()
    assert ('cf10-s01-runtime-launch-preflight:\n'
            '\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2') in make
    assert 'cf10-s01-pilot-owner-run:' in make
    assert guard.TASK == 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
    assert 'cf10_r052_owner_launch_guard_v0_1 --mode guarded-preflight' in make
    assert 'cf10_owner_operator_console_v0_1 run' in make
    for t in ('governed-worker-cycle-launch','governed-worker-cycle-advance','governed-worker-cycle-reconcile-result-return'):
        assert f'{t}: cf10-s01-runtime-launch-preflight' in make


def test_backend_static_global_live_flag_sealed():
    assert backend.LIVE_CUTOVER_ENABLED is False
    src=inspect.getsource(backend.launch_after_owner_claim)
    assert src.index('pilot.assert_after_owner_claim') < src.index('_core(')
    assert 'dormant.refuse_backend_launch' in src
    assert 'subprocess.Popen' not in src


def test_release_does_not_get_created_or_accepted_in_this_module():
    src=inspect.getsource(guard)
    assert 'subprocess.Popen' not in src
    assert 'launch_after_owner_claim(' not in src
    assert 'os.O_EXCL' not in src
    assert '_core(' not in src
    assert 'issue_proof' not in src


def test_make_selector_not_interpolated_into_shell_code():
    import subprocess
    make=(ROOT/'Makefile').read_text()
    block=make.split('# CF10_R055_PILOT_OWNER_ENTRY_START',1)[1]
    assert '"$(GOVERNED_WORKER_TASK)"' not in block
    assert '"$(GOVERNED_WORKER_ATTEMPT)"' not in block
    assert '"$$CF10_TASK"' in block and '"$$CF10_ATTEMPT"' in block
    # Render the Make recipe but do not execute even the guarded preflight.
    cp=subprocess.run(['make','-n','-s','cf10-s01-pilot-owner-run',
                       'GOVERNED_WORKER_TASK=cf10-malformed;$(:> /tmp/never-run)',
                       'GOVERNED_WORKER_ATTEMPT=cf10-u180j-a999'],
                      cwd=ROOT,capture_output=True,text=True,timeout=15,check=False)
    assert cp.returncode==0
    assert '"$CF10_TASK"' in cp.stdout and '"$CF10_ATTEMPT"' in cp.stdout
    assert 'cf10-malformed' not in cp.stdout
