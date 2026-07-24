from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.coordination.modules._shared.io import (
    WorkflowError,
    read_yaml_mapping,
    sha256_file,
    write_yaml,
)

SCHEMA_VERSION = "blueprint_self_audit_input_v0_1"
MODULE_ID = "forprint_system_blueprint"
WORKFLOW_ID = "blueprint_self_audit"
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def build_input_template(
    *,
    request_id: str,
    bundle_path: str,
    bundle_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "module_id": MODULE_ID,
        "workflow_id": WORKFLOW_ID,
        "request_id": request_id,
        "status": "awaiting_input",
        "source_bundle": {
            "path": bundle_path,
            "sha256": bundle_sha256,
        },
        "analysis": {
            "summary": None,
            "confidence": None,
            "known_strengths": [],
            "gaps": [],
            "priority_actions": [],
            "confirmed_unknowns": [],
            "conflicts": [],
            "workflow_recommendations": [],
            "notes": None,
        },
    }


def create_input_file(
    path: Path,
    *,
    request_id: str,
    bundle_path: str,
    bundle_sha256: str,
) -> dict[str, Any]:
    expected = build_input_template(
        request_id=request_id,
        bundle_path=bundle_path,
        bundle_sha256=bundle_sha256,
    )
    if path.exists():
        current = read_yaml_mapping(path)
        if current == expected:
            return current
        current_status = current.get("status")
        if current_status not in {"consumed", "superseded"}:
            raise WorkflowError(
                f"operator input already exists and is not replaceable: {path} "
                f"(status={current_status!r})"
            )
    write_yaml(path, expected)
    return expected


def validate_provided_input(
    path: Path,
    *,
    expected_request_id: str,
    expected_bundle_sha256: str,
) -> dict[str, Any]:
    data = read_yaml_mapping(path)
    expected_scalars = {
        "schema_version": SCHEMA_VERSION,
        "module_id": MODULE_ID,
        "workflow_id": WORKFLOW_ID,
        "request_id": expected_request_id,
        "status": "provided",
    }
    for key, expected in expected_scalars.items():
        if data.get(key) != expected:
            raise WorkflowError(
                f"{path}: expected {key}={expected!r}, got {data.get(key)!r}"
            )

    source_bundle = data.get("source_bundle")
    if not isinstance(source_bundle, dict):
        raise WorkflowError(f"{path}: source_bundle must be a mapping")
    if source_bundle.get("sha256") != expected_bundle_sha256:
        raise WorkflowError(f"{path}: source bundle checksum does not match")

    analysis = data.get("analysis")
    if not isinstance(analysis, dict):
        raise WorkflowError(f"{path}: analysis must be a mapping")
    summary = analysis.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise WorkflowError(f"{path}: analysis.summary must be non-empty")
    confidence = analysis.get("confidence")
    if confidence not in ALLOWED_CONFIDENCE:
        raise WorkflowError(
            f"{path}: analysis.confidence must be high, medium or low"
        )

    list_fields = (
        "known_strengths",
        "gaps",
        "priority_actions",
        "confirmed_unknowns",
        "conflicts",
        "workflow_recommendations",
    )
    for field in list_fields:
        value = analysis.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            raise WorkflowError(f"{path}: analysis.{field} must be a string list")

    data["input_sha256"] = sha256_file(path)
    return data


def mark_consumed(path: Path, data: dict[str, Any]) -> None:
    updated = dict(data)
    updated.pop("input_sha256", None)
    updated["status"] = "consumed"
    write_yaml(path, updated)
