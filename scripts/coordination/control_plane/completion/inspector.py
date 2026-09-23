from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.completion.intake import (
    NORMALIZED_SCHEMA,
    load_yaml_mapping,
    sha256_path,
)

REQUEST_SCHEMA = "forprint_inspector_conformance_request_v0_1"
RESULT_SCHEMA = "forprint_inspector_conformance_result_v0_1"
RESULT_STATES = frozenset({"CONFORMANT", "NON_CONFORMANT", "INSUFFICIENT_EVIDENCE"})


@dataclass(frozen=True)
class InspectorRequestResult:
    request_id: str
    document: dict[str, Any]


@dataclass(frozen=True)
class InspectorResultValidation:
    valid: bool
    errors: tuple[str, ...]


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def build_inspector_request(
    *,
    normalized_completion_path: Path,
    acceptance_oracle_path: Path,
    prompt_contract_path: Path,
) -> InspectorRequestResult:
    normalized_path = normalized_completion_path.resolve()
    oracle_path = acceptance_oracle_path.resolve()
    contract_path = prompt_contract_path.resolve()
    normalized = load_yaml_mapping(normalized_path, label="normalized completion")
    if normalized.get("schema_version") != NORMALIZED_SCHEMA:
        raise ValueError("unsupported normalized completion schema")
    identity = normalized.get("identity")
    if not isinstance(identity, dict):
        raise ValueError("normalized completion identity missing")

    stable = {
        "normalized_completion_id": normalized.get("normalized_completion_id"),
        "normalized_completion_sha256": sha256_path(normalized_path),
        "acceptance_oracle_sha256": sha256_path(oracle_path),
        "prompt_contract_sha256": sha256_path(contract_path),
        "module_id": identity.get("module_id"),
        "prompt_id": identity.get("prompt_id"),
        "launch_request_id": identity.get("launch_request_id"),
        "dispatch_intent_id": identity.get("dispatch_intent_id"),
        "worker_invocation_id": identity.get("worker_invocation_id"),
        "task_context_fingerprint_sha256": identity.get("task_context_fingerprint_sha256"),
        "module_head_after": identity.get("module_head_after"),
    }
    if any(value in (None, "") for value in stable.values()):
        raise ValueError("Inspector request binding incomplete")

    fingerprint = hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    request_id = f"{stable['module_id']}__{stable['prompt_id']}__inspection__{fingerprint[:16]}"
    document = {
        "schema_version": REQUEST_SCHEMA,
        "request_id": request_id,
        "identity": {
            "module_id": stable["module_id"],
            "prompt_id": stable["prompt_id"],
            "normalized_completion_id": stable["normalized_completion_id"],
            "dispatch_intent_id": stable["dispatch_intent_id"],
            "worker_invocation_id": stable["worker_invocation_id"],
        },
        "evidence_binding": stable,
        "inspector_boundary": {
            "read_only": True,
            "repository_binding": "UNBOUND_EXTERNAL_REVIEWER",
            "inspector_may_mutate_module": False,
            "inspector_may_dispatch_worker": False,
            "inspector_may_blueprint_accept": False,
            "inspector_may_release_next_prompt": False,
        },
    }
    return InspectorRequestResult(request_id=request_id, document=document)


def write_inspector_request(*, result: InspectorRequestResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result.request_id}.yaml"
    payload = yaml.safe_dump(result.document, sort_keys=False, allow_unicode=True, width=112)
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise ValueError(f"Inspector request identity conflict: {path}")
    if not path.exists():
        path.write_text(payload, encoding="utf-8")
    return path


def validate_inspector_result(
    *, request_path: Path, result_path: Path
) -> InspectorResultValidation:
    request_path = request_path.resolve()
    result_path = result_path.resolve()
    request = load_yaml_mapping(request_path, label="Inspector request")
    result = load_yaml_mapping(result_path, label="Inspector result")
    errors: list[str] = []

    if request.get("schema_version") != REQUEST_SCHEMA:
        errors.append("request_schema")
    if result.get("schema_version") != RESULT_SCHEMA:
        errors.append("result_schema")
    if result.get("request_id") != request.get("request_id"):
        errors.append("request_id")
    if result.get("request_sha256") != sha256_path(request_path):
        errors.append("request_sha256")
    if result.get("state") not in RESULT_STATES:
        errors.append("state")
    if not isinstance(result.get("findings"), list):
        errors.append("findings")
    if _nested(result, "identity", "module_id") != _nested(request, "identity", "module_id"):
        errors.append("identity.module_id")
    if _nested(result, "identity", "prompt_id") != _nested(request, "identity", "prompt_id"):
        errors.append("identity.prompt_id")

    authority = result.get("authority")
    expected = {
        "read_only": True,
        "module_write_performed": False,
        "worker_dispatch_performed": False,
        "blueprint_accept_performed": False,
        "next_prompt_release_performed": False,
    }
    if not isinstance(authority, dict):
        errors.append("authority")
    else:
        for key, value in expected.items():
            if authority.get(key) is not value:
                errors.append(f"authority.{key}")

    return InspectorResultValidation(valid=not errors, errors=tuple(sorted(set(errors))))
