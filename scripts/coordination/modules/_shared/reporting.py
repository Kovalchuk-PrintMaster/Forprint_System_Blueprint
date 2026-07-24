from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from scripts.reporting.table_renderer import TableRow, render_boxed_table

TOKEN_SUCCESS = "success"
TOKEN_WARNING = "warning"
TOKEN_FAILED = "failed"
TOKEN_INFO = "info"
TOKEN_PLANNED = "planned"


def _coverage(value: int, total: int) -> tuple[str, str, str]:
    if total <= 0:
        return "unknown", TOKEN_PLANNED, "No denominator"
    percentage = (value / total) * 100
    label = f"{value} / {total}"
    note = f"{percentage:.1f}%"
    if percentage >= 80:
        token = TOKEN_SUCCESS
    elif percentage >= 50:
        token = TOKEN_WARNING
    else:
        token = TOKEN_FAILED
    return label, token, note


def build_metric_rows(
    scan: dict[str, Any],
    *,
    external_input_status: str,
) -> list[dict[str, str]]:
    files = scan["files"]
    python = scan["python"]
    make = scan["make"]
    workflows = scan["workflows"]
    freshness = scan["repository_knowledge"].get("freshness_days")

    rows: list[dict[str, str]] = [
        {
            "metric": "Repository files",
            "value": str(files["total"]),
            "state": "INFO",
            "token": TOKEN_INFO,
            "note": "Current Git-visible scope",
        },
    ]

    coverage_specs = (
        ("Files indexed", files["indexed"], files["total"]),
        ("Purpose understood", files["purpose_understood"], files["total"]),
        ("Dependencies mapped", files["dependencies_mapped"], files["total"]),
        ("Fully verified", files["fully_verified"], files["total"]),
        ("Python parsed", python["parsed"], python["files"]),
        (
            "Workflow Make targets",
            make["workflow_targets_mapped"],
            make["workflow_targets_declared"],
        ),
        ("Workflows documented", workflows["documented"], workflows["total"]),
        ("Workflows automated", workflows["automated"], workflows["total"]),
        ("Recovery coverage", workflows["recovery"], workflows["total"]),
    )
    for name, value, total in coverage_specs:
        label, token, note = _coverage(value, total)
        state = {
            TOKEN_SUCCESS: "HEALTHY",
            TOKEN_WARNING: "PARTIAL",
            TOKEN_FAILED: "LOW",
            TOKEN_PLANNED: "UNKNOWN",
        }[token]
        rows.append(
            {
                "metric": name,
                "value": label,
                "state": state,
                "token": token,
                "note": note,
            }
        )

    rows.extend(
        [
            {
                "metric": "Unknown files",
                "value": str(files["unknown"]),
                "state": "ATTENTION" if files["unknown"] else "HEALTHY",
                "token": TOKEN_WARNING if files["unknown"] else TOKEN_SUCCESS,
                "note": "Not purpose-verified",
            },
            {
                "metric": "Python entrypoints",
                "value": str(python["entrypoints"]),
                "state": "INFO",
                "token": TOKEN_INFO,
                "note": f"{python['functions']} functions; {python['classes']} classes",
            },
            {
                "metric": "Repository snapshot",
                "value": (
                    "unknown" if freshness is None else f"{freshness} day(s)"
                ),
                "state": "UNKNOWN" if freshness is None else "INFO",
                "token": TOKEN_PLANNED if freshness is None else TOKEN_INFO,
                "note": scan["repository_knowledge"].get("inventory_path") or "Missing",
            },
            {
                "metric": "Metadata consistency",
                "value": scan["metadata_consistency"]["status"],
                "state": "UNKNOWN",
                "token": TOKEN_PLANNED,
                "note": "Dedicated audit deferred",
            },
            {
                "metric": "External input",
                "value": external_input_status,
                "state": (
                    "WAITING"
                    if external_input_status == "awaiting_input"
                    else "READY"
                    if external_input_status == "provided"
                    else "INFO"
                ),
                "token": (
                    TOKEN_WARNING
                    if external_input_status == "awaiting_input"
                    else TOKEN_SUCCESS
                    if external_input_status == "provided"
                    else TOKEN_INFO
                ),
                "note": "operator_input/.../bsa.yaml",
            },
        ]
    )
    return rows[:15]


