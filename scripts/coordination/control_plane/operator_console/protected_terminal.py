from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.operator_console.session_projection import (
    ALLOWED_ACTOR_TYPES,
    SCHEMA_VERSION as SESSION_PROJECTION_SCHEMA,
)
from scripts.coordination.control_plane.worker_runtime.launcher import launch_process

SCHEMA_VERSION = "forprint_oc01_protected_terminal_gateway_v0_1"
COMMAND_REPRESENTATION = "ARGV_NO_SHELL"
CANCEL_STATE = "DEPENDENCY_PENDING_CF10"

TERMINAL_ACTOR_TYPES = frozenset(
    actor
    for actor in ALLOWED_ACTOR_TYPES
    if actor in {"operator_assistant", "human_terminal"}
)

READ_ONLY_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "repo_status": ("status", "--short", "--untracked-files=all"),
    "repo_head": ("rev-parse", "HEAD"),
    "repo_diff_check": ("diff", "--check"),
}


READ_ONLY_CAPABILITY_PROFILES: dict[str, dict[str, Any]] = {
    "repo_status": {
        "profile_id": "repository_observation",
        "description": "Read repository status without changing repository state.",
        "side_effect_class": "NONE_EXPECTED",
        "repository_mutation_allowed": False,
        "risk": "LOW",
        "approval": "EXPLICIT_ENABLE_REQUIRED",
        "evidence": "STDOUT_STDERR_AND_AUDIT",
    },
    "repo_head": {
        "profile_id": "repository_observation",
        "description": "Read the current repository HEAD without changing repository state.",
        "side_effect_class": "NONE_EXPECTED",
        "repository_mutation_allowed": False,
        "risk": "LOW",
        "approval": "EXPLICIT_ENABLE_REQUIRED",
        "evidence": "STDOUT_STDERR_AND_AUDIT",
    },
    "repo_diff_check": {
        "profile_id": "repository_validation",
        "description": "Validate repository diff whitespace without changing repository state.",
        "side_effect_class": "NONE_EXPECTED",
        "repository_mutation_allowed": False,
        "risk": "LOW",
        "approval": "EXPLICIT_ENABLE_REQUIRED",
        "evidence": "STDOUT_STDERR_AND_AUDIT",
    },
}

class ProtectedTerminalError(RuntimeError):
    def __init__(
        self,
        reason: str,
        *,
        code: str = "PROTECTED_TERMINAL_DENIED",
        receipt_path: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason
        self.receipt_path = receipt_path

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "forprint_oc01_protected_terminal_denial_v0_1",
            "decision": "DENY",
            "code": self.code,
            "reason": self.reason,
            "receipt_path": self.receipt_path,
        }

def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtectedTerminalError(f"{label} must be a mapping")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProtectedTerminalError(f"{label} must be a non-empty string")
    return value.strip()


def _argv_sha256(argv: list[str]) -> str:
    return hashlib.sha256("\0".join(argv).encode("utf-8")).hexdigest()



def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_id(payload: Mapping[str, Any]) -> str:
    material = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return "oc01-terminal-event-" + hashlib.sha256(
        material.encode("utf-8")
    ).hexdigest()[:20]


def _ensure_outside_scope(scope: Path, path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(scope)
    except ValueError:
        return resolved
    raise ProtectedTerminalError(
        f"{label} must remain outside protected repository scope",
        code="EVIDENCE_SCOPE_VIOLATION",
    )


def _resolve_evidence_root(
    scope: Path,
    evidence_dir: Path | str | None,
) -> Path:
    root = (
        Path(evidence_dir).expanduser().resolve()
        if evidence_dir is not None
        else (
            Path(tempfile.gettempdir())
            / "forprint_operator_console"
            / "protected_terminal"
        ).resolve()
    )
    return _ensure_outside_scope(scope, root, "evidence_dir")


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                dict(payload),
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )


def _record_audit_event(
    evidence_root: Path,
    *,
    event_type: str,
    decision: str,
    code: str,
    reason: str,
    actor_type: str | None = None,
    actor_id: str | None = None,
    capability_id: str | None = None,
    cwd: str | None = None,
    command_id: str | None = None,
    details: Mapping[str, Any] | None = None,
    denial: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": "forprint_oc01_protected_terminal_audit_event_v0_1",
        "recorded_at": _utc_now(),
        "event_type": event_type,
        "decision": decision,
        "code": code,
        "reason": reason,
        "actor": {
            "actor_type": actor_type,
            "actor_id": actor_id,
        },
        "capability_id": capability_id,
        "cwd": cwd,
        "command_id": command_id,
        "authority_conferred": False,
        "details": dict(details or {}),
    }
    payload["event_id"] = _event_id(payload)
    history_path = evidence_root / "terminal_history_v0_1.jsonl"
    _append_jsonl(history_path, payload)
    if denial:
        _append_jsonl(
            evidence_root / "denial_receipts_v0_1.jsonl",
            payload,
        )
    return payload


