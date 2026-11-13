from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_REVIEWER_ID = "forprint_project_inspector"
PROJECT_REVIEWER_ROLE = "PROJECT_CONFORMANCE_REVIEWER"
RUNTIME_OBSERVER_ID = "production_runtime_inspector"
RUNTIME_OBSERVER_ROLE = "PRODUCTION_RUNTIME_OBSERVER"

REGISTRY_SCHEMA = "forprint_inspector_reviewer_registry_v0_1"


class InspectorRegistryError(ValueError):
    pass


def load_registry(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InspectorRegistryError(f"inspector registry missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InspectorRegistryError("inspector registry must be a YAML mapping")
    return data


def validate_registry(data: dict[str, Any]) -> None:
    if data.get("schema_version") != REGISTRY_SCHEMA:
        raise InspectorRegistryError("inspector registry schema mismatch")
    if data.get("authority") != "forprint_system_blueprint":
        raise InspectorRegistryError("inspector registry authority mismatch")

    reviewers = data.get("reviewers")
    if not isinstance(reviewers, list):
        raise InspectorRegistryError("reviewers must be a list")

    by_id: dict[str, dict[str, Any]] = {}
    for row in reviewers:
        if not isinstance(row, dict):
            raise InspectorRegistryError("reviewer row must be a mapping")
        reviewer_id = row.get("reviewer_id")
        if not isinstance(reviewer_id, str) or not reviewer_id:
            raise InspectorRegistryError("reviewer_id missing")
        if reviewer_id in by_id:
            raise InspectorRegistryError(f"duplicate reviewer_id: {reviewer_id}")
        by_id[reviewer_id] = row

    project = by_id.get(PROJECT_REVIEWER_ID)
    if not isinstance(project, dict):
        raise InspectorRegistryError("project inspector is not registered")
    if project.get("role") != PROJECT_REVIEWER_ROLE:
        raise InspectorRegistryError("project inspector role mismatch")
    if project.get("completion_conformance_reviewer") is not True:
        raise InspectorRegistryError("project inspector must review completion conformance")
    if project.get("read_only") is not True:
        raise InspectorRegistryError("project inspector must be read-only")
    if project.get("may_accept") is not False:
        raise InspectorRegistryError("project inspector may not own human ACCEPT")
    if project.get("may_mutate_module") is not False:
        raise InspectorRegistryError("project inspector may not mutate modules")

    runtime = by_id.get(RUNTIME_OBSERVER_ID)
    if not isinstance(runtime, dict):
        raise InspectorRegistryError("production runtime inspector is not registered")
    if runtime.get("role") != RUNTIME_OBSERVER_ROLE:
        raise InspectorRegistryError("production runtime inspector role mismatch")
    if runtime.get("completion_conformance_reviewer") is not False:
        raise InspectorRegistryError("production runtime inspector cannot be completion reviewer")

    binding = data.get("completion_reviewer_binding")
    if not isinstance(binding, dict):
        raise InspectorRegistryError("completion reviewer binding missing")
    if binding.get("required_reviewer_id") != PROJECT_REVIEWER_ID:
        raise InspectorRegistryError("completion reviewer id binding mismatch")
    if binding.get("required_role") != PROJECT_REVIEWER_ROLE:
        raise InspectorRegistryError("completion reviewer role binding mismatch")
    if binding.get("binding_state") != "READY":
        raise InspectorRegistryError("completion reviewer binding is not READY")


def resolve_completion_reviewer(
    *,
    registry: dict[str, Any],
    reviewer_id: str | None = None,
) -> dict[str, Any]:
    validate_registry(registry)

    binding = registry["completion_reviewer_binding"]
    required_id = binding["required_reviewer_id"]
    selected_id = reviewer_id or required_id
    if selected_id != required_id:
        raise InspectorRegistryError(
            f"reviewer {selected_id} is not authorized for completion conformance"
        )

    selected = next(row for row in registry["reviewers"] if row["reviewer_id"] == selected_id)
    if selected["role"] != binding["required_role"]:
        raise InspectorRegistryError("selected reviewer role does not match binding")

    return {
        "binding_state": "READY",
        "reviewer_id": selected["reviewer_id"],
        "reviewer_role": selected["role"],
        "read_only": selected["read_only"],
        "completion_conformance_reviewer": selected["completion_conformance_reviewer"],
        "may_accept": selected["may_accept"],
        "may_mutate_module": selected["may_mutate_module"],
        "discovery": selected["discovery"],
        "human_acceptance_authority_preserved": True,
    }
