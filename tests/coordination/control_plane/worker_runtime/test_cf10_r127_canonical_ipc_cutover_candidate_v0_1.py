from __future__ import annotations
import hashlib
from pathlib import Path
import pytest

from scripts.coordination.control_plane.worker_runtime import cf10_r127_canonical_ipc_cutover_candidate_v0_1 as m


def sample():
    invocation={'schema_version':'forprint_worker_runtime_launch_invocation_v0_1','attempt_id':'cf10-a055','decision_id':'decision-001','task_id':'test-001','work_front_id':'cf10','argv_sha256':'a'*64,'invocation_sha256':'b'*64,'workspace_repo':'/run/fixture/workspace/repo'}
    binding={'schema_version':'forprint_cf10_r123_source_capsule_invocation_crosswalk_v0_1',
             'state':'SOURCE_CROSSWALK_CANDIDATE_NON_AUTHORIZING','capsule_id':m.CAPSULE_ID,
             'workspace_repo':invocation['workspace_repo'],'argv_sha256':invocation['argv_sha256'],
             'attempt_id':invocation['attempt_id'],'decision_id':invocation['decision_id'],
             'task_id':invocation['task_id'],'work_front_id':invocation['work_front_id'],
             'binding_sha256':'c'*64,'authority':{'worker_authorized':False,'release_receipt_attested':False}}
    lease={'schema':'cf10_r125_disposable_lease_v0_1','attempt_id':'cf10-a055','epoch':'epoch-5','source_head':'d'*40,'capsule_id':m.CAPSULE_ID,'revoked':False}
    kwargs={'invocation':invocation,'binding_record':binding,'verified_binding':dict(binding),
            'verified_lease':lease,'source_head':'d'*40,'epoch':'epoch-5',
            'socket_path':Path('/run/forprint-cf10-r125-abcdef0123456789/mcp.sock'),
            'proxy_path':Path('/srv/software_development/forprint-project/forprint_system_blueprint/'+m.REL_PROXY),
            'interpreter':Path('/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python'),
            'live_cutover_enabled':False}
    return kwargs


def test_exact_read_only_candidate():
    c=m.render_review_candidate(**sample())
    assert c['state']=='SOURCE_REVIEW_NOT_ADMITTED'
    assert all(value is False for value in c['authority'].values())
    assert c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['tools']==['run_repo_head']
    assert c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['args'][3:5]==['--attempt-id','cf10-a055']
    assert c['candidate_sha256']==hashlib.sha256(m.canonical({k:v for k,v in c.items() if k!='candidate_sha256'})).hexdigest()


def test_repeated_candidate_deterministic():
    assert m.render_review_candidate(**sample()) == m.render_review_candidate(**sample())


def test_live_cutover_flag_always_denied():
    k=sample();k['live_cutover_enabled']=True
    with pytest.raises(m.CandidateHold,match='LIVE_CUTOVER_MUST_REMAIN_OFF'):m.render_review_candidate(**k)

@pytest.mark.parametrize('mutation',[
    lambda k:k['invocation'].__setitem__('attempt_id','cf10-other'),
    lambda k:k['binding_record'].__setitem__('capsule_id','other'),
    lambda k:k['binding_record']['authority'].__setitem__('worker_authorized',True),
    lambda k:k['verified_binding'].__setitem__('binding_sha256','f'*64),
    lambda k:k['verified_lease'].__setitem__('revoked',True),
    lambda k:k['verified_lease'].__setitem__('source_head','e'*40),
    lambda k:k.__setitem__('source_head','e'*40),
    lambda k:k.__setitem__('socket_path',Path('/tmp/evil.sock')),
    lambda k:k.__setitem__('epoch','../../bad'),
    lambda k:k.__setitem__('proxy_path',Path('/tmp/worker.py')),
    lambda k:k.__setitem__('interpreter',Path('/bin/bash')),
    lambda k:k['invocation'].__setitem__('invocation_sha256','notsha'),
])
def test_false_or_drift_candidate_rejected(mutation):
    k=sample();mutation(k)
    with pytest.raises(m.CandidateHold):m.render_review_candidate(**k)


def test_only_one_candidate_script_and_no_runtime_mutation():
    k=sample();r=m.render_review_candidate(**k)
    assert r['candidate_mcp_config']['mcpServers']['ForPrintValidation']['args'][0].endswith(m.REL_PROXY)
    text=Path(m.__file__).read_text()
    assert 'systemd-run' not in text and 'git push' not in text and 'subprocess.Popen(' not in text
    assert 'revoke_lease(' not in text


def test_review_plan_is_not_legacy_r115_argv():
    r=m.render_review_candidate(**sample())
    assert r['authority']['candidate_executable_in_current_R115'] is False
    assert 'R115_R118_NEW_PROXY_PRECLAIM' in r['outstanding']
    assert 'INFLIGHT_CANCELLATION_AND_TERMINAL_FENCE' in r['outstanding']
