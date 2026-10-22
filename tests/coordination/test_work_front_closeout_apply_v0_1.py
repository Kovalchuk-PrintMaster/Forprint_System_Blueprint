import json
from pathlib import Path
import pytest
import yaml
from scripts.coordination import work_front_closeout_apply_v0_1 as app

@pytest.fixture
def repo(tmp_path):
    (tmp_path/'coordination/internal_work/blueprint/governance').mkdir(parents=True)
    (tmp_path/'coordination/standards/governance').mkdir(parents=True)
    (tmp_path/'coordination/continuity/execution_attempts').mkdir(parents=True)
    registry={'types':[{'document_type':'internal_work','authority_class':'INTERNAL_WORK_NON_AUTHORITY','path_patterns':['coordination/internal_work/**/*']}]}
    (tmp_path/'coordination/standards/governance/document_type_registry_v0_1.yaml').write_text(yaml.safe_dump(registry))
    return tmp_path

def test_out_of_scope_destination_blocked(repo):
    with pytest.raises(app.ApplyError,match='DESTINATION_NOT_REGISTERED_PATH'):
        app._validate_destination(repo,'coordination/continuity/events/a.yaml')

def test_existing_destination_create_only(repo):
    dest='coordination/internal_work/blueprint/governance/2026-10-13__blueprint__slice_completion_v0_1.yaml'
    (repo/dest).write_text('x')
    with pytest.raises(app.ApplyError,match='CREATE_ONLY_TARGET_OCCUPIED'):
        app._validate_destination(repo,dest)

def test_symlink_parent_or_target_fails(repo):
    (repo/'coordination/internal_work/blueprint/governance/2026-10-13__blueprint__fake_completion_v0_1.yaml').symlink_to('/tmp/not-real')
    with pytest.raises(app.ApplyError,match='SYMLINK_PATH_FORBIDDEN'):
        app._validate_destination(repo,'coordination/internal_work/blueprint/governance/2026-10-13__blueprint__fake_completion_v0_1.yaml')

def test_registered_non_authority_type(repo):
    app._validate_doc_registry(repo)

def test_registry_widening_rejected(repo):
    p=repo/'coordination/standards/governance/document_type_registry_v0_1.yaml'
    p.write_text(yaml.safe_dump({'types':[{'document_type':'internal_work','authority_class':'CANONICAL','path_patterns':['coordination/internal_work/**/*']}]}))
    with pytest.raises(app.ApplyError,match='DOCUMENT_TYPE_NOT_REGISTERED'):
        app._validate_doc_registry(repo)

def test_record_not_execution_authority():
    d={'schema_version':app.RECORD_SCHEMA,'layer':'GOVERNANCE_COMPLETION','status':'PASS','authority':{
        'completion_artifact_grants_execution_authority':False,'completion_artifact_grants_dispatch_authority':False},
       'closure':{'whole_work_item_closed':False}}
    app.validate_record(d)
    d['closure']['whole_work_item_closed']=True
    with pytest.raises(app.ApplyError,match='RECORD_SCHEMA_OR_AUTHORITY_INVALID'):
        app.validate_record(d)

def test_no_live_trust_cannot_apply(repo, monkeypatch):
    from scripts.coordination import work_front_closeout_authority_v0_1 as auth
    monkeypatch.setattr(auth,'TRUST_ROOT',repo/'no-trust.json')
    with pytest.raises(auth.AuthorityError,match='INDEPENDENT_TRUST_ROOT_UNAVAILABLE'):
        app.perform_closeout(repo,'tmp/request.json','tmp/decision.json','tmp/manifest.json','tmp/baseline.json')

def test_no_ledger_lock_contract_blocks(repo):
    with pytest.raises(app.ApplyError,match='GLOBAL_WRITER_PROTOCOL_UNAPPROVED'):
        app._check_ledger(repo,{'global_ledger_writer_protocol_approved':False},{},'cf10-u180j-a042')

def test_runtime_roots_must_be_explicit(repo):
    ledger=repo/'coordination/continuity/execution_attempts'
    ledger.joinpath('cf10-u180j-a041__a.yaml').write_text('stage: STARTED')
    ledger.joinpath('cf10-u180j-a041__b.yaml').write_text('stage: BLOCKED')
    import hashlib
    entries={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ledger.iterdir()}
    baseline={'schema_version':'forprint_closeout_ledger_baseline_v0_1','repository_files_sha256':entries,'required_runtime_roots':['/missing']}
    policy={'global_ledger_writer_protocol_approved':True,'required_runtime_roots':['/different']}
    with pytest.raises(app.ApplyError,match='RUNTIME_SCOPE_NOT_AUTHORIZED'):
        app._check_ledger(repo,policy,baseline,'cf10-u180j-a042')

