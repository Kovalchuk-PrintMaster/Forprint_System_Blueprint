"""R084: bounded operator provider assignment *preview*, no execution authority.

This route connects canonical Work Front/task discovery and source-state readback
with R080 provider-catalog selection. It is intentionally NOT connected to
prepare_cycle, operator ACK, dispatch, claim, PAM, systemd or finalizer.
Provider selection is explicit; no default provider or automatic fallback.
"""
from __future__ import annotations

from collections.abc import Mapping
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r080_catalog_assignment_v0_1 as assignment,
    registry,
)

SCHEMA = 'cf10_r084_operator_assignment_preview_v0_1'
ROOT = Path('/srv/software_development/forprint-project/forprint_system_blueprint')
RUNTIME = Path('/srv/software_development/forprint-worker-runtime')
FP = re.compile(r'[a-f0-9]{64}\Z')
HEAD = re.compile(r'[a-f0-9]{40}\Z')
NEEDED = ('completion_capture', 'non_interactive_prompt')
SAFE_ID = re.compile(r'[a-z][a-z0-9_-]{2,79}\Z')

class OperatorPlanBlocked(ValueError):
    pass


def deny(code: str) -> None:
    raise OperatorPlanBlocked('CF10_R084_' + code)


def digest(data: Mapping) -> str:
    return hashlib.sha256(json.dumps(dict(data), ensure_ascii=True,
        separators=(',', ':'), sort_keys=True).encode('utf-8')).hexdigest()


def build_preview(*, root: Path, task_binding: Mapping, source_state: Mapping,
                  attempt_id: str, worker_id: str, provider_id: str,
                  model_id: str) -> dict[str, Any]:
    """Pure selection preview from already trusted canonical inputs.

    This is NOT a frozen assignment and cannot be used in place of R082.
    Validation must also confirm the current trusted task/source at use time.
    """
    if not isinstance(task_binding, Mapping) or not isinstance(source_state, Mapping):
        deny('TRUSTED_TASK_AND_SOURCE_MAPPING_REQUIRED')
    task_id = task_binding.get('task_prompt_id')
    work_front = task_binding.get('work_front_id')
    if (not isinstance(task_id, str) or SAFE_ID.fullmatch(task_id) is None
        or not isinstance(work_front, str) or SAFE_ID.fullmatch(work_front) is None):
        deny('WORK_FRONT_TASK_IDENTITY_INVALID')
    head = source_state.get('git_head')
    fp = source_state.get('fingerprint_sha256')
    if not isinstance(head, str) or HEAD.fullmatch(head) is None:
        deny('SOURCE_HEAD_INVALID')
    if not isinstance(fp, str) or FP.fullmatch(fp) is None:
        deny('SOURCE_FINGERPRINT_INVALID')
    if not isinstance(provider_id, str) or SAFE_ID.fullmatch(provider_id) is None:
        deny('EXPLICIT_PROVIDER_ID_REQUIRED')
    if not isinstance(model_id, str) or not model_id:
        deny('EXPLICIT_MODEL_ID_REQUIRED')
    request = {
        'attempt_id': attempt_id,
        'source_head': head,
        'worker_id': worker_id,
        'task_id': task_id,
        'work_front_id': work_front,
        'provider_id': provider_id,
        'model_id': model_id,
        'capabilities_required': list(NEEDED),
    }
    try:
        chosen = assignment.choose_attempt_candidate(Path(root), request)
        assignment.validate_candidate_against_current_catalog(Path(root), chosen)
    except (assignment.AssignmentBlocked, registry.RuntimeRegistryError,
            ValueError, KeyError, TypeError) as exc:
        deny('CATALOG_SELECTION_UNAVAILABLE:' + type(exc).__name__)
    if (chosen['provider_id'] != provider_id or chosen['model_id'] != model_id
        or chosen['attempt_id'] != attempt_id or chosen['task_id'] != task_id
        or chosen['work_front_id'] != work_front or chosen['source_head'] != head):
        deny('CANDIDATE_IDENTITY_DRIFT')
    body = {
        'schema_version': SCHEMA,
        'task_id': task_id,
        'work_front_id': work_front,
        'attempt_id': attempt_id,
        'worker_id': worker_id,
        'provider_id': provider_id,
        'model_id': model_id,
        'source_head': head,
        'source_state_fingerprint_sha256': fp,
        'capabilities_required': list(NEEDED),
        'catalog_binding_sha256': chosen['catalog_binding_sha256'],
        'registry_sha256': chosen['registry_sha256'],
        'runtime_config_sha256': chosen['runtime_config_sha256'],
        'selected_provider_descriptor_sha256': chosen['selected_provider_descriptor_sha256'],
        'catalog_candidate': chosen,
        'status': 'CANDIDATE_ONLY_NOT_PREPARED_NOT_FROZEN',
        'eligible_for_live_dispatch': False,
        'candidate_only': True,
        'operator_selection_is_not_authorization': True,
        'provider_auth_verified': False,
        'automatic_fallback': False,
        'automatic_retry': False,
        'claim_consumed': False,
        'ledger_written': False,
        'worker_launched': False,
        'release_granted': False,
    }
    return {**body, 'preview_sha256': digest(body)}


