from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from scripts.reporting.table_renderer import TableRow, render_boxed_table_lines


def _signal_token(signal: str) -> str:
    normalized = signal.strip().upper()
    if normalized in {"GREEN", "OK", "ACCEPTED"}:
        return "success"
    if normalized in {"YELLOW", "WARNING"}:
        return "warning"
    if normalized in {"RED", "FAILED", "ERROR"}:
        return "failed"
    if normalized in {"BLUE", "ACTIVE"}:
        return "active"
    return "info"


def _section(
    title: str,
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: Sequence[TableRow],
    use_color: bool,
) -> list[str]:
    return [
        title,
        *render_boxed_table_lines(
            headers=headers,
            widths=widths,
            rows=rows,
            use_color=use_color,
        ),
    ]


def render_completion_intake_summary(
    *,
    result: str,
    mode: str,
    module: str,
    prompt_id: str,
    decision: str,
    reviewed_at: str,
    changed_files: Sequence[str],
    warnings: Sequence[str],
    next_actions: Sequence[str],
    use_color: bool,
) -> str:
    """Render a compact completion-intake decision without changing its data model."""

    signal_token = _signal_token(result)
    lines = ["Blueprint Module Completion Intake", ""]

    lines.extend(
        _section(
            "Decision summary",
            headers=("Field", "Value"),
            widths=(20, 78),
            rows=(
                TableRow(values=("RESULT:", result), token=signal_token),
                TableRow(values=("MODE:", mode)),
                TableRow(values=("MODULE:", module)),
                TableRow(values=("PROMPT_ID:", prompt_id)),
                TableRow(values=("DECISION:", decision), token=signal_token),
                TableRow(values=("REVIEWED_AT:", reviewed_at)),
                TableRow(values=("CHANGED_FILES:", str(len(changed_files)))),
                TableRow(values=("WARNINGS:", str(len(warnings)))),
            ),
            use_color=use_color,
        )
    )

    lines.append("")
    file_rows = tuple(
        TableRow(values=(str(index), path))
        for index, path in enumerate(changed_files, start=1)
    ) or (TableRow(values=("-", "No changed files")),)
    lines.extend(
        _section(
            "Changed files",
            headers=("#", "Path"),
            widths=(4, 94),
            rows=file_rows,
            use_color=use_color,
        )
    )

    lines.append("")
    warning_rows = tuple(
        TableRow(values=(str(index), warning), token="warning")
        for index, warning in enumerate(warnings, start=1)
    ) or (TableRow(values=("-", "No warnings"), token="success"),)
    lines.extend(
        _section(
            "Warnings",
            headers=("#", "Warning"),
            widths=(4, 94),
            rows=warning_rows,
            use_color=use_color,
        )
    )

    lines.extend(["", "NEXT_ACTION:"])
    action_rows = tuple(
        TableRow(values=(str(index), command), token="info")
        for index, command in enumerate(next_actions, start=1)
    ) or (TableRow(values=("-", "No follow-up command")),)
    lines.extend(
        render_boxed_table_lines(
            headers=("#", "Command"),
            widths=(4, 94),
            rows=action_rows,
            use_color=use_color,
        )
    )
    return "\n".join(lines)


def _step_row(
    scope: str,
    step: Mapping[str, Any] | None,
    *,
    token: str,
) -> TableRow:
    if not step:
        return TableRow(values=(scope, "-", "-", "-", "-"), token=token)

    return TableRow(
        values=(
            scope,
            str(step.get("sequence") or "-"),
            str(step.get("step_id") or "-"),
            str(step.get("status") or "-"),
            str(step.get("title") or "-"),
        ),
        token=token,
    )


