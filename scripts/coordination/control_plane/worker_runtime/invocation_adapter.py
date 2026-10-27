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
from scripts.coordination.control_plane import validation_evidence_readback_selection_v0_1 as readback


class WorkerRuntimeInvocationError(RuntimeError):
    """Raised when a launch invocation cannot be derived safely."""


SUPPORTED_PROVIDER = "github_copilot_cli"
# Copilot CLI 1.0.88 rejects --max-ai-credits values below 30.
# Keep aligned with the supported provider CLI; this is an argument floor, not a spend target.
COPILOT_CLI_MIN_AI_CREDITS = 30
WORKER_VALIDATION_MCP_SERVER = "ForPrintValidation"
WORKER_VALIDATION_MCP_TOOL = "run_validation_suite"
WORKER_REPO_DIFF_CHECK_MCP_TOOL = "run_repo_diff_check"
# CF10_STAGE3_FIXED_GIT_READ_ONLY_TOOLS_V0_1
WORKER_REPO_HEAD_MCP_TOOL = "run_repo_head"
WORKER_REPO_STATUS_MCP_TOOL = "run_repo_status"
WORKER_COMPLETED_READBACK_MCP_TOOL = "read_completed_validation_evidence"
WORKER_VALIDATION_MCP_SCRIPT = (
    "scripts/coordination/control_plane/worker_runtime/"
    "worker_validation_mcp.py"
)

GITHUB_COPILOT_MCP_MODEL_TOOL_ID = (
    f"{WORKER_VALIDATION_MCP_SERVER}-{WORKER_VALIDATION_MCP_TOOL}"
)
GITHUB_COPILOT_REPO_DIFF_MCP_MODEL_TOOL_ID = (
    f"{WORKER_VALIDATION_MCP_SERVER}-"
    f"{WORKER_REPO_DIFF_CHECK_MCP_TOOL}"
)
GITHUB_COPILOT_REPO_HEAD_MCP_MODEL_TOOL_ID = (
    f"{WORKER_VALIDATION_MCP_SERVER}-{WORKER_REPO_HEAD_MCP_TOOL}"
)
GITHUB_COPILOT_REPO_STATUS_MCP_MODEL_TOOL_ID = (
    f"{WORKER_VALIDATION_MCP_SERVER}-{WORKER_REPO_STATUS_MCP_TOOL}"
)
GITHUB_COPILOT_READBACK_MCP_MODEL_TOOL_ID = (
    f"{WORKER_VALIDATION_MCP_SERVER}-{WORKER_COMPLETED_READBACK_MCP_TOOL}"
)

GITHUB_COPILOT_MCP_PERMISSION_PATTERN = (
    f"{WORKER_VALIDATION_MCP_SERVER}({WORKER_VALIDATION_MCP_TOOL})"
)
GITHUB_COPILOT_REPO_DIFF_MCP_PERMISSION_PATTERN = (
    f"{WORKER_VALIDATION_MCP_SERVER}"
    f"({WORKER_REPO_DIFF_CHECK_MCP_TOOL})"
)
GITHUB_COPILOT_REPO_HEAD_MCP_PERMISSION_PATTERN = (
    f"{WORKER_VALIDATION_MCP_SERVER}({WORKER_REPO_HEAD_MCP_TOOL})"
)
GITHUB_COPILOT_REPO_STATUS_MCP_PERMISSION_PATTERN = (
    f"{WORKER_VALIDATION_MCP_SERVER}({WORKER_REPO_STATUS_MCP_TOOL})"
)
GITHUB_COPILOT_READBACK_MCP_PERMISSION_PATTERN = (
    f"{WORKER_VALIDATION_MCP_SERVER}({WORKER_COMPLETED_READBACK_MCP_TOOL})"
)

GITHUB_COPILOT_AVAILABLE_TOOLS = (
    "view",
    "edit",
    "apply_patch",
    GITHUB_COPILOT_MCP_MODEL_TOOL_ID,
    GITHUB_COPILOT_REPO_DIFF_MCP_MODEL_TOOL_ID,
    GITHUB_COPILOT_REPO_HEAD_MCP_MODEL_TOOL_ID,
    GITHUB_COPILOT_REPO_STATUS_MCP_MODEL_TOOL_ID,
)
DEFAULT_HEARTBEAT_SECONDS = 15
DEFAULT_STALL_THRESHOLD_SECONDS = 120.0

