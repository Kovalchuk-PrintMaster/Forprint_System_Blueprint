from __future__ import annotations

import argparse
from pathlib import Path

from scripts.coordination.module_roadmap import (
    RoadmapError,
    load_yaml_file,
    render_modules_summary,
    render_roadmap_dashboard,
    resolve_roadmap_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a ForPrint module roadmap dashboard.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Blueprint repository root.",
    )
    parser.add_argument(
        "--module",
        help="Single module id, for example forprint_library.",
    )
    parser.add_argument(
        "--modules",
        help="Comma-separated module ids for compact comparison.",
    )
    parser.add_argument(
        "--roadmap",
        help="Explicit roadmap YAML path for single-module mode.",
    )
    parser.add_argument(
        "--before-current",
        type=int,
        default=5,
        help="Number of steps to show before the current step.",
    )
    parser.add_argument(
        "--after-current",
        type=int,
        default=10,
        help="Number of steps to show after the current step.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable terminal colors.",
    )
    args = parser.parse_args()

    try:
        if args.modules:
            roadmaps = []
            for module in _split_modules(args.modules):
                path = resolve_roadmap_path(root=args.root, module=module)
                roadmaps.append((path, load_yaml_file(path)))
            print(render_modules_summary(roadmaps, no_color=args.no_color))
            return 0

        path = resolve_roadmap_path(
            root=args.root,
            module=args.module,
            roadmap=args.roadmap,
        )
        data = load_yaml_file(path)
        print(
            render_roadmap_dashboard(
                data,
                path=path,
                before_current=args.before_current,
                after_current=args.after_current,
                no_color=args.no_color,
            ),
        )
        return 0
    except RoadmapError as exc:
        print(f"FAILED: {exc}")
        return 1


def _split_modules(value: str) -> list[str]:
    modules = [item.strip() for item in value.split(",")]
    return [module for module in modules if module]


if __name__ == "__main__":
    raise SystemExit(main())
