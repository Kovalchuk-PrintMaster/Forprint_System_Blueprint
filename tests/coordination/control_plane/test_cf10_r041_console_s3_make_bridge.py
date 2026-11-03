"""R041 integration: source-level guards and isolated state-machine checks.

Every test is synthetic; no PAM, production Worker, receipts, git mutation or
systemd are touched. The existing S3 and Make gate remain authoritative.
"""
from __future__ import annotations
import inspect
from pathlib import Path
from unittest.mock import Mock
from types import SimpleNamespace
import subprocess
import pytest

from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as c
from scripts.coordination.control_plane import cf10_s3_worker_workflow_v0_1 as s3

TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATT = 'cf10-u180j-a050'


def projection(state):
    return {'derived_non_authoritative': True, 'state': state,
            'next_boundary': 'BOUNDED_TEST_STATE'}


def ready(state='VALIDATE_CANDIDATE'):
    return {'governed_state':state, 'classification':'READY_FOR_BOUND_POSTWORKER_ADVANCE',
            'next_action':'EXISTING_GOVERNED_MAKE_ADVANCE'}


def cycle(state='VALIDATE_CANDIDATE', **kwargs):
    return c.transition(Path('/isolated'), Path('/no-runtime'), TASK, ATT, 'a'*40,
                        state_fn=kwargs.pop('state_fn', lambda *a: projection(state)),
                        auth_fn=kwargs.pop('auth_fn', Mock()),
                        step_fn=kwargs.pop('step_fn', Mock()),
                        postworker_inspect_fn=kwargs.pop('postworker_inspect_fn', lambda *a: ready(state)),
                        preflight_fn=kwargs.pop('preflight_fn', lambda *a: (False, 'QUARANTINED')),
                        postworker_advance_fn=kwargs.pop('postworker_advance_fn', Mock()),
                        **kwargs)


def test_legacy_direct_advance_is_not_in_operator_step():
    assert "if action == 'advance'" not in inspect.getsource(c._step)
    assert 'advance_cycle(' not in inspect.getsource(c._postworker_advance)
    assert 's3.run_one(' in inspect.getsource(c._postworker_advance)


def test_s3_mutation_uses_make_and_no_direct_python():
    source = inspect.getsource(s3._advance_via_existing_make)
    assert 'governed-worker-cycle-advance' in source
    assert 'subprocess.run' in source
    assert 'advance_cycle(' not in source


def test_r041_make_target_and_existing_quarantine_retained():
    make = (Path(__file__).resolve().parents[3] / 'Makefile').read_text()
    assert 'cf10-r041-console-s3-bridge-check:' in make
    assert 'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight' in make
    assert 'QUARANTINED_NEEDS_INDEPENDENT_REBIND' in make
    assert 'cf10-s01-runtime-launch-preflight:' in make
    assert 'cf10-run:' in make and 'cf10-resume:' in make


@pytest.mark.parametrize('state', sorted(c.POST_WORKER_STATES))
def test_quarantine_blocks_before_pam_and_make(state):
    auth=Mock();advance=Mock();legacy_step=Mock()
    r=cycle(state,auth_fn=auth,postworker_advance_fn=advance,step_fn=legacy_step)
    assert r['state']=='BLOCKED'
    assert r['blocker']=='POSTWORKER_MAKE_PREFLIGHT_DENIED'
    assert r['next_action']=='INDEPENDENT_AUTHORITY_REBIND_REVIEW'
    assert r['completed']==[]
    auth.assert_not_called();advance.assert_not_called();legacy_step.assert_not_called()


@pytest.mark.parametrize('classification', ['BLOCKED', 'WAIT_FOR_WORKER_RESULT', 'OPERATOR_GATE'])
def test_s3_not_ready_is_not_advanced(classification):
    auth=Mock();advance=Mock();gate=Mock()
    r=cycle(postworker_inspect_fn=lambda *a: {'governed_state':'VALIDATE_CANDIDATE',
            'classification':classification,'next_action':'INSPECT_WORKER_RESULT','blockers':['fixture']},
            auth_fn=auth,preflight_fn=gate,postworker_advance_fn=advance)
    assert r['blocker']=='POSTWORKER_NOT_READY'
    assert r['blockers']==['fixture']
    auth.assert_not_called();advance.assert_not_called();gate.assert_not_called()


def test_status_drift_is_blocked_before_asking_password():
    auth=Mock();advance=Mock()
    r=cycle(postworker_inspect_fn=lambda *a: ready('AWAITING_OPERATOR_REVIEW'),
            auth_fn=auth,postworker_advance_fn=advance)
    assert r['blocker']=='POSTWORKER_STATUS_CHANGED_OR_INVALID'
    auth.assert_not_called();advance.assert_not_called()


