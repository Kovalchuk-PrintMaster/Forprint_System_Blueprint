from pathlib import Path

from scripts.coordination.modules._shared.reporting import build_metric_rows
from scripts.coordination.modules._shared.repository_scan import scan_repository
from scripts.coordination.modules.forprint_system_blueprint.workflows.self_audit import (
    WORKFLOW_INDEX,
)


def test_self_audit_dashboard_is_bounded() -> None:
    root = Path(__file__).resolve().parents[4]
    scan = scan_repository(root, workflow_index_path=WORKFLOW_INDEX)
    rows = build_metric_rows(scan, external_input_status="awaiting_input")

    assert 10 <= len(rows) <= 15
    assert rows[0]["metric"] == "Repository files"
    assert any(row["metric"] == "External input" for row in rows)
