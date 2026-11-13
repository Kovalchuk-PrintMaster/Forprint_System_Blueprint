from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_make_default_is_blueprint_and_explicit_override_is_preserved() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    target = text.split(".PHONY: assistant-context-pack", maxsplit=1)[1].split(
        ".PHONY:", maxsplit=1
    )[0]
    assert 'module="forprint_system_blueprint"' in target
    assert '"$(origin MODULE)" = "command line"' in target
    assert 'set -- "$$@" --module "$$module"' in target


def test_system_specs_and_operating_context_are_default_navigation() -> None:
    spec_path = ROOT / "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    assert spec["authority"] == "none_navigation_only"
    assert (
        spec["context_pack_contract"]["default_module_without_explicit_MODULE"]
        == "forprint_system_blueprint"
    )
    assert spec["source_processing"]["master_memory_is_navigation_not_authority"] is True
    assert spec["source_processing"]["bulk_promotion_from_master_memory_forbidden"] is True

    index = yaml.safe_load(
        (ROOT / "coordination/bootstrap/index_v0_1.yaml").read_text(encoding="utf-8")
    )
    assert "assistant_operating_context" in index["default_topics"]
    assert index["reading_order"][0] == (
        "coordination/instruction_intake/assistant_reading_order.md"
    )
    assert index["reading_order"][1] == (
        "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"
    )

    reading_order = (
        ROOT / "coordination/instruction_intake/assistant_reading_order.md"
    ).read_text(encoding="utf-8")
    assert (
        "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"
        in reading_order
    )
    sources = {
        row["path"]
        for row in index["topics"]["assistant_operating_context"]["sources"]
    }
    required = {
        "coordination/instruction_intake/assistant_reading_order.md",
        "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml",
        "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml",
        "coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md",
        "coordination/repository_knowledge/roadmap_enrichment/README.md",
        "coordination/repository_knowledge/roadmap_enrichment/source_map.yaml",
        "coordination/human_intent/modules/forprint_system_blueprint.yaml",
        "coordination/repository_knowledge/dialogue_master_memory/2026-09-21_v3_7/00_intake_manifest_v0_1.yaml",
    }
    assert required.issubset(sources)
