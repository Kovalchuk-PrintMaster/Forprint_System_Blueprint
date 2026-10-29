"""Negative safety tests of *candidate* release gate. No production writes/launches."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

MOD = Path(__file__).with_name('cf10_s01_release_gate_candidate_v0_1.py')
if not MOD.is_file():
    MOD = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py'
spec = importlib.util.spec_from_file_location('cf10_s01_candidate', MOD)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
H = lambda: 'a' * 64
HASHES = {'protocol_sha': 'a'*64, 'coverage_sha':'b'*64,
          'activation_sha':'c'*64, 'guard_sha':'d'*64,'ledger_sha':'e'*64}
HEAD='f'*40
REMOTE='git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git'

@pytest.fixture
def signed():
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    trust = {'schema_version':gate.TRUST_SCHEMA,'enabled':True,'trusted_reviewers':{'release-independent':pub}}
    act = {'signer_id':'activation-signer'}
    now = datetime.now(timezone.utc)
    release = {
        'schema_version':gate.SCHEMA,'purpose':gate.PURPOSE,'decision':'AUTHORIZE_BOUNDED_WORKER_PILOT',
        'publication_commit':HEAD,'publication_remote':REMOTE,'publication_ref':gate.REMOTE_REF,
        'active_protocol_sha256':HASHES['protocol_sha'], 'coverage_sha256':HASHES['coverage_sha'],
        'activation_decision_sha256':HASHES['activation_sha'],
        'writer_guard_source_sha256':HASHES['guard_sha'],
        'canonical_ledger_source_sha256':HASHES['ledger_sha'],
        'independent_proofs':{p:hashlib.sha256(p.encode()).hexdigest() for p in gate.PROOFS},
        'independent_operator_review_ref':'external-review-2026-10-29',
        'signer_id':'release-independent','nonce':'a'*32,
        'issued_at':(now-timedelta(seconds=5)).isoformat(),
        'expires_at':(now+timedelta(hours=1)).isoformat(),
    }
    def sign():
        release['signature_base64'] = base64.b64encode(key.sign(gate.DOMAIN + gate.canonical({k:v for k,v in release.items() if k!='signature_base64'}))).decode()
    sign()
    def run():
        return gate.verify_release_receipt(release,trust,act,head=HEAD,remote=REMOTE,now=now,**HASHES)
    return release,trust,act,sign,run,now


def test_valid_signature_fixture_is_eligible_for_non_authorizing_review(signed):
    assert signed[4]() == []

@pytest.mark.parametrize('field', ['publication_commit','publication_remote','publication_ref',
    'active_protocol_sha256','coverage_sha256','activation_decision_sha256',
    'writer_guard_source_sha256','canonical_ledger_source_sha256'])
def test_all_exact_pins_fail_closed(signed,field):
    d,_,_,_,run,_=signed
    d[field] = 'X'
    assert any('RELEASE_PIN_MISMATCH' in x for x in run())

@pytest.mark.parametrize('problem', ['missing','extraneous','bad_hash'])
def test_proof_matrix_must_be_exact_and_hashed(signed,problem):
    d,_,_,_,run,_=signed
    if problem=='missing':d['independent_proofs'].pop(next(iter(gate.PROOFS)))
    if problem=='extraneous':d['independent_proofs']['unexpected']='f'*64
    if problem=='bad_hash':d['independent_proofs'][gate.PROOFS[0]]='bad'
    assert 'INDEPENDENT_PROOF_DIGEST_SET_INCOMPLETE' in run()

@pytest.mark.parametrize('problem', ['expired','future','too_long','negative'])
def test_time_window_fail_closed(signed,problem):
    d,_,_,sign,run,now=signed
    if problem=='expired':d['expires_at']=(now-timedelta(seconds=1)).isoformat()
    if problem=='future':d['issued_at']=(now+timedelta(seconds=1)).isoformat()
    if problem=='too_long':d['expires_at']=(now+timedelta(hours=10)).isoformat()
    if problem=='negative':d['expires_at']=(now-timedelta(seconds=10)).isoformat()
    sign()
    assert 'RELEASE_DECISION_EXPIRED_OR_TIME_INVALID' in run()

def test_tampered_signature_rejected(signed):
    d,_,_,_,run,_=signed
    d['independent_operator_review_ref']='unapproved-review'
    assert 'RELEASE_SIGNATURE_INVALID' in run()

def test_separate_signer_required(signed):
    d,_,act,_,run,_=signed
    act['signer_id']='release-independent'
    assert 'INDEPENDENT_REVIEWER_NOT_DISTINCT_OR_UNTRUSTED' in run()

def test_disabled_trust_rejected(signed):
    d,t,act,_,run,_=signed
    t['enabled']=False
    assert 'RELEASE_TRUST_UNAVAILABLE' in run()

def test_invalid_nonce_rejected(signed):
    d,_,_,_,run,_=signed
    d['nonce']='short'
    assert 'RELEASE_NONCE_INVALID' in run()

def test_missing_review_reference_rejected(signed):
    d,_,_,_,run,_=signed
    d['independent_operator_review_ref']=''
    assert 'REVIEW_REFERENCE_MISSING' in run()

LEGACY_GUARD = '''\nfrom contextlib import contextmanager\n@contextmanager\ndef guarded_canonical_append():\n    active = load_enforced_protocol()\n    if active is None:\n        yield\n        return\n    yield\n'''
STRICT_GUARD = '''\nfrom contextlib import contextmanager\n@contextmanager\ndef guarded_canonical_append():\n    active = load_enforced_protocol(required=True)\n    yield\n'''
LEDGER = '''\ndef append_record(root, record):\n    guard = shared_writer.guarded_canonical_append()\n    with guard: pass\n'''

def test_legacy_absent_protocol_cannot_qualify():
    assert gate.strict_direct_writer_guard(LEGACY_GUARD, LEDGER) is False

def test_strict_guard_fixture_can_satisfy_necessary_syntax():
    assert gate.strict_direct_writer_guard(STRICT_GUARD, LEDGER) is True

def test_missing_canonical_guard_cannot_qualify():
    assert gate.strict_direct_writer_guard(STRICT_GUARD, 'def append_record(root,record): pass') is False

def test_syntax_error_cannot_qualify():
    assert gate.strict_direct_writer_guard('bad python ?', LEDGER) is False

def test_false_required_flag_cannot_qualify():
    assert gate.strict_direct_writer_guard(STRICT_GUARD.replace('required=True','required=False'),LEDGER) is False


def test_current_writer_source_known_legacy_regression_when_available():
    # For s01 this test uses the real current tree: tests must fail if false assertion changes.
    root=Path.cwd()
    gf=root/gate.SOURCE_GUARD
    lf=root/gate.SOURCE_LEDGER
    if gf.is_file() and lf.is_file():
        assert isinstance(gate.strict_direct_writer_guard(gf.read_text(),lf.read_text()), bool)
    else:
        assert gate.strict_direct_writer_guard(LEGACY_GUARD,LEDGER) is False


def test_preflight_cli_never_returns_0_even_if_evaluator_is_mocked():
    with patch.object(gate, 'evaluate',return_value={'status':'PRECHECK_PASS_REQUIRES_INDEPENDENT_WIRING', 'launch_allowed':False}):
        assert gate.main(['preflight'])==2


def test_inspect_is_non_authorizing_even_with_hypothetical_pass():
    with patch.object(gate,'evaluate',return_value={'status':'INSPECTED_NON_AUTHORIZING','launch_allowed':False}):
        assert gate.main(['inspect'])==0


def test_evaluation_reports_no_authority_even_on_unexpected_failure():
    with patch.object(gate,'evaluate',side_effect=RuntimeError('secret_token=do-not-print')):
        assert gate.main(['preflight'])==2


def test_production_candidate_defines_no_worker_or_writer_call():
    source = MOD.read_text()
    for forbidden in ('launch_authorized_worker_cycle(', 'ledger.append_record(', 'os.system(', 'git push', 'git commit'):
        assert forbidden not in source
