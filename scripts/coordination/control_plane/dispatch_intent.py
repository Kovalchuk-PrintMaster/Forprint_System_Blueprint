from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DISPATCH_INTENT_SCHEMA = "forprint_dispatch_intent_v0_1"
STATE_BLOCKED = "BLOCKED"
STATE_READY = "READY_FOR_EXPLICIT_DISPATCH"


@dataclass(frozen=True)
class DispatchIntentResult:
    state: str
    blocker_codes: tuple[str, ...]
    document: dict[str, Any]


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for c in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def _load(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be mapping")
    return data


def _nested(data: dict[str, Any], *keys: str) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _decision_fields(data: dict[str, Any] | None) -> tuple[Any, Any, Any]:
    if data is None:
        return None, None, None
    d = data.get("decision")
    value = (d.get("value") or d.get("decision")) if isinstance(d, dict) else d
    did = data.get("decision_id") or _nested(data, "identity", "decision_id")
    rid = (
        data.get("request_id")
        or _nested(data, "authority_binding", "request_id")
        or _nested(data, "launch_request", "request_id")
    )
    return value, did, rid


def _wip_conflict(paths: list[Path], module_id: str) -> bool:
    for path in paths:
        if not path.is_file():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        observed = data.get("module_id") or _nested(data, "identity", "module_id")
        if observed == module_id and data.get("state") in {"DISPATCHED", "RUNNING"}:
            return True
    return False


def build_dispatch_intent(
    *,
    launch_request_path: Path,
    worker_invocation_path: Path,
    approval_decision_path: Path | None = None,
    active_execution_paths: list[Path] | None = None,
) -> DispatchIntentResult:
    launch_request_path = launch_request_path.resolve()
    worker_invocation_path = worker_invocation_path.resolve()
    approval_decision_path = approval_decision_path.resolve() if approval_decision_path else None
    active_execution_paths = list(active_execution_paths or [])
    launch = _load(launch_request_path, "launch request")
    invocation = _load(worker_invocation_path, "worker invocation")
    approval = (
        _load(approval_decision_path, "approval decision") if approval_decision_path else None
    )

    module_id = _nested(launch, "identity", "module_id")
    prompt_id = _nested(launch, "identity", "prompt_id")
    request_id = launch.get("request_id")
    blockers: list[str] = []
    if launch.get("state") != "AWAITING_OPERATOR_APPROVAL":
        blockers.append("LAUNCH_REQUEST_NOT_AWAITING_OPERATOR_APPROVAL")

    value, decision_id, approval_request_id = _decision_fields(approval)
    approval_valid = _nested(invocation, "authority_binding", "approval_valid_for_dispatch") is True
    invocation_decision_id = _nested(invocation, "authority_binding", "approval_decision_id")
    if not (
        value == "APPROVE"
        and decision_id
        and approval_request_id == request_id
        and approval_valid
        and invocation_decision_id == decision_id
    ):
        blockers.append("VALID_APPROVE_DECISION_NOT_BOUND")

    if not (
        invocation.get("state") == "DRY_RUN_READY"
        and _nested(invocation, "eligibility", "dry_run_ready") is True
        and _nested(invocation, "eligibility", "future_dispatch_eligible") is True
        and _nested(invocation, "console_command", "subprocess_started") is False
    ):
        blockers.append("WORKER_INVOCATION_NOT_DRY_RUN_READY")

    if module_id != _nested(invocation, "identity", "module_id") or prompt_id != _nested(
        invocation, "identity", "prompt_id"
    ):
        blockers.append("ARTIFACT_IDENTITY_MISMATCH")

    launch_head = _nested(launch, "repository_revalidation", "module_head")
    invocation_head = _nested(invocation, "authority_binding", "module_head")
    if launch_head and invocation_head and launch_head != invocation_head:
        blockers.append("MODULE_HEAD_MISMATCH")
    if isinstance(module_id, str) and _wip_conflict(active_execution_paths, module_id):
        blockers.append("MODULE_WIP_CONFLICT")

    blockers_tuple = tuple(sorted(set(blockers)))
    state = STATE_READY if not blockers_tuple else STATE_BLOCKED
    stable = {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "request_id": request_id,
        "launch_sha256": _sha(launch_request_path),
        "approval_sha256": _sha(approval_decision_path) if approval_decision_path else None,
        "invocation_sha256": _sha(worker_invocation_path),
        "module_head": invocation_head or launch_head,
    }
    fp = hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    intent_id = f"{module_id}__{prompt_id}__dispatch__{fp[:16]}"
    doc = {
        "schema_version": DISPATCH_INTENT_SCHEMA,
        "dispatch_intent_id": intent_id,
        "state": state,
        "identity": {
            "module_id": module_id,
            "prompt_id": prompt_id,
            "request_id": request_id,
            "approval_decision_id": decision_id,
            "worker_invocation_id": invocation.get("invocation_id"),
            "dispatch_fingerprint_sha256": fp,
        },
        "authority_binding": {
            "launch_request_path": str(launch_request_path),
            "launch_request_sha256": stable["launch_sha256"],
            "approval_decision_path": str(approval_decision_path)
            if approval_decision_path
            else None,
            "approval_decision_sha256": stable["approval_sha256"],
            "worker_invocation_path": str(worker_invocation_path),
            "worker_invocation_sha256": stable["invocation_sha256"],
            "module_head": stable["module_head"],
        },
        "eligibility": {
            "ready_for_explicit_dispatch": state == STATE_READY,
            "wip_limit": 1,
            "wip_conflict": "MODULE_WIP_CONFLICT" in blockers_tuple,
            "blocker_count": len(blockers_tuple),
            "blocker_codes": list(blockers_tuple),
        },
        "execution_boundaries": {
            "explicit_dispatch_still_required": True,
            "worker_process_start_allowed_by_this_component": False,
            "worker_process_started": False,
            "prompt_claim_performed": False,
            "module_repository_write_performed": False,
            "blueprint_accept_performed": False,
            "next_prompt_release_performed": False,
        },
    }
    return DispatchIntentResult(state, blockers_tuple, doc)


# ============================================================================
# CF-09 Dispatcher integration — bounded TASK_EXECUTION preparation only
# ============================================================================
# This layer prepares and validates one bounded execution package.
# It does NOT launch a worker, grant dispatch authority, release, push or merge.
CF09_TASK_EXECUTION_PREPARE_V0_1 = "CF09_TASK_EXECUTION_PREPARE_V0_1"


def _cf09_parse_key_value_output(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key.replace("_", "").isalnum():
            values[key] = value.strip()
    return values


def _cf09_safe_value(value: str, *, label: str) -> str:
    import re as _re

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    if not _re.fullmatch(r"[A-Za-z0-9_.:/@+-]{1,500}", normalized):
        raise ValueError(f"{label} contains unsupported characters")
    return normalized


def prepare_cf09_task_execution(
    *,
    root,
    work_front: str,
    execution_profile: str,
    task_prompt_id: str,
    task_module_root: str,
    module: str | None = None,
    procedure_id: str | None = None,
    procedure_not_required_reason: str | None = None,
    runner=None,
) -> dict:
    import re as _re
    import subprocess as _subprocess
    import sys as _sys
    from pathlib import Path as _Path

    root_path = _Path(root).resolve()
    front_id = _cf09_safe_value(work_front, label="work_front")
    profile_ref = _cf09_safe_value(
        execution_profile,
        label="execution_profile",
    )
    prompt_id = _cf09_safe_value(task_prompt_id, label="task_prompt_id")
    module_root = _cf09_safe_value(
        task_module_root,
        label="task_module_root",
    )
    module_id = _cf09_safe_value(module, label="module") if module else None

    if bool(procedure_id) == bool(procedure_not_required_reason):
        raise ValueError("exactly one of procedure_id or procedure_not_required_reason is required")

    procedure = _cf09_safe_value(procedure_id, label="procedure_id") if procedure_id else None
    no_procedure_reason = (
        _cf09_safe_value(
            procedure_not_required_reason,
            label="procedure_not_required_reason",
        )
        if procedure_not_required_reason
        else None
    )

    run = runner or _subprocess.run

    work_front_runtime = root_path / "scripts/coordination/work_front_v0_1.py"
    if not work_front_runtime.is_file():
        raise RuntimeError("Work Front runtime missing")

    wf = run(
        [
            _sys.executable,
            str(work_front_runtime),
            "--root",
            str(root_path),
            "--front",
            front_id,
            "--action",
            "dispatch",
        ],
        cwd=root_path,
        text=True,
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        check=False,
    )
    wf_values = _cf09_parse_key_value_output(wf.stdout)
    if wf.returncode != 0 or wf_values.get("WORK_FRONT_VALIDATION") != "PASS":
        raise RuntimeError("Work Front dispatch gate failed")

    args = [
        "make",
        "-s",
        "assistant-handoff-v2-task-execution",
        f"FRONT={front_id}",
        f"EXECUTION_PROFILE={profile_ref}",
        f"TASK_PROMPT_ID={prompt_id}",
        f"TASK_MODULE_ROOT={module_root}",
    ]
    if module_id:
        args.append(f"MODULE={module_id}")
    if procedure:
        args.append(f"PROCEDURE_ID={procedure}")
    else:
        args.append(f"PROCEDURE_NOT_REQUIRED_REASON={no_procedure_reason}")

    handoff = run(
        args,
        cwd=root_path,
        text=True,
        stdout=_subprocess.PIPE,
        stderr=_subprocess.STDOUT,
        check=False,
    )
    values = _cf09_parse_key_value_output(handoff.stdout)
    if handoff.returncode != 0:
        raise RuntimeError("Handoff v2 TASK_EXECUTION preparation failed")

    required_exact = {
        "ASSISTANT_HANDOFF_V2_RUNTIME": "PASS",
        "LAUNCH_MODE": "TASK_EXECUTION",
        "EXECUTION_AUTHORITY_GRANTED": "false",
        "DISPATCH_AUTHORITY_GRANTED": "false",
        "WORKER_DISPATCH_PERFORMED": "false",
    }
    for key, expected in required_exact.items():
        if values.get(key) != expected:
            raise RuntimeError(f"Handoff v2 safety marker mismatch: {key}={values.get(key)!r}")

    manifest_sha = values.get("HANDOFF_MANIFEST_SHA256", "")
    if not _re.fullmatch(r"[0-9a-f]{64}", manifest_sha):
        raise RuntimeError("Handoff v2 manifest hash missing or invalid")

    return {
        "schema_version": "forprint_cf09_dispatcher_pre_execution_envelope_v0_1",
        "mode": "TASK_EXECUTION",
        "state": "AWAITING_ASSISTANT_ACK",
        "assistant_ack_validated": False,
        "module": module_id,
        "work_front_id": front_id,
        "execution_profile_ref": profile_ref,
        "task_prompt_id": prompt_id,
        "task_module_root": module_root,
        "procedure_id": procedure,
        "procedure_not_required_reason": no_procedure_reason,
        "handoff_manifest_sha256": manifest_sha,
        "work_front_gate": {
            "validated": True,
            "work_front_id": wf_values.get("WORK_FRONT_ID", front_id),
            "work_front_path": wf_values.get("WORK_FRONT_PATH"),
        },
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
        },
        "next_required_human_boundary": "ASSISTANT_ACK_REQUIRED",
    }


def write_cf09_dry_attempt_envelope(
    *,
    root,
    attempt_id: str,
    envelope: dict,
):
    import json as _json
    from pathlib import Path as _Path

    root_path = _Path(root).resolve()
    safe_attempt = _cf09_safe_value(
        attempt_id,
        label="attempt_id",
    )
    out_root = (root_path / "tmp/dispatcher_attempts").resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    output = (out_root / f"{safe_attempt}.json").resolve()
    try:
        output.relative_to(out_root)
    except ValueError as exc:
        raise ValueError("attempt output escapes tmp/dispatcher_attempts") from exc

    payload = dict(envelope)
    payload["attempt_id"] = safe_attempt
    payload["fact_authority"] = "none"
    payload["canonical_execution_attempt_ledger_written"] = False
    payload["worker_dispatch_performed"] = False

    output.write_text(
        _json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


# ============================================================================
# CF-09 Dispatcher integration — result/attempt/telemetry/retry/resume glue
# ============================================================================
CF09_ATTEMPT_RESULT_INTEGRATION_V0_1 = "CF09_ATTEMPT_RESULT_INTEGRATION_V0_1"


def _cf09_load_runtime_module(root, relative_path: str, module_name: str):
    import importlib.util as _importlib_util
    import sys as _sys
    from pathlib import Path as _Path

    path = _Path(root).resolve() / relative_path
    if not path.is_file():
        raise RuntimeError(f"required CF09 runtime missing: {relative_path}")
    spec = _importlib_util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load CF09 runtime: {relative_path}")
    module = _importlib_util.module_from_spec(spec)
    _sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cf09_find_unique_int_key(value, key: str) -> int:
    hits = []

    def visit(node):
        if isinstance(node, dict):
            if key in node:
                hits.append(node[key])
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    ints = [item for item in hits if isinstance(item, int) and not isinstance(item, bool)]
    unique = sorted(set(ints))
    if len(unique) != 1:
        raise RuntimeError(f"expected one integer {key}, found {unique!r}")
    return unique[0]


def _cf09_retry_budget(*, root, requested_max_attempts: int | None) -> dict:
    from pathlib import Path as _Path

    contract_path = (
        _Path(root).resolve() / "coordination/standards/automation/"
        "assistant_handoff_v2_result_contract_v0_1.yaml"
    )
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise RuntimeError("Handoff v2 result contract must be mapping")

    default_max = _cf09_find_unique_int_key(contract, "max_attempts_default")
    hard_ceiling = _cf09_find_unique_int_key(contract, "max_attempts_hard_ceiling")
    requested = default_max if requested_max_attempts is None else requested_max_attempts
    if not isinstance(requested, int) or isinstance(requested, bool) or requested < 1:
        raise ValueError("requested_max_attempts must be a positive integer")
    effective = min(requested, hard_ceiling)
    return {
        "default_max_attempts": default_max,
        "hard_ceiling": hard_ceiling,
        "requested_max_attempts": requested,
        "effective_max_attempts": effective,
        "clamped_to_hard_ceiling": requested > hard_ceiling,
    }


def _cf09_retry_decision(
    *,
    status: str,
    attempt_number: int,
    retry_budget: dict,
    current_attempt_id: str,
    next_attempt_id: str | None,
) -> dict:
    if (
        not isinstance(attempt_number, int)
        or isinstance(attempt_number, bool)
        or attempt_number < 1
    ):
        raise ValueError("attempt_number must be a positive integer")

    effective_max = retry_budget["effective_max_attempts"]
    if status == "PASS":
        return {
            "decision": "NO_RETRY_RESULT_PASS",
            "retry_allowed": False,
            "next_attempt_id": None,
            "human_boundary_required": False,
        }
    if status != "RETRYABLE_FAILURE":
        return {
            "decision": "ESCALATE_NON_RETRYABLE_RESULT",
            "retry_allowed": False,
            "next_attempt_id": None,
            "human_boundary_required": True,
        }
    if attempt_number >= effective_max:
        return {
            "decision": "ESCALATE_RETRY_CEILING_REACHED",
            "retry_allowed": False,
            "next_attempt_id": None,
            "human_boundary_required": True,
        }
    if not next_attempt_id:
        return {
            "decision": "RETRY_REQUIRES_NEW_ATTEMPT_ID",
            "retry_allowed": False,
            "next_attempt_id": None,
            "human_boundary_required": True,
        }

    safe_next = _cf09_safe_value(next_attempt_id, label="next_attempt_id")
    if safe_next == current_attempt_id:
        raise ValueError("retry must create a new attempt_id")
    return {
        "decision": "RETRY_ELIGIBLE_REQUIRES_EXPLICIT_DISPATCH",
        "retry_allowed": True,
        "next_attempt_id": safe_next,
        "retry_of_attempt_id": current_attempt_id,
        "human_boundary_required": True,
    }


def _cf09_write_telemetry_projection(
    *,
    root,
    attempt_id: str,
    payload: dict,
    telemetry_root_override=None,
):
    import json as _json
    from pathlib import Path as _Path

    root_path = _Path(root).resolve()
    output_root = (
        _Path(telemetry_root_override).resolve()
        if telemetry_root_override is not None
        else (root_path / "tmp/dispatcher_telemetry").resolve()
    )
    output_root.mkdir(parents=True, exist_ok=True)
    safe_attempt = _cf09_safe_value(attempt_id, label="attempt_id")
    output = (output_root / f"{safe_attempt}.json").resolve()
    try:
        output.relative_to(output_root)
    except ValueError as exc:
        raise ValueError("telemetry output escapes configured root") from exc

    value = dict(payload)
    value["attempt_id"] = safe_attempt
    value["schema_version"] = "forprint_cf09_dispatcher_telemetry_projection_v0_1"
    value["source_of_truth"] = False
    value["grants_authority"] = False
    value["worker_dispatch_performed"] = False
    output.write_text(
        _json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output



CF10_WORKER_DELTA_REPORT_SCHEMA = "forprint_worker_workspace_delta_v0_1"


def _cf09_worker_delta_required(
    *,
    attempt_id: str,
    attempt_record: dict,
) -> bool:
    work_front_id = attempt_record.get("work_front_id")
    return attempt_id.startswith("cf10-") or (
        isinstance(work_front_id, str)
        and work_front_id.startswith("wf-cf10-")
    )


def _cf09_verify_worker_delta_report(
    *,
    validated_result: dict,
    attempt_record: dict,
    worker_delta_report: dict | None,
) -> dict:
    attempt_id = str(validated_result.get("attempt_id", ""))
    required = _cf09_worker_delta_required(
        attempt_id=attempt_id,
        attempt_record=attempt_record,
    )
    reported = validated_result.get("changed_paths")

    if worker_delta_report is None:
        return {
            "schema_version": "forprint_cf09_worker_delta_verification_v0_1",
            "required": required,
            "provided": False,
            "valid": not required,
            "match": None,
            "reported_changed_paths": (
                list(reported) if isinstance(reported, list) else []
            ),
            "derived_changed_paths": [],
            "errors": (
                ["WORKER_DELTA_REPORT_REQUIRED"]
                if required
                else []
            ),
            "source_of_truth": False,
            "grants_authority": False,
        }

    errors: list[str] = []
    if not isinstance(worker_delta_report, dict):
        errors.append("WORKER_DELTA_REPORT_NOT_MAPPING")
        delta = {}
    else:
        delta = worker_delta_report

    if delta.get("schema_version") != CF10_WORKER_DELTA_REPORT_SCHEMA:
        errors.append("WORKER_DELTA_SCHEMA_MISMATCH")
    if delta.get("worker_delta_exact") is not True:
        errors.append("WORKER_DELTA_NOT_EXACT")
    if delta.get("authority_granted") is not False:
        errors.append("WORKER_DELTA_AUTHORITY_WIDENED")
    if delta.get("candidate_promoted") is not False:
        errors.append("WORKER_DELTA_PROMOTION_ALREADY_PERFORMED")
    if delta.get("canonical_write_performed") is not False:
        errors.append("WORKER_DELTA_CANONICAL_WRITE_ALREADY_PERFORMED")

    derived = delta.get("changed_paths")
    if (
        not isinstance(derived, list)
        or not all(isinstance(item, str) and item for item in derived)
        or len(derived) != len(set(derived))
    ):
        errors.append("WORKER_DELTA_CHANGED_PATHS_INVALID")
        derived_paths: list[str] = []
    else:
        derived_paths = sorted(derived)

    if not isinstance(reported, list):
        errors.append("RESULT_CHANGED_PATHS_NOT_LIST")
        reported_paths: list[str] = []
    else:
        reported_paths = sorted(reported)

    match = reported_paths == derived_paths
    if not match:
        errors.append("WORKER_DELTA_CHANGED_PATHS_MISMATCH")

    return {
        "schema_version": "forprint_cf09_worker_delta_verification_v0_1",
        "required": required,
        "provided": True,
        "valid": not errors,
        "match": match,
        "reported_changed_paths": reported_paths,
        "derived_changed_paths": derived_paths,
        "baseline_fingerprint_sha256": delta.get(
            "baseline_fingerprint_sha256"
        ),
        "source_head": delta.get("source_head"),
        "errors": errors,
        "source_of_truth": False,
        "grants_authority": False,
    }


def finalize_cf09_task_execution(
    *,
    root,
    origin_manifest: dict,
    result: dict,
    attempt_record: dict,
    attempt_number: int,
    requested_max_attempts: int | None = None,
    next_attempt_id: str | None = None,
    dispatcher_telemetry: dict | None = None,
    worker_delta_report: dict | None = None,
    ledger_store_override=None,
    telemetry_root_override=None,
    runtime_loader=None,
    ledger_loader=None,
) -> dict:
    from pathlib import Path as _Path

    root_path = _Path(root).resolve()
    load_runtime = (
        runtime_loader
        if runtime_loader is not None
        else lambda: _cf09_load_runtime_module(
            root_path,
            "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py",
            "forprint_cf09_handoff_v2_runtime",
        )
    )
    load_ledger = (
        ledger_loader
        if ledger_loader is not None
        else lambda: _cf09_load_runtime_module(
            root_path,
            "scripts/coordination/execution_attempt_ledger_v0_1.py",
            "forprint_cf09_execution_attempt_ledger",
        )
    )

    handoff_runtime = load_runtime()
    ledger_runtime = load_ledger()
    if not hasattr(handoff_runtime, "validate_result_for_return"):
        raise RuntimeError("Handoff v2 validate_result_for_return API missing")
    for name in ("load_contract", "validate_record_data", "append_record"):
        if not hasattr(ledger_runtime, name):
            raise RuntimeError(f"Execution Attempt Ledger API missing: {name}")

    validation = handoff_runtime.validate_result_for_return(
        root_path,
        origin_manifest,
        result,
        max_self_repair_attempts=2,
    )
    if not isinstance(validation, dict):
        raise RuntimeError("Handoff v2 result validator returned non-mapping")
    if validation.get("valid") is not True:
        return {
            "schema_version": "forprint_cf09_dispatcher_attempt_finalize_v0_1",
            "state": "RESULT_REJECTED",
            "result_validation": validation,
            "canonical_attempt_record_written": False,
            "telemetry_projection_written": False,
            "worker_dispatch_performed": False,
            "next_required_boundary": "RETURN_FOR_BOUNDED_RESULT_REPAIR_OR_ESCALATION",
        }

    validated_result = validation.get("result")
    if not isinstance(validated_result, dict):
        raise RuntimeError("validated result missing from Handoff v2 report")

    attempt_id = _cf09_safe_value(
        str(validated_result.get("attempt_id", "")),
        label="attempt_id",
    )
    record = dict(attempt_record)
    if record.get("attempt_id") != attempt_id:
        raise ValueError("attempt record attempt_id must equal validated result attempt_id")

    manifest_hash = validated_result.get("handoff_manifest_sha256")
    if origin_manifest.get("handoff_manifest_sha256") != manifest_hash:
        raise ValueError("validated result manifest hash must remain bound to origin manifest")

    worker_delta_verification = _cf09_verify_worker_delta_report(
        validated_result=validated_result,
        attempt_record=record,
        worker_delta_report=worker_delta_report,
    )
    if worker_delta_verification.get("valid") is not True:
        return {
            "schema_version": "forprint_cf09_dispatcher_attempt_finalize_v0_1",
            "state": "RESULT_REJECTED",
            "result_validation": validation,
            "worker_delta_verification": worker_delta_verification,
            "canonical_attempt_record_written": False,
            "telemetry_projection_written": False,
            "worker_dispatch_performed": False,
            "next_required_boundary": (
                "RETURN_FOR_WORKER_DELTA_RECONCILIATION_OR_ESCALATION"
            ),
        }

    contract = ledger_runtime.load_contract(root_path)
    errors = ledger_runtime.validate_record_data(record, contract)
    if errors:
        raise ValueError(
            "attempt record rejected by canonical ledger: "
            + "; ".join(str(item) for item in errors)
        )

    append_kwargs = {}
    if ledger_store_override is not None:
        append_kwargs["store_override"] = _Path(ledger_store_override).resolve()
    ledger_path = ledger_runtime.append_record(root_path, record, **append_kwargs)

    retry_budget = _cf09_retry_budget(
        root=root_path,
        requested_max_attempts=requested_max_attempts,
    )
    retry = _cf09_retry_decision(
        status=str(validated_result.get("status", "")),
        attempt_number=attempt_number,
        retry_budget=retry_budget,
        current_attempt_id=attempt_id,
        next_attempt_id=next_attempt_id,
    )

    telemetry_payload = {
        "handoff_manifest_sha256": manifest_hash,
        "result_status": validated_result.get("status"),
        "attempt_number": attempt_number,
        "retry_budget": retry_budget,
        "retry_decision": retry,
        "repair_attempt_count": validation.get("repair_attempt_count", 0),
        "changed_paths": validated_result.get("changed_paths", []),
        "validation_evidence": validated_result.get("validation_evidence", []),
        "resume_coordinates": validated_result.get("resume_coordinates", {}),
        "unresolved_findings": validated_result.get("unresolved_findings", []),
        "freshness_resume": validation.get("freshness_resume"),
        "worker_delta_verification": worker_delta_verification,
        "operator_supplied_telemetry": (dict(dispatcher_telemetry) if dispatcher_telemetry else {}),
    }
    telemetry_path = _cf09_write_telemetry_projection(
        root=root_path,
        attempt_id=attempt_id,
        payload=telemetry_payload,
        telemetry_root_override=telemetry_root_override,
    )

    return {
        "schema_version": "forprint_cf09_dispatcher_attempt_finalize_v0_1",
        "state": "ATTEMPT_RECORDED",
        "attempt_id": attempt_id,
        "handoff_manifest_sha256": manifest_hash,
        "canonical_attempt_record_written": True,
        "canonical_attempt_record_path": str(ledger_path),
        "telemetry_projection_written": True,
        "telemetry_projection_path": str(telemetry_path),
        "telemetry_is_source_of_truth": False,
        "result_validation": validation,
        "worker_delta_verification": worker_delta_verification,
        "retry_budget": retry_budget,
        "retry_decision": retry,
        "resume_from_full_conversation_replay": False,
        "worker_dispatch_performed": False,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "next_required_boundary": (
            "EXPLICIT_DISPATCH_DECISION"
            if retry.get("retry_allowed")
            else "RESULT_ACCEPTANCE_OR_ESCALATION"
        ),
    }


CF09_ASSISTANT_ACK_GATE_V0_1 = "CF09_ASSISTANT_ACK_GATE_V0_1"


def _cf09_ack_contract(root) -> dict:
    from pathlib import Path as _Path

    path = (
        _Path(root).resolve() / "coordination/standards/automation/"
        "assistant_handoff_v2_contract_v0_1.yaml"
    )
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    ack = data.get("ack_envelope") if isinstance(data, dict) else None
    if not isinstance(ack, dict):
        raise RuntimeError("Handoff v2 ack_envelope missing")

    fields = ack.get("exact_fields")
    if not isinstance(fields, list) or not fields:
        raise RuntimeError("Handoff v2 ACK exact_fields invalid")
    if ack.get("aliases_allowed") is not False:
        raise RuntimeError("ACK aliases must remain forbidden")
    if ack.get("additional_fields_allowed") is not False:
        raise RuntimeError("ACK additional fields must remain forbidden")

    return {
        "exact_fields": list(fields),
        "aliases_allowed": False,
        "additional_fields_allowed": False,
    }


def _cf09_exact_ack(root, value: dict, label: str) -> list[str]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")

    fields = _cf09_ack_contract(root)["exact_fields"]
    actual = list(value.keys())
    if actual != fields:
        missing = [field for field in fields if field not in value]
        additional = [field for field in actual if field not in fields]
        raise ValueError(
            f"{label} must exactly match canonical ACK envelope; "
            f"missing={missing}; additional={additional}"
        )
    return fields


def validate_cf09_assistant_ack(
    *,
    root,
    prepared_execution: dict,
    assistant_ack: dict,
    expected_ack: dict,
    expected_ack_source: str,
) -> dict:
    import re as _re

    if prepared_execution.get("state") != "AWAITING_ASSISTANT_ACK":
        raise ValueError("prepared execution must be AWAITING_ASSISTANT_ACK")
    if prepared_execution.get("mode") != "TASK_EXECUTION":
        raise ValueError("ACK gate only accepts TASK_EXECUTION")
    if prepared_execution.get("assistant_ack_validated") is not False:
        raise ValueError("prepared execution ACK state is inconsistent")

    if expected_ack_source not in {
        "TRUSTED_HANDOFF_PACK",
        "DISPATCHER_CANONICAL_BINDING",
    }:
        raise ValueError("expected ACK source must be trusted")

    fields = _cf09_exact_ack(root, expected_ack, "expected_ack")
    _cf09_exact_ack(root, assistant_ack, "assistant_ack")

    manifest = prepared_execution.get("handoff_manifest_sha256")
    if not isinstance(manifest, str) or not _re.fullmatch(
        r"[0-9a-f]{64}",
        manifest,
    ):
        raise ValueError("prepared manifest hash missing or invalid")

    for label, value in (
        ("expected_ack", expected_ack),
        ("assistant_ack", assistant_ack),
    ):
        if value["handoff_manifest_sha256"] != manifest:
            raise ValueError(f"{label} manifest hash does not match prepared execution")
        if value["launch_mode"] != "TASK_EXECUTION":
            raise ValueError(f"{label} launch_mode must be TASK_EXECUTION")

    mismatched = [field for field in fields if assistant_ack[field] != expected_ack[field]]
    if mismatched:
        raise ValueError(
            "assistant ACK does not match trusted expected bindings: " + ",".join(mismatched)
        )

    authority = prepared_execution.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("prepared authority block missing")
    forbidden = (
        "execution_authority_granted",
        "dispatch_authority_granted",
        "worker_dispatch_performed",
        "external_dispatch_allowed",
        "release_allowed",
        "push_allowed",
        "merge_allowed",
    )
    widened = [field for field in forbidden if authority.get(field) is not False]
    if widened:
        raise ValueError("ACK validation cannot widen authority: " + ",".join(widened))

    ready = dict(prepared_execution)
    ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
    ready["assistant_ack_validated"] = True
    ready["assistant_ack_gate"] = {
        "validated": True,
        "expected_ack_source": expected_ack_source,
        "exact_fields": fields,
        "opaque_ack_values_exact_match": True,
        "grants_authority": False,
        "worker_dispatch_performed": False,
    }
    ready["next_required_human_boundary"] = "EXPLICIT_DISPATCH_DECISION"
    return ready

# ============================================================================
# CF-10 exact internal zero-stage exception — eligibility only, never launch
# ============================================================================
CF10_INTERNAL_ZERO_STAGE_EXCEPTION_V0_1 = "CF10_INTERNAL_ZERO_STAGE_EXCEPTION_V0_1"

CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1 = {
    "work_id": "u180j",
    "module": "forprint_system_blueprint",
    "work_front": (
        "coordination/work_fronts/"
        "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
    ),
    "task_prompt_id": "cf10-zero-stage-dispatch-boundary-regression-v0-1",
    "task_module_root": ".",
    "execution_profile": "light-maintenance",
    "procedure_id": "governed_canonical_mutation",
    "worker_id": "worker-01",
    "attempt_id": "cf10-u180j-a001",
}


def _validate_cf10_internal_zero_stage_exception_exact_a001(
    *,
    work_id: str,
    module: str,
    work_front: str,
    task_prompt_id: str,
    task_module_root: str,
    execution_profile: str,
    procedure_id: str,
    worker_id: str,
    attempt_id: str,
    blueprint_ai_trial_ready: bool = False,
) -> dict:
    """Validate the one exact CF-10 internal-pilot binding.

    This is an eligibility exception to the future broad-trial readiness signal.
    It does not validate Assistant ACK, make an explicit dispatch decision,
    grant worker-launch authority or start a worker process.
    """
    if blueprint_ai_trial_ready is not False:
        raise ValueError(
            "CF-10 zero-stage exception must coexist with "
            "BLUEPRINT_AI_TRIAL_READY=false"
        )

    observed = {
        "work_id": work_id,
        "module": module,
        "work_front": work_front,
        "task_prompt_id": task_prompt_id,
        "task_module_root": task_module_root,
        "execution_profile": execution_profile,
        "procedure_id": procedure_id,
        "worker_id": worker_id,
        "attempt_id": attempt_id,
    }
    mismatched = [
        key
        for key, expected in CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1.items()
        if observed.get(key) != expected
    ]
    if mismatched:
        raise ValueError(
            "CF-10 internal zero-stage binding mismatch: "
            + ",".join(mismatched)
        )

    return {
        "schema_version": "forprint_cf10_internal_zero_stage_exception_v0_1",
        "eligible": True,
        "scope": "CF10_U180J_EXACT_BINDING_ONLY",
        "mode": "MANUAL_SHADOW",
        "candidate_only": True,
        "bindings": dict(CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1),
        "broad_blueprint_ai_trial_ready_required": False,
        "broad_blueprint_ai_trial_ready_observed": False,
        "assistant_ack_required": True,
        "assistant_ack_validated": False,
        "explicit_dispatch_decision_required": True,
        "explicit_dispatch_decision_recorded": False,
        "worker_process_launch_allowed": False,
        "canonical_attempt_ledger_append_allowed": False,
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "foreign_repository_write_allowed": False,
            "automatic_accept_allowed": False,
        },
    }

def validate_cf10_internal_zero_stage_exception(
    *,
    work_id: str,
    module: str,
    work_front: str,
    task_prompt_id: str,
    task_module_root: str,
    execution_profile: str,
    procedure_id: str,
    worker_id: str,
    attempt_id: str,
    blueprint_ai_trial_ready: bool = False,
) -> dict:
    # Preserve the original exact-a001 validator for every binding dimension
    # except the one explicitly bounded retry attempt id.
    binding = dict(CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1)
    exact_attempt_id = binding["attempt_id"]
    allowed_attempt_ids = (
        exact_attempt_id,
        "cf10-u180j-a002",
    )

    if attempt_id not in allowed_attempt_ids:
        raise ValueError(
            "CF-10 internal zero-stage binding mismatch: attempt_id"
        )

    result = _validate_cf10_internal_zero_stage_exception_exact_a001(
        work_id=work_id,
        module=module,
        work_front=work_front,
        task_prompt_id=task_prompt_id,
        task_module_root=task_module_root,
        execution_profile=execution_profile,
        procedure_id=procedure_id,
        worker_id=worker_id,
        attempt_id=exact_attempt_id,
        blueprint_ai_trial_ready=blueprint_ai_trial_ready,
    )
    if not isinstance(result, dict):
        raise ValueError("CF-10 exact validator result must be a mapping")

    def _rebind_attempt(value):
        if isinstance(value, str):
            return attempt_id if value == exact_attempt_id else value
        if isinstance(value, list):
            return [_rebind_attempt(item) for item in value]
        if isinstance(value, tuple):
            return tuple(_rebind_attempt(item) for item in value)
        if isinstance(value, dict):
            return {
                key: _rebind_attempt(item)
                for key, item in value.items()
            }
        return value

    rebound = _rebind_attempt(result)
    rebound["attempt_id"] = attempt_id
    rebound["cf10_retry_binding"] = {
        "mode": "EXPLICIT_A001_A002_ONLY",
        "allowed_attempt_ids": list(allowed_attempt_ids),
        "is_retry": attempt_id != exact_attempt_id,
        "retry_of_attempt_id": (
            exact_attempt_id
            if attempt_id != exact_attempt_id
            else None
        ),
        "grants_additional_authority": False,
        "a003_or_later_implicitly_allowed": False,
    }
    return rebound


def prepare_cf10_internal_zero_stage_pre_dispatch(
    *,
    root,
    worker_id: str,
    attempt_id: str,
    blueprint_ai_trial_ready: bool = False,
    runner=None,
) -> dict:
    """Reuse CF-09 TASK_EXECUTION preparation, then bind the exact CF-10 exception.

    The returned state MUST remain AWAITING_ASSISTANT_ACK.
    """
    binding = dict(CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1)
    exception = validate_cf10_internal_zero_stage_exception(
        work_id=binding["work_id"],
        module=binding["module"],
        work_front=binding["work_front"],
        task_prompt_id=binding["task_prompt_id"],
        task_module_root=binding["task_module_root"],
        execution_profile=binding["execution_profile"],
        procedure_id=binding["procedure_id"],
        worker_id=worker_id,
        attempt_id=attempt_id,
        blueprint_ai_trial_ready=blueprint_ai_trial_ready,
    )

    prepared = prepare_cf09_task_execution(
        root=root,
        work_front=binding["work_front"],
        execution_profile=binding["execution_profile"],
        task_prompt_id=binding["task_prompt_id"],
        task_module_root=binding["task_module_root"],
        module=binding["module"],
        procedure_id=binding["procedure_id"],
        runner=runner,
    )
    if prepared.get("state") != "AWAITING_ASSISTANT_ACK":
        raise ValueError(
            "CF-10 pre-dispatch preparation must stop at AWAITING_ASSISTANT_ACK"
        )
    if prepared.get("assistant_ack_validated") is not False:
        raise ValueError("CF-10 pre-dispatch cannot validate Assistant ACK")

    authority = prepared.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("CF-10 prepared execution authority block missing")
    forbidden = (
        "execution_authority_granted",
        "dispatch_authority_granted",
        "worker_dispatch_performed",
        "external_dispatch_allowed",
        "release_allowed",
        "push_allowed",
        "merge_allowed",
    )
    widened = [key for key in forbidden if authority.get(key) is not False]
    if widened:
        raise ValueError(
            "CF-10 pre-dispatch preparation widened authority: "
            + ",".join(widened)
        )

    result = dict(prepared)
    result["cf10_internal_zero_stage_exception"] = exception
    result["worker_id"] = worker_id
    result["attempt_id"] = attempt_id
    result["workspace_required_before_dispatch"] = True
    result["worker_process_launch_allowed"] = False
    result["canonical_attempt_ledger_append_allowed"] = False
    return result

# cf10-first-worker-launch-extension-v0-1:start
def _cf10_sha256_file(path):
    import hashlib as _hashlib
    from pathlib import Path as _Path

    resolved = _Path(path).resolve()
    if not resolved.is_file():
        raise ValueError(
            f"required canonical binding file missing: {resolved}"
        )
    return _hashlib.sha256(resolved.read_bytes()).hexdigest()


def build_cf10_dispatcher_canonical_ack(
    *,
    root,
    prepared_execution: dict,
    source_state_fingerprint: str,
    worker_id: str,
    attempt_id: str,
) -> dict:
    import re as _re
    from pathlib import Path as _Path

    root_path = _Path(root).resolve()
    if worker_id != "worker-01" or attempt_id not in (
        "cf10-u180j-a001",
        "cf10-u180j-a002",
    ):
        raise ValueError(
            "canonical ACK is limited to the exact first CF10 attempt"
        )
    if prepared_execution.get("mode") != "TASK_EXECUTION":
        raise ValueError("canonical ACK requires TASK_EXECUTION")
    if prepared_execution.get("state") != "AWAITING_ASSISTANT_ACK":
        raise ValueError("canonical ACK requires AWAITING_ASSISTANT_ACK")
    if prepared_execution.get("assistant_ack_validated") is not False:
        raise ValueError(
            "canonical ACK cannot rebuild an already consumed ACK"
        )
    if not _re.fullmatch(r"[0-9a-f]{64}", source_state_fingerprint):
        raise ValueError("source_state_fingerprint must be sha256 hex")

    required = {
        "module": "forprint_system_blueprint",
        "work_front_id": (
            "coordination/work_fronts/"
            "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
        ),
        "task_prompt_id": (
            "cf10-zero-stage-dispatch-boundary-regression-v0-1"
        ),
        "procedure_id": "governed_canonical_mutation",
    }
    for key, expected in required.items():
        if prepared_execution.get(key) != expected:
            raise ValueError(
                f"prepared execution is outside CF10 exact binding: {key}"
            )

    work_front_gate = prepared_execution.get("work_front_gate")
    if not isinstance(work_front_gate, dict):
        raise ValueError("prepared execution Work Front gate missing")
    if work_front_gate.get("validated") is not True:
        raise ValueError(
            "prepared execution Work Front gate is not validated"
        )
    if work_front_gate.get("work_front_id") != (
        "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
    ):
        raise ValueError(
            "prepared execution canonical Work Front ID mismatch"
        )

    profile = prepared_execution.get("execution_profile_ref")
    if profile not in {"light-maintenance", "light-maintenance@r1"}:
        raise ValueError(
            "prepared execution profile is outside CF10 exact binding"
        )

    manifest = prepared_execution.get("handoff_manifest_sha256")
    if not isinstance(manifest, str) or not _re.fullmatch(
        r"[0-9a-f]{64}",
        manifest,
    ):
        raise ValueError("prepared execution manifest hash invalid")

    constitution = (
        root_path
        / "coordination/standards/governance/project_constitution_v0_1.yaml"
    )
    module_policy = (
        root_path
        / "coordination/module_policy/forprint_system_blueprint/"
        "module_policy.md"
    )
    work_front = (
        root_path
        / "coordination/work_fronts/"
        "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
    )
    profiles = (
        root_path / "coordination/registry/execution_profiles_v0_1.yaml"
    )
    procedure = (
        root_path
        / "coordination/registry/"
        "governed_canonical_mutation_procedure_v0_1.yaml"
    )

    return {
        "schema_version": "forprint_assistant_handoff_v2_ack_v0_1",
        "handoff_manifest_sha256": manifest,
        "launch_mode": "TASK_EXECUTION",
        "context_fingerprint": source_state_fingerprint,
        "authority_ack": {
            "scope": "CF10_U180J_FIRST_INTERNAL_ONLY",
            "project_constitution_sha256": _cf10_sha256_file(
                constitution
            ),
            "module_policy_sha256": _cf10_sha256_file(module_policy),
            "authority_widening": False,
        },
        "work_front_ack": {
            "work_front_id": (
                "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
            ),
            "work_front_ref": required["work_front_id"],
            "sha256": _cf10_sha256_file(work_front),
        },
        "profile_ack": {
            "profile_ref": "light-maintenance@r1",
            "registry_sha256": _cf10_sha256_file(profiles),
        },
        "procedure_ack": {
            "procedure_id": "governed_canonical_mutation",
            "sha256": _cf10_sha256_file(procedure),
        },
        "freshness_ack": {
            "source_state_fingerprint": source_state_fingerprint,
            "worker_id": worker_id,
            "attempt_id": attempt_id,
            "workspace_equivalence_required": True,
        },
    }


def authorize_cf10_internal_zero_stage_explicit_dispatch(
    *,
    root,
    ready_execution: dict,
    worker_id: str,
    attempt_id: str,
    source_state_fingerprint: str,
    workspace_repo,
    runtime_provider: str,
    runtime_model: str,
) -> dict:
    import hashlib as _hashlib
    import json as _json
    import re as _re
    from pathlib import Path as _Path

    _ = _Path(root).resolve()
    if ready_execution.get("state") != "READY_FOR_EXPLICIT_DISPATCH":
        raise ValueError(
            "execution must be READY_FOR_EXPLICIT_DISPATCH"
        )
    if ready_execution.get("assistant_ack_validated") is not True:
        raise ValueError(
            "Assistant ACK must be validated before explicit dispatch"
        )

    if worker_id != "worker-01" or attempt_id not in (
        "cf10-u180j-a001",
        "cf10-u180j-a002",
    ):
        raise ValueError(
            "explicit dispatch is limited to the exact first attempt"
        )
    if not _re.fullmatch(r"[0-9a-f]{64}", source_state_fingerprint):
        raise ValueError("source_state_fingerprint must be sha256 hex")
    if runtime_provider != "github_copilot_cli":
        raise ValueError(
            "first CF10 runtime provider must be github_copilot_cli"
        )
    if runtime_model != "auto":
        raise ValueError(
            "first CF10 runtime model selection must be auto"
        )

    required = {
        "module": "forprint_system_blueprint",
        "work_front_id": (
            "coordination/work_fronts/"
            "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
        ),
        "task_prompt_id": (
            "cf10-zero-stage-dispatch-boundary-regression-v0-1"
        ),
        "procedure_id": "governed_canonical_mutation",
    }
    for key, expected in required.items():
        if ready_execution.get(key) != expected:
            raise ValueError(
                f"ready execution is outside CF10 exact binding: {key}"
            )

    work_front_gate = ready_execution.get("work_front_gate")
    if not isinstance(work_front_gate, dict):
        raise ValueError("ready execution Work Front gate missing")
    if work_front_gate.get("validated") is not True:
        raise ValueError(
            "ready execution Work Front gate is not validated"
        )
    if work_front_gate.get("work_front_id") != (
        "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
    ):
        raise ValueError(
            "ready execution canonical Work Front ID mismatch"
        )

    profile = ready_execution.get("execution_profile_ref")
    if profile not in {"light-maintenance", "light-maintenance@r1"}:
        raise ValueError(
            "ready execution profile is outside CF10 exact binding"
        )

    authority = ready_execution.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("ready execution authority block missing")
    for key in (
        "execution_authority_granted",
        "dispatch_authority_granted",
        "worker_dispatch_performed",
        "external_dispatch_allowed",
        "release_allowed",
        "push_allowed",
        "merge_allowed",
    ):
        if authority.get(key) is not False:
            raise ValueError(
                f"forbidden pre-dispatch authority widening: {key}"
            )

    workspace = _Path(workspace_repo).expanduser().resolve()
    suffix = _Path(
        "forprint_system_blueprint/worker-01/"
        f"{attempt_id}/workspace/repo"
    )
    if not workspace.is_dir():
        raise ValueError("isolated workspace repo is missing")
    if tuple(workspace.parts[-len(suffix.parts):]) != suffix.parts:
        raise ValueError(
            "workspace repo is outside exact CF10 attempt layout"
        )

    binding = {
        "work_id": "u180j",
        "worker_id": worker_id,
        "attempt_id": attempt_id,
        "source_state_fingerprint": source_state_fingerprint,
        "work_front_id": (
            "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
        ),
        "work_front_ref": required["work_front_id"],
        "profile_ref": "light-maintenance@r1",
        "procedure_id": required["procedure_id"],
        "runtime_provider": runtime_provider,
        "runtime_model": runtime_model,
        "workspace_repo": str(workspace),
    }
    decision_id = _hashlib.sha256(
        _json.dumps(binding, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "schema_version": (
            "forprint_cf10_internal_explicit_dispatch_decision_v0_1"
        ),
        "decision_id": decision_id,
        "decision": "ALLOW_EXACT_FIRST_INTERNAL_WORKER_LAUNCH",
        "binding": binding,
        "assistant_ack_validated": True,
        "explicit_dispatch_decision_recorded": True,
        "worker_process_launch_allowed": True,
        "canonical_attempt_ledger_append_allowed": True,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "foreign_repository_write_allowed": False,
        "automatic_accept_allowed": False,
        "grants_broad_dispatch_authority": False,
    }
# cf10-first-worker-launch-extension-v0-1:end
# cf10-a003-operator-status-binding-v0-3:start
CF10_OPERATOR_STATUS_A003_BINDING_V0_1 = {
    "work_id": "u180j",
    "module": "forprint_system_blueprint",
    "work_front": (
        "coordination/work_fronts/"
        "cf10_operator_status_surface_self_hardening_v0_1.yaml"
    ),
    "task_prompt_id": "cf10-operator-status-surface-self-hardening-v0-1",
    "task_module_root": ".",
    "execution_profile": "light-maintenance",
    "procedure_id": "governed_canonical_mutation",
    "worker_id": "worker-01",
    "attempt_id": "cf10-u180j-a003",
}


def _validate_cf10_operator_status_a003_exact(
    *, work_id: str, module: str, work_front: str, task_prompt_id: str,
    task_module_root: str, execution_profile: str, procedure_id: str,
    worker_id: str, attempt_id: str, blueprint_ai_trial_ready: bool = False,
) -> dict:
    if blueprint_ai_trial_ready is not False:
        raise ValueError("CF-10 a003 requires BLUEPRINT_AI_TRIAL_READY=false")
    observed = {
        "work_id": work_id, "module": module, "work_front": work_front,
        "task_prompt_id": task_prompt_id, "task_module_root": task_module_root,
        "execution_profile": execution_profile, "procedure_id": procedure_id,
        "worker_id": worker_id, "attempt_id": attempt_id,
    }
    bad = [k for k, v in CF10_OPERATOR_STATUS_A003_BINDING_V0_1.items()
           if observed.get(k) != v]
    if bad:
        raise ValueError("CF-10 operator-status a003 binding mismatch: " + ",".join(bad))
    return {
        "schema_version": "forprint_cf10_operator_status_a003_binding_v0_1",
        "eligible": True,
        "scope": "CF10_U180J_A003_OPERATOR_STATUS_ONLY",
        "mode": "MANUAL_SHADOW",
        "candidate_only": True,
        "bindings": dict(CF10_OPERATOR_STATUS_A003_BINDING_V0_1),
        "assistant_ack_required": True,
        "assistant_ack_validated": False,
        "explicit_dispatch_decision_required": True,
        "explicit_dispatch_decision_recorded": False,
        "worker_process_launch_allowed": False,
        "canonical_attempt_ledger_append_allowed": False,
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "foreign_repository_write_allowed": False,
            "automatic_accept_allowed": False,
        },
    }


def prepare_cf10_operator_status_a003_pre_dispatch(
    *, root, worker_id: str, attempt_id: str,
    blueprint_ai_trial_ready: bool = False, runner=None,
) -> dict:
    binding = dict(CF10_OPERATOR_STATUS_A003_BINDING_V0_1)
    exact = _validate_cf10_operator_status_a003_exact(
        work_id=binding["work_id"], module=binding["module"],
        work_front=binding["work_front"], task_prompt_id=binding["task_prompt_id"],
        task_module_root=binding["task_module_root"],
        execution_profile=binding["execution_profile"],
        procedure_id=binding["procedure_id"], worker_id=worker_id,
        attempt_id=attempt_id, blueprint_ai_trial_ready=blueprint_ai_trial_ready,
    )
    prepared = prepare_cf09_task_execution(
        root=root, work_front=binding["work_front"],
        execution_profile=binding["execution_profile"],
        task_prompt_id=binding["task_prompt_id"],
        task_module_root=binding["task_module_root"], module=binding["module"],
        procedure_id=binding["procedure_id"], runner=runner,
    )
    if prepared.get("state") != "AWAITING_ASSISTANT_ACK":
        raise ValueError("CF-10 a003 must stop at AWAITING_ASSISTANT_ACK")
    if prepared.get("assistant_ack_validated") is not False:
        raise ValueError("CF-10 a003 cannot consume ACK during preparation")
    authority = prepared.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("CF-10 a003 authority block missing")
    forbidden = (
        "execution_authority_granted", "dispatch_authority_granted",
        "worker_dispatch_performed", "external_dispatch_allowed",
        "release_allowed", "push_allowed", "merge_allowed",
    )
    widened = [k for k in forbidden if authority.get(k) is not False]
    if widened:
        raise ValueError("CF-10 a003 authority widened: " + ",".join(widened))
    result = dict(prepared)
    result["cf10_operator_status_a003_binding"] = exact
    result["worker_id"] = worker_id
    result["attempt_id"] = attempt_id
    result["workspace_required_before_dispatch"] = True
    result["worker_process_launch_allowed"] = False
    result["canonical_attempt_ledger_append_allowed"] = False
    return result


def _cf10_operator_status_a003_required(execution: dict) -> dict:
    required = {
        "module": "forprint_system_blueprint",
        "work_front_id": (
            "coordination/work_fronts/"
            "cf10_operator_status_surface_self_hardening_v0_1.yaml"
        ),
        "task_prompt_id": "cf10-operator-status-surface-self-hardening-v0-1",
        "procedure_id": "governed_canonical_mutation",
    }
    for key, expected in required.items():
        if execution.get(key) != expected:
            raise ValueError(f"execution is outside CF10 a003 binding: {key}")
    gate = execution.get("work_front_gate")
    if not isinstance(gate, dict) or gate.get("validated") is not True:
        raise ValueError("CF-10 a003 Work Front gate invalid")
    if gate.get("work_front_id") != (
        "wf-cf10-operator-status-surface-self-hardening-v0-1"
    ):
        raise ValueError("CF-10 a003 Work Front ID mismatch")
    if execution.get("execution_profile_ref") not in {
        "light-maintenance", "light-maintenance@r1"
    }:
        raise ValueError("CF-10 a003 execution profile mismatch")
    return required


def build_cf10_operator_status_a003_canonical_ack(
    *, root, prepared_execution: dict, source_state_fingerprint: str,
    worker_id: str, attempt_id: str,
) -> dict:
    import re as _re
    from pathlib import Path as _Path

    root_path = _Path(root).resolve()
    if worker_id != "worker-01" or attempt_id != "cf10-u180j-a003":
        raise ValueError("canonical ACK is limited to exact CF10 a003")
    if prepared_execution.get("mode") != "TASK_EXECUTION":
        raise ValueError("canonical ACK requires TASK_EXECUTION")
    if prepared_execution.get("state") != "AWAITING_ASSISTANT_ACK":
        raise ValueError("canonical ACK requires AWAITING_ASSISTANT_ACK")
    if prepared_execution.get("assistant_ack_validated") is not False:
        raise ValueError("canonical ACK cannot rebuild consumed ACK")
    if not _re.fullmatch(r"[0-9a-f]{64}", source_state_fingerprint):
        raise ValueError("source_state_fingerprint must be sha256 hex")

    required = _cf10_operator_status_a003_required(prepared_execution)
    manifest = prepared_execution.get("handoff_manifest_sha256")
    if not isinstance(manifest, str) or not _re.fullmatch(r"[0-9a-f]{64}", manifest):
        raise ValueError("prepared execution manifest hash invalid")

    constitution = root_path / "coordination/standards/governance/project_constitution_v0_1.yaml"
    module_policy = root_path / "coordination/module_policy/forprint_system_blueprint/module_policy.md"
    work_front = root_path / "coordination/work_fronts/cf10_operator_status_surface_self_hardening_v0_1.yaml"
    profiles = root_path / "coordination/registry/execution_profiles_v0_1.yaml"
    procedure = root_path / "coordination/registry/governed_canonical_mutation_procedure_v0_1.yaml"

    return {
        "schema_version": "forprint_assistant_handoff_v2_ack_v0_1",
        "handoff_manifest_sha256": manifest,
        "launch_mode": "TASK_EXECUTION",
        "context_fingerprint": source_state_fingerprint,
        "authority_ack": {
            "scope": "CF10_U180J_A003_OPERATOR_STATUS_ONLY",
            "project_constitution_sha256": _cf10_sha256_file(constitution),
            "module_policy_sha256": _cf10_sha256_file(module_policy),
            "authority_widening": False,
        },
        "work_front_ack": {
            "work_front_id": "wf-cf10-operator-status-surface-self-hardening-v0-1",
            "work_front_ref": required["work_front_id"],
            "sha256": _cf10_sha256_file(work_front),
        },
        "profile_ack": {
            "profile_ref": "light-maintenance@r1",
            "registry_sha256": _cf10_sha256_file(profiles),
        },
        "procedure_ack": {
            "procedure_id": "governed_canonical_mutation",
            "sha256": _cf10_sha256_file(procedure),
        },
        "freshness_ack": {
            "source_state_fingerprint": source_state_fingerprint,
            "worker_id": worker_id,
            "attempt_id": attempt_id,
            "workspace_equivalence_required": True,
        },
    }


def authorize_cf10_operator_status_a003_explicit_dispatch(
    *, root, ready_execution: dict, worker_id: str, attempt_id: str,
    source_state_fingerprint: str, workspace_repo,
    runtime_provider: str, runtime_model: str,
) -> dict:
    import hashlib as _hashlib
    import json as _json
    import re as _re
    from pathlib import Path as _Path

    _ = _Path(root).resolve()
    if ready_execution.get("state") != "READY_FOR_EXPLICIT_DISPATCH":
        raise ValueError("execution must be READY_FOR_EXPLICIT_DISPATCH")
    if ready_execution.get("assistant_ack_validated") is not True:
        raise ValueError("Assistant ACK must be validated before dispatch")
    if worker_id != "worker-01" or attempt_id != "cf10-u180j-a003":
        raise ValueError("explicit dispatch is limited to exact CF10 a003")
    if not _re.fullmatch(r"[0-9a-f]{64}", source_state_fingerprint):
        raise ValueError("source_state_fingerprint must be sha256 hex")
    if runtime_provider != "github_copilot_cli":
        raise ValueError("CF10 a003 runtime provider must be github_copilot_cli")
    if runtime_model != "auto":
        raise ValueError("CF10 a003 runtime model selection must be auto")

    required = _cf10_operator_status_a003_required(ready_execution)
    authority = ready_execution.get("authority")
    if not isinstance(authority, dict):
        raise ValueError("ready execution authority block missing")
    for key in (
        "execution_authority_granted", "dispatch_authority_granted",
        "worker_dispatch_performed", "external_dispatch_allowed",
        "release_allowed", "push_allowed", "merge_allowed",
    ):
        if authority.get(key) is not False:
            raise ValueError(f"forbidden pre-dispatch authority widening: {key}")

    workspace = _Path(workspace_repo).expanduser().resolve()
    suffix = _Path(
        "forprint_system_blueprint/worker-01/"
        f"{attempt_id}/workspace/repo"
    )
    if not workspace.is_dir():
        raise ValueError("isolated workspace repo is missing")
    if tuple(workspace.parts[-len(suffix.parts):]) != suffix.parts:
        raise ValueError("workspace repo is outside exact CF10 attempt layout")

    binding = {
        "work_id": "u180j",
        "worker_id": worker_id,
        "attempt_id": attempt_id,
        "source_state_fingerprint": source_state_fingerprint,
        "work_front_id": "wf-cf10-operator-status-surface-self-hardening-v0-1",
        "work_front_ref": required["work_front_id"],
        "profile_ref": "light-maintenance@r1",
        "procedure_id": required["procedure_id"],
        "runtime_provider": runtime_provider,
        "runtime_model": runtime_model,
        "workspace_repo": str(workspace),
    }
    decision_id = _hashlib.sha256(
        _json.dumps(binding, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": "forprint_cf10_internal_explicit_dispatch_decision_v0_1",
        "decision_id": decision_id,
        "decision": "ALLOW_EXACT_FIRST_INTERNAL_WORKER_LAUNCH",
        "binding": binding,
        "assistant_ack_validated": True,
        "explicit_dispatch_decision_recorded": True,
        "worker_process_launch_allowed": True,
        "canonical_attempt_ledger_append_allowed": True,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "foreign_repository_write_allowed": False,
        "automatic_accept_allowed": False,
        "grants_broad_dispatch_authority": False,
    }
# cf10-a003-operator-status-binding-v0-3:end
