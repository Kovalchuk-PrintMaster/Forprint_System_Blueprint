"""CF10 r045: candidate gate is deliberately incapable of release or launch."""
from __future__ import annotations

import ast
from pathlib import Path
import json
import os
import subprocess
from types import SimpleNamespace
from unittest import mock

import pytest

from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission


@pytest.fixture
def valid():
    return {key: True for key in admission.FACT_KEYS}


def test_exact_fact_matrix_is_frozen(valid):
    assert set(valid) == admission.FACT_KEYS
    assert len(valid) == 15


def test_candidate_is_never_authority_even_all_facts_true(valid):
    result = admission.classify(task='cf10-planning-projection-cursor-sync-audit-v0-1',
                                attempt='cf10-u180j-a050', facts=valid)
    assert result['preclaim_evidence_complete'] is True
    assert result['status'] == 'PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING'
    for key in ('admission_authorized', 'launch_allowed', 'production_cutover',
                'owner_pam_authenticated', 'operator_claim_consumed', 'worker_launched',
                'automatic_retry', 'automatic_acceptance', 'automatic_publication'):
        assert result[key] is False
    assert len(result['remaining_release_proofs']) == 4
    assert 'SEPARATE' in result['next_action']


@pytest.mark.parametrize('name', sorted(admission.FACT_KEYS))
def test_single_missing_fact_denies_even_if_rest_true(valid, name):
    valid[name] = False
    result = admission.classify(task='task-70', attempt='cf10-u180j-a052', facts=valid)
    assert result['preclaim_evidence_complete'] is False
    assert result['blockers'] == ['PRECONDITION_' + name.upper()]
    assert result['launch_allowed'] is False


@pytest.mark.parametrize('value', [None, '', 'wrong', '../attack', 'cf10-u180j-a049/../x',
                                    'cf10-u180j-a01', 'cf10-u180j-a000x',
                                    'cf10-u180j-a123; rm -rf .', 'cf10-u180j-a123\n'])
def test_invalid_attempt_id_denied(valid, value):
    result = admission.classify(task='task-70', attempt=value, facts=valid)
    assert 'NEW_CF10_U180J_ATTEMPT_ID_REQUIRED' in result['blockers']
    assert result['launch_allowed'] is False


@pytest.mark.parametrize('value', ['', None, 'a/b', 'task70;echo leaked', 'x\n'])
def test_invalid_task_id_denied(valid, value):
    result = admission.classify(task=value, attempt='cf10-u180j-a050', facts=valid)
    assert 'TASK_ID_INVALID' in result['blockers']


def test_missing_and_unexpected_facts_denied(valid):
    assert 'INCOMPLETE_READ_ONLY_FACTS' in admission.classify(
        task='task70', attempt='cf10-u180j-a050', facts={})['blockers']
    valid['fake_boolean_override'] = True
    assert 'INCOMPLETE_READ_ONLY_FACTS' in admission.classify(
        task='task70', attempt='cf10-u180j-a050', facts=valid)['blockers']


def test_boolean_true_not_equal_integer_one(valid):
    valid['writer_protocol_enforced'] = 1
    assert 'PRECONDITION_WRITER_PROTOCOL_ENFORCED' in admission.classify(
        task='task70', attempt='cf10-u180j-a050', facts=valid)['blockers']


def test_inventory_rejects_noncanonical_root(tmp_path):
    result = admission.inventory(tmp_path)
    assert result['status'] == 'BLOCKED_NON_AUTHORIZING'
    assert result['tasks'] == []
    assert result['launch_allowed'] is False


def test_collect_rejects_wrong_root_before_imports(tmp_path):
    result = admission.collect(tmp_path, 'task70', 'cf10-u180j-a050')
    assert result['preclaim_evidence_complete'] is False
    assert result['launch_allowed'] is False


def test_quiescence_empty_is_observation_not_authority():
    proc = subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')
    with mock.patch.object(admission.subprocess, 'run', return_value=proc) as call:
        assert admission._systemd_quiescent() == (True, 'NO_ACTIVE_CF10_WORKER_UNITS_OBSERVED')
    assert call.call_args.args[0][0] == '/usr/bin/systemctl'
    assert 'list-units' in call.call_args.args[0]


