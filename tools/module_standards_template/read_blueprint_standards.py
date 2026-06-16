#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

STANDARDS_INDEX_PATH = Path("coordination/standards/index.yaml")
REQUIRED_POLICY_FLAGS = {
    "continuous_read_required": True,
    "advisory_by_default": True,
    "not_active_prompt": True,
    "gradual_alignment_required": True,
    "hard_enforcement_requires_prompt_or_directive": True,
}


def resolve_blueprint_dir(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    env_value = os.environ.get("BLUEPRINT_DIR")
    if env_value:
        return Path(env_value).expanduser().resolve()
    return Path("/srv/software_development/forprint-project/forprint_system_blueprint").resolve()


def _issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def load_standards_index(blueprint_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    index_path = blueprint_dir / STANDARDS_INDEX_PATH
    try:
        text = index_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [_issue(index_path, "standards index does not exist")]

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [_issue(index_path, f"invalid YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [_issue(index_path, "standards index root must be a mapping")]

    return data, []


def validate_standards_visibility(blueprint_dir: Path) -> list[str]:
    data, issues = load_standards_index(blueprint_dir)
    index_path = blueprint_dir / STANDARDS_INDEX_PATH
    if data is None:
        return issues

    if data.get("standards_index_version") != "v0_1":
        issues.append(_issue(index_path, "`standards_index_version` must be `v0_1`"))
    if data.get("status") != "active":
        issues.append(_issue(index_path, "`status` must be `active`"))
    if data.get("default_semantics") != "advisory_guidance_gradual_alignment":
        issues.append(_issue(index_path, "`default_semantics` must be advisory guidance"))

    policy = data.get("policy")
    if not isinstance(policy, dict):
        issues.append(_issue(index_path, "`policy` must be a mapping"))
    else:
        for key, expected in sorted(REQUIRED_POLICY_FLAGS.items()):
            if policy.get(key) is not expected:
                issues.append(_issue(index_path, f"`policy.{key}` must be {expected}"))

    standards = data.get("standards")
    if not isinstance(standards, list) or not standards:
        issues.append(_issue(index_path, "`standards` must be a non-empty list"))
        return issues

    seen: set[str] = set()
    for index, record in enumerate(standards):
        if not isinstance(record, dict):
            issues.append(_issue(index_path, f"`standards[{index}]` must be a mapping"))
            continue
        for field_name in ("standard_id", "file", "title", "status", "adoption_mode"):
            value = record.get(field_name)
            if not isinstance(value, str) or not value.strip():
                issues.append(_issue(index_path, f"`standards[{index}].{field_name}` must be non-empty"))
        standard_id = record.get("standard_id")
        if isinstance(standard_id, str):
            if standard_id in seen:
                issues.append(_issue(index_path, f"duplicate standard_id `{standard_id}`"))
            seen.add(standard_id)
        file_name = record.get("file")
        if isinstance(file_name, str):
            standard_path = blueprint_dir / "coordination" / "standards" / file_name
            if not standard_path.is_file():
                issues.append(_issue(index_path, f"referenced standard file does not exist: {standard_path}"))
    return issues


def standards_summary(blueprint_dir: Path) -> dict[str, Any]:
    data, issues = load_standards_index(blueprint_dir)
    if data is None:
        return {"ok": False, "issues": issues, "standards": [], "standards_count": 0}
    standards = data.get("standards", [])
    if not isinstance(standards, list):
        standards = []
    return {
        "ok": not issues,
        "issues": issues,
        "standards_index_path": str(blueprint_dir / STANDARDS_INDEX_PATH),
        "standards_index_version": data.get("standards_index_version"),
        "default_semantics": data.get("default_semantics"),
        "policy": data.get("policy", {}),
        "standards_count": len(standards),
        "standards": standards,
    }


def print_standards_list(summary: dict[str, Any]) -> None:
    print("== Blueprint standards visibility ==")
    print(f"Index: {summary.get('standards_index_path', '-')}")
    print(f"Version: {summary.get('standards_index_version', '-')}")
    print(f"Default semantics: {summary.get('default_semantics', '-')}")
    print(f"Standards count: {summary.get('standards_count', 0)}")
    standards = summary.get("standards", [])
    if not isinstance(standards, list):
        standards = []
    for record in standards:
        if isinstance(record, dict):
            print(
                f"- {record.get('standard_id', '-')}: "
                f"{record.get('file', '-')} "
                f"[{record.get('status', '-')}; {record.get('adoption_mode', '-')}]"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read Blueprint standards index from a ForPrint module.")
    parser.add_argument("--blueprint-dir", default=None)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    blueprint_dir = resolve_blueprint_dir(args.blueprint_dir)
    summary = standards_summary(blueprint_dir)
    issues = validate_standards_visibility(blueprint_dir)

    if args.json:
        output = dict(summary)
        output["validation_issues"] = issues
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_standards_list(summary)

    if issues:
        print("❌ Blueprint standards visibility has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("✅ Blueprint standards are readable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
