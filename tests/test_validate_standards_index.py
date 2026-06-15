from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_standards_index.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_standards_index", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_standard(root: Path, name: str, text: str = "# Example standard\n") -> None:
    standards_dir = root / "coordination" / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)
    (standards_dir / name).write_text(text, encoding="utf-8")


def write_index(root: Path, *, file_name: str = "example_standard.md") -> None:
    standards_dir = root / "coordination" / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "standards_index_version": "v0_1",
        "status": "active",
        "default_semantics": "advisory_guidance_gradual_alignment",
        "policy": {
            "continuous_read_required": True,
            "advisory_by_default": True,
            "not_active_prompt": True,
            "gradual_alignment_required": True,
            "hard_enforcement_requires_prompt_or_directive": True,
        },
        "standards": [
            {
                "standard_id": "example_standard",
                "file": file_name,
                "title": "Example standard",
                "status": "target_standard",
                "adoption_mode": "gradual_alignment",
            }
        ],
    }

    (standards_dir / "index.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def test_valid_standards_index_passes(tmp_path: Path) -> None:
    validator = load_validator()
    write_standard(tmp_path, "example_standard.md")
    write_index(tmp_path)

    assert validator.validate_standards_index(tmp_path) == []


def test_missing_index_fails(tmp_path: Path) -> None:
    validator = load_validator()

    issues = validator.validate_standards_index(tmp_path)

    assert any("file does not exist" in issue for issue in issues)


def test_missing_policy_flag_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_standard(tmp_path, "example_standard.md")
    write_index(tmp_path)

    index_path = tmp_path / "coordination" / "standards" / "index.yaml"
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    del data["policy"]["advisory_by_default"]
    index_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    issues = validator.validate_standards_index(tmp_path)

    assert any("policy.advisory_by_default" in issue for issue in issues)


def test_unindexed_standard_file_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_standard(tmp_path, "example_standard.md")
    write_standard(tmp_path, "extra_standard.md")
    write_index(tmp_path)

    issues = validator.validate_standards_index(tmp_path)

    assert any("standard file is not indexed: extra_standard.md" in issue for issue in issues)


def test_indexed_missing_file_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_index(tmp_path, file_name="missing_standard.md")

    issues = validator.validate_standards_index(tmp_path)

    assert any("indexed standard file does not exist" in issue for issue in issues)


def test_unsupported_status_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_standard(tmp_path, "example_standard.md")
    write_index(tmp_path)

    index_path = tmp_path / "coordination" / "standards" / "index.yaml"
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    data["standards"][0]["status"] = "mandatory_now"
    index_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    issues = validator.validate_standards_index(tmp_path)

    assert any("unsupported standard status" in issue for issue in issues)


def test_placeholder_token_fails(tmp_path: Path) -> None:
    validator = load_validator()
    write_standard(tmp_path, "example_standard.md")
    write_index(tmp_path)

    index_path = tmp_path / "coordination" / "standards" / "index.yaml"
    text = index_path.read_text(encoding="utf-8").replace("example_standard", "{standard_id}")
    index_path.write_text(text, encoding="utf-8")

    issues = validator.validate_standards_index(tmp_path)

    assert any("unresolved placeholder" in issue for issue in issues)
