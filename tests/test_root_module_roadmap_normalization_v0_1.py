from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROADMAP_ROOT = ROOT / "coordination/roadmaps"
REGISTRY = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"
BASELINE = (
    ROOT / "coordination/internal_work/blueprint/normalization/"
    "2026-09-01__document_surface_normalization_baseline_v0_1.yaml"
)
VALIDATOR = ROOT / "scripts/validation/validate_root_module_roadmap_surfaces_v0_1.py"
MAKEFILE = ROOT / "Makefile"


def test_root_module_roadmap_surface_validator_passes():
    p = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert p.returncode == 0, p.stdout


def test_root_module_roadmap_document_type_is_strict():
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    entries = [x for x in registry["types"] if x["document_type"] == "roadmap"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["migration_state"] == "STRICT"
    assert entry["authority_class"] == "CANONICAL_PLANNING"
    assert "root-roadmap-check" in " ".join(entry["validation"])
    assert "validate_module_roadmap.py" in entry["mutation_method"]


def test_root_module_roadmap_debt_is_retired():
    baseline = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    debt = [x for x in baseline.get("yaml_debt", []) if x.get("document_type") == "roadmap"]
    assert debt == []

    strict = {
        item["document_type"]
        for item in baseline.get("strict_classes", [])
        if isinstance(item, dict)
    }
    assert "roadmap" in strict


def test_make_check_enforces_root_roadmap_surface():
    lines = MAKEFILE.read_text(encoding="utf-8").splitlines()
    check_lines = [line for line in lines if line.startswith("check-core:")]
    assert len(check_lines) == 1
    assert "root-roadmap-check" in check_lines[0]


def test_all_root_roadmaps_declare_planning_not_release_authority():
    for path in sorted(ROADMAP_ROOT.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["status"] == "active_planning_context"
        assert data["authority"] == "canonical_planning_not_release_or_execution_authority"
