from __future__ import annotations

import argparse
from pathlib import Path

from scripts.coordination.module_roadmap import (
    load_yaml_file,
    render_roadmap_detail,
    resolve_roadmap_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render an expanded ForPrint module roadmap detail view.",
    )
    parser.add_argument("--root", default=".")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--module")
    source.add_argument("--roadmap")
    parser.add_argument("--before-current", type=int, default=2)
    parser.add_argument("--after-current", type=int, default=8)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    path = resolve_roadmap_path(
        root=root,
        module=args.module,
        roadmap=args.roadmap,
    )
    data = load_yaml_file(path)
    print(
        render_roadmap_detail(
            data,
            path=path,
            before_current=args.before_current,
            after_current=args.after_current,
            no_color=args.no_color,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
