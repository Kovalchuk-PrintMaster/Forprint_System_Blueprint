"""Root-only, synthetic in-filesystem tests. No production launch/attempt/release."""
from __future__ import annotations
from pathlib import Path
import os
import json
import pytest
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as review
from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as dur
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kw
from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route

ATT='cf10-r035-durable-a035'
HEAD='a'*40
HAND='b'*64
BASE='c'*64
INV='d'*32
UNIT=bound.unit_for(ATT,HEAD)

def fixture(tmp_path):
    parent=tmp_path/'cf10-r035-fixture-one'
    parent.mkdir()
    store=parent/'receipts';store.mkdir(mode=0o700)
    receipts.claim(private_store=store,attempt_id=ATT,head=HEAD,handoff_sha256=HAND)
    receipts.append_observation(private_store=store,attempt_id=ATT,expected_head=HEAD,event='LAUNCH_REQUESTED')
    spec=bound.BoundedInput('test-task-r035',ATT,HEAD,HAND,BASE,
        '/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+ATT+'/workspace/repo',
        '/srv/software_development/forprint-worker-runtime',('/usr/bin/true',),60)
    ident=review.identity_from_source(attempt_id=ATT,head=HEAD,handoff_sha256=HAND)
    return store,spec,ident

def armed(tmp_path):
    p=tmp_path/'fd-synthetic';p.write_bytes(b'populated 1\n')
    return kw.KernelWitness(UNIT,INV,os.open(p,os.O_RDONLY))

def outcome(**updates):
    d={'systemd_unit':UNIT,'systemd_invocation_id':INV,'return_code':0,
        'outcome':'completed','quiescence_observation':'PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING',
        'worker_result_accepted':False,'automatic_retry':False}
    d.update(updates);return d

def pre(store,spec,w):return dur.record_pre(spec=spec,unit=UNIT,witness=w,store=store,fixture=True)
def post(store,spec):return dur.record_terminal(spec=spec,unit=UNIT,outcome=outcome(),store=store,fixture=True)
def inspect(store,ident,baseline=BASE):return dur.inspect(identity=ident,baseline_sha256=baseline,store=store,fixture=True)

