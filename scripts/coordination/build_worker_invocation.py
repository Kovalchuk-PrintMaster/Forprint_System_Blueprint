from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RUNTIME_SCHEMA = "forprint_worker_runtime_v0_1"
INVOCATION_SCHEMA = "forprint_worker_invocation_v0_1"
COMPLETION_CAPTURE_SCHEMA = "forprint_worker_completion_capture_v0_1"
APPROVAL_SCHEMA = "forprint_operator_approval_decision_v0_1"

ADAPTER_CONSOLE_COMMAND = "CONSOLE_COMMAND"
NETWORK_MODES = ("DENY", "ALLOWLIST", "ALLOW")
STATE_BLOCKED = "BLOCKED"
STATE_DRY_RUN_READY = "DRY_RUN_READY"

BLOCKER_APPROVAL_MISSING = "APPROVAL_DECISION_NOT_PROVIDED"
BLOCKER_APPROVAL_INVALID = "APPROVAL_DECISION_INVALID"
BLOCKER_LAUNCH_STATE = "LAUNCH_REQUEST_NOT_AWAITING_OPERATOR_APPROVAL"
BLOCKER_RUNTIME_INVALID = "WORKER_RUNTIME_INVALID"
BLOCKER_MODULE_MISMATCH = "WORKER_RUNTIME_MODULE_MISMATCH"
BLOCKER_ENVIRONMENT_MISSING = "REQUIRED_ENVIRONMENT_MISSING"
BLOCKER_WORKING_DIRECTORY = "WORKING_DIRECTORY_OUTSIDE_MODULE_ROOT"

_ALLOWED_PLACEHOLDERS = {
    "model",
    "module_id",
    "prompt_id",
    "module_root",
    "working_directory",
    "task_context_archive",
    "completion_output",
}
_ENV_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


@dataclass(frozen=True)
class RuntimeValidation:
    valid: bool
    errors: tuple[str, ...]
    normalized: dict[str, Any] | None


@dataclass(frozen=True)
class WorkerInvocationPlan:
    state: str
    blocker_codes: tuple[str, ...]
    document: dict[str, Any]


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping: {path}")
    return data


def _nested(mapping: dict[str, Any], *keys: str) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _load_approval_gateway(root: Path):
    gateway_path = (
        root
        / Path("scripts")
        / "coordination"
        / "build_operator_approval_decision.py"
    )
    if not gateway_path.is_file():
        raise ValueError(f"operator approval gateway is missing: {gateway_path}")
    spec = importlib.util.spec_from_file_location(
        "forprint_operator_approval_gateway_runtime",
        gateway_path,
    )
    if spec is None or spec.loader is None:
        raise ValueError("operator approval gateway import spec could not be created")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def _resolve_within(base: Path, raw: str, *, label: str) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = base / candidate
    resolved = candidate.resolve()
    base_resolved = base.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"{label} must stay within module root") from exc
    return resolved


def _validate_budget(raw: Any, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        errors.append("budget must be a mapping")
        return None

    integer_fields = (
        "max_input_tokens",
        "max_output_tokens",
        "max_total_tokens",
    )
    normalized: dict[str, Any] = {}
    for field in integer_fields:
        value = raw.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"budget.{field} must be a positive integer")
        else:
            normalized[field] = value

    max_cost = raw.get("max_cost")
    if not isinstance(max_cost, (int, float)) or isinstance(max_cost, bool) or max_cost <= 0:
        errors.append("budget.max_cost must be a positive number")
    else:
        normalized["max_cost"] = float(max_cost)

    currency = raw.get("currency")
    if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
        errors.append("budget.currency must be a three-letter uppercase code")
    else:
        normalized["currency"] = currency

    if all(field in normalized for field in integer_fields):
        if normalized["max_total_tokens"] < (
            normalized["max_input_tokens"] + normalized["max_output_tokens"]
        ):
            errors.append(
                "budget.max_total_tokens must be >= input + output token ceilings"
            )
    return normalized


