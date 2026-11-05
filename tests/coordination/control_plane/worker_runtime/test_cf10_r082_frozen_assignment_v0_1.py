"""R082 immutable provider-binding contracts. All operations are isolated/pure."""
from __future__ import annotations
import copy
from pathlib import Path
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r082_frozen_assignment_v0_1 as m

HEAD='a'*40
FP='b'*64
HANDOFF='c'*64
TASK='cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATTEMPT='cf10-u180j-a055'

@pytest.fixture
def fixed_catalog(monkeypatch,tmp_path):
    from scripts.coordination.control_plane.worker_runtime import registry
    from scripts.coordination.control_plane.worker_runtime import cf10_r080_catalog_assignment_v0_1 as catalog
    def default(_root):
        return {'provider_id':'github_copilot_cli','model_id':'auto'}
    def choose(_root,request):
        assert request['provider_id']=='github_copilot_cli'
        assert request['model_id']=='auto'
        assert request['capabilities_required']==sorted(request['capabilities_required'])
        return {'provider_id':request['provider_id'],'model_id':request['model_id'],
                'live_dispatch_wired':False,'catalog_binding_sha256':'9'*64,
                'source_head':request['source_head']}
    monkeypatch.setattr(registry,'resolve_default_runtime',default)
    monkeypatch.setattr(catalog,'choose_attempt_candidate',choose)
    monkeypatch.setattr(catalog,'validate_candidate_against_current_catalog',lambda *a,**kw:True)
    return tmp_path

def build(root):
    return m.create(root=root,task_id=TASK,work_front_id='wf-cf10',worker_id='worker-01',
                    attempt_id=ATTEMPT,source_head=HEAD,source_fingerprint=FP,
                    handoff_sha256=HANDOFF)

def verify(root,assignment,**overrides):
    args=dict(root=root,assignment=assignment,task_id=TASK,work_front_id='wf-cf10',
              worker_id='worker-01',attempt_id=ATTEMPT,source_head=HEAD,
              source_fingerprint=FP,handoff_sha256=HANDOFF)
    args.update(overrides)
    return m.verify(**args)

def prepared(binding):
    return {'cf10_training_binding':{'task_prompt_id':TASK,'work_front_id':'wf-cf10'},
            'handoff_manifest_sha256':HANDOFF,m.KEY:binding}

def decision(frozen):
    return {'binding':{'runtime_provider':'github_copilot_cli','runtime_model':'auto',
                       'cf10_frozen_provider_assignment_sha256':frozen['frozen_assignment_sha256']}}

def test_pure_freeze_deterministic_and_never_authorizes(fixed_catalog):
    a=build(fixed_catalog)
    assert a==build(fixed_catalog)
    assert a['schema_version']==m.SCHEMA
    assert a['source_head']==HEAD and a['source_state_fingerprint_sha256']==FP
    assert a['catalog_candidate']['catalog_binding_sha256']=='9'*64
    assert a['selection_is_dispatch_authority'] is False
    assert a['automatic_fallback'] is False
    assert a['worker_launched'] is False
    assert a['owner_claim_consumed'] is False
    assert verify(fixed_catalog,a)==a

