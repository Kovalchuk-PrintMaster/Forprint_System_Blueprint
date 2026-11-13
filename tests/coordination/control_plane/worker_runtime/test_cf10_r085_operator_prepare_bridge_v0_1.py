"""R085 bridge and canonical preprovision guard. All execution mocked."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace
import pytest

from scripts.coordination.control_plane.worker_runtime import cf10_r085_operator_prepare_bridge_v0_1 as m
from scripts.coordination.control_plane.worker_runtime import cf10_r084_operator_assignment_plan_v0_1 as assignment
from scripts.coordination.control_plane.worker_runtime import cf10_r082_frozen_assignment_v0_1 as frozen
from scripts.coordination.control_plane import governed_worker_cycle as cycle

TASK = m.TASK
ATTEMPT = 'cf10-u180j-a995'  # isolated test fixture; never live runtime
PROVIDER = frozen.CURRENT_PILOT_PROVIDER
MODEL = frozen.CURRENT_PILOT_MODEL
HEAD = 'a'*40
FP = 'b'*64
BINDING = {'task_prompt_id': TASK, 'work_front_id':'wf-cf10-validation-check-pipeline-profile-and-optimization-v0-1'}


def preview(**kwargs):
    p = dict(task_id=TASK, work_front_id=BINDING['work_front_id'], attempt_id=ATTEMPT,
        worker_id='worker-01', provider_id=PROVIDER, model_id=MODEL,
        source_head=HEAD, source_state_fingerprint_sha256=FP,
        preview_sha256='f'*64, catalog_candidate={'verified':'fixture'},
        candidate_only=True, eligible_for_live_dispatch=False,
        claim_consumed=False, worker_launched=False)
    p.update(kwargs)
    return p


@pytest.fixture
def root_runtime(monkeypatch,tmp_path):
    root=tmp_path/'canonical'; runtime=tmp_path/'runtime'
    root.mkdir();runtime.mkdir()
    monkeypatch.setattr(m,'ROOT',root)
    monkeypatch.setattr(m,'RUNTIME',runtime)
    monkeypatch.setattr(m.os,'geteuid',lambda:0)
    monkeypatch.setattr(m.os,'isatty',lambda _:True)
    return root,runtime


def invoke(root,runtime,**kwargs):
    args=dict(root=root,runtime_root=runtime,task_id=TASK,attempt_id=ATTEMPT,
        worker_id='worker-01',provider_id=PROVIDER,model_id=MODEL,confirm=m.CONFIRM)
    args.update(kwargs)
    return m.prepare_selected(**args)


def test_inspect_is_non_authorizing():
    facts=m.inspect()
    assert facts['worker_launched'] is False
    assert facts['claim_consumed'] is False
    assert facts['automatic_fallback'] is False
    assert facts['other_provider_prepare_enabled'] is False


def test_missing_confirmation_does_not_plan_or_prepare(root_runtime,monkeypatch):
    root,runtime=root_runtime
    planned=Mock(side_effect=AssertionError('must not plan'))
    monkeypatch.setattr(assignment,'live_preview',planned)
    with pytest.raises(m.OperatorPrepareBlocked,match='CONFIRMATION_REQUIRED'):
        invoke(root,runtime,confirm='')
    planned.assert_not_called()


def test_codex_or_other_model_denied_before_plan(root_runtime,monkeypatch):
    root,runtime=root_runtime
    planned=Mock(side_effect=AssertionError('not called'))
    monkeypatch.setattr(assignment,'live_preview',planned)
    for kw in (dict(provider_id='openai_codex_cli'),dict(model_id='codex-model')):
        with pytest.raises(m.OperatorPrepareBlocked,match='SECOND_PROVIDER_PREPARE_NOT_AUTHORIZED'):
            invoke(root,runtime,**kw)
    planned.assert_not_called()


def test_wrong_task_denied_before_plan(root_runtime,monkeypatch):
    root,runtime=root_runtime
    planned=Mock(side_effect=AssertionError('not called'))
    monkeypatch.setattr(assignment,'live_preview',planned)
    with pytest.raises(m.OperatorPrepareBlocked,match='EXACT_TRAINING_TASK'):
        invoke(root,runtime,task_id='other-task')
    planned.assert_not_called()


def test_non_root_denied_before_plan(root_runtime,monkeypatch):
    root,runtime=root_runtime
    monkeypatch.setattr(m.os,'geteuid',lambda:1000)
    planned=Mock(side_effect=AssertionError('not called'))
    monkeypatch.setattr(assignment,'live_preview',planned)
    with pytest.raises(m.OperatorPrepareBlocked,match='INTERACTIVE_ROOT_REQUIRED'):
        invoke(root,runtime)
    planned.assert_not_called()


def test_wrong_root_denied_before_plan(root_runtime,monkeypatch,tmp_path):
    root,runtime=root_runtime
    with pytest.raises(m.OperatorPrepareBlocked,match='CANONICAL_ROOTS_REQUIRED'):
        invoke(tmp_path,runtime)


def test_selected_copilot_plan_passes_to_canonical_prepare(root_runtime,monkeypatch):
    root,runtime=root_runtime
    p=preview()
    planned=Mock(return_value=p)
    prepared=Mock(return_value=dict(state='AWAITING_ASSISTANT_ACK',
        operator_preview_sha256=p['preview_sha256'],operator_provider_id=PROVIDER,
        worker_launch_performed=False))
    monkeypatch.setattr(assignment,'live_preview',planned)
    monkeypatch.setattr(cycle,'prepare_cycle',prepared)
    r=invoke(root,runtime)
    prepared.assert_called_once_with(root=root,runtime_root=runtime,
        task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id='worker-01',
        operator_provider_preview=p)
    assert r['state']=='AWAITING_ASSISTANT_ACK'
    assert r['authorization_granted'] is False
    assert r['claim_consumed'] is False


def test_untrusted_preview_cannot_trigger_prepare(root_runtime,monkeypatch):
    root,runtime=root_runtime
    planned=Mock(return_value=preview(candidate_only=False))
    prepared=Mock(side_effect=AssertionError('must not prepare'))
    monkeypatch.setattr(assignment,'live_preview',planned)
    monkeypatch.setattr(cycle,'prepare_cycle',prepared)
    with pytest.raises(m.OperatorPrepareBlocked,match='NON_CANDIDATE_PROVIDER_PLAN'):
        invoke(root,runtime)
    prepared.assert_not_called()


def test_canonical_result_drift_requires_review_no_retry(root_runtime,monkeypatch):
    root,runtime=root_runtime
    p=preview()
    monkeypatch.setattr(assignment,'live_preview',lambda **k:p)
    monkeypatch.setattr(cycle,'prepare_cycle',lambda **k:{'state':'AWAITING_ASSISTANT_ACK',
        'operator_preview_sha256':'0'*64,'operator_provider_id':PROVIDER,
        'worker_launch_performed':False})
    with pytest.raises(m.OperatorPrepareBlocked,match='RESULT_NOT_EXACT_REVIEW'):
        invoke(root,runtime)


def install_cycle_preflight(monkeypatch):
    monkeypatch.setattr(cycle.training,'resolve_training_task',lambda **k:dict(BINDING))
    monkeypatch.setattr(cycle.training,'assert_attempt_unused',lambda **k:None)
    monkeypatch.setattr(cycle,'build_source_state',lambda root:{'git_head':HEAD,'fingerprint_sha256':FP})
    plan_workspace=Mock(side_effect=RuntimeError('REACHED_WORKSPACE_PLAN'))
    monkeypatch.setattr(cycle,'plan_workspace',plan_workspace)
    return plan_workspace


def test_preview_attempt_mismatch_blocked_before_workspace(monkeypatch,tmp_path):
    planning=install_cycle_preflight(monkeypatch)
    with pytest.raises(cycle.GovernedWorkerCycleError,match='identity mismatch'):
        cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,
            task_prompt_id=TASK,attempt_id=ATTEMPT,
            operator_provider_preview=preview(attempt_id='cf10-u180j-a996'))
    planning.assert_not_called()


def test_preview_reverification_failure_blocks_before_workspace(monkeypatch,tmp_path):
    planning=install_cycle_preflight(monkeypatch)
    def bad_verify(**kwargs):
        raise assignment.OperatorPlanBlocked('CATALOG_DRIFT')
    monkeypatch.setattr(assignment,'verify_preview',bad_verify)
    with pytest.raises(assignment.OperatorPlanBlocked,match='CATALOG_DRIFT'):
        cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,
            task_prompt_id=TASK,attempt_id=ATTEMPT,operator_provider_preview=preview())
    planning.assert_not_called()


def test_verified_preview_reaches_workspace_plan(monkeypatch,tmp_path):
    planning=install_cycle_preflight(monkeypatch)
    verified=Mock(return_value=True)
    monkeypatch.setattr(assignment,'verify_preview',verified)
    with pytest.raises(RuntimeError,match='REACHED_WORKSPACE_PLAN'):
        cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,
            task_prompt_id=TASK,attempt_id=ATTEMPT,operator_provider_preview=preview())
    planning.assert_called_once()
    verified.assert_called_once()


def test_legacy_prepare_does_not_demand_operator_preview(monkeypatch,tmp_path):
    planning=install_cycle_preflight(monkeypatch)
    verified=Mock(side_effect=AssertionError('not called'))
    monkeypatch.setattr(assignment,'verify_preview',verified)
    with pytest.raises(RuntimeError,match='REACHED_WORKSPACE_PLAN'):
        cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,
            task_prompt_id=TASK,attempt_id=ATTEMPT)
    planning.assert_called_once()
    verified.assert_not_called()


def test_noncopilot_verified_preview_still_blocked_before_workspace(monkeypatch,tmp_path):
    planning=install_cycle_preflight(monkeypatch)
    monkeypatch.setattr(assignment,'verify_preview',lambda **k:True)
    with pytest.raises(cycle.GovernedWorkerCycleError,match='non-Copilot'):
        cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,task_prompt_id=TASK,
            attempt_id=ATTEMPT,operator_provider_preview=preview(provider_id='openai_codex_cli'))
    planning.assert_not_called()


def test_preview_freeze_drift_detected_before_evidence_publish(monkeypatch,tmp_path):
    install_cycle_preflight(monkeypatch)
    monkeypatch.setattr(assignment,'verify_preview',lambda **k:True)
    plan=SimpleNamespace(layout=SimpleNamespace(workspace_repo=tmp_path/'workspace/repo',
        manifest=tmp_path/'manifest.yaml'))
    monkeypatch.setattr(cycle,'plan_workspace',lambda **k:plan)
    monkeypatch.setattr(cycle,'provision_workspace',lambda *a,**k:None)
    monkeypatch.setattr(cycle,'seal_pre_dispatch_workspace',lambda *a,**k:{'evidence_path':'fixture'})
    monkeypatch.setattr(cycle.training,'prepare_training_pre_dispatch',lambda **k:{'handoff_manifest_sha256':'c'*64})
    monkeypatch.setattr(frozen,'create',lambda **k:{'provider_id':PROVIDER,'model_id':MODEL,
        'source_head':HEAD,'source_state_fingerprint_sha256':FP,
        'catalog_candidate':{'verified':'different'}})
    persisted=Mock(side_effect=AssertionError('must not write original handoff'))
    monkeypatch.setattr(cycle,'_persist_original_handoff_manifest',persisted)
    with pytest.raises(cycle.GovernedWorkerCycleError,match='preview / R082 frozen assignment drift'):
        cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,
            task_prompt_id=TASK,attempt_id=ATTEMPT,operator_provider_preview=preview())
    persisted.assert_not_called()


def test_explicit_preview_persisted_only_after_exact_freeze(monkeypatch,tmp_path):
    install_cycle_preflight(monkeypatch)
    monkeypatch.setattr(assignment,'verify_preview',lambda **k:True)
    plan=SimpleNamespace(layout=SimpleNamespace(workspace_repo=tmp_path/'workspace/repo',
        manifest=tmp_path/'manifest.yaml'))
    monkeypatch.setattr(cycle,'plan_workspace',lambda **k:plan)
    monkeypatch.setattr(cycle,'provision_workspace',lambda *a,**k:None)
    monkeypatch.setattr(cycle,'seal_pre_dispatch_workspace',lambda *a,**k:{'evidence_path':'fixture'})
    monkeypatch.setattr(cycle.training,'prepare_training_pre_dispatch',lambda **k:{'handoff_manifest_sha256':'c'*64})
    monkeypatch.setattr(frozen,'create',lambda **k:{'provider_id':PROVIDER,'model_id':MODEL,
        'source_head':HEAD,'source_state_fingerprint_sha256':FP,
        'catalog_candidate':{'verified':'fixture'}})
    monkeypatch.setattr(cycle,'_persist_original_handoff_manifest',lambda **k:None)
    monkeypatch.setattr(cycle.training,'build_training_canonical_ack',lambda **k:{'expected':'ack'})
    observed=[]
    monkeypatch.setattr(cycle,'_write_yaml_new',lambda path,doc:observed.append((str(path),doc)))
    r=cycle.prepare_cycle(root=tmp_path,runtime_root=tmp_path,
            task_prompt_id=TASK,attempt_id=ATTEMPT,operator_provider_preview=preview())
    assert r['operator_preview_sha256']=='f'*64
    prepared=[v for p,v in observed if p.endswith('governed_worker_cycle_prepared_execution_v0_1.yaml')]
    assert len(prepared)==1
    assert prepared[0]['cf10_operator_assignment_preview_sha256']=='f'*64
    assert r['operator_selection_is_authority'] is False
