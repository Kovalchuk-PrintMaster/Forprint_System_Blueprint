"""AG joins real dispatcher decision to AE physical result via fresh nonce.

No production auth/claim/launch is tested or implied. All tests use a fake
Dispatcher API implementation solely to exercise exact call/hold behavior.
"""
from __future__ import annotations
import copy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ag_bound_dispatcher_worker_v0_1 as ag

A='cf10-u180j-a123456789';F='9e17680295581ff07bc2ae913a96fdc4cf86c88be60078ba03d1866ab3d9792d'
U='forprint-cf10-batchad-0123456789abcdef.service';I='a'*32;D='b'*64;SALT='1'*64

def preview():
 return {'state':'CANONICAL_API_DECISION_PREVIEW_ONLY','task_id':ag.TASK,'work_id':'u180j',
  'preview_identity_sha256':'c'*64,'exact_generated_ack_checked':True,
  'ack_from_independent_assistant':False,'claim_consumed':False,'canonical_worker_released':False}

def physical(nonce=None):
 from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
 if nonce is None:nonce=ag.disposable_nonce(preview()['preview_identity_sha256'],SALT)
 result_digest=child.worker_digest(ag.TASK,nonce)
 return {'schema':'cf10_ae_physical_delegated_leaf_v0_1',
  'status':'PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL',
  'stage':'STOPPED_AND_TERMINAL_VERIFIED','unit':U,'gates_open':list(ag.GATES),
  'nonce_binding':{'disposable_external_nonce_used':True,'nonce_sha256':hashlib.sha256(nonce.encode()).hexdigest()},
  'worker_pid':4201,'anchor':{'pid':4200,'invocation_id':I},
  'canonical_binding':{'task_id':ag.TASK,'production_dispatch_performed':False,'worker_claim_consumed':False},
  'runtime_cleanup':'PASS_DISPOSABLE_ONLY','result':{'synthetic_result_digest':result_digest,
      'result_verified_by_root':True,'model_inference_executed':False,
      'worker_result_accepted':False,'canonical_result_ledger_written':False},
  'kernel':{'observation':'PINNED_DELEGATED_LEAF_FD','samples':['1','0'],
     'transition':'1_TO_0','parent_anchor_populated':'1','invocation_id':I,
     'unit':U,'leaf_name':'cf10-actual-worker'},
  'poststop':{'active':'inactive','main_pid':'0','result':'success'},
  'terminal':{'unit':U,'canonical_task_binding':ag.TASK,'worker_result_verified_by_root':True,
    'kernel_leaf_transition':'1_TO_0','parent_anchor_held_until_kernel_zero':True,
    'retained_systemd':True,'stopped_readback':True,
    'production_claim_consumed':False,'production_ledger_written':False,
    'production_result_acceptance':False,'canonical_dispatcher_release':False,
    'provider_inference':False,'provider_credentials':False,'external_egress':False,
    'held_invocation_id':I,'result_sha256':result_digest,'worker_pid':4201,'anchor_pid':4200}}

def test_positive_join_but_not_live_authority():
 x=ag.join(preview=preview(),physical=physical(),salt_hex=SALT)
 assert x['status'].startswith('PASS_')
 assert x['nonce_binding_verified_against_child_digest'] is True
 assert x['canonical_api_prepare_ack_validate_explicit_preview'] is True
 assert x['real_kernel_leaf_1_to_0'] is True
 assert x['canonical_production_dispatch_performed'] is False
 assert x['canonical_worker_claim_consumed'] is False
 assert x['provider_credentials_used'] is False
 assert x['gates_open']==ag.GATES
 assert x['join_sha256']==ag.digest({k:v for k,v in x.items() if k!='join_sha256'})

@pytest.mark.parametrize('key,value',[
 ('state','LIVE'),('task_id','other'),('claim_consumed',True),
 ('canonical_worker_released',True),('exact_generated_ack_checked',False),
 ('ack_from_independent_assistant',True),
])
def test_preview_authority_drift_denied(key,value):
 a=preview();a[key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=a,physical=physical(),salt_hex=SALT)

