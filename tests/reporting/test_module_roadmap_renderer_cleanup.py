from __future__ import annotations

import ast
from pathlib import Path

from scripts.reporting.audit_consolidation import classify_source

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "scripts/coordination/module_roadmap.py"
CLI = ROOT / "scripts/coordination/render_module_roadmap_dashboard.py"


def _function_names(source: str) -> set[str]:
    tree = ast.parse(source)
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _cli_flags(source: str) -> set[str]:
    tree = ast.parse(source)
    result: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
        ):
            for argument in node.args:
                if (
                    isinstance(argument, ast.Constant)
                    and isinstance(argument.value, str)
                    and argument.value.startswith("-")
                ):
                    result.add(argument.value)
    return result


def test_residual_wrappers_are_removed() -> None:
    names = _function_names(ROADMAP.read_text(encoding="utf-8"))
    assert {"_row", "_boxed_table", "_token_color"}.isdisjoint(names)


def test_shared_renderer_is_called_directly() -> None:
    source = ROADMAP.read_text(encoding="utf-8")
    assert source.count("render_boxed_table_lines(") == 3
    assert source.count("tuple(TableRow(values=row) for row in table_rows)") == 2
    assert "from scripts.reporting.statuses import colorize" in source
    assert "return colorize(value, semantic_token, use_color=True)" in source


def test_cli_contract_is_unchanged() -> None:
    assert _cli_flags(CLI.read_text(encoding="utf-8")) == {
        "--after-current",
        "--before-current",
        "--module",
        "--modules",
        "--no-color",
        "--roadmap",
        "--root",
    }


def test_reporting_audit_reclassifies_module_roadmap() -> None:
    source = ROADMAP.read_text(encoding="utf-8")
    record = classify_source("scripts/coordination/module_roadmap.py", source)
    assert record.classification == "consolidated_consumer"
    assert record.status == "OK"
    assert record.local_helper_names == ()
