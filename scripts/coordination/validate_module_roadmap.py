from __future__ import annotations

import argparse
from pathlib import Path

from scripts.coordination.module_roadmap import (
    RoadmapError,
    load_yaml_file,
    resolve_roadmap_path,
    validate_roadmap_document,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a ForPrint module development roadmap.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Blueprint repository root.",
    )
    parser.add_argument(
        "--module",
        help="Module id, for example forprint_library.",
    )
    parser.add_argument(
        "--roadmap",
        help="Explicit roadmap YAML path.",
    )
    args = parser.parse_args()

    try:
        path = resolve_roadmap_path(
            root=args.root,
            module=args.module,
            roadmap=args.roadmap,
        )
        data = load_yaml_file(path)
        result = validate_roadmap_document(data, path=path)
    except RoadmapError as exc:
        print(f"FAILED: {exc}")
        return 1

    print(f"Roadmap: {result.path}")
    print(f"Module: {result.module}")
    print(f"Steps: {result.step_count}")
    print(f"Current step: {result.current_step_id or '-'}")

    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    print("OK: module roadmap is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
