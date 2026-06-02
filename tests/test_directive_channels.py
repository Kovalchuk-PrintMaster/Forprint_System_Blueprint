
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_directives_readme_exists() -> None:
    assert (ROOT / "coordination" / "directives" / "README.md").exists()


def test_global_directives_index_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "directives"
        / "global"
        / "index.yaml"
    ).exists()


def test_global_module_coordination_directive_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "directives"
        / "global"
        / "active"
        / "2026-06-02__global__directive__module-coordination-standard-v1.md"
    ).exists()


def test_calculator_directives_index_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "directives"
        / "modules"
        / "calculator_engine"
        / "index.yaml"
    ).exists()


def test_calculator_active_directive_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "directives"
        / "modules"
        / "calculator_engine"
        / "active"
        / "2026-06-02__calculator_engine__directive__coordination-pull-and-calculator-focus-v1.md"
    ).exists()


def test_global_directive_index_references_existing_file() -> None:
    data = _load_yaml(
        ROOT
        / "coordination"
        / "directives"
        / "global"
        / "index.yaml"
    )

    directive = data["global_directives"]["active"][0]
    file_path = ROOT / directive["file"]

    assert directive["status"] == "active"
    assert directive["priority"] == "p0"
    assert file_path.exists()


def test_calculator_directive_index_references_existing_file() -> None:
    data = _load_yaml(
        ROOT
        / "coordination"
        / "directives"
        / "modules"
        / "calculator_engine"
        / "index.yaml"
    )

    directive = data["module_directives"]["active"][0]
    file_path = ROOT / directive["file"]

    assert directive["status"] == "active"
    assert directive["priority"] == "p0"
    assert directive["requires_acknowledgement"] is True
    assert file_path.exists()


def test_calculator_directive_mentions_expected_strategic_direction() -> None:
    content = (
        ROOT
        / "coordination"
        / "directives"
        / "modules"
        / "calculator_engine"
        / "active"
        / "2026-06-02__calculator_engine__directive__coordination-pull-and-calculator-focus-v1.md"
    ).read_text(encoding="utf-8")

    assert "CalculationOutputPackage" in content
    assert "Quote / CommercialOffer" in content
    assert "OrderDraft / OrderCreationDraft" in content
    assert "ForPrint Library" in content