def test_pre_boundary_is_root_owned_immutable_and_fail_closed(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:
        r=pre(store,spec,w)
        assert r['event']=='ARMED_BEFORE_LEDGER_STARTED_AND_RELEASE'
        st=(store/ATT/dur.PRE).lstat()
        assert st.st_uid==0 and st.st_mode & 0o777==0o600
        assert inspect(store,ident)['state']=='BLOCKED_CONTROLLER_INTERRUPTED_OR_TERMINAL_NOT_RECORDED'
        with pytest.raises(dur.DurableBoundaryBlocked,match='ALREADY_EXISTS_NO_RETRY'):pre(store,spec,w)
    finally:w.close()

def test_terminal_boundary_survives_controller_object_loss(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()  # simulation of controller FD loss; no re-arm/retry
    result=post(store,spec)
    assert result['pre_record_sha256']
    restored=inspect(store,ident)
    assert restored['terminal_candidate_recorded'] is True
    assert restored['state'].startswith('TERMINAL_RECORD_PRESENT')
    assert restored['worker_result_accepted'] is False
    assert restored['production_quiescence_proven'] is False
    assert restored['automatic_retry'] is False

def test_no_boundary_without_claim_is_blocked(tmp_path):
    store,spec,ident=fixture(tmp_path)
    with pytest.raises(dur.DurableBoundaryBlocked,match='PRE_BOUNDARY_ABSENT'):
        post(store,spec)
    assert inspect(store,ident)['state']=='BLOCKED_NO_DURABLE_WITNESS_BOUNDARY'

def test_duplicate_terminal_event_never_overwrites(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    post(store,spec)
    with pytest.raises(dur.DurableBoundaryBlocked,match='ALREADY_EXISTS_NO_RETRY'):post(store,spec)

@pytest.mark.parametrize('wrong',[
 {'systemd_invocation_id':'e'*32}, {'return_code':1},{'systemd_unit':'bad'},
 {'outcome':'running'}, {'quiescence_observation':'REMOVED_CGROUP'},
 {'automatic_retry':True}, {'worker_result_accepted':True},
])
def test_terminal_forgery_and_incomplete_evidence_fail_closed(tmp_path,wrong):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    with pytest.raises(dur.DurableBoundaryBlocked,match='TERMINAL_NOT_CANONICAL'):
        dur.record_terminal(spec=spec,unit=UNIT,outcome=outcome(**wrong),store=store,fixture=True)
    assert inspect(store,ident)['terminal_candidate_recorded'] is False

def test_changed_baseline_never_joins(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    with pytest.raises(dur.DurableBoundaryBlocked,match='PRE_BOUNDARY_BINDING'):
        inspect(store,ident,baseline='f'*64)

def test_tampered_pre_file_never_joins(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    p=store/ATT/dur.PRE
    p.write_bytes(p.read_bytes().replace(b'ARMED_BEFORE',b'FORGED_BEFORE'))
    with pytest.raises(dur.DurableBoundaryBlocked,match='ROOT_RECORD_TAMPER'):
        inspect(store,ident)

def test_pre_must_not_be_symlink_or_wrong_mode(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    p=store/ATT/dur.PRE;p.chmod(0o644)
    with pytest.raises(dur.DurableBoundaryBlocked,match='ROOT_RECORD_INODE'):
        inspect(store,ident)
    p.chmod(0o600);p.rename(store/ATT/'saved.json');p.symlink_to(store/ATT/'saved.json')
    with pytest.raises(OSError):inspect(store,ident)

def test_post_without_pre_is_quarantined(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    post(store,spec)
    (store/ATT/dur.PRE).unlink()
    with pytest.raises(dur.DurableBoundaryBlocked,match='TERMINAL_WITHOUT_PRE'):inspect(store,ident)

def test_root_claim_corruption_blocks(tmp_path):
    store,spec,ident=fixture(tmp_path)
    (store/ATT/'0000_claim.json').write_text('{}')
    with pytest.raises(dur.DurableBoundaryBlocked,match='ROOT_CLAIM_INVALID'):inspect(store,ident)

def test_production_store_not_caller_overridable(tmp_path):
    store,spec,ident=fixture(tmp_path)
    with pytest.raises(dur.DurableBoundaryBlocked,match='PRODUCTION_STORE_PIN'):
        dur.inspect(identity=ident,baseline_sha256=BASE,store=store)

def test_join_r025_non_authorizing_even_with_terminal_record(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    post(store,spec)
    summ=receipts.observe(private_store=store,attempt_id=ATT,expected_head=HEAD)
    d=dur.join_review(identity=ident,baseline_sha256=BASE,receipt_summary=summ,
        ledger_rows=[],service=None,claim_path_occupied=True,store=store,fixture=True)
    assert d['state']=='BLOCKED_TERMINAL_CANDIDATE_PENDING_INDEPENDENT_CROSS_BOUNDARY_VERIFICATION'
    assert d['manual_review_required'] is True and d['launch_allowed'] is False

def test_active_unit_overrides_terminal_candidate(tmp_path):
    store,spec,ident=fixture(tmp_path);w=armed(tmp_path)
    try:pre(store,spec,w)
    finally:w.close()
    post(store,spec)
    summ=receipts.observe(private_store=store,attempt_id=ATT,expected_head=HEAD)
    service=dict(unit=UNIT,attempt_id=ATT,source_head=HEAD,load_state='loaded',
        active_state='active',main_pid=12345,control_group='/system.slice/'+UNIT,
        user='forprint-runner',group='forprint-runner',kill_mode='control-group',
        provenance='ROOT_SYSTEMCTL_SHOW_READBACK')
    d=dur.join_review(identity=ident,baseline_sha256=BASE,receipt_summary=summ,
        ledger_rows=[],service=service,claim_path_occupied=True,store=store,fixture=True)
    assert d['state']=='BLOCKED_PROCESS_MAY_STILL_BE_RUNNING'
    assert d['release_allowed'] is False

def test_source_route_persists_before_started_and_after_terminal():
    src=Path(route.__file__).read_text()
    assert src.index('witness.arm(')<src.index('durable.record_pre(')<src.index('started_callback(record)')
    assert src.index('terminal.witnessed_terminal(')<src.index('durable.record_terminal(')
    assert 'LIVE_CUTOVER_ENABLED = True' not in src
