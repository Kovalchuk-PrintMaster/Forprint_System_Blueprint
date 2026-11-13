"""Synthetic isolated fixture tests; never run on live server state."""
from pathlib import Path
import json, subprocess, sys
import yaml
import pytest

from scripts.coordination.control_plane import cf10_attempt_operator_report_v0_2 as m

TASK='cf10-planning-projection-cursor-sync-audit-v0-1'
ATT='cf10-u180j-a047'


def put(p,data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data,sort_keys=False))

@pytest.fixture
def example(tmp_path):
    root=tmp_path/'forprint_system_blueprint';root.mkdir()
    subprocess.run(['git','init','-q',str(root)],check=True)
    subprocess.run(['git','-C',str(root),'commit','--allow-empty','-m','synthetic','-q'],check=True,
                   env={**__import__('os').environ,'GIT_AUTHOR_NAME':'Test','GIT_AUTHOR_EMAIL':'t@example.com','GIT_COMMITTER_NAME':'Test','GIT_COMMITTER_EMAIL':'t@example.com'})
    runtime=tmp_path/'runtime';base=runtime/'forprint_system_blueprint'/'worker-01'/ATT
    put(base/'result/worker_result.yaml',{'attempt_id':ATT,'status':'PASS','changed_paths':[],'unresolved_findings':[],
        'validation_evidence':[{'kind':'validation_suite','suite_id':'blueprint-continuity-planning','outcome':'PASS','result':'36 passed'}]})
    put(base/'evidence/governed_worker_cycle_result_return_v0_1.yaml',{'attempt_id':ATT,'result':'PASS','validation_passed':True,'blocked':False,'result_path':str(base/'result/worker_result.yaml')})
    put(base/'evidence/governed_worker_cycle_worker_process_result_v0_1.yaml',{'attempt_id':ATT,'process':{'return_code':0}})
    put(base/'manifest.yaml',{'attempt_id':ATT})
    put(base/'input/governed_worker_cycle_origin_handoff_manifest_v0_1.yaml',{'attempt_id':ATT})
    led=root/'coordination/continuity/execution_attempts'
    put(led/(ATT+'__start.yaml'),{'attempt_id':ATT,'attempt_stage':'STARTED','result_state':'PENDING','validator_outcome':'NOT_RUN'})
    put(led/(ATT+'__finished.yaml'),{'attempt_id':ATT,'attempt_stage':'FINISHED','result_state':'SUCCEEDED','validator_outcome':'PASS','work_front_id':'wf-cf10-planning-projection-cursor-sync-audit-v0-1'})
    def provider(*args):return {'state':'AWAITING_OPERATOR_REVIEW','next_boundary':'OPERATOR_REVIEW','derived_non_authoritative':True}
    return root,runtime,base,provider


def collect(e):
    root,runtime,_,provider=e
    return m.collect(root,runtime,TASK,ATT,status_provider=provider)


def test_a047_zero_delta_happy_path(example):
    r=collect(example)
    assert r['result_classification']=='AWAITING_OPERATOR_REVIEW'
    assert r['operator_decision_state']=='NOT_RECORDED'
    assert r['blockers']==[]
    assert len(r['attempt_ledgers'])==2
    assert r['next_action']['required_authority']=='EXPLICIT_HUMAN_OPERATOR_DECISION'
    assert r['automatic_accept'] is False
    assert r['validation_evidence_provenance']=='WORKER_REPORTED_NOT_REEXECUTED_BY_THIS_REPORT'


def test_missing_worker_result_is_blocked(example):
    (example[2]/'result/worker_result.yaml').unlink()
    r=collect(example)
    assert r['result_classification']=='BLOCKED'
    assert 'WORKER_RESULT_MISSING' in r['blockers']


def test_duplicate_terminal_is_blocked(example):
    root=example[0]
    put(root/'coordination/continuity/execution_attempts'/(ATT+'__more.yaml'),{'attempt_id':ATT,'attempt_stage':'FINISHED','result_state':'SUCCEEDED','validator_outcome':'PASS'})
    r=collect(example)
    assert 'TERMINAL_LEDGER_COUNT=2: expected exactly 1' in r['blockers']