@pytest.mark.parametrize('stdout', [
    'forprint-cf10-worker-' + 'a' * 24 + '.service loaded active running example\n',
    'forprint-cf10-worker-' + 'a' * 24 + '.service loaded activating start example\n',
    'garbage data\n',
    'forprint-website-preview.service loaded inactive dead unrelated\n',
])
def test_quiescence_blocks_nonidle_or_unexpected_service(stdout):
    proc = subprocess.CompletedProcess([], 0, stdout=stdout, stderr='')
    with mock.patch.object(admission.subprocess, 'run', return_value=proc):
        assert admission._systemd_quiescent()[0] is False


def test_quiescence_blocks_failed_systemctl():
    proc = subprocess.CompletedProcess([], 1, stdout='', stderr='failed')
    with mock.patch.object(admission.subprocess, 'run', return_value=proc):
        assert admission._systemd_quiescent() == (False, 'SYSTEMD_READBACK_UNAVAILABLE')


def test_claim_existing_is_never_treated_as_new():
    # Mock the existing root-owned opener; never create a claim in tests.
    import scripts.coordination.control_plane.cf10_s01_root_controlled_single_use_v0_2 as once
    with mock.patch.object(once, 'open_root_owned_state_dir', return_value=34), \
         mock.patch.object(admission.os, 'stat', return_value=SimpleNamespace(st_mode=0o100600)), \
         mock.patch.object(admission.os, 'close'):
        ok, status = admission._claim_unconsumed('cf10-u180j-a055')
    assert (ok, status) == (False, 'ALREADY_CONSUMED')


def test_missing_claim_is_fresh_without_writing():
    import scripts.coordination.control_plane.cf10_s01_root_controlled_single_use_v0_2 as once
    with mock.patch.object(once, 'open_root_owned_state_dir', return_value=34), \
         mock.patch.object(admission.os, 'stat', side_effect=FileNotFoundError()), \
         mock.patch.object(admission.os, 'close'):
        assert admission._claim_unconsumed('cf10-u180j-a057') == (True, 'NOT_CONSUMED')


def test_inventory_exact_single_task70(monkeypatch):
    from scripts.coordination.control_plane import cf10_training_dispatch as t
    root = admission.PROJECT
    entries = [{'work_id': 'u180j', 'task_id': 'candidateA'},
               {'work_id': 'u180j', 'task_id': 'candidateB'}]
    def load(path, _label):
        if path == root / t.TRAINING_QUEUE:
            return {'work_id': 'u180j', 'step_id': 'CF-10', 'tasks': [
                {'task_id': 'validation_check_pipeline_profile_and_optimization', 'order': 70}]}
        return {'tasks': entries}
    monkeypatch.setattr(t, '_load_yaml', load)
    def resolve(*, root, task_prompt_id):
        return {'task_prompt_id': task_prompt_id,
                'training_order': 70 if task_prompt_id=='candidateB' else 60,
                'training_task_id': ('validation_check_pipeline_profile_and_optimization'
                                     if task_prompt_id == 'candidateB' else 'different'),
                'work_front_id':'front70', 'task_ref':'task-file'}
    monkeypatch.setattr(t, 'resolve_training_task', resolve)
    items, errors = admission._task70(root)
    assert errors == []
    assert [x['task_prompt_id'] for x in items] == ['candidateB']
    assert items[0]['training_task_id'] == 'validation_check_pipeline_profile_and_optimization'


def test_inventory_duplicate_task70_is_blocked(monkeypatch):
    from scripts.coordination.control_plane import cf10_training_dispatch as t
    root = admission.PROJECT
    monkeypatch.setattr(t, '_load_yaml', lambda path, _label:
        {'work_id':'u180j','step_id':'CF-10','tasks':[
          {'task_id':'validation_check_pipeline_profile_and_optimization','order':70},
          {'task_id':'duplicate','order':70}]} if path == root / t.TRAINING_QUEUE else
        {'tasks':[{'work_id':'u180j','task_id':'candidateA'}]})
    _, blockers = admission._task70(root)
    assert 'TASK70_REQUIRES_ONE_CANONICAL_QUEUE_BINDING' in blockers


