#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from read_blueprint_standards import (
    resolve_blueprint_dir,
    standards_summary,
    validate_standards_visibility,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Blueprint standards visibility from a ForPrint module.")
    parser.add_argument("--blueprint-dir", default=None)
    parser.add_argument("--module-root", default=".")
    args = parser.parse_args()

    blueprint_dir = resolve_blueprint_dir(args.blueprint_dir)
    module_root = Path(args.module_root).resolve()

    issues = validate_standards_visibility(blueprint_dir)
    summary = standards_summary(blueprint_dir)
    policy = summary.get("policy", {})
    if not isinstance(policy, dict):
        policy = {}

    if not module_root.exists():
        issues.append(f"{module_root}: module root does not exist")
    if policy.get("advisory_by_default") is not True:
        issues.append("Blueprint standards must be advisory by default")
    if policy.get("not_active_prompt") is not True:
        issues.append("Blueprint standards must not be treated as active prompts by default")
    if policy.get("hard_enforcement_requires_prompt_or_directive") is not True:
        issues.append("Hard enforcement must require explicit prompt or directive")

    if issues:
        print("❌ Blueprint standards visibility check failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Blueprint standards visibility check passed")
    print(f"Blueprint: {blueprint_dir}")
    print(f"Module root: {module_root}")
    print(f"Standards count: {summary.get('standards_count', 0)}")
    print("Semantics: advisory / gradual alignment unless activated by prompt or directive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
