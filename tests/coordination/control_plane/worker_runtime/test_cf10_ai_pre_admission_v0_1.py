"""First live pre-admission is observational, auth- and token-free, fail closed."""
from __future__ import annotations
import copy
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ai_pre_admission_contract_v0_1 as c
from scripts.coordination.control_plane.worker_runtime import cf10_ai_root_copilot_survey_v0_1 as s


def arguments():
    probe={h:{'host':h,'path':'/_ping','state':'PASS_TLS_200','http_status':200,
               'tls_certificate_verified':True,'response_bytes':8} for h in c.ENDPOINTS}
    cli={'pinned_sha256':c.BINARY_SHA,'binary_verified_by_r115':True,'help_exit_code':0,
         'help_flag_matches':dict.fromkeys(c.CLI_FLAGS,True),'offline_no_auto_update':True,
         'credential_env_passed':False,'provider_inference':False}
    auth={'source':'ROOT_EXTERNAL_HANDLE_REVIEW_ONLY','root_owns_material':True,
          'group_or_world_access':False,'material_read':False,
          'passed_to_cli_env':False,'passed_to_child_tools':False,
          'credential_exchange_attested':False,'metadata_status':'ROOT_METADATA_ONLY'}
    canonical=dict.fromkeys(('live_cutover_enabled','canonical_claim_consumed','production_ledger_written',
                             'independent_owner_ack','production_dispatcher_authorized'),False)
    return dict(source_head='a'*40,network=probe,cli=cli,credential=auth,canonical=canonical)


def test_all_green_network_metadata_still_keeps_gates_open():
    d=c.plan(**arguments())
    assert d['status']=='PASS_COMPLETED_OBSERVATIONAL_PRE_ADMISSION_ONLY'
    assert d['root_tls_ping_pass_count']==2
    assert d['gates_open']==['G1','G2','G3','G4','G5']
    assert d['live_worker_authorized'] is False
    assert d['provider_inference_executed'] is False
    assert d['external_provider_request_executed'] is False
    assert d['g1_real_worker_egress_attested'] is False
    assert d['g2_authenticated_nonexposure_attested'] is False
    assert d['first_inference_candidate']['request_executed'] is False
    out=dict(d);v=out.pop('report_sha256')
    assert v==c.digest(out)


def test_missing_pings_are_not_fake_pass():
    a=arguments()
    a['network'][c.ENDPOINTS[0]].update(state='HOLD_NETWORK',http_status=None,
                  tls_certificate_verified=False,response_bytes=0)
    p=c.plan(**a)
    assert p['root_tls_ping_pass_count']==1
    assert 'ROOT_DIRECT_TLS_PING_PARTIAL_OR_BLOCKED' in p['blockers']
    assert p['gates_open']==list(c.GATES)


@pytest.mark.parametrize('mutate',[
    lambda x:x['network'][c.ENDPOINTS[0]].update(host='evil.example'),
    lambda x:x['network'][c.ENDPOINTS[0]].update(path='/token'),
    lambda x:x['network'][c.ENDPOINTS[0]].update(state='PASS_TLS_200',tls_certificate_verified=False),
    lambda x:x['network'][c.ENDPOINTS[0]].update(state='PASS_TLS_200',http_status=True),
    lambda x:x['network'][c.ENDPOINTS[0]].update(response_bytes=10000),
    lambda x:x['network'][c.ENDPOINTS[0]].update(access_token='secret'),
    lambda x:x['network'].update({'github.com':x['network'][c.ENDPOINTS[0]]}),
    lambda x:x['cli'].update(pinned_sha256='b'*64),
    lambda x:x['cli'].update(provider_inference=True),
    lambda x:x['cli'].update(credential_env_passed=True),
    lambda x:x['cli']['help_flag_matches'].update({'--allow-all':True}),
    lambda x:x['credential'].update(material_read=True),
    lambda x:x['credential'].update(credential_exchange_attested=True),
    lambda x:x['credential'].update(group_or_world_access=True),
    lambda x:x['credential'].update(token='do not echo'),
    lambda x:x['credential'].update(metadata_status='PROVIDER_AUTHENTICATED'),
    lambda x:x['canonical'].update(canonical_claim_consumed=True),
    lambda x:x['canonical'].update(live_cutover_enabled=1),
    lambda x:x.update(source_head='not-a-sha'),
])
def test_rejects_authority_escalation_and_untrusted_values(mutate):
    a=arguments();mutate(a)
    with pytest.raises(c.AdmissionHold):c.plan(**a)


def test_unconfigured_fixture_uses_no_auth_or_inference():
    row=c.source_check()
    assert row['gates_open']==c.GATES
    assert row['credential_metadata']['metadata_status']=='UNCONFIGURED'
    assert row['production_claim_consumed'] is False
    assert row['provider_token_read'] is False


def test_fixed_prompt_and_no_tools_policy():
    assert c.PROMPT.startswith('Reply with exactly FORPRINT_CF10_')
    assert c.DENY_TOOLS==('read','write','shell','url','memory')
    assert 'Bearer' not in c.PROMPT
    assert '--allow-all' not in repr(c.DENY_TOOLS)


@pytest.mark.parametrize('host',['example.com','github.com','api.githubcopilot.com.attacker.com',
                                 '127.0.0.1','copilot-proxy.githubusercontent.com:443',None])
def test_tls_probe_rejects_other_host_without_network(host):
    with pytest.raises(s.SurveyHold):s.https_ping(host,factory=lambda *a,**kw:None)


