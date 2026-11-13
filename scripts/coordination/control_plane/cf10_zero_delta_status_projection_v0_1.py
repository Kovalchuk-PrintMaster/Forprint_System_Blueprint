#!/usr/bin/env python3
"""Derived CF-10 zero-delta operator-review overlay, never execution authority.

S2C deliberately leaves governed_worker_cycle.status unchanged: its ordinary
operator_review_passed fact controls the promotion corridor, which is not valid
for zero-delta. Delegates LIVE evidence checks to the canonical S2B evaluate().
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable
import yaml

SCHEMA = 'cf10_zero_delta_review_status_projection_v0_1'
DECISION_SCHEMA = 'cf10_zero_delta_operator_decision_v0_1'
DECISION_DIR = Path('coordination/continuity/worker_result_decisions')
SHA64 = re.compile(r'^[0-9a-f]{64}$')
TOKEN = re.compile(r'^[a-z0-9][a-z0-9-]{2,110}$')
STATES = {
    'ACCEPT': ('ZERO_DELTA_OPERATOR_ACCEPTED', 'ROADMAP_OPERATOR_PLANNING_REVIEW_NOT_DISPATCH'),
    'HOLD': ('ZERO_DELTA_OPERATOR_HELD', 'HOLD_SUPERSESSION_POLICY_REVIEW'),
    'RETURN': ('ZERO_DELTA_OPERATOR_RETURNED', 'EXPLICIT_REWORK_AUTHORIZATION_REVIEW'),
}

class ProjectionBlocked(RuntimeError):
    pass


def require(value: bool, error: str) -> None:
    if not value:
        raise ProjectionBlocked(error)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_s2b_evaluate(root: Path, runtime: Path, proof: Path, task: str, attempt: str) -> dict:
    from scripts.coordination.control_plane.cf10_zero_delta_operator_review_v0_1 import evaluate
    return evaluate(root, runtime, proof, task, attempt)


def project(root: Path, runtime: Path, proof: Path, task: str, attempt: str,
            *, evaluator: Callable | None = None) -> dict[str, Any]:
    root = root.resolve(strict=True)
    require(bool(TOKEN.fullmatch(attempt)) and bool(TOKEN.fullmatch(task)), 'INVALID_ATTEMPT_OR_TASK')
    preview = (evaluator or native_s2b_evaluate)(root, runtime, proof, task, attempt)
    require(isinstance(preview, dict), 'S2B_PREVIEW_NOT_MAPPING')
    require(preview.get('schema_version') == 'cf10_zero_delta_operator_review_preview_v0_1', 'S2B_SCHEMA_INVALID')
    require(preview.get('attempt_id') == attempt and preview.get('task_prompt_id') == task, 'S2B_IDENTITY_MISMATCH')
    require(preview.get('governed_state') == 'AWAITING_OPERATOR_REVIEW', 'UNEXPECTED_BASE_GOVERNED_STATE')
    for flag in ('automatic_accept', 'automatic_commit', 'automatic_push', 'automatic_publication',
                 'governed_status_changed_by_this_tool', 'historical_exit_attestation',
                 'zero_delta_promotion_required'):
        require(preview.get(flag) is False, 'S2B_AUTHORITY_OR_TIME_SCOPE_INVALID:'+flag)
    binding = preview.get('decision_binding_sha256')
    require(isinstance(binding, str) and bool(SHA64.fullmatch(binding)), 'S2B_BINDING_INVALID')
    bound = preview.get('bound_evidence')
    require(isinstance(bound, dict) and bound.get('temporal_scope') == 'CURRENT_WORKSPACE_AT_REVIEW_NOT_HISTORICAL_EXIT', 'S2B_BOUND_EVIDENCE_INVALID')
    require(bound.get('attempt_id') == attempt and bound.get('task_prompt_id') == task, 'S2B_BOUND_IDENTITY_INVALID')
    rows = preview.get('existing_decisions')
    require(isinstance(rows, list) and len(rows) <= 1, 'S2B_DECISION_CARDINALITY_INVALID')
    require(preview.get('operator_decision_recorded') is (len(rows) == 1), 'S2B_DECISION_FLAG_CONTRADICTION')
    expected_preview_status = 'EXISTING_OPERATOR_DECISION' if rows else 'READY_FOR_EXPLICIT_OPERATOR_DECISION'
    require(preview.get('status') == expected_preview_status, 'S2B_PREVIEW_STATUS_CONTRADICTION')
    base = {'schema_version': SCHEMA, 'report_role': 'DERIVED_READ_ONLY_NON_AUTHORITATIVE',
            'attempt_id': attempt, 'task_prompt_id': task,
            'work_front_id': preview.get('work_front_id'),
            'governed_cycle_base_state': 'AWAITING_OPERATOR_REVIEW',
            'governed_cycle_base_state_unchanged': True,
            'decision_binding_sha256': binding,
            'decision': None, 'decision_id': None, 'decision_record_sha256': None,
            'operator_decision_recorded': False,
            'historical_worker_exit_attested': False,
            'zero_delta_promotion_required': False, 'automatic_accept': False,
            'automatic_commit': False, 'automatic_push': False,
            'automatic_publication': False, 'canonical_mutation_performed': False,
            'next_dispatch_authorized': False, 'roadmap_lifecycle_closed': False}
    if not rows:
        return {**base, 'review_overlay_state': 'AWAITING_EXPLICIT_ZERO_DELTA_REVIEW',
                'next_boundary': 'EXPLICIT_HUMAN_OPERATOR_DECISION',
                'next_action_requires_authority': 'HUMAN_OPERATOR',
                'review_evidence_validated': True}
    row = rows[0]
    require(isinstance(row, dict), 'DECISION_ROW_INVALID')
    expected_rel = (DECISION_DIR / f'{attempt}__zero_delta_operator_decision_v0_1.yaml').as_posix()
    require(row.get('path') == expected_rel, 'DECISION_PATH_NOT_CANONICAL')
    target = root / expected_rel
    require(target.is_file() and not target.is_symlink(), 'DECISION_FILE_MISSING_OR_SYMLINK')
    actual_sha = file_sha256(target)
    require(row.get('sha256') == actual_sha, 'DECISION_CHANGED_SINCE_S2B_PREVIEW')
    value = yaml.safe_load(target.read_bytes())
    require(isinstance(value, dict) and value == row.get('record'), 'DECISION_READBACK_INCONSISTENT')
    decision = value.get('decision')
    require(value.get('schema_version') == DECISION_SCHEMA and decision in STATES, 'DECISION_SCHEMA_OR_ENUM_INVALID')
    require(value.get('record_role') == 'zero_delta_operator_decision_not_promotion_or_publication', 'DECISION_ROLE_INVALID')
    require(value.get('attempt_id') == attempt and value.get('task_prompt_id') == task, 'DECISION_IDENTITY_INVALID')
    require(value.get('work_front_id') == preview.get('work_front_id'), 'DECISION_WORK_FRONT_INVALID')
    require(value.get('review_binding_sha256') == binding, 'DECISION_PROOF_BINDING_MISMATCH')
    require(value.get('evidence_bindings') == bound, 'DECISION_EVIDENCE_BINDINGS_MISMATCH')
    for key in ('decision_id', 'operator_ref'):
        require(isinstance(value.get(key), str) and bool(TOKEN.fullmatch(value[key])), 'DECISION_OPERATOR_ID_INVALID:'+key)
    try:
        stamp = datetime.fromisoformat(str(value['recorded_at']))
    except (KeyError, ValueError, TypeError) as exc:
        raise ProjectionBlocked('DECISION_TIME_MALFORMED') from exc
    require(stamp.tzinfo is not None, 'DECISION_TIME_HAS_NO_TIMEZONE')
    for key in ('zero_delta_confirmed_current_workspace',):
        require(value.get(key) is True, 'DECISION_CURRENT_WORKSPACE_ACK_MISSING')
    for key in ('historical_exit_attestation', 'canonical_promotion_performed',
                'commit_performed', 'push_performed', 'governed_status_projection_updated'):
        require(value.get(key) is False, 'DECISION_AUTHORITY_WIDENED:'+key)
    require(value.get('publication_state') == 'NOT_ATTESTED', 'DECISION_PUBLICATION_CLAIM_INVALID')
    require(value.get('next_boundary') == 'ZERO_DELTA_STATUS_POLICY_RECONCILIATION', 'DECISION_ORIGINAL_BOUNDARY_INVALID')
    derived_state, next_boundary = STATES[decision]
    return {**base, 'decision': decision, 'decision_id': value['decision_id'],
            'decision_record_sha256': actual_sha,
            'operator_decision_recorded': True,
            'review_overlay_state': derived_state,
            'next_boundary': next_boundary,
            'next_action_requires_authority': 'HUMAN_OPERATOR_OR_GOVERNED_ROADMAP_POLICY',
            'review_evidence_validated': True}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('preview',))
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--runtime-root', type=Path, default=Path('/srv/software_development/forprint-worker-runtime'))
    p.add_argument('--proof-file', type=Path, required=True)
    p.add_argument('--task', required=True)
    p.add_argument('--attempt-id', required=True)
    p.add_argument('--format', choices=('yaml', 'json'), default='yaml')
    args = p.parse_args(argv)
    try:
        sys.path.insert(0, str(args.root.resolve(strict=True)))
        result = project(args.root, args.runtime_root, args.proof_file, args.task, args.attempt_id)
        if args.format == 'json':
            print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True))
        return 0
    except (ProjectionBlocked, ValueError, OSError, TypeError, yaml.YAMLError) as exc:
        print('CF10_S2C_PROJECTION_BLOCKED=' + str(exc), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
