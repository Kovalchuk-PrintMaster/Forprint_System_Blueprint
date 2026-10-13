"""Proposed pre-activation tests of the shared canonical ledger writer lock.

These are non-live, fixture-only tests; no /etc, /run or real attempt files.
"""
import hashlib
import json
import multiprocessing
import os
import queue
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
from scripts.coordination import execution_attempt_writer_lock_v0_1 as lock

CONTRACT_SOURCE = Path(__file__).resolve().parents[2] / 'coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml'


def record(attempt='cf10-u180j-fixture', state='PENDING', n=0):
    at = (datetime(2026,10,13,tzinfo=timezone.utc) + timedelta(minutes=n)).isoformat()
    return {
        'schema_version': 'forprint_execution_attempt_record_v0_1',
        'attempt_id': attempt, 'work_front_id': 'wf-test', 'recorded_at': at,
        'actor_or_worker_ref': 'fixture-worker', 'where': 'isolated-test',
        'why': 'shared-writer-race-test', 'source_fingerprint': 'fixture-source',
        'profile_ref_or_revision': None, 'pack_hash_or_context_hash': None,
        'launch_or_invocation_ref': None,
        'attempt_stage': 'STARTED' if state == 'PENDING' else 'FINISHED',
        'result_state': state, 'result_refs': [],
        'validator_outcome': 'NOT_RUN' if state == 'PENDING' else 'PASS',
        'validator_evidence_refs': [], 'failure_or_retry_ref': None,
        'resume': {'latest_accepted_ref': None, 'resume_coordinates': [], 'replay_forbidden_refs': []},
    }


@pytest.fixture
def repo(tmp_path, monkeypatch):
    src = CONTRACT_SOURCE
    dst = tmp_path / 'coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml'
    dst.parent.mkdir(parents=True)
    dst.write_bytes(src.read_bytes())
    d = tmp_path / 'run-forprint'
    d.mkdir()
    policy = tmp_path / 'protocol.yaml'
    monkeypatch.setattr(lock, 'PROTOCOL_PATH', policy)
    monkeypatch.setattr(lock, 'APPROVED_LOCK_DIRECTORY', d)
    monkeypatch.setattr(lock, 'TRUSTED_OWNER_UID', os.getuid())
    return tmp_path, policy, d


def enable(policy, directory):
    policy.write_text(yaml.safe_dump({'schema_version':lock.SCHEMA, 'state':'ENFORCED', 'lock_path':str(directory/'ledger.lock')}))
    return directory/'ledger.lock'


def _child_append(root, row, messages):
    messages.put('STARTING')
    try:
        path = ledger.append_record(root, row)
        messages.put(('PASS', path.name))
    except Exception as exc:
        messages.put(('BLOCKED', type(exc).__name__))


def test_absent_config_legacy_append_and_duplicate_rejection(repo):
    root, _, _ = repo
    row = record()
    assert ledger.append_record(root, row).is_file()
    with pytest.raises(FileExistsError):
        ledger.append_record(root, row)


def test_unsafe_present_configuration_never_silently_falls_back(repo):
    root, policy, directory = repo
    real = root/'elsewhere.yaml'
    real.write_text(yaml.safe_dump({'schema_version':lock.SCHEMA,'state':'ENFORCED','lock_path':str(directory/'ledger.lock')}))
    policy.symlink_to(real)
    with pytest.raises(lock.WriterProtocolError, match='UNSAFE'):
        ledger.append_record(root, record())
    assert list((root/'coordination/continuity/execution_attempts').glob('*.yaml')) == [] if (root/'coordination/continuity/execution_attempts').exists() else True


def test_untrusted_owner_is_rejected(repo, monkeypatch):
    root, policy, directory = repo
    enable(policy, directory)
    monkeypatch.setattr(lock, 'TRUSTED_OWNER_UID', os.getuid()+10000)
    with pytest.raises(lock.WriterProtocolError, match='UNSAFE'):
        ledger.append_record(root, record())


