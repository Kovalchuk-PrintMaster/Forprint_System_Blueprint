from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ALLOWED_PRIORITIES = {"p0", "p1", "p2", "hold", "selective", "deferred"}
PRIORITY_ALIASES = {
    "high": "p0",
    "medium": "p1",
    "low": "p2",
}

REQUIRED_COORDINATION_FILES = [
    "coordination/status/current_status.yaml",
    "coordination/status/current_status.md",
    "coordination/status/next_questions_for_blueprint.md",
    "coordination/prompts/index.yaml",
    "coordination/reports/index.yaml",
]

REQUIRED_CURRENT_STATUS_KEYS = [
    "module_id",
    "module_name",
    "module_status",
    "priority",
    "current_phase",
    "last_completed_step",
    "last_commit",
    "branch",
    "checks",
    "boundary",
    "recommended_next_step",
    "updated_at",
]


@dataclass(frozen=True)
class CoordinationIssue:
    severity: str
    code: str
    message: str
    path: str


@dataclass(frozen=True)
class CoordinationCheckResult:
    module_root: str
    ok: bool
    errors: list[CoordinationIssue]
    warnings: list[CoordinationIssue]


@dataclass(frozen=True)
class CoordinationFixResult:
    module_root: str
    changed_files: list[str]
    skipped: list[str]
    warnings: list[str]


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, data: Any) -> None:
    path.write_text(
        yaml.safe_dump(
            data,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def issue(
    severity: str,
    code: str,
    message: str,
    path: str,
) -> CoordinationIssue:
    return CoordinationIssue(
        severity=severity,
        code=code,
        message=message,
        path=path,
    )


def _safe_load_yaml(
    module_root: Path,
    relative_path: str,
    errors: list[CoordinationIssue],
) -> Any | None:
    path = module_root / relative_path
    if not path.exists():
        errors.append(
            issue(
                "ERROR",
                "missing_file",
                f"Required file is missing: {relative_path}",
                relative_path,
            )
        )
        return None

    try:
        return read_yaml(path)
    except yaml.YAMLError as exc:
        errors.append(
            issue(
                "ERROR",
                "invalid_yaml",
                f"Invalid YAML in {relative_path}: {exc}",
                relative_path,
            )
        )
        return None


def _find_duplicate_ids(entries: list[dict[str, Any]], key: str) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for entry in entries:
        value = entry.get(key)
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    return duplicates


def _check_file_references(
    module_root: Path,
    entries: list[dict[str, Any]],
    file_key: str,
    errors: list[CoordinationIssue],
    source_path: str,
) -> None:
    for entry in entries:
        file_value = entry.get(file_key)
        if not file_value:
            errors.append(
                issue(
                    "ERROR",
                    "missing_reference",
                    f"Entry in {source_path} has no {file_key}",
                    source_path,
                )
            )
            continue

        referenced_file = module_root / str(file_value)
        if not referenced_file.exists():
            errors.append(
                issue(
                    "ERROR",
                    "broken_reference",
                    f"Referenced file does not exist: {file_value}",
                    source_path,
                )
            )


def _check_current_status(
    status: dict[str, Any] | None,
    errors: list[CoordinationIssue],
    warnings: list[CoordinationIssue],
) -> None:
    source_path = "coordination/status/current_status.yaml"

    if not isinstance(status, dict):
        errors.append(
            issue(
                "ERROR",
                "invalid_current_status",
                "current_status.yaml must contain a YAML mapping",
                source_path,
            )
        )
        return

    for key in REQUIRED_CURRENT_STATUS_KEYS:
        if key not in status:
            errors.append(
                issue(
                    "ERROR",
                    "missing_current_status_key",
                    f"current_status.yaml is missing required key: {key}",
                    source_path,
                )
            )

    priority = status.get("priority")
    if priority not in ALLOWED_PRIORITIES:
        if priority in PRIORITY_ALIASES:
            warnings.append(
                issue(
                    "WARNING",
                    "priority_alias",
                    (
                        f"priority uses alias {priority!r}; "
                        f"preferred value is {PRIORITY_ALIASES[priority]!r}"
                    ),
                    source_path,
                )
            )
        else:
            errors.append(
                issue(
                    "ERROR",
                    "invalid_priority",
                    f"Invalid priority: {priority!r}",
                    source_path,
                )
            )

    if status.get("last_commit") == "pending":
        warnings.append(
            issue(
                "WARNING",
                "pending_last_commit",
                "last_commit is still pending",
                source_path,
            )
        )


def _check_prompt_index(
    prompt_index: dict[str, Any] | None,
    module_root: Path,
    errors: list[CoordinationIssue],
) -> None:
    source_path = "coordination/prompts/index.yaml"

    if not isinstance(prompt_index, dict):
        errors.append(
            issue(
                "ERROR",
                "invalid_prompt_index",
                "prompts/index.yaml must contain a YAML mapping",
                source_path,
            )
        )
        return

    prompts = prompt_index.get("prompts", [])
    if not isinstance(prompts, list):
        errors.append(
            issue(
                "ERROR",
                "invalid_prompt_list",
                "prompts/index.yaml key 'prompts' must be a list",
                source_path,
            )
        )
        return

    duplicates = _find_duplicate_ids(prompts, "prompt_id")
    for duplicate in sorted(duplicates):
        errors.append(
            issue(
                "ERROR",
                "duplicate_prompt_id",
                f"Duplicate prompt_id: {duplicate}",
                source_path,
            )
        )

    _check_file_references(
        module_root=module_root,
        entries=prompts,
        file_key="file",
        errors=errors,
        source_path=source_path,
    )


def _check_report_index(
    report_index: dict[str, Any] | None,
    module_root: Path,
    errors: list[CoordinationIssue],
    warnings: list[CoordinationIssue],
) -> None:
    source_path = "coordination/reports/index.yaml"

    if not isinstance(report_index, dict):
        errors.append(
            issue(
                "ERROR",
                "invalid_report_index",
                "reports/index.yaml must contain a YAML mapping",
                source_path,
            )
        )
        return

    reports = report_index.get("reports", [])
    if not isinstance(reports, list):
        errors.append(
            issue(
                "ERROR",
                "invalid_report_list",
                "reports/index.yaml key 'reports' must be a list",
                source_path,
            )
        )
        return

    duplicates = _find_duplicate_ids(reports, "report_id")
    for duplicate in sorted(duplicates):
        errors.append(
            issue(
                "ERROR",
                "duplicate_report_id",
                f"Duplicate report_id: {duplicate}",
                source_path,
            )
        )

    _check_file_references(
        module_root=module_root,
        entries=reports,
        file_key="report_file",
        errors=errors,
        source_path=source_path,
    )

    for report in reports:
        if report.get("status") == "completed":
            if report.get("commit") == "pending":
                warnings.append(
                    issue(
                        "WARNING",
                        "completed_report_pending_commit",
                        (
                            "Completed report still has commit: pending "
                            f"for report_id={report.get('report_id')}"
                        ),
                        source_path,
                    )
                )
            if report.get("pushed") is False:
                warnings.append(
                    issue(
                        "WARNING",
                        "completed_report_not_pushed",
                        (
                            "Completed report has pushed: false "
                            f"for report_id={report.get('report_id')}"
                        ),
                        source_path,
                    )
                )


def check_module_coordination_metadata(module_root: Path) -> CoordinationCheckResult:
    module_root = module_root.resolve()

    errors: list[CoordinationIssue] = []
    warnings: list[CoordinationIssue] = []

    if not module_root.exists():
        errors.append(
            issue(
                "ERROR",
                "missing_module_root",
                f"Module root does not exist: {module_root}",
                str(module_root),
            )
        )
        return CoordinationCheckResult(
            module_root=str(module_root),
            ok=False,
            errors=errors,
            warnings=warnings,
        )

    for relative_path in REQUIRED_COORDINATION_FILES:
        if not (module_root / relative_path).exists():
            errors.append(
                issue(
                    "ERROR",
                    "missing_file",
                    f"Required file is missing: {relative_path}",
                    relative_path,
                )
            )

    current_status = _safe_load_yaml(
        module_root,
        "coordination/status/current_status.yaml",
        errors,
    )
    prompt_index = _safe_load_yaml(
        module_root,
        "coordination/prompts/index.yaml",
        errors,
    )
    report_index = _safe_load_yaml(
        module_root,
        "coordination/reports/index.yaml",
        errors,
    )

    _check_current_status(current_status, errors, warnings)
    _check_prompt_index(prompt_index, module_root, errors)
    _check_report_index(report_index, module_root, errors, warnings)

    return CoordinationCheckResult(
        module_root=str(module_root),
        ok=not errors,
        errors=errors,
        warnings=warnings,
    )


def _entry_signature(entry: dict[str, Any]) -> str:
    return yaml.safe_dump(entry, allow_unicode=True, sort_keys=True)


def _dedupe_exact_entries(
    entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], bool]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    changed = False

    for entry in entries:
        signature = _entry_signature(entry)
        if signature in seen:
            changed = True
            continue
        seen.add(signature)
        output.append(entry)

    return output, changed


def _git_head(module_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(module_root), "rev-parse", "--short", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def fix_module_coordination_metadata(
    module_root: Path,
    update_git_commit: bool = False,
) -> CoordinationFixResult:
    module_root = module_root.resolve()

    changed_files: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []

    current_status_path = module_root / "coordination/status/current_status.yaml"
    prompts_index_path = module_root / "coordination/prompts/index.yaml"
    reports_index_path = module_root / "coordination/reports/index.yaml"

    if current_status_path.exists():
        current_status = read_yaml(current_status_path) or {}
        changed = False

        priority = current_status.get("priority")
        if priority in PRIORITY_ALIASES:
            current_status["priority"] = PRIORITY_ALIASES[priority]
            changed = True

        if update_git_commit and current_status.get("last_commit") == "pending":
            commit = _git_head(module_root)
            if commit:
                current_status["last_commit"] = commit
                changed = True
            else:
                warnings.append("Could not read git HEAD for last_commit update")

        if changed:
            write_yaml(current_status_path, current_status)
            changed_files.append("coordination/status/current_status.yaml")
    else:
        skipped.append("coordination/status/current_status.yaml")

    if prompts_index_path.exists():
        prompt_index = read_yaml(prompts_index_path) or {}
        prompts = prompt_index.get("prompts", [])
        if isinstance(prompts, list):
            deduped, changed = _dedupe_exact_entries(prompts)
            if changed:
                prompt_index["prompts"] = deduped
                write_yaml(prompts_index_path, prompt_index)
                changed_files.append("coordination/prompts/index.yaml")
        else:
            skipped.append("coordination/prompts/index.yaml invalid prompts list")
    else:
        skipped.append("coordination/prompts/index.yaml")

    if reports_index_path.exists():
        report_index = read_yaml(reports_index_path) or {}
        reports = report_index.get("reports", [])
        if isinstance(reports, list):
            deduped, changed = _dedupe_exact_entries(reports)
            if update_git_commit:
                commit = _git_head(module_root)
                if commit:
                    for report in deduped:
                        if report.get("commit") == "pending":
                            report["commit"] = commit
                            changed = True
                else:
                    warnings.append("Could not read git HEAD for report commit update")

            if changed:
                report_index["reports"] = deduped
                write_yaml(reports_index_path, report_index)
                changed_files.append("coordination/reports/index.yaml")
        else:
            skipped.append("coordination/reports/index.yaml invalid reports list")
    else:
        skipped.append("coordination/reports/index.yaml")

    return CoordinationFixResult(
        module_root=str(module_root),
        changed_files=changed_files,
        skipped=skipped,
        warnings=warnings,
    )
