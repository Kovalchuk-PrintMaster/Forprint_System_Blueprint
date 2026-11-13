#!/usr/bin/env python3
"""Shared authority-neutral structured command capability executor.

The executor owns execution mechanics and generic safety validation only.
Consumer-specific policy/authority remains external and must arrive in a
fully bound authorization envelope. Raw shell text, arbitrary executables and
unrestricted argv are intentionally unsupported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.coordination.control_plane.worker_runtime.launcher import (
    launch_process,
)
from scripts.validation import run_validation_suite_v0_1 as validation_suite

SCHEMA = "forprint_structured_command_capability_registry_v0_1"
REGISTRY = Path(
    "coordination/registry/structured_command_capabilities_v0_1.yaml"
)
PLAN_SCHEMA = "forprint_structured_execution_plan_v0_1"
RESULT_SCHEMA = "forprint_structured_execution_result_v0_1"
AUTHORIZATION_SCHEMA = (
    "forprint_structured_execution_authorization_envelope_v0_1"
)
CAPABILITY_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")

REQUEST_KEYS = {
    "capability_id",
    "capability_version",
    "execution_scope",
    "exact_cwd",
    "parameters",
    "timeout_seconds",
    "evidence_destination",
    "execution_identity",
    "consumer_id",
    "request_id",
    "authorization_envelope",
}
AUTHORIZATION_KEYS = {
    "schema_version",
    "decision",
    "consumer_id",
    "request_id",
    "capability_id",
    "capability_version",
    "execution_identity",
    "execution_scope",
    "authority",
    "exact_cwd",
    "parameters",
    "timeout_seconds",
    "evidence_destination",
}
AUTHORITY_KEYS = {
    "consumer_policy_validated",
    "executor_grants_authority",
    "canonical_write_allowed",
    "safe_write_allowed",
    "commit_allowed",
    "push_allowed",
    "merge_allowed",
    "release_allowed",
    "promotion_allowed",
    "arbitrary_shell_allowed",
}
FORBIDDEN_TRUE_AUTHORITY = AUTHORITY_KEYS - {"consumer_policy_validated"}

CAPABILITY_KEYS_COMMON = {
    "capability_version",
    "description",
    "builder_kind",
    "executable_identity",
    "fixed_argv",
    "parameter_schema",
    "allowed_cwd_scope_kind",
    "timeout_bounds",
    "side_effect_class",
    "output_contract",
    "heartbeat_policy_support",
    "cancellation_support_state",
    "consumer_compatibility",
}
CAPABILITY_KEYS_VALIDATION = CAPABILITY_KEYS_COMMON | {
    "validation_suite_script",
    "validation_suite_registry",
}

REGISTRY_KEYS = {
    "schema_version",
    "status",
    "authority",
    "registry_grants_authority",
    "command_representation",
    "shell",
    "arbitrary_command_text_allowed",
    "capabilities",
}

ALLOWED_BUILDERS = {"FIXED_GIT", "VALIDATION_SUITE"}
ALLOWED_SIDE_EFFECTS = {"NONE_EXPECTED", "READ_ONLY_VALIDATION"}


class StructuredCommandExecutorError(RuntimeError):
    """Raised when structured execution cannot be proven safe and bound."""


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StructuredCommandExecutorError(f"{label} must be a mapping")
    return dict(value)


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StructuredCommandExecutorError(
            f"{label} must be a non-empty string"
        )
    return value.strip()


def _reject_unknown(
    mapping: Mapping[str, Any],
    allowed: set[str],
    label: str,
) -> None:
    unknown = sorted(set(mapping) - allowed)
    if unknown:
        raise StructuredCommandExecutorError(
            f"{label} contains unsupported keys: {unknown}"
        )


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_absolute_path(raw: Any, label: str) -> Path:
    text = _string(raw, label)
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise StructuredCommandExecutorError(
            f"{label} must be an absolute path"
        )
    resolved = path.resolve()
    if str(resolved) != text:
        raise StructuredCommandExecutorError(
            f"{label} must be normalized and canonical"
        )
    return resolved


def _is_inside(scope: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(scope)
        return True
    except ValueError:
        return False


def _validate_timeout_bounds(value: Any, label: str) -> dict[str, int]:
    data = _mapping(value, label)
    _reject_unknown(
        data,
        {"minimum", "default", "maximum"},
        label,
    )
    values: dict[str, int] = {}
    for key in ("minimum", "default", "maximum"):
        item = data.get(key)
        if (
            not isinstance(item, int)
            or isinstance(item, bool)
            or item <= 0
        ):
            raise StructuredCommandExecutorError(
                f"{label}.{key} must be a positive integer"
            )
        values[key] = item
    if not (
        values["minimum"]
        <= values["default"]
        <= values["maximum"]
        <= 1200
    ):
        raise StructuredCommandExecutorError(
            f"{label} ordering/range is invalid"
        )
    return values


def validate_capability_registry_data(
    value: Any,
    *,
    root: Path,
) -> dict[str, Any]:
    registry = _mapping(value, "capability registry")
    _reject_unknown(registry, REGISTRY_KEYS, "capability registry")
    if registry.get("schema_version") != SCHEMA:
        raise StructuredCommandExecutorError(
            "capability registry schema mismatch"
        )
    if registry.get("status") != "current_standard":
        raise StructuredCommandExecutorError(
            "capability registry status must be current_standard"
        )
    if registry.get("authority") != "forprint_system_blueprint":
        raise StructuredCommandExecutorError(
            "capability registry authority mismatch"
        )
    if registry.get("registry_grants_authority") is not False:
        raise StructuredCommandExecutorError(
            "capability registry must not grant authority"
        )
    if registry.get("command_representation") != "STRUCTURED_ARGV":
        raise StructuredCommandExecutorError(
            "capability registry must use STRUCTURED_ARGV"
        )
    if registry.get("shell") is not False:
        raise StructuredCommandExecutorError(
            "capability registry shell must remain false"
        )
    if registry.get("arbitrary_command_text_allowed") is not False:
        raise StructuredCommandExecutorError(
            "arbitrary command text must remain forbidden"
        )

    capabilities = _mapping(
        registry.get("capabilities"),
        "capability registry capabilities",
    )
    if not capabilities:
        raise StructuredCommandExecutorError(
            "capability registry must not be empty"
        )

    for capability_id, raw in capabilities.items():
        if (
            not isinstance(capability_id, str)
            or not CAPABILITY_ID_RE.fullmatch(capability_id)
        ):
            raise StructuredCommandExecutorError(
                f"invalid capability id: {capability_id!r}"
            )
        capability = _mapping(
            raw,
            f"capability {capability_id}",
        )
        builder = capability.get("builder_kind")
        if builder not in ALLOWED_BUILDERS:
            raise StructuredCommandExecutorError(
                f"unsupported builder kind for {capability_id}: {builder!r}"
            )
        allowed_keys = (
            CAPABILITY_KEYS_VALIDATION
            if builder == "VALIDATION_SUITE"
            else CAPABILITY_KEYS_COMMON
        )
        _reject_unknown(
            capability,
            allowed_keys,
            f"capability {capability_id}",
        )

        version = capability.get("capability_version")
        if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
            raise StructuredCommandExecutorError(
                f"capability {capability_id} version invalid"
            )
        if (
            not isinstance(capability.get("description"), str)
            or not capability["description"].strip()
        ):
            raise StructuredCommandExecutorError(
                f"capability {capability_id} description missing"
            )
        if capability.get("allowed_cwd_scope_kind") != "GIT_REPOSITORY_ROOT":
            raise StructuredCommandExecutorError(
                f"capability {capability_id} cwd scope kind invalid"
            )
        _validate_timeout_bounds(
            capability.get("timeout_bounds"),
            f"capability {capability_id} timeout_bounds",
        )
        if capability.get("side_effect_class") not in ALLOWED_SIDE_EFFECTS:
            raise StructuredCommandExecutorError(
                f"capability {capability_id} side effect class invalid"
            )
        if (
            capability.get("output_contract")
            != "STDOUT_STDERR_EXTERNAL_EVIDENCE"
        ):
            raise StructuredCommandExecutorError(
                f"capability {capability_id} output contract invalid"
            )
        if capability.get("heartbeat_policy_support") is not True:
            raise StructuredCommandExecutorError(
                f"capability {capability_id} heartbeat support invalid"
            )
        if capability.get("cancellation_support_state") != "NOT_IMPLEMENTED":
            raise StructuredCommandExecutorError(
                f"capability {capability_id} cancellation state invalid"
            )
        consumers = capability.get("consumer_compatibility")
        if (
            not isinstance(consumers, list)
            or not consumers
            or not all(isinstance(item, str) and item for item in consumers)
            or len(consumers) != len(set(consumers))
        ):
            raise StructuredCommandExecutorError(
                f"capability {capability_id} consumer compatibility invalid"
            )

        parameter_schema = _mapping(
            capability.get("parameter_schema"),
            f"capability {capability_id} parameter_schema",
        )
        if parameter_schema.get("additional_properties") is not False:
            raise StructuredCommandExecutorError(
                f"capability {capability_id} must reject arbitrary parameters"
            )

        if builder == "FIXED_GIT":
            if capability.get("executable_identity") != "git":
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} executable identity invalid"
                )
            argv = capability.get("fixed_argv")
            if (
                not isinstance(argv, list)
                or not argv
                or not all(isinstance(item, str) and item for item in argv)
            ):
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} fixed argv invalid"
                )
            if parameter_schema != {
                "model": "EMPTY_OBJECT",
                "additional_properties": False,
            }:
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} parameter schema invalid"
                )
        else:
            if capability.get("executable_identity") != "python_runtime":
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} executable identity invalid"
                )
            if capability.get("fixed_argv") is not None:
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} fixed argv must be null"
                )
            if parameter_schema != {
                "model": "VALIDATION_SUITE_V0_2",
                "additional_properties": False,
                "required": ["suite_id"],
                "optional": ["require_tier", "profile"],
            }:
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} parameter schema invalid"
                )
            script = capability.get("validation_suite_script")
            suite_registry = capability.get("validation_suite_registry")
            if script != "scripts/validation/run_validation_suite_v0_1.py":
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} validation script drift"
                )
            if (
                suite_registry
                != "coordination/standards/automation/"
                "validation_suite_registry_v0_1.yaml"
            ):
                raise StructuredCommandExecutorError(
                    f"capability {capability_id} suite registry drift"
                )
            for rel in (script, suite_registry):
                path = root / rel
                if not path.is_file() or path.is_symlink():
                    raise StructuredCommandExecutorError(
                        f"capability dependency missing or unsafe: {rel}"
                    )

    return registry


def load_capability_registry(root: Path | str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    path = root_path / REGISTRY
    if not path.is_file() or path.is_symlink():
        raise StructuredCommandExecutorError(
            f"capability registry missing or unsafe: {REGISTRY}"
        )
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise StructuredCommandExecutorError(
            f"invalid capability registry YAML: {exc}"
        ) from exc
    return validate_capability_registry_data(value, root=root_path)


def list_capabilities(root: Path | str) -> dict[str, Any]:
    registry = load_capability_registry(root)
    return {
        "schema_version": SCHEMA,
        "registry_grants_authority": False,
        "command_representation": "STRUCTURED_ARGV",
        "shell": False,
        "arbitrary_command_text_allowed": False,
        "capabilities": [
            {
                "capability_id": capability_id,
                "capability_version": item["capability_version"],
                "builder_kind": item["builder_kind"],
                "side_effect_class": item["side_effect_class"],
                "parameter_schema": item["parameter_schema"],
                "consumer_compatibility": item["consumer_compatibility"],
                "cancellation_support_state": item[
                    "cancellation_support_state"
                ],
            }
            for capability_id, item in sorted(
                registry["capabilities"].items()
            )
        ],
    }


def _validate_scope(request: Mapping[str, Any]) -> Path:
    exact_cwd = _normalized_absolute_path(
        request.get("exact_cwd"),
        "exact_cwd",
    )
    scope = _mapping(
        request.get("execution_scope"),
        "execution_scope",
    )
    _reject_unknown(scope, {"kind", "root"}, "execution_scope")
    if scope.get("kind") != "GIT_REPOSITORY_ROOT":
        raise StructuredCommandExecutorError(
            "execution_scope kind must be GIT_REPOSITORY_ROOT"
        )
    scope_root = _normalized_absolute_path(
        scope.get("root"),
        "execution_scope.root",
    )
    if scope_root != exact_cwd:
        raise StructuredCommandExecutorError(
            "execution_scope root must equal exact_cwd"
        )
    git_marker = exact_cwd / ".git"
    if not git_marker.exists() or git_marker.is_symlink():
        raise StructuredCommandExecutorError(
            "exact_cwd must be an exact GIT_REPOSITORY_ROOT"
        )
    return exact_cwd


def _validate_authorization_envelope(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = _mapping(
        request.get("authorization_envelope"),
        "authorization envelope",
    )
    _reject_unknown(
        envelope,
        AUTHORIZATION_KEYS,
        "authorization envelope",
    )
    if envelope.get("schema_version") != AUTHORIZATION_SCHEMA:
        raise StructuredCommandExecutorError(
            "authorization envelope schema mismatch"
        )
    if envelope.get("decision") != "ALLOW_EXACT_STRUCTURED_EXECUTION":
        raise StructuredCommandExecutorError(
            "authorization envelope decision must be exact allow"
        )

    binding_fields = (
        "consumer_id",
        "request_id",
        "capability_id",
        "capability_version",
        "execution_identity",
        "execution_scope",
        "exact_cwd",
        "parameters",
        "timeout_seconds",
        "evidence_destination",
    )
    drift = [
        field
        for field in binding_fields
        if envelope.get(field) != request.get(field)
    ]
    if drift:
        raise StructuredCommandExecutorError(
            "authorization envelope binding drift: "
            + ",".join(drift)
        )

    authority = _mapping(
        envelope.get("authority"),
        "authorization envelope authority",
    )
    _reject_unknown(
        authority,
        AUTHORITY_KEYS,
        "authorization envelope authority",
    )
    if authority.get("consumer_policy_validated") is not True:
        raise StructuredCommandExecutorError(
            "authorization envelope consumer policy is not validated"
        )
    widened = [
        key
        for key in sorted(FORBIDDEN_TRUE_AUTHORITY)
        if authority.get(key) is not False
    ]
    if widened:
        raise StructuredCommandExecutorError(
            "authorization envelope widened authority: "
            + ",".join(widened)
        )
    return envelope


def _validate_request(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    value = _mapping(request, "structured execution request")
    _reject_unknown(value, REQUEST_KEYS, "structured execution request")

    capability_id = _string(
        value.get("capability_id"),
        "capability_id",
    )
    if not CAPABILITY_ID_RE.fullmatch(capability_id):
        raise StructuredCommandExecutorError("capability_id invalid")

    version = _string(
        value.get("capability_version"),
        "capability_version",
    )
    if not VERSION_RE.fullmatch(version):
        raise StructuredCommandExecutorError(
            "capability_version invalid"
        )

    consumer_id = _string(value.get("consumer_id"), "consumer_id")
    request_id = _string(value.get("request_id"), "request_id")
    if not REQUEST_ID_RE.fullmatch(request_id):
        raise StructuredCommandExecutorError("request_id invalid")

    parameters = _mapping(value.get("parameters"), "parameters")
    execution_identity = _mapping(
        value.get("execution_identity"),
        "execution_identity",
    )
    if not execution_identity:
        raise StructuredCommandExecutorError(
            "execution_identity must not be empty"
        )

    timeout = value.get("timeout_seconds")
    if (
        not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or timeout <= 0
    ):
        raise StructuredCommandExecutorError(
            "timeout_seconds must be a positive integer"
        )

    exact_cwd = _validate_scope(value)
    evidence_destination = _normalized_absolute_path(
        value.get("evidence_destination"),
        "evidence_destination",
    )
    if evidence_destination == exact_cwd or _is_inside(
        exact_cwd,
        evidence_destination,
    ):
        raise StructuredCommandExecutorError(
            "evidence_destination must remain outside exact_cwd"
        )

    _validate_authorization_envelope(value)

    return {
        **value,
        "capability_id": capability_id,
        "capability_version": version,
        "consumer_id": consumer_id,
        "request_id": request_id,
        "parameters": parameters,
        "execution_identity": execution_identity,
        "timeout_seconds": timeout,
        "exact_cwd": str(exact_cwd),
        "execution_scope": {
            "kind": "GIT_REPOSITORY_ROOT",
            "root": str(exact_cwd),
        },
        "evidence_destination": str(evidence_destination),
    }


def _build_argv(
    *,
    root: Path,
    capability_id: str,
    capability: Mapping[str, Any],
    parameters: Mapping[str, Any],
) -> list[str]:
    builder = capability["builder_kind"]

    if builder == "FIXED_GIT":
        if parameters:
            raise StructuredCommandExecutorError(
                f"capability {capability_id} accepts no parameters"
            )
        git_executable = shutil.which("git")
        if not git_executable:
            raise StructuredCommandExecutorError(
                "registered git executable is unavailable"
            )
        return [
            str(Path(git_executable).resolve()),
            "--no-optional-locks",
            *list(capability["fixed_argv"]),
        ]

    if builder != "VALIDATION_SUITE":
        raise StructuredCommandExecutorError(
            f"unsupported builder kind: {builder}"
        )

    unknown = sorted(
        set(parameters) - {"suite_id", "require_tier", "profile"}
    )
    if unknown:
        raise StructuredCommandExecutorError(
            "validation_suite contains unsupported parameters: "
            + ",".join(unknown)
        )

    suite_id = _string(parameters.get("suite_id"), "parameters.suite_id")
    try:
        suites = validation_suite.load_registry(root)
        suite = validation_suite.resolve_suite(suites, suite_id)
    except validation_suite.SuiteError as exc:
        raise StructuredCommandExecutorError(
            f"unknown validation suite or invalid registry binding: {exc}"
        ) from exc

    require_tier = parameters.get("require_tier")
    if require_tier is not None:
        require_tier = _string(
            require_tier,
            "parameters.require_tier",
        )
        if require_tier not in validation_suite.ALLOWED_VERIFICATION_TIERS:
            raise StructuredCommandExecutorError(
                "validation suite require_tier is unsupported"
            )
        if suite.get("verification_tier") != require_tier:
            raise StructuredCommandExecutorError(
                f"validation suite {suite_id} does not match registered tier "
                f"{require_tier}"
            )

    profile = parameters.get("profile", False)
    if not isinstance(profile, bool):
        raise StructuredCommandExecutorError(
            "validation suite profile must be boolean"
        )

    argv = [
        sys.executable,
        "scripts/validation/run_validation_suite_v0_1.py",
        "--suite",
        suite_id,
    ]
    if require_tier is not None:
        argv.extend(["--require-tier", require_tier])
    if profile:
        argv.append("--profile")
    return argv


def build_execution_plan(
    *,
    root: Path | str,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    normalized = _validate_request(request)
    registry = load_capability_registry(root_path)

    capability_id = normalized["capability_id"]
    capabilities = registry["capabilities"]
    if capability_id not in capabilities:
        raise StructuredCommandExecutorError(
            f"unknown capability: {capability_id}"
        )
    capability = capabilities[capability_id]
    if normalized["capability_version"] != capability["capability_version"]:
        raise StructuredCommandExecutorError(
            "capability version mismatch"
        )

    timeout_bounds = capability["timeout_bounds"]
    timeout = normalized["timeout_seconds"]
    if not (
        timeout_bounds["minimum"]
        <= timeout
        <= timeout_bounds["maximum"]
    ):
        raise StructuredCommandExecutorError(
            "timeout_seconds outside registered bounds"
        )

    argv = _build_argv(
        root=root_path,
        capability_id=capability_id,
        capability=capability,
        parameters=normalized["parameters"],
    )
    argv_digest = hashlib.sha256(
        "\0".join(argv).encode("utf-8")
    ).hexdigest()

    request_digest = _sha(normalized)
    execution_id = "structured-exec-" + request_digest[:20]
    evidence_root = Path(normalized["evidence_destination"]).resolve()
    execution_dir = evidence_root / execution_id

    capability_material = {
        "capability_id": capability_id,
        **capability,
    }

    return {
        "schema_version": PLAN_SCHEMA,
        "request": normalized,
        "request_sha256": request_digest,
        "execution_id": execution_id,
        "capability": {
            "capability_id": capability_id,
            "capability_version": capability["capability_version"],
            "definition_sha256": _sha(capability_material),
            "builder_kind": capability["builder_kind"],
            "side_effect_class": capability["side_effect_class"],
            "cancellation_support_state": capability[
                "cancellation_support_state"
            ],
        },
        "execution": {
            "command_representation": "STRUCTURED_ARGV",
            "argv": argv,
            "argv_digest": argv_digest,
            "cwd": normalized["exact_cwd"],
            "shell": False,
            "timeout_seconds": timeout,
            "heartbeat_seconds": 15,
            "stall_threshold_seconds": None,
            "stdout_path": str(execution_dir / "stdout.log"),
            "stderr_path": str(execution_dir / "stderr.log"),
            "result_path": str(
                execution_dir / "execution_result_v0_1.yaml"
            ),
        },
        "execution_policy_result": {
            "decision": "ALLOW",
            "consumer_policy_validated": True,
            "authorization_envelope_verified": True,
            "authority_originated_by_executor": False,
        },
        "authority": {
            "executor_grants_authority": False,
            "canonical_write_allowed": False,
            "safe_write_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
            "arbitrary_shell_allowed": False,
        },
    }


def _file_evidence(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise StructuredCommandExecutorError(
            f"execution evidence file missing: {path}"
        )
    return {
        "path": str(path),
        "sha256": _sha_file(path),
        "size_bytes": path.stat().st_size,
    }


def execute_execution_plan(
    *,
    root: Path | str,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    root_path = Path(root).resolve()
    supplied = _mapping(plan, "execution plan")
    if supplied.get("schema_version") != PLAN_SCHEMA:
        raise StructuredCommandExecutorError(
            "execution plan schema mismatch"
        )
    request = _mapping(supplied.get("request"), "execution plan request")
    expected = build_execution_plan(root=root_path, request=request)
    if _canonical_json(supplied) != _canonical_json(expected):
        raise StructuredCommandExecutorError(
            "execution plan drift detected before launch"
        )

    execution = expected["execution"]
    stdout_path = Path(execution["stdout_path"])
    stderr_path = Path(execution["stderr_path"])
    result_path = Path(execution["result_path"])
    for path in (stdout_path, stderr_path, result_path):
        if path.exists() or path.is_symlink():
            raise StructuredCommandExecutorError(
                f"immutable execution evidence already exists: {path}"
            )

    launched = launch_process(
        argv=list(execution["argv"]),
        cwd=execution["cwd"],
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_seconds=execution["timeout_seconds"],
        heartbeat_seconds=execution["heartbeat_seconds"],
        stall_threshold_seconds=execution["stall_threshold_seconds"],
    )

    launcher_binding_drift: list[str] = []

    if launched.get("process_started") is not True:
        launcher_binding_drift.append("process_started")

    if launched.get("shell") is not False:
        launcher_binding_drift.append("shell")

    if launched.get("cwd") != execution["cwd"]:
        launcher_binding_drift.append("cwd")

    if launched.get("argv_sha256") != execution["argv_digest"]:
        launcher_binding_drift.append("argv_sha256")

    if launched.get("stdout_path") != str(stdout_path):
        launcher_binding_drift.append("stdout_path")

    if launched.get("stderr_path") != str(stderr_path):
        launcher_binding_drift.append("stderr_path")

    if launcher_binding_drift:
        raise StructuredCommandExecutorError(
            "launcher result binding drift: "
            + ",".join(launcher_binding_drift)
        )

    stdout_evidence = _file_evidence(stdout_path)
    stderr_evidence = _file_evidence(stderr_path)

    result: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA,
        "request_id": request["request_id"],
        "capability_id": request["capability_id"],
        "capability_version": request["capability_version"],
        "execution_id": expected["execution_id"],
        "execution_identity": request["execution_identity"],
        "consumer_id": request["consumer_id"],
        "exact_cwd": execution["cwd"],
        "argv_digest": execution["argv_digest"],
        "started_at": launched.get("started_at"),
        "finished_at": launched.get("finished_at"),
        "elapsed_seconds": launched.get("elapsed_seconds"),
        "return_code": launched.get("return_code"),
        "outcome": launched.get("outcome"),
        "timed_out": launched.get("timed_out"),
        "shell": False,
        "stdout_evidence": stdout_evidence,
        "stderr_evidence": stderr_evidence,
        "heartbeat_evidence": {
            "observations": launched.get(
                "heartbeat_observations",
                [],
            ),
            "stall_detected": bool(
                launched.get("stall_detected")
            ),
            "stall_evidence": launched.get(
                "stall_evidence",
                [],
            ),
        },
        "stall_detected": bool(launched.get("stall_detected")),
        "cancellation_state": "NOT_IMPLEMENTED",
        "execution_policy_result": expected[
            "execution_policy_result"
        ],
        "authority": dict(expected["authority"]),
        "result_evidence_path": str(result_path),
    }
    result["evidence_digest"] = _sha(result)

    result_path.parent.mkdir(parents=True, exist_ok=True)
    with result_path.open("x", encoding="utf-8") as handle:
        yaml.safe_dump(
            result,
            handle,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        )
    return result


def _proof_request(
    *,
    root: Path,
    evidence_dir: Path,
    suite_id: str,
    require_tier: str | None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "capability_id": "validation_suite",
        "capability_version": "0.2.0",
        "execution_scope": {
            "kind": "GIT_REPOSITORY_ROOT",
            "root": str(root),
        },
        "exact_cwd": str(root),
        "parameters": {"suite_id": suite_id},
        "timeout_seconds": 1200,
        "evidence_destination": str(evidence_dir),
        "execution_identity": {
            "attempt_id": "cf10-shared-executor-foundation-proof",
            "actor_type": "human_terminal",
        },
        "consumer_id": "CF10_FOUNDATION_PROOF",
        "request_id": "cf10-shared-executor-foundation-proof",
    }
    if require_tier is not None:
        request["parameters"]["require_tier"] = require_tier

    request["authorization_envelope"] = {
        "schema_version": AUTHORIZATION_SCHEMA,
        "decision": "ALLOW_EXACT_STRUCTURED_EXECUTION",
        "consumer_id": request["consumer_id"],
        "request_id": request["request_id"],
        "capability_id": request["capability_id"],
        "capability_version": request["capability_version"],
        "execution_identity": dict(request["execution_identity"]),
        "execution_scope": dict(request["execution_scope"]),
        "exact_cwd": request["exact_cwd"],
        "parameters": dict(request["parameters"]),
        "timeout_seconds": request["timeout_seconds"],
        "evidence_destination": request["evidence_destination"],
        "authority": {
            "consumer_policy_validated": True,
            "executor_grants_authority": False,
            "canonical_write_allowed": False,
            "safe_write_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
            "arbitrary_shell_allowed": False,
        },
    }
    return request


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ForPrint shared structured command capability executor"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check")
    check.add_argument("--root", default=str(PROJECT_ROOT))

    listing = sub.add_parser("list")
    listing.add_argument("--root", default=str(PROJECT_ROOT))

    proof = sub.add_parser("proof")
    proof.add_argument("--root", default=str(PROJECT_ROOT))
    proof.add_argument("--suite", default="cf10-worker-pipeline")
    proof.add_argument("--require-tier")
    proof.add_argument("--evidence-dir", required=True)

    args = parser.parse_args()

    try:
        root = Path(args.root).resolve()

        if args.command == "check":
            registry = load_capability_registry(root)
            print("STRUCTURED_COMMAND_EXECUTOR_CHECK=PASS")
            print(f"CAPABILITY_COUNT={len(registry['capabilities'])}")
            print("COMMAND_REPRESENTATION=STRUCTURED_ARGV")
            print("SHELL=false")
            print("ARBITRARY_COMMAND_TEXT_ALLOWED=false")
            print("REGISTRY_GRANTS_AUTHORITY=false")
            return 0

        if args.command == "list":
            print(
                yaml.safe_dump(
                    list_capabilities(root),
                    sort_keys=False,
                    allow_unicode=True,
                    width=112,
                ).rstrip()
            )
            return 0

        evidence_dir = Path(args.evidence_dir).expanduser().resolve()
        request = _proof_request(
            root=root,
            evidence_dir=evidence_dir,
            suite_id=args.suite,
            require_tier=args.require_tier,
        )
        plan = build_execution_plan(root=root, request=request)
        result = execute_execution_plan(root=root, plan=plan)

        if result.get("return_code") != 0 or result.get("timed_out") is True:
            print("STRUCTURED_COMMAND_EXECUTOR_PROOF=FAIL")
            print(f"RETURN_CODE={result.get('return_code')}")
            print(f"TIMED_OUT={str(result.get('timed_out')).lower()}")
            print(
                "RESULT_EVIDENCE="
                + str(result.get("result_evidence_path"))
            )
            return 1

        print("STRUCTURED_COMMAND_EXECUTOR_PROOF=PASS")
        print(f"CAPABILITY_ID={result['capability_id']}")
        print(f"EXECUTION_ID={result['execution_id']}")
        print(f"RETURN_CODE={result['return_code']}")
        print("SHELL=false")
        print("AUTHORITY_WIDENED=false")
        print(f"EVIDENCE_DIGEST={result['evidence_digest']}")
        print(f"RESULT_EVIDENCE={result['result_evidence_path']}")
        return 0

    except StructuredCommandExecutorError as exc:
        print("STRUCTURED_COMMAND_EXECUTOR=FAIL")
        print(f"ERROR={type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
