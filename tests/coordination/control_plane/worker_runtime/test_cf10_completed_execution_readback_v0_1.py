"""A044 evidence readback: synthetic-only, fail-closed, read-only regression."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime.completed_execution_readback_v0_1 import (
    ReadbackBlocked, verify_completed_execution,
)

ATTEMPT = 'cf10-u180j-a044'
EXECUTION = 'structured-exec-' + 'a' * 20
DECISION = 'd' * 64
TASK = 'cf10-planning-projection-cursor-sync-audit-v0-1'
FRONT = 'wf-cf10-planning-projection-cursor-sync-audit-v0-1'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json_sha(v):
    return _sha(json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())


def _fixture(tmp_path):
    attempt = tmp_path / ATTEMPT
    workspace = attempt / 'workspace/repo'
    evidence = attempt / 'evidence/structured_command' / EXECUTION
    workspace.mkdir(parents=True)
    evidence.mkdir(parents=True)
    stdout, stderr = evidence / 'stdout.log', evidence / 'stderr.log'
    stdout.write_bytes(b'33 passed in 245.58s\nVALIDATION_SUITE=PASS\n')
    stderr.write_bytes(b'')
    record = {
        'schema_version': 'forprint_structured_execution_result_v0_1',
        'request_id': ATTEMPT + ':validation:0003',
        'capability_id': 'validation_suite',
        'capability_version': '0.2.0',
        'execution_id': EXECUTION,
        'execution_identity': {
            'attempt_id': ATTEMPT, 'task_id': TASK, 'work_front_id': FRONT,
            'explicit_dispatch_decision_id': DECISION,
        },
        'consumer_id': 'cf10_worker_validation_mcp',
        'exact_cwd': str(workspace),
        'argv_digest': 'b'*64,
        'started_at': '2026-10-23T16:03:44Z',
        'finished_at': '2026-10-23T16:08:46Z',
        'elapsed_seconds': 302.107,
        'return_code': 0,
        'outcome': 'completed',
        'timed_out': False,
        'shell': False,
        'stdout_evidence': {'path': str(stdout), 'sha256': _sha(stdout.read_bytes()), 'size_bytes': stdout.stat().st_size},
        'stderr_evidence': {'path': str(stderr), 'sha256': _sha(stderr.read_bytes()), 'size_bytes': 0},
        'heartbeat_evidence': {'observations': [], 'stall_detected': False, 'stall_evidence': []},
        'stall_detected': False,
        'cancellation_state': 'NOT_IMPLEMENTED',
        'execution_policy_result': {'decision': 'ALLOW', 'consumer_policy_validated': True,
                                    'authorization_envelope_verified': True,
                                    'authority_originated_by_executor': False},
        'authority': {k: False for k in (
            'executor_grants_authority', 'canonical_write_allowed', 'safe_write_allowed',
            'commit_allowed', 'push_allowed', 'merge_allowed', 'release_allowed',
            'promotion_allowed', 'arbitrary_shell_allowed')},
        'result_evidence_path': str(evidence / 'execution_result_v0_1.yaml'),
    }
    record['evidence_digest'] = _json_sha(record)
    path = evidence / 'execution_result_v0_1.yaml'
    path.write_text(yaml.safe_dump(record, sort_keys=False), encoding='utf-8')
    kw = {'attempt_root': str(attempt), 'execution_id': EXECUTION,
          'expected_task_id': TASK, 'expected_work_front_id': FRONT,
          'expected_decision_id': DECISION, 'expected_workspace': str(workspace),
          'expected_request_id': ATTEMPT + ':validation:0003'}
    return path, record, kw


def _save(path, rec):
    rec = copy.deepcopy(rec)
    rec.pop('evidence_digest', None)
    rec['evidence_digest'] = _json_sha(rec)
    path.write_text(yaml.safe_dump(rec, sort_keys=False), encoding='utf-8')


def test_a044_like_completed_evidence_is_read_only_non_authorizing(tmp_path):
    path, record, kw = _fixture(tmp_path)
    before = {p: _sha(p.read_bytes()) for p in path.parents[4].rglob('*') if p.is_file()}
    out = verify_completed_execution(**kw)
    assert out['status'] == 'PASS_NON_AUTHORIZING'
    assert out['execution_completed'] is True
    assert out['historical_source_fingerprint_verified'] is False
    assert out['acceptance_granted'] is False
    assert out['replay_skip_authorized'] is False
    assert {p: _sha(p.read_bytes()) for p in path.parents[4].rglob('*') if p.is_file()} == before


def test_missing_execution_result_blocks_without_relaunch(tmp_path):
    path, _, kw = _fixture(tmp_path)
    path.unlink()
    with pytest.raises(ReadbackBlocked):
        verify_completed_execution(**kw)


def test_unchanged_result_but_mutated_stdout_blocks(tmp_path):
    path, _, kw = _fixture(tmp_path)
    (path.parent / 'stdout.log').write_text('forged PASS')
    with pytest.raises(ReadbackBlocked, match='stdout'):
        verify_completed_execution(**kw)


def test_tampered_result_digest_blocks(tmp_path):
    path, record, kw = _fixture(tmp_path)
    record['elapsed_seconds'] = 1.0
    path.write_text(yaml.safe_dump(record, sort_keys=False))
    with pytest.raises(ReadbackBlocked, match='evidence digest'):
        verify_completed_execution(**kw)


@pytest.mark.parametrize('change', [
    lambda r: r['execution_identity'].update(task_id='different-task'),
    lambda r: r['execution_identity'].update(explicit_dispatch_decision_id='f'*64),
    lambda r: r['authority'].update(commit_allowed=True),
    lambda r: r.update(timed_out=True),
    lambda r: r.update(return_code=2),
    lambda r: r.update(result_evidence_path='/tmp/forged'),
    lambda r: r.update(capability_id='repo_head'),
])
def test_recomputed_digest_cannot_bypass_binding(tmp_path, change):
    path, record, kw = _fixture(tmp_path)
    change(record)
    _save(path, record)
    with pytest.raises(ReadbackBlocked):
        verify_completed_execution(**kw)


def test_wrong_request_identity_blocks(tmp_path):
    path, rec, kw = _fixture(tmp_path)
    kw['expected_request_id'] = ATTEMPT + ':validation:0007'
    with pytest.raises(ReadbackBlocked, match='expected request'):
        verify_completed_execution(**kw)


def test_symlink_result_blocks(tmp_path):
    path, _, kw = _fixture(tmp_path)
    elsewhere = tmp_path / 'outside.yml'
    elsewhere.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(elsewhere)
    with pytest.raises(ReadbackBlocked, match='unsafe'):
        verify_completed_execution(**kw)


def test_duplicate_yaml_key_blocks(tmp_path):
    path, rec, kw = _fixture(tmp_path)
    with path.open('a') as f:
        f.write('\nreturn_code: 0\n')
    with pytest.raises(ReadbackBlocked, match='duplicate'):
        verify_completed_execution(**kw)
