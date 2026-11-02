"""r036 read-only cross-boundary finalizer candidate and crash/reboot matrix."""
from __future__ import annotations
import json
from pathlib import Path
import os
import pytest
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as recovery
from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as durable
from scripts.coordination.control_plane.worker_runtime import cf10_r036_independent_result_crosscheck_v0_1 as r
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kw

ATT='cf10-r036-candidate-a036';HEAD='a'*40;HAND='b'*64;BASE='c'*64;INV='d'*32
UNIT=bound.unit_for(ATT,HEAD)

def fixture(tmp_path):
    d=tmp_path/'cf10-r035-fixture-r036';d.mkdir()
    store=d/'receipts';store.mkdir(mode=0o700)
    receipts.claim(private_store=store,attempt_id=ATT,head=HEAD,handoff_sha256=HAND)
    receipts.append_observation(private_store=store,attempt_id=ATT,expected_head=HEAD,event='LAUNCH_REQUESTED')
    spec=bound.BoundedInput('test-task-r036',ATT,HEAD,HAND,BASE,
        '/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+ATT+'/workspace/repo',
        '/srv/software_development/forprint-worker-runtime',('/usr/bin/true',),60)
    ident=recovery.identity_from_source(attempt_id=ATT,head=HEAD,handoff_sha256=HAND)
    attempt=tmp_path/ATT;attempt.mkdir();(attempt/'result').mkdir(mode=0o700)
    summary=receipts.observe(private_store=store,attempt_id=ATT,expected_head=HEAD)
    ledger=[dict(attempt_id=ATT,attempt_stage='STARTED',result_state='PENDING',
                 recorded_at='2026-11-02T10:00:00Z')]
    service=dict(unit=UNIT,attempt_id=ATT,source_head=HEAD,load_state='not-found',
        active_state='inactive',main_pid=0,control_group='',user='',group='',kill_mode='',
        provenance='ROOT_SYSTEMCTL_SHOW_READBACK')
    result=dict(attempt_id=ATT,status='PASS',handoff_manifest_sha256=HAND,changed_paths=[])
    (attempt/'result'/'worker_result.yaml').write_text(json.dumps(result)+'\n')
    (attempt/'result'/'worker_result.yaml').chmod(0o600)
    options=dict(identity=ident,baseline_sha256=BASE,attempt_root=attempt,
        origin_manifest={'handoff_manifest_sha256':HAND},
        governed_worker_context={'handoff_manifest_sha256':HAND},
        receipt_summary=summary,ledger_rows=ledger,service=service,claim_path_occupied=True,
        envelope_validator=lambda *args:[],resume_validator=lambda *args:[],store=store,fixture=True)
    return store,spec,ident,attempt,options

def complete(tmp_path,store,spec):
    src=tmp_path/'cgroup-fixture';src.write_bytes(b'populated 1\n')
    w=kw.KernelWitness(UNIT,INV,os.open(src,os.O_RDONLY))
    try:durable.record_pre(spec=spec,unit=UNIT,witness=w,store=store,fixture=True)
    finally:w.close()
    durable.record_terminal(spec=spec,unit=UNIT,store=store,fixture=True,outcome={
        'systemd_unit':UNIT,'systemd_invocation_id':INV,'return_code':0,'outcome':'completed',
        'quiescence_observation':'PINNED_KERNEL_1_TO_0_RETAINED_SYSTEMD_NON_AUTHORIZING',
        'worker_result_accepted':False,'automatic_retry':False})

def test_missing_terminal_after_controller_death_quarantines(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path)
    assert r._assess(**opts)['status']=='BLOCKED_TERMINAL_NOT_DURABLE'
    src=tmp_path/'fd';src.write_text('populated 1\n')
    w=kw.KernelWitness(UNIT,INV,os.open(src,os.O_RDONLY))
    try:durable.record_pre(spec=spec,unit=UNIT,witness=w,store=store,fixture=True)
    finally:w.close()
    o=r._assess(**opts)
    assert o['status']=='BLOCKED_TERMINAL_NOT_DURABLE' and o['automatic_retry'] is False
    assert o['worker_result_accepted'] is False and o['release_allowed'] is False

