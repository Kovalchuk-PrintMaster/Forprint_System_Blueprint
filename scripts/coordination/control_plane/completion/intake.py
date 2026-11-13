from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CAPTURE_SCHEMA = "forprint_worker_completion_capture_v0_1"
REPORT_SCHEMA = "forprint_worker_completion_report_v0_1"
NORMALIZED_SCHEMA = "forprint_normalized_completion_intake_v0_1"
DISPATCH_SCHEMA = "forprint_dispatch_intent_v0_1"
INVOCATION_SCHEMA = "forprint_worker_invocation_v0_1"


@dataclass(frozen=True)
class NormalizedCompletionResult:
    normalized_id: str
    document: dict[str, Any]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping: {path}")
    return data


def _mapping(data: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{label}.{key} must be a mapping")
    return value


def _list(data: dict[str, Any], key: str, label: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{label}.{key} must be a list")
    return value


def _string(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}.{key} must be a non-empty string")
    return value


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def normalize_completion_intake(
    *,
    completion_capture_path: Path,
    completion_report_path: Path,
    dispatch_intent_path: Path,
    worker_invocation_path: Path,
    legacy_packet_path: Path | None = None,
    legacy_outbox_path: Path | None = None,
) -> NormalizedCompletionResult:
    paths = [
        completion_capture_path,
        completion_report_path,
        dispatch_intent_path,
        worker_invocation_path,
    ]
    capture_path, report_path, dispatch_path, invocation_path = [path.resolve() for path in paths]
    capture = load_yaml_mapping(capture_path, label="completion capture")
    report = load_yaml_mapping(report_path, label="completion report")
    dispatch = load_yaml_mapping(dispatch_path, label="dispatch intent")
    invocation = load_yaml_mapping(invocation_path, label="worker invocation")

    if capture.get("schema_version") != CAPTURE_SCHEMA:
        raise ValueError("unsupported completion capture schema")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError("unsupported completion report schema")
    if dispatch.get("schema_version") != DISPATCH_SCHEMA:
        raise ValueError("unsupported dispatch intent schema")
    if invocation.get("schema_version") != INVOCATION_SCHEMA:
        raise ValueError("unsupported worker invocation schema")
    if capture.get("state") != "COMPLETED":
        raise ValueError("completion capture must be COMPLETED")

    capture_id = _mapping(capture, "identity", "capture")
    report_id = _mapping(report, "identity", "report")
    dispatch_id = _mapping(dispatch, "identity", "dispatch")
    invocation_id = _mapping(invocation, "identity", "invocation")

    module_id = _string(capture_id, "module_id", "capture.identity")
    prompt_id = _string(capture_id, "prompt_id", "capture.identity")
    worker_invocation_id = _string(capture_id, "worker_invocation_id", "capture.identity")
    dispatch_intent_id = _string(capture_id, "dispatch_intent_id", "capture.identity")
    launch_request_id = _string(capture_id, "launch_request_id", "capture.identity")
    task_context_fingerprint = _string(
        capture_id,
        "task_context_fingerprint_sha256",
        "capture.identity",
    )

    comparisons = [
        ("report.module_id", report_id.get("module_id"), module_id),
        ("report.prompt_id", report_id.get("prompt_id"), prompt_id),
        ("dispatch.module_id", dispatch_id.get("module_id"), module_id),
        ("dispatch.prompt_id", dispatch_id.get("prompt_id"), prompt_id),
        ("dispatch_intent_id", dispatch.get("dispatch_intent_id"), dispatch_intent_id),
        ("invocation.module_id", invocation_id.get("module_id"), module_id),
        ("invocation.prompt_id", invocation_id.get("prompt_id"), prompt_id),
        ("worker_invocation_id", invocation.get("invocation_id"), worker_invocation_id),
    ]
    mismatch = [name for name, observed, expected in comparisons if observed != expected]
    if mismatch:
        raise ValueError("completion identity mismatch: " + ",".join(mismatch))

    capture_sha = sha256_path(capture_path)
    if report.get("completion_capture_sha256") != capture_sha:
        raise ValueError("completion report capture SHA mismatch")

    module_head_before = _nested(invocation, "authority_binding", "module_head") or capture.get(
        "module_head_before"
    )
    module_head_after = capture.get("module_head_after")
    if not isinstance(module_head_before, str) or not module_head_before:
        raise ValueError("module_head_before missing")
    if not isinstance(module_head_after, str) or not module_head_after:
        raise ValueError("module_head_after missing")

    changed_files = _list(report, "changed_files", "report")
    validation_evidence = _list(report, "validation_evidence", "report")
    inventory_lineage_impact = _mapping(report, "inventory_lineage_impact", "report")
    resource_observability = _mapping(report, "resource_observability", "report")
    evidence_manifest = _list(report, "evidence_manifest", "report")

    observed_keys = (
        "runtime_duration",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cost",
        "currency",
        "peak_memory",
        "cpu_time",
        "network_bytes",
    )
    normalized_observability = {
        key: resource_observability.get(key, "not_observable") for key in observed_keys
    }

    identity = {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "worker_invocation_id": worker_invocation_id,
        "dispatch_intent_id": dispatch_intent_id,
        "launch_request_id": launch_request_id,
        "task_context_fingerprint_sha256": task_context_fingerprint,
        "completion_capture_sha256": capture_sha,
        "completion_report_sha256": sha256_path(report_path),
        "module_head_before": module_head_before,
        "module_head_after": module_head_after,
    }
    fingerprint = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    normalized_id = f"{module_id}__{prompt_id}__completion__{fingerprint[:16]}"

    legacy = {
        "completion_packet_path": None,
        "completion_packet_sha256": None,
        "completion_outbox_path": None,
        "completion_outbox_sha256": None,
        "legacy_primitives_are_acceptance_authority": False,
    }
    if legacy_packet_path is not None:
        path = legacy_packet_path.resolve()
        legacy["completion_packet_path"] = str(path)
        legacy["completion_packet_sha256"] = sha256_path(path)
    if legacy_outbox_path is not None:
        path = legacy_outbox_path.resolve()
        legacy["completion_outbox_path"] = str(path)
        legacy["completion_outbox_sha256"] = sha256_path(path)

    document = {
        "schema_version": NORMALIZED_SCHEMA,
        "normalized_completion_id": normalized_id,
        "identity": identity,
        "sources": {
            "completion_capture_path": str(capture_path),
            "completion_report_path": str(report_path),
            "dispatch_intent_path": str(dispatch_path),
            "worker_invocation_path": str(invocation_path),
        },
        "completion": {
            "changed_files": changed_files,
            "validation_evidence": validation_evidence,
            "inventory_lineage_impact": inventory_lineage_impact,
            "resource_observability": normalized_observability,
            "evidence_manifest": evidence_manifest,
        },
        "legacy_compatibility": legacy,
        "semantic_boundaries": {
            "normalized_intake_is_blueprint_accept": False,
            "normalized_intake_is_operator_decision": False,
            "automatic_accept": False,
            "automatic_next_prompt_release": False,
        },
    }
    return NormalizedCompletionResult(normalized_id=normalized_id, document=document)


def write_normalized_completion(*, result: NormalizedCompletionResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{result.normalized_id}.yaml"
    payload = yaml.safe_dump(result.document, sort_keys=False, allow_unicode=True, width=112)
    if path.exists() and path.read_text(encoding="utf-8") != payload:
        raise ValueError(f"normalized completion identity conflict: {path}")
    if not path.exists():
        path.write_text(payload, encoding="utf-8")
    return path