def test_deleted_a041_blocks(repo):
    ledger=repo/'coordination/continuity/execution_attempts'
    baseline={'schema_version':'forprint_closeout_ledger_baseline_v0_1','repository_files_sha256':{'cf10-u180j-a041__a.yaml':'0'*64},'required_runtime_roots':['/missing']}
    policy={'global_ledger_writer_protocol_approved':True,'required_runtime_roots':['/missing']}
    with pytest.raises(app.ApplyError,match='HISTORICAL_LEDGER_DRIFT'):
        app._check_ledger(repo,policy,baseline,'cf10-u180j-a042')

@pytest.fixture
def authorized_transaction(repo, tmp_path, monkeypatch):
    """Independently controlled authority fixture: temp Git and temp ledger."""
    import base64, hashlib, subprocess
    from datetime import datetime, timezone, timedelta
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    from scripts.coordination import work_front_closeout_authority_v0_1 as auth
    def git(*args):
        return subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True).stdout.decode().strip()
    git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.org')
    (repo/'app.py').write_text('x=1\n')
    ledger=repo/'coordination/continuity/execution_attempts'
    (ledger/'cf10-u180j-a041__one.yaml').write_text('attempt_id: cf10-u180j-a041\nattempt_stage: STARTED\n')
    (ledger/'cf10-u180j-a041__two.yaml').write_text('attempt_id: cf10-u180j-a041\nattempt_stage: BLOCKED\n')
    git('add','.');git('commit','-qm','published fixture')
    remote=tmp_path/'r.git'
    subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
    git('remote','add','origin',str(remote)); git('push','-q','origin','HEAD:refs/heads/main')
    commit=git('rev-parse','HEAD')
    def save(path,doc):
        file=repo/path
        file.parent.mkdir(parents=True,exist_ok=True)
        raw=auth.canonical(doc)
        file.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()
    rootsha=hashlib.sha256((repo/'app.py').read_bytes()).hexdigest()
    prefix='coordination/internal_work/blueprint/governance/'
    destination=prefix+'2026-10-13__blueprint__fixture_completion_v0_1.yaml'
    front='tmp/front.json'; frontsha=save(front,{'id':'f'})
    ev='tmp/evidence.json'; evsha=save(ev,{'status':'PASS'})
    plan='tmp/plan.json'; planbody={'schema_version':'forprint_blueprint_work_front_closeout_plan_v0_1',
          'source_state':{'head':commit},'work_front':{'path':front,'id':'wf-fixture','sha256':frontsha},
          'completion_evidence':{'path':ev,'sha256':evsha}, 'implementation_file_sha256':{'app.py':rootsha}}
    plansha=save(plan,planbody)
    candidate='tmp/candidate.json'; csha=save(candidate,{'input_plan':{'sha256':plansha}})
    b2='tmp/b2.json'; b2sha=save(b2,{'review_status':'PASS_NON_AUTHORIZING'})
    request={'schema_version':'forprint_blueprint_work_front_closeout_review_request_v0_1',
      'status':'PENDING_AUTHENTICATED_OPERATOR_APPROVAL_AND_PUBLICATION',
      'request_id':'wf-closeout-fixture','binding':{
        'plan':{'path':plan,'sha256':plansha},'completion_candidate':{'path':candidate,'sha256':csha},
        'b2_observation':{'path':b2,'sha256':b2sha}, 'work_front':planbody['work_front'],
        'completion_evidence':planbody['completion_evidence'],'work_id':'u180j',
        'canonical_destination':destination,'observed_repository_head':commit,
        'forbidden_attempt_id':'cf10-u180j-a042'},
      'acceptance_review':[{'index':1,'criterion':'No dispatch'}], 'authority':{'operator_approved':False}}
    reqpath='tmp/request.json';reqsha=save(reqpath,request)
    manifest={'schema_version':'forprint_closeout_publication_manifest_v0_1','commit':commit,
      'implementation_sha256':{'app.py':rootsha},'frozen_prepublication_file_sha256':{'app.py':rootsha}}
    manpath='tmp/manifest.json';mansha=save(manpath,manifest)
    runtime=tmp_path/'runtime';runtime.mkdir()
    entries={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ledger.iterdir()}
    baseline={'schema_version':'forprint_closeout_ledger_baseline_v0_1','repository_files_sha256':entries,
      'required_runtime_roots':[str(runtime)]}
    basepath='tmp/baseline.json';basesha=save(basepath,baseline)
    key=Ed25519PrivateKey.generate()
    pem=key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    policy={'schema_version':auth.TRUST_SCHEMA,'enabled_for_canonical_apply':True,'trusted_signers':{'fixture':pem},
      'publication_remote':'origin','publication_ref':'refs/heads/main','publication_remote_url':str(remote),'ledger_baseline_sha256':basesha,
      'approved_staged_diff_sha256':hashlib.sha256(b'').hexdigest(),
      'global_ledger_writer_protocol_approved':True,'required_runtime_roots':[str(runtime)]}
    now=datetime.now(timezone.utc)
    decision={'schema_version':auth.DECISION_SCHEMA,'purpose':auth.PURPOSE,'decision':'ACCEPT',
      'request_id':request['request_id'],'request_sha256':reqsha,'destination':destination,
      'work_front_id':'wf-fixture','work_id':'u180j',
      'acceptance':[{'index':1,'criterion_sha256':auth.digest(b'No dispatch'),'accepted':True}],
      'signer_id':'fixture','issued_at':(now-timedelta(minutes=1)).isoformat(),
      'expires_at':(now+timedelta(minutes=10)).isoformat(),
      'nonce':'f'*48,'publication_commit':commit,'publication_remote':'origin',
      'publication_ref':'refs/heads/main','publication_manifest_sha256':mansha,'ledger_baseline_sha256':basesha}
    signature=key.sign(auth.DOMAIN+auth.canonical(decision))
    decision['signature_base64']=base64.b64encode(signature).decode()
    decpath='tmp/decision.json'; save(decpath,decision)
    monkeypatch.setattr(app,'_lock_path',lambda _:tmp_path/'guard.lock')
    return repo,policy,reqpath,decpath,manpath,basepath,destination,runtime

