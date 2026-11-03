"""R043 tests: derived S3 review auto-export only; no live Worker or authority."""
from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile
import pytest
from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as c
from scripts.coordination.control_plane import cf10_s3_worker_workflow_v0_1 as s3

TASK='cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATT='cf10-u180j-a050'

def projection(state='AWAITING_OPERATOR_REVIEW'):
    return {'derived_non_authoritative':True,'state':state,'next_boundary':'OPERATOR_REVIEW'}

def preview(**kwargs):
    return {'governed_state':'AWAITING_OPERATOR_REVIEW','classification':'OPERATOR_GATE',
            'evidence_validated_by_s1':True,'next_action':'EXPLICIT_OPERATOR_REVIEW',
            'worker_result_status':'PASS','changed_paths':[],
            'operator_decision':'NOT_RECORDED','s1_result_classification':'AWAITING_OPERATOR_REVIEW', **kwargs}

def s1_report():
    return {'attempt_id':ATT,'task_prompt_id':TASK,'blockers':[],
            'result_classification':'AWAITING_OPERATOR_REVIEW',
            'worker_result_status':'PASS','result_return_status':'PASS',
            'terminal_ledger':{'result_state':'SUCCEEDED','binding':{'sha256':'a'*64,'path':'fixture'}},
            'operator_decision_state':'NOT_RECORDED',
            'governed_state':'AWAITING_OPERATOR_REVIEW', 'next_boundary':'OPERATOR_REVIEW',
            'declared_changed_paths':[], 'validation_suites':[], 'evidence':{},
            'next_action':{'type':'OPERATOR_REVIEW',
                           'required_authority':'EXPLICIT_HUMAN_OPERATOR_DECISION'}}

def fake_report(*args):
    return {'run_action':'S1_REPORT_WRITTEN_IN_TMP','report_artifact':'/tmp/derived-review.zip'}

def test_terminal_review_exports_once_without_authority():
    auth=Mock(); post=Mock(side_effect=fake_report); preflight=Mock(); mutate=Mock()
    outcome=c.transition(Path('/isolated'),Path('/runtime'),TASK,ATT,'a'*40,
        state_fn=lambda *a:projection(),auth_fn=auth,
        postworker_inspect_fn=lambda *a:preview(),postworker_report_fn=post,
        preflight_fn=preflight,postworker_advance_fn=mutate)
    assert outcome['state']=='AWAITING_OPERATOR_REVIEW'
    assert outcome['report_artifact']=='/tmp/derived-review.zip'
    assert outcome['changed_paths']==[]
    assert outcome['automatic_accept'] is False
    assert outcome['automatic_publication'] is False
    assert outcome['completed']==[]
    post.assert_called_once()
    auth.assert_not_called();preflight.assert_not_called();mutate.assert_not_called()

@pytest.mark.parametrize('invalid', [
    {'classification':'BLOCKED','evidence_validated_by_s1':True},
    {'classification':'OPERATOR_GATE','evidence_validated_by_s1':False},
    {'classification':'READY_FOR_BOUND_POSTWORKER_ADVANCE','evidence_validated_by_s1':True},
])
def test_terminal_invalid_evidence_never_exports(invalid):
    base=preview();base.update(invalid)
    writer=Mock();auth=Mock()
    r=c.transition(Path('/isolated'),Path('/runtime'),TASK,ATT,'a'*40,
        state_fn=lambda *a:projection(),postworker_inspect_fn=lambda *a:base,
        postworker_report_fn=writer,auth_fn=auth)
    assert r['state']=='BLOCKED' and r['blocker']=='S1_REVIEW_EVIDENCE_NOT_VALIDATED'
    writer.assert_not_called();auth.assert_not_called()

def test_review_status_drift_no_export():
    writer=Mock();auth=Mock()
    r=c.transition(Path('/isolated'),Path('/runtime'),TASK,ATT,'a'*40,
        state_fn=lambda *a:projection(),postworker_inspect_fn=lambda *a:preview(governed_state='BROKEN'),
        postworker_report_fn=writer,auth_fn=auth)
    assert r['blocker']=='S1_REVIEW_STATUS_DRIFT'
    writer.assert_not_called();auth.assert_not_called()