# B4-P2C: session-only Copilot MCP timeout is separate from the Worker deadline.
# The current registered validation bridge has a 900-second inner budget.
_CF10_VALIDATION_BRIDGE_TIMEOUT_MS = 900_000
_COPILOT_MCP_TIMEOUT_MAX_MS = 1_200_000


def _resolve_copilot_mcp_tool_timeout_ms(
    *, runtime_config: dict[str, Any], worker_timeout_seconds: int,
) -> int | None:
    policy = runtime_config.get("copilot_mcp")
    if policy is None:
        # Legacy lightweight test fixtures omit the canonical schema_version.
        # A real canonical module runtime must never silently fall back to 30s.
        if runtime_config.get("schema_version") == "forprint_module_worker_runtime_v0_1":
            raise WorkerRuntimeInvocationError("canonical Copilot MCP timeout policy missing")
        return None
    if not isinstance(policy, dict) or set(policy) != {
        "tool_timeout_ms", "minimum_worker_finish_reserve_seconds",
    }:
        raise WorkerRuntimeInvocationError("invalid Copilot MCP timeout policy")
    ms = policy["tool_timeout_ms"]
    reserve = policy["minimum_worker_finish_reserve_seconds"]
    if (type(ms) is not int or not
            _CF10_VALIDATION_BRIDGE_TIMEOUT_MS < ms <= _COPILOT_MCP_TIMEOUT_MAX_MS):
        raise WorkerRuntimeInvocationError("Copilot MCP timeout must exceed validation bridge budget")
    if type(reserve) is not int or reserve < 120:
        raise WorkerRuntimeInvocationError("Worker result finish reserve too small")
    if runtime_config.get("timeout_seconds") != worker_timeout_seconds:
        raise WorkerRuntimeInvocationError("Copilot MCP and Worker timeout config drift")
    if worker_timeout_seconds * 1000 - ms < reserve * 1000:
        raise WorkerRuntimeInvocationError("Copilot MCP timeout leaves insufficient Worker result reserve")
    return ms

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



# CF10_S4_LITERAL_RESUME_CAPSULE_V0_1_START

def render_literal_s4_resume_binding(
    *,
    governed_worker_context: dict[str, Any],
    attempt_id: str,
) -> str:
    """Render authoritative S4 base fields as literal YAML for the Worker.

    This does NOT generate a Worker result or change validator semantics.
    All hash/cursor values come from the already-validated governed context.
    """
    governed = _validated_governed_worker_context(governed_worker_context)
    if governed is None:
        raise WorkerRuntimeInvocationError("S4 literal binding requires governed context")
    cursor = _require_mapping(
        governed.get("lifecycle_roadmap_cursor"),
        "governed S4 lifecycle_roadmap_cursor",
    )
    frozen_resume = {
        "attempt_id": _require_string(attempt_id, "S4 attempt_id"),
        "handoff_manifest_sha256": _require_string(
            governed.get("handoff_manifest_sha256"), "S4 handoff hash"
        ),
        "source_state_fingerprint": _require_string(
            governed.get("handoff_source_state_fingerprint"), "S4 source fingerprint"
        ),
        "lifecycle_roadmap_cursor": cursor,
    }
    return yaml.safe_dump(
        {"resume_coordinates": frozen_resume},
        sort_keys=False,
        allow_unicode=True,
        width=110,
    ).rstrip()

# CF10_S4_LITERAL_RESUME_CAPSULE_V0_1_END

# CF10_STAGE4C_TRUSTED_TRANSPORT_BINDING_V0_1
LEGACY_RESULT_TRANSPORT = "handoff-v2-full"
DRAFT_RESULT_TRANSPORT = "worker-completion-draft-v0-1"


