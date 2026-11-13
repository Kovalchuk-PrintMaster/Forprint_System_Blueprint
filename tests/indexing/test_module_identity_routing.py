import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def test_accounting_current_machine_identity_is_canonical() -> None:
    modules = _load("machine/modules.yaml")["modules"]
    ids = {item["id"] for item in modules}

    assert "forprint_accounting_registry_service" in ids
    assert "accounting_registry_service" not in ids


def test_legacy_operations_queue_has_no_current_authority() -> None:
    data = _load(
        "coordination/outgoing_prompts/forprint_operational_registry/index.yaml"
    )

    assert data["lifecycle"] == "historical_non_authoritative"
    assert data["authority"] == "none"
    assert data["active_prompts"] == []
    assert data["superseded_by"]["module"] == (
        "forprint_operations_control_registry"
    )


def test_current_operations_queue_uses_canonical_identity() -> None:
    data = _load(
        "coordination/outgoing_prompts/"
        "forprint_operations_control_registry/index.yaml"
    )

    assert data["schema_version"] == "prompt_queue_v0_2"
    assert data["module"] == "forprint_operations_control_registry"
    assert data["prompt_queue"] == []


def test_source_registry_points_to_current_operations_queue() -> None:
    data = _load(
        "coordination/registry/coordination_source_registry_v0_1.yaml"
    )
    entry = next(
        item
        for item in data["modules"]
        if item["module_id"] == "forprint_operations_control_registry"
    )

    assert entry["sources"]["prompt_queue"]["path"] == (
        "coordination/outgoing_prompts/"
        "forprint_operations_control_registry/index.yaml"
    )


def test_identity_routing_validator_passes() -> None:
    result = subprocess.run(
        [
            str(ROOT / ".venv_blueprint" / "bin" / "python"),
            "scripts/indexing/validate_module_identity_registry.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "MODULE_IDENTITY_ROUTING_VALIDATION=PASS" in result.stdout
