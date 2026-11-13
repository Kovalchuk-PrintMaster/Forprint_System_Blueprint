"""Non-live fixture checks for independent CF-10 ledger-writer activation gates."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.serialization import NoEncryption, PrivateFormat
import pytest
import yaml

from scripts.coordination import execution_attempt_writer_activation_v0_1 as gate
from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True).stdout.decode().strip()


def save_json(path, doc):
    path.write_bytes(gate.canonical(doc))


@pytest.fixture
def rig(tmp_path, monkeypatch):
    src = Path(__file__).resolve().parents[2]
    root = tmp_path / 'repo'
    root.mkdir()
    for rel in gate.SOURCES:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((src / rel).read_bytes())
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'test@example.invalid')
    git(root, 'config', 'user.name', 'Test Only')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'fixture published writer sources')
    commit = git(root, 'rev-parse', 'HEAD')
    git(root, 'remote', 'add', 'origin', 'ssh://example.invalid/blueprint.git')
    ext = tmp_path / 'external'
    ext.mkdir()
    locks = tmp_path / 'run-forprint'
    locks.mkdir()
    cfg_dir = tmp_path / 'forprint'
    cfg_dir.mkdir()
    protocol_file = cfg_dir / 'execution_attempt_writer_protocol_v0_1.yaml'
    monkeypatch.setattr(gate, 'TRUST_DIR', ext)
    monkeypatch.setattr(gate, 'TRUST_FILE', ext / 'trust_root_v0_1.json')
    monkeypatch.setattr(gate, 'COVERAGE_FILE', ext / 'writer_coverage_v0_1.json')
    monkeypatch.setattr(gate, 'CANDIDATE_FILE', ext / 'protocol_candidate_v0_1.yaml')
    monkeypatch.setattr(gate, 'DECISION_FILE', ext / 'signed_decision_v0_1.json')
    monkeypatch.setattr(writer, 'PROTOCOL_PATH', protocol_file)
    monkeypatch.setattr(writer, 'APPROVED_LOCK_DIRECTORY', locks)
    monkeypatch.setattr(writer, 'TRUSTED_OWNER_UID', os.getuid())
    monkeypatch.setattr(gate, 'RUNTIME_LOCK_OWNER_UID', os.getuid())
    # Simulate root-owned files and directories in isolated fixture only.
    # The CLI has no root-ownership override; this applies only to test context.
    monkeypatch.setattr(gate.os, 'getuid', os.getuid)
    original = gate.trusted_bytes
    def fixture_owned_bytes(path):
        st = path.parent.lstat()
        assert st.st_uid == os.getuid() and not (st.st_mode & 0o022)
        lst = path.lstat()
        assert lst.st_uid == os.getuid() and not (lst.st_mode & 0o022)
        return path.read_bytes()
    monkeypatch.setattr(gate, 'trusted_bytes', fixture_owned_bytes)
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    trust = {'schema_version': gate.TRUST_SCHEMA, 'enabled_for_activation': True,
             'publication_remote': 'ssh://example.invalid/blueprint.git',
             'publication_ref': 'refs/heads/main', 'trusted_signers': {'operator-fixture': public}}
    coverage = {'schema_version': gate.COVERAGE_SCHEMA, 'status': 'VERIFIED',
                'all_writer_processes_enrolled': True, 'running_process_restart_or_drain_verified': True,
                'unreviewed_writers': [], 'writer_entrypoints': [
                    'scripts/coordination/control_plane/governed_worker_cycle.py',
                    'scripts/coordination/control_plane/dispatch_intent.py',
                    'scripts/coordination/execution_attempt_ledger_v0_1.py'],
                'independent_operator_review_ref': 'fixture-review'}
    candidate = yaml.safe_dump({'schema_version': writer.SCHEMA, 'state': 'ENFORCED',
                                'lock_path': str(locks/'ledger.lock')}).encode()
    now = datetime.now(timezone.utc)
    decision = {'schema_version': gate.DECISION_SCHEMA, 'purpose': gate.PURPOSE,
                'decision': 'AUTHORIZE_OPERATOR_PROVISIONING', 'signer_id': 'operator-fixture',
                'nonce': 'fixture-nonce-0000000000000000000000000001',
                'issued_at': (now - timedelta(minutes=1)).isoformat(),
                'expires_at': (now + timedelta(hours=1)).isoformat(),
                'protocol_sha256': gate.digest(candidate),
                'coverage_sha256': gate.digest(gate.canonical(coverage)),
                'publication_commit': commit, 'publication_remote': trust['publication_remote'],
                'publication_ref': trust['publication_ref']}
    def sign():
        material = gate.DOMAIN + gate.canonical(decision)
        decision['signature_base64'] = base64.b64encode(key.sign(material)).decode()
        save_json(gate.DECISION_FILE, decision)
    save_json(gate.TRUST_FILE, trust)
    save_json(gate.COVERAGE_FILE, coverage)
    gate.CANDIDATE_FILE.write_bytes(candidate)
    sign()
    return root, ext, locks, cfg_dir, protocol_file, trust, coverage, decision, sign, commit


def evaluate(rig, stage='activation-check'):
    return gate.evaluate(rig[0], stage=stage,
                         publication_probe=lambda remote, ref: rig[-1])


def test_activation_check_signed_handoff_only_no_provisioning(rig):
    outcome = evaluate(rig)
    assert outcome['status'] == 'PASS', outcome
    assert not rig[4].exists()
    assert outcome['operator_actions']['external_provisioning_performed'] is False


def test_readiness_non_authorizing_with_no_protocol(rig):
    result = evaluate(rig, 'readiness')
    assert result['checks']['external_protocol'] == 'NOT_PROVISIONED'
    assert result['operator_actions']['canonical_closeout_performed'] is False


def test_verify_requires_system_activation(rig):
    result = evaluate(rig, 'verify')
    assert result['status'] == 'BLOCKED'
    assert 'ACTIVATION_NOT_PROVISIONED' in result['blockers']


def test_verify_exact_config_bytes_after_independent_install(rig):
    rig[4].write_bytes(gate.CANDIDATE_FILE.read_bytes())
    out = evaluate(rig, 'verify')
    assert out['checks']['external_protocol'] == 'ENFORCED'
    assert out['status'] == 'PASS', out


def test_protocol_tamper_blocks_verify(rig):
    rig[4].write_bytes(gate.CANDIDATE_FILE.read_bytes() + b'\n# tamper\n')
    out = evaluate(rig, 'verify')
    assert 'ACTIVATION_PROTOCOL_BYTES_MISMATCH' in out['blockers']


def test_candidate_hash_changed_after_signing(rig):
    gate.CANDIDATE_FILE.write_bytes(gate.CANDIDATE_FILE.read_bytes() + b'\n# changed\n')
    assert any('SIGNED_ACTIVATION_BINDING_DRIFT' in x for x in evaluate(rig)['blockers'])


def test_bad_signature_blocks_approval(rig):
    rig[7]['signature_base64'] = base64.b64encode(b'fake').decode()
    save_json(gate.DECISION_FILE, rig[7])
    assert any('ACTIVATION_SIGNATURE_INVALID' in x for x in evaluate(rig)['blockers'])


def test_reused_closeout_purpose_rejected(rig):
    rig[7]['purpose'] = 'FORPRINT_WORK_FRONT_CLOSEOUT_ACCEPTANCE_V0_1'
    rig[8]()
    assert any('PURPOSE_INVALID' in x for x in evaluate(rig)['blockers'])


def test_expired_signed_decision_rejected(rig):
    now = datetime.now(timezone.utc)
    rig[7]['issued_at'] = (now - timedelta(hours=2)).isoformat()
    rig[7]['expires_at'] = (now - timedelta(hours=1)).isoformat()
    rig[8]()
    assert any('EXPIRED' in x for x in evaluate(rig)['blockers'])


def test_unsigned_writer_coverage_drift_blocked(rig):
    rig[6]['unreviewed_writers'] = ['unknown-writer']
    save_json(gate.COVERAGE_FILE, rig[6])
    assert any('COVERAGE_INCOMPLETE' in x for x in evaluate(rig)['blockers'])


def test_known_writer_missing_blocked(rig):
    rig[6]['writer_entrypoints'].remove('scripts/coordination/control_plane/dispatch_intent.py')
    save_json(gate.COVERAGE_FILE, rig[6])
    assert any('ENTRYPOINT_NOT_COVERED' in x for x in evaluate(rig)['blockers'])


def test_unpublished_head_blocks_handoff(rig):
    git(rig[0], 'commit', '--allow-empty', '-qm', 'unpublished new HEAD')
    assert any('CHECKOUT_NOT_APPROVED_PUBLICATION_COMMIT' in x for x in evaluate(rig)['blockers'])


def test_bad_remote_ref_blocks_handoff(rig):
    result = gate.evaluate(rig[0], stage='activation-check',
                           publication_probe=lambda remote, ref: '0' * 40)
    assert any('REMOTE_PUBLICATION_COMMIT_DRIFT' in x for x in result['blockers'])


def test_b4_writer_source_mutation_blocks_handoff(rig):
    f = rig[0] / 'scripts/coordination/work_front_closeout_apply_v0_1.py'
    f.write_bytes(f.read_bytes() + b'\n# drift')
    assert any('SOURCE_POSTIMAGE_DRIFT' in x for x in evaluate(rig)['blockers'])


def test_trust_root_absent_blocks(rig):
    gate.TRUST_FILE.unlink()
    assert evaluate(rig)['status'] == 'BLOCKED'


def test_protocol_symlink_rejected(rig):
    rig[4].symlink_to(gate.CANDIDATE_FILE)
    result = evaluate(rig, 'verify')
    assert result['status'] == 'BLOCKED'
    assert result['checks']['external_protocol'] == 'INVALID'


def test_unsafe_lock_directory_blocks_activation_handoff(rig):
    rig[2].chmod(0o777)
    result = evaluate(rig)
    assert 'RUNTIME_LOCK_DIRECTORY_UNSAFE' in result['blockers']


def test_protocol_present_blocks_second_activation_handoff(rig):
    rig[4].write_bytes(gate.CANDIDATE_FILE.read_bytes())
    out = evaluate(rig, 'activation-check')
    assert 'ACTIVATION_ALREADY_PROVISIONED_USE_VERIFY' in out['blockers']


def test_coverage_sha_tamper_even_if_semantically_complete(rig):
    rig[6]['independent_operator_review_ref'] = 'unapproved-provenance-change'
    save_json(gate.COVERAGE_FILE, rig[6])
    assert any('SIGNED_ACTIVATION_BINDING_DRIFT:coverage_sha256' in x for x in evaluate(rig)['blockers'])