def test_s3_exception_does_not_grant_launch_or_retry():
    auth=Mock();advance=Mock()
    def fail(*a): raise ValueError('S3_BAD_FIXTURE')
    r=cycle(postworker_inspect_fn=fail,auth_fn=auth,postworker_advance_fn=advance)
    assert r['blocker']=='S3_INSPECTION_FAILED:ValueError'
    assert r['completed']==[]
    auth.assert_not_called();advance.assert_not_called()


def test_read_only_quarantine_probe_calls_exact_make_target(monkeypatch):
    calls=[]
    def fake(args,**kwargs):
        calls.append((args,kwargs))
        return SimpleNamespace(returncode=2,stdout='QUARANTINED_NEEDS_INDEPENDENT_REBIND\n',stderr='')
    monkeypatch.setattr(c.subprocess,'run',fake)
    ok, reason=c._postworker_make_preflight(Path('/isolated'))
    assert ok is False and 'QUARANTINED' in reason
    assert calls[0][0]==['make','-s','cf10-s01-runtime-launch-preflight']
    assert calls[0][1]['cwd']==Path('/isolated')


def test_s3_advance_stub_invoked_once_after_pam_and_gate():
    order=[]
    sequence=iter(['VALIDATE_CANDIDATE','AWAITING_OPERATOR_REVIEW'])
    def authorized(): order.append('PAM')
    def advanced(*a):
        order.append('S3_RUN_ONE')
        return {'execution_performed':True,'governed_state':'AWAITING_OPERATOR_REVIEW',
                'classification':'OPERATOR_GATE'}
    r=cycle(auth_fn=authorized,
       state_fn=lambda *a:projection(next(sequence)),
       preflight_fn=lambda *a:(True,'PASS'),postworker_advance_fn=advanced)
    assert order==['PAM','S3_RUN_ONE']
    assert r['state']=='AWAITING_OPERATOR_REVIEW'
    assert r['completed']==['postworker-advance-via-existing-make']
    assert r['next_action']=='CF10_WORKER_S3_REPORT_AND_EXPLICIT_OPERATOR_REVIEW'


def test_failed_s3_make_has_no_second_attempt():
    called=[]
    def fail(*a):
        called.append(True)
        raise s3.WorkflowBlocked('NATIVE_MAKE_ADVANCE_FAILED:rc=2:QUARANTINED')
    r=cycle(preflight_fn=lambda *a:(True,'PASS'),postworker_advance_fn=fail)
    assert r['blocker']=='POSTWORKER_S3_MAKE_ADVANCE_FAILED:WorkflowBlocked'
    assert r['next_action']=='MANUAL_GATE_REVIEW_NO_AUTO_RETRY'
    assert len(called)==1 and r['completed']==[]


@pytest.mark.parametrize('state', ['FINALIZE_HANDOFF','ATTEMPT_TERMINAL'])
def test_postworker_phase_reuses_s3_not_old_stop_branch(state):
    auth=Mock();r=cycle(state,auth_fn=auth)
    assert r['blocker']=='POSTWORKER_MAKE_PREFLIGHT_DENIED'
    auth.assert_not_called()


def test_race_result_unproven_never_reports_success():
    r=cycle(preflight_fn=lambda *a:(True,'PASS'),
       postworker_advance_fn=lambda *a:{'execution_performed':False,
          'classification':'OPERATOR_GATE','governed_state':'AWAITING_OPERATOR_REVIEW'})
    assert r['blocker']=='POSTWORKER_RESULT_UNPROVEN'
    assert r['completed']==[]


def test_repeated_state_still_blocked_without_retry():
    n={'count':0}
    def auth():n['count']+=1
    r=cycle(preflight_fn=lambda *a:(True,'PASS'),auth_fn=auth,
       postworker_advance_fn=lambda *a:{'execution_performed':True,
          'classification':'OPERATOR_GATE','governed_state':'AWAITING_OPERATOR_REVIEW'})
    assert r['blocker']=='NO_PROGRESS_OR_REPEATED_STATE'
    assert n['count']==1


def test_observe_never_mutates_or_prompts():
    auth=Mock();advance=Mock();gate=Mock()
    r=cycle('OBSERVE_WORKER',auth_fn=auth,postworker_advance_fn=advance,preflight_fn=gate)
    assert r['state']=='OBSERVE_WORKER'
    assert r['completed']==[]
    auth.assert_not_called();advance.assert_not_called();gate.assert_not_called()


def test_report_stop_never_auto_accepts():
    auth=Mock();advance=Mock()
    r=cycle('AWAITING_OPERATOR_REVIEW',auth_fn=auth,postworker_advance_fn=advance)
    assert r['next_action']=='CF10_WORKER_S3_REPORT_AND_EXPLICIT_OPERATOR_REVIEW'
    assert r['completed']==[]
    auth.assert_not_called();advance.assert_not_called()


def test_guarded_source_pins_s3_adapter():
    assert 'scripts/coordination/control_plane/cf10_s3_worker_workflow_v0_1.py' in c.CRITICAL
