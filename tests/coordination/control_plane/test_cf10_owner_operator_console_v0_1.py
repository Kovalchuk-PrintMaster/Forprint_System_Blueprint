from __future__ import annotations
import datetime as dt
import json
import os
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as c

TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATTEMPT = 'cf10-u180j-a049'

def state(name):
    return {'derived_non_authoritative':True,'state':name,'next_boundary':'FAKE_TEST_BOUNDARY'}

def test_invalid_ids_rejected():
    with pytest.raises(c.ConsoleBlocked):c.ids('../escape', ATTEMPT)
    with pytest.raises(c.ConsoleBlocked):c.ids(TASK, '../escape')
    c.ids(TASK,ATTEMPT)

def test_no_selection_fails_closed(tmp_path):
    with pytest.raises(c.ConsoleBlocked,match='NO_SELECTION'):c.resolve_selection(tmp_path,'','')

def test_selection_is_temporary_and_reusable(tmp_path):
    (tmp_path/'tmp').mkdir()
    c.save_selection(tmp_path,TASK,ATTEMPT)
    assert c.resolve_selection(tmp_path,'','')==(TASK,ATTEMPT)
    assert 'NOT_AUTHORITY' in c.selection_path(tmp_path).read_text()
    c.save_selection(tmp_path,TASK,ATTEMPT)

def test_selection_symlink_refused(tmp_path):
    (tmp_path/'tmp').mkdir()
    (tmp_path/'tmp/cf10_operator_console').symlink_to(tmp_path)
    with pytest.raises(c.ConsoleBlocked):c.save_selection(tmp_path,TASK,ATTEMPT)

def test_select_requires_both_ids(tmp_path):
    with pytest.raises(c.ConsoleBlocked,match='TOGETHER'):
        c.resolve_selection(tmp_path,TASK,'')

def test_password_is_never_accepted_when_sudo_is_passwordless():
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0)
    with pytest.raises(c.ConsoleBlocked,match='PASSWORDLESS'):
        c.authenticate_operator(process=runner,geteuid=lambda:0,isatty=lambda fd:True)
    assert len(calls)==1

def test_password_pam_must_succeed():
    calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=1)
    with pytest.raises(c.ConsoleBlocked,match='AUTHENTICATION_FAILED'):
        c.authenticate_operator(process=runner,geteuid=lambda:0,isatty=lambda fd:True)
    assert len(calls)==2

def test_password_pam_interactive_success():
    calls=[]
    def runner(argv,**kwargs):
        calls.append((argv,kwargs))
        return SimpleNamespace(returncode=1 if len(calls)==1 else 0)
    c.authenticate_operator(process=runner,geteuid=lambda:0,isatty=lambda fd:True)
    assert 'sudo' in calls[0][0]
    assert calls[1][0][-2:]==['-k','-v']
    assert 'input' not in calls[1][1]

def test_root_and_tty_required():
    with pytest.raises(c.ConsoleBlocked,match='ROOT'):
        c.authenticate_operator(process=Mock(),geteuid=lambda:1000,isatty=lambda fd:True)
    with pytest.raises(c.ConsoleBlocked,match='TTY'):
        c.authenticate_operator(process=Mock(),geteuid=lambda:0,isatty=lambda fd:False)

def test_failed_pam_refuses_stage():
    def rejected():
        raise c.ConsoleBlocked('OPERATOR_PAM_AUTHENTICATION_FAILED')
    with pytest.raises(c.ConsoleBlocked,match='AUTHENTICATION_FAILED'):
        c.decision('ACK',TASK,ATTEMPT,'a'*40,authenticate=rejected)

def test_operator_positive_calls_auth_once():
    auth=Mock()
    c.decision('ACK',TASK,ATTEMPT,'a'*40,authenticate=auth)
    auth.assert_called_once_with()

def test_pipeline_prepare_then_two_gates_stop_at_launch(tmp_path):
    sequence=iter(['RESOLVE_TASK','AWAITING_ASSISTANT_ACK','READY_FOR_EXPLICIT_DISPATCH','READY_FOR_WORKER_LAUNCH'])
    steps=[];auth=Mock()
    def statusfn(*args):return state(next(sequence))
    def stepfn(*args):steps.append(args[-1])
    result=c.transition(tmp_path,tmp_path,TASK,ATTEMPT,'a'*40,
        state_fn=statusfn,step_fn=stepfn,auth_fn=auth)
    assert result['state']=='READY_FOR_WORKER_LAUNCH'
    assert 'AUTHORITY_MIGRATION' in result['blocker']
    assert steps==['prepare','ack','authorize-dispatch']
    assert auth.call_count==2

