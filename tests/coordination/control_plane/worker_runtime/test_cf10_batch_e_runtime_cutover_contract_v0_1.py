"""Batch E source-only whole-process cutover; no root/systemd/Worker authority."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import pytest

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import (
    cf10_batch_e_runtime_cutover_contract_v0_1 as e,
)

HERE=Path(__file__).resolve().parent
ROOT=Path(__file__).resolve().parents[4]

def fixture():
    source=HERE/'test_cf10_batch_d_canonical_ipc_preclaim_bridge_v0_1.py'
    s=importlib.util.spec_from_file_location('batch_e_existing_batch_d_fixture',source)
    mod=importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    inv,c,_=mod.scenario()
    spec,plan=mod.bound(inv,c)
    r030=mod.route()
    report=r030.review_guarded_ipc_handoff(spec=spec,plan=plan,
        invocation=inv,candidate=c)
    return inv,c,spec,plan,report


def base():
    inv,c,s,p,report=fixture()
    raw={k:v for k,v in report.items() if k not in (
        'runtime_cutover_report_sha256','runtime_cutover_state',
        'whole_process_isolation_gates_open')}
    return inv,c,s,p,raw


def test_full_canonical_join_is_a_deterministic_non_authorizing_result():
    inv,c,s,p,review=base()
    result=e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=review)
    assert result['status']==e.STATE
    assert result['open_gates']==list(e.EXPECTED_OPEN)
    assert result['ipc_model_tools']==['ForPrintValidation-run_repo_head']
    assert result['static_ipc_tool_restriction_source_validated'] is True
    assert result['static_systemd_baseline_source_validated'] is True
    assert result['inference_transport']=='DIRECT_COPILOT_NETWORK_NOT_EGRESS_ISOLATED'
    assert result['credential_scope']=='UNVERIFIED_PROVIDER_HOME_ENV_CACHE'
    assert result['ipc_scope']=='R140_LAB_ONLY_NO_PRODUCTION_LISTENER'
    assert result['authority']==e.MODELED_NEGATIVE
    assert result['report_sha256']==e._digest({k:v for k,v in result.items() if k!='report_sha256'})
    assert result==e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=review)
    assert 'fixture prompt' not in json.dumps(result)
    assert 'token' not in json.dumps(result).lower()


def test_r030_integrates_batch_e_without_enabling_live_authority():
    inv,c,s,p,preclaim=fixture()
    assert preclaim['runtime_cutover_state']==e.STATE
    assert preclaim['whole_process_isolation_gates_open']==list(e.EXPECTED_OPEN)
    assert len(preclaim['runtime_cutover_report_sha256'])==64
    assert preclaim['live_worker_authorized'] is False
    assert preclaim['claim_consumed'] is False
    assert preclaim['worker_started'] is False


def test_profile_has_explicit_protect_home_but_no_network_enforcement():
    props=e._canonical_profile({'properties':dict(binding.EXPECTED_PROPERTIES)})
    assert props['ProtectHome']=='yes'
    assert props['NoNewPrivileges']=='yes'
    assert 'IPAddressDeny' not in props and 'PrivateNetwork' not in props
    assert e.EXPECTED_OPEN[0].startswith('G1_')


@pytest.mark.parametrize('key',[
    'PrivateNetwork','IPAddressDeny','IPAddressAllow','RestrictAddressFamilies',
    'JoinsNamespaceOf','SocketBindAllow','SocketBindDeny','NetworkNamespacePath',
])
def test_no_unreviewed_network_policy_claims(key):
    props=dict(binding.EXPECTED_PROPERTIES)
    props[key]='yes' if key!='IPAddressDeny' else 'any'
    with pytest.raises(e.RuntimeCutoverHold,match='NETWORK_POLICY'):
        e._canonical_profile({'properties':props})

@pytest.mark.parametrize('key,value',[
    ('User','root'),('Group','root'),('ProtectSystem','full'),
    ('ProtectHome','no'),('KillMode','process'),
    ('StateDirectory','unreviewed'),('NoNewPrivileges','no'),
])
def test_no_systemd_baseline_drift(key,value):
    p=dict(binding.EXPECTED_PROPERTIES);p[key]=value
    with pytest.raises(e.RuntimeCutoverHold):e._canonical_profile({'properties':p})

@pytest.mark.parametrize('name',[
    'live_worker_authorized','claim_consumed','worker_started',
    'terminal_ledger_written','g1_g5_closed','automatic_retry',
])
def test_r030_cannot_claim_success(name):
    inv,c,s,p,r=base();r[name]=True
    with pytest.raises(e.RuntimeCutoverHold,match='PRETENDS_TO_AUTHORIZE'):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=r)

@pytest.mark.parametrize('name',[
    'attempt_id','source_head','unit','canonical_argv_sha256','model_tools',
])
def test_r030_identity_mismatch_holds(name):
    inv,c,s,p,r=base()
    r[name]=['view'] if name=='model_tools' else 'incorrect'
    with pytest.raises(e.RuntimeCutoverHold,match='R030_FROZEN_IDENTITY'):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=r)

@pytest.mark.parametrize('where,key,change',[
    ('inv','argv', ['bad']),('inv','workspace_repo','/tmp/bad'),
    ('candidate','attempt_id','other'),('candidate','source_head','0'*40),
])
def test_canonical_invocation_and_candidate_bound(where,key,change):
    inv,c,s,p,r=base(); (inv if where=='inv' else c)[key]=change
    with pytest.raises(e.RuntimeCutoverHold):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=r)


def test_crosswalk_digest_change_rejected():
    inv,c,s,p,r=base();r['crosswalk_report_sha256']='e'*64
    with pytest.raises(e.RuntimeCutoverHold,match='CROSSWALK_DIGEST'):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=r)


def test_candidate_hidden_tool_widening_rejected():
    inv,c,s,p,r=base()
    c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['tools'].append('run_repo_status')
    with pytest.raises(e.RuntimeCutoverHold,match='EXACT_READONLY_IPC_CROSSWALK'):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=r)


def test_plan_properties_tamper_rejected_even_with_canonical_hash():
    inv,c,s,p,r=base()
    p['properties']['ProtectHome']='no'
    with pytest.raises(e.RuntimeCutoverHold,match='FROZEN_R013_PLAN_DRIFT'):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,preclaim=r)


def test_missing_review_cannot_be_replaced_with_worker_report():
    inv,c,s,p,r=base()
    with pytest.raises(e.RuntimeCutoverHold,match='R030_PRECLAIM_SCHEMA'):
        e.review(spec=s,plan=p,invocation=inv,candidate=c,
                 preclaim={'schema_version':'WORKER_SAYS_SUCCESS'})


def test_source_check_cannot_enable_worker():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_launcher_v0_1 as launcher,
    )
    with mock.patch.object(launcher,'LIVE_CUTOVER_ENABLED',False):
        doc=e.source_check()
    assert doc['live_worker_authorized'] is False
    assert doc['open_gates']==list(e.EXPECTED_OPEN)


def test_source_check_denies_accidental_live_switch():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_launcher_v0_1 as launcher,
    )
    with mock.patch.object(launcher,'LIVE_CUTOVER_ENABLED',True):
        with pytest.raises(e.RuntimeCutoverHold,match='LIVE_SWITCH_ALREADY_ON'):
            e.source_check()
    assert launcher.LIVE_CUTOVER_ENABLED is False


def test_review_source_does_not_modify_launch_or_claim_route():
    content=(ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py').read_text()
    before=content.split('def review_guarded_ipc_handoff(',1)[0]
    after=content.split('\ndef _trusted_runner(',1)[1]
    old=(ROOT/'tests/coordination/control_plane/worker_runtime/test_cf10_batch_d_canonical_ipc_preclaim_bridge_v0_1.py').read_text()
    assert 'def run_once(' in after
    assert 'def assert_cutover_ready()' in before
    assert 'launch_after_owner_claim(' in after
    assert 'def review_guarded_ipc_handoff(' in content
    assert 'runtime_cutover.review(' in content
    assert 'def test_live_switch_fixture_releases_guard_even_after_exception' in old
