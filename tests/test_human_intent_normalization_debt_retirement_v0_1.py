from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"
BASELINE = (
    ROOT / "coordination/internal_work/blueprint/normalization/"
    "2026-09-01__document_surface_normalization_baseline_v0_1.yaml"
)
MAKEFILE = ROOT / "Makefile"

STRICT_TYPES = {"human_intent_module_ledger", "human_intent_delta"}


def _type_map():
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    return {entry["document_type"]: entry for entry in data["types"]}


def test_human_intent_document_types_are_strict_and_registered_to_shared_tools():
    types = _type_map()

    module_ledger = types["human_intent_module_ledger"]
    assert module_ledger["migration_state"] == "STRICT"
    assert "human_intent_mutation_v0_1.py" in module_ledger["mutation_method"]
    assert "make human-intent-check" in module_ledger["validation"]

    delta = types["human_intent_delta"]
    assert delta["migration_state"] == "STRICT"
    assert "controlled dated Human Intent Delta" in delta["mutation_method"]
    assert "validate_human_intent_surfaces_v0_1.py" in delta["mutation_method"]
    assert "make human-intent-check" in delta["validation"]


def test_human_intent_debt_is_retired_from_normalization_baseline():
    baseline = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    debt = baseline.get("yaml_debt", [])
    assert not [item for item in debt if item.get("document_type") in STRICT_TYPES]

    strict = {
        item["document_type"]
        for item in baseline.get("strict_classes", [])
        if isinstance(item, dict)
    }
    assert STRICT_TYPES <= strict


def test_make_check_persistently_enforces_normalization_and_human_intent():
    text = MAKEFILE.read_text(encoding="utf-8")
    check_lines = [line for line in text.splitlines() if line.startswith("check-core:")]
    assert len(check_lines) == 1
    assert "surface-normalization-check" in check_lines[0]
    assert "human-intent-check" in check_lines[0]
