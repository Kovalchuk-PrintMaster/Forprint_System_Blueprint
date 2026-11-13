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
VALIDATOR = ROOT / "scripts/validation/validate_portfolio_rebuild_seed_surfaces_v0_1.py"
MAKEFILE = ROOT / "Makefile"
SEED_ROOT = ROOT / "coordination/roadmaps/details/forprint_system_blueprint/portfolio_rebuild_seeds"


def test_portfolio_rebuild_seed_validator_passes():
    p = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert p.returncode == 0, p.stdout


def test_roadmap_detail_registry_has_strict_seed_subclass():
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    entries = [x for x in registry["types"] if x["document_type"] == "roadmap_detail"]
    assert len(entries) == 1
    entry = entries[0]
    subclasses = {
        x["subclass_id"]: x for x in entry.get("strict_subclasses", []) if isinstance(x, dict)
    }
    seed = subclasses["portfolio_rebuild_seed"]
    assert seed["migration_state"] == "STRICT"
    assert "portfolio_rebuild_seeds/*.yaml" in seed["path_pattern"]
    assert "roadmap-rebuild-seed-check" in " ".join(seed["validation"])


def test_portfolio_rebuild_seed_debt_is_retired_only_for_subclass():
    baseline = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    debt = [
        x
        for x in baseline.get("yaml_debt", [])
        if x.get("document_type") == "roadmap_detail"
        and "/portfolio_rebuild_seeds/" in str(x.get("path", ""))
    ]
    assert debt == []

    strict = {
        item["document_type"]: item
        for item in baseline.get("strict_classes", [])
        if isinstance(item, dict)
    }
    assert "roadmap_detail_portfolio_rebuild_seed" in strict


def test_roadmap_detail_debt_is_fully_retired_after_full_normalization():
    baseline = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    remaining = []
    for debt_key in ("yaml_debt", "markdown_debt"):
        remaining.extend(
            x for x in baseline.get(debt_key, []) if x.get("document_type") == "roadmap_detail"
        )
    assert remaining == []


def test_make_check_enforces_portfolio_rebuild_seed_surface():
    lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    check_lines = [line for line in lines if line.startswith("check-core:")]
    assert len(check_lines) == 1
    assert "roadmap-detail-check" in check_lines[0]


def test_seed_authority_is_non_execution_and_count_is_stable():
    paths = sorted(SEED_ROOT.glob("*.yaml"))
    assert len(paths) == 19
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["authority"] == "provisional_planning_input_not_release_or_execution_authority"
        assert len(data["steps"]) == 10