def test_failed_validation_suite_is_blocked(example):
    file=example[2]/'result/worker_result.yaml';data=yaml.safe_load(file.read_text());data['validation_evidence'][0]['outcome']='FAIL';put(file,data)
    assert 'VALIDATION_SUITE_NOT_PASS' in collect(example)['blockers']


def test_conflicting_operator_decisions_are_blocked(example):
    root=example[0];d=root/'coordination/continuity/worker_result_decisions'
    put(d/'one.yaml',{'attempt_id':ATT,'decision':'ACCEPT','decision_id':'a'})
    put(d/'two.yaml',{'attempt_id':ATT,'decision':'RETURN','decision_id':'b'})
    assert 'CONFLICTING_OPERATOR_DECISIONS' in collect(example)['blockers']


def test_report_deterministic_and_bounded_tmp_output(example):
    root=example[0];r=collect(example)
    assert json.dumps(r,sort_keys=True)==json.dumps(collect(example),sort_keys=True)
    z=m.write_preview(root,r,root/'tmp'/'report-1')
    assert z.is_file()
    assert (root/'tmp'/'report-1'/'operator_report.yaml').is_file()
    with pytest.raises((FileExistsError,ValueError)):
        m.write_preview(root,r,root/'tmp'/'report-1')
    with pytest.raises(ValueError):
        m.write_preview(root,r,root/'coordination'/'danger')


def test_process_failure_blocks_and_never_recommends_review(example):
    file=example[2]/'evidence/governed_worker_cycle_worker_process_result_v0_1.yaml'
    put(file, {'attempt_id': ATT, 'process': {'return_code': 1}})
    r=collect(example)
    assert 'WORKER_PROCESS_NOT_SUCCESSFUL' in r['blockers']
    assert r['result_classification']=='BLOCKED'
    assert r['next_action']['type']=='INVESTIGATE_EVIDENCE'

def test_cross_attempt_result_return_path_rejected(example):
    file=example[2]/'evidence/governed_worker_cycle_result_return_v0_1.yaml'
    put(file, {'attempt_id':ATT,'result':'PASS','validation_passed':True,'blocked':False,
               'result_path': '/somewhere/other_attempt/result/worker_result.yaml'})
    r=collect(example)
    assert 'RESULT_RETURN_PATH_MISMATCH' in r['blockers']

def test_missing_suite_fails_closed(example):
    file=example[2]/'result/worker_result.yaml'
    d=yaml.safe_load(file.read_text()); d['validation_evidence']=[];put(file,d)
    assert 'VALIDATION_SUITE_EVIDENCE_MISSING' in collect(example)['blockers']

def test_projection_must_be_marked_non_authoritative(example):
    root,runtime,base,_=example
    def provider(*args): return {'state':'AWAITING_OPERATOR_REVIEW',
      'next_boundary':'OPERATOR_REVIEW','derived_non_authoritative':False}
    r=m.collect(root,runtime,TASK,ATT,status_provider=provider)
    assert r['result_classification']=='BLOCKED'
    assert 'STATUS_PROJECTION_AUTHORITY_UNEXPECTED' in r['blockers']

def test_nonzero_worker_unresolved_findings_is_blocked(example):
    file=example[2]/'result/worker_result.yaml'
    d=yaml.safe_load(file.read_text());d['unresolved_findings']=['unreviewed'];put(file,d)
    assert 'WORKER_UNRESOLVED_FINDINGS' in collect(example)['blockers']


def test_report_zip_contains_only_digest_bound_reports_by_default(example):
    import zipfile
    root=example[0]
    p=m.write_preview(root,collect(example),root/'tmp'/'report-fixed')
    with zipfile.ZipFile(p) as z:
        assert sorted(z.namelist())==sorted(['operator_report.json','operator_report.yaml','operator_report.md','SHA256SUMS'])
        for line in z.read('SHA256SUMS').decode().strip().splitlines():
            expected, name=line.split('  ',1)
            assert __import__('hashlib').sha256(z.read(name)).hexdigest()==expected
    assert not (root/'tmp'/'report-fixed'/'reuse_inventory.json').exists()

def test_repeat_report_byte_for_byte_determinism(example):
    import zipfile
    root=example[0]
    report=collect(example)
    a=m.write_preview(root,report,root/'tmp'/'run1')
    b=m.write_preview(root,report,root/'tmp'/'run2')
    assert a.read_bytes()==b.read_bytes()
