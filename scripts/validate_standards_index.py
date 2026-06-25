#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

STANDARDS_DIR = Path("coordination/standards")
INDEX_PATH = STANDARDS_DIR / "index.yaml"

ALLOWED_STATUSES = {
    "active_standard",
    "target_standard",
    "advisory_guidance",
    "draft",
}

ALLOWED_ADOPTION_MODES = {
    "continuous_read",
    "gradual_alignment",
    "prompt_or_directive_required",
    "reference_only",
}

REQUIRED_POLICY_FLAGS = {
    "continuous_read_required": True,
    "advisory_by_default": True,
    "not_active_prompt": True,
    "gradual_alignment_required": True,
    "hard_enforcement_requires_prompt_or_directive": True,
}

BAD_PLACEHOLDERS = {
    "{now}",
    "{branch}",
    "{commit}",
    "{module_id}",
    "{standard_id}",
    "{{now}}",
    "{{branch}}",
    "{{commit}}",
    "{{module_id}}",
    "{{standard_id}}",
}

FORBIDDEN_TEXT_TOKENS = {
    "forprint_calculator_engine": "Use canonical module id `calculator_engine`.",
}


def _issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def _read_yaml(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    issues: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [_issue(path, "file does not exist")]

    for token in sorted(BAD_PLACEHOLDERS):
        if token in text:
            issues.append(_issue(path, f"unresolved placeholder token: {token}"))

    for token, hint in sorted(FORBIDDEN_TEXT_TOKENS.items()):
        if token in text:
            issues.append(_issue(path, f"forbidden token `{token}`. {hint}"))

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, issues + [_issue(path, f"invalid YAML: {exc}")]

    if not isinstance(data, dict):
        return None, issues + [_issue(path, "YAML root must be a mapping")]

    return data, issues


def _standards_files(root: Path) -> set[str]:
    standards_root = root / STANDARDS_DIR
    files: set[str] = set()

    for path in standards_root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(standards_root)

        if relative_path.as_posix() == "index.yaml":
            continue

        if path.suffix not in {".md", ".yaml", ".yml"}:
            continue

        files.add(relative_path.as_posix())

    return files


def _validate_policy(root: Path, data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    policy = data.get("policy")

    if not isinstance(policy, dict):
        return [_issue(root / INDEX_PATH, "`policy` must be a mapping")]

    for key, expected in sorted(REQUIRED_POLICY_FLAGS.items()):
        if policy.get(key) is not expected:
            issues.append(_issue(root / INDEX_PATH, f"`policy.{key}` must be {expected}"))

    return issues


def _validate_standard_records(root: Path, data: dict[str, Any]) -> list[str]:
    index_path = root / INDEX_PATH
    issues: list[str] = []

    records = data.get("standards")
    if not isinstance(records, list) or not records:
        return [_issue(index_path, "`standards` must be a non-empty list")]

    known_ids: set[str] = set()
    indexed_files: set[str] = set()

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(_issue(index_path, f"`standards[{index}]` must be a mapping"))
            continue

        for field_name in ("standard_id", "file", "title", "status", "adoption_mode"):
            value = record.get(field_name)
            if not isinstance(value, str) or not value.strip():
                issues.append(
                    _issue(index_path, f"`standards[{index}].{field_name}` must be a non-empty string")
                )

        standard_id = record.get("standard_id")
        if isinstance(standard_id, str):
            if standard_id in known_ids:
                issues.append(_issue(index_path, f"duplicate standard_id `{standard_id}`"))
            known_ids.add(standard_id)

        status = record.get("status")
        if isinstance(status, str) and status not in ALLOWED_STATUSES:
            issues.append(_issue(index_path, f"unsupported standard status `{status}`"))

        adoption_mode = record.get("adoption_mode")
        if isinstance(adoption_mode, str) and adoption_mode not in ALLOWED_ADOPTION_MODES:
            issues.append(_issue(index_path, f"unsupported adoption_mode `{adoption_mode}`"))

        file_name = record.get("file")
        if isinstance(file_name, str):
            indexed_files.add(file_name)
            standard_path = root / STANDARDS_DIR / file_name
            if not standard_path.exists():
                issues.append(_issue(index_path, f"indexed standard file does not exist: {standard_path}"))
            elif not standard_path.is_file():
                issues.append(_issue(index_path, f"indexed standard path is not a file: {standard_path}"))

    existing_files = _standards_files(root)

    for file_name in sorted(existing_files - indexed_files):
        issues.append(_issue(index_path, f"standard file is not indexed: {file_name}"))

    for file_name in sorted(indexed_files - existing_files):
        issues.append(_issue(index_path, f"indexed file is not a standards file: {file_name}"))

    return issues


def validate_standards_index(root: Path) -> list[str]:
    data, issues = _read_yaml(root / INDEX_PATH)

    if data is None:
        return issues

    if data.get("standards_index_version") != "v0_1":
        issues.append(_issue(root / INDEX_PATH, "`standards_index_version` must be `v0_1`"))

    if data.get("status") != "active":
        issues.append(_issue(root / INDEX_PATH, "`status` must be `active`"))

    if data.get("default_semantics") != "advisory_guidance_gradual_alignment":
        issues.append(
            _issue(
                root / INDEX_PATH,
                "`default_semantics` must be `advisory_guidance_gradual_alignment`",
            )
        )

    issues.extend(_validate_policy(root, data))
    issues.extend(_validate_standard_records(root, data))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForPrint Blueprint standards index.")
    parser.add_argument("--root", default=".", help="Blueprint repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues = validate_standards_index(root)

    if issues:
        print("❌ Standards index validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Standards index validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
