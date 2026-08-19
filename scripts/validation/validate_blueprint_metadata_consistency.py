#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

BLUEPRINT_MODULE_ID = "forprint_system_blueprint"
PROMPT_QUEUE_SCHEMA = "prompt_queue_v0_2"
GOVERNANCE_DIR = Path(
    "coordination/internal_work/blueprint/governance"
)
OUTGOING_DIR = Path("coordination/outgoing_prompts")
CORRECTION_SCHEMA = "blueprint_governance_metadata_correction_v0_1"
CORRECTABLE_FIELDS = {
    "metadata.module_id": BLUEPRINT_MODULE_ID,
    "metadata.owner": BLUEPRINT_MODULE_ID,
}


@dataclass(frozen=True)
class ValidationIssue:
    path: Path
    code: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    governance_files: int
    prompt_indexes: int
    prompt_records: int
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def _load_mapping(
    path: Path,
) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return None, [
            ValidationIssue(path, "read_error", str(error))
        ]

    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as error:
        return None, [
            ValidationIssue(path, "invalid_yaml", str(error))
        ]

    if not isinstance(loaded, dict):
        return None, [
            ValidationIssue(
                path,
                "root_not_mapping",
                "YAML root must be a mapping",
            )
        ]

    return loaded, []


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nested_value(data: dict[str, Any], field: str) -> Any:
    current: Any = data
    for part in field.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _collect_metadata_corrections(
    root: Path,
    paths: list[Path],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    list[ValidationIssue],
]:
    corrections: dict[tuple[str, str], dict[str, Any]] = {}
    issues: list[ValidationIssue] = []
    governance_root = (root / GOVERNANCE_DIR).resolve()

    for correction_path in paths:
        data, load_issues = _load_mapping(correction_path)
        issues.extend(load_issues)
        if (
            data is None
            or data.get("schema_version") != CORRECTION_SCHEMA
        ):
            continue

        metadata = data.get("metadata")
        correction = data.get("correction")
        if (
            not isinstance(metadata, dict)
            or not isinstance(correction, dict)
        ):
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_structure_invalid",
                    "Metadata correction requires metadata and "
                    "correction mappings",
                )
            )
            continue

        if metadata.get("module_id") != BLUEPRINT_MODULE_ID:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_module_id_mismatch",
                    "Metadata correction record requires "
                    f"metadata.module_id == {BLUEPRINT_MODULE_ID!r}",
                )
            )
            continue

        if metadata.get("owner") != BLUEPRINT_MODULE_ID:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_owner_mismatch",
                    "Metadata correction record requires "
                    f"metadata.owner == {BLUEPRINT_MODULE_ID!r}",
                )
            )
            continue

        if metadata.get("immutable_correction_record") is not True:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_not_immutable",
                    "metadata.immutable_correction_record must be true",
                )
            )
            continue

        target_value = correction.get("target_path")
        target_sha = correction.get("target_sha256")
        field = correction.get("field")
        observed = correction.get("observed_value")
        corrected = correction.get("corrected_value")

        if (
            not isinstance(target_value, str)
            or not target_value.strip()
        ):
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_target_path_invalid",
                    "correction.target_path must be a non-empty "
                    "repository-relative path",
                )
            )
            continue

        target = (root / target_value).resolve()
        try:
            target.relative_to(governance_root)
        except ValueError:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_target_outside_governance",
                    "Correction target must stay inside Blueprint "
                    "governance directory",
                )
            )
            continue

        if target == correction_path.resolve():
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_self_target",
                    "Correction record may not target itself",
                )
            )
            continue

        if not target.is_file():
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_target_missing",
                    f"Correction target does not exist: {target_value}",
                )
            )
            continue

        if not isinstance(target_sha, str) or len(target_sha) != 64:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_target_sha256_invalid",
                    "correction.target_sha256 must be a 64-character "
                    "SHA256",
                )
            )
            continue

        actual_sha = _sha256(target)
        if actual_sha != target_sha:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_target_sha256_mismatch",
                    "Correction target SHA256 mismatch: "
                    f"expected {target_sha}, got {actual_sha}",
                )
            )
            continue

        if (
            not isinstance(field, str)
            or field not in CORRECTABLE_FIELDS
        ):
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_field_not_allowed",
                    "correction.field must be one of "
                    f"{sorted(CORRECTABLE_FIELDS)}",
                )
            )
            continue

        expected = CORRECTABLE_FIELDS[field]
        if corrected != expected:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_value_not_canonical",
                    f"{field} may only be corrected to {expected!r}",
                )
            )
            continue

        target_data, target_issues = _load_mapping(target)
        issues.extend(target_issues)
        if target_data is None:
            continue

        target_metadata = target_data.get("metadata")
        if (
            not isinstance(target_metadata, dict)
            or target_metadata.get("immutable_decision_record")
            is not True
        ):
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_target_not_immutable",
                    "Correction target must have "
                    "metadata.immutable_decision_record: true",
                )
            )
            continue

        actual_observed = _nested_value(target_data, field)
        if actual_observed != observed:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "correction_observed_value_mismatch",
                    f"{field} expected {observed!r}; "
                    f"target has {actual_observed!r}",
                )
            )
            continue

        relative = target.relative_to(root.resolve()).as_posix()
        key = (relative, field)
        if key in corrections:
            issues.append(
                ValidationIssue(
                    correction_path,
                    "duplicate_metadata_correction",
                    "Multiple corrections target "
                    f"{relative}:{field}",
                )
            )
            continue

        corrections[key] = {
            "observed_value": observed,
            "corrected_value": corrected,
        }

    return corrections, issues


