"""CF10 r025: no-authority recovery + canonical source boundary regression tests."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import pytest
from scripts.coordination.control_plane import cf10_r025_recovery_readback_v0_1 as r
from scripts.coordination.control_plane import cf10_r025_canonical_seam_v0_1 as seam
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipt

HEAD='e2f0e6d7c2d4aea8de976de4af397c887b83207a'
ATTEMPT='cf10-r025fixture-abcdef123456-a025'
HANDOFF='a'*64

def identity():return r.identity_from_source(attempt_id=ATTEMPT,head=HEAD,handoff_sha256=HANDOFF)

def startrow():return {'attempt_id':ATTEMPT,'attempt_stage':'STARTED','result_state':'PENDING','recorded_at':'2026-11-02T13:00:00+00:00'}

def service(state='active'):
    ident=identity()
    return {'unit':ident.unit,'attempt_id':ATTEMPT,'source_head':HEAD,'load_state':'loaded',
        'active_state':state,'main_pid':1234 if state in ('active','activating','deactivating') else 0,
        'control_group':'/system.slice/'+ident.unit if state in ('active','activating','deactivating') else '',
        'user':'forprint-runner','group':'forprint-runner','kill_mode':'control-group',
        'provenance':'ROOT_SYSTEMCTL_SHOW_READBACK'}

def s(receipt_summary=None, ledger_rows=None, svc=None,occupied=False):
    return r.decide(identity=identity(),receipt_summary=receipt_summary,
        ledger_rows=ledger_rows or [],service=svc,claim_path_occupied=occupied)

def safe(v):
    assert v['automatic_retry'] is False
    assert v['launch_allowed'] is False
    assert v['stop_allowed'] is False
    assert v['release_allowed'] is False
    assert v['worker_result_accepted'] is False
    assert v['production_quiescence_proven'] is False
    assert v['manual_review_required'] is True
    return v

def test_no_attempt_unknown_service():
    assert safe(s())['state']=='UNKNOWN_NO_TRUSTED_SYSTEMD_READBACK'

def test_unclaimed_no_service_readback():
    assert safe(s(svc=service('inactive')))['state']=='UNCLAIMED_NO_LEDGER_FACT_REVIEW_ONLY'

def test_incomplete_claim_directory_fails_closed():
    assert safe(s(occupied=True))['state']=='QUARANTINE_OCCUPIED_MISSING_OR_CORRUPT_CLAIM'

@pytest.mark.parametrize('state', ['active','activating','deactivating'])
def test_orphan_active_unit_quarantine(state):
    row=service(state);row['main_pid']=321
    assert safe(s(svc=row))['state']=='QUARANTINE_ORPHAN_SERVICE_NO_ROOT_CLAIM'

@pytest.mark.parametrize('field,value', [('unit','other.service'),('attempt_id','cf10-u180j-a049'),
    ('source_head','0'*40),('provenance','WORKER_SUPPLIED'),('load_state','unknown'),
    ('active_state','running'),('main_pid',True),('user','root'),('group','root'),('kill_mode','process')])
def test_service_tampering_denied(field,value):
    x=service();x[field]=value
    with pytest.raises(r.RecoveryBlocked):s(svc=x)

@pytest.mark.parametrize('key', list(service().keys()))
def test_service_missing_field_denied(key):
    x=service();x.pop(key)
    with pytest.raises(r.RecoveryBlocked):s(svc=x)

@pytest.mark.parametrize('field,value', [('load_state','not-found'),('main_pid',0),
    ('control_group','/'),('user',''),('group',''),('kill_mode','')])
def test_live_service_incomplete_denied(field,value):
    x=service();x[field]=value
    with pytest.raises(r.RecoveryBlocked):s(svc=x)

def test_started_without_claim_quarantine():
    assert safe(s(ledger_rows=[startrow()],svc=service('inactive')))['state']=='QUARANTINE_ORPHAN_LEDGER_NO_RECEIPT'

def test_active_without_claim_with_started_quarantine():
    assert safe(s(ledger_rows=[startrow()],svc=service()))['state']=='QUARANTINE_ORPHAN_SERVICE_NO_ROOT_CLAIM'

def test_claim_with_active_unit_review():
    summary={'attempt_id':ATTEMPT,'source_head':HEAD,'claim_consumed':True,'event_count':1,
        'last_digest':'c'*64,'worker_result_accepted':False,'automatic_retry':False,
        'root_receipt_chain_verified':True}
    assert safe(s(summary,[startrow()],service(),True))['state']=='BLOCKED_SYSTEMD_MAY_BE_ACTIVE_REQUIRES_OPERATOR_RECONCILIATION'

def test_claim_with_unknown_service_blocked():
    summary={'attempt_id':ATTEMPT,'source_head':HEAD,'claim_consumed':True,'event_count':1,
        'last_digest':'c'*64,'worker_result_accepted':False,'automatic_retry':False,
        'root_receipt_chain_verified':True}
    assert safe(s(summary,[startrow()],None,True))['state']=='BLOCKED_CGROUP_OR_SERVICE_UNKNOWN'

def test_receipt_without_claim_path_denied():
    summary={'attempt_id':ATTEMPT,'source_head':HEAD,'claim_consumed':True,'event_count':1,
        'last_digest':'c'*64,'worker_result_accepted':False,'automatic_retry':False,
        'root_receipt_chain_verified':True}
    with pytest.raises(r.RecoveryBlocked):s(summary,[startrow()],service(),False)

@pytest.mark.parametrize('field,value', [('attempt_id','cf10-u180j-a049'),('head','0'*40),
    ('handoff_sha256','xyz'),('runtime_root','/tmp'),('unit','forprint-cf10-worker-unsafe.service')])
def test_bound_identity_rejects_drift(field,value):
    from dataclasses import replace
    with pytest.raises((r.RecoveryBlocked,ValueError)):
        replace(identity(),**{field:value}).validate()

def test_transient_invalid_service_type():
    with pytest.raises(r.RecoveryBlocked):s(svc='active')

def test_not_active_with_unreaped_pid_unknown():
    x=service('inactive');x['main_pid']=22
    assert safe(s(svc=x))['service_state']=='UNKNOWN'

@pytest.mark.skipif(os.geteuid()!=0,reason='root-owned receipt proof')
def test_root_claim_process_restart_survives_no_retry(tmp_path):
    # Run a fresh Python interpreter that exits abruptly after durable claim,
    # then recover with a DIFFERENT interpreter, not in-process test globals.
    private=tmp_path/'cf10-r025-fixture-interpreter'
    private.mkdir(mode=0o700)
    store=private/'receipts';store.mkdir(mode=0o700)
    script="""import os,sys
