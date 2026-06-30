from __future__ import annotations

from pathlib import Path

from scripts.coordination.build_context_bundle import (
    build_context_bundle,
    select_bundle_records,
    write_context_bundle,
)
from scripts.coordination.render_document_awareness_dashboard import build_dashboard


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
    exclude_patterns:
      - ".gitkeep"

  - source_id: standards
    path: coordination/standards
    priority: high
    applies_to: all
    action: review_before_next_prompt
    include_patterns:
      - "*.md"
    exclude_patterns:
      - ".gitkeep"

  - source_id: templates
    path: coordination/templates
    priority: normal
    applies_to: all
    action: review_when_relevant
    include_patterns:
      - "*.md"
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


def test_context_bundle_bootstrap_includes_critical_and_high_docs(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    (global_dir / "policy.md").write_text("# Global Policy\n\nGlobal content.\n", encoding="utf-8")

    standards_dir = tmp_path / "coordination" / "standards"
    standards_dir.mkdir(parents=True)
    (standards_dir / "standard.md").write_text("# Standard\n\nStandard content.\n", encoding="utf-8")

    templates_dir = tmp_path / "coordination" / "templates"
    templates_dir.mkdir(parents=True)
    (templates_dir / "template.md").write_text("# Template\n\nTemplate content.\n", encoding="utf-8")

    module_dir = tmp_path / "coordination" / "module_policy" / "forprint_library"
    module_dir.mkdir(parents=True)
    (module_dir / "module_policy.md").write_text(
        "# Module Policy\n\nModule content.\n",
        encoding="utf-8",
    )

    bundle = build_context_bundle(
        root=tmp_path,
        module="forprint_library",
        scope="bootstrap",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )

    assert bundle.document_count == 3
    assert "coordination/global_policy/policy.md" in bundle.content
    assert "coordination/standards/standard.md" in bundle.content
    assert "coordination/module_policy/forprint_library/module_policy.md" in bundle.content
    assert "coordination/templates/template.md" not in bundle.content


def test_context_bundle_changed_scope_uses_attention_statuses(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    (global_dir / "policy.md").write_text("# Global Policy\n\nGlobal content.\n", encoding="utf-8")

    dashboard = build_dashboard(
        root=tmp_path,
        module="forprint_library",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )

    selected = select_bundle_records(
        dashboard.records,
        scope="changed",
        module="forprint_library",
    )

    assert len(selected) == 1
    assert selected[0].awareness_status == "unseen"


def test_context_bundle_module_scope_filters_module_specific_docs(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    (global_dir / "policy.md").write_text("# Global Policy\n\nGlobal content.\n", encoding="utf-8")

    module_dir = tmp_path / "coordination" / "module_policy" / "forprint_library"
    module_dir.mkdir(parents=True)
    (module_dir / "module_policy.md").write_text(
        "# Module Policy\n\nModule content.\n",
        encoding="utf-8",
    )

    other_module_dir = tmp_path / "coordination" / "module_policy" / "forprint_crm"
    other_module_dir.mkdir(parents=True)
    (other_module_dir / "module_policy.md").write_text(
        "# CRM Policy\n\nCRM content.\n",
        encoding="utf-8",
    )

    bundle = build_context_bundle(
        root=tmp_path,
        module="forprint_library",
        scope="module",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )

    assert bundle.document_count == 1
    assert "forprint_library" in bundle.content
    assert "forprint_crm" not in bundle.content
    assert "coordination/global_policy/policy.md" not in bundle.content


def test_context_bundle_can_limit_documents(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    standards_dir = tmp_path / "coordination" / "standards"
    standards_dir.mkdir(parents=True)

    for index in range(3):
        (standards_dir / f"standard_{index}.md").write_text(
            f"# Standard {index}\n\nContent.\n",
            encoding="utf-8",
        )

    bundle = build_context_bundle(
        root=tmp_path,
        module="forprint_library",
        scope="high",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
        limit=2,
    )

    assert bundle.document_count == 2


def test_context_bundle_writes_markdown_file(tmp_path: Path) -> None:
    registry_path = _write_source_registry(tmp_path)

    global_dir = tmp_path / "coordination" / "global_policy"
    global_dir.mkdir(parents=True)
    (global_dir / "policy.md").write_text("# Global Policy\n\nGlobal content.\n", encoding="utf-8")

    bundle = build_context_bundle(
        root=tmp_path,
        module="forprint_library",
        scope="critical",
        registry_path=registry_path,
        ledger_path=tmp_path / "missing_ledger.yaml",
    )

    output_path = write_context_bundle(
        root=tmp_path,
        bundle=bundle,
        output_dir=tmp_path / "reports" / "coordination_context_bundles",
    )

    assert output_path.exists()
    assert output_path.suffix == ".md"
    assert "Coordination Context Bundle" in output_path.read_text(encoding="utf-8")
