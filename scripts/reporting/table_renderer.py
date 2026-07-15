from __future__ import annotations

import re
from dataclasses import dataclass

from scripts.reporting.statuses import ANSI_RESET, colorize

ANSI_RE = re.compile(r"\033\[[0-9;]*m")


@dataclass(frozen=True, slots=True)
class TableRow:
    """One boxed-table row with an optional semantic visual token."""

    values: tuple[str, ...]
    token: str | None = None


def strip_ansi(value: str) -> str:
    """Remove ANSI sequences for correct visible-width calculations."""

    return ANSI_RE.sub("", value)


def _format_cell(value: str, width: int) -> str:
    clean = strip_ansi(str(value).replace("\n", " "))
    if len(clean) > width:
        clean = clean[: width - 1] + "…"
    return clean.ljust(width)


def _border(
    widths: tuple[int, ...],
    *,
    left: str,
    separator: str,
    right: str,
) -> str:
    return left + separator.join("─" * (width + 2) for width in widths) + right


def _row(
    values: tuple[str, ...],
    widths: tuple[int, ...],
    *,
    token: str | None,
    use_color: bool,
) -> str:
    cells = [_format_cell(value, width) for value, width in zip(values, widths, strict=True)]
    rendered = "│ " + " │ ".join(cells) + " │"
    if token:
        return colorize(rendered, token, use_color=use_color)
    return rendered


def render_boxed_table(
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: tuple[TableRow, ...],
    use_color: bool,
) -> str:
    """Render a closed-border table readable with or without ANSI color."""

    if len(headers) != len(widths):
        raise ValueError("headers and widths must have the same length")

    for row in rows:
        if len(row.values) != len(headers):
            raise ValueError("every table row must match the header count")

    lines = [
        _border(widths, left="┌", separator="┬", right="┐"),
        _row(headers, widths, token=None, use_color=False),
        _border(widths, left="├", separator="┼", right="┤"),
    ]
    lines.extend(
        _row(row.values, widths, token=row.token, use_color=use_color)
        for row in rows
    )
    lines.append(_border(widths, left="└", separator="┴", right="┘"))
    rendered = "\n".join(lines)
    return rendered + (ANSI_RESET if use_color else "")
