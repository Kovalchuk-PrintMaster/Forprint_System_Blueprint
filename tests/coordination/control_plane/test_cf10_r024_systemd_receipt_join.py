"""Non-authorizing r024 boundary tests; real systemd is a separate explicit pilot."""
import os
from pathlib import Path
from unittest.mock import patch
import pytest
from scripts.coordination.control_plane import cf10_r024_receipt_systemd_join_v0_1 as bridge
from scripts.coordination.control_plane import cf10_r024_disposable_supervisor_v0_1 as sysd
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipt

HEAD=bridge.PIN
UNIT='forprint-cf10-r024-fixture-abcdef123456.service'
ATTEMPT='cf10-r024fixture-abcdef123456-a024'

def valid():
    return {'schema':'cf10_systemd_disposable_supervisor_gate_r024','head':HEAD,'unit':UNIT,
        'control_group':'/system.slice/'+UNIT,'operator_approval_for_live_worker':False,
        'live_worker_launched':False,'attempt_mutated':False,
        'production_promotion_allowed':False,'process_quiescence_proven_for_production':False,
        'status':'PASS_DISPOSABLE_ONLY_NON_AUTHORIZING','teardown':{'unit_stopped':True,
        'all_sampled_pids_gone':True,'cgroup_empty_or_removed':True,'after_state':'inactive'},
        'start_rc':0,'runner_uid_proven':True,'setsid_child_contained':True,
        'systemd_properties_verified':True,'fixture_started':True,
        'test_directory_removed':True,'parent_pid':1317,'child_pid':1318}

@pytest.mark.parametrize('field,value', [('schema','wrong'),('head','0'*40),('unit','other.service'),
 ('control_group','/system.slice/malicious.service'),('operator_approval_for_live_worker',True),
 ('live_worker_launched',True),('attempt_mutated',True),('production_promotion_allowed',True),
 ('process_quiescence_proven_for_production',True)])
def test_invalid_evidence_blocked(field,value):
    row=valid();row[field]=value
    with pytest.raises(bridge.PilotBlocked):bridge.classify_fixture(row)

@pytest.mark.parametrize('field,value', [('runner_uid_proven',False),('setsid_child_contained',False),
 ('fixture_started',False),('test_directory_removed',False),('status','UNKNOWN'),('start_rc',1),
 ('parent_pid',0),('child_pid',0)])
def test_incomplete_evidence_never_passes(field,value):
    row=valid();row[field]=value
    assert bridge.classify_fixture(row)['disposable_systemd_proven'] is False

def test_pass_still_no_authority():
    output=bridge.classify_fixture(valid())
    assert output['disposable_systemd_proven'] is True
    assert not any(output[k] for k in ('production_quiescence_proven','production_launch_allowed',
                                     'worker_result_accepted','automatic_retry'))

@pytest.mark.skipif(os.geteuid()!=0,reason='Root receipt contract')
def test_consumed_claim_and_join_missing_started(tmp_path):
    parent=tmp_path/'cf10-r024-disposable-test';parent.mkdir(mode=0o700)
    store=parent/'receipts';store.mkdir(mode=0o700)
    probe=tmp_path/'fixed.py';probe.write_text('pass')
    result=bridge.execute_disposable(private_store=store,attempt_id=ATTEMPT,probe=probe,
        systemd_fixture=lambda _probe:valid())
    assert result['status']=='PASS_DISPOSABLE_SYSTEMD_RECEIPT_JOIN_NON_AUTHORIZING'
    assert result['receipt_events']==2
    assert result['join_state']=='BLOCKED_CONSUMED_CLAIM_NO_STARTED_FACT'
    assert result['worker_launched'] is False
    assert receipt.observe(private_store=store,attempt_id=ATTEMPT,expected_head=HEAD)['claim_consumed']
    with pytest.raises(receipt.ReceiptBlocked):
        bridge.execute_disposable(private_store=store,attempt_id=ATTEMPT,probe=probe,
                                  systemd_fixture=lambda _probe:valid())

@pytest.mark.skipif(os.geteuid()!=0,reason='Root receipt contract')
def test_error_consumes_claim_no_retry(tmp_path):
    parent=tmp_path/'cf10-r024-disposable-test';parent.mkdir(mode=0o700)
    store=parent/'receipts';store.mkdir(mode=0o700)
    probe=tmp_path/'fixed.py';probe.write_text('pass')
    result=bridge.execute_disposable(private_store=store,attempt_id=ATTEMPT,probe=probe,
        systemd_fixture=lambda _probe:(_ for _ in ()).throw(OSError('fixture failure')))
    assert result['status']=='BLOCKED_DISPOSABLE_SYSTEMD_UNKNOWN'
    assert result['receipt_events']==2
    assert result['join_state']=='BLOCKED_CONSUMED_CLAIM_NO_STARTED_FACT'

def test_systemd_unit_prefix_and_pinned_head():
    assert sysd.PINNED_HEAD==HEAD
    assert sysd.UNIT_RE.fullmatch(UNIT)
    assert not sysd.UNIT_RE.fullmatch('forprint-cf10-worker-abcdef123456.service')
    assert sysd.UID==996 and sysd.GID==992
    assert sysd.RUNNER=='forprint-runner'

def test_reject_non_disposable_attempt(tmp_path):
    with pytest.raises(bridge.PilotBlocked):
        bridge.execute_disposable(private_store=tmp_path/'receipts',
            attempt_id='cf10-u180j-a049',probe=Path(__file__),
            systemd_fixture=lambda _:valid())
