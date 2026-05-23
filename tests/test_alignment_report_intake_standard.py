from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_alignment_report_schema_has_required_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    data = _load_yaml(root / "machine/module_alignment_report_schema.yaml")

    required_sections = data["required_sections"]

    assert "metadata" in required_sections
    assert "detected_architecture_drift" in required_sections
    assert "contract_gaps" in required_sections
    assert "summary" in required_sections


def test_alignment_report_template_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    template_path = root / "coordination/templates/module_alignment_report_template.md"

    assert template_path.exists()

    content = template_path.read_text(encoding="utf-8")
    assert "# Module Alignment Report" in content
    assert "Detected architecture drift" in content
    assert "Open questions for ForPrint System Blueprint" in content