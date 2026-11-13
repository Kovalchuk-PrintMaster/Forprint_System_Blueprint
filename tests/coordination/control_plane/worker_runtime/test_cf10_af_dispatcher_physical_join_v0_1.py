"""AF joins real dispatcher API decision *preview* to AE real physical evidence.

No production auth/claim/launch is tested or implied. All tests use a fake
Dispatcher API implementation solely to exercise exact call/hold behavior.
"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_af_dispatcher_physical_join_v0_1 as af

A='cf10-u180j-a123456789';F='9e17680295581ff07bc2ae913a96fdc4cf86c88be60078ba03d1866ab3d9792d'
U='forprint-cf10-batchad-0123456789abcdef.service';I='a'*32;D='b'*64

def preview():
 return {'state':'CANONICAL_API_DECISION_PREVIEW_ONLY','task_id':af.TASK,'work_id':'u180j',
  'preview_identity_sha256':'c'*64,'exact_generated_ack_checked':True,
  'ack_from_independent_assistant':False,'claim_consumed':False,'canonical_worker_released':False}

def physical():
 return {'schema':'cf10_ae_physical_delegated_leaf_v0_1',
  'status':'PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL',
  'stage':'STOPPED_AND_TERMINAL_VERIFIED','unit':U,'gates_open':list(af.GATES),
  'canonical_binding':{'task_id':af.TASK,'production_dispatch_performed':False,'worker_claim_consumed':False},
  'runtime_cleanup':'PASS_DISPOSABLE_ONLY','result':{'synthetic_result_digest':D,'result_verified_by_root':True},
  'kernel':{'observation':'PINNED_DELEGATED_LEAF_FD','samples':['1','0'],
     'transition':'1_TO_0','parent_anchor_populated':'1','invocation_id':I},
  'poststop':{'active':'inactive','main_pid':'0','result':'success'},
  'terminal':{'unit':U,'canonical_task_binding':af.TASK,'worker_result_verified_by_root':True,
    'kernel_leaf_transition':'1_TO_0','parent_anchor_held_until_kernel_zero':True,
    'retained_systemd':True,'stopped_readback':True,
    'production_claim_consumed':False,'production_ledger_written':False,
    'production_result_acceptance':False,'canonical_dispatcher_release':False,
    'provider_inference':False,'provider_credentials':False,'external_egress':False,
    'held_invocation_id':I,'result_sha256':D}}

def test_positive_join_but_not_live_authority():
 x=af.join(preview=preview(),physical=physical())
 assert x['status'].startswith('PASS_')
 assert x['canonical_api_prepare_ack_validate_explicit_preview'] is True
 assert x['real_kernel_leaf_1_to_0'] is True
 assert x['canonical_production_dispatch_performed'] is False
 assert x['canonical_worker_claim_consumed'] is False
 assert x['provider_credentials_used'] is False
 assert x['gates_open']==af.GATES
 assert x['join_sha256']==af.digest({k:v for k,v in x.items() if k!='join_sha256'})

@pytest.mark.parametrize('key,value',[
 ('state','LIVE'),('task_id','other'),('claim_consumed',True),
 ('canonical_worker_released',True),('exact_generated_ack_checked',False),
 ('ack_from_independent_assistant',True),
])
def test_preview_authority_drift_denied(key,value):
 a=preview();a[key]=value
 with pytest.raises(af.AFHold):af.join(preview=a,physical=physical())

@pytest.mark.parametrize('key,value',[
 ('schema','other'),('status','PASS_FAKE'),('stage','EXECUTING'),
 ('unit','worker.service'),('gates_open',[]),('runtime_cleanup','HOLD'),
])
def test_physical_top_level_drift_denied(key,value):
 p=physical();p[key]=value
 with pytest.raises(af.AFHold):af.join(preview=preview(),physical=p)

@pytest.mark.parametrize('key,value',[
 ('unit','other.service'),('canonical_task_binding','other'),('worker_result_verified_by_root',False),
 ('kernel_leaf_transition','SYSTEMCTL_ONLY'),('parent_anchor_held_until_kernel_zero',False),
 ('retained_systemd',False),('stopped_readback',False),('production_claim_consumed',True),
 ('production_ledger_written',True),('production_result_acceptance',True),
 ('canonical_dispatcher_release',True),('provider_inference',True),
 ('provider_credentials',True),('external_egress',True),
 ('held_invocation_id','c'*32),('result_sha256','c'*64),
])
def test_terminal_tampering_denied(key,value):
 p=physical();p['terminal'][key]=value
 with pytest.raises(af.AFHold):af.join(preview=preview(),physical=p)

@pytest.mark.parametrize('key,value',[
 ('observation','PID_EXIT'),('samples',['0']),('samples',['1','1','0']),
 ('transition','FAILED'),('parent_anchor_populated','0'),('invocation_id','c'*32),
])
def test_kernel_tampering_denied(key,value):
 p=physical();p['kernel'][key]=value
 with pytest.raises(af.AFHold):af.join(preview=preview(),physical=p)

@pytest.mark.parametrize('key,value',[
 ('active','active'),('main_pid','42'),('result','exit-code'),
])
def test_poststop_tampering_denied(key,value):
 p=physical();p['poststop'][key]=value
 with pytest.raises(af.AFHold):af.join(preview=preview(),physical=p)

@pytest.mark.parametrize('key,value',[
 ('task_id','other'),('worker_claim_consumed',True),('production_dispatch_performed',True),
])
def test_canonical_binding_tampering_denied(key,value):
 p=physical();p['canonical_binding'][key]=value
 with pytest.raises(af.AFHold):af.join(preview=preview(),physical=p)


def fake_training(events):
 ctx='c'*64
 def prepare(**kw):
  events.append('PREPARE')
  assert kw['blueprint_ai_trial_ready'] is False
  assert kw['ledger_store_override'].is_dir()
  assert kw['attempt_id']==A
  return {'state':'AWAITING_ASSISTANT_ACK','assistant_ack_validated':False,
   'task_prompt_id':af.TASK,'worker_id':'worker-01','attempt_id':A,
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
          'decision_id':'d'*64,'assistant_ack_validated':True,'explicit_dispatch_decision_recorded':True,
          'worker_process_launch_allowed':True,
          'binding':{'attempt_id':A,'worker_id':'worker-01','task_prompt_id':af.TASK,
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
 def ae_run():events.append('PHYSICAL_AE');return physical()
 data=af.run_with_apis(training=training,ae=SimpleNamespace(run_once=ae_run),
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
 def ae_run():raise AssertionError('AE MUST NOT RUN')
 with pytest.raises(af.AFHold,match=phase):
  af.run_with_apis(training=training,ae=SimpleNamespace(run_once=ae_run),
    root=tmp_path,scratch=tmp_path,attempt_id=A)

@pytest.mark.parametrize('id',[
 'cf10-u180j-a001','cf10-u180j-a099','cf10-u180j-a12345678',
 'cf10-u180j-a123456789;rm','/run/cf10-u180j-a123456789',
])
def test_no_unsafe_attempt_id(tmp_path,id):
 with pytest.raises(af.AFHold):
  af.run_with_apis(training=SimpleNamespace(),ae=SimpleNamespace(),
     root=tmp_path,scratch=tmp_path,attempt_id=id)


@pytest.mark.parametrize('key,value', [('result_verified_by_root',False),('synthetic_result_digest','0')])
def test_result_verification_not_inferred_from_other_facts(key,value):
 p=physical();p['result'][key]=value
 with pytest.raises(af.AFHold):af.join(preview=preview(),physical=p)
