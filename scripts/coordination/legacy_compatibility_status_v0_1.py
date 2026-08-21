from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    path = root / "coordination/legacy/compatibility_registry_v0_1.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    print("ForPrint Legacy Compatibility Status")
    print("current_gate: NONBLOCKING")
    print("visibility: ADVISORY_YELLOW")
    for item in data.get("components", []):
        print(
            f"{item.get('component_id')}: "
            f"{item.get('status')} "
            f"blocking_current_gates={str(item.get('blocking_current_gates')).lower()}"
        )
        replacement = item.get("replacement", {})
        print(f"  replacement_release: {replacement.get('release_projection')}")
        print(f"  planned_retirement: {item.get('retirement', {}).get('planned_slice')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