def test_isolated_create_only_positive(authorized_transaction):
    r,policy,req,dec,man,base,dest,runtime=authorized_transaction
    path,record=app.perform_closeout(r,req,dec,man,base,approved_policy=policy)
    assert path==r/dest
    assert record['closure']['whole_work_item_closed'] is False
    assert record['implementation']['published'] is True
    assert record['operator_decision']['signer_id']=='fixture'
    with pytest.raises(app.ApplyError,match='CREATE_ONLY_TARGET_OCCUPIED'):
        app.perform_closeout(r,req,dec,man,base,approved_policy=policy)

def test_forbidden_a042_runtime_blocks_before_write(authorized_transaction):
    r,policy,req,dec,man,base,dest,runtime=authorized_transaction
    (runtime/'cf10-u180j-a042-unauthorized.yaml').write_text('attempt_id: cf10-u180j-a042')
    with pytest.raises(app.ApplyError,match='FORBIDDEN_ATTEMPT_IN_RUNTIME'):
        app.perform_closeout(r,req,dec,man,base,approved_policy=policy)
    assert not (r/dest).exists()

def test_ledger_mutation_blocks_before_write(authorized_transaction):
    r,policy,req,dec,man,base,dest,runtime=authorized_transaction
    (r/'coordination/continuity/execution_attempts/cf10-u180j-a041__two.yaml').write_text('tampered\n')
    with pytest.raises(app.ApplyError,match='HISTORICAL_LEDGER_DRIFT'):
        app.perform_closeout(r,req,dec,man,base,approved_policy=policy)
    assert not (r/dest).exists()

def test_staged_unrelated_change_blocks_before_write(authorized_transaction):
    r,policy,req,dec,man,base,dest,runtime=authorized_transaction
    import subprocess
    (r/'sensitive.txt').write_text('modified')
    subprocess.run(['git','-C',str(r),'add','sensitive.txt'],check=True)
    with pytest.raises(app.ApplyError,match='PROTECTED_STAGING_DRIFT'):
        app.perform_closeout(r,req,dec,man,base,approved_policy=policy)
    assert not (r/dest).exists()
