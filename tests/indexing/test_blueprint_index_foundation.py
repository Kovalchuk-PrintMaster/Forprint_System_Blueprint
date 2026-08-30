import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ROOT / "machine" / "module_identity_registry.yaml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_identity_registry_is_canonical() -> None:
    data = _load(IDENTITY)
    assert data["status"] == "active"
    assert data["authority_state"] == "canonical"
    assert data["authority_scope"] == "stable_module_identifier_only"

    ids = data["canonical_module_ids"]
    assert len(ids) == len(set(ids))
    assert "forprint_operations_control_registry" in ids
    assert "forprint_accounting_registry_service" in ids
    assert "forprint_operational_registry" not in ids
    assert "accounting_registry_service" not in ids


def test_identity_aliases_are_non_current() -> None:
    data = _load(IDENTITY)
    aliases = {item["alias"]: item for item in data["aliases"]}

    assert aliases["accounting_registry_service"]["canonical_id"] == (
        "forprint_accounting_registry_service"
    )
    assert aliases["accounting_registry_service"]["current_use_allowed"] is False

    assert aliases["forprint_operational_registry"]["canonical_id"] == (
        "forprint_operations_control_registry"
    )
    assert aliases["forprint_operational_registry"]["current_use_allowed"] is False


def test_self_coordination_defers_to_current_release_authority() -> None:
    text = (
        ROOT / "coordination" / "self_coordination" / "README.md"
    ).read_text(encoding="utf-8")

    assert "coordination/releases/current.yaml" in text
    assert "historical_non_authoritative_projections" in text
    assert "current.yaml` wins" in text


def test_structure_baseline_is_only_a_profile() -> None:
    text = (
        ROOT / "coordination" / "standards" / "repository_structure_baseline.md"
    ).read_text(encoding="utf-8")

    normalized = " ".join(text.split())
    assert "Advisory minimal profile / reference only" in normalized
    assert "project_structure_standard.md" in normalized
    assert "canonical standard wins" in normalized


def test_derived_indexes_never_claim_authority() -> None:
    root_index = _load(ROOT / "indexes" / "index.yaml")
    modules = _load(ROOT / "indexes" / "modules.yaml")
    authorities = _load(ROOT / "indexes" / "authorities.yaml")

    assert root_index["status"] == "derived_non_authoritative"
    assert root_index["authority"] == "none"
    assert modules["status"] == "derived_non_authoritative"
    assert authorities["status"] == "derived_non_authoritative"


def test_index_builder_is_deterministic_and_clean() -> None:
    result = subprocess.run(
        [
            str(ROOT / ".venv_blueprint" / "bin" / "python"),
            "scripts/indexing/build_blueprint_index.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BLUEPRINT_INDEX_DRIFT_CHECK=PASS" in result.stdout
