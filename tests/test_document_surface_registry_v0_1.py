from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (
    ROOT
    / "coordination/standards/governance/document_type_registry_v0_1.yaml"
)



def test_document_surface_registry_validator() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validation/validate_document_surface_registry_v0_1.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    assert "DOCUMENT_SURFACE_REGISTRY_VALIDATION=PASS" in result.stdout

# strict-subclass-dispatch-regression-v0-1
def test_document_surface_path_matching_respects_directory_boundaries():
    from scripts.validation.validate_document_surface_registry_v0_1 import match

    root = "coordination/roadmaps/forprint_library.yaml"
    nested = (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "portfolio_rebuild_seeds/calculator_engine.yaml"
    )

    assert match(
        "coordination/roadmaps/*.yaml",
        root,
    )

    assert not match(
        "coordination/roadmaps/*.yaml",
        nested,
    )

    assert match(
        "coordination/roadmaps/details/**/*",
        nested,
    )

    assert match(
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "portfolio_rebuild_seeds/*.yaml",
        nested,
    )


def test_document_surface_strict_subclass_profile_overrides_parent():
    from scripts.validation.validate_document_surface_registry_v0_1 import (
        effective_profile,
    )

    registry = yaml.safe_load(
        REGISTRY.read_text(
            encoding="utf-8",
        )
    )

    parent = next(
        item
        for item in registry["types"]
        if item["document_type"] == "roadmap_detail"
    )

    rel = (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "portfolio_rebuild_seeds/calculator_engine.yaml"
    )

    profile = effective_profile(
        parent,
        rel,
    )

    assert profile["subclass_id"] == "portfolio_rebuild_seed"
    assert profile["format"] == "yaml"
    assert (
        profile["schema_version"]
        == "forprint_portfolio_roadmap_rebuild_seed_v0_1"
    )

    assert profile["required_top_level"] == [
        "schema_version",
        "module_id",
        "role_summary",
        "status",
        "authority",
        "source_action",
        "steps",
    ]


def test_document_surface_nonmatching_detail_keeps_parent_profile():
    from scripts.validation.validate_document_surface_registry_v0_1 import (
        effective_profile,
    )

    registry = yaml.safe_load(
        REGISTRY.read_text(
            encoding="utf-8",
        )
    )

    parent = next(
        item
        for item in registry["types"]
        if item["document_type"] == "roadmap_detail"
    )

    rel = (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "future_unclassified_example.yaml"
    )

    profile = effective_profile(
        parent,
        rel,
    )

    assert "subclass_id" not in profile
    assert profile["document_type"] == "roadmap_detail"

def test_document_surface_knowledge_foundation_resolves_to_strict_subclass():
    from scripts.validation.validate_document_surface_registry_v0_1 import (
        effective_profile,
    )

    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    parent = next(
        item
        for item in registry["types"]
        if item["document_type"] == "roadmap_detail"
    )

    rel = (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "knowledge_foundation_program_v0_1.yaml"
    )
    profile = effective_profile(parent, rel)

    assert profile["subclass_id"] == "knowledge_foundation_program"
    assert profile["migration_state"] == "STRICT"

