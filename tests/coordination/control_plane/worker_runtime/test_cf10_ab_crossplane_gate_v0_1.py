"""AB: exact cross-plane join rejects broad authority, no Worker invocation."""
import copy
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_first_worker_crossplane_gate_v0_1 as gate


def fixture():
 return dict(task={'work_id':'u180j','module':'forprint_system_blueprint','task_prompt_id':gate.TASK,'candidate_only':True},
  review={'all_gates_open':True,'worker_launched':False,'owner_authority_granted':False,'terminal_ledger_written':False,
          'gates':dict.fromkeys(gate.OPEN,'NOT_ATTESTED')},
  lifecycle={'source_only_trace_valid':True,'mode':'SYNTHETIC_ONLY_NON_AUTHORIZING',
   'synthetic_event_count':11,'authority':{
    'live_worker_allowed':False,'claim_consumed':False,'root_release_granted':False,
    'automatic_retry':False,'tool_cancellation_attested':False,'g1_g5_closed':False}},
  kernel_anchor_implemented=True,backend_closed=True)

def test_safe_join_has_zero_live_authority():
 r=gate.check_join(**fixture())
 assert r['gates_open']==gate.OPEN and not r['worker_started'] and not r['owner_claim_consumed']
 assert not r['auth_proven'] and not r['real_upstream_proven'] and not r['real_worker_terminal_proven']
 assert r['report_sha256']==gate.digest({k:v for k,v in r.items() if k!='report_sha256'})

@pytest.mark.parametrize('section,key,value',[
 ('task','work_id','wrong'),('task','module','other'),('task','candidate_only',False),
 ('review','all_gates_open',False),('review','worker_launched',True),
 ('review','owner_authority_granted',True),('review','terminal_ledger_written',True),
 ('review','gates',{'G1':'CLOSED'}),
 ('lifecycle','source_only_trace_valid',False),('lifecycle','synthetic_event_count',10),
 ('lifecycle','mode','LIVE'),('lifecycle','authority',{}),
])
def test_tamper_denied(section,key,value):
 d=fixture();d[section][key]=value
 with pytest.raises(gate.JoinHold):gate.check_join(**d)

@pytest.mark.parametrize('key',('kernel_anchor_implemented','backend_closed'))
def test_no_live_toggle(key):
 d=fixture();d[key]=False
 with pytest.raises(gate.JoinHold):gate.check_join(**d)


def test_non_dict_fail_closed():
 d=fixture();d['task']=None
 with pytest.raises(gate.JoinHold):gate.check_join(**d)
