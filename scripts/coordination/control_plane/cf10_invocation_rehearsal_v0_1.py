"""Read-only canonical Worker invocation rehearsal (no Worker, STARTED, or authority).

Only checks an existing, prepared, explicitly dispatched attempt. It cannot
create an attempt or authorization, renew a signature, append a ledger record,
start a provider, or publish Git. Reuses the actual project-native launch
provenance checks and actual invocation adapter builder/evidence sanitizer.

The returned dictionary MUST NOT contain the generated prompt, full argv,
secrets or any unsanitized provider invocation object.
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

SHA256 = re.compile(r'^[a-f0-9]{64}$')
EXPECTED_FILES = (
    'manifest.yaml',
    'input/governed_worker_cycle_source_state_v0_1.yaml',
    'input/governed_worker_cycle_prepared_execution_v0_1.yaml',
    'input/governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml',
)


def finding(state: str, detail: str) -> dict[str, str]:
    if state not in {'PASS', 'BLOCKED', 'NOT_YET_TESTABLE'}:
        raise ValueError('INVALID_REHEARSAL_STATE')
    return {'id': 'invocation_rehearsal', 'status': state,
            'category': 'NON_AUTHORITY', 'detail': detail[:640]}


def safe_reason(exc: Exception) -> str:
    """Avoid accidental inclusion of prompt/argv/runtime secrets in reports."""
    text = str(exc)
    # Known bounded error messages only. Unknown errors expose class, not content.
    approved = (
        'frozen capsule ', 'Stage 4C ', 'B3 readback ',
        'project-native ', 'explicit dispatch ', 'runtime ',
        'prepared ', 'source ', 'workspace ', 'governed Worker ',
        'attempt ', 'original Handoff ', 'Worker ', 'configured ',
        'result transport ', 'transport ', 'dispatch/',
    )
    if (text.startswith(approved) and len(text) <= 190
            and '\n' not in text and '\r' not in text
            and not re.search(r'(token|secret|password|credential|api[_-]?key)', text, re.I)):
        # Never leak quotes, shell metacharacters or hidden access tokens.
        if re.fullmatch(r'[A-Za-z0-9_ .:/,=+()\[\]-]+', text):
            return type(exc).__name__ + ':' + text
    return type(exc).__name__ + ':DETAIL_WITHHELD_REVIEW_LOCALLY'


def inspect(root: Path, runtime: Path, task_id: str, attempt_id: str,
            worker_id: str = 'worker-01') -> dict[str, str]:
    """Build the actual provider plan without writing it or any ledger record."""
    if not re.fullmatch(r'cf10-[a-z0-9-]+-a[0-9]{3}', attempt_id):
        return finding('BLOCKED', 'INVALID_ATTEMPT_ID')
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', worker_id):
        return finding('BLOCKED', 'INVALID_WORKER_ID')
    root = Path(root).resolve()
    runtime = Path(runtime).resolve()
    attempt = runtime / 'forprint_system_blueprint' / worker_id / attempt_id
    guarded = (runtime, runtime / 'forprint_system_blueprint',
               runtime / 'forprint_system_blueprint' / worker_id, attempt,
               attempt / 'input', attempt / 'workspace', attempt / 'workspace/repo')
    if any(path.is_symlink() for path in guarded):
        return finding('BLOCKED', 'ATTEMPT_PATH_ANCESTOR_SYMLINK')
    if not attempt.is_dir():
        return finding('NOT_YET_TESTABLE', 'NO_ATTEMPT_CREATED: no preparation or authorization performed')
    for rel in EXPECTED_FILES:
        path = attempt / rel
        if path.is_symlink():
            return finding('BLOCKED', 'SYMLINK_REQUIRED_INPUT:' + rel)
        if not path.is_file():
            return finding('NOT_YET_TESTABLE', 'MISSING_PRELAUNCH_INPUT:' + rel)

    try:
        # The canonical launch code's exact input / proof / transport routines.
        from scripts.coordination.control_plane import governed_worker_cycle as cycle
        from scripts.coordination.control_plane.worker_runtime import invocation_adapter as inv
        source = cycle._load_yaml(
            attempt / 'input/governed_worker_cycle_source_state_v0_1.yaml', 'source state')
        prepared = cycle._load_yaml(
            attempt / 'input/governed_worker_cycle_prepared_execution_v0_1.yaml',
            'prepared execution')
        decision = cycle._load_yaml(
            attempt / 'input/governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml',
            'explicit dispatch decision')
        cycle._assert_frozen_source_state_current(
            root, source, boundary='non-authorizing invocation rehearsal')
        cycle._load_verified_original_handoff_manifest(
            attempt=attempt, prepared_execution=prepared, source_state=source)
        transport = cycle._resolve_stage4c_trusted_transport(
            root=root, prepared_execution=prepared,
            explicit_dispatch_decision=decision,
            expected_task_prompt_id=task_id, expected_attempt_id=attempt_id)
        readback = cycle._resolve_b3_trusted_readback(
            root=root, prepared_execution=prepared,
            explicit_dispatch_decision=decision,
            expected_task_prompt_id=task_id, expected_attempt_id=attempt_id)
        started_record, task_context = cycle._project_native_started_record(
            canonical=root, attempt=attempt, task_prompt_id=task_id,
            attempt_id=attempt_id, worker_id=worker_id,
            source_state=source, prepared_execution=prepared,
            explicit_dispatch_decision=decision)
        if started_record.get('attempt_stage') != 'STARTED' or started_record.get('result_state') != 'PENDING':
            raise ValueError('STARTED_RECORD_PREVIEW_INVALID')
        governed = cycle._validated_project_native_governed_worker_context(
            prepared_execution=prepared, explicit_dispatch_decision=decision)
        # Critical: canonical builder used by live launch; NEVER call cycle.launch_cycle,
        # launch_authorized_worker_cycle, launcher, append, or any write method.
        plan = inv.build_launch_invocation(
            root=root, task_context=task_context,
            explicit_dispatch_decision=decision, attempt_root=attempt,
            governed_worker_context=governed,
            result_transport=transport,
            validation_readback_selection=readback)
        evidence = inv.build_invocation_evidence(plan)
        if not isinstance(plan, dict) or not isinstance(evidence, dict):
            raise ValueError('INVOCATION_PLAN_NOT_MAPPING')
        for key in ('prompt_sha256', 'argv_sha256', 'invocation_sha256'):
            if not isinstance(evidence.get(key), str) or not SHA256.fullmatch(evidence[key]):
                raise ValueError('UNBOUND_INVOCATION_' + key.upper())
            if evidence.get(key) != plan.get(key):
                raise ValueError('INVOCATION_EVIDENCE_DRIFT_' + key.upper())
        if (plan.get('attempt_id') != attempt_id
                or evidence.get('attempt_id') != attempt_id
                or plan.get('command_representation') != 'ARGV_NO_SHELL'
                or evidence.get('command_representation') != 'ARGV_NO_SHELL'):
            raise ValueError('INVOCATION_ATTEMPT_OR_COMMAND_DRIFT')
        if plan.get('workspace_repo') != str((attempt / 'workspace/repo').resolve()):
            raise ValueError('INVOCATION_WORKSPACE_DRIFT')
        effects = plan.get('effects', {})
        for key in ('filesystem_write_performed', 'worker_process_started',
                    'attempt_ledger_appended', 'candidate_promoted',
                    'commit_performed', 'push_performed'):
            if effects.get(key) is not False:
                raise ValueError('INVOCATION_EFFECT_CONTRADICTION_' + key)
        auth = plan.get('authority', {})
        if auth.get('adapter_grants_authority') is not False:
            raise ValueError('ADAPTER_AUTHORITY_WIDENED')
        if evidence.get('serialization_boundary', {}).get('prompt_text_serialized') is not False:
            raise ValueError('PROMPT_SERIALIZATION_NOT_DISABLED')
        if evidence.get('serialization_boundary', {}).get('full_argv_serialized') is not False:
            raise ValueError('ARGV_SERIALIZATION_NOT_DISABLED')
        # Only metadata is returned. Prompt and argv stay in-process and are discarded.
        return finding('PASS', 'CANONICAL_INVOCATION_BUILDER_AND_EVIDENCE_PASS; '
            'invocation_sha256=' + evidence['invocation_sha256'] + '; '
            'prompt_sha256=' + evidence['prompt_sha256'] + '; '
            'argv_sha256=' + evidence['argv_sha256'] + '; '
            'WORKER_LAUNCHED=false; LEDGER_APPENDED=false; AUTHORITY_GRANTED=false')
    except Exception as exc:
        return finding('BLOCKED', safe_reason(exc))