def test_inventory_queue_index_binding_mismatch_is_blocked(monkeypatch):
    from scripts.coordination.control_plane import cf10_training_dispatch as t
    root=admission.PROJECT
    monkeypatch.setattr(t, '_load_yaml', lambda path, _label:
        {'work_id':'u180j','step_id':'CF-10','tasks':[
         {'task_id':'validation_check_pipeline_profile_and_optimization','order':70}]}
        if path == root / t.TRAINING_QUEUE else
        {'tasks':[{'work_id':'u180j','task_id':'candidateA'}]})
    monkeypatch.setattr(t,'resolve_training_task', lambda *,root,task_prompt_id:
        {'task_prompt_id':task_prompt_id,'training_order':70,'training_task_id':'wrong',
         'work_front_id':'f','task_ref':'f'})
    _, blockers=admission._task70(root)
    assert 'TASK70_INDEX_AND_QUEUE_REBIND_FAILED' in blockers


def test_source_contains_no_live_writes_or_pam_or_dynamic_exec():
    tree = ast.parse(Path(admission.__file__).read_text('utf-8'))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    banned = {'systemd-run','systemctl stop','systemctl start','chmod', 'git push', 'git commit'}
    src = Path(admission.__file__).read_text('utf-8')
    assert all(x not in src for x in banned)
    assert "root / 'tmp'" not in src
    assert 'subprocess.Popen' not in src
    assert 'os.O_CREAT' not in src
    assert 'input(' not in src
    assert all(not(isinstance(c.func, ast.Name) and c.func.id in {'eval','exec'}) for c in calls)


def test_main_launch_preflight_is_deny_even_if_facts_complete(capsys, valid):
    outcome = admission.classify(task='task70', attempt='cf10-u180j-a055', facts=valid)
    with mock.patch.object(admission, 'collect', return_value=outcome):
        rc = admission.main(['launch-preflight','--task-prompt-id','task70',
                             '--attempt-id','cf10-u180j-a055'])
    assert rc == 2
    assert json.loads(capsys.readouterr().out)['launch_allowed'] is False


def test_main_inspect_reports_failclosed(capsys):
    rc = admission.main(['inspect', '--task-prompt-id','bad/task','--attempt-id','reuse'])
    assert rc == 2
    obj = json.loads(capsys.readouterr().out)
    assert obj['admission_authorized'] is False


