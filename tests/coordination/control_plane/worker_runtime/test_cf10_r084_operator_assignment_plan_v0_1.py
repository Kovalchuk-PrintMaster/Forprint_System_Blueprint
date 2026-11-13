"""R084 operator assignment plan, pure fake-catalog tests, no Worker activity."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import pytest
import yaml
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r084_operator_assignment_plan_v0_1 as m,
    cf10_r080_catalog_assignment_v0_1 as r080,
)

TASK={'task_prompt_id':'cf10-validation-check-pipeline-profile-and-optimization-v0-1',
      'work_front_id':'wf-cf10-validation-check-pipeline-profile-and-optimization-v0-1'}
SOURCE={'git_head':'a'*40,'fingerprint_sha256':'c'*64}
ATTEMPT='cf10-u180j-a995'

@pytest.fixture
def sample_root(tmp_path):
    # Copied fixture files are local; no external root, ledger or process.
    root=tmp_path/'repo'
    (root/'coordination/registry').mkdir(parents=True)
    (root/'config').mkdir()
    source=Path(__file__).resolve().parents[4]
    for rel in ('coordination/registry/worker_runtime_adapters_v0_1.yaml','config/worker_runtime.yaml'):
        (root/rel).write_bytes((source/rel).read_bytes())
    return root


def preview(root, **values):
    kw=dict(root=root,task_binding=TASK,source_state=SOURCE,
            attempt_id=ATTEMPT,worker_id='worker-01',
            provider_id='github_copilot_cli',model_id='auto')
    kw.update(values)
    return m.build_preview(**kw)


def test_one_ready_copilot_candidate_no_authority(sample_root):
    p=preview(sample_root)
    assert p['status']=='CANDIDATE_ONLY_NOT_PREPARED_NOT_FROZEN'
    assert p['provider_id']=='github_copilot_cli'
    assert p['candidate_only'] and not p['eligible_for_live_dispatch']
    assert all(p[x] is False for x in ('claim_consumed','ledger_written','worker_launched','automatic_fallback','automatic_retry'))
    assert m.verify_preview(root=sample_root,preview=p,task_binding=TASK,source_state=SOURCE)


def test_plan_deterministic_same_inputs(sample_root):
    assert preview(sample_root)==preview(sample_root)


def test_two_ready_provider_choices_are_explicit(sample_root):
    reg=sample_root/'coordination/registry/worker_runtime_adapters_v0_1.yaml'
    data=yaml.safe_load(reg.read_text())
    second=deepcopy(data['providers'][0]);second.update(provider_id='openai_codex_cli',runtime_id='openai_codex_cli',
        executable='/opt/forprint-codex-bin',display_name='Codex test')
    second['model_selection']['default']='codex-model-test'
    if len(data['providers'])==1: data['providers'].append(second)
    else: data['providers'][1]=second
    reg.write_text(yaml.safe_dump(data,sort_keys=False))
    p=preview(sample_root,provider_id='openai_codex_cli',model_id='codex-model-test')
    assert p['provider_id']=='openai_codex_cli'
    assert p['catalog_candidate']['legacy_default_provider_id']=='github_copilot_cli'
    assert m.verify_preview(root=sample_root,preview=p,task_binding=TASK,source_state=SOURCE)
    assert p['eligible_for_live_dispatch'] is False


def test_unconfigured_codex_fails_without_default_fallback(sample_root):
    with pytest.raises(m.OperatorPlanBlocked, match='CATALOG_SELECTION_UNAVAILABLE'):
        preview(sample_root,provider_id='openai_codex_cli',model_id='auto')


def test_provider_is_mandatory(sample_root):
    with pytest.raises(m.OperatorPlanBlocked,match='EXPLICIT_PROVIDER_ID_REQUIRED'):
        preview(sample_root,provider_id='')


def test_bad_workfront_identity_fails(sample_root):
    broken=dict(TASK,work_front_id='../escape')
    with pytest.raises(m.OperatorPlanBlocked, match='WORK_FRONT_TASK_IDENTITY_INVALID'):
        preview(sample_root,task_binding=broken)

@pytest.mark.parametrize('field,value',[('attempt_id','../bad'),('worker_id',''),('model_id',''),
                                           ('provider_id','github_copilot_cli;echo 1')])
def test_injected_or_unbound_values_fail(sample_root,field,value):
    with pytest.raises((m.OperatorPlanBlocked,ValueError)):
        preview(sample_root,**{field:value})


def test_altered_preview_even_rehashed_cannot_rebind(sample_root):
    p=preview(sample_root)
    p['provider_id']='openai_codex_cli'; p['preview_sha256']=m.digest({k:v for k,v in p.items() if k!='preview_sha256'})
    with pytest.raises(m.OperatorPlanBlocked):
        m.verify_preview(root=sample_root,preview=p,task_binding=TASK,source_state=SOURCE)


def test_catalog_tamper_blocks_recheck(sample_root):
    p=preview(sample_root)
    reg=sample_root/'coordination/registry/worker_runtime_adapters_v0_1.yaml'
    reg.write_text(reg.read_text()+'\n# drift\n')
    with pytest.raises(m.OperatorPlanBlocked):
        m.verify_preview(root=sample_root,preview=p,task_binding=TASK,source_state=SOURCE)


def test_source_head_changes_block_old_preview(sample_root):
    p=preview(sample_root)
    with pytest.raises(m.OperatorPlanBlocked,match='PREVIEW_NOT_REPRODUCIBLE'):
        m.verify_preview(root=sample_root,preview=p,task_binding=TASK,
            source_state=dict(SOURCE,git_head='b'*40))


def test_task_binding_changes_block_old_preview(sample_root):
    p=preview(sample_root)
    with pytest.raises(m.OperatorPlanBlocked,match='PREVIEW_NOT_REPRODUCIBLE'):
        m.verify_preview(root=sample_root,preview=p,task_binding=dict(TASK,task_prompt_id='cf10-other-task'),source_state=SOURCE)


def test_inspect_lists_registry_not_launch(sample_root):
    result=m.inspect(sample_root)
    assert result['ready_provider_ids']==['github_copilot_cli']
    assert not result['live_dispatch_provider_selection_wired']


def test_cannot_plan_existing_or_consumed_attempt_before_task_resolution(monkeypatch,tmp_path):
    # The root-scope guard should deny before importing or reading a ledger.
    with pytest.raises(m.OperatorPlanBlocked,match='EXACT_CANONICAL_ROOTS_REQUIRED'):
        m.live_preview(root=tmp_path,runtime_root=tmp_path,task_id=TASK['task_prompt_id'],
            attempt_id=ATTEMPT,worker_id='worker-01',provider_id='github_copilot_cli',model_id='auto')
