"""R085: exact operator provider plan -> canonical prepare, Copilot-only.

Explicit operator command, NOT provider authorization, PAM, claim or launch.
Canonical prepare independently revalidates the plan before workspace writes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r084_operator_assignment_plan_v0_1 as assignment,
    cf10_r082_frozen_assignment_v0_1 as frozen,
)

ROOT = assignment.ROOT
RUNTIME = assignment.RUNTIME
CONFIRM = 'PREPARE_EXPLICIT_COPILOT_NO_LAUNCH'
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
WORKER = 'worker-01'


class OperatorPrepareBlocked(ValueError):
    pass


def deny(message: str) -> None:
    raise OperatorPrepareBlocked('CF10_R085_' + message)


def inspect() -> dict:
    return {
        'schema_version': 'cf10_r085_operator_prepare_bridge_v0_1',
        'status': 'EXPLICIT_COPILOT_PREPARE_BRIDGE_NOT_LAUNCH',
        'provider_id': frozen.CURRENT_PILOT_PROVIDER,
        'model_id': frozen.CURRENT_PILOT_MODEL,
        'other_provider_prepare_enabled': False,
        'provider_auth_verified': False,
        'operator_confirmation_required': True,
        'automatic_retry': False,
        'automatic_fallback': False,
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
    }


def prepare_selected(*, root: Path, runtime_root: Path, task_id: str,
                     attempt_id: str, worker_id: str, provider_id: str,
                     model_id: str, confirm: str) -> dict:
    """One bounded, operator-explicit prepare; never ACK or dispatch."""
    from scripts.coordination.control_plane import governed_worker_cycle as cycle

    root = Path(root)
    runtime_root = Path(runtime_root)
    if (root != ROOT or runtime_root != RUNTIME or root.is_symlink()
        or runtime_root.is_symlink() or not root.is_dir() or not runtime_root.is_dir()):
        deny('CANONICAL_ROOTS_REQUIRED')
    if os.geteuid() != 0 or not os.isatty(0) or not os.isatty(1):
        deny('INTERACTIVE_ROOT_REQUIRED')
    if confirm != CONFIRM:
        deny('EXPLICIT_PREPARE_CONFIRMATION_REQUIRED')
    if task_id != TASK or worker_id != WORKER:
        deny('CURRENT_EXACT_TRAINING_TASK_AND_WORKER_REQUIRED')
    if provider_id != frozen.CURRENT_PILOT_PROVIDER or model_id != frozen.CURRENT_PILOT_MODEL:
        deny('SECOND_PROVIDER_PREPARE_NOT_AUTHORIZED')

    # Canonical task, unused ledger, absent runtime, source fingerprint, READY
    # provider and SHA-bound candidate are checked by R084. This cannot create
    # or modify an attempt. Canonical prepare rechecks against current inputs.
    plan = assignment.live_preview(
        root=root, runtime_root=runtime_root, task_id=task_id,
        attempt_id=attempt_id, worker_id=worker_id,
        provider_id=provider_id, model_id=model_id,
    )
    if (plan.get('candidate_only') is not True
        or plan.get('eligible_for_live_dispatch') is not False
        or plan.get('claim_consumed') is not False
        or plan.get('worker_launched') is not False):
        deny('NON_CANDIDATE_PROVIDER_PLAN')

    prepared = cycle.prepare_cycle(
        root=root, runtime_root=runtime_root,
        task_prompt_id=task_id, attempt_id=attempt_id,
        worker_id=worker_id, operator_provider_preview=plan,
    )
    if (prepared.get('state') != 'AWAITING_ASSISTANT_ACK'
        or prepared.get('operator_preview_sha256') != plan['preview_sha256']
        or prepared.get('operator_provider_id') != provider_id
        or prepared.get('worker_launch_performed') is not False):
        deny('CANONICAL_PREPARE_RESULT_NOT_EXACT_REVIEW_ATTEMPT_NO_RETRY')
    return {
        'schema_version': 'cf10_r085_operator_prepare_result_v0_1',
        'status': 'PREPARED_AWAITING_ASSISTANT_ACK_NO_DISPATCH',
        'attempt_id': attempt_id,
        'task_id': task_id,
        'worker_id': worker_id,
        'provider_id': provider_id,
        'model_id': model_id,
        'source_head': plan['source_head'],
        'operator_preview_sha256': plan['preview_sha256'],
        'state': 'AWAITING_ASSISTANT_ACK',
        'next_boundary': 'EXPLICIT_ASSISTANT_ACK',
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
        'automatic_retry': False,
        'automatic_fallback': False,
        'authorization_granted': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', required=True, choices=('inspect', 'prepare'))
    args = parser.parse_args(argv)
    try:
        if args.mode == 'inspect':
            result = inspect()
        else:
            values = {k: os.environ.get(k, '') for k in (
                'CF10_TASK', 'CF10_ATTEMPT', 'CF10_WORKER', 'CF10_PROVIDER',
                'CF10_MODEL', 'CF10_CONFIRM_PREPARE')}
            result = prepare_selected(
                root=ROOT, runtime_root=RUNTIME,
                task_id=values['CF10_TASK'], attempt_id=values['CF10_ATTEMPT'],
                worker_id=values['CF10_WORKER'] or WORKER,
                provider_id=values['CF10_PROVIDER'], model_id=values['CF10_MODEL'],
                confirm=values['CF10_CONFIRM_PREPARE'],
            )
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (OperatorPrepareBlocked, assignment.OperatorPlanBlocked,
            OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        # This is a human terminal command; failure never creates a retry.
        # Avoid printing raw exceptions which may contain provider credentials.
        print('CF10_R085_BLOCKED=' + type(exc).__name__)
        print('CF10_R085_NO_WORKER_NO_CLAIM=true')
        print('CF10_R085_IF_PARTIAL_PREPARE_REVIEW_ATTEMPT_DO_NOT_RETRY=true')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
