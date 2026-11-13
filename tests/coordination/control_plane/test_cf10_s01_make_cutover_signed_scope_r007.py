"""Negative-only signed scope and Make wiring tests; no Writer/claim/spawn."""
import importlib
from pathlib import Path
from unittest.mock import patch
import pytest

mod=importlib.import_module('scripts.coordination.control_plane.cf10_s01_live_pilot_corridor_v0_1')


def good_doc():
    return {'pilot_scope': {
        'worker_id':'worker-01', 'task_prompt_id':'cf10-planning-task85',
        'attempt_id':'cf10-u180j-a048', 'max_active_workers':1, 'max_attempts':1,
        'explicit_operator_dispatch_required':True, 'automatic_retry_allowed':False,
        'automatic_accept_allowed':False, 'route':'GOVERNED_WORKER_CYCLE_ONLY',
    }}


def test_signed_scope_extracts_only_reviewed_exact_scope():
    assert mod.signed_scope_from_document(good_doc())==('cf10-planning-task85','cf10-u180j-a048')


@pytest.mark.parametrize('field,value', [
    ('worker_id','worker-02'),('max_attempts',2), ('automatic_retry_allowed',True),
    ('explicit_operator_dispatch_required',False), ('route','DIRECT_CLI'),
    ('attempt_id','../../bad'),('task_prompt_id',''),('max_active_workers',True),
])
def test_invalid_scope_cannot_be_selected(field,value):
    d=good_doc();d['pilot_scope'][field]=value
    with pytest.raises(mod.PilotLaunchBlocked,match='SIGNED_RELEASE_SCOPE_INVALID'):
        mod.signed_scope_from_document(d)


def test_missing_scope_does_not_fallback_to_caller_arguments():
    for doc in ({}, {'pilot_scope':None}, {'pilot_scope':{}}, None):
        with pytest.raises(mod.PilotLaunchBlocked):
            mod.signed_scope_from_document(doc)


def test_from_signed_release_conflicts_with_caller_selected_attempt():
    with patch.object(mod,'_root_signed_pilot_scope',side_effect=AssertionError('must not read')):
        assert mod.main(['launch','--from-signed-release','--task-prompt-id','spoof','--confirm-launch'])==2


def test_from_signed_release_wires_scope_to_corridor_not_make_variables():
    calls=[]
    with patch.object(mod,'_root_signed_pilot_scope',return_value=('task85','cf10-u180j-a048')):
        with patch.object(mod,'launch_once',side_effect=lambda **kwargs: calls.append(kwargs) or {'state':'FAKE_TEST_RETURN'}):
            assert mod.main(['launch','--from-signed-release','--confirm-launch'])==0
    assert len(calls)==1 and calls[0]['task_prompt_id']=='task85' and calls[0]['attempt_id']=='cf10-u180j-a048'
    assert calls[0]['confirm'] is True


def test_make_target_uses_only_fixed_arguments_and_old_quarantine_remains():
    root=Path(__file__).resolve().parents[3]
    s=(root/'Makefile').read_text()
    assert 'CF10_S01_AUTHORIZED_ONE_SHOT_LAUNCH_V0_1' in s
    assert 'cf10-s01-governed-one-shot-launch:' in s
    assert 'cf10_s01_live_pilot_corridor_v0_1 launch' in s
    assert '--from-signed-release' in s
    assert '--confirm-launch' in s
    assert 'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND' in s
    target=s.split('cf10-s01-governed-one-shot-launch:',1)[1].split('\n\n',1)[0]
    assert '$(CF10_S01_PILOT_' not in target
    assert '--task-prompt-id' not in target and '--attempt-id' not in target


def test_direct_python_still_rejects_without_privileged_session(tmp_path):
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    with pytest.raises(cycle.GovernedWorkerCycleError,match='CF10_S01_DIRECT_PYTHON_LAUNCH_QUARANTINED'):
        cycle.launch_cycle(root=tmp_path,runtime_root=tmp_path/'runtime',task_prompt_id='task85',
                           attempt_id='cf10-u180j-a048',worker_id='worker-01',confirm=True)
    assert not (tmp_path/'runtime').exists()
