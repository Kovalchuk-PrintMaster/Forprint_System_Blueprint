"""Synthetic S3 governance behavior; no production repos or worker are touched."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from copy import deepcopy
import pytest

# The candidate lives next to its tests inside tmp/. Once installed, the
# source belongs under scripts/ and the tests under tests/. Both layouts are
# intentional and must remain executable.
MODULE = Path(__file__).with_name("cf10_s3_worker_workflow_v0_1.py")
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("s3_candidate", MODULE)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
else:
    from scripts.coordination.control_plane import cf10_s3_worker_workflow_v0_1 as m

TASK = "cf10-planning-projection-cursor-sync-audit-v0-1"
ATT = "cf10-u180j-a047"


def make_status(state, **facts):
    return {"derived_non_authoritative": True, "task_prompt_id": TASK,
            "attempt_id": ATT, "state": state, "next_boundary": "TEST",
            "facts": {"worker_process_finished": False, "worker_result_return_valid": False, **facts},
            "contradictions": []}


def s1(*args):
    return {"blockers": [], "attempt_id": ATT, "task_prompt_id": TASK,
            "worker_result_status": "PASS", "declared_changed_paths": [],
            "operator_decision_state": "NOT_RECORDED", "result_classification": "AWAITING_OPERATOR_REVIEW"}


def overlay(*args):
    return {"review_evidence_validated": True, "attempt_id": ATT, "task_prompt_id": TASK,
            "next_dispatch_authorized": False, "roadmap_lifecycle_closed": False,
            "review_overlay_state": "ZERO_DELTA_OPERATOR_ACCEPTED", "decision": "ACCEPT",
            "next_boundary": "ROADMAP_OPERATOR_PLANNING_REVIEW_NOT_DISPATCH",
            "decision_record_sha256": "1" * 64}


def observe(status, *, proof=None, report_fn=s1, overlay_fn=overlay):
    return m.inspect(Path("/frozen"), Path("/runtime"), TASK, ATT, proof,
                     status_fn=lambda *a: deepcopy(status), report_fn=report_fn, overlay_fn=overlay_fn)


def test_awaiting_review_without_proof_stays_gate():
    r = observe(make_status("AWAITING_OPERATOR_REVIEW"))
    assert r["classification"] == "OPERATOR_GATE"
    assert "PROVIDE_ATTEMPT_BOUND" in r["next_action"]
    assert r["automatic_accept"] is False


def test_accepted_zero_delta_overlays_without_base_mutation():
    r = observe(make_status("AWAITING_OPERATOR_REVIEW"), proof=Path("/tmp/s2a.json"))
    assert r["review_overlay_state"] == "ZERO_DELTA_OPERATOR_ACCEPTED"
    assert r["governed_state"] == "AWAITING_OPERATOR_REVIEW"
    assert r["operator_decision"] == "ACCEPT"
    assert not r["automatic_dispatch"] and not r["automatic_promotion"]


def test_s1_blockers_fail_closed():
    def bad(*args): return {**s1(*args), "blockers": ["tamper"]}
    r = observe(make_status("AWAITING_OPERATOR_REVIEW"), report_fn=bad)
    assert r["classification"] == "BLOCKED"
    assert "tamper" in r["blockers"]


def test_s2c_implied_dispatch_blocked():
    def bad(*args):return {**overlay(*args), "next_dispatch_authorized": True}
    with pytest.raises(m.WorkflowBlocked, match="S2C_AUTHORITY_WIDENED"):
        observe(make_status("AWAITING_OPERATOR_REVIEW"), proof=Path("/tmp/p.json"), overlay_fn=bad)


def test_ready_for_existing_advance_only_when_return_valid():
    r = observe(make_status("VALIDATE_CANDIDATE", worker_process_finished=True,
                            worker_result_return_valid=True))
    assert r["mutating_advance_allowed"] is True
    assert r["classification"] == "READY_FOR_BOUND_POSTWORKER_ADVANCE"


@pytest.mark.parametrize("facts", [
    {"worker_process_finished": False, "worker_result_return_valid": True},
    {"worker_process_finished": True, "worker_result_return_valid": False},
    {"worker_process_finished": True, "worker_result_return_valid": True, "blocked": True},
    {"worker_process_finished": True, "worker_result_return_valid": True, "attempt_terminal_pass": True},
    {"worker_process_finished": True, "worker_result_return_valid": True, "worker_result_return_blocked": True},
])
def test_preconditions_fail_closed(facts):
    r = observe(make_status("FINALIZE_HANDOFF", **facts))
    assert r["classification"] == "BLOCKED"
    assert not r["mutating_advance_allowed"]


@pytest.mark.parametrize("state", ["READY_FOR_WORKER_LAUNCH", "READY_FOR_EXPLICIT_DISPATCH",
                                    "PROMOTE_CANDIDATE", "PUBLISHED", "OBSERVE_WORKER"])
def test_operator_or_observation_states_do_not_launch(state):
    r = observe(make_status(state))
    assert r["mutating_advance_allowed"] is False
    assert r["automatic_dispatch"] is False


def test_contradiction_blocks():
    status=make_status("ATTEMPT_TERMINAL",worker_process_finished=True,worker_result_return_valid=True)
    status["contradictions"]=["no-parent"]
    assert observe(status)["classification"] == "BLOCKED"


def test_invalid_id_blocks():
    with pytest.raises(m.WorkflowBlocked, match="INVALID_IDS"):
        m.inspect(Path('/frozen'),Path('/runtime'), '../bad', ATT,
                  status_fn=lambda *a:make_status("ATTEMPT_TERMINAL"))


def test_non_authoritative_status_required():
    bad = make_status("AWAITING_OPERATOR_REVIEW")
    bad['derived_non_authoritative'] = False
    with pytest.raises(m.WorkflowBlocked,match="NON_AUTHORITATIVE"):
        observe(bad)


def test_run_terminal_already_done_never_advances():
    calls=[]
    r=m.run_one(Path('/frozen'),Path('/runtime'),TASK,ATT,Path('/proof'),"python",
      status_fn=lambda *a: make_status("AWAITING_OPERATOR_REVIEW"),
      report_fn=s1, overlay_fn=overlay,
      advance_fn=lambda *a:calls.append(a))
    assert calls==[]
    assert r['run_action']=='NO_MUTATION_OR_GATE_REACHED'
    assert r['execution_performed'] is False


def test_run_uses_one_bounded_advance_then_stops_at_gate():
    state={'value': 'FINALIZE_HANDOFF'}
    calls=[]
    def stat(*a):return make_status(state['value'],worker_process_finished=True,worker_result_return_valid=True)
    def advance(*a):
        calls.append(a)
        state['value']='AWAITING_OPERATOR_REVIEW'
        return {'delegated_to':'governed-worker-cycle-advance','return_code':0}
    r=m.run_one(Path('/frozen'),Path('/runtime'),TASK,ATT,None,'python',
       status_fn=stat, report_fn=s1, overlay_fn=overlay,advance_fn=advance)
    assert len(calls)==1
    assert r['governed_state']=='AWAITING_OPERATOR_REVIEW'
    assert r['execution_performed'] is True
    assert r['mutating_advance_allowed'] is False


def test_run_does_not_proceed_past_an_unexpected_state():
    state={'value':'FINALIZE_HANDOFF'}
    def stat(*a):return make_status(state['value'],worker_process_finished=True,worker_result_return_valid=True)
    def advance(*a):
        state['value']='READY_FOR_WORKER_LAUNCH'
        return {'return_code':0}
    with pytest.raises(m.WorkflowBlocked,match='ADVANCE_DID_NOT_REACH'):
        m.run_one(Path('/frozen'),Path('/runtime'),TASK,ATT,None,'python',
           status_fn=stat,report_fn=s1,overlay_fn=overlay,advance_fn=advance)


def test_report_requires_terminal_state():
    with pytest.raises(m.WorkflowBlocked,match='REPORT_REQUIRES_VALID_TERMINAL'):
        m.report_attempt(Path('/frozen'),Path('/runtime'),TASK,ATT,None,Path('/tmp/new'),
          status_fn=lambda *a:make_status('OBSERVE_WORKER'),report_fn=s1)


def test_report_reuses_s1_writer(tmp_path):
    p=tmp_path/'out'
    calls=[]
    def writer(*a):
        calls.append(a)
        return p.with_suffix('.zip')
    r=m.report_attempt(Path('/frozen'),Path('/runtime'),TASK,ATT,None,p,
      status_fn=lambda *a:make_status('AWAITING_OPERATOR_REVIEW'),
      report_fn=s1,overlay_fn=overlay,write_fn=writer)
    assert len(calls)==1
    assert r['report_artifact'].endswith('out.zip')


def test_no_subprocess_when_native_advance_mock_rejected():
    state=make_status('ATTEMPT_TERMINAL',worker_process_finished=True,worker_result_return_valid=True)
    with pytest.raises(m.WorkflowBlocked,match='NATIVE_MAKE_REJECTED'):
        m.run_one(Path('/frozen'),Path('/runtime'),TASK,ATT,None,'python',
           status_fn=lambda *a:state,report_fn=s1,
           advance_fn=lambda *a:(_ for _ in ()).throw(m.WorkflowBlocked('NATIVE_MAKE_REJECTED')))


def test_native_advance_calls_existing_make_preflight(monkeypatch, tmp_path):
    from subprocess import CompletedProcess
    captured = []
    def fake_run(args, **kwargs):
        captured.append((args, kwargs))
        return CompletedProcess(args, 0, 'state: AWAITING_OPERATOR_REVIEW\n', '')
    monkeypatch.setattr(m.subprocess, 'run', fake_run)
    result = m._advance_via_existing_make(tmp_path, tmp_path / 'runtime', TASK, ATT, '.venv_blueprint/bin/python')
    assert result['delegated_to'] == 'governed-worker-cycle-advance'
    assert result['return_code'] == 0
    assert len(captured) == 1
    argv, opts = captured[0]
    assert argv[:3] == ['make', '-s', 'governed-worker-cycle-advance']
    assert 'GOVERNED_WORKER_TASK=' + TASK in argv
    assert 'GOVERNED_WORKER_ATTEMPT=' + ATT in argv
    assert 'PYTHON=.venv_blueprint/bin/python' in argv
    assert opts['cwd'] == tmp_path
    assert opts['timeout'] == 1200


def test_native_advance_failed_make_never_returns_success(monkeypatch, tmp_path):
    from subprocess import CompletedProcess
    monkeypatch.setattr(m.subprocess, 'run', lambda args, **kwargs: CompletedProcess(args, 2, '', 'PREFLIGHT_DENIED'))
    with pytest.raises(m.WorkflowBlocked, match='NATIVE_MAKE_ADVANCE_FAILED:rc=2:PREFLIGHT_DENIED'):
        m._advance_via_existing_make(tmp_path, tmp_path / 'runtime', TASK, ATT, '.venv_blueprint/bin/python')
