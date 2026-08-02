from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.forprint_coordination_tools.metadata import (  # noqa: E402
    CoordinationIssue,
    check_module_coordination_metadata,
)

BLUEPRINT_MANIFEST = Path(
    "coordination/modules/forprint_system_blueprint/"
    "module_workflow_manifest.yaml"
)


def print_issue(item: CoordinationIssue) -> None:
    print(
        f"{item.severity}: {item.code}: "
        f"{item.path}: {item.message}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate ForPrint module coordination metadata "
            "with repository-class applicability."
        )
    )
    parser.add_argument("--module-root", default=".")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def _load_mapping(path: Path) -> dict[str, Any] | None:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return loaded if isinstance(loaded, dict) else None


def is_blueprint_root(root: Path) -> bool:
    manifest = _load_mapping(root.resolve() / BLUEPRINT_MANIFEST)
    return bool(
        manifest
        and manifest.get("module_id") == "forprint_system_blueprint"
        and manifest.get("control_role")
        == "blueprint_internal_control"
    )


def main() -> int:
    args = parse_args()
    root = Path(args.module_root).resolve()

    if is_blueprint_root(root):
        print("ForPrint coordination metadata check")
        print(f"Repository root: {root}")
        print("Repository class: blueprint")
        print("Applicability: NOT_APPLICABLE")
        print("Reason: module_coordination_metadata_contract")
        print("Blueprint source: coordination/self_coordination/")
        print("RESULT: N/A")
        return 0

    result = check_module_coordination_metadata(root)
    print("ForPrint coordination metadata check")
    print(f"Module root: {result.module_root}")
    print("Repository class: module")
    print("Applicability: APPLICABLE")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")

    if result.errors:
        print("\nErrors:")
        for item in result.errors:
            print_issue(item)

    if result.warnings:
        print("\nWarnings:")
        for item in result.warnings:
            print_issue(item)

    if result.ok and (not args.strict or not result.warnings):
        print("\n✅ Coordination metadata check passed")
        print("RESULT: OK")
        return 0

    print("\n❌ Coordination metadata check failed")
    print("RESULT: FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
