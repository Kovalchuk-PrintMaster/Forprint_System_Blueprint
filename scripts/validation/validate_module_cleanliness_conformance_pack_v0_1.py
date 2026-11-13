#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "module_cleanliness_conformance_pack_v0_1.yaml"
)
PORTFOLIO = (
    ROOT
    / "coordination/internal_work/blueprint/cleanliness/"
    "module_cleanliness_conformance_portfolio_v0_1.yaml"
)

REQUIRED_COMPONENTS = {
    "repository_asset_classification",
    "canonical_source_generator_relationships",
    "generated_drift_detection",
    "validator_registry",
    "cleanliness_debt_baseline",
    "orphan_asset_detection",
    "temporary_and_root_clutter_detection",
    "duplicate_helper_and_semantic_candidate_detection",
    "naming_schema_version_conformance",
    "safe_mutation_path",
    "asset_lifecycle_and_retirement",
    "skipped_test_inventory_when_applicable",
    "normal_cleanliness_check_command",
}
ALLOWED_STATES = {
    "IMPLEMENTED_BLUEPRINT_REFERENCE",
    "REQUIRED_PLANNED_NOT_STARTED",
    "LOCAL_IMPLEMENTATION_IN_PROGRESS",
    "READY_FOR_CONFORMANCE_REVIEW",
    "CONFORMANT",
    "BLOCKED",
}


def fail(message: str) -> None:
    print("MODULE_CLEANLINESS_CONFORMANCE_PACK_VALIDATION=FAIL")
    print("ERROR=" + message)
    raise SystemExit(1)


def main() -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    portfolio = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))

    if policy.get("status") != "ACTIVE":
        fail("POLICY_NOT_ACTIVE")
    if policy.get("authority") != "BLUEPRINT_CLEANLINESS_GOVERNANCE":
        fail("POLICY_AUTHORITY")

    components = policy.get("required_components", [])
    component_ids = {
        item.get("component_id")
        for item in components
        if isinstance(item, dict)
    }
    if component_ids != REQUIRED_COMPONENTS:
        fail(
            "REQUIRED_COMPONENT_SET_DRIFT:"
            f"actual={sorted(component_ids)}:"
            f"expected={sorted(REQUIRED_COMPONENTS)}"
        )

    gates = policy.get("gates", {})
    if gates.get("assistant_distribution_allowed_now") is not False:
        fail("ASSISTANT_DISTRIBUTION_GATE_OPEN")
    if gates.get("module_implementation_allowed_now") is not False:
        fail("MODULE_IMPLEMENTATION_GATE_OPEN")
    if gates.get("future_distribution_requires_local_pack") is not True:
        fail("FUTURE_DISTRIBUTION_REQUIREMENT_MISSING")

    if portfolio.get("assistant_distribution_allowed") is not False:
        fail("PORTFOLIO_DISTRIBUTION_GATE_OPEN")
    if portfolio.get("module_implementation_allowed") is not False:
        fail("PORTFOLIO_IMPLEMENTATION_GATE_OPEN")

    modules = portfolio.get("modules", [])
    if not isinstance(modules, list):
        fail("MODULES_NOT_LIST")
    if len(modules) != 23:
        fail(f"CANONICAL_MODULE_COUNT:{len(modules)}")

    module_ids = [item.get("module_id") for item in modules]
    if len(set(module_ids)) != 23:
        fail("DUPLICATE_MODULE_ID")
    if "forprint_system_blueprint" not in module_ids:
        fail("BLUEPRINT_MODULE_MISSING")

    blueprint = next(
        item for item in modules
        if item["module_id"] == "forprint_system_blueprint"
    )
    if blueprint.get("conformance_state") != "IMPLEMENTED_BLUEPRINT_REFERENCE":
        fail("BLUEPRINT_REFERENCE_NOT_IMPLEMENTED")

    planned = 0
    for item in modules:
        state = item.get("conformance_state")
        if state not in ALLOWED_STATES:
            fail("UNKNOWN_CONFORMANCE_STATE:" + str(state))
        if item.get("local_pack_required") is not True:
            fail("LOCAL_PACK_NOT_REQUIRED:" + str(item.get("module_id")))
        if item.get("implementation_allowed_now") is not False:
            fail("MODULE_IMPLEMENTATION_ALLOWED:" + str(item.get("module_id")))
        if item["module_id"] != "forprint_system_blueprint":
            if state != "REQUIRED_PLANNED_NOT_STARTED":
                fail(
                    "NON_BLUEPRINT_PREMATURE_STATE:"
                    + item["module_id"]
                    + ":"
                    + str(state)
                )
            planned += 1

    expected_hash = hashlib.sha256(
        "\n".join(sorted(module_ids)).encode("utf-8")
    ).hexdigest()
    if portfolio.get("canonical_module_set_sha256") != expected_hash:
        fail("CANONICAL_MODULE_SET_HASH_DRIFT")

    summary = portfolio.get("summary", {})
    if summary.get("canonical_module_count") != 23:
        fail("SUMMARY_CANONICAL_COUNT")
    if summary.get("implemented_blueprint_reference_count") != 1:
        fail("SUMMARY_BLUEPRINT_COUNT")
    if summary.get("required_planned_not_started_count") != planned:
        fail("SUMMARY_PLANNED_COUNT")

    print("MODULE_CLEANLINESS_CONFORMANCE_PACK_VALIDATION=PASS")
    print("REQUIRED_COMPONENT_COUNT=13")
    print("CANONICAL_MODULE_COUNT=23")
    print("IMPLEMENTED_BLUEPRINT_REFERENCE_COUNT=1")
    print(f"REQUIRED_PLANNED_NOT_STARTED_COUNT={planned}")
    print("FUTURE_DISTRIBUTION_REQUIRES_LOCAL_PACK=true")
    print("ASSISTANT_DISTRIBUTION_ALLOWED=false")
    print("MODULE_IMPLEMENTATION_ALLOWED=false")


if __name__ == "__main__":
    main()