@pytest.mark.parametrize('key,value',[
 ('schema','other'),('status','PASS_FAKE'),('stage','EXECUTING'),
 ('unit','worker.service'),('gates_open',[]),('runtime_cleanup','HOLD'),
])
def test_physical_top_level_drift_denied(key,value):
 p=physical();p[key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=preview(),physical=p,salt_hex=SALT)

@pytest.mark.parametrize('key,value',[
 ('unit','other.service'),('canonical_task_binding','other'),('worker_result_verified_by_root',False),
 ('kernel_leaf_transition','SYSTEMCTL_ONLY'),('parent_anchor_held_until_kernel_zero',False),
 ('retained_systemd',False),('stopped_readback',False),('production_claim_consumed',True),
 ('production_ledger_written',True),('production_result_acceptance',True),
 ('canonical_dispatcher_release',True),('provider_inference',True),
 ('provider_credentials',True),('external_egress',True),
 ('held_invocation_id','c'*32),('result_sha256','c'*64),
 ('worker_pid',99),('anchor_pid',99),
])
def test_terminal_tampering_denied(key,value):
 p=physical();p['terminal'][key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=preview(),physical=p,salt_hex=SALT)

@pytest.mark.parametrize('key,value',[
 ('observation','PID_EXIT'),('samples',['0']),('samples',['1','1','0']),
 ('transition','FAILED'),('parent_anchor_populated','0'),('invocation_id','c'*32),
 ('unit','forprint-cf10-batchad-'+'1'*16+'.service'),('leaf_name','other'),
])
def test_kernel_tampering_denied(key,value):
 p=physical();p['kernel'][key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=preview(),physical=p,salt_hex=SALT)

@pytest.mark.parametrize('key,value',[
 ('active','active'),('main_pid','42'),('result','exit-code'),
])
def test_poststop_tampering_denied(key,value):
 p=physical();p['poststop'][key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=preview(),physical=p,salt_hex=SALT)

@pytest.mark.parametrize('key,value',[
 ('task_id','other'),('worker_claim_consumed',True),('production_dispatch_performed',True),
])
def test_canonical_binding_tampering_denied(key,value):
 p=physical();p['canonical_binding'][key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=preview(),physical=p,salt_hex=SALT)


def fake_training(events):
 ctx='c'*64
 def prepare(**kw):
  events.append('PREPARE')
  assert kw['blueprint_ai_trial_ready'] is False
  assert kw['ledger_store_override'].is_dir()
  assert kw['attempt_id']==A
  return {'state':'AWAITING_ASSISTANT_ACK','assistant_ack_validated':False,
   'task_prompt_id':ag.TASK,'worker_id':'worker-01','attempt_id':A,
   'authority':dict.fromkeys(('execution_authority_granted','dispatch_authority_granted',
     'worker_dispatch_performed','external_dispatch_allowed','release_allowed','push_allowed','merge_allowed'),False)}
 def ack(**kw):
  events.append('BUILD_ACK')
  assert kw['prepared_execution']['state']=='AWAITING_ASSISTANT_ACK'
  return {'launch_mode':'TASK_EXECUTION','authority_ack':{'authority_widening':False},
          'freshness_ack':{'attempt_id':A,'source_state_fingerprint':F,'worker_id':'worker-01'}}
 def validate(**kw):
  events.append('VALIDATE_ACK')
  assert kw['assistant_ack']==kw['expected_ack']
  b=dict(kw['prepared_execution']);b['state']='READY_FOR_EXPLICIT_DISPATCH';b['assistant_ack_validated']=True
  b['governed_worker_context_sha256']=ctx
  return b
 def authorize(**kw):
  events.append('EXPLICIT_PREVIEW')
  assert kw['ledger_store_override'].is_dir()
  assert kw['workspace_repo'].is_dir()
  assert kw['runtime_provider']=='github_copilot_cli' and kw['runtime_model']=='auto'
  assert kw['ready_execution']['state']=='READY_FOR_EXPLICIT_DISPATCH'
  return {'decision':'ALLOW_EXACT_CF10_TRAINING_WORKER_LAUNCH',
          'decision_id':ag.digest({'attempt_id':A,'worker_id':'worker-01','task_prompt_id':ag.TASK,
                     'source_state_fingerprint':F,'runtime_provider':'github_copilot_cli',
                     'runtime_model':'auto','governed_worker_context_sha256':ctx}),'assistant_ack_validated':True,'explicit_dispatch_decision_recorded':True,
          'worker_process_launch_allowed':True,
          'binding':{'attempt_id':A,'worker_id':'worker-01','task_prompt_id':ag.TASK,
                     'source_state_fingerprint':F,'runtime_provider':'github_copilot_cli',
                     'runtime_model':'auto','governed_worker_context_sha256':ctx},
          **dict.fromkeys(('external_dispatch_allowed','release_allowed','push_allowed',
              'merge_allowed','foreign_repository_write_allowed','automatic_accept_allowed',
              'grants_broad_dispatch_authority'),False)}
 return SimpleNamespace(prepare_training_pre_dispatch=prepare,build_training_canonical_ack=ack,
         validate_training_assistant_ack=validate,authorize_training_explicit_dispatch=authorize)

