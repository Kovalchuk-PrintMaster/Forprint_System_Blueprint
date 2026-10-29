"""CF-10 operator activation boundary for the shared canonical ledger writer.

READ ONLY by construction. This module never provisions /etc or /run, signs
approvals, launches Workers, publishes Git, or runs Closeout Apply.
An independent system operator installs the externally approved protocol.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Callable

import yaml

from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer

RUNTIME_LOCK_OWNER_UID = 0
TRUST_DIR = Path('/etc/forprint/execution_attempt_writer_activation')
TRUST_FILE = TRUST_DIR / 'trust_root_v0_1.json'
COVERAGE_FILE = TRUST_DIR / 'writer_coverage_v0_1.json'
CANDIDATE_FILE = TRUST_DIR / 'protocol_candidate_v0_1.yaml'
DECISION_FILE = TRUST_DIR / 'signed_decision_v0_1.json'
PURPOSE = 'FORPRINT_LEDGER_WRITER_PROTOCOL_ACTIVATION_V0_1'
DOMAIN = b'FORPRINT/LEDGER_WRITER/ACTIVATION/v0.1\x00'
TRUST_SCHEMA = 'forprint_execution_attempt_writer_activation_trust_v0_1'
COVERAGE_SCHEMA = 'forprint_execution_attempt_writer_coverage_v0_1'
DECISION_SCHEMA = 'forprint_execution_attempt_writer_activation_decision_v0_1'
SOURCES = {
    'scripts/coordination/execution_attempt_ledger_v0_1.py': '7fba536611f4e33fada0144635291ed0f8cf62ed7e3687322a9644ba71b953d5',
    'scripts/coordination/execution_attempt_writer_lock_v0_1.py': '90ef12604e855914d3d9bb7bc04abdfb0c7515e9ffa489108cef380054f36703',
    'scripts/coordination/work_front_closeout_apply_v0_1.py': 'd7926f2ff944b8fd0b5073ec37650340fbb7787f9c151788cc68182048598d95',
}

class ActivationBlocked(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()


def trusted_bytes(path: Path) -> bytes:
    """No symlink, unsafe parent, or writable-by-others external authority file."""
    parent = path.parent
    if not parent.exists() or parent.is_symlink():
        raise ActivationBlocked('EXTERNAL_PARENT_MISSING_OR_SYMLINK:' + str(parent))
    pst = parent.lstat()
    if not stat.S_ISDIR(pst.st_mode) or pst.st_uid != 0 or pst.st_mode & 0o022:
        raise ActivationBlocked('EXTERNAL_PARENT_UNSAFE:' + str(parent))
    try:
        lst = path.lstat()
    except FileNotFoundError as exc:
        raise ActivationBlocked('EXTERNAL_FILE_MISSING:' + path.name) from exc
    if not stat.S_ISREG(lst.st_mode) or lst.st_uid != 0 or lst.st_mode & 0o022:
        raise ActivationBlocked('EXTERNAL_FILE_UNSAFE:' + path.name)
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0))
    try:
        fstat = os.fstat(fd)
        if (fstat.st_dev, fstat.st_ino) != (lst.st_dev, lst.st_ino):
            raise ActivationBlocked('EXTERNAL_FILE_REPLACED:' + path.name)
        with os.fdopen(fd, 'rb', closefd=False) as f:
            return f.read()
    finally:
        os.close(fd)


def trusted_json(path: Path) -> tuple[dict, bytes]:
    raw = trusted_bytes(path)
    try:
        doc = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ActivationBlocked('EXTERNAL_JSON_INVALID:' + path.name) from exc
    if not isinstance(doc, dict) or canonical(doc) != raw:
        raise ActivationBlocked('EXTERNAL_JSON_NONCANONICAL:' + path.name)
    return doc, raw


def git(root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(['git', *args], cwd=root, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return result.stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise ActivationBlocked('PUBLICATION_OR_SOURCE_GIT_UNAVAILABLE') from exc


def verify_source_and_publication(root: Path, trust: dict, approved_commit: str,
                                  *, publication_probe: Callable[[str, str], str] | None = None) -> None:
    if not re.fullmatch(r'[a-f0-9]{40}', approved_commit):
        raise ActivationBlocked('PUBLICATION_COMMIT_INVALID')
    if git(root, 'rev-parse', 'HEAD').decode().strip() != approved_commit:
        raise ActivationBlocked('CHECKOUT_NOT_APPROVED_PUBLICATION_COMMIT')
    remote = trust.get('publication_remote')
    ref = trust.get('publication_ref')
    if not isinstance(remote, str) or not remote or not isinstance(ref, str) or not ref.startswith('refs/heads/'):
        raise ActivationBlocked('PUBLICATION_TRUST_PIN_INVALID')
    # Independent policy pins the remote URL and exact ref; no user-supplied URL.
    actual_remote = git(root, 'remote', 'get-url', 'origin').decode().strip()
    if actual_remote != remote:
        raise ActivationBlocked('PUBLICATION_REMOTE_URL_DRIFT')
    if publication_probe is None:
        def publication_probe(url: str, branch_ref: str) -> str:
            raw = git(root, 'ls-remote', '--exit-code', url, branch_ref).decode()
            parts = raw.splitlines()
            if len(parts) != 1:
                raise ActivationBlocked('REMOTE_REF_NOT_UNIQUE')
            sha, sep, observed_ref = parts[0].partition('\t')
            if not sep or observed_ref != branch_ref:
                raise ActivationBlocked('REMOTE_REF_MISMATCH')
            return sha
    if publication_probe(remote, ref) != approved_commit:
        raise ActivationBlocked('REMOTE_PUBLICATION_COMMIT_DRIFT')
    for path, expected in SOURCES.items():
        live = root / path
        if not live.is_file() or live.is_symlink() or digest(live.read_bytes()) != expected:
            raise ActivationBlocked('WRITER_SOURCE_POSTIMAGE_DRIFT:' + path)
        try:
            blob = git(root, 'show', approved_commit + ':' + path)
        except ActivationBlocked as exc:
            raise ActivationBlocked('PUBLISHED_SOURCE_MISSING:' + path) from exc
        if digest(blob) != expected:
            raise ActivationBlocked('PUBLISHED_WRITER_BLOB_DRIFT:' + path)


def validate_coverage(coverage: dict) -> None:
    if coverage.get('schema_version') != COVERAGE_SCHEMA or coverage.get('status') != 'VERIFIED':
        raise ActivationBlocked('WRITER_COVERAGE_NOT_VERIFIED')
    if (coverage.get('all_writer_processes_enrolled') is not True or
            coverage.get('running_process_restart_or_drain_verified') is not True or
            coverage.get('unreviewed_writers') != []):
        raise ActivationBlocked('WRITER_COVERAGE_INCOMPLETE')
    rows = coverage.get('writer_entrypoints')
    if not isinstance(rows, list) or len(rows) < 2 or any(not isinstance(x, str) or not x for x in rows):
        raise ActivationBlocked('WRITER_ENTRYPOINT_INVENTORY_MISSING')
    required = {'scripts/coordination/control_plane/governed_worker_cycle.py',
                'scripts/coordination/control_plane/dispatch_intent.py',
                'scripts/coordination/execution_attempt_ledger_v0_1.py'}
    if not required.issubset(set(rows)):
        raise ActivationBlocked('KNOWN_WRITER_ENTRYPOINT_NOT_COVERED')
    if not isinstance(coverage.get('independent_operator_review_ref'), str) or not coverage['independent_operator_review_ref']:
        raise ActivationBlocked('COVERAGE_REVIEW_PROVENANCE_MISSING')


def verify_signed_decision(decision: dict, trust: dict, *, candidate_sha: str,
                           coverage_sha: str, approved_commit: str,
                           now: datetime | None = None) -> None:
    if trust.get('schema_version') != TRUST_SCHEMA or trust.get('enabled_for_activation') is not True:
        raise ActivationBlocked('TRUST_POLICY_NOT_ENABLED')
    if (decision.get('schema_version') != DECISION_SCHEMA or decision.get('purpose') != PURPOSE
            or decision.get('decision') != 'AUTHORIZE_OPERATOR_PROVISIONING'):
        raise ActivationBlocked('ACTIVATION_DECISION_PURPOSE_INVALID')
    for key, expected in [('protocol_sha256', candidate_sha), ('coverage_sha256', coverage_sha),
                          ('publication_commit', approved_commit),
                          ('publication_remote', trust.get('publication_remote')),
                          ('publication_ref', trust.get('publication_ref'))]:
        if decision.get(key) != expected:
            raise ActivationBlocked('SIGNED_ACTIVATION_BINDING_DRIFT:' + key)
    trusted = trust.get('trusted_signers')
    signer_id = decision.get('signer_id')
    if not isinstance(trusted, dict) or not isinstance(signer_id, str) or signer_id not in trusted:
        raise ActivationBlocked('ACTIVATION_SIGNER_NOT_TRUSTED')
    try:
        issued = datetime.fromisoformat(decision['issued_at'].replace('Z', '+00:00'))
        expires = datetime.fromisoformat(decision['expires_at'].replace('Z', '+00:00'))
    except (ValueError, KeyError, AttributeError) as exc:
        raise ActivationBlocked('ACTIVATION_DECISION_TIME_INVALID') from exc
    now = now or datetime.now(timezone.utc)
    if (issued.tzinfo is None or expires.tzinfo is None or issued > now or expires <= now or
            (expires - issued).total_seconds() > 86400):
        raise ActivationBlocked('ACTIVATION_DECISION_EXPIRED_OR_UNBOUNDED')
    if not isinstance(decision.get('nonce'), str) or len(decision['nonce']) < 32:
        raise ActivationBlocked('ACTIVATION_NONCE_INVALID')
    signature = decision.get('signature_base64')
    if not isinstance(signature, str):
        raise ActivationBlocked('ACTIVATION_SIGNATURE_MISSING')
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        sig = base64.b64decode(signature, validate=True)
        key = load_pem_public_key(trusted[signer_id].encode('ascii'))
        if not isinstance(key, Ed25519PublicKey):
            raise ActivationBlocked('ACTIVATION_ALGORITHM_INVALID')
        material = {k: v for k, v in decision.items() if k != 'signature_base64'}
        key.verify(sig, DOMAIN + canonical(material))
    except (ValueError, TypeError, UnicodeError, ImportError, AttributeError) as exc:
        raise ActivationBlocked('ACTIVATION_SIGNATURE_UNVERIFIABLE') from exc
    except Exception as exc:
        if isinstance(exc, ActivationBlocked):
            raise
        raise ActivationBlocked('ACTIVATION_SIGNATURE_INVALID') from exc


def validate_candidate(raw: bytes) -> Path:
    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ActivationBlocked('CANDIDATE_YAML_INVALID') from exc
    if (not isinstance(doc, dict) or doc.get('schema_version') != writer.SCHEMA
            or doc.get('state') != 'ENFORCED'):
        raise ActivationBlocked('CANDIDATE_NOT_ENFORCED')
    named = doc.get('lock_path')
    if not isinstance(named, str):
        raise ActivationBlocked('CANDIDATE_LOCK_PATH_MISSING')
    lock_path = Path(named)
    if (not lock_path.is_absolute() or lock_path.parent != writer.APPROVED_LOCK_DIRECTORY
            or lock_path.name.startswith('.') or lock_path.name in ('', '.', '..')):
        raise ActivationBlocked('CANDIDATE_LOCK_PATH_UNAPPROVED')
    return lock_path


def evaluate(root: Path, *, stage: str,
             publication_probe: Callable[[str, str], str] | None = None,
             now: datetime | None = None) -> dict:
    """Fail closed; no external write, no test-operator bypass in CLI."""
    root = root.resolve()
    if stage not in ('readiness', 'approval-check', 'activation-check', 'verify'):
        raise ActivationBlocked('STAGE_INVALID')
    checks = {'source_installation': 'UNKNOWN', 'external_approval': 'UNKNOWN',
              'deployment_coverage': 'UNKNOWN', 'publication': 'UNKNOWN',
              'external_protocol': 'UNKNOWN'}
    blockers = []
    # Readiness is a complete report. All later stages use the same strict gate.
    for path, expected in SOURCES.items():
        live = root / path
        if not live.is_file() or live.is_symlink() or digest(live.read_bytes()) != expected:
            blockers.append('SOURCE_POSTIMAGE_DRIFT:' + path)
    checks['source_installation'] = 'PASS' if not blockers else 'BLOCKED'
    trust = coverage = decision = None
    candidate_raw = None
    try:
        trust, _ = trusted_json(TRUST_FILE)
        coverage, coverage_raw = trusted_json(COVERAGE_FILE)
        validate_coverage(coverage)
        checks['deployment_coverage'] = 'ATTESTED'
        candidate_raw = trusted_bytes(CANDIDATE_FILE)
        validate_candidate(candidate_raw)
        decision, _ = trusted_json(DECISION_FILE)
        signed_commit = decision.get('publication_commit')
        verify_signed_decision(decision, trust, candidate_sha=digest(candidate_raw),
                               coverage_sha=digest(coverage_raw),
                               approved_commit=signed_commit, now=now)
        checks['external_approval'] = 'SIGNED_PASS'
    except (ActivationBlocked, OSError) as exc:
        blockers.append('INDEPENDENT_APPROVAL_OR_COVERAGE:' + str(exc))
    if not blockers and trust and decision:
        try:
            verify_source_and_publication(root, trust, decision['publication_commit'],
                                          publication_probe=publication_probe)
            checks['publication'] = 'REMOTE_REF_AND_BLOBS_PASS'
        except ActivationBlocked as exc:
            blockers.append('PUBLICATION:' + str(exc))
    try:
        active = writer.load_enforced_protocol(required=False)
        if active is None:
            checks['external_protocol'] = 'NOT_PROVISIONED'
            if stage == 'verify':
                blockers.append('ACTIVATION_NOT_PROVISIONED')
        else:
            checks['external_protocol'] = 'ENFORCED'
            if candidate_raw is None or active['sha256'] != digest(candidate_raw):
                blockers.append('ACTIVATION_PROTOCOL_BYTES_MISMATCH')
    except (writer.WriterProtocolError, OSError) as exc:
        checks['external_protocol'] = 'INVALID'
        blockers.append('ACTIVATION_PROTOCOL_INVALID:' + str(exc))
    if stage in ('activation-check', 'verify'):
        parent = writer.APPROVED_LOCK_DIRECTORY
        try:
            st = parent.lstat()
            if not stat.S_ISDIR(st.st_mode) or st.st_uid != RUNTIME_LOCK_OWNER_UID or st.st_mode & 0o022:
                blockers.append('RUNTIME_LOCK_DIRECTORY_UNSAFE')
        except FileNotFoundError:
            blockers.append('RUNTIME_LOCK_DIRECTORY_NOT_READY')
    if stage == 'activation-check' and checks['external_protocol'] != 'NOT_PROVISIONED':
        blockers.append('ACTIVATION_ALREADY_PROVISIONED_USE_VERIFY')
    if stage == 'approval-check' and checks['external_protocol'] == 'ENFORCED':
        blockers.append('APPROVAL_CHECK_AFTER_ACTIVATION_USE_VERIFY')
    return {'schema_version': 'forprint_execution_attempt_writer_activation_gate_v0_1',
            'stage': stage, 'status': 'PASS' if not blockers else 'BLOCKED',
            'checks': checks, 'blockers': blockers,
            'operator_actions': {
                'external_provisioning_performed': False,
                'signing_performed': False,
                'worker_launch_performed': False,
                'canonical_closeout_performed': False,
                'commit_performed': False, 'push_performed': False}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('readiness', 'approval-check', 'activation-check', 'verify'))
    parser.add_argument('--root', type=Path, default=Path('.'))
    args = parser.parse_args(argv)
    result = evaluate(args.root, stage=args.stage)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' or args.stage == 'readiness' else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ActivationBlocked as exc:
        print(json.dumps({'status': 'BLOCKED', 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