def test_canonical_lock_serializes_across_processes(repo):
    root, policy, directory = repo
    enable(policy, directory)
    ctx = multiprocessing.get_context('fork')
    messages = ctx.Queue()
    with lock.guarded_canonical_append():
        process = ctx.Process(target=_child_append, args=(root,record(),messages))
        process.start()
        assert messages.get(timeout=3) == 'STARTING'
        time.sleep(0.25)
        with pytest.raises(queue.Empty):
            messages.get_nowait()
    outcome = messages.get(timeout=5)
    process.join(timeout=5)
    assert not process.is_alive()
    assert process.exitcode == 0
    assert outcome[0] == 'PASS'


def test_only_one_terminal_append_can_win(repo):
    root, policy, directory = repo
    enable(policy, directory)
    ledger.append_record(root, record())
    ctx = multiprocessing.get_context('fork')
    messages = ctx.Queue()
    workers = [ctx.Process(target=_child_append, args=(root, record(state='SUCCEEDED',n=i+1),messages)) for i in range(2)]
    for p in workers: p.start()
    observations = [messages.get(timeout=5) for _ in range(4)]
    for p in workers:
        p.join(timeout=5)
        assert not p.is_alive() and p.exitcode == 0
    results = [item[0] for item in observations if isinstance(item, tuple)]
    assert sorted(results) == ['BLOCKED','PASS']
    assert len(ledger.records_for_attempt(root/'coordination/continuity/execution_attempts', 'cf10-u180j-fixture')) == 2


def test_store_override_alias_of_canonical_uses_lock(repo, monkeypatch):
    root, policy, directory = repo
    enable(policy, directory)
    hits = []
    original = lock.guarded_canonical_append
    def tracked():
        hits.append(1)
        return original()
    monkeypatch.setattr(lock, 'guarded_canonical_append', tracked)
    canonical = root/'coordination/continuity/execution_attempts'
    ledger.append_record(root,record(),store_override=canonical)
    assert hits == [1]


def test_noncanonical_override_isolated_fixture_remains_supported(repo):
    root, policy, directory = repo
    enable(policy, directory)
    dest = root/'tmp/fixtures'
    path = ledger.append_record(root,record(),store_override=dest)
    assert path.parent == dest
    assert not (directory/'ledger.lock').exists()


def test_b4_does_not_accept_lock_claim_when_protocol_unprovisioned(repo):
    from scripts.coordination import work_front_closeout_apply_v0_1 as closeout
    root, policy, directory = repo
    claim = {'approved_global_ledger_lock_path':str(directory/'ledger.lock'),
             'approved_global_ledger_writer_protocol_sha256':'0'*64}
    with pytest.raises(closeout.ApplyError, match='GLOBAL_WRITER_PROTOCOL_NOT_ENFORCED'):
        closeout._lock_path(claim)


def test_b4_rejects_wrong_external_protocol_hash_pin(repo):
    from scripts.coordination import work_front_closeout_apply_v0_1 as closeout
    root, policy, directory = repo
    path = enable(policy, directory)
    claim = {'approved_global_ledger_lock_path':str(path),
             'approved_global_ledger_writer_protocol_sha256':'0'*64}
    with pytest.raises(closeout.ApplyError, match='GLOBAL_LEDGER_LOCK_BINDING_MISMATCH'):
        closeout._lock_path(claim)


def test_b4_and_append_use_same_lock_identity_when_provisioned(repo):
    from scripts.coordination import work_front_closeout_apply_v0_1 as closeout
    root, policy, directory = repo
    path = enable(policy, directory)
    claim = {'approved_global_ledger_lock_path':str(path),
             'approved_global_ledger_writer_protocol_sha256':hashlib.sha256(policy.read_bytes()).hexdigest()}
    assert closeout._lock_path(claim) == lock.load_enforced_protocol(required=True)['lock_path']
    assert ledger.append_record(root,record()).is_file()
    assert path.is_file()
