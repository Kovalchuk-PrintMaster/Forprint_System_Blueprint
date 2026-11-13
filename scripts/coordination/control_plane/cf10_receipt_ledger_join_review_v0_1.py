"""CF10 r020: read-only receipt/ledger divergence classification.

No attempt creation, no claim, no systemd, no ledger write, no worker spawn.
Caller must authenticate source provenance independently. Reports are never authority.
This deliberately does NOT resolve production reconciliation or grant a retry.
"""
from __future__ import annotations
from collections.abc import Mapping
from datetime import datetime
import re

_ATTEMPT = re.compile(r"cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z")
_HEAD = re.compile(r"[a-f0-9]{40}\Z")
_HASH = re.compile(r"[a-f0-9]{64}\Z")

class JoinBlocked(ValueError):
    pass

def _bad(tag):
    raise JoinBlocked('CF10_R020_'+tag)

def _scope(attempt_id, source_head, handoff_sha256):
    for label, value, pattern in (
        ('ATTEMPT', attempt_id, _ATTEMPT),
        ('HEAD', source_head, _HEAD),
        ('HANDOFF', handoff_sha256, _HASH),
    ):
        if not isinstance(value, str) or not pattern.fullmatch(value):
            _bad('SCOPE_'+label)

def _classify_receipt(receipt, attempt_id, source_head):
    if receipt is None:
        return 'ABSENT'
    required = {
        'attempt_id','source_head','claim_consumed','event_count',
        'last_digest','worker_result_accepted','automatic_retry',
        'root_receipt_chain_verified',
    }
    if (not isinstance(receipt, dict) or set(receipt) != required
            or receipt.get('attempt_id') != attempt_id
            or receipt.get('source_head') != source_head
            or receipt.get('claim_consumed') is not True
            or receipt.get('root_receipt_chain_verified') is not True
            or receipt.get('worker_result_accepted') is not False
            or receipt.get('automatic_retry') is not False
            or type(receipt.get('event_count')) is not int
            or not 0 <= receipt['event_count'] <= 9999
            or not isinstance(receipt.get('last_digest'),str)
            or not _HASH.fullmatch(receipt['last_digest'])):
        _bad('RECEIPT_UNTRUSTED_OR_CORRUPT')
    return 'CLAIM_CONSUMED'

def _classify_ledger(ledger_rows, attempt_id):
    if not isinstance(ledger_rows,(list,tuple)) or len(ledger_rows)>2:
        _bad('LEDGER_COUNT')
    if not ledger_rows:
        return 'ABSENT'
    for row in ledger_rows:
        if (not isinstance(row,dict) or row.get('attempt_id')!=attempt_id
                or row.get('attempt_stage') not in {'STARTED','FINISHED','BLOCKED','INTERRUPTED'}
                or row.get('result_state') not in {'PENDING','BLOCKED','PARTIAL','SUCCEEDED','FAILED'}
                or not isinstance(row.get('recorded_at'),str)):
            _bad('LEDGER_ROW_INVALID')
        try:
            dt=datetime.fromisoformat(row['recorded_at'].replace('Z','+00:00'))
            if dt.tzinfo is None:_bad('LEDGER_TIMESTAMP_NO_TZ')
        except ValueError:
            _bad('LEDGER_TIMESTAMP')
    first=ledger_rows[0]
    if first.get('attempt_stage')!='STARTED' or first.get('result_state')!='PENDING':
        _bad('LEDGER_FIRST_NOT_STARTED_PENDING')
    if len(ledger_rows)==2:
        last=ledger_rows[1]
        if last.get('result_state')=='PENDING':_bad('LEDGER_NONTERMINAL_APPEND')
        d1=datetime.fromisoformat(first['recorded_at'].replace('Z','+00:00'))
        d2=datetime.fromisoformat(last['recorded_at'].replace('Z','+00:00'))
        if d2<=d1:_bad('LEDGER_NONMONOTONIC')
        return 'TERMINAL_CANDIDATE_UNVERIFIED'
    return 'STARTED_PENDING'

def reconcile(*,attempt_id:str,source_head:str,handoff_sha256:str,
              receipt:Mapping|None,ledger_rows:list[dict],
              supervisor_observation:Mapping|None=None)->dict:
    """Never assert production quiescence. Never allow resume or result acceptance.

    Ledger input must be independently validated against its canonical contract by
    the caller; this function checks only the cross-store mismatch signals.
    """
    _scope(attempt_id,source_head,handoff_sha256)
    r=_classify_receipt(receipt,attempt_id,source_head)
    l=_classify_ledger(ledger_rows,attempt_id)
    if supervisor_observation is not None:
        if (not isinstance(supervisor_observation,dict)
                or supervisor_observation.get('attempt_id')!=attempt_id
                or supervisor_observation.get('source_head')!=source_head
                or supervisor_observation.get('worker_result_accepted') is not False
                or supervisor_observation.get('production_quiescence_proven') is not False
                or supervisor_observation.get('authorization_granted') is not False):
            _bad('SUPERVISOR_ASSERTS_UNTRUSTED_AUTHORITY')
    if r=='ABSENT' and l=='ABSENT':
        state='UNCLAIMED_NO_LEDGER_FACT_REVIEW_ONLY'
    elif r=='ABSENT':
        state='QUARANTINE_ORPHAN_LEDGER_NO_RECEIPT'
    elif l=='ABSENT':
        state='BLOCKED_CONSUMED_CLAIM_NO_STARTED_FACT'
    elif l=='STARTED_PENDING':
        state='BLOCKED_STARTED_PENDING_RECOVERY_REQUIRED'
    else:
        state='BLOCKED_TERMINAL_FACT_NEEDS_INDEPENDENT_PROOFS'
    return {'schema_version':'cf10_r020_receipt_ledger_review_v0_1',
            'attempt_id':attempt_id,'source_head':source_head,
            'receipt_state':r,'ledger_state':l,'state':state,
            'worker_started_proven':False,
            'production_quiescence_proven':False,
            'resume_allowed':False,'automatic_retry':False,
            'worker_result_accepted':False,'release_allowed':False,
            'operator_authority_granted':False,
            'production_cutover_completed':False,
            'input_is_authority':False,
            'manual_review_required':r!='ABSENT' or l!='ABSENT'}
