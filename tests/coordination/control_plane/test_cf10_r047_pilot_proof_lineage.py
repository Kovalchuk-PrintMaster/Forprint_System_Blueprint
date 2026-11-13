"""r047: real raw source bytes are mandatory before r046 candidate verification."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import pytest

from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
from scripts.coordination.control_plane import cf10_r047_pilot_proof_lineage_v0_1 as r047

HEAD = '3' * 40
ATTEMPT = 'cf10-u180j-a053'
TASK = r046.TASK70


def serial(doc):
    return (json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()


def raw_record(kind, **updates):
    doc = dict(
        schema_version=r047.SCHEMA, status=r047.STATUS, proof_type=kind,
        source_head=HEAD, task_prompt_id=TASK, attempt_id=ATTEMPT, worker_id=r046.WORKER,
        production_worker_launched=False, automatic_retry=False,
        scope=('READ_ONLY_EXACT_ATTEMPT' if kind == 'SOURCE_AND_WRITER_BOUNDARY'
               else 'DISPOSABLE_NON_AUTHORIZING'),
        observations={k: True for k in r047.REQUIRED_OBSERVATIONS[kind]},
    )
    doc.update(updates)
    return doc


def fixture():
    raw = {r047.raw_name(kind, ATTEMPT): serial(raw_record(kind)) for kind in r046.PROOF_TYPES}
    proofs = {kind: {'source_evidence_sha256': hashlib.sha256(raw[r047.raw_name(kind, ATTEMPT)]).hexdigest()}
              for kind in r046.PROOF_TYPES}
    def read(_, name): return raw[name]
    return raw, proofs, read


def verify(proofs, read):
    return r047.verify_sources(folder_fd=6, proofs=proofs, head=HEAD, task=TASK,
                               attempt=ATTEMPT, worker=r046.WORKER,
                               read=read, decode=r046._json_checked)


def test_all_four_actual_source_bytes_required_and_bound():
    _,p,reader=fixture()
    assert verify(p,reader) == []
    assert all(r047.raw_name(k,ATTEMPT).endswith(k.lower()+'.json') for k in r046.PROOF_TYPES)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_missing_raw_source_never_accepted(kind):
    raw,p,reader=fixture();del raw[r047.raw_name(kind,ATTEMPT)]
    assert 'RAW_SOURCE_NOT_AVAILABLE:'+kind in verify(p,lambda _, name: raw[name])

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_tampering_or_stale_raw_source_sha_rejected(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    raw[name]=raw[name].replace(b'PASS_NON_AUTHORIZING',b'FAKE_NON_AUTHORIZING')
    assert 'RAW_SOURCE_SHA256_MISMATCH:'+kind in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_raw_source_wrong_head_even_with_rehashed_proof(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    d=json.loads(raw[name]);d['source_head']='4'*40
    raw[name]=serial(d);p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_SCOPE_MISMATCH:'+kind+':source_head' in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_raw_source_wrong_attempt_even_with_rehashed_proof(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    d=json.loads(raw[name]);d['attempt_id']='cf10-u180j-a099'
    raw[name]=serial(d);p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_SCOPE_MISMATCH:'+kind+':attempt_id' in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_false_observation_rejected_even_when_digests_match(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    d=json.loads(raw[name]);first=next(iter(d['observations']));d['observations'][first]=False
    raw[name]=serial(d);p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_UNVERIFIED_OUTCOME:'+kind in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_missing_observation_rejected_even_when_digests_match(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    d=json.loads(raw[name]);d['observations'].pop(next(iter(d['observations'])))
    raw[name]=serial(d);p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_EXACT_OBSERVATIONS_REQUIRED:'+kind in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_production_worker_flag_rejected_even_when_digests_match(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    d=json.loads(raw[name]);d['production_worker_launched']=True
    raw[name]=serial(d);p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_SCOPE_MISMATCH:'+kind+':production_worker_launched' in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_duplicate_json_key_fails_closed(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    raw[name]=raw[name].replace(b'"status":', b'"status":"FAKE","status":')
    p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_INVALID_JSON_OR_DUPLICATE_KEYS:'+kind in verify(p,reader)

@pytest.mark.parametrize('kind',r046.PROOF_TYPES)
def test_extra_raw_field_rejected(kind):
    raw,p,reader=fixture();name=r047.raw_name(kind,ATTEMPT)
    d=json.loads(raw[name]);d['quietly_authorize']=True
    raw[name]=serial(d);p[kind]['source_evidence_sha256']=hashlib.sha256(raw[name]).hexdigest()
    assert 'RAW_SOURCE_EXACT_FIELDS_REQUIRED:'+kind in verify(p,reader)


def test_missing_proofs_map_rejected():
    raw,p,reader=fixture();del p[r046.PROOF_TYPES[0]]
    assert verify(p,reader)==['RAW_SOURCE_PROOFS_INCOMPLETE']

@pytest.mark.parametrize('bad',[None,'bad',{},True, 'cf10-u180j-a1', '../../x'])
def test_raw_name_cannot_escape_or_expand_scope(bad):
    with pytest.raises(ValueError):r047.raw_name(r046.PROOF_TYPES[0],bad)


def test_no_widening_of_r046_authority():
    text=Path(r046.__file__).read_text()
    assert 'lineage.verify_sources(' in text
    assert "'launch_allowed': False" in text
    assert "'production_cutover': False" in text
    assert not hasattr(r047,'launch')
    assert not hasattr(r047,'authorize')
    assert not hasattr(r047,'write_proofs')


def test_integration_with_r046_inspect_blocks_absent_raw_bytes(monkeypatch):
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as admission
    monkeypatch.setattr(console,'source_guard',lambda _: HEAD)
    monkeypatch.setattr(admission,'collect',lambda root,task,attempt:{'preclaim_evidence_complete':True,'status':'PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING'})
    monkeypatch.setattr(r046,'_trusted_folder',lambda _: os.open('/dev/null',os.O_RDONLY))
    raw,p,_=fixture()
    proof_docs={}
    for kind in r046.PROOF_TYPES:
        doc={
            'schema_version':r046.PROOF_SCHEMA,'status':'VERIFIED_TECHNICAL_EVIDENCE',
            'proof_type':kind,'source_head':HEAD,'task_prompt_id':TASK,'attempt_id':ATTEMPT,
            'worker_id':r046.WORKER,
            'fixture_only':kind in r046.PROOF_TYPES[:3],
            'production_worker_launched':False,'independently_reviewed':True,
            'source_evidence_sha256':p[kind]['source_evidence_sha256'],
        }
        proof_docs[kind]=doc
    release={
      'schema_version':r046.RELEASE_SCHEMA,'status':'EXPLICIT_OWNER_PILOT_CANDIDATE_NON_AUTHORIZING',
      'profile':'SINGLE_OWNER_BOUNDED_TASK70','owner':'forprint_system_blueprint','worker_id':r046.WORKER,
      'task_prompt_id':TASK,'attempt_id':ATTEMPT,'source_head':HEAD,
      'automatic_retry':False,'automatic_acceptance':False,'automatic_publication':False,
      'legacy_signed_release_replaced':False,'independent_human_signer_required':False,
      'root_owned_one_shot_claim_required':True,'pam_operator_confirmation_required':True,'strict_finalizer_required':True,
      'proofs':{k:{'sha256':hashlib.sha256(serial(v)).hexdigest(),
                   'relative_file':r046._proof_name(k,ATTEMPT)} for k,v in proof_docs.items()},
    }
    contents={'owner_pilot_release_'+r046._attempt_key(ATTEMPT)+'.json':serial(release)}
    contents.update({r046._proof_name(k,ATTEMPT):serial(v) for k,v in proof_docs.items()})
    contents.update(raw)
    monkeypatch.setattr(r046,'_trusted_file',lambda fd,name:contents[name])
    out=r046.inspect(root=r046.ROOT if hasattr(r046,'ROOT') else Path('/srv/software_development/forprint-project/forprint_system_blueprint'),
                     task=TASK,attempt=ATTEMPT)
    assert out['status']=='PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED'
    assert out['launch_allowed'] is False
    del contents[r047.raw_name(r046.PROOF_TYPES[0],ATTEMPT)]
    out=r046.inspect(root=Path('/srv/software_development/forprint-project/forprint_system_blueprint'),task=TASK,attempt=ATTEMPT)
    assert out['status']=='BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE'
    assert 'RAW_SOURCE_NOT_AVAILABLE:'+r046.PROOF_TYPES[0] in out['blockers']
