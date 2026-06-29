#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROMPT_QUEUE_SCHEMA_VERSION = "prompt_queue_v0_2"
OUTGOING_PROMPTS_DIR = Path("coordination/outgoing_prompts")

ALLOWED_PRIORITIES = {
    "critical",
    "high",
    "normal",
    "low",
    "reference",
}

ALLOWED_MODULE_EXECUTION_STATUSES = {
    "planned",
    "ready_for_module_pull",
    "in_progress",
    "completed_by_module",
    "returned_for_fix",
    "paused",
    "blocked",
    "superseded",
}

ALLOWED_BLUEPRINT_REVIEW_STATUSES = {
    "not_started",
    "pending_review",
    "accepted_by_blueprint",
    "returned_for_fix",
    "not_required",
    "superseded",
}


@dataclass(frozen=True)
class ValidationIssue:
    path: Path
    message: str


@dataclass(frozen=True)
class ValidationResult:
    checked_indexes: int
    prompt_queue_indexes: int
    legacy_indexes: int
    issues: list[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.issues


def _load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, [ValidationIssue(path, f"invalid YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [ValidationIssue(path, "YAML root must be a mapping")]

    return data, []


def _require_string(
    *,
    record: dict[str, Any],
    field: str,
    index_path: Path,
    prompt_id: str,
) -> list[ValidationIssue]:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        return [
            ValidationIssue(
                index_path,
                f"prompt `{prompt_id}` has missing/invalid `{field}`",
            )
        ]
    return []


def _require_int(
    *,
    record: dict[str, Any],
    field: str,
    index_path: Path,
    prompt_id: str,
) -> list[ValidationIssue]:
    value = record.get(field)
    if not isinstance(value, int):
        return [
            ValidationIssue(
                index_path,
                f"prompt `{prompt_id}` has missing/invalid integer `{field}`",
            )
        ]
    return []


def _validate_nested_status(
    *,
    nested: Any,
    nested_name: str,
    status_field: str,
    allowed_statuses: set[str],
    index_path: Path,
    prompt_id: str,
) -> list[ValidationIssue]:
    if not isinstance(nested, dict):
        return [
            ValidationIssue(
                index_path,
                f"prompt `{prompt_id}` has missing/invalid `{nested_name}` block",
            )
        ]

    status = nested.get(status_field)
    if status not in allowed_statuses:
        return [
            ValidationIssue(
                index_path,
                f"prompt `{prompt_id}` has unsupported "
                f"`{nested_name}.{status_field}`: {status}",
            )
        ]

    return []


def _validate_prompt_record(
    *,
    root: Path,
    module_dir: Path,
    index_path: Path,
    record: dict[str, Any],
    seen_prompt_ids: set[str],
    seen_sequences: set[int],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    prompt_id_value = record.get("prompt_id")
    prompt_id = prompt_id_value if isinstance(prompt_id_value, str) else "<missing>"

    for field in ("prompt_id", "title", "file", "target_module", "phase", "priority"):
        issues.extend(
            _require_string(
                record=record,
                field=field,
                index_path=index_path,
                prompt_id=prompt_id,
            )
        )

    issues.extend(
        _require_int(
            record=record,
            field="sequence",
            index_path=index_path,
            prompt_id=prompt_id,
        )
    )

    if isinstance(prompt_id_value, str):
        if prompt_id_value in seen_prompt_ids:
            issues.append(
                ValidationIssue(index_path, f"duplicate prompt_id: {prompt_id_value}")
            )
        seen_prompt_ids.add(prompt_id_value)

    sequence = record.get("sequence")
    if isinstance(sequence, int):
        if sequence in seen_sequences:
            issues.append(
                ValidationIssue(
                    index_path,
                    f"duplicate sequence `{sequence}` in module `{module_dir.name}`",
                )
            )
        seen_sequences.add(sequence)

    target_module = record.get("target_module")
    if target_module != module_dir.name:
        issues.append(
            ValidationIssue(
                index_path,
                f"prompt `{prompt_id}` target_module `{target_module}` "
                f"does not match module directory `{module_dir.name}`",
            )
        )

    priority = record.get("priority")
    if priority not in ALLOWED_PRIORITIES:
        issues.append(
            ValidationIssue(
                index_path,
                f"prompt `{prompt_id}` has unsupported priority `{priority}`",
            )
        )

    file_value = record.get("file")
    if isinstance(file_value, str) and file_value.strip():
        prompt_path = module_dir / file_value
        if not prompt_path.exists():
            issues.append(
                ValidationIssue(
                    index_path,
                    f"prompt `{prompt_id}` file does not exist: "
                    f"{prompt_path.relative_to(root)}",
                )
            )
        elif not prompt_path.is_file():
            issues.append(
                ValidationIssue(
                    index_path,
                    f"prompt `{prompt_id}` path is not a file: "
                    f"{prompt_path.relative_to(root)}",
                )
            )

    issues.extend(
        _validate_nested_status(
            nested=record.get("module_execution"),
            nested_name="module_execution",
            status_field="status",
            allowed_statuses=ALLOWED_MODULE_EXECUTION_STATUSES,
            index_path=index_path,
            prompt_id=prompt_id,
        )
    )

    issues.extend(
        _validate_nested_status(
            nested=record.get("blueprint_review"),
            nested_name="blueprint_review",
            status_field="status",
            allowed_statuses=ALLOWED_BLUEPRINT_REVIEW_STATUSES,
            index_path=index_path,
            prompt_id=prompt_id,
        )
    )

    return issues


def _validate_prompt_queue_index(root: Path, index_path: Path) -> list[ValidationIssue]:
    data, issues = _load_yaml(index_path)
    if data is None:
        return issues

    module_dir = index_path.parent

    module = data.get("module")
    if module != module_dir.name:
        issues.append(
            ValidationIssue(
                index_path,
                f"`module` value `{module}` does not match directory "
                f"`{module_dir.name}`",
            )
        )

    prompt_queue = data.get("prompt_queue")
    if not isinstance(prompt_queue, list):
        issues.append(ValidationIssue(index_path, "`prompt_queue` must be a list"))
        return issues

    seen_prompt_ids: set[str] = set()
    seen_sequences: set[int] = set()

    for index, record in enumerate(prompt_queue):
        if not isinstance(record, dict):
            issues.append(
                ValidationIssue(index_path, f"`prompt_queue[{index}]` must be a mapping")
            )
            continue

        issues.extend(
            _validate_prompt_record(
                root=root,
                module_dir=module_dir,
                index_path=index_path,
                record=record,
                seen_prompt_ids=seen_prompt_ids,
                seen_sequences=seen_sequences,
            )
        )

    return issues


def validate_root(root: Path) -> ValidationResult:
    outgoing_root = root / OUTGOING_PROMPTS_DIR
    issues: list[ValidationIssue] = []

    if not outgoing_root.exists():
        return ValidationResult(
            checked_indexes=0,
            prompt_queue_indexes=0,
            legacy_indexes=0,
            issues=[
                ValidationIssue(
                    outgoing_root,
                    "outgoing prompts directory does not exist",
                )
            ],
        )

    index_paths = sorted(outgoing_root.glob("*/index.yaml"))

    checked_indexes = 0
    prompt_queue_indexes = 0
    legacy_indexes = 0

    for index_path in index_paths:
        checked_indexes += 1
        data, load_issues = _load_yaml(index_path)
        issues.extend(load_issues)

        if data is None:
            continue

        schema_version = data.get("schema_version")

        if schema_version is None:
            legacy_indexes += 1
            continue

        if schema_version != PROMPT_QUEUE_SCHEMA_VERSION:
            issues.append(
                ValidationIssue(
                    index_path,
                    f"unsupported schema_version `{schema_version}`",
                )
            )
            continue

        prompt_queue_indexes += 1
        issues.extend(_validate_prompt_queue_index(root, index_path))

    return ValidationResult(
        checked_indexes=checked_indexes,
        prompt_queue_indexes=prompt_queue_indexes,
        legacy_indexes=legacy_indexes,
        issues=issues,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate ForPrint Blueprint Prompt Queue v0.2 indexes."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Blueprint repository root. Defaults to current directory.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = validate_root(root)

    print("ForPrint Prompt Queue v0.2 validation")
    print(f"Root: {root}")
    print(f"Checked indexes: {result.checked_indexes}")
    print(f"Prompt Queue v0.2 indexes: {result.prompt_queue_indexes}")
    print(f"Legacy indexes skipped: {result.legacy_indexes}")

    if result.ok:
        print("✅ Prompt Queue validation passed")
        return 0

    print("❌ Prompt Queue validation failed")
    for issue in result.issues:
        try:
            rel_path = issue.path.resolve().relative_to(root)
        except ValueError:
            rel_path = issue.path
        print(f"- {rel_path}: {issue.message}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
