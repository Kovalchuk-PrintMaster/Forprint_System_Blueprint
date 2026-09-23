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
DETAIL_ROOT = ROOT / "coordination/roadmaps/details/forprint_system_blueprint"
VALIDATOR = ROOT / "scripts/validation/validate_roadmap_detail_surfaces_v0_2.py"
MAKEFILE = ROOT / "Makefile"


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_full_roadmap_detail_validator_passes():
    process = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert process.returncode == 0, process.stdout
    assert "ROADMAP_DETAIL_SURFACES=PASS" in process.stdout


def test_roadmap_detail_parent_is_strict_and_debt_free():
    registry = load(REGISTRY)
    roadmap_detail = next(
        item for item in registry["types"] if item["document_type"] == "roadmap_detail"
    )
    assert roadmap_detail["migration_state"] == "STRICT"
    assert "make roadmap-detail-check" in roadmap_detail["validation"]

    baseline = load(BASELINE)
    remaining = []
    for debt_key in ("yaml_debt", "markdown_debt"):
        remaining.extend(
            item
            for item in baseline.get(debt_key, [])
            if item.get("document_type") == "roadmap_detail"
        )
    assert remaining == []


def test_all_roadmap_detail_yaml_resolves_to_strict_subclass():
    from scripts.validation.validate_document_surface_registry_v0_1 import (
        effective_profile,
    )

    registry = load(REGISTRY)
    roadmap_detail = next(
        item for item in registry["types"] if item["document_type"] == "roadmap_detail"
    )

    paths = sorted(DETAIL_ROOT.rglob("*.yaml"))
    assert paths

    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        profile = effective_profile(roadmap_detail, rel)
        assert profile.get("subclass_id"), rel
        assert profile["migration_state"] == "STRICT", rel


def test_all_roadmap_detail_markdown_has_one_h1():
    paths = sorted(DETAIL_ROOT.rglob("*.md"))
    assert paths

    for path in paths:
        h1_count = sum(
            1
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("# ") and not line.startswith("## ")
        )
        assert h1_count == 1, path.relative_to(ROOT)


def test_projection_uses_proposed_status_not_synthetic_status():
    yaml_path = DETAIL_ROOT / "portfolio_full_horizon_target_states_v0_1.yaml"
    md_path = DETAIL_ROOT / "portfolio_full_horizon_target_states_v0_1.md"

    data = load(yaml_path)
    assert data["status"] == "PROPOSED_PORTFOLIO_BASELINE_REQUIRES_OWNER_REVIEW"
    assert "Status: `PROPOSED_PORTFOLIO_BASELINE_REQUIRES_OWNER_REVIEW`" in md_path.read_text(
        encoding="utf-8"
    )


def test_first_pass_status_map_uses_schema_version_only():
    path = (
        DETAIL_ROOT / "portfolio_rebuild_inputs/2026-08-28__first_pass_module_status_map_v0_1.yaml"
    )
    data = load(path)

    assert data["schema_version"] == "forprint_portfolio_first_pass_status_map_v0_1"
    assert "schema" not in data
    assert data["authority"] == "planning_input_not_release_or_execution_authority"


def test_make_check_uses_roadmap_detail_umbrella():
    lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    check_lines = [line for line in lines if line.startswith("check-core:")]
    assert len(check_lines) == 1
    assert "roadmap-detail-check" in check_lines[0]