def test_frozen_across_prepare_ack_dispatch_launch(fixed_catalog):
    a=build(fixed_catalog)
    doc=prepared(a)
    assert m.verify_prepared(root=fixed_catalog,prepared=doc,assignment=a,
        source_head=HEAD,source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')==a
    verdict=m.verify_decision(root=fixed_catalog,prepared=doc,decision=decision(a),
        source_head=HEAD,source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')
    assert verdict['new_assignment_verified'] is True
    assert verdict['legacy_copilot_only'] is False

@pytest.mark.parametrize('field',[
    'attempt_id','task_id','work_front_id','provider_id','model_id','source_head',
    'source_state_fingerprint_sha256','handoff_manifest_sha256','automatic_fallback',
    'worker_launched','owner_claim_consumed','selection_is_dispatch_authority'])
def test_tamper_fails_closed(fixed_catalog,field):
    x=build(fixed_catalog)
    x[field]='evil' if isinstance(x[field],str) else True
    with pytest.raises(m.FrozenAssignmentBlocked):verify(fixed_catalog,x)

@pytest.mark.parametrize('field,value',[
    ('source_head','d'*40),('source_fingerprint','e'*64),
    ('handoff_sha256','f'*64),('attempt_id','cf10-u180j-a056'),
    ('worker_id','worker-02')])
def test_source_or_attempt_drift_rejected(fixed_catalog,field,value):
    a=build(fixed_catalog)
    with pytest.raises(m.FrozenAssignmentBlocked):verify(fixed_catalog,a,**{field:value})

def test_prep_missing_selection_rejected(fixed_catalog):
    with pytest.raises(m.FrozenAssignmentBlocked):
        m.verify_prepared(root=fixed_catalog,prepared=prepared(None),assignment=None,
            source_head=HEAD,source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')

def test_non_copilot_default_remains_blocked(fixed_catalog,monkeypatch):
    from scripts.coordination.control_plane.worker_runtime import registry
    monkeypatch.setattr(registry,'resolve_default_runtime',lambda _: {'provider_id':'openai_codex_cli','model_id':'auto'})
    with pytest.raises(m.FrozenAssignmentBlocked,match='NON_COPILOT_PILOT_STILL_BLOCKED'):
        build(fixed_catalog)

def test_legacy_historic_unchanged_and_copilot_only(fixed_catalog):
    d={'binding':{'runtime_provider':'github_copilot_cli','runtime_model':'auto'}}
    assert m.verify_decision(root=fixed_catalog,prepared={},decision=d,source_head=HEAD,
                            source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')['legacy_copilot_only']
    d['binding']['runtime_provider']='openai_codex_cli'
    with pytest.raises(m.FrozenAssignmentBlocked):
        m.verify_decision(root=fixed_catalog,prepared={},decision=d,source_head=HEAD,
                          source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')

def test_new_frozen_requires_dispatch_hash(fixed_catalog):
    a=build(fixed_catalog)
    d=decision(a)
    d['binding'].pop('cf10_frozen_provider_assignment_sha256')
    with pytest.raises(m.FrozenAssignmentBlocked,match='DECISION_FROZEN_BINDING_DRIFT'):
        m.verify_decision(root=fixed_catalog,prepared=prepared(a),decision=d,
            source_head=HEAD,source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')

def test_new_frozen_cannot_mislabel_other_provider(fixed_catalog):
    a=build(fixed_catalog)
    d=decision(a);d['binding']['runtime_provider']='openai_codex_cli'
    with pytest.raises(m.FrozenAssignmentBlocked,match='DECISION_FROZEN_BINDING_DRIFT'):
        m.verify_decision(root=fixed_catalog,prepared=prepared(a),decision=d,
            source_head=HEAD,source_fingerprint=FP,attempt_id=ATTEMPT,worker_id='worker-01')

def test_registry_change_fails_even_when_candidate_sha_recomputed(fixed_catalog,monkeypatch):
    a=build(fixed_catalog)
    from scripts.coordination.control_plane.worker_runtime import cf10_r080_catalog_assignment_v0_1 as catalog
    monkeypatch.setattr(catalog,'choose_attempt_candidate',lambda *args,**kwargs: {'provider_id':'github_copilot_cli',
                 'model_id':'auto','live_dispatch_wired':False,'catalog_binding_sha256':'1'*64})
    with pytest.raises(m.FrozenAssignmentBlocked,match='FROZEN_SOURCE_OR_ATTEMPT_DRIFT'):
        verify(fixed_catalog,a)

def test_freeze_does_not_create_files(fixed_catalog):
    before=list(fixed_catalog.rglob('*'))
    _=build(fixed_catalog)
    assert list(fixed_catalog.rglob('*'))==before
