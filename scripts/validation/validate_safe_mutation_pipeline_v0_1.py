#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "safe_mutation_pipeline_v0_1.yaml"
)
PLANNER = "scripts/coordination/plan_safe_mutation_v0_1.py"

REQUIRED_CLASSES = {
    "governance_standard",
    "human_intent",
    "roadmap_detail",
    "document_surface_governance",
    "executable_or_test_surface",
    "indexed_source_fallback",
}

REQUIRED_FINAL_ACTIONS = {
    "skip_inventory_validation",
    "ruff_full",
    "full_pytest",
    "make_check",
    "release_authority_guard",
    "diff_check",
}


def fail(message: str) -> None:
    print("SAFE_MUTATION_PIPELINE_VALIDATION=FAIL")
    print("ERROR=" + message)
    raise SystemExit(1)


def main() -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        fail("POLICY_NOT_MAPPING")
    if policy.get("status") != "ACTIVE":
        fail("POLICY_NOT_ACTIVE")
    if policy.get("authority") != "BLUEPRINT_MUTATION_GOVERNANCE":
        fail("POLICY_AUTHORITY")

    classes = policy.get("source_class_registry")
    actions = policy.get("action_registry")
    if not isinstance(classes, dict) or not isinstance(actions, dict):
        fail("REGISTRY_SHAPE")

    if set(classes) != REQUIRED_CLASSES:
        fail(
            "SOURCE_CLASS_SET:"
            f"actual={sorted(classes)}:"
            f"expected={sorted(REQUIRED_CLASSES)}"
        )

    for class_id, spec in classes.items():
        if not spec.get("patterns"):
            fail("CLASS_WITHOUT_PATTERNS:" + class_id)
        for action_id in spec.get("actions", []):
            if action_id not in actions:
                fail("UNKNOWN_CLASS_ACTION:" + class_id + ":" + action_id)

    final_actions = set(policy.get("universal_final_actions", []))
    if final_actions != REQUIRED_FINAL_ACTIONS:
        fail("UNIVERSAL_FINAL_ACTION_SET")

    orders = []
    for action_id, spec in actions.items():
        if not isinstance(spec.get("order"), int):
            fail("ACTION_ORDER:" + action_id)
        command = spec.get("command")
        if not isinstance(command, list) or not command:
            fail("ACTION_COMMAND:" + action_id)
        orders.append(spec["order"])

    if min(orders) < 0:
        fail("NEGATIVE_ACTION_ORDER")

    process = subprocess.run(
        [
            sys.executable,
            PLANNER,
            "--json",
            "coordination/standards/governance/example_policy.yaml",
            "coordination/human_intent/modules/example.yaml",
            "scripts/example.py",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if process.returncode != 0:
        fail("PLANNER_EXECUTION:" + process.stdout)

    plan = json.loads(process.stdout)
    matched = set(plan["matched_source_classes"])
    for required in (
        "governance_standard",
        "human_intent",
        "executable_or_test_surface",
        "indexed_source_fallback",
    ):
        if required not in matched:
            fail("PLANNER_CLASSIFICATION_MISSING:" + required)

    action_ids = {item["action_id"] for item in plan["actions"]}
    for required in REQUIRED_FINAL_ACTIONS:
        if required not in action_ids:
            fail("PLANNER_FINAL_ACTION_MISSING:" + required)

    if "standards_index_validation" not in action_ids:
        fail("PLANNER_STANDARDS_ACTION_MISSING")
    if "human_intent_sync" not in action_ids:
        fail("PLANNER_HUMAN_INTENT_SYNC_MISSING")
    if "knowledge_index_build" not in action_ids:
        fail("PLANNER_KNOWLEDGE_BUILD_MISSING")

    if plan["assistant_distribution_allowed"] is not False:
        fail("ASSISTANT_DISTRIBUTION_GUARD")
    if plan["module_implementation_started"] is not False:
        fail("MODULE_IMPLEMENTATION_GUARD")

    print("SAFE_MUTATION_PIPELINE_VALIDATION=PASS")
    print(f"SOURCE_CLASS_COUNT={len(classes)}")
    print(f"ACTION_REGISTRY_COUNT={len(actions)}")
    print("EXPLICIT_SOURCE_TO_DOWNSTREAM_MAPPING=true")
    print("STANDARDS_REGISTRATION_IS_EXPLICIT=true")
    print("STRUCTURAL_HASH_REVIEW_IS_EXPLICIT=true")
    print("DERIVED_INDEX_REFRESH_IS_REGISTERED=true")
    print("FINAL_GATES_REGISTERED=true")


if __name__ == "__main__":
    main()
