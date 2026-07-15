from __future__ import annotations

import json
from pathlib import Path

from scripts.reporting.artifact_writer import write_report_artifacts
from scripts.reporting.console_summary import render_compact_report
from scripts.reporting.models import CheckResult
from scripts.reporting.statuses import (
    STATUS_FAILED,
    STATUS_OK,
    STATUS_WARNING,
    detect_status,
    has_warning_signal,
    summarize_results,
)
from scripts.reporting.table_renderer import TableRow, render_boxed_table
from scripts.run_blueprint_checks import build_checks


def _result(
    *,
    status: str = STATUS_OK,
    group: str = "core_quality",
    title: str = "Example check",
) -> CheckResult:
    return CheckResult(
        check_id="example",
        title=title,
        expected_result="Expected",
        command=("python", "-V"),
        group=group,
        status=status,
        return_code=0 if status != STATUS_FAILED else 1,
        duration_seconds=0.25,
        stdout="ok\n",
        stderr="",
        stdout_tail="ok",
        stderr_tail="",
    )


def test_zero_warning_summary_is_not_a_warning() -> None:
    assert not has_warning_signal("Warnings: 0\nAll checks passed")
    assert detect_status(0, "Warnings: 0") == STATUS_OK


def test_real_warning_is_detected() -> None:
    assert has_warning_signal("WARNING: review required")
    assert detect_status(0, "WARNING: review required") == STATUS_WARNING


def test_non_zero_return_code_is_failed() -> None:
    assert detect_status(2, "") == STATUS_FAILED


def test_summary_preserves_counts_and_blockers() -> None:
    results = [
        _result(status=STATUS_OK, title="OK"),
        _result(status=STATUS_WARNING, title="Warn"),
        _result(status=STATUS_FAILED, title="Fail"),
    ]
    summary = summarize_results(results)

    assert summary.overall_status == STATUS_FAILED
    assert summary.total == 3
    assert summary.passed == 1
    assert summary.warnings == 1
    assert summary.failed == 1
    assert summary.blockers == ("Fail",)


def test_boxed_table_is_readable_without_color() -> None:
    rendered = render_boxed_table(
        headers=("A", "B"),
        widths=(6, 8),
        rows=(TableRow(values=("one", "two"), token="success"),),
        use_color=False,
    )

    assert "┌" in rendered
    assert "└" in rendered
    assert "\033[" not in rendered
    assert "one" in rendered


def test_compact_report_uses_multiple_concern_tables(tmp_path: Path) -> None:
    results = [
        _result(group="core_quality", title="Core"),
        _result(group="coordination", title="Coordination"),
        _result(group="documentation", title="Docs"),
    ]
    summary = summarize_results(results)
    rendered = render_compact_report(
        results,
        summary,
        artifact_paths={"json": Path("reports/report.json")},
        use_color=False,
    )

    assert "Core quality" in rendered
    assert "Coordination and governance" in rendered
    assert "Documentation and generated artifacts" in rendered
    assert "Final result" in rendered


def test_artifact_writer_creates_machine_human_and_full_reports(
    tmp_path: Path,
) -> None:
    results = [_result()]
    summary = summarize_results(results)

    paths = write_report_artifacts(
        project_root=tmp_path,
        results=results,
        summary=summary,
        include_full_log=True,
    )

    assert set(paths) == {"json", "markdown", "full_log"}
    payload = json.loads((tmp_path / paths["json"]).read_text(encoding="utf-8"))
    assert payload["schema_version"] == "blueprint_check_report_v0_2"
    assert payload["summary"]["overall_status"] == STATUS_OK
    assert (tmp_path / paths["markdown"]).exists()
    assert (tmp_path / paths["full_log"]).exists()


def test_check_catalog_has_stable_groups_and_no_lint_fix() -> None:
    checks = build_checks()

    assert checks
    assert {check.group for check in checks} == {
        "core_quality",
        "coordination",
        "documentation",
    }
    commands = [" ".join(check.command) for check in checks]
    assert not any("--fix" in command for command in commands)
    assert any(
        "tests/coordination/test_module_completion_finalization.py" in command
        for command in commands
    )

def test_legacy_runner_public_api_remains_compatible() -> None:
    from scripts import run_blueprint_checks as runner

    result = runner.CheckResult(
        "legacy",
        "Legacy",
        "Works",
        runner.STATUS_OK,
        0,
        0.1,
        ["python", "-V"],
        "",
        "",
    )

    assert result.duration_seconds == 0.1
    assert result.duration_sec == 0.1
    assert runner.summarize_results([result])[runner.STATUS_OK] == 1
    rendered = runner.render_text_table([result], use_color=False)
    assert "ForPrint System Blueprint — check report" in rendered
    assert "Legacy" in rendered

def test_legacy_table_keeps_ukrainian_public_headers() -> None:
    from scripts import run_blueprint_checks as runner

    result = runner.CheckResult(
        "legacy-labels",
        "Legacy labels",
        "Works",
        runner.STATUS_OK,
        0,
        0.1,
        ["python", "-V"],
        "",
        "",
    )

    rendered = runner.render_text_table([result], use_color=False)

    assert "Перевірка" in rendered
    assert "Очікуваний результат" in rendered
    assert "Статус" in rendered
    assert "Час" in rendered

def test_check_catalog_preserves_existing_governance_contract_titles() -> None:
    titles = {check.title for check in build_checks()}

    assert "Module governance audit" in titles
    assert "Completion packet template validation" in titles
