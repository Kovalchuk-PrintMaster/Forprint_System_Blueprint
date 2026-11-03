"""r054 proof-gated postworker bridge: synthetic fixtures, no real Worker."""
from __future__ import annotations
import inspect
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from scripts.coordination.control_plane import cf10_r054_pilot_postworker_gate_v0_1 as gate
from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
from scripts.coordination.control_plane import cf10_s3_worker_workflow_v0_1 as s3

TASK = gate.TASK
ATTEMPT = 'cf10-u180j-a999'
HEAD = 'a'*40


def claim():
    return {'schema_version':'cf10_owner_pam_attempt_claim_v0_1',
            'status':'CONSUMED_BEFORE_SPAWN_NO_RETRY',
            'worker_id':'worker-01','task_prompt_id':TASK,'attempt_id':ATTEMPT,
            'source_head':HEAD,'authority_is_password_and_operator_policy':True,
            'automatic_retry':False,'time_utc':'2026-11-03T00:00:00+00:00'}


def test_requirements_never_grant_launch(capsys):
    assert gate.main(['--mode','requirements']) == 0
    report=json.loads(capsys.readouterr().out)
    assert report['production_cutover'] is False
    assert report['worker_launched'] is False
    assert report['canonical_advance_only'] is True


def test_empty_or_wrong_scope_does_not_advance(monkeypatch):
    run=Mock(side_effect=AssertionError('unexpected advance'))
    monkeypatch.setitem(sys.modules,'scripts.coordination.control_plane.governed_worker_cycle',SimpleNamespace(advance_cycle=run))
    for task, attempt in [('',ATTEMPT),(TASK,''),('wrong-task',ATTEMPT),(TASK,'cf10-u180j-a001/../../')]:
        assert gate.inspect(root=Path('/nope'),runtime=Path('/nope'),task=task,attempt=attempt)['status'].startswith('BLOCKED_')
        with pytest.raises(gate.PilotPostworkerBlocked):
            gate.advance(root=Path('/nope'),runtime=Path('/nope'),task=task,attempt=attempt)
    run.assert_not_called()


def test_root_claim_missing_rejected(monkeypatch):
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:os.open('/dev/null',os.O_RDONLY))
    with pytest.raises(gate.PilotPostworkerBlocked,match='CLAIM_UNAVAILABLE'):
        gate._consumed_owner_claim(task=TASK,attempt=ATTEMPT,head=HEAD)


@pytest.mark.parametrize('change',[
    {'status':'READY'}, {'worker_id':'worker-02'}, {'attempt_id':'cf10-u180j-a998'},
    {'task_prompt_id':'other-task'}, {'source_head':'b'*40},
    {'automatic_retry':True}, {'authority_is_password_and_operator_policy':False},
    {'extra':'not-authorized'}, {'time_utc':''}, {'schema_version':'fake'},
])
def test_claim_spoofing_blocked(tmp_path,monkeypatch,change):
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    key=__import__('hashlib').sha256(('worker-01\0'+ATTEMPT).encode()).hexdigest()
    p=tmp_path/('owner_attempt_'+key+'.json')
    raw=claim();raw.update(change)
    p.write_text(json.dumps(raw)+'\n');p.chmod(0o600)
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:os.open(tmp_path,os.O_RDONLY|os.O_DIRECTORY))
    if os.geteuid()==0:
        with pytest.raises(gate.PilotPostworkerBlocked):
            gate._consumed_owner_claim(task=TASK,attempt=ATTEMPT,head=HEAD)
    else:
        # A user-owned 0600 document is *not* a root-owned receipt.
        with pytest.raises(gate.PilotPostworkerBlocked):
            gate._consumed_owner_claim(task=TASK,attempt=ATTEMPT,head=HEAD)


def test_claim_success_is_only_a_boundary_fixture(tmp_path,monkeypatch):
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    key=__import__('hashlib').sha256(('worker-01\0'+ATTEMPT).encode()).hexdigest()
    p=tmp_path/('owner_attempt_'+key+'.json')
    p.write_text(json.dumps(claim())+'\n');p.chmod(0o600)
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:os.open(tmp_path,os.O_RDONLY|os.O_DIRECTORY))
    if os.geteuid()!=0:
        with pytest.raises(gate.PilotPostworkerBlocked):gate._consumed_owner_claim(task=TASK,attempt=ATTEMPT,head=HEAD)
    else:
        gate._consumed_owner_claim(task=TASK,attempt=ATTEMPT,head=HEAD)


def test_duplicate_json_keys_rejected():
    with pytest.raises(gate.PilotPostworkerBlocked,match='DUPLICATE'):
        gate._json_no_duplicates(b'{"attempt_id":"x","attempt_id":"y"}')


def test_claim_symlink_rejected(tmp_path,monkeypatch):
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    key=__import__('hashlib').sha256(('worker-01\0'+ATTEMPT).encode()).hexdigest()
    dest=tmp_path/'other.json';dest.write_text(json.dumps(claim()))
    (tmp_path/('owner_attempt_'+key+'.json')).symlink_to(dest)
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:os.open(tmp_path,os.O_RDONLY|os.O_DIRECTORY))
    with pytest.raises(gate.PilotPostworkerBlocked):gate._consumed_owner_claim(task=TASK,attempt=ATTEMPT,head=HEAD)


