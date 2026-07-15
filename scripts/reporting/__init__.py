"""Shared reporting primitives for ForPrint Blueprint and modules."""

from scripts.reporting.models import CheckDefinition, CheckResult, ReportSummary
from scripts.reporting.statuses import STATUS_FAILED, STATUS_OK, STATUS_WARNING
from scripts.reporting.table_renderer import (
    TableRow,
    format_visible_cell,
    leading_ansi_color,
    render_boxed_table,
    render_boxed_table_lines,
    strip_ansi,
)

__all__ = [
    "CheckDefinition",
    "CheckResult",
    "ReportSummary",
    "STATUS_FAILED",
    "STATUS_OK",
    "STATUS_WARNING",
    "TableRow",
    "format_visible_cell",
    "leading_ansi_color",
    "render_boxed_table",
    "render_boxed_table_lines",
    "strip_ansi",
]