class FakeResponse:
    def __init__(self,code=200,body=b'pong'):
        self.status=code;self.body=body
    def read(self,n):return self.body[:n]

class FakeConnection:
    def __init__(self,host,port,timeout,context):
        assert host in c.ENDPOINTS and port==443 and timeout==7
        assert context.verify_mode != 0 and context.check_hostname
        self.request_args=None;self.closed=False
        self.response=FakeResponse()
    def request(self,*args,**kw):self.request_args=(args,kw)
    def getresponse(self):return self.response
    def close(self):self.closed=True


def test_root_https_public_ping_fixed_get_exact_path():
    connections=[]
    def factory(*args,**kwargs):
        x=FakeConnection(*args,**kwargs);connections.append(x);return x
    row=s.https_ping(c.ENDPOINTS[0],factory=factory)
    assert row['state']=='PASS_TLS_200'
    assert row['tls_certificate_verified'] is True
    assert connections[0].request_args[0][:2]==('GET','/_ping')
    assert 'Authorization' not in connections[0].request_args[1]['headers']
    assert connections[0].closed


@pytest.mark.parametrize('status', [301,302,307,308,401,403,500])
def test_no_redirect_and_no_false_tls_success(status):
    class Connection(FakeConnection):
        def getresponse(self):return FakeResponse(status,b'not success')
    row=s.https_ping(c.ENDPOINTS[0],factory=Connection)
    assert row['state']=='HOLD_HTTP_STATUS' and row['tls_certificate_verified'] is False


def test_huge_response_is_fail_closed():
    class Connection(FakeConnection):
        def getresponse(self):return FakeResponse(200,b'X'*1100)
    row=s.https_ping(c.ENDPOINTS[1],factory=Connection)
    assert row['state']=='HOLD_RESPONSE_SIZE' and row['response_bytes']==1024


@pytest.mark.parametrize('error', [ConnectionError('network'),TimeoutError('timeout'),
                                  OSError('dns')])
def test_root_ping_network_error_no_secret_text(error):
    def fail(*args,**kwargs):raise error
    row=s.https_ping(c.ENDPOINTS[1],factory=fail)
    assert row['state']=='HOLD_NETWORK' and 'error' not in row


def test_root_cli_help_no_secret_environment(monkeypatch):
    import sys, types
    name='scripts.coordination.control_plane.worker_runtime.cf10_r115_preclaim_executable_profile_v0_1'
    fake=types.ModuleType(name)
    fake.COPILOT_PILOT_PATH=s.CLI
    fake.COPILOT_PILOT_SHA256=c.BINARY_SHA
    fake.assert_pinned_binary=lambda:None
    monkeypatch.setitem(sys.modules,name,fake)
    monkeypatch.setenv('GH_TOKEN','FAKE_TEST_SECRET_NEVER_READ')
    observed={}
    def fake_run(argv,**kwargs):
        observed.update(kwargs)
        text=' '.join(c.CLI_FLAGS)
        return SimpleNamespace(returncode=0,stdout=text.encode(),stderr=b'')
    row=s.offline_cli_help(runner=fake_run)
    assert row['binary_verified_by_r115'] is True
    assert row['help_exit_code']==0
    assert all(row['help_flag_matches'].values())
    assert 'GH_TOKEN' not in observed['env']
    assert observed['env']['COPILOT_AUTO_UPDATE']=='false'
    assert observed['env']['COPILOT_OFFLINE']=='true'
    assert observed['stdin'] is not None
    assert observed['timeout']==12


def test_credential_path_cannot_be_redirected():
    with pytest.raises(s.SurveyHold):s.credential_metadata(path=Path('/tmp/credentials'))


def test_credential_absent_is_only_unconfigured(monkeypatch):
    monkeypatch.setattr(s,'HANDLE',Path('/var/lib/forprint-cf10/absent-credential-handle'))
    p=s.credential_metadata()
    assert p['metadata_status']=='UNCONFIGURED'
    assert p['material_read'] is False


def test_metadata_only_is_not_provider_auth(monkeypatch,tmp_path):
    # Test-only direct inspector; actual server uses canonical root-owned O_NOFOLLOW.
    monkeypatch.setattr(s,'HANDLE',tmp_path/'handle')
    (tmp_path/'handle').write_bytes(b'fake-placeholder-no-token')
    row=dict(arguments()['credential']);row.pop('metadata_status')
    res=s.credential_metadata(inspector=lambda *args,**kwargs:row)
    assert res['source']=='ROOT_EXTERNAL_HANDLE_REVIEW_ONLY'
    assert res['credential_exchange_attested'] is False
    assert res['metadata_status']=='ROOT_METADATA_ONLY'
    assert 'handle' not in str(res)


def test_survey_with_injected_probes_still_no_worker(monkeypatch,tmp_path):
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    monkeypatch.setattr(s,'ROOT',tmp_path)
    monkeypatch.setattr(launcher,'LIVE_CUTOVER_ENABLED',False)
    a=arguments()
    result=s.run_survey(probe=lambda host:a['network'][host],help_probe=lambda:a['cli'],
                        metadata=lambda:a['credential'],source_head='a'*40)
    assert result['root_tls_ping_pass_count']==2
    assert result['gates_open']==list(c.GATES)
    assert result['worker_launched'] is False


def test_survey_denies_open_live_flag(monkeypatch,tmp_path):
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launcher
    monkeypatch.setattr(s,'ROOT',tmp_path)
    monkeypatch.setattr(launcher,'LIVE_CUTOVER_ENABLED',True)
    with pytest.raises(s.SurveyHold):s.run_survey(source_head='a'*40)
