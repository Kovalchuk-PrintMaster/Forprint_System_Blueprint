from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

REGISTRY = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"
BASELINE = (
    ROOT / "coordination/internal_work/blueprint/normalization/"
    "2026-09-01__document_surface_normalization_baseline_v0_1.yaml"
)
CONTROL = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/"
    "continuity/prompt_sequence_v0_1.yaml"
)
SNAPSHOT = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/"
    "continuity/snapshots/2026-08-22__after_b1_activation_publication_v0_1.yaml"
)
VALIDATOR = ROOT / "scripts/validation/validate_continuity_roadmap_detail_surfaces_v0_1.py"
MAKEFILE = ROOT / "Makefile"


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_continuity_surface_validator_passes():
    process = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert process.returncode == 0, process.stdout
    assert "CONTINUITY_ROADMAP_DETAIL_SURFACES=PASS" in process.stdout


def test_control_preserves_authority_locator_mapping():
    data = load(CONTROL)

    assert data["status"] == "ACTIVE_CONTINUITY_CONTROL"
    assert data["authority"] == {
        "current_release": "coordination/releases/current.yaml",
        "start_here": (
            "coordination/roadmaps/details/forprint_system_blueprint/continuity/START_HERE.md"
        ),
    }


def test_snapshot_is_explicitly_historical_and_non_authoritative():
    data = load(SNAPSHOT)

    assert data["status"] == "HISTORICAL_CONTINUITY_SNAPSHOT"
    assert data["authority"] == "historical_snapshot_not_current_release_or_execution_authority"
    assert data["authoritative"] is False
    assert data["snapshot_class"] == "handoff_navigation_only"


def test_registry_contains_two_separate_continuity_strict_subclasses():
    registry = load(REGISTRY)

    roadmap_detail = next(
        item for item in registry["types"] if item["document_type"] == "roadmap_detail"
    )

    subclasses = {
        item["subclass_id"]: item
        for item in roadmap_detail.get("strict_subclasses", [])
        if isinstance(item, dict)
    }

    control = subclasses["continuity_prompt_sequence"]
    snapshot = subclasses["continuity_snapshot"]

    assert control["migration_state"] == "STRICT"
    assert snapshot["migration_state"] == "STRICT"
    assert control["schema_version"] == "forprint_blueprint_prompt_sequence_v0_1"
    assert snapshot["schema_version"] == "forprint_blueprint_continuity_snapshot_v0_1"
    assert "make continuity-surface-check" in control["validation"]
    assert "make continuity-surface-check" in snapshot["validation"]


def test_continuity_baseline_debt_is_retired_only_for_two_surfaces():
    baseline = load(BASELINE)

    debt = [
        item
        for item in baseline.get("yaml_debt", [])
        if item.get("document_type") == "roadmap_detail"
        and "/continuity/" in str(item.get("path", ""))
    ]
    assert debt == []

    other_detail_debt = []
    for debt_key in ("yaml_debt", "markdown_debt"):
        other_detail_debt.extend(
            item
            for item in baseline.get(debt_key, [])
            if item.get("document_type") == "roadmap_detail"
        )
    assert other_detail_debt == []


def test_make_check_enforces_continuity_surfaces():
    lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    check_lines = [line for line in lines if line.startswith("check-core:")]

    assert len(check_lines) == 1
    assert "roadmap-detail-check" in check_lines[0]
