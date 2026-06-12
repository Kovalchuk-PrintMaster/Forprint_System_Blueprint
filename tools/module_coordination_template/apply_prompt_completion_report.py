#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PLANNED_COORDINATION_FILES = [
    "coordination/status/current_status.yaml",
    "coordination/prompts/index.yaml",
    "coordination/reports/index.yaml",
    "coordination/status/next_questions_for_blueprint.md",
]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _load_validator_module() -> Any:
    validator_path = Path(__file__).with_name("validate_prompt_completion_report.py")

    if not validator_path.exists():
        raise RuntimeError(f"Validator script not found: {validator_path}")

    spec = importlib.util.spec_from_file_location(
        "validate_prompt_completion_report",
        validator_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator script: {validator_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _extract_frontmatter(report_path: Path) -> dict[str, Any]:
    text = report_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise ValueError("completion report must start with YAML frontmatter delimiter `---`")

    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        raise ValueError("completion report frontmatter has no closing `---` delimiter")

    yaml_text = "\n".join(lines[1:closing_index]).strip()
    data = yaml.safe_load(yaml_text)

    if not isinstance(data, dict):
        raise ValueError("completion report frontmatter root must be a mapping")

    return data


def _normalize_boundary_confirmation(boundary: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(boundary)

    mappings = {
        "production_api_added": ("no_production_api_added", True),
        "live_external_integrations_added": ("no_real_external_integrations_added", True),
        "database_ownership_added": ("no_database_ownership_added", True),
        "operational_data_ownership_added": ("no_operational_data_ownership_added", True),
        "queue_or_cache_dependency_added": ("no_queue_redis_s3_dependency_added", True),
        "one_c_writes_added": ("no_1c_writes_added", True),
        "automatic_posting_added": ("no_automatic_posting_added", True),
        "final_price_calculation_added": ("no_final_price_calculation_added", True),
    }

    for positive_key, (negative_key, safe_value) in mappings.items():
        if positive_key in normalized and normalized[positive_key] is False:
            normalized.setdefault(negative_key, safe_value)

    return normalized


def _relative_report_path(report_path: Path, module_root: Path) -> str:
    try:
        return str(report_path.resolve().relative_to(module_root.resolve()))
    except ValueError:
        return str(report_path)


def build_planned_updates(
    frontmatter: dict[str, Any],
    *,
    report_path: Path | None = None,
    module_root: Path | None = None,
) -> dict[str, Any]:
    checks = frontmatter.get("checks", {})
    boundary = frontmatter.get("boundary_confirmation", {})
    normalized_boundary = (
        _normalize_boundary_confirmation(boundary)
        if isinstance(boundary, dict)
        else {}
    )

    report_file = frontmatter.get("report_file")
    if not report_file and report_path is not None and module_root is not None:
        report_file = _relative_report_path(report_path, module_root)
    if not report_file:
        report_file = f"coordination/reports/{frontmatter['report_id']}_completion.md"

    implementation_commit = frontmatter["implementation_commit"]
    completion_report_commit = frontmatter.get("completion_report_commit")
    last_commit = completion_report_commit or implementation_commit

    prompt_record: dict[str, Any] = {
        "prompt_id": frontmatter["prompt_id"],
        "source": "forprint_system_blueprint",
        "status": frontmatter["status"],
        "implementation_commit": implementation_commit,
        "phase": frontmatter["phase"],
        "completed_step": frontmatter["completed_step"],
        "report_file": report_file,
    }

    if completion_report_commit:
        prompt_record["completion_report_commit"] = completion_report_commit

    report_record: dict[str, Any] = {
        "report_id": frontmatter["report_id"],
        "prompt_id": frontmatter["prompt_id"],
        "phase": frontmatter["phase"],
        "status": "completed",
        "implementation_commit": implementation_commit,
        "report_file": report_file,
        "validation_results": checks,
        "boundary_confirmation": normalized_boundary,
    }

    if completion_report_commit:
        report_record["completion_report_commit"] = completion_report_commit

    return {
        "current_status": {
            "module_id": frontmatter["target_module"],
            "current_phase": frontmatter["phase"],
            "last_completed_step": frontmatter["completed_step"],
            "last_commit": last_commit,
            "checks": checks,
            "boundary_confirmation": normalized_boundary,
        },
        "prompts_index_record": prompt_record,
        "reports_index_record": report_record,
        "next_questions_for_blueprint": frontmatter.get("next_questions_for_blueprint", []),
    }


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")

    return data


def _write_yaml_mapping(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _upsert_record(records: list[Any], key: str, record: dict[str, Any]) -> list[dict[str, Any]]:
    normalized_records: list[dict[str, Any]] = []
    replaced = False

    for existing in records:
        if not isinstance(existing, dict):
            continue

        if existing.get(key) == record[key]:
            normalized_records.append(record)
            replaced = True
        else:
            normalized_records.append(existing)

    if not replaced:
        normalized_records.append(record)

    return normalized_records


def _write_current_status(module_root: Path, planned_updates: dict[str, Any]) -> Path:
    path = module_root / "coordination/status/current_status.yaml"
    current = _read_yaml_mapping(path)
    current.update(planned_updates["current_status"])
    current["last_updated"] = _utc_now()

    _write_yaml_mapping(path, current)
    return path


def _write_prompts_index(module_root: Path, planned_updates: dict[str, Any]) -> Path:
    path = module_root / "coordination/prompts/index.yaml"
    record = planned_updates["prompts_index_record"]

    data = _read_yaml_mapping(path)
    data["module_id"] = planned_updates["current_status"]["module_id"]
    data["updated_at"] = _utc_now()
    data["prompts"] = _upsert_record(data.get("prompts", []), "prompt_id", record)

    _write_yaml_mapping(path, data)
    return path


def _write_reports_index(module_root: Path, planned_updates: dict[str, Any]) -> Path:
    path = module_root / "coordination/reports/index.yaml"
    record = planned_updates["reports_index_record"]

    data = _read_yaml_mapping(path)
    data["module_id"] = planned_updates["current_status"]["module_id"]
    data["updated_at"] = _utc_now()
    data["reports"] = _upsert_record(data.get("reports", []), "report_id", record)

    _write_yaml_mapping(path, data)
    return path


def _write_next_questions(module_root: Path, planned_updates: dict[str, Any]) -> Path:
    path = module_root / "coordination/status/next_questions_for_blueprint.md"
    path.parent.mkdir(parents=True, exist_ok=True)

    module_id = planned_updates["current_status"]["module_id"]
    phase = planned_updates["current_status"]["current_phase"]
    completed_step = planned_updates["current_status"]["last_completed_step"]
    questions = planned_updates.get("next_questions_for_blueprint", [])

    lines = [
        "# Next questions for ForPrint System Blueprint",
        "",
        f"Module: `{module_id}`",
        f"Phase: `{phase}`",
        f"Completed step: `{completed_step}`",
        "",
        "## Questions",
        "",
    ]

    if questions:
        lines.extend(f"- {question}" for question in questions)
    else:
        lines.append("- No open questions.")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_planned_updates(module_root: Path, planned_updates: dict[str, Any]) -> list[str]:
    written_paths = [
        _write_current_status(module_root, planned_updates),
        _write_prompts_index(module_root, planned_updates),
        _write_reports_index(module_root, planned_updates),
        _write_next_questions(module_root, planned_updates),
    ]

    return [str(path) for path in written_paths]


def apply_prompt_completion_report(
    report_path: Path,
    *,
    expected_module: str | None = None,
    write: bool = False,
    module_root: Path | None = None,
) -> dict[str, Any]:
    module_root = module_root or Path.cwd()

    validator = _load_validator_module()
    issues = validator.validate_completion_report(
        report_path,
        expected_module=expected_module,
    )

    if issues:
        return {
            "ok": False,
            "mode": "dry_run" if not write else "write",
            "report_path": str(report_path),
            "issues": issues,
        }

    frontmatter = _extract_frontmatter(report_path)
    planned_updates = build_planned_updates(
        frontmatter,
        report_path=report_path,
        module_root=module_root,
    )

    if write:
        written_files = write_planned_updates(module_root, planned_updates)
        return {
            "ok": True,
            "mode": "write",
            "report_path": str(report_path),
            "target_module": frontmatter["target_module"],
            "prompt_id": frontmatter["prompt_id"],
            "report_id": frontmatter["report_id"],
            "phase": frontmatter["phase"],
            "completed_step": frontmatter["completed_step"],
            "written_files": written_files,
            "planned_updates": planned_updates,
        }

    return {
        "ok": True,
        "mode": "dry_run",
        "report_path": str(report_path),
        "target_module": frontmatter["target_module"],
        "prompt_id": frontmatter["prompt_id"],
        "report_id": frontmatter["report_id"],
        "phase": frontmatter["phase"],
        "completed_step": frontmatter["completed_step"],
        "planned_files": PLANNED_COORDINATION_FILES,
        "planned_updates": planned_updates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply ForPrint module prompt completion report."
    )
    parser.add_argument("report_path", help="Path to completion report markdown file.")
    parser.add_argument("--module-id", default=None, help="Expected target_module value.")
    parser.add_argument(
        "--module-root",
        default=".",
        help="Module repository root. Defaults to current working directory.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write coordination files. Without this flag the command runs dry-run only.",
    )
    args = parser.parse_args()

    report_path = Path(args.report_path)
    if not report_path.exists():
        print(f"❌ Completion report does not exist: {report_path}")
        return 1

    result = apply_prompt_completion_report(
        report_path,
        expected_module=args.module_id,
        write=args.write,
        module_root=Path(args.module_root),
    )

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))

    if not result["ok"]:
        return 1

    if args.write:
        print("✅ Completion report write apply passed")
    else:
        print("✅ Completion report dry-run apply passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
