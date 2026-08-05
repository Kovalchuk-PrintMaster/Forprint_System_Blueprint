#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Any

import yaml

CONTRACT_YAML = Path(
    "coordination/standards/governance/"
    "mutation_builder_contract_v0_1.yaml"
)
CONTRACT_MD = Path(
    "coordination/standards/governance/"
    "mutation_builder_contract_v0_1.md"
)
GOVERNANCE_INDEX = Path(
    "coordination/standards/governance/index.yaml"
)
GOVERNANCE_README = Path(
    "coordination/standards/governance/README.md"
)
STANDARDS_INDEX = Path("coordination/standards/index.yaml")
CHECK_CATALOG = Path("scripts/run_blueprint_checks.py")

SCHEMA = "mutation_builder_contract_v0_1"
FLOW = [
    "inspect_exact_structure",
    "render_all_changes_in_memory",
    "validate_typed_exact_path_set",
    "reject_no_op_mutations",
    "parse_and_compile_generated_artifacts",
    "preserve_existing_file_modes",
    "perform_bounded_atomic_writes",
    "run_focused_tests",
    "run_canonical_gate",
    "verify_complete_rollback_on_failure",
]

GOVERNANCE_RECORDS = {
    CONTRACT_MD.name: {
        "title": "ForPrint Mutation Builder Contract",
        "status": "active_standard",
        "adoption_mode": "prompt_or_directive_required",
        "order": 90,
    },
    CONTRACT_YAML.name: {
        "title": "ForPrint Mutation Builder Machine Contract",
        "status": "active_standard",
        "adoption_mode": "prompt_or_directive_required",
        "order": 100,
    },
}

STANDARD_RECORDS = {
    "mutation_builder_contract": {
        "file": CONTRACT_MD.relative_to(
            Path("coordination/standards")
        ).as_posix(),
        "title": "ForPrint Mutation Builder Contract",
        "status": "active_standard",
        "adoption_mode": "prompt_or_directive_required",
    },
    "mutation_builder_contract_machine_contract": {
        "file": CONTRACT_YAML.relative_to(
            Path("coordination/standards")
        ).as_posix(),
        "title": "ForPrint Mutation Builder Machine Contract",
        "status": "active_standard",
        "adoption_mode": "prompt_or_directive_required",
    },
}

REQUIRED_HEADINGS = (
    "# ForPrint Mutation Builder Contract",
    "## Mandatory ten-stage flow",
    "## Source and path contracts",
    "## Preflight validation",
    "## Atomic write contract",
    "## Verification order",
    "## Failure and rollback behavior",
    "## Review checklist",
    "## Safety boundaries",
)

REQUIRED_TRUE_PATHS = (
    ("scope", "clean_working_tree_required"),
    ("contracts", "source_guards", "expected_branch_required"),
    ("contracts", "source_guards", "expected_head_required"),
    ("contracts", "source_guards", "source_sha256_guards_required"),
    ("contracts", "source_guards", "clean_working_tree_required"),
    (
        "contracts",
        "rendered_path_contract",
        "exact_path_set_required",
    ),
    (
        "contracts",
        "rendered_path_contract",
        "missing_and_unexpected_paths_reported",
    ),
    (
        "contracts",
        "rendered_path_contract",
        "no_op_mutations_rejected",
    ),
    (
        "contracts",
        "preflight_validation",
        "all_outputs_rendered_before_first_tracked_write",
    ),
    (
        "contracts",
        "preflight_validation",
        "python_ast_parse_required",
    ),
    (
        "contracts",
        "preflight_validation",
        "python_compile_required",
    ),
    (
        "contracts",
        "preflight_validation",
        "yaml_unique_key_validation_required",
    ),
    (
        "contracts",
        "preflight_validation",
        "markdown_fence_balance_required",
    ),
    (
        "contracts",
        "preflight_validation",
        "lint_preflight_in_ignored_repository_tmp_required",
    ),
    ("contracts", "write_contract", "atomic_replace_required"),
    ("contracts", "write_contract", "bounded_to_declared_paths"),
    (
        "contracts",
        "write_contract",
        "preserve_existing_file_modes",
    ),
    (
        "contracts",
        "verification_contract",
        "focused_tests_before_canonical_gate",
    ),
    (
        "contracts",
        "verification_contract",
        "canonical_gate_required",
    ),
    (
        "contracts",
        "verification_contract",
        "exact_dirty_path_set_required",
    ),
    (
        "contracts",
        "verification_contract",
        "immutable_boundary_hashes_required",
    ),
    (
        "contracts",
        "rollback_contract",
        "rollback_on_any_failure",
    ),
    (
        "contracts",
        "rollback_contract",
        "restore_existing_bytes",
    ),
    (
        "contracts",
        "rollback_contract",
        "restore_existing_file_modes",
    ),
    ("contracts", "rollback_contract", "remove_new_files"),
    (
        "contracts",
        "rollback_contract",
        "bounded_git_restore_fallback",
    ),
    (
        "contracts",
        "rollback_contract",
        "verify_clean_working_tree_after_rollback",
    ),
)


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key `{key}`",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(
            value_node,
            deep=deep,
        )
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def load_yaml(
    path: Path,
) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [issue(path, "file does not exist")]

    try:
        data = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        return None, [issue(path, f"invalid YAML: {error}")]

    if not isinstance(data, dict):
        return None, [issue(path, "YAML root must be a mapping")]
    return data, []


