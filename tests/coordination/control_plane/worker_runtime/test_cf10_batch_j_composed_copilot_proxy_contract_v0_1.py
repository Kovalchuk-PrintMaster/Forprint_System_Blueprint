"""Canonical contract tests: Batch J is a lab TLS CONNECT tunnel, never live admission."""
from __future__ import annotations
import copy
import hashlib
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_batch_j_composed_copilot_proxy_contract_v0_1 as h

U='forprint-cf10-batchj-'+'b'*16+'.service'
D='/run/'+U.removesuffix('.service')

def plan():return h.plan(unit=U,lab_dir=D,private_file=D+'/fake_credential.txt')

def test_source_check_is_negative_only():
    r=h.source_check()
    assert r['authority'] is False
    assert len(r['open_gates'])==5
    assert 'live' not in r or r.get('live') is False

def test_plan_effective_sandbox_and_gates():
    r=plan(); p=r['properties']
    assert p['User']=='forprint-runner' and p['Group']=='forprint-runner'
    assert p['PrivateNetwork']=='yes'
    assert p['RestrictAddressFamilies']=='AF_UNIX AF_INET AF_INET6'
    assert p['IPAddressDeny']=='any' and p['IPAddressAllow']=='localhost'
    assert p['ProtectSystem']=='strict' and p['ProtectHome']=='yes'
    assert p['InaccessiblePaths']=='/var/lib/forprint-runner '+D+'/fake_credential.txt'
    assert p.get('StateDirectory') is None
    for k in ('live_admission','provider_credentials_used','copilot_inference_executed','worker_claim_consumed',
              'external_network_used','production_broker_used','kernel_terminal_proven'):
        assert r[k] is False
    assert r['copilot_version_only'] is True and r['copilot_proxy_use_proven'] is False
    assert p['ReadWritePaths']==D and p['Environment']=='HOME='+D+'/home'
    assert len(r['open_gates'])==5
    assert r['profile_sha256']==h.digest(p)

def test_one_allowed_tunnel_one_rejected_target():
    yes=h.connect_request(U,h.ALLOW)
    no=h.connect_request(U,h.REJECT)
    assert h.broker_decide(yes,U)=={'status':'ALLOW_FIXTURE_TLS','request_id':h.request_id(U)}
    assert h.broker_decide(no,U)=={'status':'DENY_CONNECT','request_id':h.request_id(U)}
    assert h.expected_https_body().startswith(b'CF10_BATCH_J_PUBLIC')
    assert h.BODY_SHA256==hashlib.sha256(h.expected_https_body()).hexdigest()

@pytest.mark.parametrize('change',[
    {'schema':'foo'}, {'request_id':'0'*24},{'attempt_mode':'PRODUCTION'},
    {'target':'evil.invalid:443'},{'target':'127.0.0.1:443'},
    {'target':'fixture.forprint.invalid:80'}, {'target':'fixture.forprint.invalid:8443'},
    {'target':'FIXTURE.FORPRINT.INVALID:443'},
])
def test_request_drift_denied(change):
    obj=h.connect_request(U,h.ALLOW)|change
    with pytest.raises(h.TransportHold):h.broker_decide(obj,U)

@pytest.mark.parametrize('extra',[
    {'env':{}},{'Authorization':'fake'},{'provider':'copilot'},
    {'headers':{}},{'arguments':[]},
])
def test_widened_request_denied(extra):
    obj=h.connect_request(U,h.ALLOW)|extra
    with pytest.raises(h.TransportHold):h.broker_decide(obj,U)

@pytest.mark.parametrize('bad',[None,[],42,'x',{'schema':True},{'schema':None}])
def test_invalid_shape_denied(bad):
    with pytest.raises((h.TransportHold,ValueError,TypeError)):
        h.broker_decide(bad,U)

@pytest.mark.parametrize('unit',["",'forprint-cf10-batchg-'+'b'*16+'.service',
                             'forprint-cf10-batchj-AAAA.service',
                             'forprint-cf10-batchj-'+'b'*15+'.service',
                             'forprint-cf10-batchj-'+'b'*16+'.service;rm',
                             '/etc/passwd','forprint-cf10-batchj-'+'b'*16+'.timer'])
def test_unit_scope_negative(unit):
    with pytest.raises(h.TransportHold):h.request_id(unit)

@pytest.mark.parametrize('path',[D+'-other',D+'/..', '/tmp/not-durable','/run/wrong'])
def test_lab_path_not_widened(path):
    with pytest.raises(h.TransportHold):h.plan(unit=U,lab_dir=path,private_file=path+'/fake_credential.txt')

@pytest.mark.parametrize('path',[D+'/fake_credential.txt/other',D+'/secrets',
                               '/var/lib/forprint-runner/.config',None])
def test_credential_path_not_widened(path):
    with pytest.raises(h.TransportHold):h.plan(unit=U,lab_dir=D,private_file=path)

@pytest.mark.parametrize('policy',[None,{},'127.0.0.1/32',
    '127.0.0.0/7 ::1/128','127.0.0.0/8',
    '127.0.0.0/8 ::1/128 2001:db8::/32','0.0.0.0/0 ::/0'])
def test_effective_allowlist_not_broad(policy):
    assert h.effective_network_set(policy)!={'127.0.0.0/8','::1/128'}

@pytest.mark.parametrize('raw',['localhost','127.0.0.0/8 ::1/128','::1/128 127.0.0.0/8'])
def test_effective_allowlist_exact(raw):
    assert h.effective_network_set(raw)=={'127.0.0.0/8','::1/128'}

def test_source_does_not_modify_live_r030():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    assert launcher.LIVE_CUTOVER_ENABLED is False
