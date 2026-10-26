"""Isolated S2B tests: no real Blueprint ledger or Worker runtime is mutated."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import pytest
import yaml

SIBLING=Path(__file__).with_name('cf10_zero_delta_operator_review_v0_1.py')
if SIBLING.exists():
    spec=importlib.util.spec_from_file_location('cf10_zero_delta_operator_review_v0_1',SIBLING)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
else:
    from scripts.coordination.control_plane import cf10_zero_delta_operator_review_v0_1 as m


def dump(path,val):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(val),encoding='utf-8')

def setup_demo(tmp_path):
    root=tmp_path/'root'; root.mkdir(); (root/'.git').mkdir(); (root/'tmp').mkdir()
    (root/'coordination/continuity/worker_result_decisions').mkdir(parents=True)
    (root/'coordination/continuity/execution_attempts').mkdir(parents=True)
    (root/'coordination/work_fronts').mkdir(parents=True)
    runtime=tmp_path/'worker-runtime';base=runtime/'forprint_system_blueprint/worker-01/cf10-u180j-a047'
    task='cf10-planning-projection-cursor-sync-audit-v0-1';attempt='cf10-u180j-a047'
    originals={
     'worker_manifest':{'attempt_id':attempt,'source_head':'a'*40,'workspace_repo':str(base/'workspace/repo')},
     'worker_baseline':{'source_head':'a'*40},
     'worker_result':{'attempt_id':attempt,'status':'PASS','changed_paths':[],'unresolved_findings':[], 'handoff_manifest_sha256':'e'*64, 'resume_coordinates':{'attempt_id':attempt}},
     'result_return':{'validation_passed':True,'blocked':False,'result':'PASS','result_path':str(base/'result/worker_result.yaml')},
     'process_result':{'process':{'return_code':0}},
     'origin_handoff':{'schema_version':'test'},
     'terminal_ledger':{'attempt_id':attempt,'work_front_id':'wf-demo','attempt_stage':'FINISHED','result_state':'SUCCEEDED','validator_outcome':'PASS','pack_hash_or_context_hash':'e'*64},
    }
    paths={k:base/v for k,v in m.BINDING_FILES.items()}
    paths['terminal_ledger']=root/f'coordination/continuity/execution_attempts/{attempt}__terminal.yaml'
    for key,p in paths.items():dump(p,originals[key])
    dump(root/'coordination/work_fronts/demo.yaml',{'work_front_id':'wf-demo','scope':['tests/test.py'], 'authority':{'layer':'WORK_FRONT'}})
    native={'attempt_id':attempt,'source_head':'a'*40,'baseline_fingerprint_sha256':'b'*64,'workspace_repo':str(base/'workspace/repo'),
         'changed_paths':[],'post_worker_dirty_paths':['AGENTS.md'],'inherited_dirty_paths':['AGENTS.md'],'worker_delta_exact':True,
         'authority_granted':False,'candidate_promoted':False,'canonical_write_performed':False}
    report={'blockers':[],'attempt_id':attempt,'task_prompt_id':task,'report_role':'DERIVED_NON_AUTHORITATIVE_NOT_OPERATOR_DECISION',
       'worker_result_status':'PASS','result_return_status':'PASS','declared_changed_paths':[],
       'terminal_ledger':{'stage':'FINISHED','result_state':'SUCCEEDED','validator_outcome':'PASS','work_front_id':'wf-demo',
                        'binding':{'sha256':m.sha(paths['terminal_ledger'])}},
       'governed_state':'AWAITING_OPERATOR_REVIEW','next_boundary':'OPERATOR_REVIEW'}
    proof={'schema_version':'cf10_s2_independent_workspace_proof_v0_1','attempt_id':attempt,'task_prompt_id':task,
      'result_role':'DERIVED_READ_ONLY_NON_AUTHORITATIVE_NOT_ACCEPT','source_head':'a'*40,
      'time_scope':'CURRENT_WORKSPACE_AT_PROOF_EXECUTION_NOT_AT_WORKER_EXIT',
      'operator_decision_written':False,'canonical_mutation_performed':False,
      'disposition':{'state':'INDEPENDENT_CURRENT_WORKSPACE_ZERO_DELTA_PASS','blockers':[],
          'independent_current_workspace_zero_delta_proven':True,'historical_end_of_process_snapshot_attested':False,
          'operator_decision_allowed_by_this_tool':False},
      'workspace_repo':str(base/'workspace/repo'),
      'independent_delta':{k:deepcopy(v) for k,v in native.items() if k != 'workspace_repo'},
      'evidence_bindings':{k:{'path':str(p),'sha256':m.sha(p),'bytes':p.stat().st_size} for k,p in paths.items()}}
    pf=root/'tmp/proof.json'; pf.write_text(json.dumps(proof),encoding='utf-8')
    def collect(*args):return report
    def derive(*args):return native
    return root,runtime,pf,task,attempt,proof,paths,report,native,collect,derive

def evalu(v):
    root,runtime,pf,task,attempt,*_=v
    return m.evaluate(root,runtime,pf,task,attempt,collect_fn=v[-2],derive_fn=v[-1])

@pytest.fixture
def demo(tmp_path):return setup_demo(tmp_path)

def test_preview_ready_and_pure(demo):
    root=demo[0]; before=list(root.rglob('*.yaml'))
    x=evalu(demo)
    assert x['status']=='READY_FOR_EXPLICIT_OPERATOR_DECISION'
    assert x['historical_exit_attestation'] is False
    assert x['automatic_accept'] is False
    assert list(root.rglob('*.yaml'))==before

def test_proof_bad_sha_blocks(demo):
    demo[6]['worker_result'].write_text('invalid: content\n')
    with pytest.raises(m.Blocked,match='EVIDENCE_SHA_CHANGED'):evalu(demo)

def test_proof_bad_role_blocks(demo):
    pf=demo[2];p=json.loads(pf.read_text());p['result_role']='AUTHORITY';pf.write_text(json.dumps(p))
    with pytest.raises(m.Blocked,match='PROOF_ROLE'):evalu(demo)

def test_proof_changed_delta_blocks(demo):
    demo[5]['independent_delta']['changed_paths']=['AGENTS.md']
    demo[2].write_text(json.dumps(demo[5]))
    with pytest.raises(m.Blocked,match='LIVE_DELTA_CHANGED:changed_paths'):evalu(demo)

def test_source_symlink_blocks(demo):
    p=demo[6]['result_return'];p.unlink();p.symlink_to(demo[6]['worker_result'])
    with pytest.raises(m.Blocked,match='SOURCE_MISSING_OR_SYMLINK'):evalu(demo)

def test_foreign_proof_path_blocks(demo,tmp_path):
    external=tmp_path/'out.json';external.write_bytes(demo[2].read_bytes())
    v=list(demo);v[2]=external
    with pytest.raises(m.Blocked,match='PROOF_NOT_UNDER_REPO_TMP'):evalu(v)

def test_multiple_finished_ledger_blocks(demo):
    p=demo[0]/'coordination/continuity/execution_attempts/cf10-u180j-a047__other.yaml'
    dump(p,{'attempt_stage':'FINISHED'})
    with pytest.raises(m.Blocked,match='EXPECTED_ONE_FINISHED_LEDGER'):evalu(demo)

def test_work_front_missing_blocks(demo):
    (demo[0]/'coordination/work_fronts/demo.yaml').unlink()
    with pytest.raises(m.Blocked,match='WORK_FRONT_NOT_UNIQUE'):evalu(demo)

def test_report_contradiction_blocks(demo):
    demo[7]['blockers']=['CONTRADICTION']
    with pytest.raises(m.Blocked,match='S1_BLOCKERS'):evalu(demo)

def test_current_delta_changed_blocks(demo):
    demo[8]['changed_paths']=['new.py']
    with pytest.raises(m.Blocked,match='LIVE_DELTA_CHANGED'):evalu(demo)

def test_decide_requires_separate_confirmation(demo):
    x=evalu(demo)
    with pytest.raises(m.Blocked,match='CONFIRMATION_MISMATCH'):
        m.decide(demo[0],x,'ACCEPT','review-20261026','forprint-operator','ACCEPT:bad','CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT')
    assert not list((demo[0]/m.DIR).glob('*'))

def test_decide_requires_temporal_ack(demo):
    x=evalu(demo)
    with pytest.raises(m.Blocked,match='TEMPORAL_LIMIT_ACK_REQUIRED'):
        m.decide(demo[0],x,'ACCEPT','review-20261026','forprint-operator',f'ACCEPT:{x["attempt_id"]}:{x["decision_binding_sha256"][:12]}','')

def test_decision_append_only_and_replay(demo):
    x=evalu(demo);conf=f'ACCEPT:{x["attempt_id"]}:{x["decision_binding_sha256"][:12]}'
    first=m.decide(demo[0],x,'ACCEPT','review-20261026','forprint-operator',conf,'CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT')
    assert first['action']=='APPEND_ONLY_DECISION_WRITTEN'
    p=Path(first['decision_record']); initial=p.read_bytes()
    later=evalu(demo)
    assert later['status']=='EXISTING_OPERATOR_DECISION'
    twice=m.decide(demo[0],later,'ACCEPT','review-20261026','forprint-operator',conf,'CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT')
    assert twice['action']=='IDENTICAL_REPLAY_NO_WRITE' and p.read_bytes()==initial

def test_decision_conflict_blocks(demo):
    x=evalu(demo);conf=f'HOLD:{x["attempt_id"]}:{x["decision_binding_sha256"][:12]}'
    m.decide(demo[0],x,'HOLD','review-20261026','forprint-operator',conf,'CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT')
    x=evalu(demo);conf=f'ACCEPT:{x["attempt_id"]}:{x["decision_binding_sha256"][:12]}'
    with pytest.raises(m.Blocked,match='DECISION_REPLAY_CONFLICT'):
        m.decide(demo[0],x,'ACCEPT','review-20261026','forprint-operator',conf,'CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT')

def test_decision_second_file_cannot_be_created(demo):
    x=evalu(demo);conf=f'RETURN:{x["attempt_id"]}:{x["decision_binding_sha256"][:12]}'
    f=demo[0]/m.DIR/f'{x["attempt_id"]}__zero_delta_operator_decision_v0_1.yaml'
    f.write_text('someone else just created this',encoding='utf-8')
    with pytest.raises(m.Blocked,match='DECISION_FILE_ALREADY_CREATED_CONCURRENTLY'):
        m.decide(demo[0],x,'RETURN','review-20261026','forprint-operator',conf,'CURRENT_WORKSPACE_ONLY_NOT_HISTORICAL_EXIT')


def test_s2a_actual_workspace_contract_split(demo):
    root,runtime,pf,task,attempt,proof,paths,report,native,collect,derive=demo
    assert 'workspace_repo' not in proof['independent_delta']
    assert proof['workspace_repo'] == native['workspace_repo']
    assert evalu(demo)['status'] == 'READY_FOR_EXPLICIT_OPERATOR_DECISION'

def test_workspace_top_level_proof_tampering_blocks(demo):
    pf = demo[2]
    proof = json.loads(pf.read_text())
    proof['workspace_repo'] = '/wrong/workspace'
    pf.write_text(json.dumps(proof))
    with pytest.raises(m.Blocked, match='LIVE_DELTA_CHANGED:workspace_repo'):
        evalu(demo)

def test_live_workspace_rebinding_blocks(demo):
    demo[8]['workspace_repo'] = '/wrong/workspace'
    with pytest.raises(m.Blocked, match='LIVE_DELTA_CHANGED:workspace_repo'):
        evalu(demo)
