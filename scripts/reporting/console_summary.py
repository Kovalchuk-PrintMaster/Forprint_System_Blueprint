from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from scripts.reporting.models import CheckResult, ReportSummary
from scripts.reporting.statuses import STATUS_FAILED, STATUS_WARNING, status_token
from scripts.reporting.table_renderer import TableRow, render_boxed_table

GROUP_TITLES = {
    "core_quality": "Core quality",
    "coordination": "Coordination and governance",
    "documentation": "Documentation and generated artifacts",
}


def _duration(value: float) -> str:
    return f"{value:.2f}s"


def _marker(result: CheckResult) -> str:
    if result.status == STATUS_FAILED:
        return "!"
    if result.status == STATUS_WARNING:
        return "~"
    return ""


def render_check_groups(
    results: list[CheckResult],
    *,
    use_color: bool,
) -> str:
    """Render one compact table per coherent check group."""

    grouped: dict[str, list[CheckResult]] = defaultdict(list)
    for result in results:
        grouped[result.group].append(result)

    sections: list[str] = []
    ordered_groups = ("core_quality", "coordination", "documentation")

    for group in ordered_groups:
        group_results = grouped.get(group, [])
        if not group_results:
            continue

        sections.append(GROUP_TITLES.get(group, group))
        rows = tuple(
            TableRow(
                values=(
                    _marker(result),
                    result.title,
                    result.expected_result,
                    result.status,
                    _duration(result.duration_seconds),
                ),
                token=status_token(result.status),
            )
            for result in group_results
        )
        sections.append(
            render_boxed_table(
                headers=("", "Check", "Expected result", "Status", "Time"),
                widths=(2, 30, 54, 9, 8),
                rows=rows,
                use_color=use_color,
            )
        )

    return "\n\n".join(sections)


def render_final_summary(
    summary: ReportSummary,
    *,
    artifact_paths: dict[str, Path],
    use_color: bool,
) -> str:
    """Render a compact final decision and artifact table."""

    artifact_text = ", ".join(
        f"{name}={path}" for name, path in sorted(artifact_paths.items())
    )
    blocker_text = ", ".join(summary.blockers) if summary.blockers else "-"

    rows = (
        TableRow(
            values=(
                ">",
                summary.overall_status,
                str(summary.total),
                str(summary.passed),
                str(summary.warnings),
                str(summary.failed),
                f"{summary.duration_seconds:.2f}s",
            ),
            token=status_token(summary.overall_status),
        ),
    )

    table = render_boxed_table(
        headers=("", "Overall", "Total", "OK", "Warnings", "Failed", "Time"),
        widths=(2, 10, 7, 7, 10, 8, 10),
        rows=rows,
        use_color=use_color,
    )

    return "\n".join(
        [
            "Final result",
            table,
            f"Blockers: {blocker_text}",
            f"Artifacts: {artifact_text}",
        ]
    )


def render_compact_report(
    results: list[CheckResult],
    summary: ReportSummary,
    *,
    artifact_paths: dict[str, Path],
    use_color: bool,
) -> str:
    """Render the complete routine Blueprint report."""

    return "\n\n".join(
        [
            "ForPrint System Blueprint — compact check report",
            render_check_groups(results, use_color=use_color),
            render_final_summary(
                summary,
                artifact_paths=artifact_paths,
                use_color=use_color,
            ),
        ]
    )
