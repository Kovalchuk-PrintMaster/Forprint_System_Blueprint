"""Batch K: source R030 preclaim review + disposable sandbox provenance digest.

Fixtures are independent of provider authentication. No live worker is started.
"""
from __future__ import annotations
from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_batch_k_dispatcher_runtime_join_v0_1 as k
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
from scripts.coordination.control_plane.worker_runtime import cf10_r115_preclaim_executable_profile_v0_1 as r115
HERE=Path(__file__).resolve().parent

def _scenario():
    source=HERE/'test_cf10_batch_d_canonical_ipc_preclaim_bridge_v0_1.py'
    spec=importlib.util.spec_from_file_location('cf10_k_existing_d_fixture',source)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    inv,c,_=mod.scenario();s,p=mod.bound(inv,c);route=mod.route()
    return inv,c,s,p,route

def _frozen():
    inv,c,s,p,route=_scenario()
    return k.review(spec=s,plan=p,invocation=inv,candidate=c,
                    reviewer=route.review_guarded_ipc_handoff)

def _lab(p):
    return {'status':'PASS_COMPOSED_COPILOT_VERSION_AND_HTTPS_TLS_SANDBOX',
       'preclaim_review_sha256':p['report_sha256'],
       'host_peercred_cgroup_verified':True,'effective_private_netns':True,
       'effective_ip_deny_all':True,'effective_ip_allow_localhost_only':True,
       'tls_over_unix_verified':True,'unauthorized_connect_denied':True,
       'copilot_offline_version_verified':True,'stop_readback_proven':True,
       'kernel_1_to_0_proven':False,'worker_claim_consumed':False,
       'copilot_inference_executed':False,'copilot_proxy_use_proven':False,
       'provider_credentials_used':False,'production_broker_used':False,
       'external_network_used':False,'peer_uid':996,'peer_gid':992,
       'unit':'forprint-cf10-batchk-'+'a'*16+'.service',
       'cgroup':'/system.slice/forprint-cf10-batchk-'+'a'*16+'.service',
       'copilot_version_metadata':{'result_status':'PASS_OFFLINE_VERSION',
          'pinned_argv':'VERSION_ONLY','copilot_proxy_use_proven':False},
       'isolation':{'direct_external_ipv4':{'denied':True},
           'direct_external_ipv6':{'denied':True},'fake_credential':{'denied':True}}}

def test_positive_existing_canonical_r030_review():
    p=_frozen();assert p['status']==k.STATUS
    assert p['gates_open']==['G1','G2','G3','G4','G5']
    assert p['lab_only'] and p['live_authority'] is False
    assert p['canonical_unit'].startswith('forprint-cf10-worker-')
    assert p['report_sha256'] == k._sha({q:v for q,v in p.items() if q!='report_sha256'})

def test_positive_join_never_authorizes():
    p=_frozen();r=k.attest(preclaim=p,lab=_lab(p))
    assert r['status']=='PASS_FIXTURE_PRECLAIM_SHA_JOINED_TO_ONE_SANDBOX'
    assert r['same_production_attempt'] is False
    assert r['kernel_terminal_proven'] is False
    assert r['worker_started'] is False

@pytest.mark.parametrize('field,value',[('report_sha256','0'*64),('lab_only',False),
    ('live_authority',True),('gates_open',[]),('status','READY'),('claim_consumed',True)])
def test_preclaim_tamper_denied(field,value):
    p=_frozen();p[field]=value
    with pytest.raises(k.JoinHold):k.attest(preclaim=p,lab=_lab(_frozen()))

@pytest.mark.parametrize('field,value',[('preclaim_review_sha256','0'*64),
   ('host_peercred_cgroup_verified',False),('effective_private_netns',False),
   ('effective_ip_deny_all',False),('tls_over_unix_verified',False),
   ('unauthorized_connect_denied',False),('stop_readback_proven',False),
   ('kernel_1_to_0_proven',True),('worker_claim_consumed',True),
   ('copilot_inference_executed',True),('peer_uid',0),('peer_gid',0),
   ('unit','forprint-cf10-worker-'+'a'*24+'.service'),
   ('copilot_proxy_use_proven',True)])
def test_lab_tamper_denied(field,value):
    p=_frozen();b=_lab(p);b[field]=value
    with pytest.raises(k.JoinHold):k.attest(preclaim=p,lab=b)

def test_r030_source_only_live_gate_stays_false():
    assert k.source_check()['no_claim'] is True
    assert k.backend.LIVE_CUTOVER_ENABLED is False

def test_composed_client_has_no_model_command():
    path=Path(__file__).resolve().parents[4]/'scripts/coordination/control_plane/worker_runtime/cf10_batch_k_rehearsal_child_v0_1.py'
    s=path.read_text()
    assert "[PINNED_COPILOT,'--version']" in s
    assert "'preclaim_review_sha256':review_sha" in s
    assert 'R030.run_once(' not in s

def test_wrong_r030_state_denied():
    inv,c,s,p,route=_scenario()
    def spoof(**kwargs):
        d=route.review_guarded_ipc_handoff(**kwargs);d['g1_g5_closed']=True;return d
    with pytest.raises(k.JoinHold):k.review(spec=s,plan=p,invocation=inv,candidate=c,reviewer=spoof)
