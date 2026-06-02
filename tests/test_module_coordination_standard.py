from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_module_coordination_standard_doc_exists() -> None:
    assert (ROOT / "human" / "module_coordination_standard.md").exists()


def test_module_coordination_prompt_template_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "templates"
        / "module_coordination_prompt.md"
    ).exists()


def test_module_coordination_standard_mentions_required_status_files() -> None:
    content = (
        ROOT
        / "human"
        / "module_coordination_standard.md"
    ).read_text(encoding="utf-8")

    assert "coordination/status/current_status.yaml" in content
    assert "coordination/status/current_status.md" in content
    assert "coordination/status/next_questions_for_blueprint.md" in content


def test_module_coordination_standard_mentions_prompt_archive() -> None:
    content = (
        ROOT
        / "human"
        / "module_coordination_standard.md"
    ).read_text(encoding="utf-8")

    assert "coordination/prompts/received/" in content
    assert "coordination/prompts/index.yaml" in content
    assert "prompt_id" in content
    assert "expected_report_id" in content


def test_module_coordination_standard_mentions_reports_archive() -> None:
    content = (
        ROOT
        / "human"
        / "module_coordination_standard.md"
    ).read_text(encoding="utf-8")

    assert "coordination/reports/completion/" in content
    assert "coordination/reports/commits/" in content
    assert "coordination/reports/index.yaml" in content
    assert "responds_to_prompt_id" in content


def test_module_coordination_prompt_mentions_required_indexes() -> None:
    content = (
        ROOT
        / "coordination"
        / "templates"
        / "module_coordination_prompt.md"
    ).read_text(encoding="utf-8")

    assert "coordination/prompts/index.yaml" in content
    assert "coordination/reports/index.yaml" in content


def test_module_coordination_standard_defers_control_plane() -> None:
    content = (
        ROOT
        / "human"
        / "module_coordination_standard.md"
    ).read_text(encoding="utf-8")

    assert "ForPrint Control Plane is planned but deferred" in content
