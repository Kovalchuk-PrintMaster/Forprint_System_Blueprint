from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_outgoing_prompts.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_outgoing_prompts", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_index(root: Path, module: str, data: dict) -> Path:
    module_dir = root / "coordination" / "outgoing_prompts" / module
    drafts_dir = module_dir / "drafts"
    drafts_dir.mkdir(parents=True)
    (drafts_dir / "prompt.md").write_text(
        "# Prompt: Example\n\n## Target module\n\n`example_module`\n\n## Purpose\n\nExample.\n",
        encoding="utf-8",
    )
    index_path = module_dir / "index.yaml"
    index_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return index_path


def test_valid_outgoing_prompt_index_passes(tmp_path: Path) -> None:
    validator = load_validator()
    write_index(
        tmp_path,
        "example_module",
        {
            "module": "example_module",
            "active_prompts": [
                {
                    "prompt_id": "example_prompt_v0_1",
                    "status": "ready_for_module_pull",
                    "file": "drafts/prompt.md",
                    "target_module": "example_module",
                }
            ],
            "completed_prompts": [],
            "review_notes": [],
        },
    )

    assert validator.validate_root(tmp_path) == []


def test_missing_active_prompt_file_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_index(
        tmp_path,
        "example_module",
        {
            "module": "example_module",
            "active_prompts": [
                {
                    "prompt_id": "example_prompt_v0_1",
                    "status": "ready_for_module_pull",
                    "file": "drafts/missing.md",
                    "target_module": "example_module",
                }
            ],
        },
    )

    issues = validator.validate_root(tmp_path)

    assert any("file does not exist" in issue.message for issue in issues)


def test_placeholder_token_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_index(
        tmp_path,
        "example_module",
        {
            "module": "example_module",
            "active_prompts": [
                {
                    "prompt_id": "{now}",
                    "status": "ready_for_module_pull",
                    "file": "drafts/prompt.md",
                    "target_module": "example_module",
                }
            ],
        },
    )

    issues = validator.validate_root(tmp_path)

    assert any("unresolved placeholder" in issue.message for issue in issues)


def test_forbidden_module_id_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_index(
        tmp_path,
        "example_module",
        {
            "module": "example_module",
            "active_prompts": [
                {
                    "prompt_id": "example_prompt_v0_1",
                    "status": "ready_for_module_pull",
                    "file": "drafts/prompt.md",
                    "target_module": "example_module",
                }
            ],
        },
    )
    prompt_path = tmp_path / "coordination" / "outgoing_prompts" / "example_module" / "drafts" / "prompt.md"
    prompt_path.write_text("forprint_calculator_engine", encoding="utf-8")

    issues = validator.validate_root(tmp_path)

    assert any("forbidden token" in issue.message for issue in issues)


def test_module_directory_mismatch_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_index(
        tmp_path,
        "example_module",
        {
            "module": "wrong_module",
            "active_prompts": [],
        },
    )

    issues = validator.validate_root(tmp_path)

    assert any("does not match directory" in issue.message for issue in issues)
