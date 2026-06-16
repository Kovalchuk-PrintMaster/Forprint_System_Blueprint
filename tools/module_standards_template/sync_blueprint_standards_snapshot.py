#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from read_blueprint_standards import (
    resolve_blueprint_dir,
    standards_summary,
    validate_standards_visibility,
)

SNAPSHOT_PATH = Path("coordination/standards/blueprint_standards_snapshot.yaml")


def build_snapshot(blueprint_dir: Path, module_root: Path) -> dict[str, Any]:
    issues = validate_standards_visibility(blueprint_dir)
    summary = standards_summary(blueprint_dir)
    if issues:
        raise ValueError("Blueprint standards visibility has issues:\\n- " + "\\n- ".join(issues))

    standards = summary.get("standards", [])
    if not isinstance(standards, list):
        standards = []

    reviewed = []
    for record in standards:
        if isinstance(record, dict):
            reviewed.append(
                {
                    "standard_id": record.get("standard_id"),
                    "file": record.get("file"),
                    "title": record.get("title"),
                    "status": record.get("status"),
                    "adoption_mode": record.get("adoption_mode"),
                }
            )

    return {
        "snapshot_version": "v0_1",
        "snapshot_created_at": datetime.now(UTC).isoformat(),
        "source_blueprint_dir": str(blueprint_dir),
        "source_standards_index": str(blueprint_dir / "coordination/standards/index.yaml"),
        "module_root": str(module_root),
        "standards_index_version": summary.get("standards_index_version"),
        "default_semantics": summary.get("default_semantics"),
        "policy": summary.get("policy", {}),
        "standards_count": len(reviewed),
        "standards_reviewed": reviewed,
        "alignment_notes": [
            "Blueprint standards are visible to the module.",
            "Standards are advisory by default.",
            "Hard enforcement requires an explicit prompt or directive.",
            "No destructive refactor is implied by this snapshot.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync lightweight Blueprint standards snapshot into a module.")
    parser.add_argument("--blueprint-dir", default=None)
    parser.add_argument("--module-root", default=".")
    args = parser.parse_args()

    blueprint_dir = resolve_blueprint_dir(args.blueprint_dir)
    module_root = Path(args.module_root).resolve()

    try:
        snapshot = build_snapshot(blueprint_dir, module_root)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    path = module_root / SNAPSHOT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=False), encoding="utf-8")

    print(f"✅ Blueprint standards snapshot written: {path}")
    print(f"Standards count: {snapshot['standards_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