def _has_exact_metadata_correction(
    *,
    corrections: dict[tuple[str, str], dict[str, Any]],
    root: Path,
    path: Path,
    field: str,
    observed_value: Any,
    corrected_value: Any,
) -> bool:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    record = corrections.get((relative, field))
    return bool(
        record
        and record.get("observed_value") == observed_value
        and record.get("corrected_value") == corrected_value
    )


def _validate_governance_records(
    root: Path,
) -> tuple[int, list[ValidationIssue]]:
    directory = root / GOVERNANCE_DIR
    issues: list[ValidationIssue] = []

    if not directory.is_dir():
        return 0, [
            ValidationIssue(
                directory,
                "governance_directory_missing",
                "Blueprint governance directory does not exist",
            )
        ]

    paths = sorted(directory.glob("*.yaml"))
    if not paths:
        return 0, [
            ValidationIssue(
                directory,
                "governance_records_missing",
                "No Blueprint governance YAML records found",
            )
        ]

    corrections, correction_issues = _collect_metadata_corrections(root, paths)
    issues.extend(correction_issues)

    for path in paths:
        data, load_issues = _load_mapping(path)
        issues.extend(load_issues)
        if data is None:
            continue

        schema_version = data.get("schema_version")
        if not isinstance(schema_version, str) or not schema_version.strip():
            issues.append(
                ValidationIssue(
                    path,
                    "schema_version_missing",
                    "Governance record requires a non-empty schema_version",
                )
            )

        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            issues.append(
                ValidationIssue(
                    path,
                    "metadata_missing",
                    "Governance record requires a metadata mapping",
                )
            )
            continue

        module_id = metadata.get("module_id")
        if (
            module_id is not None
            and module_id != BLUEPRINT_MODULE_ID
            and not _has_exact_metadata_correction(
                corrections=corrections,
                root=root,
                path=path,
                field="metadata.module_id",
                observed_value=module_id,
                corrected_value=BLUEPRINT_MODULE_ID,
            )
        ):
            issues.append(
                ValidationIssue(
                    path,
                    "module_id_mismatch",
                    "metadata.module_id, when present, must equal "
                    f"{BLUEPRINT_MODULE_ID!r}; got {module_id!r}",
                )
            )

        owner = metadata.get("owner")
        if (
            owner is not None
            and owner != BLUEPRINT_MODULE_ID
            and not _has_exact_metadata_correction(
                corrections=corrections,
                root=root,
                path=path,
                field="metadata.owner",
                observed_value=owner,
                corrected_value=BLUEPRINT_MODULE_ID,
            )
        ):
            issues.append(
                ValidationIssue(
                    path,
                    "owner_mismatch",
                    "metadata.owner, when present, must equal "
                    f"{BLUEPRINT_MODULE_ID!r}; got {owner!r}",
                )
            )

    return len(paths), issues


