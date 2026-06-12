from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "module_coordination_template"
    / "validate_prompt_completion_report.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_prompt_completion_report", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_report(path: Path, frontmatter: str, body: str = "Human report text.") -> Path:
    path.write_text(f"---\n{frontmatter.strip()}\n---\n\n{body}\n", encoding="utf-8")
    return path


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


def test_valid_completion_report_passes(tmp_path: Path) -> None:
    validator = load_validator()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER)

    assert validator.validate_completion_report(report, expected_module="forprint_integration_gateway") == []


def test_missing_frontmatter_fails(tmp_path: Path) -> None:
    validator = load_validator()
    report = tmp_path / "completion.md"
    report.write_text("No frontmatter here.", encoding="utf-8")

    issues = validator.validate_completion_report(report)

    assert any("must start with YAML frontmatter" in issue for issue in issues)


def test_placeholder_token_fails(tmp_path: Path) -> None:
    validator = load_validator()
    report = write_report(
        tmp_path / "completion.md",
        VALID_FRONTMATTER.replace("abc1234", "{commit}"),
    )

    issues = validator.validate_completion_report(report)

    assert any("unresolved placeholder" in issue for issue in issues)


def test_expected_module_mismatch_fails(tmp_path: Path) -> None:
    validator = load_validator()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER)

    issues = validator.validate_completion_report(report, expected_module="wrong_module")

    assert any("does not match expected module" in issue for issue in issues)


def test_missing_required_check_fails(tmp_path: Path) -> None:
    validator = load_validator()
    frontmatter = VALID_FRONTMATTER.replace("  make_check_report: ok\n", "")
    report = write_report(tmp_path / "completion.md", frontmatter)

    issues = validator.validate_completion_report(report)

    assert any("required check `make_check_report`" in issue for issue in issues)


def test_non_ok_check_fails(tmp_path: Path) -> None:
    validator = load_validator()
    frontmatter = VALID_FRONTMATTER.replace("  make_check: ok\n", "  make_check: failed\n")
    report = write_report(tmp_path / "completion.md", frontmatter)

    issues = validator.validate_completion_report(report)

    assert any("non-ok value" in issue or "must be `ok`" in issue for issue in issues)


def test_missing_boundary_rule_fails(tmp_path: Path) -> None:
    validator = load_validator()
    frontmatter = VALID_FRONTMATTER.replace("  database_ownership_added: false\n", "")
    report = write_report(tmp_path / "completion.md", frontmatter)

    issues = validator.validate_completion_report(report)

    assert any("database_ownership_added" in issue for issue in issues)


def test_negative_boundary_key_form_is_accepted(tmp_path: Path) -> None:
    validator = load_validator()
    frontmatter = VALID_FRONTMATTER.replace(
        "  production_api_added: false\n",
        "  no_production_api_added: true\n",
    )
    report = write_report(tmp_path / "completion.md", frontmatter)

    issues = validator.validate_completion_report(report)

    assert not any("production_api_added" in issue for issue in issues)


def test_forbidden_module_id_fails(tmp_path: Path) -> None:
    validator = load_validator()
    report = write_report(tmp_path / "completion.md", VALID_FRONTMATTER, body="forprint_calculator_engine")

    issues = validator.validate_completion_report(report)

    assert any("forbidden token" in issue for issue in issues)
