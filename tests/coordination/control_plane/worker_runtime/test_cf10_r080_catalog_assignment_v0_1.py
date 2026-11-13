"""R080 non-authorizing multi-ready catalog and source-bound selection tests."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime import registry
from scripts.coordination.control_plane.worker_runtime import cf10_r080_catalog_assignment_v0_1 as m


def cli(provider='github_copilot_cli'):
    return dict(provider_id=provider, runtime_id=provider, state='READY', ready=True,
        adapter_type='CONSOLE_COMMAND', command_representation='ARGV_NO_SHELL',
        executable='/usr/local/bin/' + provider.replace('_', '-'),
        model_selection={'mode':'runtime_selectable', 'default':'auto'},
        auth={'material_source':'outside_git','value_serialized':False},
        capabilities={'non_interactive_prompt':True,'workspace_read':True,
             'workspace_write':'launch_policy_bound','completion_capture':True},
        authority={'execution':False,'dispatch':False,'release':False,
             'push':False,'merge':False,'automatic_accept':False})


def catalog(*, multiple=False):
    return {'schema_version':'forprint_worker_runtime_adapter_registry_v0_1',
        'worker_identity':{'provider_neutral':True,'provider_selected_per_attempt':True},
        'adapter_interface':{'architectural_authority':False,'shell_execution_allowed':False},
        'providers':[cli(), cli('openai_codex_cli')] if multiple else [cli()]}


def request(provider='github_copilot_cli'):
    return dict(attempt_id='cf10-u180j-a099', source_head='a'*40,
        worker_id='worker-01', task_id='cf10-validation-check-pipeline-profile-and-optimization-v0-1',
        work_front_id='wf-cf10', provider_id=provider, model_id='auto',
        capabilities_required=['non_interactive_prompt','completion_capture'])


def fixture(tmp_path,monkeypatch,*,multiple=True):
    a=catalog(multiple=multiple)
    root=tmp_path
    (root/'coordination/registry').mkdir(parents=True)
    (root/'config').mkdir()
    (root/m.CATALOG_PATH).write_text(yaml.safe_dump(a))
    (root/m.CONFIG_PATH).write_text('provider: github_copilot_cli\n')
    def load(_):return copy.deepcopy(yaml.safe_load((root/m.CATALOG_PATH).read_text()))
    monkeypatch.setattr(m.registry,'load_runtime_registry',load)
    monkeypatch.setattr(m.registry,'resolve_default_runtime',lambda _:dict(provider_id='github_copilot_cli',model_id='auto'))
    return root


def test_inspect_reports_multiple_ready_no_authority(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    out=m.inspect_catalog(root)
    assert out['ready_provider_count']==2
    assert out['ready_provider_ids']==['github_copilot_cli','openai_codex_cli']
    assert out['default_provider_id']=='github_copilot_cli'
    assert out['live_dispatch_provider_selection_wired'] is False
    assert out['authorization_granted'] is False
    assert out['worker_launched'] is False
    assert out['claim_consumed'] is False


def test_candidate_selection_is_explicit_and_bound(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    result=m.choose_attempt_candidate(root,request('openai_codex_cli'))
    assert result['provider_id']=='openai_codex_cli'
    assert result['legacy_default_provider_id']=='github_copilot_cli'
    assert result['provider_credentials_verified'] is False
    assert result['live_dispatch_wired'] is False
    assert result['worker_launched'] is False
    assert result['automatic_retry'] is False
    assert result['authorization_granted'] is False
    assert m.validate_candidate_against_current_catalog(root,result)


def test_candidate_deterministic(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    assert m.choose_attempt_candidate(root,request())==m.choose_attempt_candidate(root,request())


def test_registry_drift_blocks_even_if_candidate_body_well_formed(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    result=m.choose_attempt_candidate(root,request())
    (root/m.CATALOG_PATH).write_text((root/m.CATALOG_PATH).read_text()+'\n')
    with pytest.raises(m.AssignmentBlocked,match='CATALOG_DRIFT'):
        m.validate_candidate_against_current_catalog(root,result)


def test_runtime_config_drift_blocks(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    result=m.choose_attempt_candidate(root,request())
    (root/m.CONFIG_PATH).write_text('provider: different\n')
    with pytest.raises(m.AssignmentBlocked,match='RUNTIME_CONFIG_DRIFT'):
        m.validate_candidate_against_current_catalog(root,result)


@pytest.mark.parametrize('key,value',[
    ('provider_id','not_ready'),('source_head','b'),('attempt_id','../a099'),
    ('worker_id',''),('capabilities_required',['workspace_write']),
    ('model_id',''),('capabilities_required',['completion_capture','completion_capture']),
])
def test_bad_selection_fails_closed(tmp_path,monkeypatch,key,value):
    root=fixture(tmp_path,monkeypatch)
    req=request();req[key]=value
    with pytest.raises(m.AssignmentBlocked):
        m.choose_attempt_candidate(root,req)


@pytest.mark.parametrize('key,value',[
    ('provider_id','openai_codex_cli'),('dispatch_authorized',True),
    ('worker_launched',True),('owner_claim_consumed',True),
    ('catalog_binding_sha256','0'*64),('authorization_granted',True),
])
def test_mutated_candidate_rejected(tmp_path,monkeypatch,key,value):
    root=fixture(tmp_path,monkeypatch)
    result=m.choose_attempt_candidate(root,request())
    result[key]=value
    with pytest.raises(m.AssignmentBlocked):
        m.validate_candidate_against_current_catalog(root,result)


def test_no_implicit_fallback_to_default(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch,multiple=False)
    with pytest.raises(m.AssignmentBlocked):
        m.choose_attempt_candidate(root,request('openai_codex_cli'))


def test_provider_descriptor_hash_binds_selected_provider(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    result=m.choose_attempt_candidate(root,request())
    row=yaml.safe_load((root/m.CATALOG_PATH).read_text())['providers'][0]
    assert result['selected_provider_descriptor_sha256']==hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()


def test_untrusted_catalog_ready_with_authority_rejected(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    x=yaml.safe_load((root/m.CATALOG_PATH).read_text())
    x['providers'][1]['authority']['push']=True
    (root/m.CATALOG_PATH).write_text(yaml.safe_dump(x))
    with pytest.raises(Exception):
        m.choose_attempt_candidate(root,request('openai_codex_cli'))


def test_reject_symlink_catalog(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    p=root/m.CATALOG_PATH
    target=root/'catalog-ref.yaml'
    p.rename(target);p.symlink_to(target)
    with pytest.raises(m.AssignmentBlocked,match='SOURCE_FILE_MISSING_OR_SYMLINK'):
        m.inspect_catalog(root)


def test_actual_registry_allows_multi_ready_in_isolated_catalog(tmp_path):
    """Tests the actual registry loader, not just the pure R079 candidate fixture."""
    root=tmp_path
    (root/'coordination/registry').mkdir(parents=True)
    target=root/m.CATALOG_PATH
    target.write_text(yaml.safe_dump(catalog(multiple=True)))
    loaded=registry.load_runtime_registry(root)
    assert len([r for r in loaded['providers'] if r['state']=='READY'])==2


def test_actual_registry_rejects_zero_ready(tmp_path):
    root=tmp_path
    (root/'coordination/registry').mkdir(parents=True)
    x=catalog()
    for row in x['providers']:
        row.update(state='NOT_CONFIGURED',ready=False,executable=None,model_selection=None,auth=None)
    (root/m.CATALOG_PATH).write_text(yaml.safe_dump(x))
    with pytest.raises(registry.RuntimeRegistryError,match='at least one READY'):
        registry.load_runtime_registry(root)


def test_project_default_still_copilot():
    root=Path(__file__).resolve().parents[4]
    cfg=registry.resolve_default_runtime(root)
    assert cfg['provider_id']=='github_copilot_cli'
    assert cfg['model_id']=='auto'


def test_no_source_has_runtime_credential_values():
    root=Path(__file__).resolve().parents[4]
    catalog_data=registry.load_runtime_registry(root)
    assert all(row['authority'].get('execution') is False for row in catalog_data['providers'])


def test_recomputed_digest_cannot_authorize_untrusted_mutation(tmp_path,monkeypatch):
    root=fixture(tmp_path,monkeypatch)
    result=m.choose_attempt_candidate(root,request())
    result['result_accepted']=True
    result.pop('catalog_binding_sha256')
    result['catalog_binding_sha256']=m._digest(result)
    with pytest.raises(m.AssignmentBlocked,match='CANDIDATE_NOT_REPRODUCIBLE'):
        m.validate_candidate_against_current_catalog(root,result)


def test_source_audit_recognizes_migrated_ready_rule(tmp_path):
    from scripts.coordination.control_plane.worker_runtime import cf10_provider_neutral_boundary_v0_1 as neutral
    for code,rel,needle in neutral.COUPLING_CHECKS:
        p=tmp_path/rel
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('if ready_count < 1:' if code=='registry_single_ready' else needle)
    audit=neutral.audit_current_source(tmp_path)
    found={row['code']:row['state'] for row in audit['findings']}
    assert found['registry_single_ready']=='MIGRATED_MULTI_READY_CATALOG_NO_DISPATCH_CHANGE'
    assert found['training_copilot_pin']=='OBSERVED_LEGACY_COUPLING'
