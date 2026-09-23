#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA = Path(
    "coordination/internal_work/blueprint/module_inventory/"
    "2026-09-06__module_memory_schema_v0_1.yaml"
)
LOGISTICS_LINEAGE = Path(
    "coordination/internal_work/blueprint/module_inventory/logistics_service/"
    "2026-09-05__logistics_service__implementation_lineage_baseline_v0_1.yaml"
)

EXPECTED_SECTIONS = {
    "identity",
    "purpose_and_provenance",
    "classification",
    "semantic_binding",
    "lifecycle",
    "lineage",
    "interfaces",
    "relationships",
    "evidence",
    "roadmap",
    "retirement",
    "freshness",
    "unknowns",
}
EXPECTED_SCOPE = {"S0", "S1", "S2", "S3", "S4"}
EXPECTED_CRITICALITY = {"C0", "C1", "C2", "C3", "C4"}
EXPECTED_MATURITY = {
    "LOCAL",
    "OBSERVED",
    "PROVISIONAL",
    "RECOMMENDED",
    "CANONICAL",
    "DEPRECATED",
    "RETIRED",
}
EXPECTED_MIGRATION = {
    "KEEP",
    "MAP_ONLY",
    "MIGRATE_ON_TOUCH",
    "ROADMAP_REQUIRED",
    "MIGRATION_REQUIRED",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def resolve_field_path(schema: dict[str, Any], field_path: str) -> bool:
    section_name, _, field_name = field_path.partition(".")
    sections = schema["record_contract"]["sections"]
    section = sections.get(section_name)
    if not isinstance(section, dict):
        return False
    required = section.get("required_fields")
    return isinstance(required, list) and field_name in required


def validate(root: Path) -> list[str]:
    issues: list[str] = []
    schema = load_yaml(root / SCHEMA)

    if schema.get("schema_version") != "forprint_module_memory_schema_v0_1":
        issues.append("schema_version is invalid")

    contract = schema.get("record_contract")
    if not isinstance(contract, dict):
        return issues + ["record_contract must be a mapping"]

    required_sections = contract.get("required_sections")
    if not isinstance(required_sections, list):
        issues.append("record_contract.required_sections must be a list")
    elif set(required_sections) != EXPECTED_SECTIONS:
        issues.append("required Module Memory sections do not match v0.1 contract")

    sections = contract.get("sections")
    if not isinstance(sections, dict):
        issues.append("record_contract.sections must be a mapping")
    else:
        for name in EXPECTED_SECTIONS:
            section = sections.get(name)
            if not isinstance(section, dict):
                issues.append(f"missing section contract: {name}")
                continue
            fields = section.get("required_fields")
            if not isinstance(fields, list) or not fields:
                issues.append(f"section {name} has no required_fields")

    enums = schema.get("enums")
    if not isinstance(enums, dict):
        issues.append("enums must be a mapping")
    else:
        scope = enums.get("interaction_scope")
        if not isinstance(scope, dict) or set(scope) != EXPECTED_SCOPE:
            issues.append("interaction_scope must define S0 through S4")
        criticality = enums.get("criticality")
        if not isinstance(criticality, dict) or set(criticality) != EXPECTED_CRITICALITY:
            issues.append("criticality must define C0 through C4")
        maturity = enums.get("standardization_maturity")
        if not isinstance(maturity, list) or set(maturity) != EXPECTED_MATURITY:
            issues.append("standardization_maturity values are incomplete")
        migration = enums.get("migration_mode")
        if not isinstance(migration, list) or set(migration) != EXPECTED_MIGRATION:
            issues.append("migration_mode values are incomplete")

    provenance = (
        sections.get("purpose_and_provenance", {})
        .get("unknown_legacy_rule", {})
        if isinstance(sections, dict)
        else {}
    )
    if provenance.get("purpose") != "UNKNOWN_LEGACY":
        issues.append("unknown legacy purpose must remain UNKNOWN_LEGACY")
    if provenance.get("review_required") is not True:
        issues.append("unknown legacy provenance must require review")

    bindings = schema.get("source_bindings")
    if not isinstance(bindings, list) or len(bindings) < 4:
        issues.append("source_bindings must preserve existing inventory primitives")
    else:
        binding_ids = set()
        for binding in bindings:
            if not isinstance(binding, dict):
                issues.append("source binding must be a mapping")
                continue
            binding_id = binding.get("binding_id")
            path = binding.get("path")
            if isinstance(binding_id, str):
                binding_ids.add(binding_id)
            if not isinstance(path, str) or not (root / path).exists():
                issues.append(f"source binding path does not resolve: {path!r}")
            if binding.get("must_not_be_replaced") is not True:
                issues.append(f"source binding must be preserved: {binding_id}")
        expected_bindings = {
            "repository_capability_inventory",
            "module_current_state_evidence",
            "module_cleanliness_conformance",
            "implementation_lineage",
        }
        if not expected_bindings.issubset(binding_ids):
            issues.append("existing inventory/current-state/cleanliness/lineage bindings are incomplete")

    lineage = load_yaml(root / LOGISTICS_LINEAGE)
    future_fields = lineage.get("future_minimum_registry_fields")
    mapping = (
        schema.get("compatibility_mapping", {})
        .get("logistics_lineage_future_fields", {})
    )
    if not isinstance(future_fields, list):
        issues.append("Logistics future_minimum_registry_fields must be a list")
    elif not isinstance(mapping, dict):
        issues.append("Logistics lineage compatibility mapping must be a mapping")
    else:
        missing = sorted(set(future_fields) - set(mapping))
        if missing:
            issues.append(
                "Module Memory does not map Logistics future lineage fields: "
                + ", ".join(missing)
            )
        for field_name, target in mapping.items():
            if not isinstance(target, str) or not resolve_field_path(schema, target):
                issues.append(
                    f"Logistics lineage field {field_name} maps to invalid target {target!r}"
                )

    adoption = schema.get("adoption_policy")
    if not isinstance(adoption, dict):
        issues.append("adoption_policy must be a mapping")
    else:
        if adoption.get("initial_reference_module") != "logistics_service":
            issues.append("Logistics must remain the initial reference module")
        if adoption.get("full_portfolio_backfill_required_before_logistics_prompt_1") is not False:
            issues.append("full portfolio backfill must not block Logistics prompt 1")

    return issues


def main() -> int:
    root = Path(".").resolve()
    try:
        issues = validate(root)
    except Exception as error:
        print(f"FAILED: {error}")
        print("RESULT: MODULE_MEMORY_SCHEMA_VALIDATION_FAILED")
        return 1

    if issues:
        print("Module Memory schema validation failed:")
        for issue in issues:
            print(f"- {issue}")
        print("RESULT: MODULE_MEMORY_SCHEMA_VALIDATION_FAILED")
        return 1

    print("MODULE_MEMORY_SCHEMA_VALIDATION=PASS")
    print("SCHEMA_VERSION=forprint_module_memory_schema_v0_1")
    print("SOURCE_BINDINGS=RCI,CURRENT_STATE,CLEANLINESS,LINEAGE")
    print("LOGISTICS_FUTURE_LINEAGE_MAPPING=PASS")
    print("UNKNOWN_LEGACY_PROVENANCE_INVENTION_ALLOWED=false")
    print("FULL_PORTFOLIO_BACKFILL_BLOCKS_LOGISTICS_PROMPT_1=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