def test_actual_sequence_to_physical_after_preview(tmp_path):
 events=[]
 training=fake_training(events)
 def ae_run(*,disposable_nonce):events.append('PHYSICAL_AE');return physical(disposable_nonce)
 data=ag.run_with_apis(training=training,ae=SimpleNamespace(run_once=ae_run),
      root=tmp_path,scratch=tmp_path,attempt_id=A)
 assert events==['PREPARE','BUILD_ACK','VALIDATE_ACK','EXPLICIT_PREVIEW','PHYSICAL_AE']
 assert data['joined']['real_kernel_leaf_1_to_0'] is True
 assert data['preview']['ack_from_independent_assistant'] is False

@pytest.mark.parametrize('phase',['PREPARE','BUILD_ACK','VALIDATE_ACK','EXPLICIT_PREVIEW'])
def test_failure_never_runs_worker(tmp_path,phase):
 events=[];training=fake_training(events)
 attr={'PREPARE':'prepare_training_pre_dispatch','BUILD_ACK':'build_training_canonical_ack',
       'VALIDATE_ACK':'validate_training_assistant_ack','EXPLICIT_PREVIEW':'authorize_training_explicit_dispatch'}[phase]
 def broken(**kw):events.append(phase);raise ValueError('expected fake failure')
 setattr(training,attr,broken)
 def ae_run(**kw):raise AssertionError('AE MUST NOT RUN')
 with pytest.raises(ag.AGHold,match=phase):
  ag.run_with_apis(training=training,ae=SimpleNamespace(run_once=ae_run),
    root=tmp_path,scratch=tmp_path,attempt_id=A)

@pytest.mark.parametrize('id',[
 'cf10-u180j-a001','cf10-u180j-a099','cf10-u180j-a12345678',
 'cf10-u180j-a123456789;rm','/run/cf10-u180j-a123456789',
])
def test_no_unsafe_attempt_id(tmp_path,id):
 with pytest.raises(ag.AGHold):
  ag.run_with_apis(training=SimpleNamespace(),ae=SimpleNamespace(),
     root=tmp_path,scratch=tmp_path,attempt_id=id)


@pytest.mark.parametrize('key,value', [('result_verified_by_root',False),('synthetic_result_digest','0')])
def test_result_verification_not_inferred_from_other_facts(key,value):
 p=physical();p['result'][key]=value
 with pytest.raises(ag.AGHold):ag.join(preview=preview(),physical=p,salt_hex=SALT)


@pytest.mark.parametrize('key,value',[
 ('disposable_external_nonce_used',False),('nonce_sha256','0'*64),
 ('nonce_sha256',None),('disposable_external_nonce_used',1),
])
def test_ae_nonce_identity_mismatch_hold(key,value):
    r=physical();r['nonce_binding'][key]=value
    with pytest.raises(ag.AGHold,match='NONCE'):
        ag.join(preview=preview(),physical=r,salt_hex=SALT)

@pytest.mark.parametrize('salt',[None,'x'*64,'1'*63,'1'*65,1])
def test_nonce_salt_fails_closed(salt):
    with pytest.raises(ag.AGHold):ag.disposable_nonce('c'*64,salt)

def test_distinct_decisions_or_salts_produce_distinct_nonces():
    a=ag.disposable_nonce('c'*64,SALT)
    assert a!=ag.disposable_nonce('d'*64,SALT)
    assert a!=ag.disposable_nonce('c'*64,'2'*64)