def _records_for_index(
    data: dict[str, Any],
    *,
    path: Path,
) -> tuple[list[dict[str, Any]], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []

    if data.get("schema_version") == PROMPT_QUEUE_SCHEMA:
        value = data.get("prompt_queue")
        field = "prompt_queue"
    else:
        active = data.get("active_prompts", [])
        completed = data.get("completed_prompts", [])

        if not isinstance(active, list):
            issues.append(
                ValidationIssue(
                    path,
                    "active_prompts_not_list",
                    "active_prompts must be a list",
                )
            )
            active = []

        if not isinstance(completed, list):
            issues.append(
                ValidationIssue(
                    path,
                    "completed_prompts_not_list",
                    "completed_prompts must be a list",
                )
            )
            completed = []

        value = [*active, *completed]
        field = "active_prompts/completed_prompts"

    if not isinstance(value, list):
        issues.append(
            ValidationIssue(
                path,
                "prompt_records_not_list",
                f"{field} must be a list",
            )
        )
        return [], issues

    records: list[dict[str, Any]] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            issues.append(
                ValidationIssue(
                    path,
                    "prompt_record_not_mapping",
                    f"{field}[{index}] must be a mapping",
                )
            )
            continue
        records.append(record)

    return records, issues


def _validate_prompt_indexes(
    root: Path,
) -> tuple[int, int, list[ValidationIssue]]:
    directory = root / OUTGOING_DIR
    issues: list[ValidationIssue] = []

    if not directory.is_dir():
        return 0, 0, [
            ValidationIssue(
                directory,
                "outgoing_directory_missing",
                "Outgoing prompt directory does not exist",
            )
        ]

    index_paths = sorted(directory.glob("*/index.yaml"))
    if not index_paths:
        return 0, 0, [
            ValidationIssue(
                directory,
                "prompt_indexes_missing",
                "No outgoing prompt indexes found",
            )
        ]

    seen_prompt_ids: dict[str, Path] = {}
    prompt_records = 0

    for index_path in index_paths:
        module_dir = index_path.parent
        module_id = module_dir.name

        data, load_issues = _load_mapping(index_path)
        issues.extend(load_issues)
        if data is None:
            continue

        declared_module = data.get("module")
        if declared_module is not None and declared_module != module_id:
            issues.append(
                ValidationIssue(
                    index_path,
                    "module_directory_mismatch",
                    f"module value {declared_module!r} does not match "
                    f"directory {module_id!r}",
                )
            )

        records, record_issues = _records_for_index(
            data,
            path=index_path,
        )
        issues.extend(record_issues)

        for record in records:
            prompt_records += 1
            prompt_id = record.get("prompt_id")

            if not isinstance(prompt_id, str) or not prompt_id.strip():
                issues.append(
                    ValidationIssue(
                        index_path,
                        "prompt_id_missing",
                        "Prompt record requires a non-empty prompt_id",
                    )
                )
            elif prompt_id in seen_prompt_ids:
                first = seen_prompt_ids[prompt_id]
                issues.append(
                    ValidationIssue(
                        index_path,
                        "duplicate_prompt_id",
                        f"prompt_id {prompt_id!r} already appears in "
                        f"{first.relative_to(root)}",
                    )
                )
            else:
                seen_prompt_ids[prompt_id] = index_path

            target_module = record.get("target_module")
            if (
                target_module is not None
                and target_module != module_id
            ):
                issues.append(
                    ValidationIssue(
                        index_path,
                        "target_module_mismatch",
                        f"target_module {target_module!r} does not match "
                        f"directory {module_id!r}",
                    )
                )

            file_value = record.get("file")
            if file_value is None:
                continue
            if not isinstance(file_value, str) or not file_value.strip():
                issues.append(
                    ValidationIssue(
                        index_path,
                        "file_reference_invalid",
                        "Prompt file reference must be a non-empty string",
                    )
                )
                continue

            module_root = module_dir.resolve()
            candidate = (module_dir / file_value).resolve()

            try:
                candidate.relative_to(module_root)
            except ValueError:
                issues.append(
                    ValidationIssue(
                        index_path,
                        "file_reference_escapes_module",
                        f"Prompt file reference escapes module directory: "
                        f"{file_value}",
                    )
                )
                continue

            if not candidate.is_file():
                issues.append(
                    ValidationIssue(
                        index_path,
                        "broken_file_reference",
                        f"Prompt file does not exist: {file_value}",
                    )
                )

    return len(index_paths), prompt_records, issues


def validate_root(root: Path) -> ValidationResult:
    resolved = root.resolve()

    governance_files, governance_issues = (
        _validate_governance_records(resolved)
    )
    prompt_indexes, prompt_records, prompt_issues = (
        _validate_prompt_indexes(resolved)
    )

    return ValidationResult(
        governance_files=governance_files,
        prompt_indexes=prompt_indexes,
        prompt_records=prompt_records,
        issues=tuple([*governance_issues, *prompt_issues]),
    )


def _display_path(root: Path, path: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate current Blueprint governance and outgoing-prompt "
            "metadata consistency without repository mutation."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Blueprint repository root; defaults to current directory.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    result = validate_root(root)

    print("ForPrint Blueprint metadata consistency validation")
    print(f"Root: {root}")
    print(f"Governance YAML records: {result.governance_files}")
    print(f"Outgoing prompt indexes: {result.prompt_indexes}")
    print(f"Prompt records: {result.prompt_records}")
    print(f"Issues: {len(result.issues)}")

    if result.ok:
        print("RESULT: PASSED")
        return 0

    for issue in result.issues:
        print(
            f"- {_display_path(root, issue.path)}: "
            f"{issue.code}: {issue.message}"
        )

    print("RESULT: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