def _assert_selected_transport(decision: dict[str, Any], result_transport: str) -> None:
    """Require the trusted caller's mode to agree with the hash-bound decision."""
    if result_transport not in (LEGACY_RESULT_TRANSPORT, DRAFT_RESULT_TRANSPORT):
        raise WorkerRuntimeInvocationError("unsupported trusted result_transport")
    binding = _require_mapping(decision.get("binding"), "explicit dispatch binding")
    if "result_transport_selection" not in binding:
        if result_transport != LEGACY_RESULT_TRANSPORT:
            raise WorkerRuntimeInvocationError("unbound draft result transport refused")
        return  # preserve historical legacy fixture/result behavior
    selector = _require_mapping(
        binding["result_transport_selection"], "bound result transport selection",
    )
    if selector.get("schema_version") != "forprint_cf10_result_transport_selection_v0_1":
        raise WorkerRuntimeInvocationError("transport selector schema mismatch")
    if selector.get("transport") != result_transport:
        raise WorkerRuntimeInvocationError("invocation/result transport selection disagreement")
    for field in ("task_prompt_id", "work_front_id", "work_front_ref"):
        if selector.get(field) != binding.get(field):
            raise WorkerRuntimeInvocationError("transport selector identity drift: " + field)
    if not isinstance(selector.get("policy_sha256"), str) or len(selector["policy_sha256"]) != 64:
        raise WorkerRuntimeInvocationError("transport policy SHA invalid")
    expected_id = hashlib.sha256(json.dumps(
        binding, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    if decision.get("decision_id") != expected_id:
        raise WorkerRuntimeInvocationError("bound transport decision hash mismatch")

def render_worker_prompt(
    *,
    task_context: dict[str, Any],
    explicit_dispatch_decision: dict[str, Any],
    governed_worker_context: dict[str, Any] | None = None,
    result_transport: str = LEGACY_RESULT_TRANSPORT,
) -> str:
    """Render a task-generic Worker prompt from canonical normalized facts."""

    envelope = _require_mapping(task_context.get("task_envelope"), "task envelope")
    binding = _require_mapping(
        explicit_dispatch_decision.get("binding"),
        "explicit dispatch binding",
    )
    _assert_selected_transport(explicit_dispatch_decision, result_transport)
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
    if result_transport == DRAFT_RESULT_TRANSPORT:
        if governed is None:
            raise WorkerRuntimeInvocationError("draft result requires bound governed context")
        # The draft is Worker-owned facts only: no origin SHA, full Handoff or S4
        # literal is model-transcribed. Stage 4A composes authoritative coordinates.
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
            "- Emit exactly one strict JSON Worker completion draft, and no other stdout text.\n"
            "- Begin the first non-whitespace content with exactly "
            "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_BEGIN.\n"
            "- End the last non-whitespace content with exactly "
            "FORPRINT_WORKER_COMPLETION_DRAFT_V0_1_END.\n"
            "- Between those markers emit exactly one JSON object containing only "
            "status, changed_paths, validation_evidence, self_repair_attempts, "
            "unresolved_findings, and optional partial_resume.\n"
            "- For PARTIAL/INTERRUPTED/BLOCKED/RETRYABLE_FAILURE include partial_resume "
            "with exactly latest_completed_node, latest_accepted_ref, replay_forbidden_refs.\n"
            "- No unknown fields, duplicate JSON keys, or commentary outside the frame.\n"
            "- Do not supply attempt_id, manifest SHA, roadmap cursor, "
            "source_state_fingerprint, resume_coordinates or origin data.\n"
            "- The original validated attempt context, not Worker stdout, will be "
            "used by the independent result composer and strict validators.\n"
            "- Do not invent missing facts or evidence.\n"
            "- Result transport grants no acceptance, promotion, Git, retry or release authority.\n\n"
            "NORMALIZED TASK ENVELOPE\n"
            f"{envelope_yaml}\n"
        )

    governed_section = ""
    if governed is not None:
        governed_yaml = yaml.safe_dump(
            governed,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip()
        literal_resume = render_literal_s4_resume_binding(
            governed_worker_context=governed,
            attempt_id=_require_string(binding.get("attempt_id"), "dispatch attempt_id"),
        )
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
            "\nS4 RESULT RESUME BINDING — LITERAL COPY START\n"
            f"{literal_resume}\n"
            "S4 RESULT RESUME BINDING — LITERAL COPY END\n"
            "- Copy the entire literal resume_coordinates mapping above unchanged "
            "into the Handoff v2 result; add partial/resumable fields only when required.\n"
            "- Never recalculate roadmap_status_sha256 from files, the Git workspace, "
            "fresh roadmap status, or any command; the frozen digest is origin-bound.\n"
            "- Future advisory suggestions require separate governed, versioned "
            "artifacts; no additional Worker stdout is allowed.\n"
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
        "- Do not emit any assistant-facing progress updates, status narration, "
        "summaries, tool-call preambles, or tool-call postambles at any time.\n"
        "- The first non-whitespace content written to provider stdout must be "
        "exactly FORPRINT_HANDOFF_V2_RESULT_BEGIN.\n"
        "- The last non-whitespace content written to provider stdout must be "
        "exactly FORPRINT_HANDOFF_V2_RESULT_END.\n"
        "- Encode all failures, limitations, partial status, and unresolved "
        "findings inside the framed YAML; never emit them as prose outside "
        "the frame.\n"
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


# CF10_B3_P2_INDEPENDENT_INVOCATION_GUARD_V0_1_START

def _verify_b3_readback_invocation(
    *, root: Path, decision: dict[str, Any],
    trusted_selection: dict[str, Any] | None,
) -> bool:
    """Re-verify P0 policy bytes + dispatch digest in provider adapter itself."""
    binding = _require_mapping(decision.get("binding"), "readback dispatch binding")
    declared = "validation_readback_selection" in binding
    if not declared:
        if trusted_selection is not None:
            raise WorkerRuntimeInvocationError("unbound B3 readback selection refused")
        return False
    if not isinstance(trusted_selection, dict):
        raise WorkerRuntimeInvocationError("bound B3 readback requires trusted prelaunch selection")
    expected_id = hashlib.sha256(json.dumps(
        binding, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    if decision.get("decision_id") != expected_id:
        raise WorkerRuntimeInvocationError("B3 readback dispatch digest mismatch")
    try:
        current = readback.resolve_selection(root=root, task_binding=binding)
    except readback.ReadbackSelectionError as exc:
        raise WorkerRuntimeInvocationError("B3 readback policy verification rejected: " + str(exc)) from exc
    if (current != trusted_selection
            or binding["validation_readback_selection"] != current):
        raise WorkerRuntimeInvocationError("B3 readback trusted policy/dispatch drift")
    return current["enabled"] is True

# CF10_B3_P2_INDEPENDENT_INVOCATION_GUARD_V0_1_END


# CF10_A046_FROZEN_BASELINE_CAPSULE_MINIMAL_V0_1
# READ-ONLY provenance delivery; no new execution, acceptance, or mutation authority.
def _verify_prior_zero_delta_accept(
    *, root: Path, attempt: Path, accepted: str, decision_path: Path,
    decision: dict[str, Any], bindings: dict[str, Any], source_refs: list[Any],
) -> None:
    """Check the *historical* zero-delta ACCEPT contract, never current authority.

    Zero-delta S3 decisions use flat SHA256 fields; ordinary post-commit ACCEPT
    uses per-artifact {path, sha256}. Require an exact signed-off decision byte
    digest in Work Front provenance, an unambiguous terminal ledger fact, and
    byte-identical Worker Result, Result Return, baseline and Handoff files.
    No evidence is generated, rewritten, accepted, promoted or published here.
    """
    def fail(why: str) -> None:
        raise WorkerRuntimeInvocationError("frozen capsule zero-delta ACCEPT " + why)

    def digest_ok(value: Any) -> bool:
        return (isinstance(value, str) and len(value) == 64
                and all(c in "0123456789abcdef" for c in value))

    record_hashes = [x.split(":", 1)[1] for x in source_refs
                     if isinstance(x, str)
                     and x.startswith("accepted_decision_record_sha256:")]
    if len(record_hashes) != 1 or not digest_ok(record_hashes[0]):
        fail("decision provenance digest missing or ambiguous")
    if (not decision_path.is_file() or decision_path.is_symlink()
            or hashlib.sha256(decision_path.read_bytes()).hexdigest() != record_hashes[0]):
        fail("decision provenance digest drift")

    if (decision.get("record_role") != "zero_delta_operator_decision_not_promotion_or_publication"
            or decision.get("zero_delta_confirmed_current_workspace") is not True
            or decision.get("historical_exit_attestation") is not False
            or decision.get("canonical_promotion_performed") is not False
            or decision.get("commit_performed") is not False
            or decision.get("push_performed") is not False
            or decision.get("publication_state") != "NOT_ATTESTED"):
        fail("status or historical scope contradiction")
    if (bindings.get("attempt_id") != accepted
            or bindings.get("task_prompt_id") != decision.get("task_prompt_id")
            or bindings.get("work_front_id") != decision.get("work_front_id")
            or bindings.get("temporal_scope") != "CURRENT_WORKSPACE_AT_REVIEW_NOT_HISTORICAL_EXIT"):
        fail("attempt, Work Front or temporal scope binding drift")

    required_hashes = (
        "proof_sha256", "terminal_sha256", "worker_result_sha256",
        "result_return_sha256", "manifest_sha256", "baseline_sha256",
        "origin_handoff_sha256", "work_front_sha256",
    )
    if (not all(digest_ok(bindings.get(k)) for k in required_hashes)
            or not isinstance(bindings.get("source_head"), str)
            or len(bindings["source_head"]) != 40
            or not all(c in "0123456789abcdef" for c in bindings["source_head"])):
        fail("required evidence digest or source HEAD malformed")

    canonical_store = root / "coordination/continuity/execution_attempts"
    candidates = []
    for path in sorted(canonical_store.glob(accepted + "__*.yaml")):
        if path.is_symlink():
            fail("unsafe terminal ledger path")
        if (path.is_file()
                and hashlib.sha256(path.read_bytes()).hexdigest()
                == bindings["terminal_sha256"]):
            candidates.append(path)
    if len(candidates) != 1:
        fail("terminal ledger missing, duplicated or digest drift")
    terminal = yaml.safe_load(candidates[0].read_text(encoding="utf-8"))
    if (not isinstance(terminal, dict)
            or terminal.get("attempt_id") != accepted
            or terminal.get("attempt_stage") != "FINISHED"
            or terminal.get("result_state") != "SUCCEEDED"
            or terminal.get("validator_outcome") != "PASS"):
        fail("terminal ledger state mismatch")

    prior = attempt.parent / accepted
    evidence_files = {
        "worker_result_sha256": prior / "result/worker_result.yaml",
        "result_return_sha256": prior / "evidence/governed_worker_cycle_result_return_v0_1.yaml",
        "manifest_sha256": prior / "manifest.yaml",
        "baseline_sha256": prior / "evidence/worker_baseline_v0_1.yaml",
        "origin_handoff_sha256": prior / "input/governed_worker_cycle_origin_handoff_manifest_v0_1.yaml",
    }
    for key, path in evidence_files.items():
        if not path.is_file() or path.is_symlink():
            fail("missing/unsafe evidence:" + key)
        if hashlib.sha256(path.read_bytes()).hexdigest() != bindings[key]:
            fail("evidence digest drift:" + key)
    source_file = prior / "input/governed_worker_cycle_source_state_v0_1.yaml"
    if not source_file.is_file() or source_file.is_symlink():
        fail("frozen source missing/unsafe")
    prior_source = yaml.safe_load(source_file.read_text(encoding="utf-8"))
    if (not isinstance(prior_source, dict)
            or prior_source.get("git_head") != bindings["source_head"]):
        fail("frozen source HEAD binding drift")

    returned = yaml.safe_load(evidence_files["result_return_sha256"].read_text(encoding="utf-8"))
    if (not isinstance(returned, dict)
            or returned.get("attempt_id") != accepted
            or returned.get("result") != "PASS"
            or returned.get("validation_passed") is not True):
        fail("result-return state mismatch")

    # No claim of historical process-exit attestation: that flag is false in
    # the accepted S3 zero-delta contract. Unresolved proof/review references
    # are NOT silently interpreted as separate file-path attestations.


def _verified_frozen_launch_context(
    *, root: Path, attempt: Path, workspace: Path, binding: dict[str, Any],
) -> str:
    """Report *pre-worker* facts, reusing exact baseline-delta verification.

    Historical invocation fixtures do not carry a workspace manifest. In a real
    governed launch, the manifest is mandatory before this adapter is called.
    A partially present manifest/baseline always fails closed.
    """
    manifest_path = attempt / "manifest.yaml"
    if not manifest_path.exists() and not manifest_path.is_symlink():
        return ""  # non-governed historical invocation fixtures only

    def read_yaml(path: Path, what: str) -> dict[str, Any]:
        if not path.is_file() or path.is_symlink():
            raise WorkerRuntimeInvocationError("frozen capsule unsafe/missing " + what)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise WorkerRuntimeInvocationError("frozen capsule malformed " + what)
        return data

    manifest = read_yaml(manifest_path, "manifest")
    frozen = read_yaml(
        attempt / "input/governed_worker_cycle_source_state_v0_1.yaml",
        "frozen source",
    )
    baseline_path = attempt / "evidence/worker_baseline_v0_1.yaml"
    baseline = read_yaml(baseline_path, "worker baseline")
    head = frozen.get("git_head")
    fingerprint = frozen.get("fingerprint_sha256")
    baseline_fp = baseline.get("baseline_fingerprint_sha256")
    if (
        not isinstance(head, str) or len(head) != 40
        or not isinstance(fingerprint, str) or len(fingerprint) != 64
        or not isinstance(baseline_fp, str) or len(baseline_fp) != 64
        or manifest.get("source_head") != head
        or baseline.get("source_head") != head
        or manifest.get("source_state_fingerprint") != fingerprint
        or manifest.get("worker_baseline_fingerprint_sha256") != baseline_fp
        or manifest.get("worker_baseline_evidence") != str(baseline_path)
        or manifest.get("workspace_equivalence_validated") is not True
        or manifest.get("source_state_frozen") is not True
        or manifest.get("worker_baseline_captured") is not True
        or baseline.get("workspace_repo") != str(workspace)
        or baseline.get("durable_dirty_paths") != frozen.get("durable_dirty_paths")
    ):
        raise WorkerRuntimeInvocationError("frozen capsule source/baseline binding drift")

    # Existing project-native verifier checks the content-addressed baseline,
    # workspace HEAD and every inherited dirty-path snapshot independently.
    from scripts.coordination.control_plane.workspace.provision import (
        derive_worker_delta_from_manifest,
    )
    delta = derive_worker_delta_from_manifest(manifest_path)
    dirty = baseline.get("baseline_dirty_paths")
    if (
        delta.get("worker_delta_exact") is not True
        or delta.get("workspace_repo") != str(workspace)
        or delta.get("source_head") != head
        or delta.get("baseline_fingerprint_sha256") != baseline_fp
        or delta.get("changed_paths") != []
        or not isinstance(dirty, list)
        or delta.get("inherited_dirty_paths") != dirty
        or not all(isinstance(item, str) for item in dirty)
    ):
        raise WorkerRuntimeInvocationError("frozen capsule initial workspace delta drift")

    lines = [
        "\nFROZEN PRE-WORKER WORKSPACE EVIDENCE — READ-ONLY, NON-AUTHORITATIVE",
        "- These facts were checked by Control Plane BEFORE starting this Worker.",
        "- This is inherited baseline state, NOT changes attributed to this Worker.",
        f"- Frozen canonical Git HEAD: {head}",
        f"- Frozen canonical source fingerprint: {fingerprint}",
        f"- Captured worker baseline fingerprint: {baseline_fp}",
        f"- Initial exact Worker delta: [] (verified before process start)",
        f"- Inherited dirty path count: {len(dirty)}",
        "- Inherited dirty paths (JSON-escaped path strings):",
        json.dumps(dirty, ensure_ascii=True, separators=(",", ":")),
        "- Git status alone shows inherited edits; do not label them new Worker edits.",
        "- Independent post-worker verification still determines actual Worker delta.",
        "- Do not modify unrelated inherited paths, change scope or infer ACCEPT.",
    ]

    # Optional source-backed dependency proof. No task/attempt ID is hardcoded.
    front_ref = binding.get("work_front_ref")
    if not isinstance(front_ref, str) or not (
        front_ref.startswith("coordination/work_fronts/")
        and front_ref.endswith(".yaml")
        and ".." not in Path(front_ref).parts
    ):
        raise WorkerRuntimeInvocationError("frozen capsule Work Front reference invalid")
    front = read_yaml(root / front_ref, "Work Front")
    provenance = front.get("provenance")
    if not isinstance(provenance, dict):
        raise WorkerRuntimeInvocationError("frozen capsule Work Front provenance missing")
    source_refs = provenance.get("source_refs")
    if not isinstance(source_refs, list):
        raise WorkerRuntimeInvocationError("frozen capsule source refs invalid")
    op_refs = [x[len("operator_decision:"):] for x in source_refs
               if isinstance(x, str) and x.startswith("operator_decision:")]
    accepted_refs = [x[len("accepted_attempt:"):] for x in source_refs
                     if isinstance(x, str) and x.startswith("accepted_attempt:")]
    if op_refs:
        if len(op_refs) != 1 or len(accepted_refs) != 1:
            raise WorkerRuntimeInvocationError("frozen capsule ACCEPT binding ambiguous")
        ref, accepted = op_refs[0], accepted_refs[0]
        if not (ref.startswith("coordination/continuity/worker_result_decisions/")
                and ref.endswith(".yaml") and ".." not in Path(ref).parts
                and accepted.startswith("cf10-") and "/" not in accepted
                and ".." not in accepted):
            raise WorkerRuntimeInvocationError("frozen capsule ACCEPT reference unsafe")
        decision = read_yaml(root / ref, "prior operator decision")
        if decision.get("decision") != "ACCEPT" or decision.get("attempt_id") != accepted:
            raise WorkerRuntimeInvocationError("frozen capsule prior ACCEPT mismatched")
        artifacts = decision.get("evidence_bindings")
        if not isinstance(artifacts, dict):
            raise WorkerRuntimeInvocationError("frozen capsule prior ACCEPT bindings missing")
        if decision.get("schema_version") == "cf10_zero_delta_operator_decision_v0_1":
            _verify_prior_zero_delta_accept(
                root=root, attempt=attempt, accepted=accepted,
                decision_path=root / ref, decision=decision,
                bindings=artifacts, source_refs=source_refs,
            )
            prior_proof_label = "Prior operator zero-delta ACCEPT (current-workspace scope) verified via exact accepted evidence:"
        else:
            expected_paths = {
                "terminal_ledger": root / "coordination/continuity/execution_attempts" /
                    Path(str(artifacts.get("terminal_ledger", {}).get("path", ""))).name,
                "worker_result": attempt.parent / accepted / "result/worker_result.yaml",
                "result_return": attempt.parent / accepted /
                    "evidence/governed_worker_cycle_result_return_v0_1.yaml",
            }
            for kind, expected_path in expected_paths.items():
                item = artifacts.get(kind)
                if not isinstance(item, dict) or item.get("path") != str(expected_path):
                    raise WorkerRuntimeInvocationError("frozen capsule prior ACCEPT path drift:" + kind)
                digest = item.get("sha256")
                if not isinstance(digest, str) or len(digest) != 64:
                    raise WorkerRuntimeInvocationError("frozen capsule prior ACCEPT digest missing:" + kind)
                if not expected_path.is_file() or expected_path.is_symlink():
                    raise WorkerRuntimeInvocationError("frozen capsule prior ACCEPT evidence missing:" + kind)
                if hashlib.sha256(expected_path.read_bytes()).hexdigest() != digest:
                    raise WorkerRuntimeInvocationError("frozen capsule prior ACCEPT evidence drift:" + kind)
            prior_proof_label = "Prior operator ACCEPT verified via canonical decision and 3 SHA256-bound artifacts:"
        lines += [
            "- " + prior_proof_label,
            json.dumps({"attempt_id": accepted, "decision_ref": ref},
                       ensure_ascii=True, sort_keys=True),
            "- This confirms the *prior* attempt only; it grants no current ACCEPT.",
        ]
    value = "\n".join(lines) + "\n"
    if len(value.encode("utf-8")) > 32768:
        raise WorkerRuntimeInvocationError("frozen capsule evidence exceeds prompt budget")
    return value

# CF10_A046_FROZEN_BASELINE_CAPSULE_MINIMAL_V0_1_END


def build_launch_invocation(
    *,
    root: Path | str,
    task_context: dict[str, Any],
    explicit_dispatch_decision: dict[str, Any],
    attempt_root: Path | str,
    governed_worker_context: dict[str, Any] | None = None,
    result_transport: str = LEGACY_RESULT_TRANSPORT,
    validation_readback_selection: dict[str, Any] | None = None,
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
    _assert_selected_transport(explicit_dispatch_decision, result_transport)
    readback_enabled = _verify_b3_readback_invocation(
        root=root_path,
        decision=explicit_dispatch_decision,
        trusted_selection=validation_readback_selection,
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
        or max_ai_credits < COPILOT_CLI_MIN_AI_CREDITS
    ):
        raise WorkerRuntimeInvocationError(
            f"max_ai_credits must be at least {COPILOT_CLI_MIN_AI_CREDITS} "
            "for GitHub Copilot CLI"
        )

    timeout_seconds = runtime.get("timeout_seconds")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise WorkerRuntimeInvocationError("runtime timeout_seconds invalid")

    mcp_tool_timeout_ms = _resolve_copilot_mcp_tool_timeout_ms(
        runtime_config=runtime_config, worker_timeout_seconds=timeout_seconds,
    )

    prompt = render_worker_prompt(
        task_context=task_context,
        explicit_dispatch_decision=explicit_dispatch_decision,
        governed_worker_context=governed,
        result_transport=result_transport,
    )
    prompt += _verified_frozen_launch_context(
        root=root_path, attempt=attempt, workspace=workspace, binding=binding,
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
                    *(["--enable-completed-readback"] if readback_enabled else []),
                ],
                "tools": [
                    WORKER_VALIDATION_MCP_TOOL,
                    WORKER_REPO_DIFF_CHECK_MCP_TOOL,
                    WORKER_REPO_HEAD_MCP_TOOL,
                    WORKER_REPO_STATUS_MCP_TOOL,
                    *([WORKER_COMPLETED_READBACK_MCP_TOOL] if readback_enabled else []),
                ],
                "cwd": str(workspace),
                **({"timeout": mcp_tool_timeout_ms} if mcp_tool_timeout_ms is not None else {}),
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
        *([GITHUB_COPILOT_READBACK_MCP_MODEL_TOOL_ID] if readback_enabled else []),
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
            "available_tools": [
                *GITHUB_COPILOT_AVAILABLE_TOOLS,
                *([GITHUB_COPILOT_READBACK_MCP_MODEL_TOOL_ID] if readback_enabled else []),
            ],
            "mcp_permission_patterns": [
                GITHUB_COPILOT_MCP_PERMISSION_PATTERN,
                GITHUB_COPILOT_REPO_DIFF_MCP_PERMISSION_PATTERN,
                GITHUB_COPILOT_REPO_HEAD_MCP_PERMISSION_PATTERN,
                GITHUB_COPILOT_REPO_STATUS_MCP_PERMISSION_PATTERN,
                *([GITHUB_COPILOT_READBACK_MCP_PERMISSION_PATTERN] if readback_enabled else []),
            ],
            "permission_mode": "ALLOW_ALL_WITHIN_AVAILABLE_TOOL_UNIVERSE",
            "bash_available": False,
            "web_available": False,
            "builtin_mcps_disabled": True,
            "additional_mcp_config_source": "SESSION_ONLY_ARGV",
            "mcp_server_names": [WORKER_VALIDATION_MCP_SERVER],
            "mcp_transport": "STDIO_LOCAL",
            "mcp_server_tool_timeout_ms": mcp_tool_timeout_ms,
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
