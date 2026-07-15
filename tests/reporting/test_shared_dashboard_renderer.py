from __future__ import annotations

from pathlib import Path

from scripts.reporting.table_renderer import (
    TableRow,
    format_visible_cell,
    render_boxed_table_lines,
    strip_ansi,
)

ROOT = Path(__file__).resolve().parents[2]


def test_shared_renderer_supports_semantic_and_legacy_row_color() -> None:
    rendered = "\n".join(
        render_boxed_table_lines(
            headers=("Status", "Value"),
            widths=(10, 12),
            rows=(
                TableRow(values=("accepted", "one"), token="success"),
                TableRow(values=("active", "two"), color="\033[34m"),
            ),
            use_color=True,
        )
    )

    assert "\033[32m" in rendered
    assert "\033[34m" in rendered
    assert strip_ansi(rendered).count("accepted") == 1


def test_shared_renderer_preserves_leading_cell_color() -> None:
    cell = format_visible_cell("\033[33mwarning\033[0m", 10, use_color=True)

    assert cell.startswith("\033[33m")
    assert strip_ansi(cell) == "warning   "


def test_shared_renderer_no_color_removes_ansi() -> None:
    rendered = "\n".join(
        render_boxed_table_lines(
            headers=("Status",),
            widths=(10,),
            rows=(
                TableRow(
                    values=("\033[31mfailed\033[0m",),
                    color="\033[31m",
                ),
            ),
            use_color=False,
        )
    )

    assert "\033[" not in rendered
    assert "failed" in rendered


def test_shared_renderer_truncates_with_ellipsis() -> None:
    assert format_visible_cell("abcdefghijkl", 6, use_color=False) == "abcde…"


def test_prompt_dashboard_uses_shared_renderer() -> None:
    source = (
        ROOT / "scripts/coordination/render_prompt_dashboard.py"
    ).read_text(encoding="utf-8")

    assert "from scripts.reporting.table_renderer import" in source
    assert "render_boxed_table_lines" in source
    assert "def _boxed_border" not in source
    assert "def _boxed_row" not in source
    assert "class TableRow" not in source


def test_module_roadmap_uses_shared_renderer() -> None:
    source = (
        ROOT / "scripts/coordination/module_roadmap.py"
    ).read_text(encoding="utf-8")

    assert "from scripts.reporting.table_renderer import" in source
    assert "render_boxed_table_lines" in source
    assert "def _boxed_border" not in source
    assert "def _boxed_row" not in source
    assert "def _format_visible_cell" not in source
    assert "def _strip_ansi" not in source