def test_resume_at_launch_does_not_touch_worker(tmp_path):
    step=Mock();auth=Mock()
    result=c.transition(tmp_path,tmp_path,TASK,ATTEMPT,'a'*40,
        state_fn=lambda *args:state('READY_FOR_WORKER_LAUNCH'),step_fn=step,
        auth_fn=auth)
    assert result['completed']==[]
    step.assert_not_called();auth.assert_not_called()

def test_partial_prepare_not_retried(tmp_path):
    a=tmp_path/'forprint_system_blueprint'/'worker-01'/ATTEMPT
    a.mkdir(parents=True);(a/'manifest.yaml').write_text('value: old\n')
    step=Mock()
    result=c.transition(tmp_path,tmp_path,TASK,ATTEMPT,'a'*40,state_fn=lambda *args:state('RESOLVE_TASK'),step_fn=step)
    assert result['state']=='BLOCKED'
    assert result['blocker']=='PARTIAL_ATTEMPT_REQUIRES_OPERATOR_REVIEW'
    step.assert_not_called()

def test_unknown_and_blocked_cannot_mutate(tmp_path):
    for name in ['BLOCKED','UNKNOWN','OBSERVE_WORKER','AWAITING_OPERATOR_REVIEW','PUBLISHED']:
        step=Mock()
        result=c.transition(tmp_path,tmp_path,TASK,ATTEMPT,'a'*40,state_fn=lambda *args:state(name),step_fn=step)
        assert result['completed']==[];step.assert_not_called()

def test_no_duplicate_without_state_progress(tmp_path):
    step=Mock()
    result=c.transition(tmp_path,tmp_path,TASK,ATTEMPT,'a'*40,state_fn=lambda *args:state('RESOLVE_TASK'),step_fn=step)
    assert result['blocker']=='NO_PROGRESS_OR_REPEATED_STATE'; assert step.call_count==1

def test_wrong_projection_rejected(tmp_path):
    with pytest.raises(c.ConsoleBlocked,match='UNTRUSTED'):
        c.transition(tmp_path,tmp_path,TASK,ATTEMPT,'a'*40,state_fn=lambda *args:{'state':'RESOLVE_TASK'},step_fn=Mock())

def test_disposable_report_no_secrets(tmp_path):
    (tmp_path/'tmp').mkdir()
    report=c.record(tmp_path,TASK,ATTEMPT,{'state':'BLOCKED','blocker':'TEST'})
    data=json.loads(report.read_text());assert data['password_or_credential_collected'] is False
    assert data['authority_granted_by_report'] is False
    assert (report.stat().st_mode & 0o777)==0o600

def test_cleanup_only_own_old_reports(tmp_path):
    (tmp_path/'tmp').mkdir()
    old=c.record(tmp_path,TASK,ATTEMPT,{'state':'PAUSED'})
    other=old.parent/'do_not_delete.txt';other.write_text('keep')
    oldtime=dt.datetime(2020,1,1,tzinfo=dt.timezone.utc).timestamp()
    os.utime(old,(oldtime,oldtime))
    assert c.cleanup(tmp_path,days=7)==1
    assert other.is_file()

def test_source_guard_rejects_wrong_root(tmp_path):
    with pytest.raises(c.ConsoleBlocked,match='CANONICAL_ROOT_REQUIRED'):
        c.source_guard(tmp_path)

def test_step_dispatch_uses_native_entrypoint(monkeypatch,tmp_path):
    from scripts.coordination.control_plane import governed_worker_cycle as gwc
    called=Mock(return_value={'state':'READY_FOR_WORKER_LAUNCH'})
    monkeypatch.setattr(gwc,'authorize_dispatch',called)
    c._step(tmp_path,tmp_path,TASK,ATTEMPT,'authorize-dispatch')
    assert called.call_args.kwargs['confirm'] is True

def test_never_touch_legacy_make_or_signed_keys():
    assert 'launch' not in [x[0] for x in c.GATES.values()]
    assert 'reconcile-result-return' not in [x[0] for x in c.GATES.values()]
    assert 'cf10_s01_live_pilot_corridor' in c.CRITICAL[2]
