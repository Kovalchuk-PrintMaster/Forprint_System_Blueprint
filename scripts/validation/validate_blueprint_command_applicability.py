#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REGISTRY = Path(
    "coordination/standards/adoption/"
    "blueprint_command_applicability_v0_1.yaml"
)
SCHEMA = "blueprint_command_applicability_v0_1"

EXPECTED_TARGETS = {
    "prompt-prepare": False,
    "prompt-release": False,
    "prompt-status": True,
    "completion-intake-preview": True,
    "completion-intake-check": True,
    "completion-accept": True,
    "completion-return": True,
    "module-workflow-check": True,
    "standards-check": True,
    "check-report": True,
    "coordination-check": True,
    "blueprint-self-audit": True,
    "blueprint-self-status": True,
    "blueprint-self-report-full": True,
    "modules-self-status": True,
}

EXPECTED_BLOCKERS = {
    "prompt_prepare_not_implemented",
    "prompt_release_not_implemented",
    "blueprint_self_audit_not_executed",
}


def validate(root: Path) -> list[str]:
    issues: list[str] = []
    path = root / REGISTRY

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except yaml.YAMLError as error:
        return [f"{path}: invalid YAML: {error}"]

    if not isinstance(data, dict):
        return [f"{path}: YAML root must be a mapping"]
    if data.get("schema_version") != SCHEMA:
        issues.append(f"{path}: unsupported schema_version")

    profile = data.get("repository_profile")
    expected_profile = {
        "repository_id": "forprint_system_blueprint",
        "repository_class": "blueprint",
        "control_role": "blueprint_internal_control",
        "operational_readiness": "blocked",
        "self_audit_state": "ready_to_initialize",
        "external_rollout": "gated",
    }
    if not isinstance(profile, dict):
        issues.append(f"{path}: repository_profile must be a mapping")
    else:
        for key, value in expected_profile.items():
            if profile.get(key) != value:
                issues.append(
                    f"{path}: repository_profile.{key} "
                    f"must be {value!r}"
                )

    rows = data.get("commands")
    if not isinstance(rows, list):
        return [*issues, f"{path}: commands must be a list"]

    commands: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            issues.append(f"{path}: command row must be a mapping")
            continue
        command_id = row.get("command_id")
        if not isinstance(command_id, str):
            issues.append(f"{path}: command_id must be a string")
            continue
        if command_id in commands:
            issues.append(f"{path}: duplicate command_id {command_id!r}")
        commands[command_id] = row

    if set(commands) != set(EXPECTED_TARGETS):
        issues.append(f"{path}: command set is incomplete")

    target_set = set(
        re.findall(
            r"^([A-Za-z0-9_.-]+):(?:\s|$)",
            (root / "Makefile").read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )

    for command_id, expected_present in EXPECTED_TARGETS.items():
        row = commands.get(command_id, {})
        target = row.get("public_target")
        if target != command_id:
            issues.append(
                f"{path}: {command_id}.public_target "
                f"must be {command_id!r}"
            )
            continue
        if row.get("target_present") is not expected_present:
            issues.append(
                f"{path}: {command_id}.target_present "
                f"must be {expected_present!r}"
            )
        if ((target in target_set) is not expected_present):
            issues.append(
                f"{path}: actual target presence drift for {target!r}"
            )

        implementation = row.get("implementation")
        state = row.get("implementation_state")
        if state == "not_implemented":
            if implementation is not None:
                issues.append(
                    f"{path}: {command_id}.implementation must be null"
                )
        elif not isinstance(implementation, str):
            issues.append(
                f"{path}: {command_id}.implementation must be a path"
            )
        elif not (root / implementation).is_file():
            issues.append(
                f"{path}: implementation file missing: {implementation}"
            )

    prompt = commands.get("prompt-status", {})
    route = prompt.get("blueprint_route")
    if not isinstance(route, dict):
        issues.append(f"{path}: prompt-status.blueprint_route missing")
    else:
        if route.get("source") != (
            "coordination/self_coordination/prompt_queue/index.yaml"
        ):
            issues.append(
                f"{path}: prompt-status source must be self_coordination"
            )
        if route.get("external_module_queue_allowed") is not False:
            issues.append(
                f"{path}: external module queue must remain forbidden"
            )

    coordination = commands.get("coordination-check", {})
    if coordination.get("applicability") != "not_applicable":
        issues.append(
            f"{path}: coordination-check must be not_applicable"
        )
    if coordination.get("not_applicable_reason") != (
        "module_coordination_metadata_contract"
    ):
        issues.append(
            f"{path}: coordination-check reason is invalid"
        )

    result = data.get("result")
    if not isinstance(result, dict):
        issues.append(f"{path}: result must be a mapping")
    else:
        if result.get("inventory_state") != "completed":
            issues.append(f"{path}: inventory_state must be completed")
        if result.get("conformance_state") != "blocked":
            issues.append(f"{path}: conformance_state must be blocked")
        blockers = result.get("blockers")
        if not isinstance(blockers, list) or set(blockers) != EXPECTED_BLOCKERS:
            issues.append(f"{path}: blockers do not match inventory")
        if result.get("reference_pilot_migration") != "not_authorized":
            issues.append(f"{path}: pilot must remain not_authorized")
        if result.get("external_rollout") != "gated":
            issues.append(f"{path}: external rollout must remain gated")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    issues = validate(Path(args.root).resolve())
    if issues:
        print("❌ Blueprint command applicability validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Blueprint command applicability validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