def test_valid_physical_from_different_decision_must_not_join():
    other=ag.disposable_nonce('d'*64,SALT)
    with pytest.raises(ag.AGHold,match='NONCE'):
        ag.join(preview=preview(),physical=physical(other),salt_hex=SALT)

def test_old_ae_unbound_physical_must_not_join():
    r=physical();r.pop('nonce_binding')
    with pytest.raises(ag.AGHold,match='NONCE'):
        ag.join(preview=preview(),physical=r,salt_hex=SALT)

def test_forged_result_with_matching_nonce_commitment_rejected():
    r=physical();r['result']['synthetic_result_digest']='f'*64
    r['terminal']['result_sha256']='f'*64
    with pytest.raises(ag.AGHold,match='CHILD_RESULT'):
        ag.join(preview=preview(),physical=r,salt_hex=SALT)

def test_af_false_approval_cannot_widen_by_echo():
    a=preview();a['ack_from_independent_assistant']=True
    with pytest.raises(ag.AGHold):ag.join(preview=a,physical=physical(),salt_hex=SALT)

def test_nonce_override_format_validation_not_secret():
    from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_kernel_rehearsal_v0_1 as ae
    assert ae.disposable_nonce_for_run('a'*64)==('a'*64,True)
    for bad in ('/tmp/token',True,1,'g'*64,'A'*64,'a'*63,'a'*65,{},b'0'*64):
        with pytest.raises(ae.AEHold):ae.disposable_nonce_for_run(bad)
    nonce,extern=ae.disposable_nonce_for_run(None)
    assert len(nonce)==64 and extern is False


def test_dispatcher_decision_digest_recomputed_not_literal():
    events=[];training=fake_training(events)
    record=training.authorize_training_explicit_dispatch(root=None,ready_execution={'state':'READY_FOR_EXPLICIT_DISPATCH'},
      worker_id='worker-01',attempt_id=A,source_state_fingerprint=F,workspace_repo=Path('/tmp'),
      runtime_provider='github_copilot_cli',runtime_model='auto',ledger_store_override=Path('/tmp'))
    assert record['decision_id']==ag.digest(record['binding'])
    record['decision_id']='0'*64
    prepared=training.prepare_training_pre_dispatch(root=None,task_prompt_id=ag.TASK,worker_id='worker-01',
      attempt_id=A,blueprint_ai_trial_ready=False,ledger_store_override=Path('/tmp'))
    ack=training.build_training_canonical_ack(root=None,prepared_execution=prepared,
      source_state_fingerprint=F,worker_id='worker-01',attempt_id=A)
    ready=training.validate_training_assistant_ack(root=None,prepared_execution=prepared,
      assistant_ack=ack,expected_ack=ack)
    with pytest.raises(ag.AGHold,match='DECISION_ID'):
        ag._safe_preview(prepared=prepared,ack=ack,ready=ready,decision=record,
          attempt_id=A,source_fingerprint=F)

@pytest.mark.skipif(os.geteuid()!=0,reason='root-owned disposable AF_UNIX test')
def test_external_nonce_reaches_actual_ae_ipc_worker_under_mock_systemd(tmp_path,monkeypatch):
    """Reuse the already-reviewed AE two-peer socket scenario, but with AG nonce."""
    import importlib.util
    source=Path(__file__).with_name('test_cf10_ae_delegated_kernel_rehearsal_v0_1.py')
    spec=importlib.util.spec_from_file_location('cf10_ag_existing_ae_socket_fixture',source)
    existing=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(existing)
    observed={}
    original=existing.a.run_once
    def injected_once():
        response=original(disposable_nonce=existing.NONCE)
        observed.update(response)
        return response
    monkeypatch.setattr(existing.a,'run_once',injected_once)
    existing.test_full_two_process_protocol_with_mock_systemd_and_cgroup(tmp_path,monkeypatch)
    assert observed['nonce_binding']=={
        'disposable_external_nonce_used':True,
        'nonce_sha256':hashlib.sha256(existing.NONCE.encode('ascii')).hexdigest()}
    from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
    assert observed['result']['synthetic_result_digest']==child.worker_digest(ag.TASK,existing.NONCE)
