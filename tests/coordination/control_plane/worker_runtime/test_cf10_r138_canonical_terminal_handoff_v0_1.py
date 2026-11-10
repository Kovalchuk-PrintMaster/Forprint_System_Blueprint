"""R138 source-only readback integration. No root receipt, Worker, or systemd mutation."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import cf10_r138_canonical_terminal_handoff_v0_1 as m

ATTEMPT='cf10-r138case-a138'
HEAD='a'*40
INVOCATION='f'*32
ROOT=Path(__file__).resolve().parents[4]

@pytest.fixture
def scenario(monkeypatch):
    monkeypatch.setattr(m.os, 'geteuid', lambda: 0)
    runtime='/srv/software_development/forprint-worker-runtime'
    spec=binding.BoundedInput('r138-task',ATTEMPT,HEAD,'b'*64,'c'*64,
        f'{runtime}/forprint_system_blueprint/worker-01/{ATTEMPT}/workspace/repo',
        runtime,('/usr/bin/python3','-c','pass'),120)
    unit=binding.unit_for(ATTEMPT,HEAD)
    return spec,unit

def success(unit):
    return dict(systemd_unit=unit,systemd_invocation_id=INVOCATION,outcome='completed',
      return_code=0,timed_out=False,worker_result_accepted=False,automatic_retry=False,
      release_allowed=False,quiescence_observation=m.KERNEL)

def cancelled(unit):
    return dict(state='CANCELLED_KERNEL_ZERO_REVIEW_REQUIRED',unit=unit,
      systemd_invocation_id=INVOCATION,terminal_success=False,
      worker_result_accepted=False,automatic_retry=False,release_allowed=False,
      root_review_recorded=True)

def proof(kind=False):
    return dict(r035_pre_record_sha256='1'*64,
      r035_terminal_record_sha256=None if kind else '2'*64,
      r015_last_receipt_sha256='3'*64,
      ledger_started_sha256='4'*64)

def test_success_root_durable_start_ledger_read_only(monkeypatch,scenario):
    spec,unit=scenario
    calls=[]
    monkeypatch.setattr(m,'_trusted_readback',lambda **kw:(calls.append(kw),proof())[1])
    r=m.review_success(spec=spec,unit=unit,outcome=success(unit))
    assert len(calls)==1 and calls[0]['cancelled'] is False
    assert r['state']=='ROOT_TERMINAL_READY_FOR_INDEPENDENT_RESULT_VERIFIER'
    assert r['r035_terminal_record_sha256']=='2'*64
    assert r['independent_worker_result_verified'] is False
    for k in ('result_accepted','terminal_ledger_written','automatic_retry','release_allowed','launch_allowed','production_cutover_authorized','g1_g5_closed'):
        assert r[k] is False
    assert r['report_sha256']==m._sha({k:v for k,v in r.items() if k!='report_sha256'})

def test_cancellation_keeps_terminal_unrecorded(monkeypatch,scenario):
    spec,unit=scenario
    monkeypatch.setattr(m,'_trusted_readback',lambda **kw:proof(True))
    r=m.review_cancelled(spec=spec,unit=unit,outcome=cancelled(unit))
    assert r['r035_terminal_record_sha256'] is None
    assert r['state']=='QUARANTINE_REVIEW_REQUIRED_NO_TERMINAL_LEDGER'
    assert r['terminal_ledger_written'] is r['result_accepted'] is False

@pytest.mark.parametrize('field,bad',[
    ('return_code',1),('return_code',True),('outcome','failed'),
    ('quiescence_observation','EMPTY_AT_SAMPLE'),('systemd_invocation_id','0'),
    ('release_allowed',True),('worker_result_accepted',True),('automatic_retry',True),
    ('timed_out',True),('systemd_unit','other.service')])
def test_success_forged_result_denied_before_readback(monkeypatch,scenario,field,bad):
    spec,unit=scenario
    monkeypatch.setattr(m,'_trusted_readback',lambda **kw:pytest.fail('no readback on forged input'))
    out=success(unit);out[field]=bad
    with pytest.raises(m.TerminalHandoffHold):m.review_success(spec=spec,unit=unit,outcome=out)

@pytest.mark.parametrize('field,bad',[
    ('terminal_success',True),('root_review_recorded',False),
    ('state','TERMINAL_PASS'),('systemd_invocation_id','e'),
    ('worker_result_accepted',True),('unit','other')])
def test_cancelled_forgery_denied(monkeypatch,scenario,field,bad):
    spec,unit=scenario
    monkeypatch.setattr(m,'_trusted_readback',lambda **kw:pytest.fail('no readback'))
    out=cancelled(unit);out[field]=bad
    with pytest.raises(m.TerminalHandoffHold):m.review_cancelled(spec=spec,unit=unit,outcome=out)

def test_wrong_unit_denied_even_with_valid_outcome(monkeypatch,scenario):
    spec,unit=scenario
    wrong='forprint-cf10-worker-'+'0'*24+'.service'
    with pytest.raises(m.TerminalHandoffHold,match='UNIT_BINDING'):
        m.review_success(spec=spec,unit=wrong,outcome=success(wrong))

def test_nonroot_denied_before_readback(monkeypatch,scenario):
    spec,unit=scenario
    monkeypatch.setattr(m.os,'geteuid',lambda:996)
    with pytest.raises(m.TerminalHandoffHold,match='ROOT_REQUIRED'):
        m.review_success(spec=spec,unit=unit,outcome=success(unit))

def test_bad_proof_digests_denied(monkeypatch,scenario):
    spec,unit=scenario
    bad=proof();bad['r035_pre_record_sha256']='not-sha'
    monkeypatch.setattr(m,'_trusted_readback',lambda **kw:bad)
    with pytest.raises(m.TerminalHandoffHold,match='PROOF_DIGEST_SHAPE'):
        m.review_success(spec=spec,unit=unit,outcome=success(unit))

def test_cross_store_witness_and_ledger_joins_use_existing_readers(monkeypatch,scenario):
    spec,unit=scenario
    from scripts.coordination import control_plane as cp
    from scripts.coordination.control_plane import worker_runtime as wr
    calls=[]
    identity=SimpleNamespace(attempt_id=ATTEMPT)
    monkeypatch.setattr(cp,'cf10_r025_recovery_readback_v0_1',SimpleNamespace(identity_from_source=lambda **kw:identity),raising=False)
    p=proof();pre={'unit':unit,'invocation_id':INVOCATION,'record_sha256':p['r035_pre_record_sha256']}
    post={'unit':unit,'invocation_id':INVOCATION,'pre_record_sha256':p['r035_pre_record_sha256'],
          'record_sha256':p['r035_terminal_record_sha256'],'quiescence_observation':m.KERNEL}
    r035=SimpleNamespace(PRE='pre',POST='post',
       inspect=lambda **kw:dict(state=m.SUCCESS,worker_result_accepted=False,automatic_retry=False),
       _directory=lambda *a:'dir',_read=lambda directory,name:pre if name=='pre' else post)
    monkeypatch.setattr(wr,'cf10_r035_durable_witness_boundary_v0_1',r035,raising=False)
    receipt=dict(attempt_id=ATTEMPT,source_head=HEAD,claim_consumed=True,event_count=0,
       last_digest=p['r015_last_receipt_sha256'],worker_result_accepted=False,
       automatic_retry=False,root_receipt_chain_verified=True)
    monkeypatch.setattr(cp,'cf10_root_lifecycle_receipt_v0_1',
       SimpleNamespace(observe=lambda **kw:receipt),raising=False)
    monkeypatch.setattr(cp,'cf10_receipt_ledger_join_review_v0_1',
       SimpleNamespace(reconcile=lambda **kw:(calls.append(kw),
         dict(state='BLOCKED_STARTED_PENDING_RECOVERY_REQUIRED',
              worker_result_accepted=False,release_allowed=False))[1]),raising=False)
    monkeypatch.setattr(m,'_ledger_pending',lambda x:({'attempt_id':ATTEMPT,'attempt_stage':'STARTED','result_state':'PENDING'},p['ledger_started_sha256']))
    got=m._trusted_readback(spec=spec,unit=unit,invocation=INVOCATION,cancelled=False)
    assert got==p
    assert len(calls)==1 and calls[0]['receipt'] is receipt
    assert calls[0]['ledger_rows'][0]['result_state']=='PENDING'
    post['invocation_id']='e'*32
    with pytest.raises(m.TerminalHandoffHold,match='DURABLE_TERMINAL_BINDING'):
       m._trusted_readback(spec=spec,unit=unit,invocation=INVOCATION,cancelled=False)

def test_cancelled_requires_consecutive_root_review_receipts(monkeypatch,scenario):
    spec,unit=scenario
    from scripts.coordination import control_plane as cp
    from scripts.coordination.control_plane import worker_runtime as wr
    monkeypatch.setattr(cp,'cf10_r025_recovery_readback_v0_1',
       SimpleNamespace(identity_from_source=lambda **kw:SimpleNamespace()),raising=False)
    pre={'unit':unit,'invocation_id':INVOCATION,'record_sha256':'1'*64}
    monkeypatch.setattr(wr,'cf10_r035_durable_witness_boundary_v0_1',SimpleNamespace(
       PRE='pre',POST='post',inspect=lambda **kw:dict(state=m.CANCELLED,worker_result_accepted=False,automatic_retry=False),
       _directory=lambda *a:Path('/fake'),_read=lambda d,n:pre if n=='pre' else None),raising=False)
    n=2
    receipt=dict(attempt_id=ATTEMPT,source_head=HEAD,claim_consumed=True,event_count=n,
       last_digest='3'*64,worker_result_accepted=False,automatic_retry=False,root_receipt_chain_verified=True)
    ev1={'event':'QUIESCENCE_OBSERVED_CANDIDATE','receipt_sha256':'2'*64}
    ev2={'event':'REVIEW_REQUIRED','previous_sha256':'2'*64,'receipt_sha256':'3'*64}
    root=SimpleNamespace(observe=lambda **kw:receipt,_read_json=lambda path:ev1 if path.name=='event_0001.json' else ev2)
    monkeypatch.setattr(cp,'cf10_root_lifecycle_receipt_v0_1',root,raising=False)
    monkeypatch.setattr(cp,'cf10_receipt_ledger_join_review_v0_1',SimpleNamespace(
      reconcile=lambda **kw:dict(state='BLOCKED_STARTED_PENDING_RECOVERY_REQUIRED',worker_result_accepted=False,release_allowed=False)),raising=False)
    monkeypatch.setattr(m,'_ledger_pending',lambda x:({'attempt_id':ATTEMPT,'attempt_stage':'STARTED','result_state':'PENDING'},'4'*64))
    assert m._trusted_readback(spec=spec,unit=unit,invocation=INVOCATION,cancelled=True)['r035_terminal_record_sha256'] is None
    ev2['event']='UNTRUSTED_TERMINAL'
    with pytest.raises(m.TerminalHandoffHold,match='CANCELLATION_REVIEW_NOT_IN_CHAIN'):
       m._trusted_readback(spec=spec,unit=unit,invocation=INVOCATION,cancelled=True)

def test_r030_calls_hooks_after_proof_before_retire_and_never_appends_ledger():
    source=(ROOT/'scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py').read_text()
    tree=ast.parse(source)
    fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_once')
    calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(fun) if isinstance(n,ast.Call)]
    select=lambda f:[n for n,x in calls if x==f]
    assert len(select('handoff.review_success'))==len(select('handoff.review_cancelled'))==1
    assert select('durable.record_terminal')[0]<select('handoff.review_success')[0]<select('_retire_after_durable_terminal')[0]
    assert select('quarantine.quarantine')[0]<select('handoff.review_cancelled')[0]
    assert not any(x.startswith(('ledger.append','receipt.claim')) for _,x in calls)

def test_source_check_keeps_live_gate_off():
    assert m.main(['--mode','source-check']) == 0

@pytest.mark.parametrize('defect', ['none','duplicate','symlink','terminal','name_hash_drift'])
def test_ledger_pending_immutable_fact_negative(monkeypatch,tmp_path,scenario,defect):
    spec,_=scenario
    from scripts import coordination as coord
    import yaml
    base=tmp_path/'blueprint';store=base/'coordination/continuity/execution_attempts'
    store.mkdir(parents=True)
    monkeypatch.setattr(m,'ROOT',base)
    row={'attempt_id':spec.attempt_id,'attempt_stage':'STARTED','result_state':'PENDING',
         'validator_outcome':'NOT_RUN','recorded_at':'2026-11-10T12:00:00Z'}
    hashrow=lambda r:hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
    rowhash=hashrow(row)
    path=store/(spec.attempt_id+'__'+rowhash[:12]+'.yaml')
    fake=SimpleNamespace(load_contract=lambda root:{'storage':{'default_root':'coordination/continuity/execution_attempts'}},
                         validate_record_data=lambda x,c:[],record_digest=hashrow)
    monkeypatch.setattr(coord,'execution_attempt_ledger_v0_1',fake,raising=False)
    if defect!='none':
        path.write_text(yaml.safe_dump(row))
    if defect=='duplicate':
        (store/(spec.attempt_id+'__'+'f'*12+'.yaml')).write_text(yaml.safe_dump(row))
    if defect=='symlink':
        path.unlink();path.symlink_to('/etc/passwd')
    if defect=='terminal':
        row['result_state']='SUCCEEDED';path.write_text(yaml.safe_dump(row))
    if defect=='name_hash_drift':
        row['recorded_at']='2026-11-11T12:00:00Z';path.write_text(yaml.safe_dump(row))
    if defect=='none':
        with pytest.raises(m.TerminalHandoffHold,match='NOT_EXACTLY_ONE_PENDING'):
            m._ledger_pending(spec)
    else:
        with pytest.raises(m.TerminalHandoffHold):m._ledger_pending(spec)

def test_ledger_pending_valid_read_only(monkeypatch,tmp_path,scenario):
    spec,_=scenario
    from scripts import coordination as coord
    import yaml
    store=tmp_path/'coordination/continuity/execution_attempts';store.mkdir(parents=True)
    monkeypatch.setattr(m,'ROOT',tmp_path)
    row={'attempt_id':spec.attempt_id,'attempt_stage':'STARTED','result_state':'PENDING',
         'validator_outcome':'NOT_RUN','recorded_at':'2026-11-10T12:00:00Z'}
    rowhash=lambda r:hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()
    sha=rowhash(row)
    (store/(spec.attempt_id+'__'+sha[:12]+'.yaml')).write_text(yaml.safe_dump(row))
    monkeypatch.setattr(coord,'execution_attempt_ledger_v0_1',SimpleNamespace(
       load_contract=lambda r:{'storage':{'default_root':'coordination/continuity/execution_attempts'}},
       validate_record_data=lambda row,contract:[],record_digest=rowhash),raising=False)
    assert m._ledger_pending(spec)==(row,sha)