def verify_preview(*, root: Path, preview: Mapping,
                   task_binding: Mapping, source_state: Mapping) -> bool:
    """Reproduce the exact plan from current trusted catalog/task/source facts."""
    if not isinstance(preview, Mapping) or preview.get('schema_version') != SCHEMA:
        deny('PREVIEW_SCHEMA')
    content = dict(preview)
    value = content.pop('preview_sha256', None)
    if not isinstance(value, str) or FP.fullmatch(value) is None or digest(content) != value:
        deny('PREVIEW_CONTENT_DIGEST')
    expected = build_preview(root=root, task_binding=task_binding,
        source_state=source_state, attempt_id=preview.get('attempt_id'),
        worker_id=preview.get('worker_id'), provider_id=preview.get('provider_id'),
        model_id=preview.get('model_id'))
    if dict(preview) != expected:
        deny('PREVIEW_NOT_REPRODUCIBLE')
    return True


def live_preview(*, root: Path, runtime_root: Path, task_id: str,
                 attempt_id: str, worker_id: str, provider_id: str,
                 model_id: str) -> dict[str, Any]:
    """Read-only canonical task/head/ledger check; never provision an attempt."""
    root = Path(root)
    runtime_root = Path(runtime_root)
    if (root != ROOT or root.is_symlink() or not root.is_dir()
        or runtime_root != RUNTIME or runtime_root.is_symlink()
        or not runtime_root.is_dir()):
        deny('EXACT_CANONICAL_ROOTS_REQUIRED')
    from scripts.coordination.control_plane import cf10_training_dispatch as training
    from scripts.coordination.control_plane.context.task_context_adapter import build_source_state
    if worker_id != 'worker-01':
        deny('CURRENT_PILOT_WORKER_REQUIRED')
    if not isinstance(task_id, str) or SAFE_ID.fullmatch(task_id) is None:
        deny('TASK_ID_INVALID')
    # The preview may only concern an unused, not-yet-prepared attempt.
    training.assert_attempt_unused(root=root, attempt_id=attempt_id)
    attempt = runtime_root / 'forprint_system_blueprint' / worker_id / attempt_id
    if attempt.is_symlink() or attempt.exists():
        deny('ATTEMPT_ALREADY_EXISTS_NO_REBIND')
    binding = training.resolve_training_task(root=root, task_prompt_id=task_id)
    source = build_source_state(root)
    preview = build_preview(root=root, task_binding=binding, source_state=source,
        attempt_id=attempt_id, worker_id=worker_id,
        provider_id=provider_id, model_id=model_id)
    verify_preview(root=root, preview=preview, task_binding=binding, source_state=source)
    return preview


def inspect(root: Path) -> dict[str, Any]:
    catalog = registry.load_runtime_registry(root)
    ready = sorted(row['provider_id'] for row in catalog['providers']
        if row.get('state') == 'READY' and row.get('ready') is True)
    configured = registry.resolve_default_runtime(root)
    return {
        'schema_version': SCHEMA,
        'status': 'OPERATOR_PLAN_AVAILABLE_NO_LIVE_PROVIDER_ROUTING',
        'ready_provider_ids': ready,
        'configured_legacy_default': configured['provider_id'],
        'explicit_provider_required_for_plan': True,
        'codex_launch_enabled': False,
        'claude_launch_enabled': False,
        'live_dispatch_provider_selection_wired': False,
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
        'automatic_fallback': False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('inspect', 'plan'), required=True)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--runtime-root', type=Path, default=RUNTIME)
    args = parser.parse_args(argv)
    try:
        if args.mode == 'inspect':
            result = inspect(args.root)
        else:
            values = {key: os.environ.get(key, '') for key in
                ('CF10_TASK', 'CF10_ATTEMPT', 'CF10_PROVIDER', 'CF10_MODEL', 'CF10_WORKER')}
            if not values['CF10_WORKER']:
                values['CF10_WORKER'] = 'worker-01'
            result = live_preview(root=args.root, runtime_root=args.runtime_root,
                task_id=values['CF10_TASK'], attempt_id=values['CF10_ATTEMPT'],
                provider_id=values['CF10_PROVIDER'], model_id=values['CF10_MODEL'],
                worker_id=values['CF10_WORKER'])
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (OperatorPlanBlocked, assignment.AssignmentBlocked, registry.RuntimeRegistryError,
            OSError, ValueError, KeyError, TypeError) as exc:
        print('CF10_R084_BLOCKED=' + type(exc).__name__ + ':' + str(exc)[:150])
        print('CF10_R084_NO_WORKER_NO_CLAIM=true')
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
