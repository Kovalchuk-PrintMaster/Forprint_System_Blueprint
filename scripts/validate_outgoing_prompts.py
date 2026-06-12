#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_ACTIVE_STATUSES = {
    "ready_for_module_pull",
    "draft",
    "paused",
    "blocked",
}

ALLOWED_COMPLETED_STATUSES = {
    "completed_accepted",
    "completed_pending_coordination_record_fix",
    "completed_in_module",
    "applied_in_module",
    "superseded",
    "rejected",
}

BAD_PLACEHOLDERS = {
    "{now}",
    "{branch}",
    "{commit}",
    "{module_id}",
    "{phase}",
    "{completed_step}",
    "{{now}}",
    "{{branch}}",
    "{{commit}}",
    "{{module_id}}",
    "{{phase}}",
    "{{completed_step}}",
}

FORBIDDEN_TEXT_TOKENS = {
    "forprint_calculator_engine": "Use canonical module id `calculator_engine`.",
}

OUTGOING_DIR = Path("coordination/outgoing_prompts")


@dataclass(frozen=True)
class ValidationIssue:
    path: Path
    message: str


def _load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    text = path.read_text(encoding="utf-8")
    issues: list[ValidationIssue] = []

    for token in sorted(BAD_PLACEHOLDERS):
        if token in text:
            issues.append(ValidationIssue(path, f"unresolved placeholder token: {token}"))

    for token, hint in sorted(FORBIDDEN_TEXT_TOKENS.items()):
        if token in text:
            issues.append(ValidationIssue(path, f"forbidden token `{token}`. {hint}"))

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        issues.append(ValidationIssue(path, f"invalid YAML: {exc}"))
        return None, issues

    if not isinstance(data, dict):
        issues.append(ValidationIssue(path, "YAML root must be a mapping"))
        return None, issues

    return data, issues


def _as_list(value: Any, path: Path, field_name: str) -> tuple[list[dict[str, Any]], list[ValidationIssue]]:
    if value is None:
        return [], []

    if not isinstance(value, list):
        return [], [ValidationIssue(path, f"`{field_name}` must be a list")]

    records: list[dict[str, Any]] = []
    issues: list[ValidationIssue] = []

    for index, item in enumerate(value):
        if not isinstance(item, dict):
            issues.append(ValidationIssue(path, f"`{field_name}[{index}]` must be a mapping"))
            continue
        records.append(item)

    return records, issues


def _validate_prompt_file_text(path: Path) -> list[ValidationIssue]:
    text = path.read_text(encoding="utf-8")
    issues: list[ValidationIssue] = []

    for token in sorted(BAD_PLACEHOLDERS):
        if token in text:
            issues.append(ValidationIssue(path, f"unresolved placeholder token: {token}"))

    for token, hint in sorted(FORBIDDEN_TEXT_TOKENS.items()):
        if token in text:
            issues.append(ValidationIssue(path, f"forbidden token `{token}`. {hint}"))

    if "## Target module" in text and "## Purpose" not in text:
        issues.append(ValidationIssue(path, "prompt has `## Target module` but no `## Purpose` section"))

    return issues


