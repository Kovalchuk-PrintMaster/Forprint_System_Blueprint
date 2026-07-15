from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.reporting.models import CheckResult, ReportSummary
from scripts.reporting.statuses import STATUS_FAILED, STATUS_WARNING


def _generated_at() -> str:
    return datetime.now(UTC).isoformat()


def _duration(value: float) -> str:
    return f"{value:.2f}s"


def render_markdown_report(
    results: list[CheckResult],
    summary: ReportSummary,
    *,
    generated_at: str,
) -> str:
    """Render a durable human-readable report without raw successful logs."""

    lines = [
        "# ForPrint System Blueprint — Check Report",
        "",
        f"Generated at: `{generated_at}`",
        "",
        "## Summary",
        "",
        "| Overall | Total | OK | Warnings | Failed | Duration |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| {summary.overall_status} | {summary.total} | {summary.passed} | "
            f"{summary.warnings} | {summary.failed} | "
            f"{_duration(summary.duration_seconds)} |"
        ),
        "",
        "## Checks",
        "",
        "| Group | Check | Expected result | Status | Duration | Return code |",
        "|---|---|---|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            "| "
            f"{result.group} | {result.title} | {result.expected_result} | "
            f"{result.status} | {_duration(result.duration_seconds)} | "
            f"{result.return_code} |"
        )

    noteworthy = [
        result
        for result in results
        if result.status in {STATUS_WARNING, STATUS_FAILED}
    ]
    if noteworthy:
        lines.extend(["", "## Warning and failure evidence", ""])
        for result in noteworthy:
            lines.extend(
                [
                    f"### {result.title}",
                    "",
                    f"Status: `{result.status}`",
                    "",
                    "Command:",
                    "",
                    "```bash",
                    " ".join(result.command),
                    "```",
                    "",
                    "STDOUT tail:",
                    "",
                    "```text",
                    result.stdout_tail or "<empty>",
                    "```",
                    "",
                    "STDERR tail:",
                    "",
                    "```text",
                    result.stderr_tail or "<empty>",
                    "```",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def render_full_log(results: list[CheckResult], *, generated_at: str) -> str:
    """Render complete captured command output for deep diagnostics."""

    lines = [
        "ForPrint System Blueprint — full diagnostic log",
        f"Generated at: {generated_at}",
        "",
    ]

    for index, result in enumerate(results, start=1):
        lines.extend(
            [
                "=" * 96,
                f"[{index}] {result.title}",
                f"check_id: {result.check_id}",
                f"group: {result.group}",
                f"status: {result.status}",
                f"return_code: {result.return_code}",
                f"duration_seconds: {result.duration_seconds:.6f}",
                f"command: {' '.join(result.command)}",
                "-" * 96,
                "STDOUT",
                result.stdout or "<empty>",
                "-" * 96,
                "STDERR",
                result.stderr or "<empty>",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def write_report_artifacts(
    *,
    project_root: Path,
    results: list[CheckResult],
    summary: ReportSummary,
    include_full_log: bool,
) -> dict[str, Path]:
    """Write JSON/Markdown and optional full diagnostics using stable paths."""

    reports_dir = project_root / "reports"
    diagnostics_dir = reports_dir / "diagnostics"
    reports_dir.mkdir(parents=True, exist_ok=True)

    generated_at = _generated_at()
    json_path = reports_dir / "blueprint_check_report.json"
    markdown_path = reports_dir / "blueprint_check_report.md"

    payload = {
        "schema_version": "blueprint_check_report_v0_2",
        "generated_at": generated_at,
        "project_root": str(project_root),
        "summary": asdict(summary),
        "results": [asdict(result) for result in results],
    }

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_markdown_report(results, summary, generated_at=generated_at),
        encoding="utf-8",
    )

    paths = {
        "json": json_path.relative_to(project_root),
        "markdown": markdown_path.relative_to(project_root),
    }

    if include_full_log:
        diagnostics_dir.mkdir(parents=True, exist_ok=True)
        full_log_path = diagnostics_dir / "blueprint_check_report_full.log"
        full_log_path.write_text(
            render_full_log(results, generated_at=generated_at),
            encoding="utf-8",
        )
        paths["full_log"] = full_log_path.relative_to(project_root)

    return paths