def render_dashboard(
    rows: Iterable[dict[str, str]],
    *,
    use_color: bool,
) -> str:
    table_rows = tuple(
        TableRow(
            values=(
                row["metric"],
                row["value"],
                row["state"],
                row["note"],
            ),
            token=row["token"],
        )
        for row in rows
    )
    table = render_boxed_table(
        headers=("Metric", "Value", "State", "Note"),
        widths=(24, 16, 11, 42),
        rows=table_rows,
        use_color=use_color,
    )
    return "\n".join(
        [
            "Blueprint Self-Knowledge",
            table,
        ]
    )


def render_full_markdown(
    *,
    scan: dict[str, Any],
    rows: list[dict[str, str]],
    runtime: dict[str, Any],
    external_analysis: dict[str, Any] | None,
) -> str:
    lines = [
        "# Blueprint Self-Knowledge Report",
        "",
        f"Generated at: `{scan['generated_at']}`",
        "",
        "## Current metrics",
        "",
        "| Metric | Value | State | Note |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['metric']} | {row['value']} | {row['state']} | {row['note']} |"
        )

    lines.extend(
        [
            "",
            "## Runtime",
            "",
            "```yaml",
            f"run_id: {runtime['run_id']}",
            f"stage: {runtime['stage']}",
            f"request_id: {runtime['request_id']}",
            f"bundle: {runtime.get('bundle_path')}",
            "```",
            "",
            "## Repository categories",
            "",
            "| Root | Files |",
            "|---|---:|",
        ]
    )
    for category, count in scan["files"]["categories"].items():
        lines.append(f"| {category} | {count} |")

    lines.extend(
        [
            "",
            "## Python inventory",
            "",
            f"- Files: `{scan['python']['files']}`",
            f"- Parsed: `{scan['python']['parsed']}`",
            f"- Parse failures: `{scan['python']['parse_failures']}`",
            f"- Functions: `{scan['python']['functions']}`",
            f"- Classes: `{scan['python']['classes']}`",
            f"- CLI entrypoints: `{scan['python']['entrypoints']}`",
            "",
            "## Make and workflow coverage",
            "",
            f"- Make targets: `{scan['make']['targets_total']}`",
            (
                "- Declared workflow targets: "
                f"`{scan['make']['workflow_targets_declared']}`"
            ),
            (
                "- Mapped workflow targets: "
                f"`{scan['make']['workflow_targets_mapped']}`"
            ),
            f"- Workflow definitions: `{scan['workflows']['total']}`",
            f"- Documented: `{scan['workflows']['documented']}`",
            f"- Automated: `{scan['workflows']['automated']}`",
            f"- Recovery-covered: `{scan['workflows']['recovery']}`",
            "",
            "## Honesty boundary",
            "",
            "- Indexed does not mean understood.",
            "- A filename alone does not verify purpose.",
            "- Low coverage is a planning signal, not an automatic failure.",
            "- Metadata consistency remains unknown in v0.1.",
        ]
    )

    if external_analysis:
        analysis = external_analysis["analysis"]
        lines.extend(
            [
                "",
                "## External analysis",
                "",
                f"Confidence: `{analysis['confidence']}`",
                "",
                analysis["summary"].strip(),
            ]
        )
        for title, key in (
            ("Known strengths", "known_strengths"),
            ("Gaps", "gaps"),
            ("Priority actions", "priority_actions"),
            ("Confirmed unknowns", "confirmed_unknowns"),
            ("Conflicts", "conflicts"),
            ("Workflow recommendations", "workflow_recommendations"),
        ):
            lines.extend(["", f"### {title}", ""])
            values = analysis.get(key, [])
            lines.extend(f"- {value}" for value in values)
            if not values:
                lines.append("- None provided.")
        if analysis.get("notes"):
            lines.extend(["", "### Notes", "", str(analysis["notes"]).strip()])

    return "\n".join(lines).rstrip() + "\n"


def artifact_paths(root: Path) -> dict[str, Path]:
    current = root / "reports/modules/forprint_system_blueprint/current"
    return {
        "summary": current / "self_knowledge_summary.json",
        "full": current / "self_knowledge_report.md",
        "runtime": current / "runtime_state.yaml",
    }
