from __future__ import annotations

import json
from pathlib import Path

from scripts.reporting.audit_consolidation import (
    audit_repository,
    build_payload,
    classify_source,
)


def test_shared_console_summary_is_reporting_core() -> None:
    source = """
from scripts.reporting.table_renderer import render_boxed_table

def render_compact_report() -> str:
    return render_boxed_table(headers=("A",), widths=(4,), rows=())
"""
    record = classify_source("scripts/reporting/console_summary.py", source)

    assert record.classification == "shared_reporting_core"
    assert record.status == "OK"


def test_awareness_dashboard_is_consolidated_consumer() -> None:
    source = """
from scripts.reporting.document_awareness_tables import (
    render_awareness_area_summary,
)

def render_dashboard() -> str:
    return "\\n".join(render_awareness_area_summary((), use_color=False))
"""
    record = classify_source(
        "scripts/coordination/render_document_awareness_dashboard.py",
        source,
    )

    assert record.classification == "consolidated_consumer"
    assert record.status == "OK"


def test_module_roadmap_residual_wrappers_are_actionable() -> None:
    source = """
from scripts.reporting.table_renderer import render_boxed_table_lines

def _row():
    return ()

def _boxed_table():
    return render_boxed_table_lines(headers=(), widths=(), rows=())

def _token_color():
    return None
"""
    record = classify_source("scripts/coordination/module_roadmap.py", source)

    assert record.classification == "partial_migration"
    assert record.status == "ACTION"
    assert record.local_helper_names == (
        "_boxed_table",
        "_row",
        "_token_color",
    )


def test_json_payload_is_serializable(tmp_path: Path) -> None:
    targets = ("scripts/reporting/console_summary.py",)
    path = tmp_path / targets[0]
    path.parent.mkdir(parents=True)
    path.write_text(
        "from scripts.reporting.table_renderer import render_boxed_table\n",
        encoding="utf-8",
    )

    records = audit_repository(tmp_path, targets)
    payload = build_payload(tmp_path, records)

    encoded = json.dumps(payload, ensure_ascii=False)
    assert "blueprint_reporting_consolidation_audit_v0_1" in encoded
    assert payload["summary"]["failed"] == 0
