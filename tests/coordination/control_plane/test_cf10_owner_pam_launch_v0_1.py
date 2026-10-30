"""Owner CLI policy tests use temp sources and mocked canonical boundaries only."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import Mock
import json
import os
import re
import pytest
from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
from scripts.coordination.control_plane import governed_worker_cycle as cycle
from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once

TASK='cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATTEMPT='cf10-u180j-a049'
HEAD='1'*40


def test_no_global_session():
    assert owner.active() is False
    with pytest.raises(owner.OwnerLaunchBlocked,match='SESSION_REQUIRED'):
        owner.require_owner_session(root=owner.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,
                                    worker_id=owner.WORKER,route='launch_cycle')


def test_scope_and_route_recheck(monkeypatch):
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_: HEAD)
    monkeypatch.setattr(owner.os,'geteuid',lambda: 0)
    s=owner._Session(TASK,ATTEMPT,HEAD)
    tok=owner._SESSION.set(s)
    try:
        with pytest.raises(owner.OwnerLaunchBlocked,match='SCOPE_MISMATCH'):
            owner.require_owner_session(root=owner.PROJECT,task_prompt_id='other',attempt_id=ATTEMPT,
                                        worker_id=owner.WORKER,route='launch_cycle')
        owner.require_owner_session(root=owner.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,
                                    worker_id=owner.WORKER,route='launch_cycle')
        with pytest.raises(owner.OwnerLaunchBlocked,match='UNEXPECTED'):
            owner.require_owner_session(root=owner.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,
                                        worker_id=owner.WORKER,route='launch_cycle')
        owner.require_owner_session(root=owner.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,
                                    worker_id=owner.WORKER,route='launch_authorized_worker_cycle')
        assert s.phase=='INNER_ENTERED'
    finally: owner._SESSION.reset(tok)
    assert not owner.active()


def test_root_required_even_with_session(monkeypatch):
    monkeypatch.setattr(owner.os,'geteuid',lambda: 1000)
    tok=owner._SESSION.set(owner._Session(TASK,ATTEMPT,HEAD))
    try:
        with pytest.raises(owner.OwnerLaunchBlocked,match='SESSION_REQUIRED'):
            owner.require_owner_session(root=owner.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,
                                        worker_id=owner.WORKER,route='launch_cycle')
    finally: owner._SESSION.reset(tok)


def test_guard_direct_no_session_always_denied():
    with pytest.raises(cycle.GovernedWorkerCycleError,match='QUARANTINED'):
        cycle.require_bounded_s01_launch_authority(root=owner.PROJECT,task_prompt_id=TASK,
            attempt_id=ATTEMPT,worker_id=owner.WORKER,route='launch_cycle')


def test_guard_owner_wrong_scope_denied_without_falling_to_old(monkeypatch):
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_: HEAD)
    monkeypatch.setattr(owner.os,'geteuid',lambda: 0)
    tok=owner._SESSION.set(owner._Session(TASK,ATTEMPT,HEAD))
    try:
        with pytest.raises(cycle.GovernedWorkerCycleError,match='OWNER_LAUNCH_SCOPE_REFUSED'):
            cycle.require_bounded_s01_launch_authority(root=owner.PROJECT,task_prompt_id='another',
                attempt_id=ATTEMPT,worker_id=owner.WORKER,route='launch_cycle')
    finally: owner._SESSION.reset(tok)


def test_guard_owner_successful_scoped_route(monkeypatch):
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_: HEAD)
    monkeypatch.setattr(owner.os,'geteuid',lambda: 0)
    tok=owner._SESSION.set(owner._Session(TASK,ATTEMPT,HEAD))
    try:
        cycle.require_bounded_s01_launch_authority(root=owner.PROJECT,task_prompt_id=TASK,
            attempt_id=ATTEMPT,worker_id=owner.WORKER,route='launch_cycle')
        cycle.require_bounded_s01_launch_authority(root=owner.PROJECT,task_prompt_id=TASK,
            attempt_id=ATTEMPT,worker_id=owner.WORKER,route='launch_authorized_worker_cycle')
    finally: owner._SESSION.reset(tok)


def test_preclaim_rejects_unready_without_claim(monkeypatch):
    monkeypatch.setattr(cycle,'status',lambda **_: {'state':'OBSERVE_WORKER','derived_non_authoritative':True})
    with pytest.raises(owner.OwnerLaunchBlocked,match='NOT_READY'):
        owner._cycle_preclaim(owner.PROJECT,owner.RUNTIME,TASK,ATTEMPT)


def test_file_claim_is_one_attempt_only(tmp_path,monkeypatch):
    tmp_path.chmod(0o700)
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:os.open(tmp_path,os.O_RDONLY))
    first=owner._owner_claim(tmp_path,TASK,ATTEMPT,HEAD)
    assert re.fullmatch(r'owner_attempt_[0-9a-f]{64}\.json',first)
    doc=json.loads((tmp_path/first).read_text())
    assert doc['status']=='CONSUMED_BEFORE_SPAWN_NO_RETRY'
    assert doc['attempt_id']==ATTEMPT and doc['source_head']==HEAD
    assert (tmp_path/first).stat().st_mode&0o777 == 0o600
    with pytest.raises(owner.OwnerLaunchBlocked,match='ALREADY_CONSUMED'):
        owner._owner_claim(tmp_path,TASK,ATTEMPT,HEAD)
    assert owner._owner_claim(tmp_path,TASK,'cf10-u180j-a050',HEAD)!=first


def test_no_claim_without_password(monkeypatch):
    called=[]
    monkeypatch.setattr(owner.os,'geteuid',lambda:0)
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_:HEAD)
    monkeypatch.setattr(owner,'_cycle_preclaim',lambda *_:None)
    monkeypatch.setattr(console,'authenticate_operator',lambda:(_ for _ in ()).throw(console.ConsoleBlocked('NO_PASSWORD')))
    monkeypatch.setattr(owner,'_owner_claim',lambda *_: called.append('claim'))
    with pytest.raises(console.ConsoleBlocked):
        owner.launch_once(root=owner.PROJECT,runtime_root=owner.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT)
    assert called==[]


def test_wrong_root_refused_before_auth(monkeypatch):
    auth=Mock();monkeypatch.setattr(console,'authenticate_operator',auth)
    with pytest.raises(owner.OwnerLaunchBlocked,match='CANONICAL'):
        owner.launch_once(root=Path('/noncanonical'),runtime_root=owner.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT)
    auth.assert_not_called()


def test_source_guard_verifies_published_blobs(tmp_path,monkeypatch):
    monkeypatch.setattr(console,'source_guard',lambda _: HEAD)
    with pytest.raises(owner.OwnerLaunchBlocked,match='UNAVAILABLE'):
        owner._assert_live_source(tmp_path)


def test_session_scope_head_changed(monkeypatch):
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_:'0'*40)
    monkeypatch.setattr(owner.os,'geteuid',lambda:0)
    tok=owner._SESSION.set(owner._Session(TASK,ATTEMPT,HEAD))
    try:
        with pytest.raises(owner.OwnerLaunchBlocked,match='SOURCE_CHANGED'):
            owner.require_owner_session(root=owner.PROJECT,task_prompt_id=TASK,attempt_id=ATTEMPT,
                worker_id=owner.WORKER,route='launch_cycle')
    finally: owner._SESSION.reset(tok)


def test_console_never_auto_accepts_worker_result():
    assert 'AWAITING_OPERATOR_REVIEW' in console.STOP
    assert 'PROMOTE_CANDIDATE' in console.STOP
    assert 'AWAITING_PUBLICATION_APPROVAL' in console.STOP
    assert 'READY_FOR_WORKER_LAUNCH' not in console.STOP


def test_no_root_pam_shortcut_in_owner_module():
    import inspect
    src=inspect.getsource(owner.launch_once)
    assert 'console.authenticate_operator()' in src
    assert '_owner_claim(' in src and 'cycle.launch_cycle(' in src
    assert src.index('console.authenticate_operator()') < src.index('_owner_claim(') < src.index('cycle.launch_cycle(')


def _patch_successful_owner_launch(monkeypatch,tmp_path,head=HEAD):
    monkeypatch.setattr(owner.os,'geteuid',lambda:0)
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_:head)
    monkeypatch.setattr(owner,'_cycle_preclaim',lambda *_:None)
    monkeypatch.setattr(console,'authenticate_operator',Mock())
    tmp_path.chmod(0o700)
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:os.open(tmp_path,os.O_RDONLY))


def test_password_once_two_guarded_routes_and_per_attempt_claim(monkeypatch,tmp_path):
    _patch_successful_owner_launch(monkeypatch,tmp_path)
    calls=[]
    def actual(**kwargs):
        calls.append(kwargs)
        cycle.require_bounded_s01_launch_authority(root=kwargs['root'],
            task_prompt_id=kwargs['task_prompt_id'],attempt_id=kwargs['attempt_id'],
            worker_id=kwargs['worker_id'],route='launch_cycle')
        cycle.require_bounded_s01_launch_authority(root=kwargs['root'],
            task_prompt_id=kwargs['task_prompt_id'],attempt_id=kwargs['attempt_id'],
            worker_id=kwargs['worker_id'],route='launch_authorized_worker_cycle')
        return {'state':'OBSERVE_WORKER'}
    monkeypatch.setattr(cycle,'launch_cycle',actual)
    result=owner.launch_once(root=owner.PROJECT,runtime_root=owner.RUNTIME,
                             task_prompt_id=TASK,attempt_id=ATTEMPT)
    assert result['state']=='LAUNCH_RETURNED_REQUIRES_WORKER_RESULT_REVIEW'
    assert result['worker_spawn_claimed_by_console'] is False
    assert len(calls)==1 and not owner.active()
    assert console.authenticate_operator.call_count==1
    with pytest.raises(owner.OwnerLaunchBlocked,match='ALREADY_CONSUMED'):
        owner.launch_once(root=owner.PROJECT,runtime_root=owner.RUNTIME,
                          task_prompt_id=TASK,attempt_id=ATTEMPT)
    assert len(calls)==1
    assert console.authenticate_operator.call_count==2


def test_error_after_claim_never_auto_retries(monkeypatch,tmp_path):
    _patch_successful_owner_launch(monkeypatch,tmp_path)
    launches=Mock(side_effect=RuntimeError('injected postclaim crash'))
    monkeypatch.setattr(cycle,'launch_cycle',launches)
    with pytest.raises(RuntimeError,match='postclaim crash'):
        owner.launch_once(root=owner.PROJECT,runtime_root=owner.RUNTIME,
                          task_prompt_id=TASK,attempt_id=ATTEMPT)
    assert launches.call_count==1 and not owner.active()
    with pytest.raises(owner.OwnerLaunchBlocked,match='ALREADY_CONSUMED'):
        owner.launch_once(root=owner.PROJECT,runtime_root=owner.RUNTIME,
                          task_prompt_id=TASK,attempt_id=ATTEMPT)
    assert launches.call_count==1


def test_source_drift_after_password_before_claim(monkeypatch,tmp_path):
    _patch_successful_owner_launch(monkeypatch,tmp_path)
    heads=iter([HEAD,'2'*40])
    monkeypatch.setattr(owner,'_assert_live_source',lambda *_: next(heads))
    launch=Mock();monkeypatch.setattr(cycle,'launch_cycle',launch)
    with pytest.raises(owner.OwnerLaunchBlocked,match='SOURCE_CHANGED_AFTER_PASSWORD'):
        owner.launch_once(root=owner.PROJECT,runtime_root=owner.RUNTIME,
                          task_prompt_id=TASK,attempt_id=ATTEMPT)
    launch.assert_not_called()
    assert not list(tmp_path.glob('owner_attempt_*.json'))


def test_canonical_pam_gate_sees_current_source_and_required_lock(monkeypatch,tmp_path):
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    monkeypatch.setattr(cycle,'status',lambda **_: {'state':'READY_FOR_WORKER_LAUNCH',
                          'derived_non_authoritative':True,'contradictions':[]})
    monkeypatch.setattr(writer,'load_enforced_protocol',lambda **_: {'sha256':'abcd'})
    monkeypatch.setattr(cycle,'_load_yaml',lambda *_: {'git_head':HEAD})
    capture=Mock();monkeypatch.setattr(cycle,'_assert_frozen_source_state_current',capture)
    runtime=tmp_path/'runtime'
    attempt_root=runtime/'forprint_system_blueprint'/'worker-01'/ATTEMPT/'input'
    attempt_root.mkdir(parents=True)
    (attempt_root/'governed_worker_cycle_source_state_v0_1.yaml').write_text('git_head: test\n')
    owner._cycle_preclaim(tmp_path,runtime,TASK,ATTEMPT)
    capture.assert_called_once()


def test_missing_enforced_lock_denied_preclaim(monkeypatch,tmp_path):
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    monkeypatch.setattr(cycle,'status',lambda **_: {'state':'READY_FOR_WORKER_LAUNCH',
                          'derived_non_authoritative':True,'contradictions':[]})
    monkeypatch.setattr(writer,'load_enforced_protocol',lambda **_:None)
    with pytest.raises(owner.OwnerLaunchBlocked,match='NOT_ENFORCED'):
        owner._cycle_preclaim(tmp_path,tmp_path,TASK,ATTEMPT)


def test_owner_policy_pin_and_review_fields():
    import yaml
    root=Path(__file__).resolve().parents[3]
    p=root/'coordination/continuity/cf10_sole_owner_pam_launch_policy_v0_1.yaml'
    doc=yaml.safe_load(p.read_text())
    assert doc['status']=='OWNER_APPROVED_EXPLICIT_TERMINAL_PASSWORD'
    assert doc['human_roles']['independent_human_reviewers_claimed']==0
    assert doc['control']['worker_result_not_automatically_accepted'] is True
    assert doc['control']['per_attempt_claim_not_global_pilot_slot'] is True
