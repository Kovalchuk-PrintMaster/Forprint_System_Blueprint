#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

ALLOWED_STATUSES = {
    "completed_in_module",
    "completed_accepted",
    "applied_in_module",
    "completed_pending_blueprint_acceptance",
}

REQUIRED_ROOT_FIELDS = {
    "report_id",
    "prompt_id",
    "target_module",
    "phase",
    "completed_step",
    "status",
    "implementation_commit",
    "checks",
    "boundary_confirmation",
}

REQUIRED_CHECKS = {
    "governance_check",
    "make_check",
    "make_check_report",
}

BAD_PLACEHOLDERS = {
    "{now}",
    "{branch}",
    "{commit}",
    "{module_id}",
    "{phase}",
    "{completed_step}",
    "{prompt_id}",
    "{{now}}",
    "{{branch}}",
    "{{commit}}",
    "{{module_id}}",
    "{{phase}}",
    "{{completed_step}}",
    "{{prompt_id}}",
}

FORBIDDEN_TEXT_TOKENS = {
    "forprint_calculator_engine": "Use canonical module id `calculator_engine`.",
}

BOUNDARY_RULES = (
    ("production_api_added", False, "no_production_api_added", True),
    ("live_external_integrations_added", False, "no_real_external_integrations_added", True),
    ("database_ownership_added", False, "no_database_ownership_added", True),
    ("operational_data_ownership_added", False, "no_operational_data_ownership_added", True),
    ("queue_or_cache_dependency_added", False, "no_queue_redis_s3_dependency_added", True),
    ("one_c_writes_added", False, "no_1c_writes_added", True),
    ("automatic_posting_added", False, "no_automatic_posting_added", True),
    ("final_price_calculation_added", False, "no_final_price_calculation_added", True),
)


def _issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def _extract_frontmatter(path: Path, text: str) -> tuple[dict[str, Any] | None, list[str]]:
    issues: list[str] = []
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        return None, [_issue(path, "completion report must start with YAML frontmatter delimiter `---`")]

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        return None, [_issue(path, "completion report frontmatter has no closing `---` delimiter")]

    yaml_text = "\n".join(lines[1:closing_index]).strip()
    if not yaml_text:
        return None, [_issue(path, "completion report frontmatter is empty")]

    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        return None, [_issue(path, f"invalid YAML frontmatter: {exc}")]

    if not isinstance(data, dict):
        return None, [_issue(path, "completion report frontmatter root must be a mapping")]

    return data, issues


def _validate_no_bad_tokens(path: Path, text: str) -> list[str]:
    issues: list[str] = []

    for token in sorted(BAD_PLACEHOLDERS):
        if token in text:
            issues.append(_issue(path, f"unresolved placeholder token: {token}"))

    for token, hint in sorted(FORBIDDEN_TEXT_TOKENS.items()):
        if token in text:
            issues.append(_issue(path, f"forbidden token `{token}`. {hint}"))

    return issues


