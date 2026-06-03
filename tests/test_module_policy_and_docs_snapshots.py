from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_module_policy_readme_exists() -> None:
    assert (ROOT / "coordination" / "module_policy" / "README.md").exists()


def test_calculator_module_policy_files_exist() -> None:
    required_files = [
        ROOT / "coordination" / "module_policy" / "calculator_engine" / "module_goals.md",
        ROOT / "coordination" / "module_policy" / "calculator_engine" / "role_boundaries.md",
        ROOT / "coordination" / "module_policy" / "calculator_engine" / "development_focus.md",
    ]

    for path in required_files:
        assert path.exists()


def test_module_docs_snapshots_readme_exists() -> None:
    assert (ROOT / "coordination" / "module_docs_snapshots" / "README.md").exists()


def test_calculator_docs_snapshot_readme_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "module_docs_snapshots"
        / "calculator_engine"
        / "README.md"
    ).exists()


def test_calculator_module_policy_mentions_output_package() -> None:
    content = (
        ROOT
        / "coordination"
        / "module_policy"
        / "calculator_engine"
        / "module_goals.md"
    ).read_text(encoding="utf-8")
    normalized_content = content.casefold()

    assert "calculationoutputpackage".casefold() in normalized_content
    assert "quote" in normalized_content
    assert "order" in normalized_content


def test_calculator_role_boundaries_prevent_foreign_ownership() -> None:
    content = (
        ROOT
        / "coordination"
        / "module_policy"
        / "calculator_engine"
        / "role_boundaries.md"
    ).read_text(encoding="utf-8")

    assert "canonical client registry" in content
    assert "canonical order registry" in content
    assert "Accounting Registry" in content
    assert "ForPrint Library" in content


def test_module_docs_snapshots_are_manual_for_now() -> None:
    content = (
        ROOT / "coordination" / "module_docs_snapshots" / "README.md"
    ).read_text(encoding="utf-8")

    assert "Manual / semi-manual" in content
    assert "avoid overbuilding automation too early" in content


def test_calculator_docs_snapshot_points_to_source_path() -> None:
    content = (
        ROOT
        / "coordination"
        / "module_docs_snapshots"
        / "calculator_engine"
        / "README.md"
    ).read_text(encoding="utf-8")

    assert "/srv/software_development/forprint-project/calculator_engine/app" in content
