import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FILES = [
    "coordination/instruction_intake/assistant_reading_order.md",
    "coordination/instruction_intake/instruction_sources.yaml",
    "coordination/instruction_intake/module_profile_model.md",
    "coordination/instruction_intake/default_profile_traits.yaml",
]

REQUIRED_SOURCE_IDS = [
    "instruction_intake",
    "global_policy",
    "active_directives",
    "module_policy",
    "outgoing_prompt",
    "standards",
    "current_status_and_reports",
    "local_implementation",
]

REQUIRED_SOURCE_ROOTS = [
    "instruction_intake",
    "global_policy",
    "active_directives",
    "module_policy",
    "outgoing_prompt",
    "standards",
    "coordination_template",
    "standards_template",
]

REQUIRED_PROFILE_DIMENSIONS = [
    "maturity",
    "business_criticality",
    "complexity",
    "automation_level",
    "standards_strictness",
    "prompt_priority",
    "cleanup_priority",
    "feedback_required",
]


def issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def load_yaml_mapping(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [issue(path, "file does not exist")]
    except yaml.YAMLError as exc:
        return None, [issue(path, f"invalid YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [issue(path, "YAML root must be a mapping")]

    return data, []


def validate_docs(root: Path) -> list[str]:
    issues: list[str] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.is_file():
            issues.append(issue(path, "required instruction intake file is missing"))

    reading_order = root / "coordination/instruction_intake/assistant_reading_order.md"
    if reading_order.is_file():
        text = reading_order.read_text(encoding="utf-8").lower()
        for expected in (
            "source of truth",
            "required reading order",
            "priority model",
            "conflict handling",
        ):
            if expected not in text:
                issues.append(issue(reading_order, f"missing phrase {expected!r}"))

    profile_model = root / "coordination/instruction_intake/module_profile_model.md"
    if profile_model.is_file():
        text = profile_model.read_text(encoding="utf-8").lower()
        for expected in ("composable traits", "core dimensions", "lightweight helper"):
            if expected not in text:
                issues.append(issue(profile_model, f"missing phrase {expected!r}"))

    return issues


def validate_instruction_sources(root: Path) -> list[str]:
    path = root / "coordination/instruction_intake/instruction_sources.yaml"
    data, issues = load_yaml_mapping(path)
    if data is None:
        return issues

    if data.get("instruction_intake_version") != "v0_1":
        issues.append(issue(path, "instruction_intake_version must be v0_1"))
    if data.get("status") != "active":
        issues.append(issue(path, "status must be active"))

    freshness_policy = data.get("freshness_policy")
    if not isinstance(freshness_policy, dict):
        issues.append(issue(path, "freshness_policy must be a mapping"))
    else:
        for key in (
            "read_blueprint_source_on_each_prompt",
            "local_snapshots_are_audit_only",
            "do_not_use_stale_local_snapshots_as_truth",
        ):
            if freshness_policy.get(key) is not True:
                issues.append(issue(path, f"freshness_policy.{key} must be true"))

    priority_order = data.get("priority_order")
    if not isinstance(priority_order, list):
        issues.append(issue(path, "priority_order must be a list"))
    else:
        seen_source_ids = []
        for index, record in enumerate(priority_order):
            if not isinstance(record, dict):
                issues.append(issue(path, f"priority_order[{index}] must be a mapping"))
                continue
            source_id = record.get("source_id")
            priority = record.get("priority")
            if isinstance(source_id, str) and source_id.strip():
                seen_source_ids.append(source_id)
            else:
                issues.append(issue(path, f"priority_order[{index}].source_id is invalid"))
            if not isinstance(priority, int):
                issues.append(issue(path, f"priority_order[{index}].priority must be an integer"))

        for source_id in REQUIRED_SOURCE_IDS:
            if source_id not in seen_source_ids:
                issues.append(issue(path, f"missing priority source_id {source_id!r}"))

    source_roots = data.get("source_roots")
    if not isinstance(source_roots, list):
        issues.append(issue(path, "source_roots must be a list"))
    else:
        roots_by_id = {}
        for index, record in enumerate(source_roots):
            if not isinstance(record, dict):
                issues.append(issue(path, f"source_roots[{index}] must be a mapping"))
                continue
            source_id = record.get("source_id")
            relative_path = record.get("path")
            if not isinstance(source_id, str) or not source_id.strip():
                issues.append(issue(path, f"source_roots[{index}].source_id is invalid"))
                continue
            roots_by_id[source_id] = record
            if not isinstance(relative_path, str) or not relative_path.strip():
                issues.append(issue(path, f"source_roots[{index}].path is invalid"))
                continue
            if record.get("required") is True and record.get("path_kind") == "blueprint_relative":
                resolved = root / relative_path
                if not resolved.exists():
                    issues.append(issue(path, f"required source path does not exist: {relative_path}"))

        for source_id in REQUIRED_SOURCE_ROOTS:
            if source_id not in roots_by_id:
                issues.append(issue(path, f"missing source root {source_id!r}"))

    profile_dimensions = data.get("module_profile_dimensions")
    if not isinstance(profile_dimensions, list):
        issues.append(issue(path, "module_profile_dimensions must be a list"))
    else:
        for dimension in REQUIRED_PROFILE_DIMENSIONS:
            if dimension not in profile_dimensions:
                issues.append(issue(path, f"missing profile dimension {dimension!r}"))

    return issues


def validate_profile_traits(root: Path) -> list[str]:
    path = root / "coordination/instruction_intake/default_profile_traits.yaml"
    data, issues = load_yaml_mapping(path)
    if data is None:
        return issues

    if data.get("profile_traits_version") != "v0_1":
        issues.append(issue(path, "profile_traits_version must be v0_1"))
    if data.get("profiles_are_composable") is not True:
        issues.append(issue(path, "profiles_are_composable must be true"))

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, dict):
        issues.append(issue(path, "dimensions must be a mapping"))
        return issues

    for dimension in REQUIRED_PROFILE_DIMENSIONS:
        record = dimensions.get(dimension)
        if not isinstance(record, dict):
            issues.append(issue(path, f"missing dimension {dimension!r}"))
            continue
        allowed = record.get("allowed")
        if not isinstance(allowed, list) or not allowed:
            issues.append(issue(path, f"dimension {dimension!r} must define allowed values"))

    return issues


def validate_instruction_intake(root: Path) -> list[str]:
    issues: list[str] = []
    issues.extend(validate_docs(root))
    issues.extend(validate_instruction_sources(root))
    issues.extend(validate_profile_traits(root))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForPrint assistant instruction intake protocol.")
    parser.add_argument("--root", default=".", help="Blueprint repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues = validate_instruction_intake(root)
    if issues:
        print("❌ Instruction intake validation failed:")
        for item in issues:
            print(f"  - {item}")
        return 1

    print("✅ Instruction intake validation passed")
    return 0


if Path(sys.argv[0]).name == "validate_instruction_intake.py":
    sys.exit(main())