def test_complete_cross_boundaries_are_candidate_only(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    out=r._assess(**opts)
    assert out['status']=='VERIFIED_RESULT_CANDIDATE_PENDING_CANONICAL_LEDGER_FINALIZER'
    assert out['existing_verifier_checked'] and out['terminal_record_sha256']
    for flag in ['worker_result_accepted','automatic_retry','release_allowed',
                 'production_quiescence_proven','launch_allowed','candidate_promotion_allowed']:
        assert out[flag] is False

def test_without_started_ledger_never_yields_candidate(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    opts['ledger_rows']=[]
    assert r._assess(**opts)['status']=='BLOCKED_CLAIM_LEDGER_OR_SERVICE_UNVERIFIED'

def test_unknown_service_never_yields_candidate(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    opts['service']=None
    assert r._assess(**opts)['status']=='BLOCKED_CLAIM_LEDGER_OR_SERVICE_UNVERIFIED'

def test_live_service_never_yields_candidate(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    opts['service']={**opts['service'],'load_state':'loaded','active_state':'active','main_pid':12345,
        'control_group':'/system.slice/'+UNIT,'user':'forprint-runner','group':'forprint-runner','kill_mode':'control-group'}
    assert r._assess(**opts)['status']=='BLOCKED_CLAIM_LEDGER_OR_SERVICE_UNVERIFIED'

def test_missing_claim_blocks(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    opts['receipt_summary']=None
    assert r._assess(**opts)['status']=='BLOCKED_CLAIM_LEDGER_OR_SERVICE_UNVERIFIED'

def test_result_missing_denied(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    (attempt/'result'/'worker_result.yaml').unlink()
    with pytest.raises(r.CrosscheckBlocked,match='RESULT_MISSING'):r._assess(**opts)

@pytest.mark.parametrize('change,reason',[
    ({'attempt_id':'other'},'RESULT_ATTEMPT'),
    ({'handoff_manifest_sha256':'f'*64},'RESULT_HANDOFF'),
    ({'status':'FAILED'},'RESULT_NOT_SUCCESS')])
def test_forged_worker_result_denied(tmp_path,change,reason):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    p=attempt/'result'/'worker_result.yaml';data=json.loads(p.read_text());data.update(change)
    p.write_text(json.dumps(data));p.chmod(0o600)
    with pytest.raises(r.CrosscheckBlocked,match=reason):r._assess(**opts)

def test_duplicate_yaml_keys_denied(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    p=attempt/'result'/'worker_result.yaml';p.write_text('attempt_id: '+ATT+'\nattempt_id: '+ATT+'\n');p.chmod(0o600)
    with pytest.raises(r.CrosscheckBlocked,match='DUPLICATE'):r._assess(**opts)

def test_result_symlink_denied(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    p=attempt/'result'/'worker_result.yaml';p.rename(attempt/'result'/'kept');p.symlink_to('kept')
    with pytest.raises(OSError):r._assess(**opts)

def test_result_writable_denied(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    (attempt/'result'/'worker_result.yaml').chmod(0o666)
    with pytest.raises(r.CrosscheckBlocked,match='INODE_OR_PERMISSIONS'):r._assess(**opts)

def test_canonical_envelope_failure_blocks(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    opts['envelope_validator']=lambda *_:['PROOF_INVALID']
    v=r._assess(**opts)
    assert v['status']=='BLOCKED_CANONICAL_HANDOFF_OR_RESUME_VALIDATION'
    assert v['verification_error_count']==1

def test_s4_resume_failure_blocks(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    opts['resume_validator']=lambda *_:['CURSOR_DRIFT','FINGERPRINT_DRIFT']
    v=r._assess(**opts)
    assert v['verification_error_count']==2 and v['worker_result_accepted'] is False

def test_verifier_exception_fails_closed(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path);complete(tmp_path,store,spec)
    def fail(*_):raise ValueError('failure')
    opts['envelope_validator']=fail
    with pytest.raises(r.CrosscheckBlocked,match='CANONICAL_VALIDATOR_ERROR_ValueError'):
        r._assess(**opts)

def test_no_production_runtime_injection(tmp_path):
    store,spec,ident,attempt,opts=fixture(tmp_path)
    opts['fixture']=False
    with pytest.raises(r.CrosscheckBlocked,match='CANONICAL_ATTEMPT_ROOT'):r._assess(**opts)

def test_backend_remains_sealed():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    p=Path(backend.__file__)
    assert 'LIVE_CUTOVER_ENABLED=False' in p.read_text()
