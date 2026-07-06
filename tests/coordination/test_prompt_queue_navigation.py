from __future__ import annotations

from pathlib import Path

from scripts.coordination.render_prompt_dashboard import (
    render_dashboard,
    resolve_next_prompt,
)
from scripts.coordination.resolve_next_prompt import resolve_next_prompt_summary
from scripts.coordination.validate_prompt_queue import validate_root


def _write_valid_prompt_queue(root: Path) -> Path:
    module_dir = root / "coordination" / "outgoing_prompts" / "forprint_library"
    approved_dir = module_dir / "approved"
    drafts_dir = module_dir / "drafts"

    approved_dir.mkdir(parents=True)
    drafts_dir.mkdir(parents=True)

    prompt_path = approved_dir / "2026-06-29__library__reference_contract_v0_2.md"
    prompt_path.write_text(
        "# Prompt: Library Reference Contract v0.2\n\n"
        "## Target module\n\n"
        "`forprint_library`\n\n"
        "## Purpose\n\n"
        "Validate prompt queue tests.\n",
        encoding="utf-8",
    )

    draft_path = (
        drafts_dir
        / "2026-07-03__library__configurable_product_workbench_v0_1.md"
    )
    draft_path.write_text(
        "# Prompt: Library Configurable Product Workbench v0.1\n\n"
        "## Target module\n\n"
        "`forprint_library`\n\n"
        "## Purpose\n\n"
        "Planning-only draft prompt.\n",
        encoding="utf-8",
    )

    index_path = module_dir / "index.yaml"
    index_path.write_text(
        """schema_version: prompt_queue_v0_2
module: forprint_library

prompt_queue:
  - prompt_id: library_previous_prompt_v0_1
    sequence: 1
    title: Previous Prompt v0.1
    file: approved/2026-06-29__library__reference_contract_v0_2.md
    target_module: forprint_library
    phase: previous_prompt_v0_1
    priority: normal

    module_execution:
      status: completed_by_module
      completion_commit: "935e51b"
      completion_report: coordination/reports/completion/example.md
      completed_at: null

    blueprint_review:
      status: accepted_by_blueprint
      acceptance_commit: "8eea4c6"
      accepted_at: null
      review_notes: null

  - prompt_id: library_reference_contract_foundation_v0_2
    sequence: 2
    title: Library Reference Contract Foundation v0.2
    file: approved/2026-06-29__library__reference_contract_v0_2.md
    target_module: forprint_library
    phase: reference_contract_foundation_v0_2
    priority: high

    module_execution:
      status: ready_for_module_pull
      completion_commit: null
      completion_report: null
      completed_at: null

    blueprint_review:
      status: not_started
      acceptance_commit: null
      accepted_at: null
      review_notes: null
""",
        encoding="utf-8",
    )

    return index_path


def test_validate_prompt_queue_accepts_valid_v0_2_index(tmp_path: Path) -> None:
    _write_valid_prompt_queue(tmp_path)

    result = validate_root(tmp_path)

    assert result.ok
    assert result.checked_indexes == 1
    assert result.prompt_queue_indexes == 1
    assert result.legacy_indexes == 0


def test_validate_prompt_queue_skips_legacy_indexes(tmp_path: Path) -> None:
    module_dir = tmp_path / "coordination" / "outgoing_prompts" / "legacy_module"
    module_dir.mkdir(parents=True)

    (module_dir / "index.yaml").write_text(
        """active_prompts:
  - prompt_id: old_prompt
    status: ready_for_module_pull
    file: approved/old.md
""",
        encoding="utf-8",
    )

    result = validate_root(tmp_path)

    assert result.ok
    assert result.checked_indexes == 1
    assert result.prompt_queue_indexes == 0
    assert result.legacy_indexes == 1


def test_validate_prompt_queue_rejects_missing_prompt_file(tmp_path: Path) -> None:
    module_dir = tmp_path / "coordination" / "outgoing_prompts" / "forprint_library"
    module_dir.mkdir(parents=True)

    (module_dir / "index.yaml").write_text(
        """schema_version: prompt_queue_v0_2
module: forprint_library

prompt_queue:
  - prompt_id: missing_file_prompt
    sequence: 1
    title: Missing File Prompt
    file: approved/missing.md
    target_module: forprint_library
    phase: missing_file_prompt
    priority: high

    module_execution:
      status: ready_for_module_pull
      completion_commit: null
      completion_report: null
      completed_at: null

    blueprint_review:
      status: not_started
      acceptance_commit: null
      accepted_at: null
      review_notes: null
""",
        encoding="utf-8",
    )

    result = validate_root(tmp_path)

    assert not result.ok
    assert any("file does not exist" in issue.message for issue in result.issues)


def test_render_prompt_dashboard_shows_next_prompt(tmp_path: Path) -> None:
    index_path = _write_valid_prompt_queue(tmp_path)

    dashboard = render_dashboard(index_path, use_color=False)

    assert "Prompt Queue Dashboard — forprint_library" in dashboard
    assert "library_reference_contract_foundation_v0_2" in dashboard
    assert "ready_for_module_pull" in dashboard
    assert "accepted_by_blueprint" in dashboard
    assert "Next prompt: 2 library_reference_contract_foundation_v0_2" in dashboard


def test_render_prompt_dashboard_shows_current_marker_and_drafts(
    tmp_path: Path,
) -> None:
    index_path = _write_valid_prompt_queue(tmp_path)

    dashboard = render_dashboard(index_path, use_color=False)

    assert "→" in dashboard
    assert "Draft / Planned Prompts" in dashboard
    assert "library__configurable_product_workbench_v0_1" in dashboard
    assert "Library Configurable Product Workbench v0.1" in dashboard
    assert "planning-only artifacts" in dashboard


def test_resolve_next_prompt_returns_first_ready_prompt(tmp_path: Path) -> None:
    index_path = _write_valid_prompt_queue(tmp_path)

    import yaml

    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    next_prompt = resolve_next_prompt(data)

    assert next_prompt is not None
    assert next_prompt["prompt_id"] == "library_reference_contract_foundation_v0_2"


def test_draft_prompt_does_not_become_next_prompt(tmp_path: Path) -> None:
    index_path = _write_valid_prompt_queue(tmp_path)

    import yaml

    data = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    next_prompt = resolve_next_prompt(data)

    assert next_prompt is not None
    assert next_prompt["prompt_id"] != "library__configurable_product_workbench_v0_1"
    assert next_prompt["prompt_id"] == "library_reference_contract_foundation_v0_2"


def test_resolve_next_prompt_summary_points_to_ready_prompt(tmp_path: Path) -> None:
    _write_valid_prompt_queue(tmp_path)

    summary = resolve_next_prompt_summary(tmp_path, "forprint_library")

    assert summary.sequence == 2
    assert summary.prompt_id == "library_reference_contract_foundation_v0_2"
    assert summary.priority == "high"
    assert summary.file == "approved/2026-06-29__library__reference_contract_v0_2.md"
    assert summary.path.exists()
