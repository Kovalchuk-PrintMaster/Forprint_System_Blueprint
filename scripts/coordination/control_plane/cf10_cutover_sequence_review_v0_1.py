"""CF10 r018b — compositional, review-only canonical cutover contract.

No claim, I/O, password authentication, systemd, worker spawn, ledger append,
acceptance, retry, approval, or promotion. All inputs are untrusted review data.
A SHA256 digest does NOT make a review document trusted or authorize a run.
"""
from __future__ import annotations
from collections.abc import Mapping
import hashlib
import json
from scripts.coordination.control_plane import (
    cf10_supervisor_binding_candidate_v0_1 as supervisor,
    cf10_trusted_baseline_binding_v0_1 as baseline,
    cf10_recovery_reconciliation_v0_1 as recovery,
    cf10_cutover_shadow_gate_v0_1 as gate,
)

class ReviewBlocked(ValueError): pass

CREDENTIAL_KEYS = frozenset({
    'schema_version','attempt_id','source_head','handoff_sha256',
    'delivery_state','secret_material_in_report','authority_granted',
})
EXPECTED_EVENTS = (
    'CLAIM_CONSUMED','LAUNCH_REQUESTED','SERVICE_OBSERVED',
    'STOP_REQUESTED','QUIESCENCE_OBSERVED_CANDIDATE',
)

def _deny(reason): raise ReviewBlocked('CF10_R018B_'+reason)

def _digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

def _cred_check(doc, spec):
    if not isinstance(doc,dict) or set(doc)!=CREDENTIAL_KEYS:
        _deny('CREDENTIAL_DESCRIPTOR_KEYS_OR_SECRET_FIELD')
    expected = {'schema_version':'cf10_r018b_credential_metadata_only_v0_1',
       'attempt_id':spec.attempt_id,'source_head':spec.source_head,
       'handoff_sha256':spec.handoff_sha256,'delivery_state':'NOT_RELEASED',
       'secret_material_in_report':False,'authority_granted':False}
    if doc!=expected:_deny('CREDENTIAL_DESCRIPTOR_VALUE_OR_AUTHORITY')

def _observation_check(obs,spec):
    if not isinstance(obs,dict) or set(obs)!= {
        'schema_version','attempt_id','source_head','status','production_quiescence_proven',
        'worker_result_accepted','authorization_granted'}:
        _deny('OBSERVATION_FIELDS')
    if obs!={'schema_version':'cf10_r018b_synthetic_observation_v0_1',
         'attempt_id':spec.attempt_id,'source_head':spec.source_head,
         'status':'REVIEW_ONLY', 'production_quiescence_proven':False,
         'worker_result_accepted':False,'authorization_granted':False}:
        _deny('OBSERVATION_AUTHORITY_OR_BINDING')

def _delta_check(doc,spec):
    if not isinstance(doc,dict) or set(doc)!= {
        'schema_version','attempt_id','source_head','status','worker_result_accepted',
        'production_quiescence_proven','git_metadata_trusted'}:
        _deny('DELTA_FIELDS')
    if doc!={'schema_version':'cf10_r018b_delta_review_only_v0_1',
         'attempt_id':spec.attempt_id,'source_head':spec.source_head,
         'status':'BLOCKED_PENDING_INDEPENDENT_PROCESS_PROOF',
         'worker_result_accepted':False,'production_quiescence_proven':False,
         'git_metadata_trusted':False}:
        _deny('DELTA_AUTHORITY_OR_BINDING')

def review(*, route:str, spec:supervisor.BoundedInput, plan:Mapping,
           baseline_binding:Mapping, receipt:Mapping,
           credentials:Mapping, supervisor_observation:Mapping, delta_preview:Mapping):
    """Compose existing contracts; output is ALWAYS BLOCKED, never a live launch permit."""
    if route not in gate.VALID_ROUTES:_deny('ENTRYPOINT')
    if not isinstance(spec,supervisor.BoundedInput):_deny('SPEC')
    supervisor.validate_plan(plan,spec)
    baseline.match_binding(baseline_binding, attempt_id=spec.attempt_id,
        task_prompt_id=spec.task_prompt_id,source_head=spec.source_head,
        handoff_sha256=spec.handoff_sha256,baseline_sha256=spec.baseline_sha256)
    _cred_check(credentials,spec)
    _observation_check(supervisor_observation,spec)
    _delta_check(delta_preview,spec)
    # Pure synthetic reconstruction: checks sequence and tamper, NEVER provenance.
    reconciled=recovery.reconcile(receipt=receipt,attempt_id=spec.attempt_id,
        source_head=spec.source_head,handoff_sha256=spec.handoff_sha256)
    if reconciled['launch_allowed'] is not False or reconciled['automatic_retry'] is not False:
        _deny('RECOVERY_AUTHORITY_FORGERY')
    if receipt.get('events') != list(EXPECTED_EVENTS):
        state = reconciled['state']
    else:
        state = 'BLOCKED_PENDING_PRODUCTION_PROOFS'
    # Do not hash arbitrary user input or include secret-bearing data in a report.
    ident={'route':route,'attempt_id':spec.attempt_id,'task_prompt_id':spec.task_prompt_id,
           'source_head':spec.source_head,'handoff_sha256':spec.handoff_sha256,
           'baseline_sha256':spec.baseline_sha256,'unit':plan['identity']['unit'],
           'receipt_event_count':len(receipt['events']),'recovery_state':state}
    return {'schema_version':'cf10_r018b_canonical_review_only_v0_1',
        'binding':ident,'binding_sha256':_digest(ident),
        'legacy_entrypoint_shadow_denied':True,'supervisor_started':False,
        'credentials_released':False,'root_claim_consumed':False,
        'ledger_written':False,'production_quiescence_proven':False,
        'worker_launched':False,'worker_result_accepted':False,
        'automatic_retry':False,'release_allowed':False,'authority_granted':False,
        'status':'BLOCKED_PRODUCTION_CUTOVER_NOT_WIRED'}
