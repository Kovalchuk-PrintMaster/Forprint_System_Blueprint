from __future__ import annotations

from pathlib import Path

from scripts.coordination.render_document_awareness_dashboard import (
    build_dashboard,
    render_dashboard,
)


def _write_source_registry(root: Path) -> Path:
    registry_dir = root / "coordination" / "document_awareness"
    registry_dir.mkdir(parents=True)

    registry_path = registry_dir / "source_registry.yaml"
    registry_path.write_text(
        """schema_version: coordination_document_source_registry_v0_1

sources:
  - source_id: global_policy
    path: coordination/global_policy
    priority: critical
    applies_to: all
    action: must_review_before_work
    include_patterns:
      - "*.md"
      - "*.yaml"
    exclude_patterns:
      - ".gitkeep"

  - source_id: module_policy
    path: coordination/module_policy
    priority: critical
    applies_to: module_specific
    action: must_review_before_work
    include_patterns:
      - "*.md"
    exclude_patterns:
      - ".gitkeep"

  - source_id: reports
    path: coordination/reports
    priority: reference
    applies_to: reference
    action: review_when_relevant
    include_patterns:
      - "*.md"
    exclude_patterns:
      - ".gitkeep"
""",
        encoding="utf-8",
    )

    return registry_path


def _write_ledger(root: Path, *, path: str, content_hash: str, status: str) -> Path:
    ledger_dir = root / "coordination" / "blueprint_awareness"
    ledger_dir.mkdir(parents=True)

    ledger_path = ledger_dir / "document_review_ledger.yaml"
    ledger_path.write_text(
        f"""schema_version: module_document_awareness_ledger_v0_1
module: forprint_library

reviewed_documents:
  - path: {path}
    content_hash: {content_hash}
    module_review_status: {status}
    reviewed_at: null
    module_commit: null
    notes: null
""",
        encoding="utf-8",
    )

    return ledger_path


def test_dashboard_marks_documents_unseen_without_ledger(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    (global_dir / "policy.md").write_text("# Policy\n\nContent.\n", encoding="utf-8")

    module_dir = tmp_path / "coordination" / "module_policy" / "forprint_library"
    module_dir.mkdir(parents=True)
    (module_dir / "module_policy.md").write_text(
        "# Module Policy\n\nContent.\n",
        encoding="utf-8",
    )

    other_module_dir = tmp_path / "coordination" / "module_policy" / "forprint_crm"
    other_module_dir.mkdir(parents=True)
    (other_module_dir / "module_policy.md").write_text(
        "# CRM Module Policy\n\nContent.\n",
        encoding="utf-8",
    )

    dashboard = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )

    assert dashboard.document_count == 2
    assert {record.awareness_status for record in dashboard.records} == {"unseen"}
    assert all("forprint_crm" not in record.document.path for record in dashboard.records)


def test_dashboard_marks_changed_when_hash_differs(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    document_path = global_dir / "policy.md"
    document_path.write_text("# Policy\n\nCurrent content.\n", encoding="utf-8")

    ledger_path = _write_ledger(
        tmp_path,
        path="coordination/global_policy/policy.md",
        content_hash="sha256:old",
        status="acknowledged",
    )

    dashboard = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=ledger_path,
    )

    assert dashboard.records[0].awareness_status == "changed"
    assert dashboard.records[0].recommended_action == "review_changed_document_hash"


def test_dashboard_keeps_status_when_hash_matches(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    document_path = global_dir / "policy.md"
    document_path.write_text("# Policy\n\nCurrent content.\n", encoding="utf-8")

    initial_dashboard = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )
    content_hash = initial_dashboard.records[0].document.content_hash

    ledger_path = _write_ledger(
        tmp_path,
        path="coordination/global_policy/policy.md",
        content_hash=content_hash,
        status="applied",
    )

    dashboard = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=ledger_path,
    )

    assert dashboard.records[0].awareness_status == "applied"
    assert dashboard.records[0].recommended_action == "no_immediate_action"


def test_dashboard_reference_docs_are_optional(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    reports_dir = tmp_path / "coordination" / "reports"
    reports_dir.mkdir(parents=True)
    (reports_dir / "report.md").write_text("# Report\n\nContent.\n", encoding="utf-8")

    without_reference = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
        include_reference=False,
    )

    with_reference = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
        include_reference=True,
    )

    assert without_reference.document_count == 0
    assert with_reference.document_count == 1


def test_dashboard_renders_no_color_table(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    (global_dir / "policy.md").write_text("# Policy\n\nContent.\n", encoding="utf-8")

    dashboard = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )

    rendered = render_dashboard(
        dashboard,
        no_color=True,
        show_all=False,
        limit=40,
    )

    assert "Coordination Document Awareness — forprint_library" in rendered
    assert "Area Summary" in rendered
    assert "Attention Required" in rendered
    assert "coordination/global_policy/policy.md" in rendered
