"""Pure R079 contract tests. No actual provider or Worker execution."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import pytest

from scripts.coordination.control_plane.worker_runtime import cf10_provider_neutral_boundary_v0_1 as m


def cli(pid='github_copilot_cli'):
    return {
        'provider_id': pid, 'runtime_id': pid,
        'state':'READY','ready':True,
        'adapter_type':'CONSOLE_COMMAND',
        'command_representation':'ARGV_NO_SHELL',
        'executable': '/usr/local/bin/' + pid.replace('_','-'),
        'model_selection':{'mode':'runtime_selectable','default':'auto'},
        'auth':{'material_source':'outside_git','value_serialized':False},
        'capabilities':{'non_interactive_prompt':True,'workspace_read':True,
            'workspace_write':'launch_policy_bound','completion_capture':True},
        'authority':{'execution':False,'dispatch':False,'release':False,
            'push':False,'merge':False,'automatic_accept':False},
    }


def catalog(providers=None):
    return {'schema_version':m.REGISTRY_SCHEMA,
        'worker_identity':{'provider_neutral':True,'provider_selected_per_attempt':True},
        'adapter_interface':{'architectural_authority':False,'shell_execution_allowed':False},
        'providers':providers if providers is not None else [cli()]}


def request(provider_id='github_copilot_cli'):
    return {'attempt_id':'cf10-u180j-a055','source_head':'a'*40,
        'worker_id':'worker-01','task_id':'cf10-validation-check-pipeline-profile-and-optimization-v0-1',
        'work_front_id':'wf-cf10','provider_id':provider_id,'model_id':'auto',
        'capabilities_required':['non_interactive_prompt','completion_capture']}


def test_existing_cli_descriptor_is_valid():
    assert len(m.validate_registry_for_future(catalog())) == 1


def test_multiple_ready_provider_descriptors_are_accepted_without_live_wiring():
    rows=m.validate_registry_for_future(catalog([cli(),cli('openai_codex_cli')]))
    assert len(rows)==2


def test_selection_is_candidate_only_even_with_two_ready_providers():
    d=m.select_candidate(catalog=catalog([cli(),cli('openai_codex_cli')]),
        request=request('openai_codex_cli'))
    assert d['provider_id']=='openai_codex_cli'
    assert d['worker_id']=='worker-01'
    assert d['dispatch_authorized'] is False
    assert d['operator_authority_granted'] is False
    assert d['worker_launched'] is False
    assert d['automatic_fallback'] is False


def test_repeated_selection_is_deterministic():
    a=m.select_candidate(catalog=catalog(),request=request())
    b=m.select_candidate(catalog=catalog(),request=request())
    assert a==b
    expected=dict(a)
    digest=expected.pop('selection_candidate_sha256')
    assert digest==hashlib.sha256(json.dumps(expected,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

@pytest.mark.parametrize('field,value',[
    ('provider_id',None),('provider_id','nonexistent_provider'),
    ('attempt_id','cf10-u180j-a054/../a055'),('source_head','bad'),
    ('worker_id','../x'),('capabilities_required',['unknown']),
    ('capabilities_required',['workspace_write']),
    ('capabilities_required',['completion_capture','completion_capture']),
    ('model_id',''),
])
def test_invalid_or_unsupported_explicit_choices_are_rejected(field,value):
    r=request();r[field]=value
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.select_candidate(catalog=catalog(),request=r)


def test_not_configured_does_not_get_selected():
    row=cli('openai_codex_cli')
    row.update(state='NOT_CONFIGURED',ready=False,executable=None,
               model_selection=None,auth=None,capabilities=None)
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.select_candidate(catalog=catalog([cli(),row]),request=request('openai_codex_cli'))


def test_ready_provider_with_authority_is_rejected():
    row=cli();row['authority']['push']=True
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.validate_registry_for_future(catalog([row]))


def test_duplicate_provider_is_rejected():
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.validate_registry_for_future(catalog([cli(),cli()]))


def test_shell_execution_and_secret_serialization_are_rejected():
    row=cli();row['auth']['value_serialized']=True
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.validate_registry_for_future(catalog([row]))
    x=catalog();x['adapter_interface']['shell_execution_allowed']=True
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.validate_registry_for_future(x)


def test_remote_requires_remote_reference_not_executable():
    row=cli('future_remote_adapter')
    row.update(adapter_type='REMOTE_JOB',command_representation='REMOTE_JOB_REFERENCE')
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.validate_registry_for_future(catalog([row]))
    row['executable']=None;row['remote_runtime_ref']='future:runtime:1'
    assert m.validate_registry_for_future(catalog([row]))[0]['adapter_type']=='REMOTE_JOB'


def test_no_implicit_model_or_permission_from_catalog():
    row=cli();row['model_selection']={'mode':'fixed','default':'safe-model'}
    r=request();r['model_id']='other'
    with pytest.raises(m.ProviderBoundaryBlocked):
        m.select_candidate(catalog=catalog([row]),request=r)
    r['model_id']='safe-model'
    assert not m.select_candidate(catalog=catalog([row]),request=r)['operator_authority_granted']


def test_audit_reports_legacy_coupling_without_claiming_ready(tmp_path:Path):
    first=m.COUPLING_CHECKS[0]
    p=tmp_path/first[1];p.parent.mkdir(parents=True);p.write_text(first[2])
    report=m.audit_current_source(tmp_path)
    assert report['findings'][0]['state']=='OBSERVED_LEGACY_COUPLING'
    assert report['findings'][1]['state']=='UNVERIFIED_SOURCE_MISSING'
    assert report['status']=='MULTI_PROVIDER_LIVE_DISPATCH_NOT_YET_ENABLED'
    assert report['worker_launched'] is False
    assert report['authorization_granted'] is False


def test_protocol_is_only_a_code_interface_not_an_executor():
    class Dummy:
        def inspect_readiness(self,binding):return {'ready':False}
        def build_invocation(self,binding,frozen_task):return {'non_authorizing':True}
        def normalize_result_candidate(self,provider_stream,binding):return {'untrusted':True}
    assert isinstance(Dummy(),m.WorkerProviderAdapter)
