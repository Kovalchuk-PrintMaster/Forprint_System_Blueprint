"""CF-10 guarded recovery reconciliation, candidate ONLY.

Independently interpret a trusted receipt chain and process/credential evidence.
No public function starts a Worker, grants authority, revokes a claim, mints a
signature, appends a ledger event, or accepts a result. Even complete synthetic
proofs yield *review required*; they are never production quiescence proof.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

class ReconciliationBlocked(ValueError):
    pass

HEAD = re.compile(r"[0-9a-f]{40}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
ATTEMPT = re.compile(r"cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z")
EVENTS = (
    'CLAIM_CONSUMED', 'LAUNCH_REQUESTED', 'SERVICE_OBSERVED', 'STOP_REQUESTED',
    'QUIESCENCE_UNPROVEN', 'QUIESCENCE_OBSERVED_CANDIDATE', 'REVIEW_REQUIRED',
)
ORDERED = ('CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED',
           'STOP_REQUESTED','QUIESCENCE_OBSERVED_CANDIDATE')


def _deny(code: str) -> None:
    raise ReconciliationBlocked('CF10_R016_' + code)


def _scope(attempt_id: str, source_head: str, handoff_sha256: str) -> None:
    for value, pattern, key in ((attempt_id, ATTEMPT, 'ATTEMPT'),
                                (source_head, HEAD, 'HEAD'),
                                (handoff_sha256, SHA, 'HANDOFF')):
        if not isinstance(value, str) or pattern.fullmatch(value) is None:
            _deny(key)


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode('utf8')).hexdigest()


def simulate_events(*, attempt_id: str, source_head: str, handoff_sha256: str,
                    events: Sequence[str]) -> dict[str, Any]:
    """Pure synthetic receipt, NEVER a substitute for a root-owned receipt."""
    _scope(attempt_id, source_head, handoff_sha256)
    if isinstance(events, (str, bytes)) or not isinstance(events, (list, tuple)):
        _deny('EVENTS_TYPE')
    if len(events) < 1 or len(events) > 100 or events[0] != 'CLAIM_CONSUMED':
        _deny('EVENTS_BOUND')
    if any(type(e) is not str or e not in EVENTS for e in events):
        _deny('EVENT_UNKNOWN')
    if len(set(events)) != len(events):
        _deny('EVENT_REPLAY')
    if not set(events).issubset(set(ORDERED) | {'QUIESCENCE_UNPROVEN', 'REVIEW_REQUIRED'}):
        _deny('EVENT_INVALID')
    last = -1
    for e in events:
        if e in ORDERED:
            index = ORDERED.index(e)
            if index <= last or index != last + 1:
                _deny('EVENT_SEQUENCE')
            last = index
    if 'QUIESCENCE_UNPROVEN' in events and 'QUIESCENCE_OBSERVED_CANDIDATE' in events:
        _deny('EVENT_CONTRADICTION')
    digest = _hash({'attempt_id': attempt_id, 'source_head': source_head,
                    'handoff_sha256': handoff_sha256, 'events': list(events)})
    return {'schema': 'cf10_r016_simulated_root_receipt_v0_1',
            'attempt_id': attempt_id, 'source_head': source_head,
            'handoff_sha256': handoff_sha256, 'events': list(events),
            'content_sha256': digest, 'production_evidence': False,
            'automatic_retry': False}


def reconcile(*, receipt: Mapping[str, Any], attempt_id: str, source_head: str,
              handoff_sha256: str, supervisor: Mapping[str, Any] | None = None,
              credentials: Mapping[str, Any] | None = None,
              delta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Fail-closed recovery projection, always non-authorizing.

    Arguments are candidate data; neither supplied boolean nor SHA256 is
    accepted as a cryptographic proof of production process quiescence.
    """
    _scope(attempt_id, source_head, handoff_sha256)
    if not isinstance(receipt, Mapping) or receipt.get('schema') != 'cf10_r016_simulated_root_receipt_v0_1':
        _deny('RECEIPT_SCHEMA_OR_PROVENANCE')
    body = dict(receipt)
    digest = body.pop('content_sha256', None)
    if digest != _hash(body) and digest != _hash({
        'attempt_id': body.get('attempt_id'), 'source_head': body.get('source_head'),
        'handoff_sha256': body.get('handoff_sha256'), 'events': body.get('events')
    }):
        _deny('RECEIPT_TAMPER')
    if any(receipt.get(k) != v for k, v in (
        ('attempt_id', attempt_id), ('source_head', source_head),
        ('handoff_sha256', handoff_sha256), ('production_evidence', False),
        ('automatic_retry', False))):
        _deny('RECEIPT_BINDING')
    events = receipt.get('events')
    expected = simulate_events(attempt_id=attempt_id,source_head=source_head,
                               handoff_sha256=handoff_sha256,events=events)
    if receipt != expected:
        _deny('RECEIPT_UNEXPECTED_FIELDS')
    stages = set(events)
    if 'QUIESCENCE_UNPROVEN' in stages:
        state = 'BLOCKED_QUIESCENCE_UNKNOWN'
    elif 'REVIEW_REQUIRED' in stages:
        state = 'BLOCKED_OPERATOR_REVIEW'
    elif 'LAUNCH_REQUESTED' not in stages:
        state = 'BLOCKED_CONSUMED_CLAIM_NO_SPAWN'
    elif 'SERVICE_OBSERVED' not in stages:
        state = 'BLOCKED_SPAWN_OUTCOME_UNKNOWN'
    elif 'STOP_REQUESTED' not in stages:
        state = 'BLOCKED_PROCESS_MAY_BE_RUNNING'
    elif 'QUIESCENCE_OBSERVED_CANDIDATE' not in stages:
        state = 'BLOCKED_TEARDOWN_UNKNOWN'
    else:
        state = 'BLOCKED_PENDING_INDEPENDENT_PRODUCTION_PROOFS'
    for proof, code in ((supervisor, 'SUPERVISOR'), (credentials, 'CREDENTIALS'), (delta, 'DELTA')):
        if proof is None:
            continue
        if not isinstance(proof, Mapping) or proof.get('attempt_id') != attempt_id or proof.get('source_head') != source_head:
            _deny(code + '_BINDING')
        if proof.get('worker_result_accepted') is True or proof.get('authorizes_launch') is True:
            _deny(code + '_AUTHORITY_FORGERY')
    if supervisor is not None and supervisor.get('production_quiescence_proven') is True:
        _deny('UNTRUSTED_QUIESCENCE_PROOF')
    if credentials is not None and credentials.get('production_credentials_released') is True:
        _deny('UNTRUSTED_CREDENTIAL_AUTHORITY')
    if delta is not None and delta.get('delta_accepted') is True:
        _deny('UNTRUSTED_DELTA_ACCEPTANCE')
    return {'schema': 'cf10_r016_recovery_projection_v0_1',
            'attempt_id': attempt_id,'source_head':source_head,
            'handoff_sha256': handoff_sha256, 'state':state,
            'claim_consumed':True,'automatic_retry':False,
            'production_quiescence_proven':False,
            'worker_result_accepted':False,'launch_allowed':False,
            'release_allowed':False,'independent_operator_review_required':True,
            'input_class':'SYNTHETIC_NON_AUTHORIZING'}
