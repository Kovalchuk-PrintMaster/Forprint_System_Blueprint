"""CF10 project-native, read-only, exact-attempt operator routing / doctor.

No evidence minting, launch, PAM, claim, systemd, ledger write, acceptance, or retry.
Decisions are derived exclusively from canonical source/native observers.  This
module is not an alternative authority: the existing Make/PAM gates remain.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

PROJECT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
TASK70 = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
WORKER = 'worker-01'
SCHEMA = 'cf10_project_native_operator_workflow_v0_1'


class OperatorWorkflowBlocked(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise OperatorWorkflowBlocked('CF10_OPERATOR_' + code)


def next_route(s: dict) -> dict:
    """Pure routing table. Never convert a report into launch authority."""
    state = s.get('state')
    claim = s.get('claim')
    counts = s.get('ledger_records')
    frozen = s.get('frozen_source_current') is True
    basic = {'schema_version': SCHEMA, 'attempt_id': s.get('attempt_id'),
             'canonical_state': state, 'claim': claim, 'ledger_records': counts,
             'automatic_retry': False, 'worker_launch_invoked': False,
             'release_granted_by_report': False, 'operator_authority_granted': False}
    if not frozen:
        return {**basic, 'route': 'FROZEN_HEAD_MISMATCH_NO_REBIND',
                'next_action': 'OPERATOR_REVIEW_AND_NEW_ATTEMPT_AFTER_SOURCE_PUBLICATION'}
    if state in ('VALIDATE_CANDIDATE', 'FINALIZE_HANDOFF', 'ATTEMPT_TERMINAL',
                 'AWAITING_OPERATOR_REVIEW'):
        return {**basic, 'route': 'S3_POSTWORKER_REVIEW_ONLY',
                'next_action': 'CANONICAL_CF10_RESUME_WITHOUT_RELAUNCH'}
    if state == 'OBSERVE_WORKER':
        return {**basic, 'route': 'WORKER_IN_PROGRESS_OR_RESULT_PENDING',
                'next_action': 'OBSERVE_AND_RECONCILE_NO_RELAUNCH'}
    if claim != 'UNCONSUMED':
        return {**basic, 'route': 'CLAIM_NOT_FREE_FAIL_CLOSED',
                'next_action': 'MANUAL_DURABLE_CLAIM_REVIEW_NEVER_RETRY'}
    if counts != 0:
        return {**basic, 'route': 'LEDGER_NOT_EMPTY_FAIL_CLOSED',
                'next_action': 'MANUAL_CANONICAL_LEDGER_REVIEW'}
    if state != 'READY_FOR_WORKER_LAUNCH':
        return {**basic, 'route': 'CANONICAL_PREPARATION_OR_MANUAL_REVIEW',
                'next_action': 'MAKE_CF10_PILOT_PLAN_AND_RESUME_NONLAUNCH'}
    if (s.get('root_receipt_store') != 'PASS' or s.get('logs') != 'PASS' or
        s.get('preclaim') != 'PRECLAIM_ROOT_RECEIPT_VERIFIED_NON_AUTHORIZING' or
        s.get('preclaim_blockers') != []):
        return {**basic, 'route': 'PRECLAIM_OR_RUNTIME_BLOCKED',
                'next_action': 'MAKE_CF10_PILOT_PLAN_NO_LAUNCH'}
    if (s.get('proof') != 'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED' or
        s.get('proof_blockers') != [] or s.get('proof_lineage') != 'EXACT_RAW_BYTES_BOUND'):
        return {**basic, 'route': 'PROOF_LINEAGE_BLOCKED',
                'next_action': 'INDEPENDENT_EVIDENCE_REVIEW_NO_LAUNCH'}
    return {**basic, 'route': 'READY_FOR_EXPLICIT_ONE_SHOT_OWNER_PAM',
            'next_action': 'SEPARATE_MAKE_CF10_PILOT_LAUNCH_ONCE_WITH_OPERATOR_PAM',
            'launch_preparation_complete': True}


def doctor(*, root: Path, runtime: Path, task: str, attempt: str) -> dict:
    """Strict read-only server observation, no cached pass flags or chat state."""
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    from scripts.coordination.control_plane import cf10_pilot_cycle_v0_1 as pilot
    from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as guard

    _require(os.geteuid() == 0 and root == PROJECT and root.resolve() == PROJECT,
             'CANONICAL_ROOT_UID_REQUIRED')
    _require(runtime == RUNTIME and task == TASK70, 'EXACT_RUNTIME_AND_TASK70_REQUIRED')
    pilot.validate_selector(root, runtime, task, attempt)
    head = console.source_guard(root)
    s = pilot.snapshot(root, runtime, task, attempt)
    _require(s.get('source_head') == head, 'SOURCE_GUARD_MISMATCH')
    derived = next_route(s)
    facts = None
    # R052 observers are launch-window checks, not valid after consumption.
    if s.get('state') == 'READY_FOR_WORKER_LAUNCH' and s.get('claim') == 'UNCONSUMED':
        facts = guard._observe(root=root, runtime_root=runtime, task=task,
                               attempt=attempt, head=head)
        required = set(('automatic_retry_disabled', 'canonical_cycle_ready',
            'canonical_ledger_unstarted', 'frozen_input_current',
            'independent_finalizer_required', 'legacy_signed_release_separate',
            'preclaim_root_receipt_verified', 'release_candidate_raw_lineage_verified',
            'root_one_shot_claim_unconsumed', 'source_bound_pilot_make_route_verified',
            'source_bound_pilot_systemd_backend_verified', 'source_guard_verified',
            'systemd_worker_quiescent', 'writer_protocol_enforced'))
        _require(set(facts) == required and all(type(v) is bool for v in facts.values()),
                 'R052_OBSERVER_FIELDS_DRIFT')
        if derived['route'] == 'READY_FOR_EXPLICIT_ONE_SHOT_OWNER_PAM':
            _require(all(facts.values()), 'R052_PRE_PAM_LAUNCH_OBSERVATION_BLOCKED')
            # R075: the doctor must test the actual frozen manifest/gate budget
            # before claiming that this attempt is ready for separate PAM.
            pilot.assert_owner_preclaim_runtime(root=root, runtime=runtime,
                                                task=task, attempt=attempt, head=head)
    return {**derived, 'task_prompt_id': task, 'source_head': head,
            'frozen_head': s.get('frozen_head'), 'source_current': s.get('frozen_source_current'),
            'source_guard_verified': True, 'r052_observations': facts,
            'canonical_preclaim': s.get('preclaim'), 'canonical_proof': s.get('proof'),
            'canonical_proof_lineage': s.get('proof_lineage'),
            'snapshot_derived_non_authoritative': True,
            'evidence_issuer_invoked': False, 'systemd_touched': False,
            'operator_password_requested': False, 'canonical_ledger_modified': False,
            'source_modified': False, 'tmp_runtime_dependency': False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--runtime-root', type=Path, required=True)
    ap.add_argument('--task', required=True)
    ap.add_argument('--attempt', required=True)
    args = ap.parse_args(argv)
    try:
        result = doctor(root=args.root, runtime=args.runtime_root,
                        task=args.task, attempt=args.attempt)
        print(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        # Never reflect exception contents: they can include arguments/prompts.
        print(json.dumps({'schema_version': SCHEMA, 'status': 'BLOCKED_FAIL_CLOSED',
            'reason_class': type(exc).__name__, 'worker_launch_invoked': False,
            'automatic_retry': False, 'source_modified': False}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