def get_path(
    data: dict[str, Any],
    path: tuple[str, ...],
) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def validate_contract_data(
    path: Path,
    data: dict[str, Any],
    issues: list[str],
) -> None:
    if data.get("schema_version") != SCHEMA:
        issues.append(
            issue(
                path,
                f"`schema_version` must be {SCHEMA!r}",
            )
        )

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        issues.append(issue(path, "`metadata` must be a mapping"))
    else:
        expected = {
            "standard_id": "mutation_builder_contract",
            "status": "active_standard",
            "authority": "blueprint_repository_mutation_control",
            "adoption_mode": "prompt_or_directive_required",
        }
        for key, value in expected.items():
            if metadata.get(key) != value:
                issues.append(
                    issue(
                        path,
                        f"`metadata.{key}` must be {value!r}",
                    )
                )

    flow = data.get("required_flow")
    if not isinstance(flow, list):
        issues.append(issue(path, "`required_flow` must be a list"))
    else:
        actual_ids: list[Any] = []
        for index, row in enumerate(flow, start=1):
            if not isinstance(row, dict):
                issues.append(
                    issue(
                        path,
                        f"`required_flow[{index - 1}]` must be a mapping",
                    )
                )
                continue
            if row.get("order") != index:
                issues.append(
                    issue(
                        path,
                        f"`required_flow[{index - 1}].order` "
                        f"must be {index}",
                    )
                )
            actual_ids.append(row.get("step_id"))

            expected_write = index >= 7
            if row.get("tracked_write_allowed") is not expected_write:
                issues.append(
                    issue(
                        path,
                        f"`required_flow[{index - 1}]."
                        "tracked_write_allowed` is invalid",
                    )
                )

        if actual_ids != FLOW:
            issues.append(
                issue(
                    path,
                    "`required_flow` step order does not match "
                    "the canonical ten-stage flow",
                )
            )

    for value_path in REQUIRED_TRUE_PATHS:
        if get_path(data, value_path) is not True:
            issues.append(
                issue(
                    path,
                    f"`{'.'.join(value_path)}` must be true",
                )
            )

    expected_values = {
        (
            "contracts",
            "rendered_path_contract",
            "expected_rendered_paths_type",
        ): "pathlib.Path",
        (
            "contracts",
            "rendered_path_contract",
            "expected_git_status_paths_type",
        ): "str",
        (
            "contracts",
            "write_contract",
            "new_file_mode",
        ): "0644",
        (
            "contracts",
            "write_contract",
            "automatic_format_fix_after_write_allowed",
        ): False,
        (
            "contracts",
            "rollback_contract",
            "automatic_retry_after_partial_failure",
        ): False,
        ("operator_boundaries", "automatic_commit"): False,
        ("operator_boundaries", "automatic_push"): False,
        ("operator_boundaries", "automatic_merge"): False,
        (
            "operator_boundaries",
            "pilot_authorization_changed",
        ): False,
        ("operator_boundaries", "release_policy_changed"): False,
        (
            "operator_boundaries",
            "external_rollout_authorized",
        ): False,
        ("operator_boundaries", "cross_repository_writes"): False,
        ("result", "contract_state"): "active",
        ("result", "canonical_validation_required"): True,
        ("result", "pilot_effect"): "none",
        ("result", "external_rollout"): "gated",
    }
    for value_path, expected in expected_values.items():
        actual = get_path(data, value_path)
        if actual != expected:
            issues.append(
                issue(
                    path,
                    f"`{'.'.join(value_path)}` must be "
                    f"{expected!r}; found {actual!r}",
                )
            )


def validate_markdown(
    path: Path,
    issues: list[str],
) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.append(issue(path, "file does not exist"))
        return

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            issues.append(
                issue(path, f"required heading is missing: {heading}")
            )

    for step_id in FLOW:
        if f"`{step_id}`" not in text:
            issues.append(
                issue(
                    path,
                    f"required flow step is undocumented: {step_id}",
                )
            )

    if text.count("```") % 2:
        issues.append(issue(path, "Markdown fences are unbalanced"))


