#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SEED_ROOT = (
    ROOT
    / "coordination/roadmaps/details/forprint_system_blueprint/"
    "portfolio_rebuild_seeds"
)

SCHEMA = "forprint_portfolio_roadmap_rebuild_seed_v0_1"
AUTHORITY = "provisional_planning_input_not_release_or_execution_authority"
ALLOWED_STATUSES = {
    "PROVISIONAL_SYNTHETIC_REBUILD_SEED_NOT_AUTHORITY",
    "CONFIRMED_PLANNED_SYNTHETIC_REBUILD_SEED_NOT_EXECUTION_AUTHORITY",
}
REQUIRED = {
    "schema_version",
    "module_id",
    "role_summary",
    "status",
    "authority",
    "source_action",
    "steps",
}
REQUIRED_STEP = {"step_id", "title", "status", "confidence"}


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
    paths = sorted(SEED_ROOT.glob("*.yaml"))
    issues: list[str] = []
    modules: set[str] = set()
    step_ids: set[str] = set()

    if len(paths) != 19:
        issues.append(f"expected 19 portfolio rebuild seeds, got {len(paths)}")

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

        if data.get("schema_version") != SCHEMA:
            issues.append(f"{rel}: unexpected schema_version")
        if data.get("authority") != AUTHORITY:
            issues.append(f"{rel}: unexpected authority")
        if data.get("status") not in ALLOWED_STATUSES:
            issues.append(f"{rel}: unexpected status {data.get('status')!r}")

        module_id = data.get("module_id")
        if not isinstance(module_id, str) or not module_id.strip():
            issues.append(f"{rel}: module_id must be a non-empty string")
        elif module_id in modules:
            issues.append(f"{rel}: duplicate module_id {module_id}")
        else:
            modules.add(module_id)

        if not isinstance(data.get("role_summary"), str) or not data["role_summary"].strip():
            issues.append(f"{rel}: role_summary must be non-empty")
        if not isinstance(data.get("source_action"), str) or not data["source_action"].strip():
            issues.append(f"{rel}: source_action must be non-empty")

        steps = data.get("steps")
        if not isinstance(steps, list):
            issues.append(f"{rel}: steps must be a list")
            continue
        if len(steps) != 10:
            issues.append(f"{rel}: expected 10 horizon steps, got {len(steps)}")

        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                issues.append(f"{rel}: steps[{index}] is not a mapping")
                continue
            step_missing = sorted(REQUIRED_STEP - set(step))
            if step_missing:
                issues.append(
                    f"{rel}: steps[{index}] missing {','.join(step_missing)}"
                )
                continue
            sid = step.get("step_id")
            if not isinstance(sid, str) or not sid.strip():
                issues.append(f"{rel}: steps[{index}] step_id must be non-empty")
            elif sid in step_ids:
                issues.append(f"{rel}: duplicate global step_id {sid}")
            else:
                step_ids.add(sid)

            if not isinstance(step.get("title"), str) or not step["title"].strip():
                issues.append(f"{rel}: steps[{index}] title must be non-empty")
            if not isinstance(step.get("status"), str) or not step["status"].strip():
                issues.append(f"{rel}: steps[{index}] status must be non-empty")
            if not isinstance(step.get("confidence"), str) or not step["confidence"].strip():
                issues.append(f"{rel}: steps[{index}] confidence must be non-empty")

        if has_indentless_sequence(path):
            issues.append(f"{rel}: legacy indentless sequence style remains")

    if issues:
        print("PORTFOLIO_REBUILD_SEED_SURFACES=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1

    print("PORTFOLIO_REBUILD_SEED_SURFACES=PASS")
    print(f"SEED_COUNT={len(paths)}")
    print(f"MODULE_COUNT={len(modules)}")
    print(f"STEP_COUNT={len(step_ids)}")
    print(f"AUTHORITY={AUTHORITY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
