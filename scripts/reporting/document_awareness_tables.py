from __future__ import annotations

from collections.abc import Sequence

from scripts.reporting.table_renderer import TableRow, render_boxed_table_lines


def _rows(values: Sequence[Sequence[str]]) -> tuple[TableRow, ...]:
    return tuple(TableRow(values=tuple(str(cell) for cell in row)) for row in values)


def render_awareness_area_summary(
    rows: Sequence[Sequence[str]],
    *,
    use_color: bool,
) -> list[str]:
    """Render the document-awareness source summary through the shared core."""

    return render_boxed_table_lines(
        headers=(
            "Source",
            "Total",
            "Unseen",
            "Changed",
            "In progress",
            "Ack",
            "Applied",
            "Deferred",
            "Priority",
            "Action",
        ),
        widths=(22, 5, 6, 7, 10, 4, 7, 8, 9, 32),
        rows=_rows(rows),
        use_color=use_color,
    )


def render_awareness_document_table(
    rows: Sequence[Sequence[str]],
    *,
    use_color: bool,
) -> list[str]:
    """Render attention-required or all awareness documents."""

    return render_boxed_table_lines(
        headers=("Priority", "Status", "Source", "Path", "Action"),
        widths=(10, 14, 22, 68, 36),
        rows=_rows(rows),
        use_color=use_color,
    )


def render_context_bundle_summary(
    *,
    module: str,
    scope: str,
    document_count: int,
    write_mode: str,
    output_path: str | None,
    use_color: bool,
) -> str:
    """Render the operator summary without changing bundle Markdown content."""

    mode_token = "success" if write_mode == "disabled" else "active"
    rows = [
        TableRow(values=("Module:", module)),
        TableRow(values=("Scope:", scope)),
        TableRow(values=("Documents included:", str(document_count))),
        TableRow(values=("Write mode:", write_mode), token=mode_token),
    ]
    if output_path:
        rows.append(TableRow(values=("Bundle:", output_path), token="info"))

    lines = [
        "ForPrint Coordination Context Bundle",
        "",
        *render_boxed_table_lines(
            headers=("Field", "Value"),
            widths=(22, 76),
            rows=tuple(rows),
            use_color=use_color,
        ),
    ]
    return "\n".join(lines)


def render_document_manifest_summary(
    *,
    schema_version: str,
    source_registry: str,
    document_count: int,
    warnings: Sequence[str],
    use_color: bool,
) -> str:
    """Render a compact terminal summary while preserving report artifacts."""

    warning_count = len(warnings)
    lines = [
        "ForPrint Coordination Document Manifest",
        "",
        *render_boxed_table_lines(
            headers=("Field", "Value"),
            widths=(22, 76),
            rows=(
                TableRow(values=("Schema:", schema_version)),
                TableRow(values=("Source registry:", source_registry)),
                TableRow(values=("Documents:", str(document_count))),
                TableRow(
                    values=("Warnings:", str(warning_count)),
                    token="warning" if warning_count else "success",
                ),
            ),
            use_color=use_color,
        ),
    ]

    if warnings:
        lines.extend(
            [
                "",
                "Warnings:",
                *render_boxed_table_lines(
                    headers=("#", "Warning"),
                    widths=(4, 94),
                    rows=tuple(
                        TableRow(
                            values=(str(index), str(warning)),
                            token="warning",
                        )
                        for index, warning in enumerate(warnings, start=1)
                    ),
                    use_color=use_color,
                ),
            ]
        )

    return "\n".join(lines)
