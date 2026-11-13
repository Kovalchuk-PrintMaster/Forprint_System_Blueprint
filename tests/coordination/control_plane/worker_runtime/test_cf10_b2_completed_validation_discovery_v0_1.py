"""CF-10 B2 synthetic immutable validation discovery, no process/authority."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime.completed_validation_discovery_v0_1 import (
    DiscoveryBlocked, discover_completed_validation_evidence,
)

ATTEMPT = 'cf10-u180j-a044'
EID = 'structured-exec-' + 'b' * 20
TASK = 'cf10-planning-projection-cursor-sync-audit-v0-1'
FRONT = 'wf-cf10-planning-projection-cursor-sync-audit-v0-1'
DECISION = 'd' * 64


def sha(data):
    return hashlib.sha256(data).hexdigest()


def js_sha(data):
    return sha(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def fixture(tmp_path):
    attempt = tmp_path / ATTEMPT
    repo = attempt / 'workspace/repo'
    run = attempt / 'evidence/structured_command' / EID
    repo.mkdir(parents=True)
    run.mkdir(parents=True)
    out = run / 'stdout.log'; err = run / 'stderr.log'
    out.write_bytes(b'33 passed\nVALIDATION_SUITE=PASS\n'); err.write_bytes(b'')
    record = {
        'schema_version': 'forprint_structured_execution_result_v0_1',
        'request_id': ATTEMPT + ':validation:0003',
        'capability_id': 'validation_suite', 'capability_version': '0.2.0',
        'execution_id': EID,
        'execution_identity': {
            'attempt_id': ATTEMPT, 'task_id': TASK, 'work_front_id': FRONT,
            'explicit_dispatch_decision_id': DECISION,
        },
        'consumer_id': 'cf10_worker_validation_mcp',
        'exact_cwd': str(repo), 'argv_digest': 'a' * 64,
        'started_at': '2026-10-23T16:03:44Z',
        'finished_at': '2026-10-23T16:08:46Z',
        'elapsed_seconds': 302.107,
        'return_code': 0, 'outcome': 'completed', 'timed_out': False,
        'shell': False,
        'stdout_evidence': {'path': str(out), 'sha256': sha(out.read_bytes()), 'size_bytes': out.stat().st_size},
        'stderr_evidence': {'path': str(err), 'sha256': sha(err.read_bytes()), 'size_bytes': err.stat().st_size},
        'heartbeat_evidence': {'observations': [], 'stall_detected': False, 'stall_evidence': []},
        'stall_detected': False, 'cancellation_state': 'NOT_IMPLEMENTED',
        'execution_policy_result': {
            'decision': 'ALLOW', 'consumer_policy_validated': True,
            'authorization_envelope_verified': True, 'authority_originated_by_executor': False,
        },
        'authority': {name: False for name in (
            'executor_grants_authority', 'canonical_write_allowed', 'safe_write_allowed',
            'commit_allowed', 'push_allowed', 'merge_allowed', 'release_allowed',
            'promotion_allowed', 'arbitrary_shell_allowed',
        )},
        'result_evidence_path': str(run / 'execution_result_v0_1.yaml'),
    }
    write_result(run, record)
    kw = {'attempt_root': str(attempt), 'expected_task_id': TASK,
          'expected_work_front_id': FRONT, 'expected_decision_id': DECISION,
          'expected_workspace': str(repo)}
    return run, record, kw


def write_result(run, record):
    record = {k: v for k, v in record.items() if k != 'evidence_digest'}
    record['evidence_digest'] = js_sha(record)
    (run / 'execution_result_v0_1.yaml').write_text(yaml.safe_dump(record, sort_keys=False))


def test_01_completed_pass_no_replay_and_no_write(tmp_path):
    run, record, kw = fixture(tmp_path)
    snapshot = {str(p): sha(p.read_bytes()) for p in tmp_path.rglob('*') if p.is_file()}
    output = discover_completed_validation_evidence(**kw)
    assert output['status'] == 'PASS_NON_AUTHORIZING'
    assert output['verified_completed_validation'][0]['execution_id'] == EID
    assert output['verified_completed_validation'][0]['request_id'] == ATTEMPT + ':validation:0003'
    assert not output['acceptance_granted'] and not output['replay_skip_authorized']
    assert not output['historical_source_fingerprint_verified']
    assert {str(p): sha(p.read_bytes()) for p in tmp_path.rglob('*') if p.is_file()} == snapshot


def test_02_missing_result_is_incomplete_not_pass(tmp_path):
    run, record, kw = fixture(tmp_path)
    (run / 'execution_result_v0_1.yaml').unlink()
    report = discover_completed_validation_evidence(**kw)
    assert report['verified_completed_validation'] == []
    assert report['incomplete_execution_ids'] == [EID]


def test_03_unrelated_completed_capability_is_not_validation(tmp_path):
    run, record, kw = fixture(tmp_path)
    record['capability_id'] = 'repo_head'
    write_result(run, record)
    report = discover_completed_validation_evidence(**kw)
    assert report['verified_completed_validation'] == []
    assert report['other_completed_count'] == 1


def test_04_corrupt_stdout_rejected(tmp_path):
    run, record, kw = fixture(tmp_path)
    (run / 'stdout.log').write_text('corrupted')
    report = discover_completed_validation_evidence(**kw)
    assert report['verified_completed_validation'] == []
    assert report['rejected_validation_ids'] == [EID]


def test_05_wrong_decision_binding_rejected(tmp_path):
    run, record, kw = fixture(tmp_path)
    kw['expected_decision_id'] = 'f' * 64
    report = discover_completed_validation_evidence(**kw)
    assert report['rejected_validation_ids'] == [EID]


def test_06_unsafe_execution_directory_symlink_blocks(tmp_path):
    run, record, kw = fixture(tmp_path)
    outside = tmp_path / 'outside'
    outside.mkdir()
    link = run.parent / ('structured-exec-' + 'a' * 20)
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(DiscoveryBlocked):
        discover_completed_validation_evidence(**kw)


def test_07_wrong_workspace_blocks(tmp_path):
    run, record, kw = fixture(tmp_path)
    kw['expected_workspace'] = str(tmp_path)
    with pytest.raises(DiscoveryBlocked):
        discover_completed_validation_evidence(**kw)


def test_08_excess_attempt_entries_blocks(tmp_path):
    run, record, kw = fixture(tmp_path)
    for i in range(64):
        (run.parent / ('structured-exec-' + f'{i:020x}')).mkdir()
    with pytest.raises(DiscoveryBlocked, match='budget'):
        discover_completed_validation_evidence(**kw)


def test_09_result_symlink_blocks(tmp_path):
    run, record, kw = fixture(tmp_path)
    path = run / 'execution_result_v0_1.yaml'
    spare = tmp_path / 'malicious.yaml'
    spare.write_bytes(path.read_bytes())
    path.unlink(); path.symlink_to(spare)
    with pytest.raises(DiscoveryBlocked, match='unsafe'):
        discover_completed_validation_evidence(**kw)


def test_10_error_result_does_not_rewrite_history(tmp_path):
    run, record, kw = fixture(tmp_path)
    record['timed_out'] = True
    write_result(run, record)
    before = (run / 'execution_result_v0_1.yaml').read_bytes()
    report = discover_completed_validation_evidence(**kw)
    assert report['rejected_validation_ids'] == [EID]
    assert (run / 'execution_result_v0_1.yaml').read_bytes() == before


def test_11_missing_evidence_root_blocks(tmp_path):
    repo = tmp_path / ATTEMPT / 'workspace/repo'
    repo.mkdir(parents=True)
    with pytest.raises(DiscoveryBlocked):
        discover_completed_validation_evidence(
            attempt_root=str(repo.parent.parent), expected_task_id=TASK,
            expected_work_front_id=FRONT, expected_decision_id=DECISION,
            expected_workspace=str(repo),
        )
