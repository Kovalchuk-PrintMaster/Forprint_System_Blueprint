"""Authority-neutral execution-side Worker Runtime invocation adapter.

This module owns provider-specific argv rendering only. It does not grant
dispatch authority, start processes, append attempt records, accept candidates,
promote candidates, commit, push, merge, release or mutate lifecycle/roadmap.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.worker_runtime import registry


class WorkerRuntimeInvocationError(RuntimeError):
    """Raised when a launch invocation cannot be derived safely."""


SUPPORTED_PROVIDER = "github_copilot_cli"
WORKER_VALIDATION_MCP_SERVER = "ForPrintValidation"
WORKER_VALIDATION_MCP_TOOL = "run_validation_suite"
WORKER_VALIDATION_MCP_SCRIPT = (
    "scripts/coordination/control_plane/worker_runtime/"
    "worker_validation_mcp.py"
)
GITHUB_COPILOT_MCP_MODEL_TOOL_ID = (
    f"{WORKER_VALIDATION_MCP_SERVER}-{WORKER_VALIDATION_MCP_TOOL}"
)
GITHUB_COPILOT_MCP_PERMISSION_PATTERN = (
    f"{WORKER_VALIDATION_MCP_SERVER}({WORKER_VALIDATION_MCP_TOOL})"
)
GITHUB_COPILOT_AVAILABLE_TOOLS = (
    "view",
    "edit",
    "apply_patch",
    GITHUB_COPILOT_MCP_MODEL_TOOL_ID,
)
DEFAULT_HEARTBEAT_SECONDS = 15
DEFAULT_STALL_THRESHOLD_SECONDS = 120.0

_FORBIDDEN_DECISION_AUTHORITY = (
    "external_dispatch_allowed",
    "release_allowed",
    "push_allowed",
    "merge_allowed",
    "foreign_repository_write_allowed",
    "automatic_accept_allowed",
)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _argv_sha256(argv: list[str]) -> str:
    return hashlib.sha256("\0".join(argv).encode("utf-8")).hexdigest()


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkerRuntimeInvocationError(f"{label} must be a mapping")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkerRuntimeInvocationError(f"{label} must be a non-empty string")
    return value.strip()


def _validate_authority(
    *,
    task_context: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    authority = _require_mapping(task_context.get("authority"), "task context authority")
    required_false = (
        "context_grants_authority",
        "dispatch_authority_conferred",
        "release_authority_conferred",
        "foreign_write_authority_conferred",
    )
    widened_context = [
        key for key in required_false if authority.get(key) is not False
    ]
    if widened_context:
        raise WorkerRuntimeInvocationError(
            "task context authority widened: " + ",".join(widened_context)
        )

    if decision.get("worker_process_launch_allowed") is not True:
        raise WorkerRuntimeInvocationError(
            "explicit dispatch does not authorize Worker process launch"
        )
    if decision.get("canonical_attempt_ledger_append_allowed") is not True:
        raise WorkerRuntimeInvocationError(
            "explicit dispatch does not authorize attempt-ledger append"
        )

    widened_decision = [
        key
        for key in _FORBIDDEN_DECISION_AUTHORITY
        if decision.get(key) is not False
    ]
    if widened_decision:
        raise WorkerRuntimeInvocationError(
            "explicit dispatch widened forbidden authority: "
            + ",".join(widened_decision)
        )

    if decision.get("grants_broad_dispatch_authority") is not False:
        raise WorkerRuntimeInvocationError(
            "explicit dispatch must remain exact and non-broad"
        )


def _validate_binding(
    *,
    task_context: dict[str, Any],
    decision: dict[str, Any],
    workspace_repo: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    envelope = _require_mapping(task_context.get("task_envelope"), "task envelope")
    envelope_authority = _require_mapping(
        envelope.get("authority"),
        "task envelope authority",
    )
    if envelope_authority.get("task_envelope_grants_authority") is not False:
        raise WorkerRuntimeInvocationError(
            "task envelope unexpectedly grants authority"
        )
    if envelope_authority.get("widening_requested") is not False:
        raise WorkerRuntimeInvocationError(
            "task envelope requests authority widening"
        )

    binding = _require_mapping(decision.get("binding"), "explicit dispatch binding")

    task_id = _require_string(envelope.get("task_id"), "task envelope task_id")
    module_id = _require_string(envelope.get("module_id"), "task envelope module_id")
    work = _require_mapping(envelope.get("work"), "task envelope work")
    profile = _require_mapping(
        envelope.get("execution_profile"),
        "task envelope execution_profile",
    )
    procedure = _require_mapping(envelope.get("procedure"), "task envelope procedure")

    expected_profile_ref = (
        f"{_require_string(profile.get('profile_id'), 'profile_id')}"
        f"@{_require_string(profile.get('revision'), 'profile revision')}"
    )
    expected_procedure = _require_string(
        procedure.get("procedure_id"),
        "procedure_id",
    )

    checks = {
        "task_prompt_id": task_id,
        "work_front_id": _require_string(
            work.get("work_front_id"),
            "task envelope work_front_id",
        ),
        "profile_ref": expected_profile_ref,
        "procedure_id": expected_procedure,
        "workspace_repo": str(workspace_repo),
    }

    if module_id != "forprint_system_blueprint":
        raise WorkerRuntimeInvocationError(
            "v0.1 internal execution adapter is Blueprint-only"
        )

    drift = [
        key
        for key, expected in checks.items()
        if binding.get(key) != expected
    ]
    if drift:
        raise WorkerRuntimeInvocationError(
            "explicit dispatch / Task Envelope binding drift: "
            + ",".join(drift)
        )

    if task_context.get("task_id") != task_id:
        raise WorkerRuntimeInvocationError("task context task_id drift")
    if task_context.get("module_id") != module_id:
        raise WorkerRuntimeInvocationError("task context module_id drift")

    return envelope, binding


def _validated_governed_worker_context(
    governed_worker_context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if governed_worker_context is None:
        return None
    context = _require_mapping(
        governed_worker_context,
        "governed Worker context",
    )
    if context.get("schema_version") != (
        "forprint_governed_worker_context_projection_v0_1"
    ):
        raise WorkerRuntimeInvocationError(
            "governed Worker context schema invalid"
        )
    authority = _require_mapping(
        context.get("authority"),
        "governed Worker context authority",
    )
    required_false = (
        "context_grants_authority",
        "dispatch_authority_granted",
        "release_authority_granted",
        "cross_repository_write_authority_granted",
    )
    widened = [
        key for key in required_false
        if authority.get(key) is not False
    ]
    if widened:
        raise WorkerRuntimeInvocationError(
            "governed Worker context authority widened: "
            + ",".join(widened)
        )

    if not isinstance(context.get("dependency_health_slice"), dict):
        raise WorkerRuntimeInvocationError(
            "governed Worker context dependency health invalid"
        )
    if not isinstance(context.get("lifecycle_roadmap_cursor"), dict):
        raise WorkerRuntimeInvocationError(
            "governed Worker context lifecycle cursor invalid"
        )
    if not isinstance(context.get("resume_coordinates"), dict):
        raise WorkerRuntimeInvocationError(
            "governed Worker context resume coordinates invalid"
        )
    if not isinstance(
        context.get("expected_result_schema_revision"),
        str,
    ):
        raise WorkerRuntimeInvocationError(
            "governed Worker context result schema invalid"
        )
    return context


def render_worker_prompt(
    *,
    task_context: dict[str, Any],
    explicit_dispatch_decision: dict[str, Any],
    governed_worker_context: dict[str, Any] | None = None,
) -> str:
    """Render a task-generic Worker prompt from canonical normalized facts."""

    envelope = _require_mapping(task_context.get("task_envelope"), "task envelope")
    binding = _require_mapping(
        explicit_dispatch_decision.get("binding"),
        "explicit dispatch binding",
    )
    source = _require_mapping(envelope.get("source"), "task envelope source")

    task_artifact_ref = _require_string(
        source.get("artifact_ref"),
        "task source artifact_ref",
    )
    work_front_ref = _require_string(
        binding.get("work_front_ref"),
        "explicit dispatch work_front_ref",
    )

    envelope_yaml = yaml.safe_dump(
        envelope,
        sort_keys=False,
        allow_unicode=True,
        width=112,
    ).rstrip()

    governed = _validated_governed_worker_context(
        governed_worker_context
    )
    governed_section = ""
    if governed is not None:
        governed_yaml = yaml.safe_dump(
            governed,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip()
        governed_section = (
            "\nGOVERNED EXECUTION CONTEXT — NON-AUTHORITATIVE\n"
            "- Work Front remains execution authority.\n"
            "- Task Envelope remains task instruction/context.\n"
            "- Governed execution context is verification context only.\n"
            "- The hash-bound governed context is the attempt-scoped freshness "
            "verification snapshot.\n"
            "- Treat roadmap_sync=IN_SYNC plus the bound ACTIVE work item as "
            "sufficient freshness proof for this attempt unless the projection "
            "is internally inconsistent.\n"
            "- Do not regenerate lifecycle/roadmap freshness through shell commands.\n"
            "- Do not mutate lifecycle/roadmap to prove freshness.\n"
            "- Context cannot widen path, dispatch, git, release, "
            "promotion or acceptance authority.\n"
            f"{governed_yaml}\n"
        )

    return (
        "You are the bounded ForPrint internal Worker for one exact execution attempt.\n\n"
        "AUTHORITY AND SOURCE BOUNDARIES\n"
        "- Chat text is not execution authority.\n"
        f"- Canonical Worker Task artifact: {task_artifact_ref}\n"
        f"- Canonical Work Front: {work_front_ref}\n"
        "- The Work Front remains execution authority.\n"
        "- The normalized Task Envelope below is instruction/context, not authority.\n"
        "- Do not widen scope or authority.\n"
        "- Modify only paths permitted by the canonical Task and Work Front.\n"
        "- Do not accept/promote/commit/push/merge/release.\n"
        "- Return bounded evidence for verification and operator review.\n\n"
        "MANDATORY MACHINE-READABLE RESULT RETURN PROTOCOL\n"
        "- Your final provider response must contain exactly one Handoff v2 YAML result frame.\n"
        "- Emit no non-whitespace content outside the frame.\n"
        "- Begin with the exact line: FORPRINT_HANDOFF_V2_RESULT_BEGIN\n"
        "- End with the exact line: FORPRINT_HANDOFF_V2_RESULT_END\n"
        "- The framed YAML must use schema_version "
        "forprint_assistant_handoff_v2_result_v0_1 and exactly the existing "
        "Handoff v2 result fields.\n"
        "- Use the exact attempt_id from the dispatch binding and the exact "
        "handoff_manifest_sha256 from the governed context.\n"
        "- Copy S4 resume bindings verbatim from the governed context: "
        "resume_coordinates.source_state_fingerprint must equal "
        "governed_worker_context.handoff_source_state_fingerprint, and "
        "resume_coordinates.lifecycle_roadmap_cursor must equal "
        "governed_worker_context.lifecycle_roadmap_cursor exactly.\n"
        "- Treat bound resume hashes and cursor values as opaque data: do not "
        "recompute, shorten, normalize, infer, repair or rewrite them.\n"
        "- For PARTIAL, INTERRUPTED, BLOCKED or RETRYABLE_FAILURE status, include "
        "latest_completed_node, latest_accepted_ref and replay_forbidden_refs in "
        "resume_coordinates exactly as required by the canonical S4 contract.\n"
        "- Do not invent or synthesize missing result fields.\n"
        "- Result transport grants no acceptance, promotion, Git, retry or release authority.\n\n"
        "NORMALIZED TASK ENVELOPE\n"
        f"{envelope_yaml}\n"
        f"{governed_section}"
    )


def build_launch_invocation(
    *,
    root: Path | str,
    task_context: dict[str, Any],
    explicit_dispatch_decision: dict[str, Any],
    attempt_root: Path | str,
    governed_worker_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic provider invocation plan without starting a process."""

    root_path = Path(root).resolve()
    attempt = Path(attempt_root).expanduser().resolve()
    workspace = (attempt / "workspace" / "repo").resolve()

    if not workspace.is_dir():
        raise WorkerRuntimeInvocationError("attempt workspace repo is missing")

    _validate_authority(
        task_context=task_context,
        decision=explicit_dispatch_decision,
    )
    envelope, binding = _validate_binding(
        task_context=task_context,
        decision=explicit_dispatch_decision,
        workspace_repo=workspace,
    )

    governed = _validated_governed_worker_context(
        governed_worker_context
    )
    bound_governed_digest = binding.get(
        "governed_worker_context_sha256"
    )
    if bound_governed_digest is not None and governed is None:
        raise WorkerRuntimeInvocationError(
            "explicit dispatch binds governed Worker context but none was supplied"
        )
    if governed is not None and bound_governed_digest is None:
        raise WorkerRuntimeInvocationError(
            "governed Worker context supplied without dispatch digest binding"
        )

    runtime_config = registry.load_module_runtime_config(root_path)
    runtime = registry.resolve_default_runtime(root_path)

    if runtime_config.get("module_id") != "forprint_system_blueprint":
        raise WorkerRuntimeInvocationError("runtime config module drift")
    if runtime_config.get("provider_adapter") != "CONSOLE_COMMAND":
        raise WorkerRuntimeInvocationError("unsupported provider adapter")
    if runtime.get("command_representation") != "ARGV_NO_SHELL":
        raise WorkerRuntimeInvocationError("runtime must remain ARGV_NO_SHELL")
    if runtime.get("working_directory") != "ATTEMPT_WORKSPACE_REPO":
        raise WorkerRuntimeInvocationError("runtime working-directory policy drift")

    command = _require_mapping(runtime_config.get("command"), "runtime command")
    if command.get("prompt_transport") != "provider_adapter_owned":
        raise WorkerRuntimeInvocationError("prompt transport ownership drift")
    if command.get("shell") is not False:
        raise WorkerRuntimeInvocationError("shell execution is forbidden")

    tool_policy = _require_mapping(
        runtime_config.get("tool_policy"),
        "runtime tool_policy",
    )
    if tool_policy.get("exact_runtime_argv_deferred_to_launch_adapter") is not True:
        raise WorkerRuntimeInvocationError(
            "runtime no longer delegates exact argv to launch adapter"
        )
    for key in (
        "automatic_accept_allowed",
        "canonical_repository_write_allowed",
        "foreign_repository_write_allowed",
        "git_commit_allowed",
        "git_push_allowed",
        "merge_allowed",
        "release_allowed",
    ):
        if tool_policy.get(key) is not False:
            raise WorkerRuntimeInvocationError(
                f"runtime tool policy widened authority: {key}"
            )

    provider_id = _require_string(runtime.get("provider_id"), "runtime provider_id")
    model_id = _require_string(runtime.get("model_id"), "runtime model_id")
    executable = _require_string(runtime.get("executable"), "runtime executable")

    if binding.get("runtime_provider") != provider_id:
        raise WorkerRuntimeInvocationError("dispatch/runtime provider drift")
    if binding.get("runtime_model") != model_id:
        raise WorkerRuntimeInvocationError("dispatch/runtime model drift")

    if provider_id != SUPPORTED_PROVIDER:
        raise WorkerRuntimeInvocationError(
            f"provider adapter not implemented: {provider_id}"
        )

    base_argv = command.get("base_argv")
    if (
        not isinstance(base_argv, list)
        or not base_argv
        or not all(isinstance(item, str) and item for item in base_argv)
    ):
        raise WorkerRuntimeInvocationError("runtime command base_argv invalid")
    if base_argv[0] != executable:
        raise WorkerRuntimeInvocationError("base_argv executable drift")

    executable_path = Path(executable)
    if not executable_path.is_file():
        raise WorkerRuntimeInvocationError("configured runtime executable is missing")

    budget = _require_mapping(runtime_config.get("budget"), "runtime budget")
    provider_budget = _require_mapping(
        budget.get("provider_specific"),
        "runtime provider-specific budget",
    )
    max_ai_credits = provider_budget.get("max_ai_credits")
    if (
        not isinstance(max_ai_credits, int)
        or isinstance(max_ai_credits, bool)
        or max_ai_credits <= 0
    ):
        raise WorkerRuntimeInvocationError("max_ai_credits must be positive")

    timeout_seconds = runtime.get("timeout_seconds")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise WorkerRuntimeInvocationError("runtime timeout_seconds invalid")

    prompt = render_worker_prompt(
        task_context=task_context,
        explicit_dispatch_decision=explicit_dispatch_decision,
        governed_worker_context=governed,
    )

    mcp_script = (workspace / WORKER_VALIDATION_MCP_SCRIPT).resolve()
    if not mcp_script.is_file() or mcp_script.is_symlink():
        raise WorkerRuntimeInvocationError(
            "attempt workspace Worker validation MCP server is missing or unsafe"
        )

    python_executable = sys.executable
    python_executable_path = Path(python_executable)
    if (
        not python_executable_path.is_absolute()
        or not python_executable_path.is_file()
    ):
        raise WorkerRuntimeInvocationError(
            "current Python runtime for Worker validation MCP is unavailable"
        )

    attempt_id = _require_string(binding.get("attempt_id"), "attempt_id")
    decision_id = _require_string(
        explicit_dispatch_decision.get("decision_id"),
        "decision_id",
    )
    task_id = _require_string(envelope.get("task_id"), "task_id")
    work_front_id = _require_string(
        binding.get("work_front_id"),
        "work_front_id",
    )
    structured_evidence_root = (
        attempt / "evidence" / "structured_command"
    ).resolve()

    mcp_config = {
        "mcpServers": {
            WORKER_VALIDATION_MCP_SERVER: {
                "type": "local",
                "command": python_executable,
                "args": [
                    str(mcp_script),
                    "--attempt-id",
                    attempt_id,
                    "--task-id",
                    task_id,
                    "--work-front-id",
                    work_front_id,
                    "--decision-id",
                    decision_id,
                    "--workspace-repo",
                    str(workspace),
                    "--evidence-root",
                    str(structured_evidence_root),
                ],
                "tools": [WORKER_VALIDATION_MCP_TOOL],
                "cwd": str(workspace),
            }
        }
    }
    mcp_config_json = json.dumps(
        mcp_config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    argv = [
        *base_argv,
        "-p",
        prompt,
        "--silent",
        "--model",
        model_id,
        "--additional-mcp-config",
        mcp_config_json,
        "--available-tools",
        *GITHUB_COPILOT_AVAILABLE_TOOLS,
        "--allow-all-tools",
        "--disable-builtin-mcps",
        "--max-ai-credits",
        str(max_ai_credits),
        "--no-auto-update",
        "-C",
        str(workspace),
    ]

    input_dir = attempt / "input"
    logs_dir = attempt / "logs"
    evidence_dir = attempt / "evidence"

    result = {
        "schema_version": "forprint_worker_runtime_launch_invocation_v0_1",
        "attempt_id": attempt_id,
        "decision_id": decision_id,
        "task_id": task_id,
        "work_front_id": work_front_id,
        "provider_id": provider_id,
        "runtime_id": runtime.get("runtime_id"),
        "model_id": model_id,
        "command_representation": "ARGV_NO_SHELL",
        "workspace_repo": str(workspace),
        "prompt": prompt,
        "prompt_sha256": _sha256_text(prompt),
        "argv": argv,
        "argv_sha256": _argv_sha256(argv),
        "timeout_seconds": timeout_seconds,
        "heartbeat_seconds": DEFAULT_HEARTBEAT_SECONDS,
        "stall_threshold_seconds": DEFAULT_STALL_THRESHOLD_SECONDS,
        "paths": {
            "prompt": str(input_dir / "worker_prompt.txt"),
            "invocation": str(input_dir / "worker_invocation_v0_1.yaml"),
            "stdout": str(logs_dir / "stdout.log"),
            "stderr": str(logs_dir / "stderr.log"),
            "process_started": str(
                evidence_dir / "worker_process_started_v0_1.yaml"
            ),
            "process_result": str(
                evidence_dir / "worker_process_result_v0_1.yaml"
            ),
        },
        "provider_policy": {
            "available_tools": list(GITHUB_COPILOT_AVAILABLE_TOOLS),
            "mcp_permission_patterns": [
                GITHUB_COPILOT_MCP_PERMISSION_PATTERN
            ],
            "permission_mode": "ALLOW_ALL_WITHIN_AVAILABLE_TOOL_UNIVERSE",
            "bash_available": False,
            "web_available": False,
            "builtin_mcps_disabled": True,
            "additional_mcp_config_source": "SESSION_ONLY_ARGV",
            "mcp_server_names": [WORKER_VALIDATION_MCP_SERVER],
            "mcp_transport": "STDIO_LOCAL",
            "persistent_mcp_config_written": False,
        },
        "authority": {
            "adapter_grants_authority": False,
            "explicit_dispatch_consumed": True,
            "worker_process_start_authorized_by": "EXPLICIT_DISPATCH_DECISION",
            "automatic_accept_allowed": False,
            "canonical_promotion_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
        },
        "effects": {
            "filesystem_write_performed": False,
            "worker_process_started": False,
            "attempt_ledger_appended": False,
            "candidate_promoted": False,
            "commit_performed": False,
            "push_performed": False,
        },
    }

    stable = dict(result)
    stable.pop("argv_sha256", None)
    stable["prompt"] = "<prompt-bound-by-prompt_sha256>"
    result["invocation_sha256"] = hashlib.sha256(
        json.dumps(
            stable,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return result


def build_invocation_evidence(
    invocation: dict[str, Any],
) -> dict[str, Any]:
    """Return durable invocation evidence without prompt text or full argv."""

    if not isinstance(invocation, dict):
        raise WorkerRuntimeInvocationError("invocation must be a mapping")
    for key in ("prompt_sha256", "argv_sha256", "invocation_sha256"):
        if not isinstance(invocation.get(key), str) or not invocation[key]:
            raise WorkerRuntimeInvocationError(
                f"invocation {key} missing"
            )

    evidence = {
        "schema_version": "forprint_worker_runtime_invocation_evidence_v0_1",
        "attempt_id": invocation.get("attempt_id"),
        "decision_id": invocation.get("decision_id"),
        "task_id": invocation.get("task_id"),
        "work_front_id": invocation.get("work_front_id"),
        "provider_id": invocation.get("provider_id"),
        "runtime_id": invocation.get("runtime_id"),
        "model_id": invocation.get("model_id"),
        "command_representation": invocation.get("command_representation"),
        "workspace_repo": invocation.get("workspace_repo"),
        "prompt_sha256": invocation.get("prompt_sha256"),
        "argv_sha256": invocation.get("argv_sha256"),
        "invocation_sha256": invocation.get("invocation_sha256"),
        "timeout_seconds": invocation.get("timeout_seconds"),
        "heartbeat_seconds": invocation.get("heartbeat_seconds"),
        "stall_threshold_seconds": invocation.get(
            "stall_threshold_seconds"
        ),
        "paths": invocation.get("paths"),
        "provider_policy": invocation.get("provider_policy"),
        "authority": invocation.get("authority"),
        "effects": invocation.get("effects"),
        "serialization_boundary": {
            "prompt_text_serialized": False,
            "full_argv_serialized": False,
            "secret_values_serialized": False,
        },
    }

    rendered = yaml.safe_dump(
        evidence,
        sort_keys=False,
        allow_unicode=True,
        width=112,
    )
    prompt = invocation.get("prompt")
    if isinstance(prompt, str) and prompt and prompt in rendered:
        raise WorkerRuntimeInvocationError(
            "sanitized invocation evidence leaked prompt text"
        )

    argv = invocation.get("argv")
    if isinstance(argv, list) and argv:
        argv_json = json.dumps(argv, ensure_ascii=False)
        if argv_json in rendered:
            raise WorkerRuntimeInvocationError(
                "sanitized invocation evidence leaked full argv"
            )

    return evidence