def test_legacy_release_remains_unchanged_and_cutover_disabled():
    root = Path(__file__).resolve().parents[3]
    owner = (root / 'coordination/standards/governance/cf10_single_owner_pilot_design_v0_1.yaml').read_text()
    backend = (root / 'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()
    make = (root / 'Makefile').read_text()
    assert 'legacy_live_release_must_remain_unchanged_until_separate_cutover: true' in owner
    assert 'LIVE_CUTOVER_ENABLED=False' in backend
    assert 'QUARANTINED_NEEDS_INDEPENDENT_REBIND' in make
    assert 'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight' in make

@pytest.fixture
def mocked_collector(tmp_path, monkeypatch):
    """Exercise the real collector with trusted component boundaries mocked.

    No tmp project directory is provisioned and no claim is written.
    """
    from scripts.coordination.control_plane import cf10_training_dispatch as t
    from scripts.coordination.control_plane import cf10_single_owner_pilot_review_v0_1 as d
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as c
    from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as o
    from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as m
    import sys
    import scripts.coordination.control_plane as cp
    g = SimpleNamespace(status=lambda **_: {'state':'READY_FOR_WORKER_LAUNCH'})
    monkeypatch.setitem(sys.modules, 'scripts.coordination.control_plane.governed_worker_cycle', g)
    monkeypatch.setattr(cp, 'governed_worker_cycle', g, raising=False)
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    import scripts.coordination as coordination
    writer = SimpleNamespace(load_enforced_protocol=lambda **_: {'sha256':'f'*64})
    monkeypatch.setitem(sys.modules, 'scripts.coordination.execution_attempt_writer_lock_v0_1', writer)
    monkeypatch.setattr(coordination, 'execution_attempt_writer_lock_v0_1', writer, raising=False)

    monkeypatch.setattr(admission, 'PROJECT', tmp_path)
    runtime=tmp_path/'durable_runtime'
    monkeypatch.setattr(admission, 'RUNTIME', runtime)
    attempt='cf10-u180j-a052'
    task='cf10-validation-check-pipeline-profile-and-optimization-v0-1'
    (runtime/'forprint_system_blueprint'/'worker-01'/attempt).mkdir(parents=True)
    (tmp_path/'scripts/coordination/control_plane').mkdir(parents=True)
    (tmp_path/'scripts/coordination/control_plane/worker_runtime').mkdir()
    (tmp_path/'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py').write_bytes(
        (Path(__file__).resolve().parents[3]/'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py').read_bytes())
    (tmp_path/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').write_text(
        'LIVE_CUTOVER_ENABLED=False\n')
    (tmp_path/'Makefile').write_text(
        'cf10-s01-runtime-launch-preflight:\n'
        '\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2\n'
        'governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight\n')
    monkeypatch.setattr(d,'inspect',lambda _root: {'status':'OWNER_SELECTED_DESIGN_RELEASE_BLOCKED','blockers':[]})
    monkeypatch.setattr(c,'source_guard',lambda _root:'f'*40)
    monkeypatch.setattr(o,'_assert_live_source',lambda _root:'f'*40)
    monkeypatch.setattr(o,'_cycle_preclaim',lambda *_:None)
    monkeypatch.setattr(t,'resolve_training_task',lambda **_:{'training_order':70})
    monkeypatch.setattr(admission,'_task70',lambda _root: ([{'task_prompt_id':task}],[]))
    monkeypatch.setattr(g,'status',lambda **_:{'state':'READY_FOR_WORKER_LAUNCH'})
    monkeypatch.setattr(writer,'load_enforced_protocol',lambda **_: {'sha256':'f'*64})
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda : 123)
    monkeypatch.setattr(admission.os,'close',lambda *_:None)
    monkeypatch.setattr(admission,'_claim_unconsumed',lambda *_: (True,'NOT_CONSUMED'))
    monkeypatch.setattr(ledger,'load_contract',lambda _root:{})
    monkeypatch.setattr(ledger,'store_root',lambda *_:tmp_path/'ledger')
    monkeypatch.setattr(ledger,'records_for_attempt',lambda *_:[])
    monkeypatch.setattr(admission,'_systemd_quiescent',lambda : (True,'NO_ACTIVE'))
    assert not (tmp_path/'tmp').exists()
    return tmp_path,task,attempt


def test_real_collector_uses_existing_rebound_checks_without_new_claim(mocked_collector):
    root,task,attempt=mocked_collector
    result=admission.collect(root,task,attempt)
    assert result['status']=='PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING'
    assert result['preclaim_evidence_complete'] is True
    assert result['launch_allowed'] is False
    assert result['operator_claim_consumed'] is False
    assert not (root/'tmp').exists()


def test_real_collector_missing_immutable_ledger_quarantines(mocked_collector, monkeypatch):
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    monkeypatch.setattr(ledger,'records_for_attempt',lambda *_:[{'result_state':'SUCCEEDED'}])
    root,task,attempt=mocked_collector
    result=admission.collect(root,task,attempt)
    assert 'PRECONDITION_LEDGER_UNSTARTED' in result['blockers']
    assert result['admission_authorized'] is False


def test_real_collector_preclaim_exception_quarantines(mocked_collector, monkeypatch):
    from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
    monkeypatch.setattr(owner,'_cycle_preclaim',lambda *_: (_ for _ in ()).throw(ValueError('frozen input drift')))
    root,task,attempt=mocked_collector
    result=admission.collect(root,task,attempt)
    assert 'PRECONDITION_FROZEN_INPUT_VERIFIED' in result['blockers']
    assert result['worker_launched'] is False