def _validate_active_prompt(
    *,
    module_dir: Path,
    index_path: Path,
    record: dict[str, Any],
    seen_prompt_ids: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    prompt_id = record.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id.strip():
        issues.append(ValidationIssue(index_path, "active prompt has missing/invalid `prompt_id`"))
    elif prompt_id in seen_prompt_ids:
        issues.append(ValidationIssue(index_path, f"duplicate prompt_id: {prompt_id}"))
    else:
        seen_prompt_ids.add(prompt_id)

    status = record.get("status")
    if status not in ALLOWED_ACTIVE_STATUSES:
        issues.append(
            ValidationIssue(
                index_path,
                f"active prompt `{prompt_id}` has unsupported status `{status}`",
            )
        )

    target_module = record.get("target_module")
    if target_module is not None and target_module != module_dir.name:
        issues.append(
            ValidationIssue(
                index_path,
                f"active prompt `{prompt_id}` target_module `{target_module}` "
                f"does not match outgoing module directory `{module_dir.name}`",
            )
        )

    file_value = record.get("file")
    if not isinstance(file_value, str) or not file_value.strip():
        issues.append(ValidationIssue(index_path, f"active prompt `{prompt_id}` has missing/invalid `file`"))
        return issues

    prompt_path = module_dir / file_value
    if not prompt_path.exists():
        issues.append(ValidationIssue(index_path, f"active prompt `{prompt_id}` file does not exist: {prompt_path}"))
        return issues

    if not prompt_path.is_file():
        issues.append(ValidationIssue(index_path, f"active prompt `{prompt_id}` path is not a file: {prompt_path}"))
        return issues

    issues.extend(_validate_prompt_file_text(prompt_path))

    return issues


def _validate_completed_prompt(
    *,
    index_path: Path,
    record: dict[str, Any],
    seen_prompt_ids: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    prompt_id = record.get("prompt_id")
    if not isinstance(prompt_id, str) or not prompt_id.strip():
        issues.append(ValidationIssue(index_path, "completed prompt has missing/invalid `prompt_id`"))
    elif prompt_id in seen_prompt_ids:
        issues.append(ValidationIssue(index_path, f"duplicate prompt_id: {prompt_id}"))
    else:
        seen_prompt_ids.add(prompt_id)

    status = record.get("status")
    if status not in ALLOWED_COMPLETED_STATUSES:
        issues.append(
            ValidationIssue(
                index_path,
                f"completed prompt `{prompt_id}` has unsupported status `{status}`",
            )
        )

    return issues


def _validate_review_notes(
    *,
    module_dir: Path,
    index_path: Path,
    records: list[dict[str, Any]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    for record in records:
        note_id = record.get("note_id", "<missing>")
        file_value = record.get("file")
        if not isinstance(file_value, str) or not file_value.strip():
            issues.append(ValidationIssue(index_path, f"review note `{note_id}` has missing/invalid `file`"))
            continue

        note_path = module_dir / file_value
        if not note_path.exists():
            issues.append(ValidationIssue(index_path, f"review note `{note_id}` file does not exist: {note_path}"))

    return issues


def validate_root(root: Path) -> list[ValidationIssue]:
    outgoing_root = root / OUTGOING_DIR
    issues: list[ValidationIssue] = []
    seen_prompt_ids: set[str] = set()

    if not outgoing_root.exists():
        return [ValidationIssue(outgoing_root, "outgoing prompts directory does not exist")]

    index_paths = sorted(outgoing_root.glob("*/index.yaml"))
    if not index_paths:
        return [ValidationIssue(outgoing_root, "no module outgoing prompt indexes found")]

    for index_path in index_paths:
        module_dir = index_path.parent
        data, yaml_issues = _load_yaml(index_path)
        issues.extend(yaml_issues)

        if data is None:
            continue

        module_value = data.get("module")
        if module_value is not None and module_value != module_dir.name:
            issues.append(
                ValidationIssue(
                    index_path,
                    f"`module` value `{module_value}` does not match directory `{module_dir.name}`",
                )
            )

        active_prompts, list_issues = _as_list(data.get("active_prompts"), index_path, "active_prompts")
        issues.extend(list_issues)

        completed_prompts, list_issues = _as_list(data.get("completed_prompts"), index_path, "completed_prompts")
        issues.extend(list_issues)

        review_notes, list_issues = _as_list(data.get("review_notes"), index_path, "review_notes")
        issues.extend(list_issues)

        for record in active_prompts:
            issues.extend(
                _validate_active_prompt(
                    module_dir=module_dir,
                    index_path=index_path,
                    record=record,
                    seen_prompt_ids=seen_prompt_ids,
                )
            )

        for record in completed_prompts:
            issues.extend(
                _validate_completed_prompt(
                    index_path=index_path,
                    record=record,
                    seen_prompt_ids=seen_prompt_ids,
                )
            )

        issues.extend(
            _validate_review_notes(
                module_dir=module_dir,
                index_path=index_path,
                records=review_notes,
            )
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForPrint Blueprint outgoing prompt indexes.")
    parser.add_argument("--root", default=".", help="Blueprint repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues = validate_root(root)

    if issues:
        print("❌ Outgoing prompt validation failed:")
        for issue in issues:
            print(f"  - {issue.path}: {issue.message}")
        return 1

    print("✅ Outgoing prompt validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