def test_preflight_never_spawns_or_issues_receipt():
    code=inspect.getsource(gate.inspect)
    for forbidden in ('owner._owner_claim(', 'authenticate_operator(', 'launch_once(', 'systemd-run', 'advance_cycle('):
        assert forbidden not in code


def test_advance_calls_only_canonical_cycle_after_full_readiness(monkeypatch):
    monkeypatch.setattr(gate,'inspect',lambda **kw:{'status':'EXACT_PILOT_POSTWORKER_READY_NON_AUTHORIZING'})
    fn=Mock(return_value={'state':'AWAITING_OPERATOR_REVIEW'})
    monkeypatch.setitem(sys.modules,'scripts.coordination.control_plane.governed_worker_cycle',SimpleNamespace(advance_cycle=fn))
    result=gate.advance(root=gate.PROJECT,runtime=gate.RUNTIME,task=TASK,attempt=ATTEMPT)
    assert result['automatic_accept'] is False and result['automatic_publication'] is False
    fn.assert_called_once_with(root=gate.PROJECT,runtime_root=gate.RUNTIME,task_prompt_id=TASK,attempt_id=ATTEMPT,worker_id='worker-01')


def test_canonical_cycle_blocked_result_never_reported_as_success(monkeypatch):
    monkeypatch.setattr(gate,'inspect',lambda **kw:{'status':'EXACT_PILOT_POSTWORKER_READY_NON_AUTHORIZING'})
    monkeypatch.setitem(sys.modules,'scripts.coordination.control_plane.governed_worker_cycle',
                        SimpleNamespace(advance_cycle=lambda **kw:{'state':'BLOCKED','reason':'FINALIZER_DENIED'}))
    with pytest.raises(gate.PilotPostworkerBlocked,match='NOT_TERMINAL_OPERATOR_REVIEW'):
        gate.advance(root=gate.PROJECT,runtime=gate.RUNTIME,task=TASK,attempt=ATTEMPT)


def test_missing_confirm_never_advances(monkeypatch,capsys):
    fn=Mock(side_effect=AssertionError('unexpected mutation'))
    monkeypatch.setattr(gate,'advance',fn)
    rc=gate.main(['--mode','advance','--task',TASK,'--attempt',ATTEMPT])
    assert rc==2 and 'CONFIRM_REQUIRED' in capsys.readouterr().out
    fn.assert_not_called()


def test_s3_selects_scoped_make_only_after_gate(monkeypatch):
    calls=[]
    monkeypatch.setattr(gate,'ready',lambda **kw:True)
    monkeypatch.setattr(s3.subprocess,'run',lambda args,**kw:(calls.append(args) or SimpleNamespace(returncode=0,stdout='',stderr='')))
    result=s3._advance_via_existing_make(gate.PROJECT,gate.RUNTIME,TASK,ATTEMPT,'python3')
    assert 'cf10-s01-pilot-postworker-advance' in calls[0]
    assert result['delegated_to']=='cf10-s01-pilot-postworker-advance'


def test_s3_old_make_unchanged_when_no_root_pilot(monkeypatch,tmp_path):
    calls=[]
    monkeypatch.setattr(s3.subprocess,'run',lambda args,**kw:(calls.append(args) or SimpleNamespace(returncode=0,stdout='',stderr='')))
    result=s3._advance_via_existing_make(tmp_path,tmp_path,TASK,ATTEMPT,'python3')
    assert 'governed-worker-cycle-advance' in calls[0]
    assert result['delegated_to']=='governed-worker-cycle-advance'


def test_console_selects_make_only_when_real_pilot_ready(monkeypatch):
    # Verify actual source ordering, without PAM or invoking a Make subprocess.
    code=inspect.getsource(console.transition)
    assert 'pilot.ready(root=root, runtime=runtime, task=task, attempt=attempt)' in code
    assert 'cf10-s01-pilot-postworker-preflight' in code
    assert 'postworker_advance_fn(root, runtime, task, attempt)' in code


def test_legacy_make_quarantine_remains_literal():
    make=(Path(__file__).resolve().parents[3]/'Makefile').read_text()
    assert 'cf10-s01-runtime-launch-preflight:\n\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2' in make
    for target in ('governed-worker-cycle-launch','governed-worker-cycle-advance','governed-worker-cycle-reconcile-result-return'):
        assert target+': cf10-s01-runtime-launch-preflight' in make
    assert 'cf10-s01-pilot-postworker-advance:' in make
    assert '--mode advance' in make


def test_current_machine_blocks_pilot_postworker_readonly():
    assert gate.inspect(root=Path('/definitely-not-canonical'),runtime=gate.RUNTIME,task=TASK,attempt=ATTEMPT)['status']=='BLOCKED_PILOT_POSTWORKER'
