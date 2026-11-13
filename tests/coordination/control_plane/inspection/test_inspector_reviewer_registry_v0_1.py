from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.inspection.reviewer_registry import (
    InspectorRegistryError,
    resolve_completion_reviewer,
    validate_registry,
)


def _registry() -> dict:
    return {
        "schema_version": "forprint_inspector_reviewer_registry_v0_1",
        "authority": "forprint_system_blueprint",
        "reviewers": [
            {
                "reviewer_id": "forprint_project_inspector",
                "role": "PROJECT_CONFORMANCE_REVIEWER",
                "completion_conformance_reviewer": True,
                "read_only": True,
                "may_accept": False,
                "may_mutate_module": False,
                "discovery": {
                    "mode": "blueprint_registry_identity",
                    "identity": "forprint_project_inspector",
                },
            },
            {
                "reviewer_id": "production_runtime_inspector",
                "role": "PRODUCTION_RUNTIME_OBSERVER",
                "completion_conformance_reviewer": False,
                "read_only": True,
                "may_accept": False,
                "may_mutate_module": False,
                "discovery": {
                    "mode": "blueprint_registry_identity",
                    "identity": "production_runtime_inspector",
                },
            },
        ],
        "completion_reviewer_binding": {
            "required_reviewer_id": "forprint_project_inspector",
            "required_role": "PROJECT_CONFORMANCE_REVIEWER",
            "binding_state": "READY",
        },
    }


def test_project_inspector_binding_is_ready() -> None:
    registry = _registry()
    validate_registry(registry)
    result = resolve_completion_reviewer(registry=registry)
    assert result["binding_state"] == "READY"
    assert result["reviewer_id"] == "forprint_project_inspector"
    assert result["reviewer_role"] == "PROJECT_CONFORMANCE_REVIEWER"
    assert result["read_only"] is True
    assert result["may_accept"] is False


def test_runtime_inspector_cannot_substitute_for_project_inspector() -> None:
    with pytest.raises(InspectorRegistryError):
        resolve_completion_reviewer(
            registry=_registry(),
            reviewer_id="production_runtime_inspector",
        )


def test_project_inspector_cannot_own_acceptance() -> None:
    registry = _registry()
    registry["reviewers"][0]["may_accept"] = True
    with pytest.raises(InspectorRegistryError):
        validate_registry(registry)


def test_project_inspector_cannot_mutate_module() -> None:
    registry = _registry()
    registry["reviewers"][0]["may_mutate_module"] = True
    with pytest.raises(InspectorRegistryError):
        validate_registry(registry)


def test_registry_roundtrip_yaml(tmp_path: Path) -> None:
    path = tmp_path / "registry.yaml"
    path.write_text(
        yaml.safe_dump(_registry(), sort_keys=False),
        encoding="utf-8",
    )
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_registry(loaded)
