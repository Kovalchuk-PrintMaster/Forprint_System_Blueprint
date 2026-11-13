"""Fixture-only tests; never read real /etc, run a Worker or write a ledger."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import pytest

P = Path(__file__).with_name('cf10_s01_runtime_rebind_v0_2.py')
if not P.is_file():
    P = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_s01_runtime_rebind_v0_2.py'
spec = importlib.util.spec_from_file_location('cf10_s01_runtime_rebind_v02_tested', P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
HEAD = 'f'*40
WORKER='worker-01'
TASK='cf10-s01-bounded-operator-pilot-v0-1'
ATTEMPT='cf10-u180j-a048'


def good_scope():
    return {'worker_id':WORKER, 'task_prompt_id':TASK, 'attempt_id':ATTEMPT,
            'max_active_workers':1,'max_attempts':1,
            'explicit_operator_dispatch_required':True,
            'automatic_retry_allowed':False,'automatic_accept_allowed':False,
            'route':'GOVERNED_WORKER_CYCLE_ONLY'}


def receipt():
    return {'pilot_scope':good_scope(),
            'signer_id':'independent-release-operator',
            'independent_operator_review_ref':'external-review-100',
            'independent_proofs':{k:'0'*64 for k in gate.REQUIREMENTS}}


def proof(key):
    return {'schema_version':gate.PROOF_SCHEMA,'requirement':key,
            'publication_commit':HEAD,'signer_id':'independent-release-operator',
            'independent_operator_review_ref':'external-review-100',
            'decision':'ACCEPTED', 'evidence':[{'ref':'operator-proof/test-1',
                                            'sha256':'a'*64,'result':'PASS'}]}


def encoded(d):
    return (json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()


def accepted():
    d=receipt()
    files={}
    for k in gate.REQUIREMENTS:
        raw=encoded(proof(k))
        d['independent_proofs'][k] = hashlib.sha256(raw).hexdigest()
        files[k+'.json'] = proof(k), raw
    def reader(p):
        return files[p.name]
    return d,files,reader


def test_all_eight_accepted_proofs():
    d,_,r=accepted()
    assert gate.proof_blockers(d,HEAD,r) == ([],8)


@pytest.mark.parametrize('field', ['schema_version','requirement','publication_commit',
                                   'signer_id','independent_operator_review_ref','decision'])
def test_proof_content_fields_block(field):
    d,files,r=accepted()
    k=gate.REQUIREMENTS[0]
    doc, raw=files[k+'.json']
    doc=dict(doc);doc[field]='other'
    raw=encoded(doc)
    files[k+'.json']=(doc,raw)
    d['independent_proofs'][k]=hashlib.sha256(raw).hexdigest()
    errors,n=gate.proof_blockers(d,HEAD,r)
    assert 'PROOF_CONTENT_NOT_ACCEPTED:'+k in errors
    assert n==7


@pytest.mark.parametrize('problem',['empty','missing_keys','invalid_digest','bad_result','blank_ref'])
def test_unstructured_proof_evidence_blocks(problem):
    d,files,r=accepted();k=gate.REQUIREMENTS[0]
    doc=dict(files[k+'.json'][0]);item=dict(doc['evidence'][0]);
    if problem=='empty':doc['evidence']=[]
    if problem=='missing_keys':item.pop('sha256');doc['evidence']=[item]
    if problem=='invalid_digest':item['sha256']='bad';doc['evidence']=[item]
    if problem=='bad_result':item['result']='FAILED';doc['evidence']=[item]
    if problem=='blank_ref':item['ref']='';doc['evidence']=[item]
    raw=encoded(doc);files[k+'.json']=(doc,raw);d['independent_proofs'][k]=hashlib.sha256(raw).hexdigest()
    errors,n=gate.proof_blockers(d,HEAD,r)
    assert errors == ['PROOF_EVIDENCE_UNSTRUCTURED:'+k]
    assert n==7


def test_proof_bytes_tamper_blocks_even_when_fields_valid():
    d,files,r=accepted();k=gate.REQUIREMENTS[3]
    doc,raw=files[k+'.json'];files[k+'.json']=(doc,raw+b'x')
    errors,n=gate.proof_blockers(d,HEAD,r)
    assert errors==['PROOF_BYTES_MISMATCH:'+k] and n==7


def test_absent_root_controlled_proof_blocks():
    d,files,r=accepted();files.pop(gate.REQUIREMENTS[2]+'.json')
    errors,n=gate.proof_blockers(d,HEAD,r)
    assert errors==['ROOT_CONTROLLED_PROOF_UNAVAILABLE:'+gate.REQUIREMENTS[2]] and n==7


def test_extra_proof_key_blocks():
    d,files,r=accepted();d['independent_proofs']['unknown']='a'*64
    assert gate.proof_blockers(d,HEAD,r)==(['SIGNED_PROOF_MATRIX_INVALID'],0)


def test_missing_proof_key_blocks():
    d,files,r=accepted();d['independent_proofs'].pop(gate.REQUIREMENTS[1])
    assert gate.proof_blockers(d,HEAD,r)==(['SIGNED_PROOF_MATRIX_INVALID'],0)


def test_invalid_matrix_hash_blocks():
    d,files,r=accepted();d['independent_proofs'][gate.REQUIREMENTS[0]]='G'*64
    assert gate.proof_blockers(d,HEAD,r)==(['SIGNED_PROOF_MATRIX_INVALID'],0)


def test_exact_pilot_scope_pass():
    assert gate.scope_blockers(receipt(),worker_id=WORKER,task_prompt_id=TASK,attempt_id=ATTEMPT)==[]


@pytest.mark.parametrize('field,value', [('max_active_workers',True),('max_attempts',2),
    ('automatic_retry_allowed',True),('automatic_accept_allowed',True),
    ('route','DIRECT_PYTHON'),('explicit_operator_dispatch_required',False),
    ('attempt_id','cf10-u180j-a047'),('task_prompt_id','wrong')])
def test_scope_never_widens(field,value):
    d=receipt();d['pilot_scope'][field]=value
    errors=gate.scope_blockers(d,worker_id=WORKER,task_prompt_id=TASK,attempt_id=ATTEMPT)
    assert errors==['SIGNED_PILOT_SCOPE_MISMATCH:'+field]


def test_scope_unknown_key_blocks():
    d=receipt();d['pilot_scope']['unknown']='x'
    assert gate.scope_blockers(d,worker_id=WORKER,task_prompt_id=TASK,
                                attempt_id=ATTEMPT)==['SIGNED_PILOT_SCOPE_INCOMPLETE']


@pytest.mark.parametrize('worker,task,attempt',[('worker-02',TASK,ATTEMPT),
  (WORKER,'../../bad',ATTEMPT),(WORKER,TASK,'/etc/passwd')])
def test_invalid_pilot_inputs_fail_closed(worker,task,attempt):
    assert gate.scope_blockers(receipt(),worker_id=worker,task_prompt_id=task,attempt_id=attempt)==['PILOT_INPUT_INVALID']


def fixture_evaluate(monkeypatch, *, base_ok=True, reread=True, proof_ok=True, stable=True):
    v=receipt()
    baseline={'candidate_preconditions_pass':base_ok,'blockers':[] if base_ok else ['EXPIRED'],
              'checks':{'head':HEAD}}
    monkeypatch.setattr(gate,'_baseline',lambda root:baseline)
    monkeypatch.setattr(gate,'_trusted_json',lambda path:(v,b'fixture'))
    monkeypatch.setattr(gate,'_reverify_receipt',lambda root,h,doc:reread)
    monkeypatch.setattr(gate,'proof_blockers',lambda doc,h:([],8) if proof_ok else (['PROOF_BYTES_MISMATCH:'+gate.REQUIREMENTS[0]],7))
    monkeypatch.setattr(gate,'_head',lambda root:HEAD if stable else '0'*40)
    return gate.evaluate(Path('/tmp/fixture'),worker_id=WORKER,task_prompt_id=TASK,attempt_id=ATTEMPT)


def test_successful_predicate_is_still_non_authorizing(monkeypatch):
    v=fixture_evaluate(monkeypatch)
    assert v['status']=='PREDICATE_PASS_NON_AUTHORIZING'
    assert v['predicate_pass'] is True
    assert all(v[k] is False for k in ['launch_allowed','authority_granted',
                 'single_use_enforced','live_make_wired','worker_launched','ledger_modified'])


def test_failed_activation_blocks_predicate(monkeypatch):
    v=fixture_evaluate(monkeypatch,base_ok=False)
    assert 'EXISTING_SIGNED_RELEASE_AND_ACTIVATION_GATE_BLOCKED' in v['blockers']
    assert v['predicate_pass'] is False


def test_reread_signature_revalidation_is_mandatory(monkeypatch):
    v=fixture_evaluate(monkeypatch,reread=False)
    assert 'SIGNED_RECEIPT_REREAD_CRYPTOGRAPHIC_CHECK_FAILED' in v['blockers']
    assert v['predicate_pass'] is False


def test_missing_proofs_block_predicate(monkeypatch):
    v=fixture_evaluate(monkeypatch,proof_ok=False)
    assert v['checks']['proof_files_verified']==7
    assert v['predicate_pass'] is False


def test_head_drift_blocks_predicate(monkeypatch):
    v=fixture_evaluate(monkeypatch,stable=False)
    assert 'SOURCE_HEAD_CHANGED_DURING_PREDICATE' in v['blockers']


def test_missing_args_never_evaluates_external_authority(monkeypatch):
    monkeypatch.setattr(gate,'_baseline',lambda root:(_ for _ in ()).throw(AssertionError('called')))
    v=gate.evaluate(Path('/tmp/fixture'),worker_id='',task_prompt_id='',attempt_id='')
    assert v['blockers']==['EXPLICIT_PILOT_PARAMETERS_REQUIRED']


def test_launch_cli_never_returns_zero_on_hypothetical_full_pass(monkeypatch):
    monkeypatch.setattr(gate,'evaluate',lambda *args,**kwargs:{'predicate_pass':True,
       'launch_allowed':False,'authority_granted':False})
    assert gate.main(['launch-preflight','--worker-id',WORKER,'--task-prompt-id',TASK,'--attempt-id',ATTEMPT])==2


def test_predicate_check_return_codes(monkeypatch):
    monkeypatch.setattr(gate,'evaluate',lambda *args,**kwargs:{'predicate_pass':True,'launch_allowed':False})
    assert gate.main(['predicate-check'])==0
    monkeypatch.setattr(gate,'evaluate',lambda *args,**kwargs:{'predicate_pass':False,'launch_allowed':False})
    assert gate.main(['predicate-check'])==2


def test_exception_fail_closed(monkeypatch):
    monkeypatch.setattr(gate,'evaluate',lambda *args,**kwargs:(_ for _ in ()).throw(ValueError('private_data')))
    assert gate.main(['predicate-check'])==2


def test_source_has_no_mutating_launch_operation():
    s=P.read_text()
    for bad in ['ledger.append_record(', 'os.system(', 'subprocess.Popen(', 'git push', 'git commit',
                'launch_authorized_worker_cycle(']:
        assert bad not in s

@pytest.mark.parametrize('signature_result', [[], ['RELEASE_SIGNATURE_INVALID']])
def test_second_receipt_read_is_reverified_through_existing_signature_verifier(
        monkeypatch, tmp_path, signature_result):
    import types
    scripts=types.ModuleType('scripts')
    coordination=types.ModuleType('scripts.coordination')
    plane=types.ModuleType('scripts.coordination.control_plane')
    existing=types.ModuleType('scripts.coordination.control_plane.cf10_s01_release_gate_candidate_v0_1')
    existing.RELEASE_TRUST=Path('/fixture/release_trust.json')
    existing.ACTIVATION_DECISION=Path('/fixture/activation.json')
    existing.COVERAGE=Path('/fixture/coverage.json')
    existing.SOURCE_GUARD='guard.py'
    existing.SOURCE_LEDGER='ledger.py'
    existing.command=lambda *args:'git@example.test:org/repo.git'
    calls=[]
    def verifier(*args, **kwargs):
        calls.append(kwargs)
        return signature_result
    existing.verify_release_receipt=verifier
    writer=types.ModuleType('scripts.coordination.execution_attempt_writer_lock_v0_1')
    writer.load_enforced_protocol=lambda *,required:{'sha256':'c'*64}
    plane.cf10_s01_release_gate_candidate_v0_1=existing
    coordination.execution_attempt_writer_lock_v0_1=writer
    scripts.coordination=coordination
    coordination.control_plane=plane
    for name,obj in [('scripts',scripts),('scripts.coordination',coordination),
                     ('scripts.coordination.control_plane',plane),
                     ('scripts.coordination.control_plane.cf10_s01_release_gate_candidate_v0_1',existing),
                     ('scripts.coordination.execution_attempt_writer_lock_v0_1',writer)]:
        monkeypatch.setitem(sys.modules,name,obj)
    (tmp_path/'guard.py').write_bytes(b'guard')
    (tmp_path/'ledger.py').write_bytes(b'ledger')
    monkeypatch.setattr(gate,'_trusted_json',lambda p: ({},b'fixture-authority'))
    assert gate._reverify_receipt(tmp_path,HEAD,receipt()) is (not signature_result)
    assert len(calls)==1
    assert calls[0]['head']==HEAD
    assert calls[0]['remote']=='git@example.test:org/repo.git'
    assert calls[0]['protocol_sha']=='c'*64
    assert calls[0]['guard_sha']==hashlib.sha256(b'guard').hexdigest()
    assert calls[0]['ledger_sha']==hashlib.sha256(b'ledger').hexdigest()
