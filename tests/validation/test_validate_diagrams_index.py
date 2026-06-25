from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "validation" / "validate_diagrams_index.py"


def _load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("validate_diagrams_index", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_valid_diagrams_tree(root: Path) -> None:
    diagrams = root / "diagrams"
    machine = root / "machine"
    scripts = root / "scripts"

    diagrams.mkdir(parents=True)
    machine.mkdir(parents=True)
    scripts.mkdir(parents=True)

    (diagrams / "README.md").write_text("# Diagrams\n", encoding="utf-8")
    (diagrams / "module_graph.mmd").write_text("graph TD\n    A --> B\n", encoding="utf-8")
    (diagrams / "ownership_map.mmd").write_text("graph TD\n    A --> C\n", encoding="utf-8")
    (machine / "data_flows.yaml").write_text("data_flows: []\n", encoding="utf-8")
    (machine / "ownership.yaml").write_text("ownership: {}\n", encoding="utf-8")
    (scripts / "generate_mermaid.py").write_text("# generator\n", encoding="utf-8")

    index = {
        "diagrams_index": {
            "version": "0.1",
            "status": "active",
            "source_module": "forprint_system_blueprint",
            "purpose": "Test diagrams index.",
            "default_format": "mermaid",
            "update_command": "make diagrams",
            "check_command": "make diagrams-check",
            "artifacts": [
                {
                    "diagram_id": "module_graph",
                    "file": "module_graph.mmd",
                    "title": "Module Graph",
                    "format": "mermaid",
                    "status": "generated",
                    "generator": "scripts/generate_mermaid.py",
                    "source_files": ["machine/data_flows.yaml"],
                    "purpose": "Shows module relationships.",
                },
                {
                    "diagram_id": "ownership_map",
                    "file": "ownership_map.mmd",
                    "title": "Ownership Map",
                    "format": "mermaid",
                    "status": "generated",
                    "generator": "scripts/generate_mermaid.py",
                    "source_files": ["machine/ownership.yaml"],
                    "purpose": "Shows ownership.",
                },
            ],
        }
    }

    (diagrams / "index.yaml").write_text(yaml.safe_dump(index, sort_keys=False), encoding="utf-8")


def test_valid_diagrams_index_passes(tmp_path: Path) -> None:
    validator = _load_validator()
    _write_valid_diagrams_tree(tmp_path)

    assert validator.validate_diagrams_index(tmp_path) == []


def test_missing_indexed_diagram_is_reported(tmp_path: Path) -> None:
    validator = _load_validator()
    _write_valid_diagrams_tree(tmp_path)

    (tmp_path / "diagrams" / "ownership_map.mmd").unlink()

    issues = validator.validate_diagrams_index(tmp_path)

    assert any("diagram file does not exist" in issue for issue in issues)


def test_unindexed_diagram_is_reported(tmp_path: Path) -> None:
    validator = _load_validator()
    _write_valid_diagrams_tree(tmp_path)

    (tmp_path / "diagrams" / "extra.mmd").write_text("graph TD\n    X --> Y\n", encoding="utf-8")

    issues = validator.validate_diagrams_index(tmp_path)

    assert any("diagram file is not indexed: extra.mmd" in issue for issue in issues)


def test_markdown_fence_in_mmd_is_reported(tmp_path: Path) -> None:
    validator = _load_validator()
    _write_valid_diagrams_tree(tmp_path)

    (tmp_path / "diagrams" / "module_graph.mmd").write_text(
        "```mermaid\ngraph TD\n    A --> B\n```\n",
        encoding="utf-8",
    )

    issues = validator.validate_diagrams_index(tmp_path)

    assert any("raw Mermaid without markdown fences" in issue for issue in issues)


def test_generated_diagram_requires_source_files(tmp_path: Path) -> None:
    validator = _load_validator()
    _write_valid_diagrams_tree(tmp_path)

    index_path = tmp_path / "diagrams" / "index.yaml"
    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    data["diagrams_index"]["artifacts"][0].pop("source_files")
    index_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    issues = validator.validate_diagrams_index(tmp_path)

    assert any("source_files" in issue for issue in issues)
