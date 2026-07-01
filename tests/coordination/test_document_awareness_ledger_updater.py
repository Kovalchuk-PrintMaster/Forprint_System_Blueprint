from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination.update_document_awareness_ledger import update_ledger


def _write_registry(root: Path) -> Path:
    registry_path = root / "coordination/document_awareness/source_registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        """
schema_version: coordination_document_source_registry_v0_1
sources:
  - source_id: global_policy
    path: coordination/global_policy
    priority: critical
    applies_to: all
    action: must_review_before_work
    include_patterns:
      - "*.md"
    exclude_patterns: []
""".lstrip(),
        encoding="utf-8",
    )
    return registry_path


def test_update_ledger_marks_selected_document(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)

    document_path = tmp_path / "coordination/global_policy/policy.md"
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_text("# Policy\n\nRules.\n", encoding="utf-8")

    ledger_path = (
        tmp_path / "module/coordination/blueprint_awareness/document_review_ledger.yaml"
    )

    result = update_ledger(
        root=tmp_path,
        registry_path=registry_path,
        ledger_path=ledger_path,
        module="forprint_library",
        status="acknowledged",
        document_selectors=["global_policy.policy"],
        source_selectors=[],
        priority_selectors=[],
        all_applicable=False,
        include_reference=False,
        reviewed_at="2026-06-30T00:00:00+00:00",
        module_commit="abc123",
        notes="Reviewed during test.",
        write=True,
    )

    assert result.selected_count == 1

    data = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "module_document_awareness_ledger_v0_1"
    assert data["module"] == "forprint_library"

    reviewed_documents = data["reviewed_documents"]
    assert len(reviewed_documents) == 1

    item = reviewed_documents[0]
    assert item["document_id"] == "global_policy.policy"
    assert item["path"] == "coordination/global_policy/policy.md"
    assert item["content_hash"].startswith("sha256:")
    assert item["module_review_status"] == "acknowledged"
    assert item["reviewed_at"] == "2026-06-30T00:00:00+00:00"
    assert item["module_commit"] == "abc123"
    assert item["notes"] == "Reviewed during test."


def test_update_ledger_no_write_does_not_create_file(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)

    document_path = tmp_path / "coordination/global_policy/policy.md"
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_text("# Policy\n\nRules.\n", encoding="utf-8")

    ledger_path = (
        tmp_path / "module/coordination/blueprint_awareness/document_review_ledger.yaml"
    )

    result = update_ledger(
        root=tmp_path,
        registry_path=registry_path,
        ledger_path=ledger_path,
        module="forprint_library",
        status="acknowledged",
        document_selectors=["coordination/global_policy/policy.md"],
        source_selectors=[],
        priority_selectors=[],
        all_applicable=False,
        include_reference=False,
        reviewed_at="2026-06-30T00:00:00+00:00",
        module_commit=None,
        notes=None,
        write=False,
    )

    assert result.selected_count == 1
    assert not ledger_path.exists()


def test_update_ledger_requires_selector(tmp_path: Path) -> None:
    registry_path = _write_registry(tmp_path)

    document_path = tmp_path / "coordination/global_policy/policy.md"
    document_path.parent.mkdir(parents=True, exist_ok=True)
    document_path.write_text("# Policy\n\nRules.\n", encoding="utf-8")

    ledger_path = (
        tmp_path / "module/coordination/blueprint_awareness/document_review_ledger.yaml"
    )

    try:
        update_ledger(
            root=tmp_path,
            registry_path=registry_path,
            ledger_path=ledger_path,
            module="forprint_library",
            status="acknowledged",
            document_selectors=[],
            source_selectors=[],
            priority_selectors=[],
            all_applicable=False,
            include_reference=False,
            reviewed_at=None,
            module_commit=None,
            notes=None,
            write=False,
        )
    except ValueError as exc:
        assert "provide at least one selector" in str(exc)
    else:
        raise AssertionError("Expected selector validation failure")
