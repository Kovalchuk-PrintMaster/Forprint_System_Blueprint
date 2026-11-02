"""r023 full fixture transaction matrix; no real supervisor and no project tmp."""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as supervisor
from scripts.coordination.control_plane import cf10_guarded_transaction_v0_1 as tx

HEAD='a'*40
HASH='b'*64
ATTEMPT='cf10-disposablefixture-a901'

class DummyDriver:
    def __init__(self, broken=None):
        self.actions=[]; self.broken=broken
    def start(self, plan, spec):
        self.actions.append('start')
        if self.broken=='start': raise RuntimeError('start failed')
    def stop(self, plan, spec):
        self.actions.append('stop')
        if self.broken=='stop': raise RuntimeError('stop failed')
    def observe(self, plan, spec):
        self.actions.append('observe')
        if self.broken=='observe': raise RuntimeError('observation failed')
        if self.broken=='forged': return {'attempt_id':spec.attempt_id,'source_head':spec.source_head,'worker_result_accepted':True,'production_quiescence_proven':True}
        return {'attempt_id':spec.attempt_id,'source_head':spec.source_head,'worker_result_accepted':False,'production_quiescence_proven':False}

class DummyLedger:
    def __init__(self): self.events=[];self.fail=False
    def started(self, spec):
        if self.fail: raise RuntimeError('ledger append failed')
        self.events.append({'attempt_id':spec.attempt_id,'attempt_stage':'STARTED','result_state':'PENDING','recorded_at':datetime.now(timezone.utc).isoformat()})
    def rows(self, spec): return list(self.events)

@pytest.fixture
def fixture(tmp_path):
    if os.geteuid()!=0:pytest.skip('root-only kernel')
    base=tmp_path/'cf10-r023-disposable-fixture'
    base.mkdir(mode=0o700)
    store=base/'root_receipts'
    store.mkdir(mode=0o700)
    spec=supervisor.BoundedInput('task-forprint-r023',ATTEMPT,HEAD,HASH,'c'*64,
        '/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+ATTEMPT+'/workspace/repo',
        '/srv/software_development/forprint-worker-runtime',('/usr/bin/python3','-V'),10)
    plan=supervisor.bind_plan(spec)
    return tx.FixtureScope(store,base),plan,spec,DummyDriver(),DummyLedger()

def assert_blocked(row):
    assert row['automatic_retry'] is False
    assert row['worker_result_accepted'] is False
    assert row['release_allowed'] is False
    assert row['state'].startswith(('BLOCKED_', 'QUARANTINE_'))

def test_successful_fixture_is_not_release(fixture):
    scope,plan,spec,driver,ledger=fixture
    row=tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    assert row['state']=='BLOCKED_STARTED_PENDING_RECOVERY_REQUIRED'
    assert driver.actions==['start','observe','stop']
    assert_blocked(row)
    with pytest.raises(Exception,match='ALREADY_CONSUMED_NO_RETRY'):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    assert driver.actions==['start','observe','stop']

@pytest.mark.parametrize('step',['after_claim','after_launch_intent','after_start',
  'after_service_observed','after_ledger_started','after_stop','after_quiescence_candidate'])
def test_crash_and_no_retry(step,fixture):
    scope,plan,spec,driver,ledger=fixture
    with pytest.raises(tx.SimulatedCrash,match=step):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger,failpoint=step)
    row=tx.inspection(scope=scope,spec=spec,ledger=ledger)
    assert_blocked(row)
    n=len(driver.actions)
    with pytest.raises(Exception,match='ALREADY_CONSUMED_NO_RETRY'):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    assert len(driver.actions)==n

@pytest.mark.parametrize('fault',['start','stop','observe','forged'])
def test_broken_driver_always_review(fault,fixture):
    scope,plan,spec,driver,ledger=fixture
    driver.broken=fault
    with pytest.raises((RuntimeError,tx.TransactionBlocked)):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    row=tx.inspection(scope=scope,spec=spec,ledger=ledger)
    assert_blocked(row)
    with pytest.raises(Exception,match='ALREADY_CONSUMED_NO_RETRY'):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)

def test_failed_ledger_no_retry(fixture):
    scope,plan,spec,driver,ledger=fixture
    ledger.fail=True
    with pytest.raises(RuntimeError,match='ledger append failed'):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    assert_blocked(tx.inspection(scope=scope,spec=spec,ledger=ledger))
    assert driver.actions[-1]=='stop'

def test_torn_claim_directory_quarantined(fixture):
    scope,plan,spec,driver,ledger=fixture
    (scope.private_store/spec.attempt_id).mkdir(mode=0o700)
    assert tx.inspection(scope=scope,spec=spec,ledger=ledger)['state']=='QUARANTINE_INCOMPLETE_OR_TAMPERED_RECEIPT'
    with pytest.raises(Exception,match='ALREADY_CONSUMED_NO_RETRY'):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)

@pytest.mark.parametrize('fault',['after_claim','after_launch_intent','after_start','after_ledger_started'])
def test_no_tmp_dependency(fault,fixture,monkeypatch):
    scope,plan,spec,driver,ledger=fixture
    monkeypatch.setenv('TMPDIR','/nonexistent-forprint-tmp-forbidden')
    with pytest.raises(tx.SimulatedCrash):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger,failpoint=fault)
    assert_blocked(tx.inspection(scope=scope,spec=spec,ledger=ledger))

def test_wrong_scope_denied(fixture):
    scope,plan,spec,driver,ledger=fixture
    bad=tx.FixtureScope(scope.private_store,Path('/srv/software_development/forprint-worker-runtime')/'cf10-r023-disposable-fixture')
    with pytest.raises(tx.TransactionBlocked):
        tx.execute_fixture(scope=bad,plan=plan,spec=spec,driver=driver,ledger=ledger)

def test_undispatched_plan_denied_before_claim(fixture):
    scope,plan,spec,driver,ledger=fixture
    plan=dict(plan)
    plan['flags']=dict(plan['flags'], authorizing=True)
    with pytest.raises(Exception):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    assert not (scope.private_store/spec.attempt_id).exists()

def test_invalid_failpoint_before_claim(fixture):
    scope,plan,spec,driver,ledger=fixture
    with pytest.raises(tx.TransactionBlocked, match='FAILPOINT'):
        tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger,failpoint='bypass')
    assert not (scope.private_store/spec.attempt_id).exists()

def test_readonly_no_claim(fixture):
    scope,plan,spec,driver,ledger=fixture
    row=tx.inspection(scope=scope,spec=spec,ledger=ledger)
    assert row['state']=='UNCLAIMED_NO_LEDGER_FACT_REVIEW_ONLY'
    assert row['automatic_retry'] is False
    assert not (scope.private_store/spec.attempt_id).exists()

def test_tamper_event_fails_closed(fixture):
    scope,plan,spec,driver,ledger=fixture
    tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    event=scope.private_store/spec.attempt_id/'event_0001.json'
    event.write_text('{"bad":true}\n')
    assert tx.inspection(scope=scope,spec=spec,ledger=ledger)['state']=='QUARANTINE_INCOMPLETE_OR_TAMPERED_RECEIPT'


def test_wrong_handoff_recovery_denied(fixture):
    scope,plan,spec,driver,ledger=fixture
    tx.execute_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    from dataclasses import replace
    other=replace(spec,handoff_sha256='d'*64)
    with pytest.raises(tx.TransactionBlocked,match='CLAIM_HANDOFF_MISMATCH'):
        tx.inspection(scope=scope,spec=other,ledger=ledger)
