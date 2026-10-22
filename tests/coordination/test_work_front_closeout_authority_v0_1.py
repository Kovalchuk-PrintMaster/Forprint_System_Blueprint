from datetime import datetime, timedelta, timezone
import base64
import hashlib
import pytest

from scripts.coordination import work_front_closeout_authority_v0_1 as a

@pytest.fixture
def signed():
    cryptography = pytest.importorskip('cryptography')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    key = Ed25519PrivateKey.generate()
    pem = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    request = {'schema_version':'forprint_blueprint_work_front_closeout_review_request_v0_1','request_id':'wf-closeout-test',
               'binding': {'canonical_destination':'coordination/internal_work/blueprint/governance/test.yaml',
                           'work_front':{'id':'wf-test'}, 'work_id':'u180j'},
               'acceptance_review':[{'index':1, 'criterion':'No dispatch'}, {'index':2,'criterion':'No ledger mutation'}],
               'authority':{'operator_approved':False}}
    raw=a.canonical(request)
    now=datetime.now(timezone.utc)
    policy={'schema_version':a.TRUST_SCHEMA, 'enabled_for_canonical_apply':True, 'trusted_signers':{'alice':pem},
            'publication_remote':'origin','publication_ref':'refs/heads/main','ledger_baseline_sha256':'b'*64}
    decision={'schema_version':a.DECISION_SCHEMA,'purpose':a.PURPOSE,'decision':'ACCEPT',
              'request_id':request['request_id'],'request_sha256':a.digest(raw),
              'destination':request['binding']['canonical_destination'], 'work_front_id':'wf-test','work_id':'u180j',
              'acceptance':[{'index':r['index'],'criterion_sha256':a.digest(r['criterion'].encode()),'accepted':True} for r in request['acceptance_review']],
              'signer_id':'alice','issued_at':(now-timedelta(minutes=1)).isoformat(), 'expires_at':(now+timedelta(minutes=10)).isoformat(),
              'nonce':'0'*40,'publication_commit':'a'*40,'publication_remote':'origin','publication_ref':'refs/heads/main',
              'publication_manifest_sha256':'1'*64,'ledger_baseline_sha256':'b'*64}
    def resign():
        decision['signature_base64']=base64.b64encode(key.sign(a.DOMAIN+a.canonical({k:v for k,v in decision.items() if k!='signature_base64'}))).decode()
    resign()
    return request,raw,decision,policy,resign

def test_valid_separate_signed_decision(signed):
    request, raw, dec, pol, _ = signed
    assert a.verify_signed_decision(request,raw,dec,pol)['signer_id']=='alice'

@pytest.mark.parametrize('tamper,expected',[('launch','CLOSEOUT_DECISION_SCHEMA_OR_PURPOSE_INVALID'),('request','REQUEST_BINDING_DRIFT'),('criterion','ACCEPTANCE_DECISION_MISMATCH'),('destination','DECISION_BINDING_DRIFT'),('remote','PUBLICATION_POLICY_MISMATCH'),('expired','APPROVAL_EXPIRED_OR_UNBOUNDED'),('signer','SIGNER_NOT_TRUSTED'),('fake_signature','SIGNATURE_INVALID'),('unsigned','SIGNATURE_MISSING'),('ledger','LEDGER_POLICY_MISMATCH')])
def test_signed_decision_fail_closed(signed,tamper,expected):
    request,raw,dec,pol,resign=signed
    if tamper=='launch': dec['purpose']='WORKER_LAUNCH'
    elif tamper=='request': dec['request_sha256']='f'*64
    elif tamper=='criterion': dec['acceptance'][1]['accepted']=False
    elif tamper=='destination': dec['destination']='evil.yaml'
    elif tamper=='remote': dec['publication_ref']='refs/heads/other'
    elif tamper=='expired': dec['expires_at']='2020-01-01T00:00:00+00:00'
    elif tamper=='signer': dec['signer_id']='unknown'
    elif tamper=='fake_signature': dec['signature_base64']=base64.b64encode(b'x'*64).decode()
    elif tamper=='unsigned': dec.pop('signature_base64')
    elif tamper=='ledger': dec['ledger_baseline_sha256']='0'*64
    with pytest.raises(a.AuthorityError,match=expected): a.verify_signed_decision(request,raw,dec,pol)

def test_signature_cannot_be_reused_for_changed_decision(signed):
    request,raw,dec,pol,_=signed
    dec['nonce']='a'*40
    with pytest.raises(a.AuthorityError,match='SIGNATURE_INVALID'): a.verify_signed_decision(request,raw,dec,pol)

def test_no_trust_enrollment_from_repo(tmp_path,monkeypatch):
    monkeypatch.setattr(a,'TRUST_ROOT',tmp_path/'nonexistent.json')
    with pytest.raises(a.AuthorityError,match='INDEPENDENT_TRUST_ROOT_UNAVAILABLE'): a.load_system_trust_root()

def test_noncanonical_request_rejected(signed):
    request,raw,dec,pol,_=signed
    with pytest.raises(a.AuthorityError,match='REQUEST_NONCANONICAL'):
        a.verify_signed_decision(request,raw+b' ',dec,pol)
