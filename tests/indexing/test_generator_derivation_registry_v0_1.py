from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/registry/generator_derivation_registry_v0_1.yaml"
INVENTORY = ROOT / "indexes/generator_inventory.yaml"


def test_inventory_is_non_authoritative_and_working_tree_scoped() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    assert data["status"] == "derived_non_authoritative"
    assert data["authority"] == "none"
    assert data["source_scope"] == "current_working_tree_python_scripts"
    assert data["summary"]["generator_candidate_count"] > 0
    assert data["summary"]["tracked_candidate_count"] >= 0
    assert data["summary"]["untracked_candidate_count"] >= 0
    assert all("git_state" in row for row in data["generator_candidates"])
    assert all("sha256" in row for row in data["generator_candidates"])


def test_hardened_tracked_output_generators_have_native_exact_checks() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    by_script = {row["script"]: row for row in data["generators"]}
    for script in (
        "scripts/generate_mermaid.py",
        "scripts/generate_module_guides.py",
    ):
        row = by_script[script]
        assert row["output_state"] == "tracked_derived"
        assert row["check_mode"] == "native_exact_check"
        assert row["make_check_allowed"] is True


def test_registered_generated_outputs_claim_no_authority() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert all(row["authority"] == "none" for row in data["generators"])


def test_critical_project_context_generator_is_visible_even_if_untracked() -> None:
    data = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    by_script = {row["script"]: row for row in data["generator_candidates"]}
    row = by_script["scripts/coordination/build_project_context_archive.py"]
    assert row["registry_state"] == "registered"
    assert row["git_state"] in {
        "tracked_clean",
        "tracked_modified",
        "untracked",
    }


def test_inventory_check_and_registry_validator_pass() -> None:
    commands = (
        [sys.executable, "scripts/indexing/build_generator_inventory.py", "--check"],
        [sys.executable, "scripts/indexing/validate_generator_derivation_registry.py"],
    )
    for command in commands:
        cp = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        assert cp.returncode == 0, cp.stdout


def test_make_exposes_generator_foundation_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert ".PHONY: generator-inventory-check" in makefile
    assert "build_generator_inventory.py --check" in makefile
    assert ".PHONY: generator-contract-check" in makefile
    assert "validate_generator_derivation_registry.py" in makefile
