"""Isolated non-live tests for the candidate S01 pilot launch corridor.

All successful launches are simulated. There is no /etc, /var, /run, Git
mutation, actual ledger append, Worker process, signer, or permissions change.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
import types
from unittest.mock import Mock
import pytest

SOURCE = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_s01_live_pilot_corridor_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_s01_candidate_module_test', SOURCE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
TASK = 'cf10-task85-project-change-impact-and-freshness-v0-1'
ATTEMPT = 'cf10-u180j-a048'
HEAD = 'b' * 40
BINDING = {'receipt_sha256': 'a'*64, 'publication_commit': HEAD,
           'worker_id':mod.WORKER, 'task_prompt_id': TASK, 'attempt_id': ATTEMPT}


def test_inspection_cannot_launch():
    assert mod.inspect()['production_launch_verified_by_inspection'] is False
    assert mod.main(['inspect']) == 0
    assert mod.main(['launch-preflight']) == 2


def test_no_in_process_authority_denies_direct_python(monkeypatch):
    monkeypatch.setattr(mod.os, 'geteuid', lambda: 0)
    with pytest.raises(mod.PilotLaunchBlocked, match='SESSION_REQUIRED'):
        mod.require_live_session(root=mod.PROJECT, task_prompt_id=TASK,
                                 attempt_id=ATTEMPT, worker_id=mod.WORKER, route='launch_cycle')


def test_session_enforces_scope_order_and_expiry(monkeypatch):
    monkeypatch.setattr(mod.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(mod, '_head', lambda root: HEAD)
    monkeypatch.setattr(mod, '_assert_reviewed_live_source', lambda root, head: None)
    s=mod._Session(mod.PROJECT,mod.WORKER,TASK,ATTEMPT,HEAD,datetime.now(timezone.utc)+timedelta(minutes=2))
    tok=mod._SESSION.set(s)
    try:
        with pytest.raises(mod.PilotLaunchBlocked,match='UNEXPECTED_OR_REPEATED'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,
                                     route='launch_authorized_worker_cycle')
        with pytest.raises(mod.PilotLaunchBlocked,match='SCOPE_DRIFT'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id='cf10-wrong',worker_id=mod.WORKER,route='launch_cycle')
        mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
        mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_authorized_worker_cycle')
        assert s.phase=='INNER_ENTERED'
        with pytest.raises(mod.PilotLaunchBlocked,match='UNEXPECTED_OR_REPEATED'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
    finally:
        mod._SESSION.reset(tok)
    s.expires_at=datetime.now(timezone.utc)-timedelta(seconds=1)
    tok=mod._SESSION.set(s)
    try:
        with pytest.raises(mod.PilotLaunchBlocked,match='EXPIRED'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
    finally:
        mod._SESSION.reset(tok)


def test_unprivileged_python_rejected_even_with_injected_context(monkeypatch):
    monkeypatch.setattr(mod.os, 'geteuid', lambda: 1000)
    tok=mod._SESSION.set(mod._Session(mod.PROJECT,mod.WORKER,TASK,ATTEMPT,HEAD,datetime.now(timezone.utc)+timedelta(minutes=2)))
    try:
        with pytest.raises(mod.PilotLaunchBlocked,match='SESSION_REQUIRED'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
    finally:
        mod._SESSION.reset(tok)


def test_canonical_roots_and_confirmation_required(monkeypatch):
    monkeypatch.setattr(mod.os, 'geteuid', lambda: 0)
    with pytest.raises(mod.PilotLaunchBlocked,match='CONFIRMATION_REQUIRED'):
        mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=False)
    with pytest.raises(mod.PilotLaunchBlocked,match='CANONICAL_ROOT'):
        mod.launch_once(root=Path('/noncanonical'),runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)
    monkeypatch.setattr(mod.os,'geteuid',lambda: 1000)
    with pytest.raises(mod.PilotLaunchBlocked,match='ROOT_ONLY'):
        mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)


def run_fixture(monkeypatch, *, injected_error=None, drift=False):
    monkeypatch.setattr(mod.os,'geteuid',lambda:0)
    monkeypatch.setattr(mod,'_git',lambda root,*args: mod.BRANCH if args[:2]==('branch','--show-current') else ('' if args[:3]==('diff','--cached','--name-only') else HEAD+'\tref'))
    monkeypatch.setattr(mod,'_head',lambda root: HEAD)
    monkeypatch.setattr(mod,'_assert_reviewed_live_source',lambda root,head: None)
    verify=Mock(side_effect=lambda *a,**k:(BINDING,datetime.now(timezone.utc)+timedelta(minutes=5)))
    monkeypatch.setattr(mod,'_authenticate',verify)
    monkeypatch.setattr(mod,'_preclaim_cycle_readiness',Mock())
    claim=Mock()
    if injected_error=='claim': claim.side_effect=mod.PilotLaunchBlocked('S01_ONE_SHOT_CLAIM_FAILED_OR_ALREADY_CONSUMED')
    monkeypatch.setattr(mod,'_claim',claim)
    fake=types.ModuleType('scripts.coordination.control_plane.governed_worker_cycle')
    spawn=Mock()
    def inner(**kwargs):
        mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
        if injected_error=='outer': raise RuntimeError('fake preflight error')
        mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_authorized_worker_cycle')
        spawn()
        return {'state':'OBSERVE_WORKER'}
    fake.launch_cycle=inner
    top=types.ModuleType('scripts')
    coordination=types.ModuleType('scripts.coordination')
    plane=types.ModuleType('scripts.coordination.control_plane')
    top.coordination=coordination
    coordination.control_plane=plane
    plane.governed_worker_cycle=fake
    for n,m in [('scripts',top),('scripts.coordination',coordination),
                ('scripts.coordination.control_plane',plane),
                ('scripts.coordination.control_plane.governed_worker_cycle',fake)]:
        monkeypatch.setitem(sys.modules,n,m)
    return claim,spawn,verify


def test_fixture_bounded_claim_then_single_process_launch(monkeypatch):
    claim,spawn,verify=run_fixture(monkeypatch)
    result=mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)
    assert result['state']=='OBSERVE_WORKER'
    assert claim.call_count==1 and spawn.call_count==1 and verify.call_count==2
    assert mod._SESSION.get() is None


def test_claim_failure_never_spawns_and_does_not_leave_session(monkeypatch):
    claim,spawn,_=run_fixture(monkeypatch,injected_error='claim')
    with pytest.raises(mod.PilotLaunchBlocked,match='CLAIM_FAILED'):
        mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)
    assert claim.call_count==1 and spawn.call_count==0
    assert mod._SESSION.get() is None


def test_after_claim_exception_clears_session_and_prevents_automatic_retry(monkeypatch):
    claim,spawn,_=run_fixture(monkeypatch,injected_error='outer')
    with pytest.raises(RuntimeError,match='fake preflight'):
        mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)
    assert claim.call_count==1 and spawn.call_count==0
    assert mod._SESSION.get() is None


def test_head_change_before_claim_fails_without_consuming(monkeypatch):
    claim,spawn,_=run_fixture(monkeypatch)
    monkeypatch.setattr(mod,'_head',lambda root:'c'*40)
    with pytest.raises(mod.PilotLaunchBlocked,match='S01_REMOTE_HEAD_NOT_VERIFIED'):
        mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)
    assert claim.call_count==0 and spawn.call_count==0


def test_missing_approved_make_binding_fails_closed(tmp_path):
    with pytest.raises(mod.PilotLaunchBlocked,match='PUBLISHED_LIVE_SOURCE_UNAVAILABLE'):
        mod._assert_reviewed_live_source(tmp_path,HEAD)


def test_invalid_release_time_rejected():
    assert mod._utc('2026-10-30T12:00:00Z').tzinfo is not None
    for raw in (None,'2026-10-30T12:00:00','not-a-date'):
        with pytest.raises(mod.PilotLaunchBlocked):mod._utc(raw)


def test_cli_missing_confirmation_does_not_start_worker(monkeypatch):
    monkeypatch.setattr(mod.os,'geteuid',lambda:0)
    assert mod.main(['launch','--root',str(mod.PROJECT),'--runtime-root',str(mod.RUNTIME),
                     '--task-prompt-id',TASK,'--attempt-id',ATTEMPT])==2


def test_no_self_sign_or_automatic_unquarantine_in_source():
    text=SOURCE.read_text()
    for fragment in ('Ed25519PrivateKey(', 'signature_base64 =', 'git push', 'git commit',
                     'os.chmod(', 'unlink(', 'rmtree(', 'subprocess.Popen('):
        assert fragment not in text


def test_new_inner_and_outer_guards_detect_head_change(monkeypatch):
    monkeypatch.setattr(mod.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(mod, '_head', lambda root: 'f'*40)
    monkeypatch.setattr(mod, '_assert_reviewed_live_source', lambda root, head: None)
    s=mod._Session(mod.PROJECT,mod.WORKER,TASK,ATTEMPT,HEAD,datetime.now(timezone.utc)+timedelta(minutes=5))
    token=mod._SESSION.set(s)
    try:
        with pytest.raises(mod.PilotLaunchBlocked,match='HEAD_CHANGED_WITHIN_LAUNCH'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
        assert s.phase=='READY'
    finally:
        mod._SESSION.reset(token)


def test_guarded_python_path_refuses_dirty_critical_dependency(monkeypatch):
    monkeypatch.setattr(mod.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(mod, '_head', lambda root: HEAD)
    def unsafe(root,head):
        raise mod.PilotLaunchBlocked('S01_LIVE_SOURCE_WORKTREE_DRIFT')
    monkeypatch.setattr(mod, '_assert_reviewed_live_source', unsafe)
    s=mod._Session(mod.PROJECT,mod.WORKER,TASK,ATTEMPT,HEAD,datetime.now(timezone.utc)+timedelta(minutes=5))
    token=mod._SESSION.set(s)
    try:
        with pytest.raises(mod.PilotLaunchBlocked,match='WORKTREE_DRIFT'):
            mod.require_live_session(root=mod.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id=mod.WORKER,route='launch_cycle')
        assert s.phase=='READY'
    finally:mod._SESSION.reset(token)


def test_post_claim_git_drift_must_not_spawn(monkeypatch):
    claim,spawn,_=run_fixture(monkeypatch)
    calls=[0]
    def moving_head(root):
        calls[0]+=1
        return 'f'*40 if calls[0]>4 else HEAD
    monkeypatch.setattr(mod,'_head',moving_head)
    with pytest.raises(mod.PilotLaunchBlocked):
        mod.launch_once(root=mod.PROJECT,runtime_root=mod.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,confirm=True)
    assert claim.call_count <= 1
    assert spawn.call_count == 0
    assert mod._SESSION.get() is None


def test_live_source_pin_contract_includes_core_dependencies():
    import ast
    tree=ast.parse(SOURCE.read_text('utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_assert_reviewed_live_source')
    rels=next(n.value for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='rels' for t in n.targets))
    assert isinstance(rels,ast.Tuple)
    actual={n.value for n in rels.elts if isinstance(n,ast.Constant)}
    essential={
     'Makefile',
     'scripts/coordination/control_plane/governed_worker_cycle.py',
     'scripts/coordination/control_plane/cf10_s01_live_pilot_corridor_v0_1.py',
     'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py',
     'scripts/coordination/control_plane/cf10_s01_runtime_rebind_v0_2.py',
     'scripts/coordination/control_plane/cf10_s01_root_controlled_single_use_v0_2.py',
     'scripts/coordination/execution_attempt_writer_activation_v0_1.py',
     'scripts/coordination/execution_attempt_writer_lock_v0_1.py',
     'scripts/coordination/execution_attempt_ledger_v0_1.py',
     'scripts/coordination/control_plane/worker_runtime/invocation_adapter.py',
    }
    assert essential <= actual


def test_cli_return_must_not_claim_spawn_or_worker_result_acceptance(monkeypatch,capsys):
    monkeypatch.setattr(mod,'launch_once',lambda **k: {'state':'BLOCKED'})
    assert mod.main(['launch','--task-prompt-id',TASK,'--attempt-id',ATTEMPT,'--confirm-launch'])==0
    payload=__import__('json').loads(capsys.readouterr().out)
    assert payload['worker_spawn_confirmed_here'] is False
    assert payload['worker_result_accepted_here'] is False
    assert payload['status']=='GOVERNED_CYCLE_RETURNED_REQUIRES_EVIDENCE_REVIEW'