def validate_governance_index(
    path: Path,
    issues: list[str],
) -> None:
    data, local = load_yaml(path)
    issues.extend(local)
    if data is None:
        return

    group = data.get("standards_group")
    if not isinstance(group, dict):
        issues.append(
            issue(path, "`standards_group` must be a mapping")
        )
        return

    documents = group.get("documents")
    if not isinstance(documents, list):
        issues.append(
            issue(path, "`standards_group.documents` must be a list")
        )
        return

    by_file: dict[str, list[dict[str, Any]]] = {}
    for row in documents:
        if isinstance(row, dict) and isinstance(row.get("file"), str):
            by_file.setdefault(row["file"], []).append(row)

    for file_name, expected in GOVERNANCE_RECORDS.items():
        rows = by_file.get(file_name, [])
        if len(rows) != 1:
            issues.append(
                issue(
                    path,
                    f"expected exactly one governance index record "
                    f"for {file_name!r}",
                )
            )
            continue
        for key, value in expected.items():
            if rows[0].get(key) != value:
                issues.append(
                    issue(
                        path,
                        f"`{file_name}.{key}` must be {value!r}",
                    )
                )


def validate_standards_index(
    path: Path,
    issues: list[str],
) -> None:
    data, local = load_yaml(path)
    issues.extend(local)
    if data is None:
        return

    standards = data.get("standards")
    if not isinstance(standards, list):
        issues.append(issue(path, "`standards` must be a list"))
        return

    by_id: dict[str, list[dict[str, Any]]] = {}
    for row in standards:
        if (
            isinstance(row, dict)
            and isinstance(row.get("standard_id"), str)
        ):
            by_id.setdefault(row["standard_id"], []).append(row)

    for standard_id, expected in STANDARD_RECORDS.items():
        rows = by_id.get(standard_id, [])
        if len(rows) != 1:
            issues.append(
                issue(
                    path,
                    f"expected exactly one standards index record "
                    f"for {standard_id!r}",
                )
            )
            continue
        for key, value in expected.items():
            if rows[0].get(key) != value:
                issues.append(
                    issue(
                        path,
                        f"`{standard_id}.{key}` must be {value!r}",
                    )
                )


def validate_readme(
    path: Path,
    issues: list[str],
) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.append(issue(path, "file does not exist"))
        return

    required = (
        "<!-- mutation-builder-contract-v0-1:start -->",
        "## Mutation builder governance",
        "mutation_builder_contract_v0_1.md",
        "mutation_builder_contract_v0_1.yaml",
        "<!-- mutation-builder-contract-v0-1:end -->",
    )
    for token in required:
        if token not in text:
            issues.append(
                issue(
                    path,
                    f"mutation-builder README token is missing: "
                    f"{token}",
                )
            )


def _constant(node: ast.AST | None) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    return None


def validate_check_catalog(
    path: Path,
    issues: list[str],
) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        issues.append(issue(path, "file does not exist"))
        return
    except SyntaxError as error:
        issues.append(issue(path, f"invalid Python: {error}"))
        return

    matches: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "CheckDefinition":
            continue

        keywords = {item.arg: item.value for item in node.keywords}
        if _constant(keywords.get("check_id")) == (
            "mutation_builder_contract_validation"
        ):
            matches.append(node)

    if len(matches) != 1:
        issues.append(
            issue(
                path,
                "expected exactly one "
                "`mutation_builder_contract_validation` check",
            )
        )
        return

    keywords = {
        item.arg: item.value
        for item in matches[0].keywords
    }
    expected_constants = {
        "title": "Mutation builder contract",
        "expected_result": (
            "Mutation builders follow predictable preflight "
            "and rollback rules"
        ),
        "group": "documentation",
    }
    for key, value in expected_constants.items():
        if _constant(keywords.get(key)) != value:
            issues.append(
                issue(
                    path,
                    f"mutation-builder check `{key}` must be {value!r}",
                )
            )

    command = keywords.get("command")
    command_strings = {
        node.value
        for node in ast.walk(command)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    } if command is not None else set()

    expected_script = (
        "scripts/validation/"
        "validate_mutation_builder_contract.py"
    )
    if expected_script not in command_strings:
        issues.append(
            issue(
                path,
                "mutation-builder check command must include "
                f"{expected_script!r}",
            )
        )


def validate(root: Path) -> list[str]:
    issues: list[str] = []

    contract_path = root / CONTRACT_YAML
    data, local = load_yaml(contract_path)
    issues.extend(local)
    if data is not None:
        validate_contract_data(contract_path, data, issues)

    validate_markdown(root / CONTRACT_MD, issues)
    validate_governance_index(root / GOVERNANCE_INDEX, issues)
    validate_standards_index(root / STANDARDS_INDEX, issues)
    validate_readme(root / GOVERNANCE_README, issues)
    validate_check_catalog(root / CHECK_CATALOG, issues)

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the ForPrint mutation-builder contract."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Blueprint repository root.",
    )
    args = parser.parse_args()

    issues = validate(Path(args.root).resolve())
    if issues:
        print("❌ Mutation-builder contract validation failed:")
        for item in issues:
            print(f"  - {item}")
        return 1

    print("✅ Mutation-builder contract validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
