from scripts.run_blueprint_checks import (
    STATUS_FAILED,
    STATUS_OK,
    CheckResult,
    format_duration,
    render_markdown_report,
    render_text_table,
    summarize_results,
)


def _result(status: str) -> CheckResult:
    return CheckResult(
        check_id=f"check_{status.lower()}",
        title=f"Check {status}",
        expected_result="Expected result",
        status=status,
        return_code=0 if status == STATUS_OK else 1,
        duration_sec=0.123,
        command=["python", "--version"],
        stdout_tail="stdout",
        stderr_tail="stderr",
    )


def test_format_duration() -> None:
    assert format_duration(0.1234) == "0.12s"


def test_summarize_results_counts_statuses() -> None:
    summary = summarize_results([_result(STATUS_OK), _result(STATUS_FAILED)])

    assert summary[STATUS_OK] == 1
    assert summary[STATUS_FAILED] == 1


def test_render_text_table_contains_expected_columns() -> None:
    table = render_text_table([_result(STATUS_OK)], use_color=False)

    assert "Перевірка" in table
    assert "Очікуваний результат" in table
    assert "Статус" in table
    assert "OK" in table


def test_render_markdown_report_contains_summary() -> None:
    report = render_markdown_report([_result(STATUS_OK), _result(STATUS_FAILED)])

    assert "# ForPrint System Blueprint" in report
    assert "## Summary" in report
    assert "FAILED" in report