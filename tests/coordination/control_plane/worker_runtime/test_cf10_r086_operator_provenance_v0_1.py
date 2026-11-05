"""R086 pure operator provenance contracts, no live attempt or Worker process."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r086_operator_provenance_v0_1 as m,
)

TASK='cf10-validation-check-pipeline-profile-and-optimization-v0-1'
FRONT='wf-cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATT='cf10-u180j-a998'
HEAD='a'*40
FINGERPRINT='b'*64
SHA='c'*64
FREEZE_SHA='d'*64


def fixture():
    source={'git_head':HEAD,'fingerprint_sha256':FINGERPRINT}
    assigned={'provider_id':'github_copilot_cli','model_id':'auto',
              'frozen_assignment_sha256':FREEZE_SHA,
              'catalog_candidate':{'test':'canonical-only'}}
    prepared={'attempt_id':ATT,'worker_id':'worker-01',
              'cf10_training_binding':{'task_prompt_id':TASK,'work_front_id':FRONT},
              m.frozen.KEY: assigned, m.KEY:SHA}
    decision={'binding':{'attempt_id':ATT,'worker_id':'worker-01',
                         'runtime_provider':'github_copilot_cli','runtime_model':'auto',
                         'cf10_frozen_provider_assignment_sha256':FREEZE_SHA,
                         m.DECISION_KEY:SHA}}
    return source,prepared,decision


@pytest.fixture
def trusted(monkeypatch):
    calls=[]
    def verified(**kwargs):
        calls.append('frozen')
        return kwargs['assignment']
    def preview(**kwargs):
        calls.append('preview')
        return {'preview_sha256':SHA,'catalog_candidate':{'test':'canonical-only'},
                'candidate_only':True,'eligible_for_live_dispatch':False}
    monkeypatch.setattr(m.frozen,'verify_prepared',verified)
    monkeypatch.setattr(m.plan,'build_preview',preview)
    return calls


def prepared(source,prepared):
    return m.verify_prepared(root=Path('/unused'),prepared=prepared,
        source_state=source,attempt_id=ATT,worker_id='worker-01')


def decision(source,p,d):
    return m.verify_decision(root=Path('/unused'),prepared=p,decision=d,
        source_state=source,attempt_id=ATT,worker_id='worker-01')


def test_explicit_operator_plan_validated_from_canonical_reconstruction(trusted):
    s,p,d=fixture()
    assert prepared(s,p)==SHA
    assert trusted==['frozen','preview']
    assert decision(s,p,d)['operator_provenance_verified'] is True
    assert decision(s,p,d)['launch_authorized'] is False


def test_no_explicit_preview_preserves_ordinary_copilot_path(trusted):
    s,p,d=fixture();p.pop(m.KEY);d['binding'].pop(m.DECISION_KEY)
    assert prepared(s,p) is None
    assert decision(s,p,d)['operator_provenance_present'] is False
    assert trusted==[]


def test_explicit_sha_missing_from_decision_denied_before_launch(trusted):
    s,p,d=fixture();d['binding'].pop(m.DECISION_KEY)
    with pytest.raises(m.OperatorProvenanceBlocked,match='DISPATCH_OPERATOR_PROVENANCE_DRIFT'):
        decision(s,p,d)


def test_injected_operator_marker_in_ordinary_decision_is_denied(trusted):
    s,p,d=fixture();p.pop(m.KEY)
    with pytest.raises(m.OperatorProvenanceBlocked,match='INJECTED_OPERATOR_DECISION_MARKER'):
        decision(s,p,d)


@pytest.mark.parametrize('bad',['','notsha','z'*64,None,42])
def test_malformed_explicit_marker_is_denied(trusted,bad):
    s,p,d=fixture();p[m.KEY]=bad
    with pytest.raises(m.OperatorProvenanceBlocked,match='OPERATOR_PREVIEW_SHA_REQUIRED'):
        prepared(s,p)


def test_rehashed_but_wrong_operator_preview_is_denied(trusted):
    s,p,d=fixture();p[m.KEY]='e'*64
    with pytest.raises(m.OperatorProvenanceBlocked,match='OPERATOR_SELECTION_PROVENANCE_DRIFT'):
        prepared(s,p)


def test_frozen_catalog_candidate_drift_denied(trusted):
    s,p,d=fixture();p[m.frozen.KEY]['catalog_candidate']={'test':'different'}
    with pytest.raises(m.OperatorProvenanceBlocked,match='OPERATOR_SELECTION_PROVENANCE_DRIFT'):
        prepared(s,p)


def test_other_provider_denied_even_if_frozen_checker_is_stubbed(trusted):
    s,p,d=fixture();p[m.frozen.KEY]['provider_id']='openai_codex_cli'
    with pytest.raises(m.OperatorProvenanceBlocked,match='NON_COPILOT'):
        prepared(s,p)


def test_missing_frozen_assignment_denied(trusted):
    s,p,d=fixture();p.pop(m.frozen.KEY)
    with pytest.raises(m.OperatorProvenanceBlocked,match='FROZEN_ASSIGNMENT_MISSING'):
        prepared(s,p)


def test_ack_marker_retained_exactly_across_dispatcher_ack():
    s,p,d=fixture()
    ready=dict(p,state='READY_FOR_EXPLICIT_DISPATCH')
    assert m.verify_ack(prepared=p,ready=ready) is True
    ready.pop(m.KEY)
    with pytest.raises(m.OperatorProvenanceBlocked,match='ACK_OPERATOR_MARKER_PRESENCE_DRIFT'):
        m.verify_ack(prepared=p,ready=ready)
    ready=dict(p);ready[m.KEY]='f'*64
    with pytest.raises(m.OperatorProvenanceBlocked,match='ACK_OPERATOR_PREVIEW_SHA_DRIFT'):
        m.verify_ack(prepared=p,ready=ready)


def test_ack_injected_marker_denied():
    s,p,d=fixture();p.pop(m.KEY)
    with pytest.raises(m.OperatorProvenanceBlocked,match='ACK_OPERATOR_MARKER_PRESENCE_DRIFT'):
        m.verify_ack(prepared=p,ready=dict(p,**{m.KEY:SHA}))


@pytest.mark.parametrize('field', ['attempt_id','worker_id','runtime_provider','runtime_model',
                                    'cf10_frozen_provider_assignment_sha256'])
def test_decision_identity_or_provider_drift_denied(trusted,field):
    s,p,d=fixture();d['binding'][field]='wrong'
    with pytest.raises(m.OperatorProvenanceBlocked):decision(s,p,d)


def test_read_only_no_lifecycle_authority(trusted):
    s,p,d=fixture()
    report=decision(s,p,d)
    assert report['worker_launched'] is False
    assert report['automatic_fallback'] is False
    assert report['launch_authorized'] is False
