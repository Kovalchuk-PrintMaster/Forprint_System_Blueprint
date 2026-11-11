"""Y: fail-closed first-worker planning, no launch or auth.
Tests do not fetch remote resources or read real tokens.
"""
import copy
import json
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_critical_path_v0_1 as y


def fresh():return copy.deepcopy(y.fixture())

def test_source_check_is_review_only():
    r=y.source_check()
    assert r['all_gates_open'] is True and len(r['gates'])==5
    assert r['owner_authority_granted'] is False
    assert r['worker_launched'] is False and r['terminal_ledger_written'] is False
    assert r['automatic_retry'] is False

def test_stable_digest_and_sequence():
    assert y.plan(**fresh())==y.plan(**fresh())
    r=y.plan(**fresh())
    assert r['review_sha256']==y.digest({k:v for k,v in r.items() if k!='review_sha256'})
    assert r['required_sequence'][0].startswith('RECONCILE')
    assert 'NEXT_WORKER' in r['required_sequence'][-1]

def test_external_handle_is_not_auth_proof():
    d=fresh();d['credential']['source']='ROOT_EXTERNAL_HANDLE_REVIEW_ONLY';d['credential']['root_owns_material']=True
    r=y.plan(**d)
    assert r['credential_boundary']['root_only_file_metadata_seen'] is True
    assert r['credential_boundary']['provider_auth_proven'] is False

@pytest.mark.parametrize('key,value',[
 ('provider','other_ai'),('binary_sha256','0'*64),('cli_offline_executed',False),
 ('cli_offline_executed',1),('model_response_attested',True),('model_response_attested',0),
])
def test_provider_mutations_hold(key,value):
    d=fresh();d['identity'][key]=value
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('key,value',[
 ('material_read',True),('passed_to_cli_env',True),('passed_to_child_tools',True),
 ('credential_exchange_attested',True),('group_or_world_access',True),
 ('root_owns_material',True),('source','ENV_TOKEN'),('source','COPILOT_HOME'),
 ('material_read',1),('passed_to_cli_env',None),
])
def test_credential_widening_holds(key,value):
    d=fresh();d['credential'][key]=value
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('key,value',[
 ('transport','PRODUCTION'),('real_provider_hosts',['api.github.com:443']),
 ('root_upstream_enabled',True),('live_provider_tls_proven',True),
 ('provider_network_auth_attested',True),('direct_worker_ipv4_ipv6_blocked',False),
 ('direct_worker_ipv4_ipv6_blocked',1),
])
def test_egress_widening_holds(key,value):
    d=fresh();d['egress'][key]=value
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('key,value',[
 ('r115_frozen',False),('r134_review_only',False),('r140_mcp_only',False),
 ('canonical_worker_dispatched',True),('claim_consumed',True),
 ('live_cutover_enabled',True),('claim_consumed',0),
])
def test_dispatcher_widening_holds(key,value):
    d=fresh();d['dispatcher'][key]=value
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('key,value',[
 ('lab_kernel_1_to_0',False),('real_worker_kernel_1_to_0',True),
 ('durable_terminal_ledger',True),('independent_result_review',True),
 ('lab_kernel_1_to_0',1),
])
def test_terminal_widening_holds(key,value):
    d=fresh();d['terminal'][key]=value
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('obj,key',[
 ('identity','token'),('credential','token'),('egress','authorization'),
 ('dispatcher','password'),('terminal','headers'),
])
def test_secret_field_injection_denied(obj,key):
    d=fresh();d[obj][key]='any-value'
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('value',[None,'x'*40,'X'*40,'../evil','a'*64,''])
def test_invalid_source_head_holds(value):
    d=fresh();d['source_head']=value
    with pytest.raises(y.AdmissionHold):y.plan(**d)

def test_no_credential_fields_in_result():
    result=y.plan(**fresh());raw=json.dumps(result)
    for forbidden in ('github_pat_secret_value','ghp_secret_value','authorization_header','credential_path'):
        assert forbidden not in raw.lower()

@pytest.mark.parametrize('section',["identity","credential","egress","dispatcher","terminal"])
def test_added_unknown_key_denied(section):
    d=fresh();d[section]['new_field']=True
    with pytest.raises(y.AdmissionHold):y.plan(**d)

@pytest.mark.parametrize('section',["identity","credential","egress","dispatcher","terminal"])
def test_missing_field_denied(section):
    d=fresh();d[section].pop(next(iter(d[section])))
    with pytest.raises(y.AdmissionHold):y.plan(**d)