def _raise_policy_denial(
    *,
    code: str,
    reason: str,
    evidence_root: Path | None = None,
    actor_type: str | None = None,
    actor_id: str | None = None,
    capability_id: str | None = None,
    cwd: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    receipt_path: str | None = None
    if evidence_root is not None:
        _record_audit_event(
            evidence_root,
            event_type="POLICY_DENIED",
            decision="DENY",
            code=code,
            reason=reason,
            actor_type=actor_type,
            actor_id=actor_id,
            capability_id=capability_id,
            cwd=cwd,
            details=details,
            denial=True,
        )
        receipt_path = str(evidence_root / "denial_receipts_v0_1.jsonl")
    raise ProtectedTerminalError(
        reason,
        code=code,
        receipt_path=receipt_path,
    )



def _sanitize_runtime_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    observation = _mapping(observation, "runtime observation")
    result: dict[str, Any] = {}

    integer_fields = (
        "pid",
        "stdout_bytes",
        "stderr_bytes",
        "stdout_growth_bytes",
        "stderr_growth_bytes",
    )
    numeric_fields = (
        "runtime_seconds",
        "no_progress_seconds",
        "stall_threshold_seconds",
    )
    boolean_fields = (
        "progress_observed",
        "stall_detected",
    )

    for field in integer_fields:
        value = observation.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[field] = value

    for field in numeric_fields:
        value = observation.get(field)
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value >= 0
        ):
            result[field] = value

    for field in boolean_fields:
        value = observation.get(field)
        if isinstance(value, bool):
            result[field] = value

    return result

def load_terminal_history(
    evidence_dir: Path | str,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit <= 0
        or limit > 1000
    ):
        raise ProtectedTerminalError(
            "history limit must be an integer between 1 and 1000",
            code="INVALID_HISTORY_LIMIT",
        )
    root = Path(evidence_dir).expanduser().resolve()
    path = root / "terminal_history_v0_1.jsonl"
    events: list[dict[str, Any]] = []
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ProtectedTerminalError(
                    "terminal history entry must be a mapping",
                    code="INVALID_HISTORY_RECORD",
                )
            events.append(value)
    selected = events[-limit:]
    return {
        "schema_version": "forprint_oc01_protected_terminal_history_v0_1",
        "history_path": str(path),
        "event_count": len(events),
        "returned_count": len(selected),
        "events": selected,
    }