def render_next_work_summary(
    *,
    data: Mapping[str, Any],
    use_color: bool,
) -> str:
    """Render next-work resolution while preserving the existing JSON contract."""

    result = str(data.get("result") or "-")
    signal = str(data.get("signal") or "-")
    module = str(data.get("module") or "-")
    decision_required = "yes" if data.get("decision_required") else "no"
    token = _signal_token(signal)

    lines = ["Blueprint Next-Work Suggestion", ""]
    lines.extend(
        _section(
            "Resolution summary",
            headers=("Field", "Value"),
            widths=(22, 76),
            rows=(
                TableRow(values=("RESULT:", result), token=token),
                TableRow(values=("SIGNAL:", signal), token=token),
                TableRow(values=("MODULE:", module)),
                TableRow(
                    values=("DECISION_REQUIRED:", decision_required),
                    token="warning" if decision_required == "yes" else "success",
                ),
            ),
            use_color=use_color,
        )
    )

    current = data.get("current_step")
    upcoming = data.get("next_step")
    lines.append("")
    lines.extend(
        _section(
            "Roadmap context",
            headers=("Scope", "Seq", "Step ID", "Status", "Title"),
            widths=(10, 5, 42, 12, 34),
            rows=(
                _step_row(
                    "CURRENT",
                    current if isinstance(current, Mapping) else None,
                    token="active",
                ),
                _step_row(
                    "NEXT",
                    upcoming if isinstance(upcoming, Mapping) else None,
                    token="planned",
                ),
            ),
            use_color=use_color,
        )
    )

    active_prompts = data.get("active_prompts")
    if isinstance(active_prompts, Sequence) and not isinstance(
        active_prompts, (str, bytes)
    ):
        active_rows = tuple(
            TableRow(
                values=(
                    str(item.get("sequence") or "-"),
                    str(item.get("prompt_id") or "-"),
                    str(item.get("status") or "-"),
                    str(item.get("file") or "-"),
                ),
                token="active",
            )
            for item in active_prompts
            if isinstance(item, Mapping)
        )
    else:
        active_rows = ()
    active_count = len(active_rows)
    if not active_rows:
        active_rows = (TableRow(values=("-", "No active prompts", "-", "-")),)

    lines.extend(["", f"ACTIVE_PROMPTS: {active_count}"])
    lines.extend(
        render_boxed_table_lines(
            headers=("Seq", "Prompt ID", "Status", "File"),
            widths=(5, 42, 24, 38),
            rows=active_rows,
            use_color=use_color,
        )
    )

    draft_candidates = data.get("draft_candidates")
    draft_values = (
        tuple(str(value) for value in draft_candidates)
        if isinstance(draft_candidates, Sequence)
        and not isinstance(draft_candidates, (str, bytes))
        else ()
    )
    draft_rows = tuple(
        TableRow(values=(str(index), value), token="planned")
        for index, value in enumerate(draft_values, start=1)
    ) or (TableRow(values=("-", "No draft candidates")),)
    lines.extend(["", f"DRAFT_CANDIDATES: {len(draft_values)}"])
    lines.extend(
        render_boxed_table_lines(
            headers=("#", "Path"),
            widths=(4, 100),
            rows=draft_rows,
            use_color=use_color,
        )
    )

    conflicting = data.get("conflicting_drafts")
    conflicting_values = (
        tuple(str(value) for value in conflicting)
        if isinstance(conflicting, Sequence)
        and not isinstance(conflicting, (str, bytes))
        else ()
    )
    conflict_rows = tuple(
        TableRow(values=(str(index), value), token="failed")
        for index, value in enumerate(conflicting_values, start=1)
    ) or (TableRow(values=("-", "No conflicting drafts"), token="success"),)
    lines.extend(["", f"CONFLICTING_DRAFTS: {len(conflicting_values)}"])
    lines.extend(
        render_boxed_table_lines(
            headers=("#", "Path"),
            widths=(4, 100),
            rows=conflict_rows,
            use_color=use_color,
        )
    )

    lines.extend(["", f"ACTION: {str(data.get('action') or '-')}"])
    return "\n".join(lines)


def render_next_prompt_summary(
    *,
    module: str,
    sequence: int,
    prompt_id: str,
    title: str,
    priority: str,
    file: str,
    path: str,
    use_color: bool,
) -> str:
    '''Render next-prompt metadata without changing resolution semantics.'''

    rows = (
        TableRow(values=("Module", module)),
        TableRow(values=("Sequence", str(sequence))),
        TableRow(values=("Prompt ID", prompt_id), token="active"),
        TableRow(values=("Title", title)),
        TableRow(values=("Priority", priority), token=priority),
        TableRow(values=("File", file)),
        TableRow(values=("Path", path)),
    )
    lines = ["ForPrint Next Prompt", ""]
    lines.extend(
        render_boxed_table_lines(
            headers=("Field", "Value"),
            widths=(14, 102),
            rows=rows,
            use_color=use_color,
        )
    )
    return "\n".join(lines)


def render_module_governance_summary(
    *,
    modules_checked: int,
    summary: Mapping[str, int],
    report_writing: bool,
    report_json: str | None,
    report_markdown: str | None,
    use_color: bool,
) -> str:
    """Render compact governance status without owning audit artifacts."""

    status_tokens = {
        "OK": "success",
        "NEEDS_ALIGNMENT": "warning",
        "WARN": "warning",
        "DEFERRED": "planned",
    }
    status_order = (
        "OK",
        "NEEDS_ALIGNMENT",
        "WARN",
        "DEFERRED",
    )

    summary_rows = (
        TableRow(
            values=("Modules checked:", str(modules_checked)),
            token="active",
        ),
        *(
            TableRow(
                values=(f"{status}:", str(summary.get(status, 0))),
                token=status_tokens[status],
            )
            for status in status_order
        ),
    )

    lines = ["ForPrint Module Governance Audit", ""]
    lines.extend(
        render_boxed_table_lines(
            headers=("Status", "Count"),
            widths=(24, 10),
            rows=summary_rows,
            use_color=use_color,
        )
    )

    if report_writing:
        artifact_rows = (
            TableRow(
                values=("Mode", "Report writing: enabled"),
                token="success",
            ),
            TableRow(
                values=("JSON report:", report_json or "-"),
            ),
            TableRow(
                values=("Markdown report:", report_markdown or "-"),
            ),
        )
    else:
        artifact_rows = (
            TableRow(
                values=("Mode", "Report writing: disabled"),
                token="active",
            ),
        )

    lines.extend(["", "Artifact output"])
    lines.extend(
        render_boxed_table_lines(
            headers=("Field", "Value"),
            widths=(18, 98),
            rows=artifact_rows,
            use_color=use_color,
        )
    )

    return "\n".join(lines)
