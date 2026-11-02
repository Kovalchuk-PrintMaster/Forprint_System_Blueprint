"""CF-10 r024: disposable root-receipt / *real* systemd fixture / ledger join.

No production Worker / STARTED record / authorization. A successful real
systemd fixture is deliberately reconciled against ABSENT production ledger;
that can only be a blocked, manual-review state. No retry after claim.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import os
import re
from typing import Callable

from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipt
from scripts.coordination.control_plane import cf10_receipt_ledger_join_review_v0_1 as join

PIN = 'e99aedbed976e8f809db471ee06888f304df0965'
UNIT_RE = re.compile(r'forprint-cf10-r024-fixture-[0-9a-f]{12}\.service\Z')
ATTEMPT_RE = re.compile(r'cf10-r024fixture-[0-9a-f]{12}-a024\Z')
HANDOFF_SENTINEL = '0'*64  # Deliberately NOT a production handoff

class PilotBlocked(RuntimeError):
    pass

def deny(tag):
    raise PilotBlocked('CF10_R024_'+tag)

def classify_fixture(report: Mapping) -> dict:
    """Strictly inspect an independently observed, disposable systemd fixture."""
    if not isinstance(report, dict): deny('REPORT_TYPE')
    if report.get('schema') != 'cf10_systemd_disposable_supervisor_gate_r024': deny('REPORT_SCHEMA')
    if report.get('head') != PIN: deny('REPORT_HEAD')
    unit=report.get('unit')
    if not isinstance(unit,str) or not UNIT_RE.fullmatch(unit): deny('REPORT_UNIT')
    if report.get('control_group') != '/system.slice/'+unit: deny('REPORT_CGROUP')
    for field in ('operator_approval_for_live_worker', 'live_worker_launched', 'attempt_mutated',
                  'production_promotion_allowed', 'process_quiescence_proven_for_production'):
        if report.get(field) is not False: deny('REPORT_AUTHORITY:'+field)
    t=report.get('teardown')
    valid=(report.get('status')=='PASS_DISPOSABLE_ONLY_NON_AUTHORIZING'
        and isinstance(t,dict)
        and all(t.get(k) is True for k in
                ('unit_stopped','all_sampled_pids_gone','cgroup_empty_or_removed'))
        and t.get('after_state') in ('inactive','failed')
        and report.get('start_rc')==0 and report.get('runner_uid_proven') is True
        and report.get('setsid_child_contained') is True
        and report.get('systemd_properties_verified') is True
        and report.get('fixture_started') is True
        and report.get('test_directory_removed') is True
        and type(report.get('parent_pid')) is int and report['parent_pid'] > 1
        and type(report.get('child_pid')) is int and report['child_pid'] > 1
        and report['parent_pid']!=report['child_pid']
        and not any(k in report for k in ('error','teardown_error','manual_review_required')))
    return {'disposable_systemd_proven':valid,'production_quiescence_proven':False,
            'production_launch_allowed':False,'worker_result_accepted':False,
            'automatic_retry':False}

def execute_disposable(*, private_store:Path, attempt_id:str, probe:Path,
                       systemd_fixture:Callable[[Path],dict]) -> dict:
    """Exactly one root-only disposable claim then real systemd fixture callback.

    Caller MUST only provide the fixed canonical probe and fixture implementation;
    no user-supplied callback is exposed by the production-free CLI.
    """
    if os.geteuid()!=0: deny('ROOT_REQUIRED')
    if not isinstance(attempt_id,str) or not ATTEMPT_RE.fullmatch(attempt_id):deny('DISPOSABLE_ID')
    if not callable(systemd_fixture):deny('CALLBACK')
    if not isinstance(probe,Path) or not probe.is_file() or probe.is_symlink():deny('PROBE')
    private_store=Path(private_store)
    parent=private_store.parent
    if (not private_store.is_absolute() or private_store.name!='receipts'
            or not parent.name.startswith('cf10-r024-disposable-') or parent.is_symlink()
            or str(private_store).startswith(('/srv/software_development/forprint-project/',
                                              '/srv/software_development/forprint-worker-runtime/'))):
        deny('STORE_SCOPE')
    receipt.claim(private_store=private_store,attempt_id=attempt_id,
                  head=PIN,handoff_sha256=HANDOFF_SENTINEL)
    # Immutable claim exists even if any subsequent action crashes.
    receipt.append_observation(private_store=private_store,attempt_id=attempt_id,
        expected_head=PIN,event='LAUNCH_REQUESTED')
    raw=None; failure=None; proof=None
    try:
        raw=systemd_fixture(probe)
        proof=classify_fixture(raw)
        if not proof['disposable_systemd_proven']: failure='DISPOSABLE_SYSTEMD_UNPROVEN'
    except Exception as exc:
        failure='FIXTURE_EXCEPTION_'+type(exc).__name__
    # Never assert production QUIESCENCE; even a passing disposable proof needs review.
    receipt.append_observation(private_store=private_store,attempt_id=attempt_id,
        expected_head=PIN,event='REVIEW_REQUIRED' if failure is None else 'QUIESCENCE_UNPROVEN')
    state=receipt.observe(private_store=private_store,attempt_id=attempt_id,expected_head=PIN)
    reconcile=join.reconcile(attempt_id=attempt_id,source_head=PIN,
        handoff_sha256=HANDOFF_SENTINEL,receipt=state,ledger_rows=[])
    if reconcile['state']!='BLOCKED_CONSUMED_CLAIM_NO_STARTED_FACT':deny('LEDGER_JOIN_UNEXPECTED')
    return {'schema_version':'cf10_r024_disposable_systemd_join_evidence_v0_1',
        'attempt_id':attempt_id,'head':PIN,
        'status':'PASS_DISPOSABLE_SYSTEMD_RECEIPT_JOIN_NON_AUTHORIZING' if failure is None else 'BLOCKED_DISPOSABLE_SYSTEMD_UNKNOWN',
        'reason':failure,'fixture_unit':raw.get('unit') if isinstance(raw,dict) else None,
        'receipt_events':state['event_count'],'receipt_sha256':state['last_digest'],
        'root_receipt_chain_verified':state['root_receipt_chain_verified'],
        'disposable_systemd_proven':failure is None,
        'join_state':reconcile['state'],'canonical_started_ledger_modified':False,
        'worker_launched':False,'release_allowed':False,'automatic_retry':False,
        'production_quiescence_proven':False,'worker_result_accepted':False}
