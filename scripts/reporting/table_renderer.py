from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from scripts.reporting.statuses import ANSI_RESET, token_color

ANSI_RE = re.compile(r"\033\[[0-9;]*m")


@dataclass(frozen=True, slots=True)
class TableRow:
    """Shared boxed-table row.

    `token` is preferred. `color` preserves existing dashboard compatibility.
    """

    values: tuple[str, ...]
    token: str | None = None
    color: str | None = None


def strip_ansi(value: str) -> str:
    """Remove ANSI sequences."""

    return ANSI_RE.sub("", value)


def leading_ansi_color(value: str) -> str | None:
    """Return a leading ANSI color sequence."""

    match = ANSI_RE.match(value)
    if not match:
        return None
    color = match.group(0)
    return None if color == ANSI_RESET else color


def format_visible_cell(
    value: str,
    width: int,
    *,
    use_color: bool = True,
) -> str:
    """Normalize, truncate and pad one visible cell."""

    if width < 1:
        raise ValueError("table cell width must be at least 1")

    raw = str(value).replace("\n", " ")
    color = leading_ansi_color(raw) if use_color else None
    clean = strip_ansi(raw)
    if len(clean) > width:
        clean = clean[: width - 1] + "…"

    cell = clean.ljust(width)
    return f"{color}{cell}{ANSI_RESET}" if color else cell


def _border(
    widths: tuple[int, ...],
    *,
    left: str,
    separator: str,
    right: str,
) -> str:
    return left + separator.join("─" * (width + 2) for width in widths) + right


def _resolve_row_color(row: TableRow, *, use_color: bool) -> str | None:
    if not use_color:
        return None
    if row.color:
        return row.color
    return token_color(row.token) if row.token else None


def _row(
    values: tuple[str, ...],
    widths: tuple[int, ...],
    *,
    row_color: str | None,
    use_color: bool,
) -> str:
    cells = [
        format_visible_cell(value, width, use_color=use_color)
        for value, width in zip(values, widths, strict=True)
    ]
    rendered = "│ " + " │ ".join(cells) + " │"
    return f"{row_color}{rendered}{ANSI_RESET}" if row_color else rendered


def render_boxed_table_lines(
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: Sequence[TableRow],
    use_color: bool,
) -> list[str]:
    """Render a closed-border table as composable lines."""

    if len(headers) != len(widths):
        raise ValueError("headers and widths must have the same length")
    for row in rows:
        if len(row.values) != len(headers):
            raise ValueError("every table row must match the header count")

    lines = [
        _border(widths, left="┌", separator="┬", right="┐"),
        _row(headers, widths, row_color=None, use_color=False),
        _border(widths, left="├", separator="┼", right="┤"),
    ]
    lines.extend(
        _row(
            row.values,
            widths,
            row_color=_resolve_row_color(row, use_color=use_color),
            use_color=use_color,
        )
        for row in rows
    )
    lines.append(_border(widths, left="└", separator="┴", right="┘"))
    return lines


def render_boxed_table(
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: Sequence[TableRow],
    use_color: bool,
) -> str:
    """Render a closed-border table as text."""

    rendered = "\n".join(
        render_boxed_table_lines(
            headers=headers,
            widths=widths,
            rows=rows,
            use_color=use_color,
        )
    )
    return rendered + (ANSI_RESET if use_color else "")
