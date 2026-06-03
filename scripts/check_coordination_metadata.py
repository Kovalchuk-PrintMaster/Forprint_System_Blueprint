from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.forprint_coordination_tools.metadata import (  # noqa: E402
    CoordinationIssue,
    check_module_coordination_metadata,
)


def print_issue(item: CoordinationIssue) -> None:
    print(f"{item.severity}: {item.code}: {item.path}: {item.message}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ForPrint module coordination metadata."
    )
    parser.add_argument(
        "--module-root",
        default=".",
        help="Path to the module repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    result = check_module_coordination_metadata(Path(args.module_root))

    print("ForPrint coordination metadata check")
    print(f"Module root: {result.module_root}")
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
        return 0

    print("\n❌ Coordination metadata check failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
