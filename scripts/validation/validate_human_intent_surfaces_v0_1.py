#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MUTATOR = ROOT / "scripts/coordination/human_intent_mutation_v0_1.py"
INDEX = ROOT / "coordination/human_intent/index.yaml"
DELTAS = ROOT / "coordination/human_intent/deltas"

CANONICAL_STATUSES = {"AGREED", "RECOVERED", "PROPOSED", "GAP"}
DELTA_REQUIRED = {"schema_version", "status", "authority", "modules"}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def has_indentless_sequence(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines[:-1]):
        stripped = line.lstrip()
        if not stripped.endswith(":") or stripped.startswith("-"):
            continue
        key_indent = len(line) - len(stripped)
        next_line = lines[i + 1]
        next_stripped = next_line.lstrip()
        if next_stripped.startswith("- "):
            next_indent = len(next_line) - len(next_stripped)
            if next_indent <= key_indent:
                return True
    return False


def validate_deltas() -> list[str]:
    issues = []
    index = load_yaml(INDEX)
    known_modules = {
        entry["module_id"]
        for entry in index.get("modules", [])
        if isinstance(entry, dict) and isinstance(entry.get("module_id"), str)
    }

    for path in sorted(DELTAS.glob("*.yaml")):
        data = load_yaml(path)
        if not isinstance(data, dict):
            issues.append(f"delta root is not mapping: {path.relative_to(ROOT)}")
            continue

        missing = sorted(DELTA_REQUIRED - set(data))
        if missing:
            issues.append(
                f"delta missing required fields {','.join(missing)}: "
                f"{path.relative_to(ROOT)}"
            )
            continue

        modules = data.get("modules")
        if not isinstance(modules, dict):
            issues.append(f"delta modules is not mapping: {path.relative_to(ROOT)}")
            continue

        seen_ids = set()
        for module_id, intents in modules.items():
            if module_id not in known_modules:
                issues.append(
                    f"delta references unknown module {module_id}: "
                    f"{path.relative_to(ROOT)}"
                )
            if not isinstance(intents, list):
                issues.append(
                    f"delta intents is not list for {module_id}: "
                    f"{path.relative_to(ROOT)}"
                )
                continue

            for intent in intents:
                if not isinstance(intent, dict):
                    issues.append(
                        f"delta intent is not mapping for {module_id}: "
                        f"{path.relative_to(ROOT)}"
                    )
                    continue
                iid = intent.get("intent_id")
                status = intent.get("status")
                text = intent.get("text")
                if not isinstance(iid, str) or not iid.strip():
                    issues.append(
                        f"delta intent missing intent_id for {module_id}: "
                        f"{path.relative_to(ROOT)}"
                    )
                    continue
                if iid in seen_ids:
                    issues.append(
                        f"duplicate delta intent_id {iid}: {path.relative_to(ROOT)}"
                    )
                seen_ids.add(iid)
                if status not in CANONICAL_STATUSES:
                    issues.append(
                        f"noncanonical delta status {status!r}: {iid}"
                    )
                if not isinstance(text, str) or not text.strip():
                    issues.append(f"empty delta intent text: {iid}")

        if has_indentless_sequence(path):
            issues.append(
                f"legacy indentless sequence remains: {path.relative_to(ROOT)}"
            )

    return issues


def main() -> int:
    checks = [
        [sys.executable, str(MUTATOR.relative_to(ROOT)), "validate"],
        [sys.executable, str(MUTATOR.relative_to(ROOT)), "sync", "--check"],
    ]
    for cmd in checks:
        p = subprocess.run(cmd, cwd=ROOT, text=True)
        if p.returncode:
            return p.returncode

    issues = validate_deltas()
    if issues:
        print("HUMAN_INTENT_SURFACE_VALIDATION=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1

    print("HUMAN_INTENT_DELTA_VALIDATION=PASS")
    print("HUMAN_INTENT_SURFACE_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
