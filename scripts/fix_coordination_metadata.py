from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.forprint_coordination_tools.metadata import (  # noqa: E402
    fix_module_coordination_metadata,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely fix simple ForPrint coordination metadata issues."
    )
    parser.add_argument(
        "--module-root",
        default=".",
        help="Path to the module repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--update-git-commit",
        action="store_true",
        help="Replace pending commit values with current git HEAD where safe.",
    )

    parser.add_argument(
        "--mark-pushed-if-upstream-clean",
        action="store_true",
        help=(
            "Set pushed: true for pending/false report entries only when "
            "local HEAD is not ahead of upstream."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    result = fix_module_coordination_metadata(
        module_root=Path(args.module_root),
        update_git_commit=args.update_git_commit,
    )


    print("ForPrint coordination metadata fixer")
    print(f"Module root: {result.module_root}")

    if result.changed_files:
        print("\nChanged files:")
        for item in result.changed_files:
            print(f"  - {item}")
    else:
        print("\nChanged files: none")

    if result.skipped:
        print("\nSkipped:")
        for item in result.skipped:
            print(f"  - {item}")

    if result.warnings:
        print("\nWarnings:")
        for item in result.warnings:
            print(f"  - {item}")

    result = fix_module_coordination_metadata(
        module_root=Path(args.module_root),
        update_git_commit=args.update_git_commit,
        mark_pushed_if_upstream_clean=args.mark_pushed_if_upstream_clean,
    )

    print("\n✅ Coordination metadata fixer completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
