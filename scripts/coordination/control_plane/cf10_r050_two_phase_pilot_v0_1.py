"""CF10 r050: disjoint PRECLAIM and LAUNCH_WINDOW reviews (non-authorizing).

A PRECLAIM snapshot is evidence from r045 while the legacy Make/backend
quarantine is intact.  The later LAUNCH_WINDOW must verify a separately
trusted, immutable PRECLAIM receipt instead of calling r045.collect again.
This module NEVER issues that receipt, authenticates PAM, modifies runtime,
or grants a cutover; it only specifies and checks exact future call contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
import re

SCHEMA = 'cf10_r050_two_phase_pilot_v0_1'
PROFILE = 'SINGLE_OWNER_BOUNDED_TASK70'
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATTEMPT = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')
HEAD = re.compile(r'[0-9a-f]{40}\Z')
REQUIRED_LAUNCH_OBSERVATIONS = frozenset({
    'source_guard_verified',
    'preclaim_root_receipt_verified',
    'release_candidate_raw_lineage_verified',
    'frozen_input_current',
    'canonical_cycle_ready',
    'writer_protocol_enforced',
    'root_one_shot_claim_unconsumed',
    'canonical_ledger_unstarted',
    'systemd_worker_quiescent',
    'owner_pam_session_authenticated',
    'source_bound_pilot_make_route_verified',
    'source_bound_pilot_systemd_backend_verified',
    'independent_finalizer_required',
    'automatic_retry_disabled',
    'legacy_signed_release_separate',
})


def _sha_dict(value: Mapping) -> str:
    return hashlib.sha256((json.dumps(dict(value), ensure_ascii=False, sort_keys=True,
                  separators=(',', ':')) + '\n').encode('utf-8')).hexdigest()


def _identity(task: object, attempt: object, head: object) -> list[str]:
    errors = []
    if task != TASK:
        errors.append('EXACT_CANONICAL_TASK70_REQUIRED')
    if not isinstance(attempt, str) or ATTEMPT.fullmatch(attempt) is None:
        errors.append('EXACT_NEW_CF10_ATTEMPT_REQUIRED')
    if not isinstance(head, str) or HEAD.fullmatch(head) is None:
        errors.append('PUBLISHED_HEAD_REQUIRED')
    return errors


def preclaim(*, report: Mapping, source_head: str, task: str, attempt: str) -> dict:
    """Derive an unhashed-authority / hash-bound *candidate*; no durable write.

    The PRECLAIM must have been gathered while the legacy source quarantine
    remained closed. Once opened, it MUST NOT be re-collected as an invariant.
    """
    bad = _identity(task, attempt, source_head)
    if not isinstance(report, Mapping):
        bad.append('R045_REPORT_UNAVAILABLE')
        report = {}
    for key, required in {
        'schema_version': 'cf10_r045_bounded_owner_pilot_admission_v0_1',
        'profile': 'SINGLE_OWNER_BOUNDED_TASK70_CANDIDATE',
        'task_prompt_id': task,
        'attempt_id': attempt,
        'status': 'PRECLAIM_EVIDENCE_CANDIDATE_NON_AUTHORIZING',
        'preclaim_evidence_complete': True,
        'admission_authorized': False,
        'launch_allowed': False,
        'production_cutover': False,
        'worker_launched': False,
        'automatic_retry': False,
        'automatic_acceptance': False,
        'automatic_publication': False,
        'owner_pam_authenticated': False,
        'operator_claim_consumed': False,
        'legacy_independent_release': 'UNCHANGED_NOT_SATISFIED_BY_OWNER_PILOT',
    }.items():
        if type(report.get(key)) is not type(required) or report.get(key) != required:
            bad.append('R045_PRECLAIM_' + key.upper() + '_INVALID')
    if report.get('blockers') != []:
        bad.append('R045_PRECLAIM_BLOCKED')
    # No assumption of root storage: hashing an in-memory report is NOT an
    # attestation. A separate root-owned durable record/verify is still needed.
    digest = _sha_dict(report) if not bad else None
    return {
        'schema_version': SCHEMA,
        'phase': 'PRECLAIM',
        'status': 'PRECLAIM_SNAPSHOT_CANDIDATE_NON_AUTHORIZING' if not bad
                  else 'BLOCKED_PRECLAIM_SNAPSHOT',
        'task_prompt_id': task,
        'attempt_id': attempt,
        'source_head': source_head,
        'r045_report_sha256': digest,
        'r045_quarantine_fact_frozen': not bad,
        'root_owned_preclaim_receipt_written': False,
        'preclaim_root_receipt_verified': False,
        'blockers': sorted(set(bad)),
        'launch_allowed': False,
        'automatic_retry': False,
        'production_cutover': False,
        'next_action': 'VERIFY_AND_SEAL_BY_SEPARATE_ROOT_OWNER_ROUTE' if not bad
                       else 'PREPARE_EXACT_TASK70_ATTEMPT_WITHOUT_LAUNCH',
    }


def launch_window(*, snapshot: Mapping, release: Mapping,
                  observations: Mapping, task: str, attempt: str,
                  source_head: str) -> dict:
    """Pure second-phase review. Does not recollect quarantine-bound r045.

    The caller is obliged to verify root-owned snapshot *bytes* independently.
    All observations are supplied by future privileged canonical observers,
    never trusted solely because a caller passed True; this evaluator grants
    no authority even if all fields are True.
    """
    bad = _identity(task, attempt, source_head)
    if not isinstance(snapshot, Mapping):
        bad.append('SEALED_PRECLAIM_UNAVAILABLE')
        snapshot = {}
    if (snapshot.get('schema_version') != SCHEMA or snapshot.get('phase') != 'PRECLAIM'
            or snapshot.get('status') != 'PRECLAIM_SNAPSHOT_CANDIDATE_NON_AUTHORIZING'
            or snapshot.get('blockers') != []
            or snapshot.get('r045_quarantine_fact_frozen') is not True
            or not isinstance(snapshot.get('r045_report_sha256'), str)
            or re.fullmatch('[0-9a-f]{64}', snapshot.get('r045_report_sha256','')) is None):
        bad.append('PRECLAIM_SNAPSHOT_INVALID')
    if any(snapshot.get(k) != v for k,v in [('task_prompt_id', task),
                                             ('attempt_id', attempt), ('source_head', source_head)]):
        bad.append('PRECLAIM_SOURCE_OR_IDENTITY_DRIFT')
    if not isinstance(release, Mapping):
        release = {}
    checks = release.get('checks')
    if not isinstance(checks, Mapping):
        checks = {}
    if (release.get('schema_version') != 'cf10_r046_pilot_cutover_review_v0_1'
            or release.get('status') != 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED'
            or release.get('blockers') != []
            or checks.get('r047_source_lineage') != 'EXACT_RAW_BYTES_BOUND'
            or release.get('task_prompt_id') != task or release.get('attempt_id') != attempt
            or release.get('launch_allowed') is not False):
        bad.append('EXACT_R046_R047_PROOFS_NOT_VERIFIED')
    if not isinstance(observations, Mapping) or set(observations) != REQUIRED_LAUNCH_OBSERVATIONS:
        bad.append('LAUNCH_OBSERVATIONS_EXACT_FIELDS_REQUIRED')
        observations = {}
    for key in sorted(REQUIRED_LAUNCH_OBSERVATIONS):
        if observations.get(key) is not True or type(observations.get(key)) is not bool:
            bad.append('LAUNCH_' + key.upper() + '_UNVERIFIED')
    # The actual launch route has independent checks; this evaluation alone
    # never satisfies release/authority semantics, including an all-true input.
    return {
        'schema_version': SCHEMA, 'phase': 'LAUNCH_WINDOW',
        'status': 'PILOT_LAUNCH_CANDIDATE_NON_AUTHORIZING' if not bad else 'BLOCKED_LAUNCH_WINDOW',
        'source_head': source_head, 'task_prompt_id': task, 'attempt_id': attempt,
        'blockers': sorted(set(bad)),
        'r045_recollected_after_cutover': False,
        'legacy_release_authority_reused': False,
        'worker_launched': False, 'launch_allowed': False,
        'release_authorized': False, 'production_cutover': False,
        'automatic_retry': False, 'automatic_acceptance': False,
        'automatic_publication': False,
        'next_action': 'SEPARATE_ROOT_PAM_AND_SOURCE_BOUND_ADMISSION_REQUIRED',
    }


def requirements() -> dict:
    return {
        'schema_version': SCHEMA,
        'status': 'TWO_PHASE_REVIEW_CONTRACT_NON_AUTHORIZING',
        'phase_order': ['PRECLAIM_WHILE_MAKE_AND_BACKEND_QUARANTINED',
                        'VERIFY_IMMUTABLE_ROOT_OWNED_PRECLAIM_RECEIPT',
                        'VERIFY_EXACT_R046_R047_RELEASE_PROOFS',
                        'REVALIDATE_FROZEN_INPUT_WRITER_CLAIM_LEDGER_SYSTEMD',
                        'OWNER_PAM_SINGLE_USE_AFTER_SEPARATE_PILOT_CUTOVER'],
        'required_launch_observations': sorted(REQUIRED_LAUNCH_OBSERVATIONS),
        'preclaim_root_receipt_writer_implemented': True,  # r051 create-only, no launch authority
        'source_bound_pilot_make_backend_activation_implemented': False,
        'production_worker_launched': False,
        'launch_allowed': False,
        'next_action': 'COMPLETE_EXACT_PILOT_PROOFS_AND_SEPARATE_MAKE_BACKEND_CUTOVER',
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('requirements', 'inspect-preclaim'))
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--task-prompt-id', default='')
    parser.add_argument('--attempt-id', default='')
    ns = parser.parse_args(argv)
    if ns.mode == 'requirements':
        result = requirements()
    else:
        from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
        from scripts.coordination.control_plane import cf10_r045_pilot_admission_v0_1 as r045
        try:
            head = console.source_guard(ns.root.resolve(strict=True))
            report = r045.collect(ns.root, ns.task_prompt_id, ns.attempt_id)
            result = preclaim(report=report, source_head=head,
                              task=ns.task_prompt_id, attempt=ns.attempt_id)
        except Exception:
            result = preclaim(report={}, source_head='', task=ns.task_prompt_id,
                              attempt=ns.attempt_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if ns.mode == 'requirements' or not result['blockers'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
