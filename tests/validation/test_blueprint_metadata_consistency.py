from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/validation/validate_blueprint_metadata_consistency.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_blueprint_metadata_consistency",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def make_governance_record(root: Path) -> None:
    write_yaml(
        root
        / "coordination/internal_work/blueprint/governance/"
        "record.yaml",
        {
            "schema_version": "test_governance_v0_1",
            "metadata": {
                "module_id": "forprint_system_blueprint",
                "owner": "forprint_system_blueprint",
            },
        },
    )


def make_queue(
    root: Path,
    module: str = "example_module",
    prompt_id: str = "example_prompt_v0_1",
) -> Path:
    module_dir = (
        root / "coordination/outgoing_prompts" / module
    )
    prompt_path = module_dir / "drafts/prompt.md"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text("# Prompt\n", encoding="utf-8")

    index = module_dir / "index.yaml"
    write_yaml(
        index,
        {
            "schema_version": "prompt_queue_v0_2",
            "module": module,
            "prompt_queue": [
                {
                    "prompt_id": prompt_id,
                    "file": "drafts/prompt.md",
                    "target_module": module,
                }
            ],
        },
    )
    return index


def test_current_blueprint_metadata_is_consistent() -> None:
    validator = load_validator()
    root = Path(__file__).resolve().parents[2]

    result = validator.validate_root(root)

    assert result.ok, [
        f"{issue.path}: {issue.code}: {issue.message}"
        for issue in result.issues
    ]
    assert result.governance_files > 0
    assert result.prompt_indexes > 0
    assert result.prompt_records > 0


def test_governance_schema_version_is_required(
    tmp_path: Path,
) -> None:
    validator = load_validator()
    make_queue(tmp_path)
    write_yaml(
        tmp_path
        / "coordination/internal_work/blueprint/governance/"
        "record.yaml",
        {
            "metadata": {
                "module_id": "forprint_system_blueprint",
            }
        },
    )

    result = validator.validate_root(tmp_path)

    assert any(
        issue.code == "schema_version_missing"
        for issue in result.issues
    )


def test_legacy_governance_record_without_module_id_is_allowed(
    tmp_path: Path,
) -> None:
    validator = load_validator()
    make_queue(tmp_path)
    write_yaml(
        tmp_path
        / "coordination/internal_work/blueprint/governance/"
        "record.yaml",
        {
            "schema_version": "legacy_governance_v0_1",
            "metadata": {
                "owner": "forprint_system_blueprint",
            },
        },
    )

    result = validator.validate_root(tmp_path)

    assert not any(
        issue.code == "module_id_mismatch"
        for issue in result.issues
    )


def test_governance_module_id_must_be_blueprint(
    tmp_path: Path,
) -> None:
    validator = load_validator()
    make_queue(tmp_path)
    write_yaml(
        tmp_path
        / "coordination/internal_work/blueprint/governance/"
        "record.yaml",
        {
            "schema_version": "test_governance_v0_1",
            "metadata": {
                "module_id": "wrong_module",
            },
        },
    )

    result = validator.validate_root(tmp_path)

    assert any(
        issue.code == "module_id_mismatch"
        for issue in result.issues
    )


def test_duplicate_prompt_id_across_indexes_fails(
    tmp_path: Path,
) -> None:
    validator = load_validator()
    make_governance_record(tmp_path)
    make_queue(
        tmp_path,
        module="module_a",
        prompt_id="duplicate_prompt",
    )
    make_queue(
        tmp_path,
        module="module_b",
        prompt_id="duplicate_prompt",
    )

    result = validator.validate_root(tmp_path)

    assert any(
        issue.code == "duplicate_prompt_id"
        for issue in result.issues
    )


def test_prompt_file_may_not_escape_module_directory(
    tmp_path: Path,
) -> None:
    validator = load_validator()
    make_governance_record(tmp_path)
    index = make_queue(tmp_path)

    data = yaml.safe_load(index.read_text(encoding="utf-8"))
    data["prompt_queue"][0]["file"] = "../outside.md"
    write_yaml(index, data)

    result = validator.validate_root(tmp_path)

    assert any(
        issue.code == "file_reference_escapes_module"
        for issue in result.issues
    )


def test_target_module_must_match_directory(
    tmp_path: Path,
) -> None:
    validator = load_validator()
    make_governance_record(tmp_path)
    index = make_queue(tmp_path)

    data = yaml.safe_load(index.read_text(encoding="utf-8"))
    data["prompt_queue"][0]["target_module"] = "wrong_module"
    write_yaml(index, data)

    result = validator.validate_root(tmp_path)

    assert any(
        issue.code == "target_module_mismatch"
        for issue in result.issues
    )