from pathlib import Path
from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as r
r.claim(private_store=Path(sys.argv[1]),attempt_id=sys.argv[2],head=sys.argv[3],handoff_sha256=sys.argv[4])
os._exit(31)
"""
    cmd=[sys.executable,'-B','-c',script,str(store),ATTEMPT,HEAD,HANDOFF]
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    child=subprocess.run(cmd,env=env,capture_output=True)
    assert child.returncode==31,child.stderr
    summary,occupied=r.read_root_claim(private_store=store,identity=identity(),
        blueprint_root=tmp_path,disposable_fixture=True)
    assert occupied and summary['claim_consumed']
    result=r.decide(identity=identity(),receipt_summary=summary,ledger_rows=[],
        service=service('inactive'),claim_path_occupied=occupied)
    assert safe(result)['state']=='BLOCKED_CONSUMED_CLAIM_NO_STARTED_FACT'
    child2=subprocess.run(cmd,env=env,capture_output=True)
    assert child2.returncode != 31
    assert b'ALREADY_CONSUMED_NO_RETRY' in child2.stderr

@pytest.mark.skipif(os.geteuid()!=0,reason='root-owned receipt proof')
def test_interrupted_claim_json_quarantined(tmp_path):
    parent=tmp_path/'cf10-r025-fixture-corrupt';parent.mkdir(mode=0o700)
    store=parent/'receipts';store.mkdir(mode=0o700)
    d=store/ATTEMPT;d.mkdir(mode=0o700)
    (d/'0000_claim.json').write_text('{')
    os.chmod(d/'0000_claim.json',0o600)
    row,occupied=r.read_root_claim(private_store=store,identity=identity(),
        blueprint_root=tmp_path,disposable_fixture=True)
    assert row is None and occupied
    assert safe(s(occupied=occupied))['state']=='QUARANTINE_OCCUPIED_MISSING_OR_CORRUPT_CLAIM'

@pytest.mark.skipif(os.geteuid()!=0,reason='root-owned receipt proof')
def test_symlink_claim_quarantine(tmp_path):
    parent=tmp_path/'cf10-r025-fixture-symlink';parent.mkdir(mode=0o700)
    store=parent/'receipts';store.mkdir(mode=0o700)
    (store/ATTEMPT).symlink_to(tmp_path)
    row,occupied=r.read_root_claim(private_store=store,identity=identity(),
        blueprint_root=tmp_path,disposable_fixture=True)
    assert row is None and occupied

def test_exact_source_inventory_shape_passes():
    import zipfile
    # The install pack test fixture bundles source-only canonical snapshots.
    root=Path(__file__).resolve().parents[3]
    paths={p:(root/p).read_bytes() for p in seam.CRITICAL}
    result=seam.review_source_shapes(paths)
    assert result['owner_claim_before_launch']
    assert result['launch_mode'] in ('LEGACY_ROOT_INHERITED_POPEN','SEALED_CANONICAL_SYSTEMD')
    assert result['legacy_popen_present'] is (result['launch_mode']=='LEGACY_ROOT_INHERITED_POPEN')
    assert result['legacy_launch_callback_after_spawn']
    assert result['worker_cutover_authorized'] is False

@pytest.mark.parametrize('path', seam.CRITICAL)
def test_source_shape_rejects_missing(path):
    root=Path(__file__).resolve().parents[3]
    sources={p:(root/p).read_bytes() for p in seam.CRITICAL if p!=path}
    with pytest.raises(seam.SeamBlocked):seam.review_source_shapes(sources)

def test_legacy_launch_drift_blocked():
    root=Path(__file__).resolve().parents[3]
    sources={p:(root/p).read_bytes() for p in seam.CRITICAL}
    path='scripts/coordination/control_plane/worker_runtime/launcher.py'
    sources[path]=sources[path].replace(b'subprocess.Popen(',b'subprocess.run(')
    with pytest.raises(seam.SeamBlocked):seam.review_source_shapes(sources)


def test_missing_started_callback_blocked():
    root=Path(__file__).resolve().parents[3]
    sources={p:(root/p).read_bytes() for p in seam.CRITICAL}
    path='scripts/coordination/control_plane/worker_runtime/launcher.py'
    sources[path]=sources[path].replace(b'on_started(dict(started))',b'noop_started(dict(started))')
    with pytest.raises(seam.SeamBlocked):seam.review_source_shapes(sources)
