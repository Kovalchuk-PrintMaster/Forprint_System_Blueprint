from __future__ import annotations

import json
from pathlib import Path

from scripts.coordination.build_document_manifest import (
    build_manifest,
    manifest_to_dict,
    render_markdown,
    write_manifest_reports,
)


def _write_source_registry(root: Path) -> Path:
    registry_dir = root / "coordination" / "document_awareness"
    registry_dir.mkdir(parents=True)

    registry_path = registry_dir / "source_registry.yaml"
    registry_path.write_text(
        """schema_version: coordination_document_source_registry_v0_1

sources:
  - source_id: standards
    path: coordination/standards
    priority: high
    applies_to: all
    action: review_before_next_prompt
    include_patterns:
      - "*.md"
      - "*.yaml"
      - "*.yml"
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
""",
        encoding="utf-8",
    )

    return registry_path


def test_document_manifest_builds_records_with_hashes(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    standards_dir = tmp_path / "coordination" / "standards" / "governance"
    standards_dir.mkdir(parents=True)
    (standards_dir / "example_policy.md").write_text(
        "# Example Policy\n\nContent.\n",
        encoding="utf-8",
    )
    (standards_dir / ".gitkeep").write_text("", encoding="utf-8")

    module_policy_dir = tmp_path / "coordination" / "module_policy" / "forprint_library"
    module_policy_dir.mkdir(parents=True)
    (module_policy_dir / "module_policy.md").write_text(
        "# Module Policy\n\nLibrary policy.\n",
        encoding="utf-8",
    )

    manifest = build_manifest(tmp_path, registry_path)

    assert manifest.document_count == 2
    assert manifest.warning_count == 0

    records = {document.document_id: document for document in manifest.documents}

    assert "standards.governance.example_policy" in records
    assert "module_policy.forprint_library.module_policy" in records

    policy_record = records["standards.governance.example_policy"]
    assert policy_record.title == "Example Policy"
    assert policy_record.priority == "high"
    assert policy_record.content_hash.startswith("sha256:")


def test_document_manifest_hash_changes_when_content_changes(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    standards_dir = tmp_path / "coordination" / "standards"
    standards_dir.mkdir(parents=True)
    document_path = standards_dir / "policy.md"

    document_path.write_text("# Policy\n\nFirst version.\n", encoding="utf-8")
    first_manifest = build_manifest(tmp_path, registry_path)
    first_hash = first_manifest.documents[0].content_hash

    document_path.write_text("# Policy\n\nSecond version.\n", encoding="utf-8")
    second_manifest = build_manifest(tmp_path, registry_path)
    second_hash = second_manifest.documents[0].content_hash

    assert first_hash != second_hash


def test_document_manifest_reports_missing_sources_as_warnings(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    manifest = build_manifest(tmp_path, registry_path)

    assert manifest.document_count == 0
    assert manifest.warning_count == 2
    assert all("source path does not exist" in warning for warning in manifest.warnings)


def test_document_manifest_can_render_markdown_and_json(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    standards_dir = tmp_path / "coordination" / "standards"
    standards_dir.mkdir(parents=True)
    (standards_dir / "policy.md").write_text("# Policy\n\nContent.\n", encoding="utf-8")

    manifest = build_manifest(tmp_path, registry_path)

    data = manifest_to_dict(manifest)
    markdown = render_markdown(manifest)

    assert data["schema_version"] == "coordination_document_manifest_v0_1"
    assert data["document_count"] == 1
    assert "# Coordination Document Manifest" in markdown
    assert "coordination/standards/policy.md" in markdown


def test_document_manifest_writes_json_and_markdown_reports(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    standards_dir = tmp_path / "coordination" / "standards"
    standards_dir.mkdir(parents=True)
    (standards_dir / "policy.md").write_text("# Policy\n\nContent.\n", encoding="utf-8")

    manifest = build_manifest(tmp_path, registry_path)
    json_path, markdown_path = write_manifest_reports(
        manifest,
        tmp_path / "reports" / "coordination_awareness",
    )

    assert json_path.exists()
    assert markdown_path.exists()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["document_count"] == 1
