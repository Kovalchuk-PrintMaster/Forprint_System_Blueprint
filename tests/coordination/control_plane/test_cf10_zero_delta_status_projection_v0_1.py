"""S2C isolated synthetic tests. No writes to production or live A047."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import importlib.util
import yaml
import pytest

HERE = Path(__file__).resolve().parent
P = HERE / 'cf10_zero_delta_status_projection_v0_1.py'
if P.is_file():
    spec = importlib.util.spec_from_file_location('cf10_zero_delta_status_projection_v0_1', P)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
else:
    from scripts.coordination.control_plane import cf10_zero_delta_status_projection_v0_1 as m

ATT = 'cf10-u180j-a047'
TASK = 'cf10-planning-projection-cursor-sync-audit-v0-1'
WF = 'wf-cf10-planning-projection-cursor-sync-audit-v0-1'
DIGEST = 'a'*64
BOUND = {'attempt_id':ATT, 'task_prompt_id':TASK,
         'temporal_scope':'CURRENT_WORKSPACE_AT_REVIEW_NOT_HISTORICAL_EXIT'}


def fixture(tmp_path):
    root = tmp_path/'canonical'; root.mkdir()
    report = {
        'schema_version':'cf10_zero_delta_operator_review_preview_v0_1',
        'status':'READY_FOR_EXPLICIT_OPERATOR_DECISION',
        'attempt_id':ATT,'task_prompt_id':TASK,'work_front_id':WF,
        'governed_state':'AWAITING_OPERATOR_REVIEW',
        'automatic_accept':False,'automatic_commit':False,'automatic_push':False,
        'automatic_publication':False,'governed_status_changed_by_this_tool':False,
        'historical_exit_attestation':False,'zero_delta_promotion_required':False,
        'decision_binding_sha256':DIGEST,'bound_evidence':deepcopy(BOUND),
        'existing_decisions':[],'operator_decision_recorded':False,
    }
    return root, report


def run(root, preview):
    return m.project(root, root, root/'tmp/proof.json', TASK, ATT,
                     evaluator=lambda *_: deepcopy(preview))


def recorded(root, preview, decision='ACCEPT'):
    r = {
        'schema_version':'cf10_zero_delta_operator_decision_v0_1',
        'record_role':'zero_delta_operator_decision_not_promotion_or_publication',
        'decision_id':'cf10-test-decision-001',
        'decision':decision,'attempt_id':ATT,'task_prompt_id':TASK,
        'work_front_id':WF,'operator_ref':'forprint-operator',
        'recorded_at':datetime(2026,10,26,tzinfo=timezone.utc).isoformat(),
        'review_binding_sha256':DIGEST,'evidence_bindings':deepcopy(BOUND),
        'zero_delta_confirmed_current_workspace':True,
        'historical_exit_attestation':False,'canonical_promotion_performed':False,
        'commit_performed':False,'push_performed':False,
        'publication_state':'NOT_ATTESTED',
        'governed_status_projection_updated':False,
        'next_boundary':'ZERO_DELTA_STATUS_POLICY_RECONCILIATION',
    }
    rel = m.DECISION_DIR/f'{ATT}__zero_delta_operator_decision_v0_1.yaml'
    p = root/rel; p.parent.mkdir(parents=True);p.write_text(yaml.safe_dump(r), encoding='utf-8')
    preview['existing_decisions']=[{'path':rel.as_posix(),'record':deepcopy(r),'sha256':m.file_sha256(p)}]
    preview['operator_decision_recorded']=True
    preview['status']='EXISTING_OPERATOR_DECISION'
    return p,r


def test_no_decision_is_still_gate(tmp_path):
    root, preview=fixture(tmp_path)
    result=run(root,preview)
    assert result['review_overlay_state']=='AWAITING_EXPLICIT_ZERO_DELTA_REVIEW'
    assert result['next_boundary']=='EXPLICIT_HUMAN_OPERATOR_DECISION'
    assert result['operator_decision_recorded'] is False
    assert result['next_dispatch_authorized'] is False
    assert result['governed_cycle_base_state_unchanged'] is True
    assert list(root.iterdir())==[]

@pytest.mark.parametrize('decision,state,boundary',[
    ('ACCEPT','ZERO_DELTA_OPERATOR_ACCEPTED','ROADMAP_OPERATOR_PLANNING_REVIEW_NOT_DISPATCH'),
    ('HOLD','ZERO_DELTA_OPERATOR_HELD','HOLD_SUPERSESSION_POLICY_REVIEW'),
    ('RETURN','ZERO_DELTA_OPERATOR_RETURNED','EXPLICIT_REWORK_AUTHORIZATION_REVIEW'),
])
def test_valid_decisions_map_to_non_authoritative_overlay(tmp_path,decision,state,boundary):
    root,preview=fixture(tmp_path);recorded(root,preview,decision)
    result=run(root,preview)
    assert result['review_overlay_state']==state
    assert result['next_boundary']==boundary
    assert result['decision']==decision
    assert result['next_dispatch_authorized'] is False
    assert result['roadmap_lifecycle_closed'] is False
    assert all(result[k] is False for k in ('automatic_accept','automatic_push','automatic_commit','automatic_publication','zero_delta_promotion_required'))

@pytest.mark.parametrize('key,mutated,reason',[
    ('review_binding_sha256','b'*64,'DECISION_PROOF_BINDING_MISMATCH'),
    ('record_role','not_operator_review','DECISION_ROLE_INVALID'),
    ('canonical_promotion_performed',True,'DECISION_AUTHORITY_WIDENED'),
    ('historical_exit_attestation',True,'DECISION_AUTHORITY_WIDENED'),
    ('zero_delta_confirmed_current_workspace',False,'DECISION_CURRENT_WORKSPACE_ACK_MISSING'),
    ('publication_state','PUBLISHED','DECISION_PUBLICATION_CLAIM_INVALID'),
])
def test_tampered_record_blocks(tmp_path,key,mutated,reason):
    root, preview=fixture(tmp_path);p,record=recorded(root,preview)
    record[key]=mutated;p.write_text(yaml.safe_dump(record),encoding='utf-8')
    preview['existing_decisions'][0]['record']=deepcopy(record)
    preview['existing_decisions'][0]['sha256']=m.file_sha256(p)
    with pytest.raises(m.ProjectionBlocked,match=reason):run(root,preview)


def test_decision_rebound_to_different_proof_blocks(tmp_path):
    root,preview=fixture(tmp_path);recorded(root,preview)
    preview['decision_binding_sha256']='b'*64
    with pytest.raises(m.ProjectionBlocked,match='DECISION_PROOF_BINDING_MISMATCH'):run(root,preview)


def test_changed_since_preview_blocks(tmp_path):
    root,preview=fixture(tmp_path);p,_=recorded(root,preview)
    p.write_text(p.read_text()+'# extra\n')
    with pytest.raises(m.ProjectionBlocked,match='DECISION_CHANGED_SINCE_S2B_PREVIEW'):run(root,preview)


def test_noncanonical_decision_path_blocks(tmp_path):
    root,preview=fixture(tmp_path);recorded(root,preview)
    preview['existing_decisions'][0]['path']='coordination/other.yaml'
    with pytest.raises(m.ProjectionBlocked,match='DECISION_PATH_NOT_CANONICAL'):run(root,preview)


def test_authority_widened_preview_blocks(tmp_path):
    root,preview=fixture(tmp_path);preview['automatic_accept']=True
    with pytest.raises(m.ProjectionBlocked,match='S2B_AUTHORITY_OR_TIME_SCOPE_INVALID'):run(root,preview)


def test_two_decisions_block(tmp_path):
    root,preview=fixture(tmp_path);recorded(root,preview)
    preview['existing_decisions'].append(deepcopy(preview['existing_decisions'][0]))
    with pytest.raises(m.ProjectionBlocked,match='S2B_DECISION_CARDINALITY_INVALID'):run(root,preview)


def test_original_governed_state_not_mutated(tmp_path):
    root,preview=fixture(tmp_path);recorded(root,preview)
    raw=root/m.DECISION_DIR/f'{ATT}__zero_delta_operator_decision_v0_1.yaml'
    before=raw.read_bytes();result=run(root,preview)
    assert raw.read_bytes()==before
    assert preview['governed_state']=='AWAITING_OPERATOR_REVIEW'
    assert result['governed_cycle_base_state']=='AWAITING_OPERATOR_REVIEW'
    assert result['report_role']=='DERIVED_READ_ONLY_NON_AUTHORITATIVE'