def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ProtectedTerminalError(f"{label} missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProtectedTerminalError(f"{label} must be a mapping")
    return value


def _validate_session_projection(
    session_projection: Mapping[str, Any],
) -> tuple[str, str]:
    if session_projection.get("schema_version") != SESSION_PROJECTION_SCHEMA:
        raise ProtectedTerminalError("session projection schema mismatch")

    authority = _mapping(
        session_projection.get("authority"),
        "session projection authority",
    )
    if not authority or any(value is not False for value in authority.values()):
        raise ProtectedTerminalError(
            "session projection unexpectedly grants authority"
        )

    actor = _mapping(session_projection.get("actor"), "session projection actor")
    actor_type = _required_string(actor.get("actor_type"), "actor_type")
    actor_id = _required_string(actor.get("actor_id"), "actor_id")
    if actor_type not in TERMINAL_ACTOR_TYPES:
        raise ProtectedTerminalError(
            "Protected Terminal requires operator_assistant or human_terminal"
        )
    if actor.get("authority_conferred") is not False:
        raise ProtectedTerminalError("actor context widened authority")
    return actor_type, actor_id


def _validate_sensitive_elevation_approval(
    *,
    approval_decision_path: Path | str,
    capability_id: str,
    capability_class: str,
    scope: Path,
    actor_type: str,
    actor_id: str,
    session_projection: Mapping[str, Any],
) -> dict[str, Any]:
    approval_path = Path(
        approval_decision_path
    ).expanduser().resolve()

    approval = _load_yaml(
        approval_path,
        "sensitive elevation approval",
    )

    def deny(
        code: str,
        reason: str,
    ) -> None:
        raise ProtectedTerminalError(
            reason,
            code=code,
        )

    if (
        approval.get("schema_version")
        != "forprint_operator_approval_decision_v0_1"
    ):
        deny(
            "APPROVAL_SCHEMA_MISMATCH",
            "sensitive elevation approval schema mismatch",
        )

    if approval.get("decision") != "APPROVE":
        deny(
            "APPROVAL_DECISION_MISMATCH",
            "sensitive elevation approval decision must be APPROVE",
        )

    if (
        approval.get("approval_purpose")
        != "SENSITIVE_CAPABILITY_ELEVATION"
    ):
        deny(
            "APPROVAL_PURPOSE_MISMATCH",
            "sensitive elevation approval purpose mismatch",
        )

    if (
        approval.get("requested_authority_delta")
        != "BOUNDED_SENSITIVE_EVIDENCE_ONLY"
    ):
        deny(
            "APPROVAL_AUTHORITY_DELTA_MISMATCH",
            "sensitive elevation authority delta mismatch",
        )

    if approval.get("capability_id") != capability_id:
        deny(
            "APPROVAL_CAPABILITY_MISMATCH",
            "sensitive elevation capability_id mismatch",
        )

    if approval.get("capability_class") != capability_class:
        deny(
            "APPROVAL_CAPABILITY_CLASS_MISMATCH",
            "sensitive elevation capability_class mismatch",
        )

    approval_scope_raw = approval.get(
        "repository_scope"
    )

    if (
        not isinstance(approval_scope_raw, str)
        or not approval_scope_raw.strip()
    ):
        deny(
            "APPROVAL_REPOSITORY_SCOPE_MISMATCH",
            "sensitive elevation repository scope is missing",
        )

    approval_scope = Path(
        approval_scope_raw
    ).expanduser().resolve()

    if approval_scope != scope:
        deny(
            "APPROVAL_REPOSITORY_SCOPE_MISMATCH",
            "sensitive elevation repository scope mismatch",
        )

    if (
        approval.get("actor_type") != actor_type
        or approval.get("actor_id") != actor_id
    ):
        deny(
            "APPROVAL_ACTOR_MISMATCH",
            "sensitive elevation actor binding mismatch",
        )

    execution_identity = _mapping(
        session_projection.get("execution_identity"),
        "session projection execution identity",
    )

    attempt_id = _required_string(
        execution_identity.get("attempt_id"),
        "execution_identity.attempt_id",
    )

    if (
        approval.get("session_or_execution_binding")
        != attempt_id
    ):
        deny(
            "APPROVAL_EXECUTION_BINDING_MISMATCH",
            "sensitive elevation execution binding mismatch",
        )

    expires_raw = approval.get("expires_at")

    try:
        expires_at = datetime.fromisoformat(
            str(expires_raw)
        )

        if expires_at.tzinfo is None:
            raise ValueError(
                "approval expiry must be timezone-aware"
            )

    except Exception:
        deny(
            "APPROVAL_EXPIRED",
            "sensitive elevation approval expiry is invalid",
        )

    if (
        datetime.now(timezone.utc)
        >= expires_at.astimezone(timezone.utc)
    ):
        deny(
            "APPROVAL_EXPIRED",
            "sensitive elevation approval has expired",
        )

    authority = _mapping(
        approval.get("authority"),
        "sensitive elevation approval authority",
    )

    if (
        authority.get("human_operator_decision")
        is not True
    ):
        deny(
            "APPROVAL_AUTHORITY_WIDENING",
            "sensitive elevation approval lacks human decision evidence",
        )

    if (
        authority.get(
            "sensitive_elevation_evidence_only"
        )
        is not True
    ):
        deny(
            "APPROVAL_AUTHORITY_WIDENING",
            "sensitive elevation approval is not evidence-only",
        )

    required_false = (
        "eligible_as_future_worker_dispatch_authority",
        "direct_worker_dispatch_allowed_by_gateway",
        "blueprint_accept",
        "prompt_claim",
        "next_prompt_release",
        "sensitive_elevation_grants_authority",
        "exclusive_module_lease",
        "safe_write",
        "commit_push_merge_release_promotion",
    )

    widened = [
        key
        for key in required_false
        if authority.get(key) is not False
    ]

    if widened:
        deny(
            "APPROVAL_AUTHORITY_WIDENING",
            "sensitive elevation approval attempts authority widening: "
            + ",".join(sorted(widened)),
        )

    decision_id = _required_string(
        approval.get("decision_id"),
        "approval decision_id",
    )

    return {
        "evidence_consumed": True,
        "decision_id": decision_id,
        "approval_purpose": (
            "SENSITIVE_CAPABILITY_ELEVATION"
        ),
        "capability_id": capability_id,
        "capability_class": capability_class,
        "repository_scope": str(scope),
        "actor_type": actor_type,
        "actor_id": actor_id,
        "session_or_execution_binding": attempt_id,
        "requested_authority_delta": (
            "BOUNDED_SENSITIVE_EVIDENCE_ONLY"
        ),
        "expires_at": expires_at.astimezone(
            timezone.utc
        ).isoformat(),
        "authority_conferred": False,
        "lease_conferred": False,
        "safe_write_conferred": False,
        "promotion_authority_conferred": False,
        "source_path": str(approval_path),
    }


def _validate_git_scope(cwd: Path | str) -> Path:
    scope = Path(cwd).expanduser().resolve()
    if not scope.is_dir():
        raise ProtectedTerminalError("cwd must be an existing directory")
    result = subprocess.run(
        ["git", "-C", str(scope), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ProtectedTerminalError("cwd must be inside a Git repository")
    top = Path(result.stdout.strip()).resolve()
    if top != scope:
        raise ProtectedTerminalError(
            "Protected Terminal v0.1 requires exact Git repository root scope"
        )
    return scope



def list_capabilities() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "default_enabled": False,
        "command_representation": COMMAND_REPRESENTATION,
        "arbitrary_command_text_allowed": False,
        "shell": False,
        "policy": {
            "mode": "REGISTERED_CAPABILITY_ONLY",
            "default_decision": "DENY",
            "explicit_enable_required": True,
            "authority_widening_allowed": False,
        },
        "capabilities": [
            {
                "capability_id": capability_id,
                "class": "READ_ONLY",
                "execution_state": "AVAILABLE_WHEN_EXPLICITLY_ENABLED",
                "profile": dict(READ_ONLY_CAPABILITY_PROFILES[capability_id]),
                "policy": {
                    "decision": "ALLOW_WHEN_EXPLICITLY_ENABLED",
                    "code": "REGISTERED_READ_ONLY_CAPABILITY",
                },
            }
            for capability_id in sorted(READ_ONLY_CAPABILITIES)
        ],
        "safe_write": {
            "class": "SAFE_WRITE",
            "execution_state": "BLOCKED",
            "blocker": "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
            "policy": {
                "decision": "DENY",
                "code": "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
            },
        },
        "cancel": {
            "state": CANCEL_STATE,
            "implemented_by_oc01": False,
        },
        "audit": {
            "mode": "APPEND_ONLY",
            "storage": "OUTSIDE_PROTECTED_REPOSITORY_SCOPE",
            "history_filename": "terminal_history_v0_1.jsonl",
            "denial_receipts_filename": "denial_receipts_v0_1.jsonl",
        },
    }


def build_terminal_plan(
    *,
    capability_id: str,
    cwd: Path | str,
    session_projection: Mapping[str, Any],
    enabled: bool = False,
    capability_class: str = "READ_ONLY",
    timeout_seconds: int = 30,
    evidence_dir: Path | str | None = None,
    observe_runtime: bool = False,
    heartbeat_seconds: int = 15,
    stall_threshold_seconds: float | None = None,
    approval_decision_path: Path | str | None = None,
) -> dict[str, Any]:
    if enabled is not True:
        raise ProtectedTerminalError(
            "Protected Terminal is default-off; explicit enable is required",
            code="EXPLICIT_ENABLE_REQUIRED",
        )

    actor_type, actor_id = _validate_session_projection(session_projection)

    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
        or timeout_seconds > 300
    ):
        raise ProtectedTerminalError(
            "timeout_seconds must be an integer between 1 and 300",
            code="INVALID_TIMEOUT",
        )


    if not isinstance(observe_runtime, bool):
        raise ProtectedTerminalError(
            "observe_runtime must be boolean",
            code="INVALID_RUNTIME_OBSERVATION_FLAG",
        )
    if not observe_runtime and (
        heartbeat_seconds != 15 or stall_threshold_seconds is not None
    ):
        raise ProtectedTerminalError(
            "runtime observation configuration requires observe_runtime",
            code="RUNTIME_OBSERVATION_NOT_ENABLED",
        )
    if observe_runtime:
        if (
            not isinstance(heartbeat_seconds, int)
            or isinstance(heartbeat_seconds, bool)
            or heartbeat_seconds <= 0
        ):
            raise ProtectedTerminalError(
                "heartbeat_seconds must be a positive integer",
                code="INVALID_HEARTBEAT_SECONDS",
            )
        if (
            stall_threshold_seconds is not None
            and (
                not isinstance(stall_threshold_seconds, (int, float))
                or isinstance(stall_threshold_seconds, bool)
                or stall_threshold_seconds <= 0
            )
        ):
            raise ProtectedTerminalError(
                "stall_threshold_seconds must be positive when set",
                code="INVALID_STALL_THRESHOLD",
            )

    scope = _validate_git_scope(cwd)
    evidence_root = _resolve_evidence_root(scope, evidence_dir)

    capability_id = _required_string(capability_id, "capability_id")
    if capability_class == "SAFE_WRITE":
        _raise_policy_denial(
            code="EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
            reason="SAFE_WRITE blocked: EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
            evidence_root=evidence_root,
            actor_type=actor_type,
            actor_id=actor_id,
            capability_id=capability_id,
            cwd=str(scope),
            details={
                "capability_class": "SAFE_WRITE",
                "safe_write_execution_allowed": False,
            },
        )
    if capability_class != "READ_ONLY":
        _raise_policy_denial(
            code="UNSUPPORTED_CAPABILITY_CLASS",
            reason="unsupported capability class",
            evidence_root=evidence_root,
            actor_type=actor_type,
            actor_id=actor_id,
            capability_id=capability_id,
            cwd=str(scope),
            details={"capability_class": capability_class},
        )

    args = READ_ONLY_CAPABILITIES.get(capability_id)
    if args is None:
        _raise_policy_denial(
            code="UNKNOWN_CAPABILITY",
            reason="unknown Protected Terminal capability",
            evidence_root=evidence_root,
            actor_type=actor_type,
            actor_id=actor_id,
            capability_id=capability_id,
            cwd=str(scope),
        )

    sensitive_elevation: dict[str, Any] | None = None

    if approval_decision_path is not None:
        sensitive_elevation = (
            _validate_sensitive_elevation_approval(
                approval_decision_path=approval_decision_path,
                capability_id=capability_id,
                capability_class=capability_class,
                scope=scope,
                actor_type=actor_type,
                actor_id=actor_id,
                session_projection=session_projection,
            )
        )

    git_executable = shutil.which("git")
    if not git_executable:
        raise ProtectedTerminalError(
            "git executable is unavailable",
            code="GIT_EXECUTABLE_UNAVAILABLE",
        )
    argv = [str(Path(git_executable).resolve()), "--no-optional-locks", *args]

    command_id_material = {
        "capability_id": capability_id,
        "cwd": str(scope),
        "actor_type": actor_type,
        "actor_id": actor_id,
        "argv_sha256": _argv_sha256(argv),
    }

    if sensitive_elevation is not None:
        command_id_material[
            "sensitive_elevation_decision_id"
        ] = sensitive_elevation["decision_id"]
    command_id = "oc01-terminal-" + hashlib.sha256(
        json.dumps(
            command_id_material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:16]

    command_dir = evidence_root / command_id
    profile = dict(READ_ONLY_CAPABILITY_PROFILES[capability_id])
    plan = {
        "schema_version": SCHEMA_VERSION,
        "command_id": command_id,
        "enabled": True,
        "capability": {
            "capability_id": capability_id,
            "class": "READ_ONLY",
            "exact_scope": str(scope),
            "profile": profile,
        },
        "policy": {
            "decision": "ALLOW",
            "code": "REGISTERED_READ_ONLY_CAPABILITY",
            "default_policy": "DENY",
            "explicit_enable_confirmed": True,
            "authority_conferred": False,
        },
        "actor": {
            "actor_type": actor_type,
            "actor_id": actor_id,
            "source": "OC01_MINI_1_SESSION_PROJECTION",
            "authority_conferred": False,
        },
        "execution": {
            "command_representation": COMMAND_REPRESENTATION,
            "argv": argv,
            "argv_sha256": _argv_sha256(argv),
            "cwd": str(scope),
            "shell": False,
            "timeout_seconds": timeout_seconds,
            "stdout_path": str(command_dir / "stdout.log"),
            "stderr_path": str(command_dir / "stderr.log"),
        },
        "runtime_observation": {
            "enabled": observe_runtime,
            "mode": "BOUNDED_RUNTIME_PROGRESS_EVIDENCE",
            "source": "SHARED_LAUNCHER_HEARTBEAT",
            "heartbeat_seconds": heartbeat_seconds if observe_runtime else None,
            "stall_threshold_seconds": (
                stall_threshold_seconds if observe_runtime else None
            ),
            "byte_streaming": False,
            "stdout_content_retained_in_history": False,
            "stderr_content_retained_in_history": False,
            "authority_conferred": False,
        },
        "audit": {
            "mode": "APPEND_ONLY",
            "storage": "OUTSIDE_PROTECTED_REPOSITORY_SCOPE",
            "history_path": str(evidence_root / "terminal_history_v0_1.jsonl"),
            "denial_receipts_path": str(
                evidence_root / "denial_receipts_v0_1.jsonl"
            ),
        },
        "authority": {
            "gateway_grants_execution_authority": False,
            "gateway_grants_dispatch_authority": False,
            "gateway_grants_lease_authority": False,
            "gateway_grants_canonical_write_authority": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
        },
        "cancel": {
            "state": CANCEL_STATE,
            "available": False,
        },
    }
    if sensitive_elevation is not None:
        plan["sensitive_elevation"] = (
            sensitive_elevation
        )

    _record_audit_event(
        evidence_root,
        event_type="PLAN_ALLOWED",
        decision="ALLOW",
        code="REGISTERED_READ_ONLY_CAPABILITY",
        reason="registered read-only capability plan created",
        actor_type=actor_type,
        actor_id=actor_id,
        capability_id=capability_id,
        cwd=str(scope),
        command_id=command_id,
        details={
            "profile_id": profile["profile_id"],
            "argv_sha256": _argv_sha256(argv),
            "runtime_observation_enabled": observe_runtime,
            "sensitive_elevation_evidence_consumed": (
                sensitive_elevation is not None
            ),
            "sensitive_elevation_decision_id": (
                sensitive_elevation["decision_id"]
                if sensitive_elevation is not None
                else None
            ),
            "sensitive_elevation_authority_conferred": False,
        },
    )
    return plan


def execute_terminal_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    plan = _mapping(plan, "terminal plan")
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ProtectedTerminalError("terminal plan schema mismatch")
    if plan.get("enabled") is not True:
        raise ProtectedTerminalError("terminal plan is not enabled")

    actor = _mapping(plan.get("actor"), "actor")
    actor_type = _required_string(actor.get("actor_type"), "actor_type")
    actor_id = _required_string(actor.get("actor_id"), "actor_id")
    if actor_type not in TERMINAL_ACTOR_TYPES:
        raise ProtectedTerminalError(
            "terminal plan actor type is not allowed"
        )
    if actor.get("source") != "OC01_MINI_1_SESSION_PROJECTION":
        raise ProtectedTerminalError("terminal plan actor source drift")
    if actor.get("authority_conferred") is not False:
        raise ProtectedTerminalError("terminal plan actor widened authority")

    capability = _mapping(plan.get("capability"), "capability")
    if capability.get("class") != "READ_ONLY":
        raise ProtectedTerminalError("only READ_ONLY execution is enabled")
    capability_id = _required_string(
        capability.get("capability_id"),
        "capability_id",
    )
    if capability_id not in READ_ONLY_CAPABILITIES:
        raise ProtectedTerminalError("unknown capability in terminal plan")

    authority = _mapping(plan.get("authority"), "authority")
    if not authority or any(value is not False for value in authority.values()):
        raise ProtectedTerminalError("terminal plan authority widened")

    exact_scope = Path(
        _required_string(capability.get("exact_scope"), "exact_scope")
    ).expanduser().resolve()

    execution = _mapping(plan.get("execution"), "execution")
    execution_cwd = _validate_git_scope(
        _required_string(execution.get("cwd"), "cwd")
    )
    if execution_cwd != exact_scope:
        raise ProtectedTerminalError(
            "terminal execution cwd / exact scope drift"
        )
    if execution.get("command_representation") != COMMAND_REPRESENTATION:
        raise ProtectedTerminalError("command representation drift")
    if execution.get("shell") is not False:
        raise ProtectedTerminalError("shell execution is forbidden")

    argv = execution.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(item, str) and item for item in argv)
    ):
        raise ProtectedTerminalError("terminal argv invalid")

    expected_args = READ_ONLY_CAPABILITIES[capability_id]
    git_executable = shutil.which("git")
    if not git_executable:
        raise ProtectedTerminalError("git executable is unavailable")
    expected_argv = [str(Path(git_executable).resolve()), "--no-optional-locks", *expected_args]
    if argv != expected_argv:
        raise ProtectedTerminalError(
            "terminal argv does not match registered capability"
        )
    if execution.get("argv_sha256") != _argv_sha256(argv):
        raise ProtectedTerminalError("terminal argv digest mismatch")

    stdout_path = _ensure_outside_scope(
        execution_cwd,
        Path(_required_string(execution.get("stdout_path"), "stdout_path")),
        "stdout_path",
    )
    stderr_path = _ensure_outside_scope(
        execution_cwd,
        Path(_required_string(execution.get("stderr_path"), "stderr_path")),
        "stderr_path",
    )

    audit = _mapping(plan.get("audit"), "audit")
    if audit.get("mode") != "APPEND_ONLY":
        raise ProtectedTerminalError("terminal audit mode drift")
    if audit.get("storage") != "OUTSIDE_PROTECTED_REPOSITORY_SCOPE":
        raise ProtectedTerminalError("terminal audit storage drift")
    history_path = _ensure_outside_scope(
        execution_cwd,
        Path(_required_string(audit.get("history_path"), "history_path")),
        "history_path",
    )
    denial_receipts_path = _ensure_outside_scope(
        execution_cwd,
        Path(
            _required_string(
                audit.get("denial_receipts_path"),
                "denial_receipts_path",
            )
        ),
        "denial_receipts_path",
    )
    if history_path.parent != denial_receipts_path.parent:
        raise ProtectedTerminalError("terminal audit root drift")
    evidence_root = history_path.parent

    runtime_observation_value = plan.get("runtime_observation")
    if runtime_observation_value is None:
        runtime_observation = {
            "enabled": False,
            "mode": "BOUNDED_RUNTIME_PROGRESS_EVIDENCE",
            "source": "SHARED_LAUNCHER_HEARTBEAT",
            "heartbeat_seconds": None,
            "stall_threshold_seconds": None,
            "byte_streaming": False,
            "stdout_content_retained_in_history": False,
            "stderr_content_retained_in_history": False,
            "authority_conferred": False,
        }
    else:
        runtime_observation = _mapping(
            runtime_observation_value,
            "runtime_observation",
        )

    observation_enabled = runtime_observation.get("enabled") is True
    if runtime_observation.get("enabled") not in {True, False}:
        raise ProtectedTerminalError("runtime observation enabled flag drift")
    if runtime_observation.get("mode") != "BOUNDED_RUNTIME_PROGRESS_EVIDENCE":
        raise ProtectedTerminalError("runtime observation mode drift")
    if runtime_observation.get("source") != "SHARED_LAUNCHER_HEARTBEAT":
        raise ProtectedTerminalError("runtime observation source drift")
    if runtime_observation.get("byte_streaming") is not False:
        raise ProtectedTerminalError("byte streaming is forbidden")
    if runtime_observation.get("stdout_content_retained_in_history") is not False:
        raise ProtectedTerminalError("stdout content retention is forbidden")
    if runtime_observation.get("stderr_content_retained_in_history") is not False:
        raise ProtectedTerminalError("stderr content retention is forbidden")
    if runtime_observation.get("authority_conferred") is not False:
        raise ProtectedTerminalError("runtime observation widened authority")

    observation_heartbeat_seconds = runtime_observation.get("heartbeat_seconds")
    observation_stall_threshold = runtime_observation.get(
        "stall_threshold_seconds"
    )
    if observation_enabled:
        if (
            not isinstance(observation_heartbeat_seconds, int)
            or isinstance(observation_heartbeat_seconds, bool)
            or observation_heartbeat_seconds <= 0
        ):
            raise ProtectedTerminalError(
                "runtime observation heartbeat_seconds drift"
            )
        if (
            observation_stall_threshold is not None
            and (
                not isinstance(observation_stall_threshold, (int, float))
                or isinstance(observation_stall_threshold, bool)
                or observation_stall_threshold <= 0
            )
        ):
            raise ProtectedTerminalError(
                "runtime observation stall_threshold_seconds drift"
            )
    else:
        if observation_heartbeat_seconds is not None:
            raise ProtectedTerminalError(
                "disabled runtime observation heartbeat_seconds drift"
            )
        if observation_stall_threshold is not None:
            raise ProtectedTerminalError(
                "disabled runtime observation stall threshold drift"
            )

    command_id = _required_string(plan.get("command_id"), "command_id")
    _record_audit_event(
        evidence_root,
        event_type="EXECUTION_STARTED",
        decision="ALLOW",
        code="REGISTERED_READ_ONLY_CAPABILITY",
        reason="registered read-only capability execution started",
        actor_type=actor_type,
        actor_id=actor_id,
        capability_id=capability_id,
        cwd=str(execution_cwd),
        command_id=command_id,
        details={"argv_sha256": execution.get("argv_sha256")},
    )

    observation_event_count = 0
    observation_callback_errors: list[dict[str, str]] = []

    def _on_runtime_observation(payload: dict[str, Any]) -> None:
        nonlocal observation_event_count
        try:
            details = _sanitize_runtime_observation(payload)
            _record_audit_event(
                evidence_root,
                event_type="RUNTIME_OBSERVATION",
                decision="OBSERVE",
                code="BOUNDED_RUNTIME_PROGRESS_EVIDENCE",
                reason="shared launcher runtime progress observation",
                actor_type=actor_type,
                actor_id=actor_id,
                capability_id=capability_id,
                cwd=str(execution_cwd),
                command_id=command_id,
                details=details,
            )
            observation_event_count += 1
        except Exception as exc:
            observation_callback_errors.append(
                {
                    "error_type": type(exc).__name__,
                    "message": str(exc)[:200],
                }
            )

    launch_kwargs: dict[str, Any] = {
        "argv": list(argv),
        "cwd": str(execution_cwd),
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "timeout_seconds": execution.get("timeout_seconds"),
    }
    if observation_enabled:
        launch_kwargs.update(
            {
                "on_heartbeat": _on_runtime_observation,
                "heartbeat_seconds": observation_heartbeat_seconds,
                "stall_threshold_seconds": observation_stall_threshold,
            }
        )

    result = launch_process(**launch_kwargs)

    terminal_result = {
        "schema_version": "forprint_oc01_protected_terminal_result_v0_1",
        "command_id": command_id,
        "capability_id": capability_id,
        "actor": plan.get("actor"),
        "cwd": execution.get("cwd"),
        "argv_sha256": execution.get("argv_sha256"),
        "stdout_path": result.get("stdout_path"),
        "stderr_path": result.get("stderr_path"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "return_code": result.get("return_code"),
        "timed_out": result.get("timed_out"),
        "outcome": result.get("outcome"),
        "shell": result.get("shell"),
        "audit": {
            "history_path": str(history_path),
            "mode": "APPEND_ONLY",
        },
        "runtime_observation": {
            "enabled": observation_enabled,
            "mode": "BOUNDED_RUNTIME_PROGRESS_EVIDENCE",
            "source": "SHARED_LAUNCHER_HEARTBEAT",
            "history_event_count": observation_event_count,
            "callback_error_count": len(observation_callback_errors),
            "callback_errors": observation_callback_errors,
            "stall_detected": (
                bool(result.get("stall_detected"))
                if observation_enabled
                else False
            ),
            "timed_out": (
                bool(result.get("timed_out"))
                if observation_enabled
                else False
            ),
            "byte_streaming": False,
            "stdout_content_retained_in_history": False,
            "stderr_content_retained_in_history": False,
            "authority_conferred": False,
        },
        "cancel": {
            "state": CANCEL_STATE,
            "available": False,
            "cancelled": False,
        },
        "authority": {
            "gateway_granted_authority": False,
            "canonical_write_performed": False,
            "commit_performed": False,
            "push_performed": False,
            "merge_performed": False,
            "release_performed": False,
            "promotion_performed": False,
        },
    }
    _record_audit_event(
        evidence_root,
        event_type="EXECUTION_FINISHED",
        decision="ALLOW",
        code="REGISTERED_READ_ONLY_CAPABILITY",
        reason="registered read-only capability execution finished",
        actor_type=actor_type,
        actor_id=actor_id,
        capability_id=capability_id,
        cwd=str(execution_cwd),
        command_id=command_id,
        details={
            "return_code": result.get("return_code"),
            "timed_out": result.get("timed_out"),
            "outcome": result.get("outcome"),
            "stdout_path": result.get("stdout_path"),
            "stderr_path": result.get("stderr_path"),
            "runtime_observation_enabled": observation_enabled,
            "runtime_observation_event_count": observation_event_count,
            "runtime_observation_callback_error_count": len(
                observation_callback_errors
            ),
            "stall_detected": (
                bool(result.get("stall_detected"))
                if observation_enabled
                else False
            ),
        },
    )
    return terminal_result

def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 capability-shaped Protected Terminal gateway"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")

    history = sub.add_parser("history")
    history.add_argument("--evidence-dir", required=True)
    history.add_argument("--limit", type=int, default=50)

    for name in ("plan", "run"):
        p = sub.add_parser(name)
        p.add_argument("--capability", required=True)
        p.add_argument("--cwd", required=True)
        p.add_argument("--session-projection", required=True)
        p.add_argument("--timeout-seconds", type=int, default=30)
        p.add_argument("--evidence-dir")
        p.add_argument("--confirm-enable", action="store_true")
        p.add_argument("--observe-runtime", action="store_true")
        p.add_argument("--heartbeat-seconds", type=int, default=15)
        p.add_argument("--stall-threshold-seconds", type=float)
        p.add_argument("--approval-decision")

    args = parser.parse_args()

    if args.command == "capabilities":
        print(
            yaml.safe_dump(
                list_capabilities(),
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
        return 0

    if args.command == "history":
        print(
            yaml.safe_dump(
                load_terminal_history(
                    Path(args.evidence_dir),
                    limit=args.limit,
                ),
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
        return 0

    plan = build_terminal_plan(
        capability_id=args.capability,
        cwd=Path(args.cwd),
        session_projection=_load_yaml(
            Path(args.session_projection),
            "session projection",
        ),
        enabled=args.confirm_enable,
        timeout_seconds=args.timeout_seconds,
        evidence_dir=Path(args.evidence_dir) if args.evidence_dir else None,
        observe_runtime=args.observe_runtime,
        heartbeat_seconds=args.heartbeat_seconds,
        stall_threshold_seconds=args.stall_threshold_seconds,
        approval_decision_path=(
            Path(args.approval_decision)
            if args.approval_decision
            else None
        ),
    )

    if args.command == "plan":
        print(
            yaml.safe_dump(
                plan,
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
        return 0

    result = execute_terminal_plan(plan)
    print(
        yaml.safe_dump(
            result,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip()
    )
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ProtectedTerminalError as exc:
        print(
            yaml.safe_dump(
                exc.as_dict(),
                sort_keys=False,
                allow_unicode=True,
                width=112,
            ).rstrip()
        )
        raise SystemExit(2)
