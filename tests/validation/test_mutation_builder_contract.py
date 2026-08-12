from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ("scripts/validation/validate_mutation_builder_contract.py")
CONTRACT_YAML = Path("coordination/standards/governance/mutation_builder_contract_v0_1.yaml")
CONTRACT_MD = Path("coordination/standards/governance/mutation_builder_contract_v0_1.md")
GOVERNANCE_INDEX = Path("coordination/standards/governance/index.yaml")
GOVERNANCE_README = Path("coordination/standards/governance/README.md")
STANDARDS_INDEX = Path("coordination/standards/index.yaml")
CHECK_CATALOG = Path("scripts/run_blueprint_checks.py")
PRECOMMIT_HELPER = Path("scripts/validation/validate_mutation_precommit_surface.py")

FIXTURE_FILES = (
    CONTRACT_YAML,
    CONTRACT_MD,
    GOVERNANCE_INDEX,
    GOVERNANCE_README,
    STANDARDS_INDEX,
    CHECK_CATALOG,
    PRECOMMIT_HELPER,
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "mutation_builder_contract_validator",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def fixture(tmp_path: Path) -> Path:
    root = tmp_path / "blueprint"
    for relative in FIXTURE_FILES:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    return root


def replace_once(
    root: Path,
    relative: Path,
    old: str,
    new: str,
) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1
    path.write_text(
        text.replace(old, new, 1),
        encoding="utf-8",
    )


def test_current_contract_passes(tmp_path: Path) -> None:
    assert validator.validate(fixture(tmp_path)) == []


def test_duplicate_yaml_key_fails(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "schema_version: mutation_builder_contract_v0_1\n",
        (
            "schema_version: mutation_builder_contract_v0_1\n"
            "schema_version: mutation_builder_contract_v0_1\n"
        ),
    )

    assert any("duplicate key `schema_version`" in item for item in validator.validate(root))


def test_required_flow_order_is_fixed(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "    step_id: inspect_exact_structure\n",
        "    step_id: render_all_changes_in_memory\n",
    )

    assert any("canonical ten-stage flow" in item for item in validator.validate(root))


def test_no_op_guard_is_required(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "    no_op_mutations_rejected: true\n",
        "    no_op_mutations_rejected: false\n",
    )

    assert any("no_op_mutations_rejected" in item for item in validator.validate(root))


def test_path_types_are_fixed(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "    expected_rendered_paths_type: pathlib.Path\n",
        "    expected_rendered_paths_type: str\n",
    )

    assert any("expected_rendered_paths_type" in item for item in validator.validate(root))


def test_ruff_preflight_is_isolated_and_required(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        ("    lint_preflight_in_ignored_repository_tmp_required: true\n"),
        ("    lint_preflight_in_ignored_repository_tmp_required: false\n"),
    )

    assert any(
        "lint_preflight_in_ignored_repository_tmp_required" in item
        for item in validator.validate(root)
    )


def test_post_write_format_fix_stays_forbidden(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        ("    automatic_format_fix_after_write_allowed: false\n"),
        ("    automatic_format_fix_after_write_allowed: true\n"),
    )

    assert any(
        "automatic_format_fix_after_write_allowed" in item for item in validator.validate(root)
    )


def test_rollback_cleanliness_is_required(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        ("    verify_clean_working_tree_after_rollback: true\n"),
        ("    verify_clean_working_tree_after_rollback: false\n"),
    )

    assert any(
        "verify_clean_working_tree_after_rollback" in item for item in validator.validate(root)
    )


def test_pilot_boundary_stays_false(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "  pilot_authorization_changed: false\n",
        "  pilot_authorization_changed: true\n",
    )

    assert any("pilot_authorization_changed" in item for item in validator.validate(root))


def test_human_contract_must_be_indexed(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    index_path = root / STANDARDS_INDEX
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    data["standards"] = [
        row for row in data["standards"] if row.get("standard_id") != "mutation_builder_contract"
    ]
    index_path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )

    assert any("mutation_builder_contract" in item for item in validator.validate(root))


def test_machine_contract_must_be_in_governance_index(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    path = root / GOVERNANCE_INDEX
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["standards_group"]["documents"] = [
        row for row in data["standards_group"]["documents"] if row.get("file") != CONTRACT_YAML.name
    ]
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )

    assert any(CONTRACT_YAML.name in item for item in validator.validate(root))


def test_readme_reference_is_required(tmp_path: Path) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        GOVERNANCE_README,
        "## Mutation builder governance\n",
        "## Builder governance\n",
    )

    assert any("README token is missing" in item for item in validator.validate(root))


def test_check_catalog_entry_is_required(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CHECK_CATALOG,
        'check_id="mutation_builder_contract_validation"',
        'check_id="mutation_builder_contract_validation_missing"',
    )

    assert any("expected exactly one" in item for item in validator.validate(root))


def test_temporary_index_precommit_is_required(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "    temporary_git_index_precommit_required: true\n",
        "    temporary_git_index_precommit_required: false\n",
    )

    assert any(
        "temporary_git_index_precommit_required" in item for item in validator.validate(root)
    )


def test_untracked_new_file_coverage_is_required(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        "    untracked_new_files_covered_required: true\n",
        "    untracked_new_files_covered_required: false\n",
    )

    assert any("untracked_new_files_covered_required" in item for item in validator.validate(root))


def test_canonical_precommit_helper_path_is_fixed(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        CONTRACT_YAML,
        (
            "    canonical_precommit_validator: "
            "scripts/validation/validate_mutation_precommit_surface.py\n"
        ),
        ("    canonical_precommit_validator: scripts/validation/other.py\n"),
    )

    assert any("canonical_precommit_validator" in item for item in validator.validate(root))


def test_precommit_helper_contract_is_validated(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        PRECOMMIT_HELPER,
        '        env["GIT_INDEX_FILE"] = str(temp_index)\n',
        '        env["TEMP_INDEX_FILE"] = str(temp_index)\n',
    )

    assert any('must assign `env["GIT_INDEX_FILE"]`' in item for item in validator.validate(root))


def test_precommit_helper_git_commands_are_semantically_validated(
    tmp_path: Path,
) -> None:
    root = fixture(tmp_path)
    replace_once(
        root,
        PRECOMMIT_HELPER,
        '        run_git(root, ["read-tree", "HEAD"], env=env)\n',
        '        run_git(root, ["read-tree", "HEAD_MISSING"], env=env)\n',
    )

    assert any(
        "precommit helper Git command is missing" in item for item in validator.validate(root)
    )


def test_canonical_check_catalog_contains_validator() -> None:
    checks = {item.check_id: item for item in build_checks()}
    check = checks["mutation_builder_contract_validation"]

    assert check.title == "Mutation builder contract"
    assert check.group == "documentation"
    assert check.expected_result == (
        "Mutation builders follow predictable preflight and rollback rules"
    )
    assert check.command[-1] == ("scripts/validation/validate_mutation_builder_contract.py")
