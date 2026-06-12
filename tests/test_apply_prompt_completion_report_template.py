from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "module_coordination_template"
    / "apply_prompt_completion_report.py"
)


def load_apply_module():
    spec = importlib.util.spec_from_file_location("apply_prompt_completion_report", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALID_FRONTMATTER = """
report_id: gateway_example_report
prompt_id: gateway_example_prompt
target_module: forprint_integration_gateway
phase: example_phase_v0_1
completed_step: example_step_ready
status: completed_in_module
implementation_commit: abc1234
checks:
  governance_check: ok
  make_check: ok
  make_check_report: ok
  coordination_records_check: ok
boundary_confirmation:
  production_api_added: false
  live_external_integrations_added: false
  database_ownership_added: false
  operational_data_ownership_added: false
  queue_or_cache_dependency_added: false
  one_c_writes_added: false
  automatic_posting_added: false
  final_price_calculation_added: false
next_questions_for_blueprint:
  - Accept completed prompt and issue next allowed prompt.
"""


def write_report(path: Path, frontmatter: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{frontmatter.strip()}\n---\n\nHuman report text.\n",
        encoding="utf-8",
    )
    return path


def read_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_dry_run_apply_returns_planned_updates(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER)

    result = apply_module.apply_prompt_completion_report(
        report,
        expected_module="forprint_integration_gateway",
    )

    assert result["ok"] is True
    assert result["mode"] == "dry_run"
    assert result["target_module"] == "forprint_integration_gateway"
    assert "coordination/status/current_status.yaml" in result["planned_files"]
    assert result["planned_updates"]["current_status"]["current_phase"] == "example_phase_v0_1"


def test_dry_run_apply_rejects_invalid_report(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = tmp_path / "completion.md"
    report.write_text("No frontmatter.", encoding="utf-8")

    result = apply_module.apply_prompt_completion_report(report)

    assert result["ok"] is False
    assert any("frontmatter" in issue for issue in result["issues"])


def test_dry_run_apply_rejects_wrong_module(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER)

    result = apply_module.apply_prompt_completion_report(report, expected_module="wrong_module")

    assert result["ok"] is False
    assert any("does not match expected module" in issue for issue in result["issues"])


def test_write_mode_updates_coordination_files(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = write_report(
        tmp_path / "coordination/reports/gateway_example_report_completion.md",
        VALID_FRONTMATTER,
    )

    result = apply_module.apply_prompt_completion_report(
        report,
        expected_module="forprint_integration_gateway",
        write=True,
        module_root=tmp_path,
    )

    assert result["ok"] is True
    assert result["mode"] == "write"

    current_status = read_yaml(tmp_path / "coordination/status/current_status.yaml")
    assert current_status["module_id"] == "forprint_integration_gateway"
    assert current_status["current_phase"] == "example_phase_v0_1"
    assert current_status["last_completed_step"] == "example_step_ready"

    prompts_index = read_yaml(tmp_path / "coordination/prompts/index.yaml")
    assert prompts_index["module_id"] == "forprint_integration_gateway"
    assert prompts_index["prompts"][0]["prompt_id"] == "gateway_example_prompt"

    reports_index = read_yaml(tmp_path / "coordination/reports/index.yaml")
    assert reports_index["module_id"] == "forprint_integration_gateway"
    assert reports_index["reports"][0]["report_id"] == "gateway_example_report"

    questions = (tmp_path / "coordination/status/next_questions_for_blueprint.md").read_text(
        encoding="utf-8"
    )
    assert "Accept completed prompt and issue next allowed prompt." in questions


def test_write_mode_upserts_existing_records(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = write_report(
        tmp_path / "coordination/reports/gateway_example_report_completion.md",
        VALID_FRONTMATTER,
    )

    apply_module.apply_prompt_completion_report(report, write=True, module_root=tmp_path)
    apply_module.apply_prompt_completion_report(report, write=True, module_root=tmp_path)

    prompts_index = read_yaml(tmp_path / "coordination/prompts/index.yaml")
    reports_index = read_yaml(tmp_path / "coordination/reports/index.yaml")

    assert len(prompts_index["prompts"]) == 1
    assert len(reports_index["reports"]) == 1


def test_boundary_positive_flags_are_normalized_to_negative_safe_flags(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER)

    result = apply_module.apply_prompt_completion_report(report)

    boundary = result["planned_updates"]["current_status"]["boundary_confirmation"]

    assert boundary["production_api_added"] is False
    assert boundary["no_production_api_added"] is True
    assert boundary["no_database_ownership_added"] is True


def test_next_questions_are_preserved(tmp_path: Path) -> None:
    apply_module = load_apply_module()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER)

    result = apply_module.apply_prompt_completion_report(report)

    questions = result["planned_updates"]["next_questions_for_blueprint"]

    assert questions == ["Accept completed prompt and issue next allowed prompt."]
