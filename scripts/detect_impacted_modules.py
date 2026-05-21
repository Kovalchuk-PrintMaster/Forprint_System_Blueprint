# python scripts/detect_impacted_modules.py material_catalog machine_capability
"""
Detect impacted modules for changed data objects.

Приклад:

    python scripts/detect_impacted_modules.py material_catalog machine_capability

Скрипт читає `machine/impact_rules.yaml` і `machine/ownership.yaml`, після чого
показує, які модулі варто попередити.
"""

from __future__ import annotations

# Дозволяє запускати скрипт і як модуль, і напряму: python scripts/name.py
if __package__ is None or __package__ == "":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.blueprint_utils import load_yaml, project_root


def detect_impacted(changed_objects: list[str], root: Path | None = None) -> dict[str, Any]:
    """Return impacted modules and reasons for changed data object IDs."""

    root = root or project_root()
    machine = root / "machine"

    impact_rules = load_yaml(machine / "impact_rules.yaml").get("impact_rules", [])
    ownership = load_yaml(machine / "ownership.yaml").get("ownership", {})

    impacted: dict[str, set[str]] = {}

    for changed in changed_objects:
        ownership_record = ownership.get(changed)
        if ownership_record:
            for module_id in ownership_record.get("consumers", []):
                impacted.setdefault(module_id, set()).add(f"consumer_of:{changed}")
            owner = ownership_record.get("owner")
            if owner:
                impacted.setdefault(owner, set()).add(f"owner_of:{changed}")

        for rule in impact_rules:
            if changed in rule.get("when_changed", []):
                for module_id in rule.get("notify_modules", []):
                    impacted.setdefault(module_id, set()).add(f"impact_rule:{rule['id']}")

    return {
        "changed_objects": changed_objects,
        "impacted_modules": [
            {"module_id": module_id, "reasons": sorted(reasons)}
            for module_id, reasons in sorted(impacted.items())
        ],
    }


def main() -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description="Detect impacted ForPrint modules")
    parser.add_argument("changed_objects", nargs="+", help="Changed data object IDs")
    args = parser.parse_args()

    result = detect_impacted(args.changed_objects)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