def _validate_network(raw: Any, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        errors.append("network_policy must be a mapping")
        return None
    mode = raw.get("mode")
    if mode not in NETWORK_MODES:
        errors.append("network_policy.mode is unsupported")
        return None
    allowlist = raw.get("allowlist", [])
    if not isinstance(allowlist, list) or not all(
        isinstance(item, str) and item.strip() for item in allowlist
    ):
        errors.append("network_policy.allowlist must be a list of non-empty strings")
        allowlist = []
    if mode != "ALLOWLIST" and allowlist:
        errors.append(
            "network_policy.allowlist must be empty unless mode is ALLOWLIST"
        )
    return {
        "mode": mode,
        "allowlist": sorted(set(item.strip() for item in allowlist)),
    }


def _validate_environment_names(
    raw: Any,
    *,
    label: str,
    errors: list[str],
) -> list[str]:
    if not isinstance(raw, list):
        errors.append(f"{label} must be a list")
        return []
    names: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not _ENV_NAME_RE.fullmatch(item):
            errors.append(f"{label} contains invalid environment variable name")
            continue
        names.append(item)
    return sorted(set(names))


def _validate_command(raw: Any, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        errors.append("command must be a mapping")
        return None
    executable = raw.get("executable")
    args = raw.get("args")
    if not isinstance(executable, str) or not executable.strip():
        errors.append("command.executable must be a non-empty string")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        errors.append("command.args must be a list of strings")
        args = []

    formatter = string.Formatter()
    for value in [executable] + list(args):
        if not isinstance(value, str):
            continue
        try:
            fields = {
                field_name
                for _, field_name, _, _ in formatter.parse(value)
                if field_name
            }
        except ValueError:
            errors.append("command template contains invalid formatting syntax")
            continue
        unknown = sorted(fields - _ALLOWED_PLACEHOLDERS)
        if unknown:
            errors.append(
                "command template contains unsupported placeholders:"
                + ",".join(unknown)
            )

    return {
        "executable": executable.strip() if isinstance(executable, str) else "",
        "args": list(args),
    }


def validate_runtime_config(
    *,
    runtime_path: Path,
    module_root: Path,
) -> RuntimeValidation:
    errors: list[str] = []
    try:
        data = _load_yaml_mapping(runtime_path.resolve(), label="worker runtime")
    except Exception as exc:
        return RuntimeValidation(False, (str(exc),), None)

    allowed_top = {
        "schema_version",
        "module_id",
        "provider_adapter",
        "model",
        "working_directory",
        "timeout_seconds",
        "network_policy",
        "budget",
        "environment_allowlist",
        "required_environment",
        "command",
        "completion",
    }
    unknown = sorted(set(data) - allowed_top)
    if unknown:
        errors.append("unknown top-level runtime fields:" + ",".join(unknown))

    if data.get("schema_version") != RUNTIME_SCHEMA:
        errors.append("worker runtime schema is unsupported")

    module_id = data.get("module_id")
    if not isinstance(module_id, str) or not module_id.strip():
        errors.append("module_id must be a non-empty string")

    if data.get("provider_adapter") != ADAPTER_CONSOLE_COMMAND:
        errors.append("provider_adapter must be CONSOLE_COMMAND in v0.1")

    model = data.get("model")
    if not isinstance(model, str) or not model.strip():
        errors.append("model must be a non-empty string")

    timeout = data.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 86400:
        errors.append("timeout_seconds must be an integer from 1 to 86400")

    working_raw = data.get("working_directory")
    working_directory: Path | None = None
    if not isinstance(working_raw, str) or not working_raw.strip():
        errors.append("working_directory must be a non-empty string")
    else:
        try:
            working_directory = _resolve_within(
                module_root.resolve(),
                working_raw,
                label="working_directory",
            )
        except Exception as exc:
            errors.append(str(exc))

    budget = _validate_budget(data.get("budget"), errors)
    network = _validate_network(data.get("network_policy"), errors)
    allowlist = _validate_environment_names(
        data.get("environment_allowlist", []),
        label="environment_allowlist",
        errors=errors,
    )
    required = _validate_environment_names(
        data.get("required_environment", []),
        label="required_environment",
        errors=errors,
    )
    if not set(required).issubset(set(allowlist)):
        errors.append("required_environment must be a subset of environment_allowlist")

    command = _validate_command(data.get("command"), errors)

    completion = data.get("completion")
    completion_normalized: dict[str, Any] | None = None
    if not isinstance(completion, dict):
        errors.append("completion must be a mapping")
    else:
        fmt = completion.get("schema_version")
        if fmt != COMPLETION_CAPTURE_SCHEMA:
            errors.append("completion.schema_version is unsupported")
        completion_normalized = {
            "schema_version": fmt,
            "report_name": "worker_completion_report.yaml",
            "stdout_name": "stdout.log",
            "stderr_name": "stderr.log",
            "invocation_manifest_name": "invocation_manifest.yaml",
            "unknown_telemetry": "not_observable",
        }

    if errors:
        return RuntimeValidation(False, tuple(sorted(set(errors))), None)

    normalized = {
        "schema_version": RUNTIME_SCHEMA,
        "module_id": module_id.strip(),
        "provider_adapter": ADAPTER_CONSOLE_COMMAND,
        "model": model.strip(),
        "working_directory": str(working_directory),
        "timeout_seconds": timeout,
        "network_policy": network,
        "budget": budget,
        "environment_allowlist": allowlist,
        "required_environment": required,
        "command": command,
        "completion": completion_normalized,
    }
    return RuntimeValidation(True, (), normalized)


def _safe_environment_presence(
    names: list[str],
) -> dict[str, str]:
    return {
        name: ("present" if os.environ.get(name) else "missing")
        for name in names
    }


def _render_console_command(
    *,
    runtime: dict[str, Any],
    launch_request: dict[str, Any],
    module_root: Path,
    completion_output: Path,
) -> list[str]:
    context = {
        "model": runtime["model"],
        "module_id": _nested(launch_request, "identity", "module_id"),
        "prompt_id": _nested(launch_request, "identity", "prompt_id"),
        "module_root": str(module_root.resolve()),
        "working_directory": runtime["working_directory"],
        "task_context_archive": _nested(
            launch_request,
            "task_context",
            "archive_path",
        ),
        "completion_output": str(completion_output.resolve()),
    }

    command = runtime["command"]
    executable = str(command["executable"]).format_map(context)
    args = [str(item).format_map(context) for item in command["args"]]
    return [executable, *args]


def _approval_validation(
    *,
    root: Path,
    module_root: Path,
    launch_request_path: Path,
    decision_path: Path | None,
) -> tuple[bool, list[str], str | None]:
    if decision_path is None:
        return False, [BLOCKER_APPROVAL_MISSING], None
    gateway = _load_approval_gateway(root)
    result = gateway.validate_approval_for_dispatch(
        root=root,
        module_root=module_root,
        launch_request_path=launch_request_path,
        decision_path=decision_path,
    )
    valid = bool(getattr(result, "valid", False))
    reason_codes = list(getattr(result, "reason_codes", ()) or ())
    decision_id = getattr(result, "decision_id", None)
    if valid:
        return True, [], str(decision_id) if decision_id else None
    return False, [BLOCKER_APPROVAL_INVALID, *reason_codes], (
        str(decision_id) if decision_id else None
    )


def build_worker_invocation(
    *,
    root: Path,
    module_root: Path,
    launch_request_path: Path,
    runtime_path: Path,
    decision_path: Path | None = None,
    completion_root: Path | None = None,
) -> WorkerInvocationPlan:
    root = root.resolve()
    module_root = module_root.resolve()
    launch_request_path = launch_request_path.resolve()
    runtime_path = runtime_path.resolve()
    if decision_path is not None:
        decision_path = decision_path.resolve()

    launch = _load_yaml_mapping(launch_request_path, label="launch request")
    module_id = _nested(launch, "identity", "module_id")
    prompt_id = _nested(launch, "identity", "prompt_id")
    task_context_id = _nested(launch, "identity", "task_context_id")
    context_fingerprint = _nested(
        launch,
        "identity",
        "context_fingerprint_sha256",
    )
    launch_request_sha = _sha256_path(launch_request_path)

    blockers: list[str] = []
    if launch.get("state") != "AWAITING_OPERATOR_APPROVAL":
        blockers.append(BLOCKER_LAUNCH_STATE)

    runtime_validation = validate_runtime_config(
        runtime_path=runtime_path,
        module_root=module_root,
    )
    runtime: dict[str, Any] | None = runtime_validation.normalized
    if not runtime_validation.valid or runtime is None:
        blockers.extend(
            [BLOCKER_RUNTIME_INVALID, *runtime_validation.errors]
        )
    elif runtime.get("module_id") != module_id:
        blockers.append(BLOCKER_MODULE_MISMATCH)

    approval_valid, approval_reasons, decision_id = _approval_validation(
        root=root,
        module_root=module_root,
        launch_request_path=launch_request_path,
        decision_path=decision_path,
    )
    if not approval_valid:
        blockers.extend(approval_reasons)

    environment_presence: dict[str, str] = {}
    missing_required: list[str] = []
    if runtime is not None:
        environment_presence = _safe_environment_presence(
            runtime["environment_allowlist"]
        )
        missing_required = [
            name
            for name in runtime["required_environment"]
            if environment_presence.get(name) != "present"
        ]
        if missing_required:
            blockers.append(BLOCKER_ENVIRONMENT_MISSING)

    unique_blockers = tuple(sorted(set(str(item) for item in blockers)))
    state = STATE_DRY_RUN_READY if not unique_blockers else STATE_BLOCKED

    runtime_sha = _sha256_path(runtime_path)
    decision_sha = (
        _sha256_path(decision_path)
        if decision_path is not None and decision_path.is_file()
        else None
    )
    task_context_archive = _nested(launch, "task_context", "archive_path")
    task_context_archive_sha = _nested(
        launch,
        "task_context",
        "archive_sha256",
    )
    module_head = _nested(
        launch,
        "repository_revalidation",
        "module_head",
    )
    blueprint_head = _nested(
        launch,
        "repository_revalidation",
        "blueprint_head",
    )

    stable = {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "launch_request_sha256": launch_request_sha,
        "task_context_archive_sha256": task_context_archive_sha,
        "runtime_sha256": runtime_sha,
        "approval_decision_sha256": decision_sha,
        "module_head": module_head,
    }
    invocation_fingerprint = hashlib.sha256(
        json.dumps(
            stable,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    invocation_id = (
        f"{module_id}__{prompt_id}__worker_invocation__"
        f"{invocation_fingerprint[:16]}"
    )

    if completion_root is None:
        completion_root = (
            root
            / Path("tmp")
            / "control_plane"
            / "worker_runs"
        )
    completion_output = completion_root.resolve() / invocation_id

    rendered_argv: list[str] | None = None
    if runtime is not None:
        rendered_argv = _render_console_command(
            runtime=runtime,
            launch_request=launch,
            module_root=module_root,
            completion_output=completion_output,
        )

    document = {
        "schema_version": INVOCATION_SCHEMA,
        "invocation_id": invocation_id,
        "state": state,
        "identity": {
            "module_id": module_id,
            "prompt_id": prompt_id,
            "task_context_id": task_context_id,
            "task_context_fingerprint_sha256": context_fingerprint,
            "invocation_fingerprint_sha256": invocation_fingerprint,
        },
        "authority_binding": {
            "approval_decision_id": decision_id,
            "approval_decision_path": (
                str(decision_path) if decision_path is not None else None
            ),
            "approval_decision_sha256": decision_sha,
            "approval_valid_for_dispatch": approval_valid,
            "launch_request_path": str(launch_request_path),
            "launch_request_sha256": launch_request_sha,
            "task_context_archive": task_context_archive,
            "task_context_archive_sha256": task_context_archive_sha,
            "blueprint_head": blueprint_head,
            "module_head": module_head,
        },
        "runtime": {
            "runtime_path": str(runtime_path),
            "runtime_sha256": runtime_sha,
            "provider_adapter": (
                runtime.get("provider_adapter") if runtime else None
            ),
            "model": runtime.get("model") if runtime else None,
            "working_directory": (
                runtime.get("working_directory") if runtime else None
            ),
            "timeout_seconds": (
                runtime.get("timeout_seconds") if runtime else None
            ),
            "network_policy": (
                runtime.get("network_policy") if runtime else None
            ),
            "budget": runtime.get("budget") if runtime else None,
            "environment_allowlist": (
                runtime.get("environment_allowlist") if runtime else []
            ),
            "environment_presence": environment_presence,
            "required_environment_missing": missing_required,
        },
        "console_command": {
            "argv": rendered_argv,
            "shell": False,
            "secret_values_serialized": False,
            "subprocess_started": False,
        },
        "completion_capture": {
            "schema_version": COMPLETION_CAPTURE_SCHEMA,
            "output_directory": str(completion_output),
            "expected_artifacts": [
                "worker_completion_report.yaml",
                "stdout.log",
                "stderr.log",
                "invocation_manifest.yaml",
            ],
            "unknown_telemetry": "not_observable",
            "semantic_acceptance_owner": "INSPECTOR_AND_HUMAN_GATE",
            "blueprint_accept_performed": False,
        },
        "eligibility": {
            "dry_run_ready": state == STATE_DRY_RUN_READY,
            "future_dispatch_eligible": state == STATE_DRY_RUN_READY,
            "blocker_count": len(unique_blockers),
            "blocker_codes": list(unique_blockers),
        },
        "execution_boundaries": {
            "adapter_mode": "DRY_RUN_ONLY_V0_1",
            "worker_process_start_allowed": False,
            "worker_process_started": False,
            "prompt_claim_allowed": False,
            "prompt_claim_performed": False,
            "module_repository_write_allowed": False,
            "blueprint_accept_allowed": False,
            "next_prompt_release_allowed": False,
            "telegram_required": False,
        },
        "next_component": "CENTRAL_LISTENER_DISPATCHER_MONITOR",
    }

    return WorkerInvocationPlan(
        state=state,
        blocker_codes=unique_blockers,
        document=document,
    )


def write_invocation_plan(
    *,
    plan: WorkerInvocationPlan,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{plan.document['invocation_id']}__dry_run.yaml"
    if path.exists():
        raise ValueError(f"worker invocation plan already exists: {path}")
    path.write_text(
        yaml.safe_dump(
            plan.document,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return path


def render_summary(
    plan: WorkerInvocationPlan,
    *,
    output_path: Path | None,
) -> str:
    lines = [
        "CONSOLE_WORKER_ADAPTER=PASS",
        f"INVOCATION_ID={plan.document['invocation_id']}",
        f"STATE={plan.state}",
        f"BLOCKER_COUNT={len(plan.blocker_codes)}",
        "BLOCKERS=" + ",".join(plan.blocker_codes),
        "APPROVAL_VALID="
        + str(
            plan.document["authority_binding"][
                "approval_valid_for_dispatch"
            ]
        ).lower(),
        "DRY_RUN_READY="
        + str(plan.document["eligibility"]["dry_run_ready"]).lower(),
        "WORKER_PROCESS_STARTED=false",
        "PROMPT_CLAIM_PERFORMED=false",
        "BLUEPRINT_ACCEPT_PERFORMED=false",
    ]
    if output_path is not None:
        lines.extend(
            [
                f"INVOCATION_PLAN_PATH={output_path}",
                f"INVOCATION_PLAN_SHA256={_sha256_path(output_path)}",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a provider-neutral dry-run worker invocation plan. "
            "v0.1 never starts a worker process."
        )
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module-root", required=True)
    parser.add_argument("--launch-request", required=True)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--approval-decision")
    parser.add_argument(
        "--output-dir",
        default=str(
            Path("tmp")
            / "control_plane"
            / "worker_invocations"
        ),
    )
    parser.add_argument("--completion-root")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--print", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    module_root = Path(args.module_root).resolve()
    launch_request = Path(args.launch_request).resolve()
    runtime = Path(args.runtime).resolve()
    decision = (
        Path(args.approval_decision).resolve()
        if args.approval_decision
        else None
    )
    completion_root = (
        Path(args.completion_root).resolve()
        if args.completion_root
        else None
    )

    try:
        plan = build_worker_invocation(
            root=root,
            module_root=module_root,
            launch_request_path=launch_request,
            runtime_path=runtime,
            decision_path=decision,
            completion_root=completion_root,
        )
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    if args.print:
        print(
            yaml.safe_dump(
                plan.document,
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
        output_path = None
    elif args.no_write:
        output_path = None
    else:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = root / output_dir
        output_path = write_invocation_plan(
            plan=plan,
            output_dir=output_dir,
        )

    print(render_summary(plan, output_path=output_path))
    if args.require_ready and plan.state != STATE_DRY_RUN_READY:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