def test_report_writer_failure_is_blocked_without_retry():
    calls=[];auth=Mock()
    def crash(*a):
        calls.append(1);raise OSError('disk-fault')
    r=c.transition(Path('/isolated'),Path('/runtime'),TASK,ATT,'a'*40,
        state_fn=lambda *a:projection(),postworker_inspect_fn=lambda *a:preview(),
        postworker_report_fn=crash,auth_fn=auth)
    assert r['state']=='BLOCKED' and r['blocker']=='S1_REVIEW_REPORT_FAILED:OSError'
    assert r['next_action']=='REVIEW_S1_EVIDENCE_NO_WORKER_RETRY'
    assert len(calls)==1;auth.assert_not_called()

def test_invalid_s3_result_not_accepted():
    r=c.transition(Path('/isolated'),Path('/runtime'),TASK,ATT,'a'*40,
        state_fn=lambda *a:projection(),postworker_inspect_fn=lambda *a:preview(),
        postworker_report_fn=lambda *a:{'report_artifact':'/tmp/forged.zip'})
    assert r['blocker']=='S1_REVIEW_REPORT_NOT_PROVEN'

def test_review_source_uses_s3_not_direct_advance():
    import inspect
    src=inspect.getsource(c._postworker_report)
    assert 's3.report_attempt(' in src
    assert 'advance_cycle(' not in src

def test_s3_export_idempotent_by_content(tmp_path,monkeypatch):
    (tmp_path/'tmp').mkdir()
    report=s1_report()
    def use_writer(root,runtime,task,attempt,proof,output,*,write_fn=None,**kw):
        return {'run_action':'S1_REPORT_WRITTEN_IN_TMP',
                'report_artifact':str(write_fn(root,report,output))}
    monkeypatch.setattr(s3,'report_attempt',use_writer)
    first=c._postworker_report(tmp_path,tmp_path/'runtime',TASK,ATT)
    again=c._postworker_report(tmp_path,tmp_path/'runtime',TASK,ATT)
    assert first==again
    archive=Path(first['report_artifact'])
    assert archive.is_file()
    with ZipFile(archive) as z:
        doc=json.loads(z.read('operator_report.json'))
    assert doc['attempt_id']==ATT and doc['task_prompt_id']==TASK
    assert len(list((tmp_path/'tmp/cf10_operator_console/s1_reviews').glob('*.zip')))==1
    report['next_action']={'type':'CHANGED_EVIDENCE','required_authority':'EXPLICIT_HUMAN_OPERATOR_DECISION'}
    changed=c._postworker_report(tmp_path,tmp_path/'runtime',TASK,ATT)
    assert changed['report_artifact']!=first['report_artifact']


def test_cached_report_corruption_blocks_not_rewrites(tmp_path,monkeypatch):
    (tmp_path/'tmp').mkdir()
    report=s1_report()
    def use_writer(root,runtime,task,attempt,proof,output,*,write_fn=None,**kw):
        return {'run_action':'S1_REPORT_WRITTEN_IN_TMP',
                'report_artifact':str(write_fn(root,report,output))}
    monkeypatch.setattr(s3,'report_attempt',use_writer)
    first=c._postworker_report(tmp_path,tmp_path/'runtime',TASK,ATT)
    archive=Path(first['report_artifact'])
    archive.write_bytes(b'corrupt zip')
    with pytest.raises(c.ConsoleBlocked, match='S1_CACHED_ARCHIVE_UNVERIFIABLE'):
        c._postworker_report(tmp_path,tmp_path/'runtime',TASK,ATT)


def test_review_report_does_not_depend_on_tmp_for_authority():
    # Read-only code contract: every emitted preview explicitly marks itself
    # derived, S3 keeps the canonical validation / review separate.
    result=c.transition(Path('/isolated'),Path('/runtime'),TASK,ATT,'a'*40,
        state_fn=lambda *a:projection(),postworker_inspect_fn=lambda *a:preview(),
        postworker_report_fn=fake_report)
    assert result['report_role']=='DERIVED_NON_AUTHORIZING'
    assert result['automatic_promotion'] is False
    assert result['automatic_accept'] is False
