#!/usr/bin/env python3
"""Explain a registered execution target and its dependency edges."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    artifacts = {row["id"]: row for row in data.get("artifacts", [])}
    targets = {row["target"]: row for row in data.get("targets", [])}

    target = targets.get(args.target)
    if target is None:
        print(f"EXECUTION_DEPENDENCY_EXPLAIN=FAIL unknown_target={args.target}")
        return 1

    print(f"TARGET={args.target}")
    print("REQUIRES:")
    if not target["requires"]:
        print("  - none")
    for artifact_id in target["requires"]:
        artifact = artifacts[artifact_id]
        print(f"  - artifact: {artifact_id}")
        print(f"    path: {artifact['path']}")
        print(f"    class: {artifact['class']}")
        print(f"    producer: {artifact.get('producer')}")
        print(f"    freshness: {artifact['freshness']}")
        print(f"    missing_behavior: {artifact['missing_behavior']}")

    print("PRODUCES:")
    if not target["produces"]:
        print("  - none")
    for artifact_id in target["produces"]:
        artifact = artifacts[artifact_id]
        print(f"  - artifact: {artifact_id}")
        print(f"    path: {artifact['path']}")
        print(f"    authority: {artifact['authority']}")
        print(f"    lifecycle: {artifact['lifecycle']}")

    print("OPTIONAL_OBSERVES:")
    if not target["optional_observes"]:
        print("  - none")
    for artifact_id in target["optional_observes"]:
        artifact = artifacts[artifact_id]
        print(f"  - artifact: {artifact_id}")
        print(f"    path: {artifact['path']}")
        print(f"    class: {artifact['class']}")
        print(f"    missing_behavior: {artifact['missing_behavior']}")

    print("REQUIRES_TOOLS=" + ",".join(target["requires_tools"]))
    print("SIDE_EFFECT_SCOPE:")
    if not target["side_effect_scope"]:
        print("  - none")
    for path in target["side_effect_scope"]:
        print(f"  - {path}")

    print("EXECUTION_DEPENDENCY_EXPLAIN=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
