"""CF10 R079: pure provider-neutral adapter selection contract / source audit.

This is NOT a launch adapter, admission check, authority, release, or registry
mutation.  Live Copilot R078 is deliberately unchanged.  A future source-reviewed
migration must wire this pure selection boundary into prepare, ACK, dispatch,
invocation, result normalization and independent finalization together.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Protocol, runtime_checkable

SCHEMA = "cf10_provider_neutral_selection_candidate_v0_1"
AUDIT_SCHEMA = "cf10_r079_source_architecture_review_v0_1"
REGISTRY_SCHEMA = "forprint_worker_runtime_adapter_registry_v0_1"
ID_RE = re.compile(r"[a-z][a-z0-9_\-]{2,79}\Z")
ATT_RE = re.compile(r"cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z")
HEX40_RE = re.compile(r"[a-f0-9]{40}\Z")
TRANSPORTS = frozenset(("CONSOLE_COMMAND", "REMOTE_JOB"))
STATES = frozenset(("READY", "NOT_CONFIGURED", "BLOCKED", "DISABLED"))
CAPABILITIES = frozenset((
    "non_interactive_prompt", "workspace_read", "workspace_write",
    "command_execution", "model_selectable", "network_required",
    "completion_capture", "mcp_tools", "structured_result",
    "remote_execution",
))

class ProviderBoundaryBlocked(ValueError):
    pass


def _deny(code: str) -> None:
    raise ProviderBoundaryBlocked("CF10_R079_" + code)


def _id(value: object, label: str) -> str:
    if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
        _deny("INVALID_" + label)
    return value


def _bool_false_authority(value: object) -> bool:
    return isinstance(value, Mapping) and bool(value) and all(v is False for v in value.values())


def validate_registry_for_future(catalog: Mapping) -> tuple[dict, ...]:
    """Pure future multi-READY validator; does not replace the live registry.

    Provider readiness does not grant execution or task routing authority.
    It validates both the existing CLI descriptors and future remote descriptors,
    but NEVER creates an executable invocation or accepts unknown providers.
    """
    if not isinstance(catalog, Mapping) or catalog.get("schema_version") != REGISTRY_SCHEMA:
        _deny("REGISTRY_SCHEMA")
    worker = catalog.get("worker_identity")
    iface = catalog.get("adapter_interface")
    if (not isinstance(worker, Mapping) or worker.get("provider_neutral") is not True
        or worker.get("provider_selected_per_attempt") is not True
        or not isinstance(iface, Mapping)
        or iface.get("architectural_authority") is not False
        or iface.get("shell_execution_allowed") is not False):
        _deny("REGISTRY_NEUTRALITY")
    rows = catalog.get("providers")
    if not isinstance(rows, list) or not rows:
        _deny("REGISTRY_EMPTY")
    seen = set()
    accepted = []
    for row in rows:
        if not isinstance(row, Mapping):
            _deny("PROVIDER_OBJECT")
        pid = _id(row.get("provider_id"), "PROVIDER_ID")
        if pid in seen:
            _deny("DUPLICATE_PROVIDER")
        seen.add(pid)
        if not _bool_false_authority(row.get("authority")):
            _deny("PROVIDER_AUTHORITY_NOT_FALSE")
        state = row.get("state")
        if not isinstance(state, str) or state not in STATES or type(row.get("ready")) is not bool:
            _deny("PROVIDER_STATE")
        if state == "READY":
            if row["ready"] is not True:
                _deny("READY_FALSE")
            transport = row.get("adapter_type")
            if transport not in TRANSPORTS:
                _deny("EXECUTION_KIND_NOT_SUPPORTED")
            caps = row.get("capabilities")
            if not isinstance(caps, Mapping) or not caps:
                _deny("READY_CAPABILITIES_REQUIRED")
            if set(caps) - CAPABILITIES or any(
                type(v) is not bool and v != "launch_policy_bound" for v in caps.values()
            ):
                _deny("CAPABILITIES_INVALID")
            if transport == "CONSOLE_COMMAND":
                exe = row.get("executable")
                if (not isinstance(exe, str) or not exe.startswith("/")
                    or ".." in Path(exe).parts or "\x00" in exe or "\n" in exe
                    or row.get("command_representation") != "ARGV_NO_SHELL"):
                    _deny("CLI_EXECUTABLE_BOUNDARY")
            else:
                # Remote jobs cannot be expressed as an arbitrary local binary.
                if row.get("executable") is not None:
                    _deny("REMOTE_JOB_MUST_NOT_IMPERSONATE_LOCAL_CLI")
                if row.get("command_representation") != "REMOTE_JOB_REFERENCE":
                    _deny("REMOTE_JOB_REFERENCE_REQUIRED")
                remote_ref = row.get("remote_runtime_ref")
                if not isinstance(remote_ref, str) or re.fullmatch(r"[a-z][a-z0-9:._-]{5,160}", remote_ref) is None:
                    _deny("REMOTE_JOB_RUNTIME_REF_REQUIRED")
            runtime_id = row.get("runtime_id")
            _id(runtime_id, "RUNTIME_ID")
            auth = row.get("auth")
            if (not isinstance(auth, Mapping)
                or auth.get("material_source") != "outside_git"
                or auth.get("value_serialized") is not False):
                _deny("AUTH_MATERIAL_BOUNDARY")
            for key, value in auth.items():
                if str(key).lower() in ("api_key", "password", "token", "access_token", "refresh_token", "secret", "credential", "credentials") and value not in (None, False, "", "outside_git"):
                    _deny("AUTH_SECRET_VALUE_IN_REGISTRY")
            accepted.append(dict(row))
        else:
            if row["ready"] is not False:
                _deny("UNAVAILABLE_READY")
            if state == "NOT_CONFIGURED" and any(
                row.get(key) is not None for key in
                ("executable", "model_selection", "auth", "capabilities")
            ):
                _deny("UNCONFIGURED_PROVIDER_HAS_EXECUTION_BINDING")
    return tuple(accepted)


def select_candidate(*, catalog: Mapping, request: Mapping) -> dict:
    """Pure explicit provider choice, *never* a dispatch or permission grant."""
    ready = validate_registry_for_future(catalog)
    if not isinstance(request, Mapping):
        _deny("TASK_REQUEST")
    attempt = request.get("attempt_id")
    head = request.get("source_head")
    if not isinstance(attempt, str) or ATT_RE.fullmatch(attempt) is None:
        _deny("ATTEMPT")
    if not isinstance(head, str) or HEX40_RE.fullmatch(head) is None:
        _deny("HEAD")
    worker_id = _id(request.get("worker_id"), "WORKER_ID")
    task = _id(request.get("task_id"), "TASK_ID")
    front = _id(request.get("work_front_id"), "WORK_FRONT_ID")
    pid = _id(request.get("provider_id"), "EXPLICIT_PROVIDER_ID_REQUIRED")
    model = request.get("model_id")
    if (not isinstance(model, str) or not model or len(model) > 128
        or any(ch in model for ch in ("\x00", "\n", "\r"))):
        _deny("MODEL_REQUIRED")
    needed = request.get("capabilities_required")
    if (not isinstance(needed, list) or len(needed) > len(CAPABILITIES)
        or any(c not in CAPABILITIES for c in needed)
        or len(needed) != len(set(needed))):
        _deny("CAPABILITIES_REQUIRED_INVALID")
    provider = next((p for p in ready if p["provider_id"] == pid), None)
    if provider is None:
        _deny("PROVIDER_NOT_READY_NO_FALLBACK")
    selected = provider.get("model_selection")
    if not isinstance(selected, Mapping):
        _deny("MODEL_SELECTION_UNAVAILABLE")
    if selected.get("mode") != "runtime_selectable" and model != selected.get("default"):
        _deny("MODEL_NOT_SUPPORTED_BY_DECLARED_SELECTION")
    for c in needed:
        # launch_policy_bound is a conditional declaration, NOT readiness.
        if provider["capabilities"].get(c) is not True:
            _deny("CAPABILITY_NOT_UNCONDITIONALLY_AVAILABLE:" + c)
    obj = {
        "schema_version": SCHEMA,
        "attempt_id": attempt, "source_head": head,
        "worker_id": worker_id, "task_id": task, "work_front_id": front,
        "provider_id": pid, "runtime_id": provider["runtime_id"],
        "model_id": model, "adapter_type": provider["adapter_type"],
        "capabilities_required": sorted(needed),
        "provider_ready_declared": True,
        "operator_authority_granted": False,
        "dispatch_authorized": False,
        "worker_launched": False,
        "owner_claim_consumed": False,
        "automatic_fallback": False,
        "automatic_retry": False,
        "result_accepted": False,
    }
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    obj["selection_candidate_sha256"] = hashlib.sha256(raw).hexdigest()
    return obj


@runtime_checkable
class WorkerProviderAdapter(Protocol):
    """Future plugin ABI; implementing it must not bypass host authority."""

    def inspect_readiness(self, binding: Mapping) -> Mapping: ...
    def build_invocation(self, binding: Mapping, frozen_task: Mapping) -> Mapping: ...
    def normalize_result_candidate(self, provider_stream: bytes, binding: Mapping) -> Mapping: ...


COUPLING_CHECKS = (
    ("registry_single_ready", "scripts/coordination/control_plane/worker_runtime/registry.py", "if ready_count != 1:"),
    ("training_copilot_pin", "scripts/coordination/control_plane/cf10_training_dispatch.py", 'runtime_provider != "github_copilot_cli"'),
    ("cycle_copilot_pin", "scripts/coordination/control_plane/governed_worker_cycle.py", 'runtime_provider="github_copilot_cli"'),
    ("invocation_copilot_pin", "scripts/coordination/control_plane/worker_runtime/invocation_adapter.py", 'SUPPORTED_PROVIDER = "github_copilot_cli"'),
    ("sandbox_single_runner", "scripts/coordination/control_plane/cf10_supervisor_binding_candidate_v0_1.py", 'RUNNER = "forprint-runner"'),
    ("provider_smoke_copilot", "scripts/coordination/control_plane/cf10_r078_copilot_cli_smoke_v0_1.py", "PROVIDER = 'github_copilot_cli'"),
)


def audit_current_source(root: Path) -> dict:
    """Conservative, heuristic source audit, not a proof of absence of coupling."""
    root = Path(root)
    findings = []
    for code, relative, needle in COUPLING_CHECKS:
        p = root / relative
        if p.is_symlink() or not p.is_file():
            findings.append({"code": code, "state": "UNVERIFIED_SOURCE_MISSING", "path": relative})
            continue
        if needle in p.read_text(encoding="utf-8"):
            findings.append({"code": code, "state": "OBSERVED_LEGACY_COUPLING", "path": relative})
        else:
            findings.append({"code": code, "state": "REVIEW_REQUIRED_NO_LONGER_MATCHES_EXPECTATION", "path": relative})
    return {
        "schema_version": AUDIT_SCHEMA,
        "status": "MULTI_PROVIDER_LIVE_DISPATCH_NOT_YET_ENABLED",
        "source_audit_method": "STATIC_SENTINEL_ONLY_NOT_SEMANTIC_PROOF",
        "findings": findings,
        "live_copilot_path_modified": False,
        "provider_selection_wired_to_dispatch": False,
        "additional_ready_provider_enabled": False,
        "parallel_workers_enabled": False,
        "remote_jobs_enabled": False,
        "claim_or_ledger_written": False,
        "worker_launched": False,
        "authorization_granted": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("audit",), required=True)
    ap.add_argument("--root", type=Path, required=True)
    args = ap.parse_args(argv)
    result = audit_current_source(args.root)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
