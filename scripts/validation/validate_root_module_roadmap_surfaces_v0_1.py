#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP_ROOT = ROOT / "coordination/roadmaps"
VALIDATOR = ROOT / "scripts/coordination/validate_module_roadmap.py"

EXPECTED_STATUS = "active_planning_context"
EXPECTED_AUTHORITY = "canonical_planning_not_release_or_execution_authority"
REQUIRED = {
    "schema_version",
    "module",
    "status",
    "authority",
    "metadata",
    "roadmap",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def has_indentless_sequence(path: Path) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines[:-1]):
        stripped = line.lstrip()
        if not stripped.endswith(":") or stripped.startswith("-"):
            continue
        key_indent = len(line) - len(stripped)
        nxt = lines[i + 1]
        nxt_stripped = nxt.lstrip()
        if nxt_stripped.startswith("- "):
            nxt_indent = len(nxt) - len(nxt_stripped)
            if nxt_indent <= key_indent:
                return True
    return False


def main() -> int:
    paths = sorted(ROADMAP_ROOT.glob("*.yaml"))
    issues: list[str] = []

    if len(paths) != 7:
        issues.append(f"expected 7 root module roadmaps, got {len(paths)}")

    seen_modules: set[str] = set()

    for path in paths:
        data = load_yaml(path)
        rel = path.relative_to(ROOT)

        if not isinstance(data, dict):
            issues.append(f"{rel}: root is not a mapping")
            continue

        missing = sorted(REQUIRED - set(data))
        if missing:
            issues.append(f"{rel}: missing required top-level {','.join(missing)}")
            continue

        if data.get("schema_version") != "module_development_roadmap_v0_1":
            issues.append(f"{rel}: unexpected schema_version")
        if data.get("status") != EXPECTED_STATUS:
            issues.append(f"{rel}: unexpected document status")
        if data.get("authority") != EXPECTED_AUTHORITY:
            issues.append(f"{rel}: unexpected authority marker")
        if not isinstance(data.get("module"), str) or not data["module"].strip():
            issues.append(f"{rel}: module must be a non-empty string")
        elif data["module"] in seen_modules:
            issues.append(f"{rel}: duplicate module {data['module']}")
        else:
            seen_modules.add(data["module"])

        if not isinstance(data.get("metadata"), dict):
            issues.append(f"{rel}: metadata must be a mapping")
        if not isinstance(data.get("roadmap"), list):
            issues.append(f"{rel}: roadmap must be a list")
        if has_indentless_sequence(path):
            issues.append(f"{rel}: legacy indentless sequence style remains")

        p = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR.relative_to(ROOT)),
                "--roadmap",
                str(rel),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if p.returncode:
            issues.append(f"{rel}: module roadmap validator failed\n{p.stdout}")

    if issues:
        print("ROOT_MODULE_ROADMAP_SURFACES=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1

    print("ROOT_MODULE_ROADMAP_SURFACES=PASS")
    print(f"ROADMAP_COUNT={len(paths)}")
    print(f"MODULE_COUNT={len(seen_modules)}")
    print(f"STATUS={EXPECTED_STATUS}")
    print(f"AUTHORITY={EXPECTED_AUTHORITY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
