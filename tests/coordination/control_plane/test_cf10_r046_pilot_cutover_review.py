"""Source-native r046 release-candidate checks; no root operations or live launches."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as g

HEAD='a'*40
ATTEMPT='cf10-u180j-a050'

def _bytes(doc):
    return (json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=False)+'\n').encode()


def valid():
    proofs={}
    bindings={}
    for i,kind in enumerate(g.PROOF_TYPES):
        doc={
            'schema_version':g.PROOF_SCHEMA,'status':'VERIFIED_TECHNICAL_EVIDENCE',
            'proof_type':kind,'source_head':HEAD,'task_prompt_id':g.TASK70,
            'attempt_id':ATTEMPT,'worker_id':g.WORKER,
            'fixture_only':kind in ('DISPOSABLE_SYSTEMD_CONTROLLER_LOSS_RECOVERY',
                                    'TMP_UNAVAILABLE_END_TO_END',
                                    'INDEPENDENT_FINALIZER_GATE_FIXTURE'),
            'production_worker_launched':False,'independently_reviewed':True,
            'source_evidence_sha256':str(i+1)*64,
        }
        proofs[kind]=doc
        bindings[kind]={'sha256':hashlib.sha256(_bytes(doc)).hexdigest(),
                        'relative_file':g._proof_name(kind, ATTEMPT)}
    release={
        'schema_version':g.RELEASE_SCHEMA,
        'status':'EXPLICIT_OWNER_PILOT_CANDIDATE_NON_AUTHORIZING',
        'profile':'SINGLE_OWNER_BOUNDED_TASK70','owner':'forprint_system_blueprint',
        'worker_id':g.WORKER,'task_prompt_id':g.TASK70,'attempt_id':ATTEMPT,
        'source_head':HEAD,'automatic_retry':False,'automatic_acceptance':False,
        'automatic_publication':False,'legacy_signed_release_replaced':False,
        'independent_human_signer_required':False,
        'root_owned_one_shot_claim_required':True,
        'pam_operator_confirmation_required':True,
        'strict_finalizer_required':True,'proofs':bindings,
    }
    return release,proofs


def errors(release,proofs,head=HEAD,task=g.TASK70,attempt=ATTEMPT):
    return g.validate_candidate(release,proofs,head=head,task=task,attempt=attempt)


def test_valid_is_only_non_authorizing_proof_candidate():
    r,p=valid()
    assert errors(r,p)==[]
    text=Path(g.__file__).read_text()
    assert 'launch_allowed\': False' in text
    assert 'production_cutover\': False' in text
    assert not hasattr(g, 'authorize')
    assert not hasattr(g, 'launch')

@pytest.mark.parametrize('key,bad',[
    ('schema_version','faked'),('status','AUTHORIZED'),('profile','BROAD'),
    ('owner','other'),('worker_id','worker-02'),('task_prompt_id','unknown'),
    ('attempt_id','cf10-u180j-a999'),('source_head','f'*40),
    ('automatic_retry',True),('automatic_acceptance',True),
    ('automatic_publication',True),('legacy_signed_release_replaced',True),
    ('independent_human_signer_required',True),('root_owned_one_shot_claim_required',False),
    ('pam_operator_confirmation_required',False),('strict_finalizer_required',False),
])
def test_rejects_widened_or_changed_release_field(key,bad):
    r,p=valid();r[key]=bad
    assert errors(r,p)

@pytest.mark.parametrize('identity',[
    ('f'*40,g.TASK70,ATTEMPT),
    (HEAD,'other-task',ATTEMPT),
    (HEAD,g.TASK70,'cf10-u180j-a051'),
    ('bad',g.TASK70,ATTEMPT),
    (HEAD,g.TASK70,'../../escape'),
])
def test_rejects_different_scope(identity):
    r,p=valid()
    assert errors(r,p,head=identity[0],task=identity[1],attempt=identity[2])

@pytest.mark.parametrize('kind',g.PROOF_TYPES)
def test_proof_missing(kind):
    r,p=valid();del p[kind]
    assert errors(r,p)

@pytest.mark.parametrize('kind',g.PROOF_TYPES)
def test_proof_tampered_after_digest(kind):
    r,p=valid();p[kind]['source_evidence_sha256']='e'*64
    assert any('PROOF_BYTES_SHA_MISMATCH:' in x for x in errors(r,p))

@pytest.mark.parametrize('field,bad',[
    ('status','AUTHORIZE'),('source_head','b'*40),('worker_id','worker-09'),
    ('attempt_id','cf10-u180j-a099'),('independently_reviewed',False),
    ('production_worker_launched',True),('fixture_only',False),
    ('source_evidence_sha256','0'),
])
def test_proof_bad_semantics(field,bad):
    r,p=valid();p[g.PROOF_TYPES[0]][field]=bad
    assert errors(r,p)

def test_duplicate_release_proof_binding_rejected():
    r,p=valid();a,b=g.PROOF_TYPES[:2];r['proofs'][b]['sha256']=r['proofs'][a]['sha256']
    assert 'DUPLICATE_PROOF_DIGEST' in errors(r,p)

def test_filename_not_retargetable():
    r,p=valid();r['proofs'][g.PROOF_TYPES[0]]['relative_file']='../../bad'
    assert errors(r,p)

def test_extra_release_field_rejected():
    r,p=valid();r['worker_count']=500
    assert 'EXACT_RELEASE_FIELDS_REQUIRED' in errors(r,p)

def test_missing_proof_schema_rejected():
    r,p=valid();p[g.PROOF_TYPES[0]].pop('schema_version')
    assert errors(r,p)

def test_missing_release_rejected():
    r,p=valid();assert errors(None,p)

def test_inspect_reports_non_authorization_on_missing_root_evidence():
    # In an isolated root, no production path may be accessed or created.
    out=g.inspect(root=Path('/a/noncanonical/root'),task=g.TASK70,attempt=ATTEMPT)
    assert out['status']=='BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE'
    assert out['launch_allowed'] is False
    assert out['production_cutover'] is False
    assert out['worker_launched'] is False


def test_requirements_is_non_authorizing_contract_only(capsys):
    assert g.main(['requirements'])==0
    payload=json.loads(capsys.readouterr().out)
    assert len(payload['required_proof_types'])==4
    assert payload['production_cutover'] is False
    assert '/tmp' not in payload['release_root']


def test_inspect_no_file_authority_without_root_owned_source(monkeypatch):
    # The exact canonical path cannot be created by this review module.
    called=[]
    def denied(_):
        called.append('checked');raise g.CutoverReviewBlocked('ROOT_NOT_PROVEN')
    monkeypatch.setattr(g,'_trusted_folder',denied)
    out=g.inspect(root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'),
                  task=g.TASK70,attempt=ATTEMPT)
    assert called==['checked']
    assert 'DURABLE_PILOT_PROOF_OR_RELEASE_UNAVAILABLE' in out['blockers']
    assert not out['launch_allowed']

def test_inspect_verified_proofs_remain_non_authorizing(monkeypatch):
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    r,p=valid()
    monkeypatch.setattr(console,'source_guard',lambda root: HEAD)
    monkeypatch.setattr(admission,'collect',lambda root,task,attempt:{
        'preclaim_evidence_complete':True,'status':'PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING'})
    monkeypatch.setattr(g,'_trusted_folder',lambda _: __import__('os').open('/dev/null',__import__('os').O_RDONLY))
    # This pre-r047 test exercises r046 release binding only; raw source checks
    # have their own negative/positive test suite in r047.
    from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as lineage
    monkeypatch.setattr(lineage, 'verify_sources', lambda **_: [])
    contents={'owner_pilot_release_'+g._attempt_key(ATTEMPT)+'.json': _bytes(r)}
    contents.update({g._proof_name(kind,ATTEMPT):_bytes(doc) for kind,doc in p.items()})
    monkeypatch.setattr(g,'_trusted_file',lambda fd,name: contents[name])
    result=g.inspect(root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'),
                     task=g.TASK70,attempt=ATTEMPT)
    assert result['status']=='PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED'
    assert result['blockers']==[]
    assert result['launch_allowed'] is False
    assert result['production_cutover'] is False
    assert result['worker_launched'] is False


def test_rejects_duplicate_json_keys():
    with pytest.raises(g.CutoverReviewBlocked, match='DUPLICATE_JSON_KEY'):
        g._json_checked(b'{"x":1,"x":2}')
