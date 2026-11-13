"""CF-10 S01 candidate release gate; never wired to live Make by this package.

The only possible positive preflight requires: independently signed release receipt,
current activation verifier PASS, exact published Git sources, active shared lock,
and mandatory canonical direct-CLI guard. No signing, provisioning or launch.
"""
from __future__ import annotations

import argparse
import ast
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SCHEMA = 'cf10_s01_release_authorization_v0_1'
TRUST_SCHEMA = 'cf10_s01_independent_release_trust_v0_1'
PURPOSE = 'CF10_S01_ONE_WORKER_ONE_ATTEMPT_RELEASE_V0_1'
DOMAIN = b'FORPRINT/CF10/S01/INDEPENDENT_RELEASE/v0.1\x00'
RELEASE_TRUST = Path('/etc/forprint/cf10_release_authority/trust_root_v0_1.json')
RELEASE_DECISION = Path('/etc/forprint/cf10_release_authority/signed_release_v0_1.json')
ACTIVATION_DECISION = Path('/etc/forprint/execution_attempt_writer_activation/signed_decision_v0_1.json')
COVERAGE = Path('/etc/forprint/execution_attempt_writer_activation/writer_coverage_v0_1.json')
SOURCE_GUARD = 'scripts/coordination/execution_attempt_writer_lock_v0_1.py'
SOURCE_LEDGER = 'scripts/coordination/execution_attempt_ledger_v0_1.py'
BRANCH = 'audit/blueprint-inventory-refresh-2026-07-29'
REMOTE_REF = 'refs/heads/' + BRANCH
SHA40 = re.compile(r'[a-f0-9]{40}\Z')
SHA64 = re.compile(r'[a-f0-9]{64}\Z')
PROOFS = (
    'writer_entrypoints_and_callbacks',
    'active_and_short_lived_process_enrollment',
    'drain_restart_and_old_writer_exclusion',
    'systemd_cron_manual_ssh_remote_paths',
    'lock_inode_acl_mount_and_dac',
    'independent_dynamic_non_bypass_proof',
    'independent_signature_and_publication',
    'separate_release_quarantine_acceptance',
)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(doc: dict) -> bytes:
    return (json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()


def command(root: Path, *argv: str) -> str:
    p = subprocess.run(['git', *argv], cwd=root, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=20, check=True)
    return p.stdout.decode('utf-8').strip()


def strict_direct_writer_guard(guard_source: str, ledger_source: str) -> bool:
    """Necessary syntax proof: the canonical direct path cannot fall back to unlocked.

    Sufficient runtime proof still requires independent dynamic attestation. This
    AST proof intentionally rejects unknown refactors until separately reviewed.
    """
    try:
        g = ast.parse(guard_source)
        l = ast.parse(ledger_source)
    except SyntaxError:
        return False
    methods = {n.name: n for n in g.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    guarded = methods.get('guarded_canonical_append')
    if guarded is None:
        return False
    required = [n for n in ast.walk(guarded) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == 'load_enforced_protocol'
                and any(k.arg == 'required' and isinstance(k.value, ast.Constant) and k.value.value is True
                        for k in n.keywords)]
    # Any early 'active is None: yield' retains the unlocked canonical fallback.
    unlocked = [n for n in ast.walk(guarded) if isinstance(n, ast.If)
                and isinstance(n.test, ast.Compare)
                and isinstance(n.test.left, ast.Name) and n.test.left.id == 'active'
                and any(isinstance(c, ast.Is) for c in n.test.ops)
                and any(isinstance(v, ast.Constant) and v.value is None for v in n.test.comparators)
                and any(isinstance(b, (ast.Expr, ast.Yield)) and
                        (isinstance(b, ast.Yield) or isinstance(b.value, ast.Yield)) for b in n.body)]
    append = next((n for n in l.body if isinstance(n, ast.FunctionDef) and n.name == 'append_record'), None)
    if append is None:
        return False
    calls = [n for n in ast.walk(append) if isinstance(n, ast.Call) and
             isinstance(n.func, ast.Attribute) and n.func.attr == 'guarded_canonical_append']
    if not required or unlocked or not calls:
        return False
    return True


def verify_release_receipt(receipt: dict, trust: dict, activation: dict,
                           *, head: str, remote: str, protocol_sha: str,
                           coverage_sha: str, activation_sha: str,
                           guard_sha: str, ledger_sha: str,
                           now: datetime | None = None) -> list[str]:
    """Independent reviewer's Ed25519 signature is mandatory, not a user bool.

    This is a contract candidate; external trust roles and decision content must
    be accepted by the independent operator before installation or live wiring.
    """
    bad = []
    if trust.get('schema_version') != TRUST_SCHEMA or trust.get('enabled') is not True:
        bad.append('RELEASE_TRUST_UNAVAILABLE')
    if receipt.get('schema_version') != SCHEMA or receipt.get('purpose') != PURPOSE or receipt.get('decision') != 'AUTHORIZE_BOUNDED_WORKER_PILOT':
        bad.append('RELEASE_DECISION_PURPOSE_INVALID')
    expected = {
        'publication_commit': head, 'publication_remote': remote, 'publication_ref': REMOTE_REF,
        'active_protocol_sha256': protocol_sha, 'coverage_sha256': coverage_sha,
        'activation_decision_sha256': activation_sha, 'writer_guard_source_sha256': guard_sha,
        'canonical_ledger_source_sha256': ledger_sha,
    }
    for k, v in expected.items():
        if receipt.get(k) != v:
            bad.append('RELEASE_PIN_MISMATCH:' + k)
    proofs = receipt.get('independent_proofs')
    if not isinstance(proofs, dict) or set(proofs) != set(PROOFS) or any(
        not isinstance(x, str) or not SHA64.fullmatch(x) for x in proofs.values()
    ):
        bad.append('INDEPENDENT_PROOF_DIGEST_SET_INCOMPLETE')
    reviewer = receipt.get('signer_id')
    signer_map = trust.get('trusted_reviewers')
    if (not isinstance(reviewer, str) or not isinstance(signer_map, dict) or
            reviewer not in signer_map or reviewer == activation.get('signer_id')):
        bad.append('INDEPENDENT_REVIEWER_NOT_DISTINCT_OR_UNTRUSTED')
    if not isinstance(receipt.get('independent_operator_review_ref'), str) or not receipt['independent_operator_review_ref'].strip():
        bad.append('REVIEW_REFERENCE_MISSING')
    if not isinstance(receipt.get('nonce'), str) or len(receipt['nonce']) < 32:
        bad.append('RELEASE_NONCE_INVALID')
    now = now or datetime.now(timezone.utc)
    try:
        issue = datetime.fromisoformat(receipt['issued_at'].replace('Z', '+00:00'))
        expiry = datetime.fromisoformat(receipt['expires_at'].replace('Z', '+00:00'))
        if (issue.tzinfo is None or expiry.tzinfo is None or issue > now or
                expiry <= now or (expiry - issue).total_seconds() <= 0 or
                (expiry - issue).total_seconds() > 28800):
            bad.append('RELEASE_DECISION_EXPIRED_OR_TIME_INVALID')
    except (KeyError, ValueError, AttributeError, TypeError):
        bad.append('RELEASE_DECISION_TIME_INVALID')
    if bad:
        return sorted(set(bad))
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        key = load_pem_public_key(signer_map[reviewer].encode('ascii'))
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError('reviewer key algorithm')
        sig = base64.b64decode(receipt['signature_base64'], validate=True)
        material = {k: v for k, v in receipt.items() if k != 'signature_base64'}
        key.verify(sig, DOMAIN + canonical(material))
    except Exception:
        bad.append('RELEASE_SIGNATURE_INVALID')
    return bad


def evaluate(root: Path, *, mode: str) -> dict:
    """Live read-only evaluation; nothing here provisions, signs, or launches."""
    from scripts.coordination import execution_attempt_writer_activation_v0_1 as activation
    from scripts.coordination import execution_attempt_writer_lock_v0_1 as writer
    blockers: list[str] = []
    checks: dict[str, str] = {}
    root = root.resolve()
    before = None
    try:
        before = command(root, 'rev-parse', 'HEAD')
        checks['head'] = before
        if not SHA40.fullmatch(before): blockers.append('INVALID_GIT_HEAD')
        if command(root, 'branch', '--show-current') != BRANCH:
            blockers.append('WRONG_RELEASE_BRANCH')
        if command(root, 'diff', '--cached', '--name-only'):
            blockers.append('STAGED_FILES_PRESENT')
        remote = command(root, 'remote', 'get-url', 'origin')
        remote_tip = command(root, 'ls-remote', '--exit-code', 'origin', REMOTE_REF)
        if remote_tip.split()[0] != before:
            blockers.append('REMOTE_HEAD_NOT_MATCHED')
        checks['remote_sha'] = remote_tip.split()[0]
    except Exception:
        blockers.append('GIT_PUBLICATION_UNVERIFIABLE')
        remote = ''
    sources: dict[str, bytes] = {}
    if before:
        for rel in (SOURCE_GUARD, SOURCE_LEDGER):
            try:
                data = (root / rel).read_bytes()
                published = subprocess.run(['git', 'show', before + ':' + rel], cwd=root,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         timeout=20, check=True).stdout
                if data != published or (root / rel).is_symlink():
                    blockers.append('UNPUBLISHED_DIRECT_WRITER_SOURCE:' + rel)
                sources[rel] = data
            except Exception:
                blockers.append('DIRECT_WRITER_SOURCE_UNAVAILABLE:' + rel)
    if set(sources) == {SOURCE_GUARD, SOURCE_LEDGER}:
        if not strict_direct_writer_guard(sources[SOURCE_GUARD].decode('utf-8'),
                                          sources[SOURCE_LEDGER].decode('utf-8')):
            blockers.append('DIRECT_PYTHON_CANONICAL_WRITER_HAS_LEGACY_UNLOCKED_FALLBACK')
    try:
        activated = activation.evaluate(root, stage='verify')
        checks['activation'] = activated['status']
        if activated['status'] != 'PASS':
            blockers.append('WRITER_ACTIVATION_NOT_VERIFIED')
    except Exception:
        blockers.append('WRITER_ACTIVATION_CHECK_FAILED')
    try:
        active = writer.load_enforced_protocol(required=True)
        checks['protocol'] = 'ENFORCED' if active else 'BLOCKED'
        if not active: blockers.append('SHARED_WRITER_PROTOCOL_ABSENT')
        protocol_sha = active['sha256'] if active else ''
    except Exception:
        protocol_sha = ''
        blockers.append('SHARED_WRITER_PROTOCOL_ABSENT_OR_INVALID')
    receipt = trust = act = None
    try:
        trust, _ = activation.trusted_json(RELEASE_TRUST)
        receipt, _ = activation.trusted_json(RELEASE_DECISION)
        act, act_raw = activation.trusted_json(ACTIVATION_DECISION)
        _, coverage_raw = activation.trusted_json(COVERAGE)
        if set(sources) == {SOURCE_GUARD, SOURCE_LEDGER}:
            blockers.extend(verify_release_receipt(
                receipt, trust, act, head=before or '', remote=remote,
                protocol_sha=protocol_sha, coverage_sha=digest(coverage_raw),
                activation_sha=digest(act_raw), guard_sha=digest(sources[SOURCE_GUARD]),
                ledger_sha=digest(sources[SOURCE_LEDGER])))
        else:
            blockers.append('CANNOT_VERIFY_SIGNED_SOURCE_BINDING')
    except Exception:
        blockers.append('INDEPENDENT_SIGNED_RELEASE_RECEIPT_ABSENT_OR_INVALID')
    try:
        if command(root, 'rev-parse', 'HEAD') != before:
            blockers.append('GIT_HEAD_DRIFT_DURING_PREFLIGHT')
    except Exception:
        blockers.append('GIT_HEAD_RECHECK_FAILED')
    if mode == 'inspect':
        status = 'INSPECTED_NON_AUTHORIZING' if not blockers else 'BLOCKED_NON_AUTHORIZING'
        allowed = False
    else:
        status = 'PRECHECK_PASS_REQUIRES_INDEPENDENT_WIRING' if not blockers else 'BLOCKED_NON_AUTHORIZING'
        # This candidate's CLI can never authorize a launch; Make remains literal quarantine.
        allowed = False
    return {'schema_version': 'cf10_s01_release_gate_candidate_v0_1',
            'mode': mode, 'status': status, 'blockers': sorted(set(blockers)),
            'checks': checks, 'candidate_preconditions_pass': not bool(blockers),
            'launch_allowed': allowed, 'authority_granted': False,
            'live_make_wiring_performed': False, 'worker_launched': False,
            'canonical_ledger_modified': False}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['inspect', 'preflight'])
    p.add_argument('--root', type=Path, default=Path('.'))
    args = p.parse_args(argv)
    try:
        report = evaluate(args.root, mode=args.mode)
    except Exception as exc:
        report = {'status':'BLOCKED_NON_AUTHORIZING','blockers':['UNEXPECTED_EVALUATOR_ERROR:' + type(exc).__name__],
                  'launch_allowed':False,'authority_granted':False}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    # Never usable as live Make prerequisite; preflight is intentionally 2.
    return 2 if args.mode == 'preflight' else 0


if __name__ == '__main__':
    raise SystemExit(main())
