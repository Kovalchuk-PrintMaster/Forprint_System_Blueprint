#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]

CONTROL = (
    ROOT
    / "coordination/roadmaps/details/forprint_system_blueprint/"
    "continuity/prompt_sequence_v0_1.yaml"
)
SNAPSHOT_ROOT = (
    ROOT
    / "coordination/roadmaps/details/forprint_system_blueprint/"
    "continuity/snapshots"
)

CONTROL_SCHEMA = "forprint_blueprint_prompt_sequence_v0_1"
SNAPSHOT_SCHEMA = "forprint_blueprint_continuity_snapshot_v0_1"

CONTROL_STATUS = "ACTIVE_CONTINUITY_CONTROL"
SNAPSHOT_STATUS = "HISTORICAL_CONTINUITY_SNAPSHOT"
SNAPSHOT_AUTHORITY = (
    "historical_snapshot_not_current_release_or_execution_authority"
)

EXPECTED_CONTROL_AUTHORITY = {
    "current_release": "coordination/releases/current.yaml",
    "start_here": (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "continuity/START_HERE.md"
    ),
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def validate_control(data: Any, issues: list[str]) -> None:
    require(
        isinstance(data, dict),
        "control root must be a mapping",
        issues,
    )
    if not isinstance(data, dict):
        return

    require(
        data.get("schema_version") == CONTROL_SCHEMA,
        "control schema drift",
        issues,
    )
    require(
        data.get("status") == CONTROL_STATUS,
        "control status drift",
        issues,
    )
    require(
        data.get("authority") == EXPECTED_CONTROL_AUTHORITY,
        "control authority locator mapping drift",
        issues,
    )
    require(
        isinstance(data.get("purpose"), str)
        and "not runtime authority" in data["purpose"].lower(),
        "control purpose must retain non-runtime-authority boundary",
        issues,
    )
    require(
        isinstance(data.get("selection_rule"), str)
        and bool(data["selection_rule"].strip()),
        "control selection_rule missing",
        issues,
    )
    require(
        isinstance(data.get("global_rules"), list)
        and bool(data["global_rules"]),
        "control global_rules missing",
        issues,
    )
    require(
        isinstance(data.get("phase_boundary_progression_policy"), dict),
        "control phase-boundary policy missing",
        issues,
    )
    require(
        isinstance(data.get("packages"), list)
        and bool(data["packages"]),
        "control package sequence missing",
        issues,
    )


def validate_snapshot(path: Path, data: Any, issues: list[str]) -> None:
    rel = path.relative_to(ROOT).as_posix()

    require(
        isinstance(data, dict),
        f"{rel}: snapshot root must be a mapping",
        issues,
    )
    if not isinstance(data, dict):
        return

    require(
        data.get("schema_version") == SNAPSHOT_SCHEMA,
        f"{rel}: snapshot schema drift",
        issues,
    )
    require(
        data.get("status") == SNAPSHOT_STATUS,
        f"{rel}: snapshot status drift",
        issues,
    )
    require(
        data.get("authority") == SNAPSHOT_AUTHORITY,
        f"{rel}: snapshot authority-class marker drift",
        issues,
    )
    require(
        data.get("authoritative") is False,
        f"{rel}: historical snapshot must remain authoritative=false",
        issues,
    )
    require(
        data.get("snapshot_class") == "handoff_navigation_only",
        f"{rel}: snapshot_class drift",
        issues,
    )
    require(
        isinstance(data.get("snapshot_at"), str)
        and bool(data["snapshot_at"].strip()),
        f"{rel}: snapshot_at missing",
        issues,
    )
    require(
        isinstance(data.get("warning"), str)
        and "revalidate git" in data["warning"].lower()
        and "coordination/releases/current.yaml" in data["warning"],
        f"{rel}: revalidation warning drift",
        issues,
    )


def main() -> int:
    issues: list[str] = []

    if not CONTROL.is_file():
        issues.append("continuity control missing")
    else:
        validate_control(load_yaml(CONTROL), issues)

    snapshots = sorted(SNAPSHOT_ROOT.glob("*.yaml"))
    if not snapshots:
        issues.append("no continuity snapshots found")

    for path in snapshots:
        validate_snapshot(path, load_yaml(path), issues)

    if issues:
        print("CONTINUITY_ROADMAP_DETAIL_SURFACES=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1

    print("CONTINUITY_ROADMAP_DETAIL_SURFACES=PASS")
    print("CONTROL_COUNT=1")
    print(f"SNAPSHOT_COUNT={len(snapshots)}")
    print(f"CONTROL_STATUS={CONTROL_STATUS}")
    print(f"SNAPSHOT_STATUS={SNAPSHOT_STATUS}")
    print("CONTROL_RELEASE_AUTHORITY=false")
    print("SNAPSHOT_RELEASE_AUTHORITY=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
