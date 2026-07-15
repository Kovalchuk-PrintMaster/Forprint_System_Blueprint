from __future__ import annotations

import ast
from pathlib import Path

from scripts.reporting.document_awareness_tables import (
    render_awareness_area_summary,
    render_awareness_document_table,
    render_context_bundle_summary,
    render_document_manifest_summary,
)

ROOT = Path(__file__).resolve().parents[2]


def test_awareness_tables_use_closed_borders_and_no_color() -> None:
    area = "\n".join(
        render_awareness_area_summary(
            (
                (
                    "coordination",
                    "8",
                    "1",
                    "0",
                    "2",
                    "3",
                    "1",
                    "1",
                    "\033[31mcritical\033[0m",
                    "Review changed documents",
                ),
            ),
            use_color=False,
        )
    )
    detail = "\n".join(
        render_awareness_document_table(
            (
                (
                    "\033[31mcritical\033[0m",
                    "\033[33mchanged\033[0m",
                    "coordination",
                    "coordination/global_policy/example.md",
                    "Review before module work",
                ),
            ),
            use_color=False,
        )
    )

    assert "Source" in area
    assert "Priority" in detail
    assert "coordination/global_policy/example.md" in detail
    assert "┌" in area and "┘" in area
    assert "┌" in detail and "┘" in detail
    assert "\033[" not in area
    assert "\033[" not in detail


def test_context_bundle_summary_preserves_legacy_labels() -> None:
    rendered = render_context_bundle_summary(
        module="forprint_library",
        scope="bootstrap",
        document_count=10,
        write_mode="disabled",
        output_path=None,
        use_color=False,
    )

    assert "ForPrint Coordination Context Bundle" in rendered
    assert "Module:" in rendered
    assert "Scope:" in rendered
    assert "Documents included:" in rendered
    assert "Write mode:" in rendered
    assert "disabled" in rendered
    assert "\033[" not in rendered


def test_manifest_summary_preserves_labels_and_warning_evidence() -> None:
    rendered = render_document_manifest_summary(
        schema_version="coordination_document_manifest_v0_1",
        source_registry="coordination/document_sources.yaml",
        document_count=12,
        warnings=("Missing optional source",),
        use_color=False,
    )

    assert "ForPrint Coordination Document Manifest" in rendered
    assert "Schema:" in rendered
    assert "Source registry:" in rendered
    assert "Documents:" in rendered
    assert "Warnings:" in rendered
    assert "Missing optional source" in rendered
    assert "\033[" not in rendered


def test_awareness_scripts_delegate_terminal_tables_to_shared_presentation() -> None:
    awareness = (
        ROOT / "scripts/coordination/render_document_awareness_dashboard.py"
    ).read_text(encoding="utf-8")
    context = (
        ROOT / "scripts/coordination/build_context_bundle.py"
    ).read_text(encoding="utf-8")
    manifest = (
        ROOT / "scripts/coordination/build_document_manifest.py"
    ).read_text(encoding="utf-8")

    assert "render_awareness_area_summary" in awareness
    assert "render_awareness_document_table" in awareness
    assert "def _render_table" not in awareness
    assert "def _strip_ansi" not in awareness

    assert "render_context_bundle_summary" in context
    assert "--no-color" in _cli_flags(context)
    assert "print(bundle.content)" in context

    assert "render_document_manifest_summary" in manifest
    assert "--no-color" in _cli_flags(manifest)
    assert "def render_markdown" in manifest
    assert "| Source | Documents |" in manifest

def _cli_flags(source: str) -> set[str]:
    flags: set[str] = set()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue

        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            flags.add(first.value)

    return flags