def _validate_required_string_fields(path: Path, data: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    missing = sorted(REQUIRED_ROOT_FIELDS.difference(data))
    for field_name in missing:
        issues.append(_issue(path, f"missing required frontmatter field `{field_name}`"))

    for field_name in (
        "report_id",
        "prompt_id",
        "target_module",
        "phase",
        "completed_step",
        "status",
        "implementation_commit",
    ):
        if field_name in data and (not isinstance(data[field_name], str) or not data[field_name].strip()):
            issues.append(_issue(path, f"`{field_name}` must be a non-empty string"))

    status = data.get("status")
    if isinstance(status, str) and status not in ALLOWED_STATUSES:
        issues.append(_issue(path, f"unsupported completion status `{status}`"))

    return issues


def _validate_expected_module(path: Path, data: dict[str, Any], expected_module: str | None) -> list[str]:
    if expected_module is None:
        return []

    target_module = data.get("target_module")
    if target_module != expected_module:
        return [
            _issue(
                path,
                f"target_module `{target_module}` does not match expected module `{expected_module}`",
            )
        ]

    return []


def _validate_checks(path: Path, data: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    checks = data.get("checks")
    if not isinstance(checks, dict):
        return [_issue(path, "`checks` must be a mapping")]

    for check_name in sorted(REQUIRED_CHECKS):
        value = checks.get(check_name)
        if value != "ok":
            issues.append(_issue(path, f"required check `{check_name}` must be `ok`"))

    for check_name, value in sorted(checks.items()):
        if value != "ok":
            issues.append(_issue(path, f"check `{check_name}` has non-ok value `{value}`"))

    return issues


def _validate_boundary_confirmation(path: Path, data: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    boundary = data.get("boundary_confirmation")
    if not isinstance(boundary, dict):
        return [_issue(path, "`boundary_confirmation` must be a mapping")]

    for positive_key, positive_expected, negative_key, negative_expected in BOUNDARY_RULES:
        positive_value = boundary.get(positive_key)
        negative_value = boundary.get(negative_key)

        positive_ok = positive_value is positive_expected
        negative_ok = negative_value is negative_expected

        if not positive_ok and not negative_ok:
            issues.append(
                _issue(
                    path,
                    f"boundary rule requires `{positive_key}: {positive_expected}` "
                    f"or `{negative_key}: {negative_expected}`",
                )
            )

    return issues


def _validate_next_questions(path: Path, data: dict[str, Any]) -> list[str]:
    if "next_questions_for_blueprint" not in data:
        return []

    questions = data["next_questions_for_blueprint"]
    if not isinstance(questions, list):
        return [_issue(path, "`next_questions_for_blueprint` must be a list when present")]

    issues: list[str] = []
    for index, question in enumerate(questions):
        if not isinstance(question, str) or not question.strip():
            issues.append(_issue(path, f"`next_questions_for_blueprint[{index}]` must be a non-empty string"))

    return issues


def _validate_standards_reviewed(path: Path, data: dict[str, Any]) -> list[str]:
    has_reviewed = "standards_reviewed" in data
    has_notes = "standards_alignment_notes" in data

    if not has_reviewed and not has_notes:
        return []

    issues: list[str] = []

    if not has_reviewed:
        issues.append(_issue(path, "`standards_reviewed` is required when standards metadata is present"))
    if not has_notes:
        issues.append(_issue(path, "`standards_alignment_notes` is required when standards metadata is present"))

    reviewed = data.get("standards_reviewed")
    if has_reviewed:
        if not isinstance(reviewed, list) or not reviewed:
            issues.append(_issue(path, "`standards_reviewed` must be a non-empty list when present"))
        else:
            for index, item in enumerate(reviewed):
                if isinstance(item, str):
                    if not item.strip():
                        issues.append(_issue(path, f"`standards_reviewed[{index}]` must be non-empty"))
                    continue

                if isinstance(item, dict):
                    standard_id = item.get("standard_id")
                    file_path = item.get("file")
                    has_identity = (
                        isinstance(standard_id, str)
                        and bool(standard_id.strip())
                    ) or (
                        isinstance(file_path, str)
                        and bool(file_path.strip())
                    )
                    if not has_identity:
                        issues.append(
                            _issue(
                                path,
                                f"`standards_reviewed[{index}]` must include non-empty `standard_id` or `file`",
                            )
                        )
                    continue

                issues.append(
                    _issue(
                        path,
                        f"`standards_reviewed[{index}]` must be a string or mapping",
                    )
                )

    return issues


def _validate_standards_alignment_notes(path: Path, data: dict[str, Any]) -> list[str]:
    if "standards_alignment_notes" not in data:
        return []

    notes = data["standards_alignment_notes"]
    if not isinstance(notes, list) or not notes:
        return [_issue(path, "`standards_alignment_notes` must be a non-empty list when present")]

    issues: list[str] = []
    for index, note in enumerate(notes):
        if not isinstance(note, str) or not note.strip():
            issues.append(_issue(path, f"`standards_alignment_notes[{index}]` must be a non-empty string"))

    return issues

def validate_completion_report(path: Path, expected_module: str | None = None) -> list[str]:
    text = path.read_text(encoding="utf-8")

    issues = _validate_no_bad_tokens(path, text)

    data, frontmatter_issues = _extract_frontmatter(path, text)
    issues.extend(frontmatter_issues)

    if data is None:
        return issues

    issues.extend(_validate_required_string_fields(path, data))
    issues.extend(_validate_expected_module(path, data, expected_module))
    issues.extend(_validate_checks(path, data))
    issues.extend(_validate_boundary_confirmation(path, data))
    issues.extend(_validate_next_questions(path, data))
    issues.extend(_validate_standards_reviewed(path, data))
    issues.extend(_validate_standards_alignment_notes(path, data))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForPrint module prompt completion report frontmatter.")
    parser.add_argument("report_path", help="Path to completion report markdown file.")
    parser.add_argument("--module-id", default=None, help="Expected target_module value.")
    args = parser.parse_args()

    report_path = Path(args.report_path)
    if not report_path.exists():
        print(f"❌ Completion report does not exist: {report_path}")
        return 1

    issues = validate_completion_report(report_path, expected_module=args.module_id)

    if issues:
        print("❌ Completion report validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Completion report validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
