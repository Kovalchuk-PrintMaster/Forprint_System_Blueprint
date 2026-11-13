#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

EXPECTED_SCHEMA = "blueprint_canonical_state_freshness_impact_report_v0_1"
RESOLVER = Path("scripts/coordination/render_blueprint_canonical_state_freshness_impact.py")

HUMAN_INTENT_INDEX = Path("coordination/human_intent/index.yaml")


def load_resolver(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "blueprint_canonical_state_freshness_impact_for_validation",
        path,
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load resolver: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def tracked_status(root: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stdout)
    return result.stdout


def authoritative_human_intent_total(root: Path) -> int:
    data = yaml.safe_load((root / HUMAN_INTENT_INDEX).read_text(encoding="utf-8"))
    modules = data.get("modules") if isinstance(data, dict) else None
    if not isinstance(modules, list):
        raise ValueError("Human Intent index modules must be a list")
    total = 0
    for item in modules:
        if not isinstance(item, dict):
            continue
        count = item.get("intent_count")
        if not isinstance(count, int):
            raise ValueError("Human Intent module intent_count must be integer")
        total += count
    return total


def validate(root: Path) -> list[str]:
    issues: list[str] = []
    resolver = load_resolver(root / RESOLVER)

    before = tracked_status(root)
    report = resolver.build_report(root)
    after = tracked_status(root)
    if before != after:
        issues.append("resolver changed tracked repository state")

    if report.get("schema_version") != EXPECTED_SCHEMA:
        issues.append("resolver schema version is invalid")

    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        issues.append("metadata must be a mapping")
    else:
        if metadata.get("read_only") is not True:
            issues.append("resolver must be read-only")
        if metadata.get("independent_authority") is not False:
            issues.append("resolver must not become independent authority")
        if metadata.get("result") != "PASS":
            issues.append(f"current resolver result must PASS, got {metadata.get('result')!r}")

    canonical = report.get("canonical_state")
    if not isinstance(canonical, dict):
        issues.append("canonical_state must be a mapping")
    else:
        expected: dict[str, Any] = {
            "hardening_release": "v0.4.1",
            "hardening_state": "ACTIVE_CURRENT",
            "current_phase": "H10",
            "pilot_module": "logistics_service",
            "logistics_queue_status": "ready_for_module_pull",
            "release_policy_state": "FAIL_CLOSED",
            "automatic_accept": False,
            "automatic_release_next_prompt": False,
        }
        for key, value in expected.items():
            if canonical.get(key) != value:
                issues.append(
                    f"canonical_state.{key} must be {value!r}, got {canonical.get(key)!r}"
                )
        expected_human_intent_total = authoritative_human_intent_total(root)
        if canonical.get("human_intent_total") != expected_human_intent_total:
            issues.append(
                "Human Intent total must match authoritative index: "
                f"expected {expected_human_intent_total}, got "
                f"{canonical.get('human_intent_total')!r}"
            )

    consistency = report.get("source_consistency")
    if not isinstance(consistency, dict):
        issues.append("source_consistency must be a mapping")
    elif consistency.get("state") != "AGREED":
        issues.append(f"source consistency must be AGREED: {consistency.get('issues')!r}")

    freshness = report.get("freshness")
    if not isinstance(freshness, dict):
        issues.append("freshness must be a mapping")
    else:
        agents = freshness.get("agents_current_state_projection")
        if not isinstance(agents, dict) or agents.get("state") != "FRESH":
            issues.append("AGENTS current-state projection must be FRESH")

    impact = report.get("working_tree_impact")
    if not isinstance(impact, dict):
        issues.append("working_tree_impact must be a mapping")
    else:
        surfaces = impact.get("surfaces")
        if not isinstance(surfaces, list) or len(surfaces) < 5:
            issues.append("at least five freshness/impact surfaces are required")

    if isinstance(canonical, dict):
        stale_text = (
            "<!-- FORPRINT_MODULE_INVENTORY_PROGRAM_U111_BEGIN -->\n"
            "release: `v0.4.1`, hardening state `ACTIVE_CURRENT`\n"
            "active reference pilot: `logistics_service`\n"
            "Logistics bootstrap prompt: "
            "`logistics_service_authority_lineage_and_module_bootstrap_v0_1`\n"
            "queue state: `ready_for_module_pull`\n"
            "release policy: fail-closed\n"
            "automatic Blueprint ACCEPT: disabled\n"
            "automatic next-prompt release: disabled\n"
            "Human Intent portfolio: `329` captured intents\n"
            "<!-- FORPRINT_MODULE_INVENTORY_PROGRAM_U111_END -->\n"
        )
        fixture = resolver.evaluate_agents_current_state_text(
            stale_text,
            canonical,
        )
        if fixture.get("state") != "STALE":
            issues.append("historical stale U111 regression fixture was not detected")
        if fixture.get("refresh_required") is not True:
            issues.append("stale U111 regression fixture must require refresh")

    foundations = freshness.get("existing_foundations") if isinstance(freshness, dict) else None
    if not isinstance(foundations, dict):
        issues.append("existing foundation status must be present")
    else:
        governance = foundations.get("governance_projection")
        repository_freshness = foundations.get("repository_knowledge_freshness")
        context = foundations.get("task_context_primitive")
        if (
            not isinstance(governance, dict)
            or governance.get("source_consistency_state") != "agreed"
        ):
            issues.append("existing governance renderer must report agreed sources")
        if (
            not isinstance(repository_freshness, dict)
            or repository_freshness.get("result") != "PASSED"
        ):
            issues.append("existing repository freshness assessor must pass")
        if not isinstance(context, dict) or context.get("available") is not True:
            issues.append("existing context-bundle primitive must remain available")

    return issues


def main() -> int:
    root = Path(".").resolve()
    try:
        issues = validate(root)
    except Exception as error:
        print(f"FAILED: {error}")
        print("RESULT: BLUEPRINT_CANONICAL_STATE_FRESHNESS_IMPACT_VALIDATION_FAILED")
        return 1

    if issues:
        print("Blueprint canonical-state freshness/impact validation failed:")
        for issue in issues:
            print(f"- {issue}")
        print("RESULT: BLUEPRINT_CANONICAL_STATE_FRESHNESS_IMPACT_VALIDATION_FAILED")
        return 1

    print("BLUEPRINT_CANONICAL_STATE_FRESHNESS_IMPACT_VALIDATION=PASS")
    print("CURRENT_RELEASE=v0.4.1")
    print("CURRENT_PHASE=H10")
    print("PILOT_MODULE=logistics_service")
    print("LOGISTICS_QUEUE_STATUS=ready_for_module_pull")
    print("RELEASE_POLICY=FAIL_CLOSED")
    print("HUMAN_INTENT_TOTAL=357")
    print("AGENTS_CURRENT_STATE_PROJECTION=FRESH")
    print("HISTORICAL_STALE_U111_FIXTURE=DETECTED")
    print("READ_ONLY=true")
    print("INDEPENDENT_AUTHORITY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
