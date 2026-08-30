import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_knowledge_index_validator_passes() -> None:
    result = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/validate_blueprint_knowledge_index.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BLUEPRINT_KNOWLEDGE_INDEX_VALIDATION=PASS" in result.stdout


def test_file_index_excludes_derived_and_volatile_roots() -> None:
    data = json.loads(
        (ROOT / "indexes/files.json").read_text(encoding="utf-8")
    )
    paths = {item["path"] for item in data["files"]}

    assert "tmp.py" not in paths
    assert not any(path.startswith("indexes/") for path in paths)
    assert not any(path.startswith("tmp/") for path in paths)
    assert not any(path.startswith("reports/") for path in paths)


def test_module_dependency_endpoints_are_known() -> None:
    data = json.loads(
        (ROOT / "indexes/dependencies.json").read_text(encoding="utf-8")
    )
    assert data["unknown_module_endpoints"] == []
    assert data["module_dependencies"]


def test_reference_review_queue_is_non_authoritative() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/review_candidates.yaml").read_text(encoding="utf-8")
    )
    assert data["status"] == "derived_non_authoritative"
    assert "nonblocking context" in data["semantics"]


def test_repository_knowledge_duplicate_pairs_are_classified_as_derived() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/review_candidates.yaml").read_text(encoding="utf-8")
    )
    groups = data["exact_duplicate_groups"]
    derived = [
        item
        for item in groups
        if item["classification"] == "declared_source_derived_pair"
    ]
    assert len(derived) == 6


def test_internal_work_is_not_reported_as_current_no_inbound_document() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/review_candidates.yaml").read_text(encoding="utf-8")
    )
    paths = {
        item["path"]
        for item in data["no_inbound_current_documents"]
    }
    assert not any(
        path.startswith("coordination/internal_work/")
        for path in paths
    )


def test_intentional_prompt_snapshots_are_not_harmful_duplicates() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/review_candidates.yaml").read_text(encoding="utf-8")
    )
    assert data["harmful_duplicate_candidates"] == []

    groups = data["exact_duplicate_groups"]
    snapshots = [
        item
        for item in groups
        if item["classification"] == "immutable_prompt_source_snapshot"
    ]
    assert snapshots


def test_scope_aware_reference_classes_are_emitted() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/knowledge_summary.yaml").read_text(encoding="utf-8")
    )
    classes = data["reference_classifications"]

    assert classes.get("external_module_coordination_reference", 0) > 0
    assert classes.get("target_module_relative_reference", 0) > 0
    assert classes.get("historical_or_internal_evidence_reference", 0) > 0


def test_root_index_registers_knowledge_surfaces() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/index.yaml").read_text(encoding="utf-8")
    )
    ids = {item["id"] for item in data["indexes"]}

    assert {
        "files",
        "document_catalog",
        "references",
        "dependencies",
        "review_candidates",
        "knowledge_summary",
    } <= ids
def test_actionable_reference_queue_is_empty_after_final_triage() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/review_candidates.yaml").read_text(encoding="utf-8")
    )
    assert data["unresolved_current_reference_candidates"] == []
    assert data["no_inbound_current_documents"] == []


def test_structurally_discoverable_no_inbound_docs_remain_visible() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/review_candidates.yaml").read_text(encoding="utf-8")
    )
    structural = data["structurally_discoverable_no_inbound_documents"]
    assert structural

    reasons = {item["discoverability"] for item in structural}
    assert "standards_governance_index" in reasons
    assert "blueprint_roadmap_detail_tree" in reasons
    assert "coordination_template_root" in reasons
    assert "module_policy_tree" in reasons
    assert "document_catalog" in reasons


def test_final_reference_classes_cover_reviewed_semantics() -> None:
    data = yaml.safe_load(
        (ROOT / "indexes/knowledge_summary.yaml").read_text(encoding="utf-8")
    )
    classes = data["reference_classifications"]

    for expected in (
        "conceptual_nonpath_reference",
        "incoming_request_module_evidence_reference",
        "target_module_completion_evidence_reference",
        "declared_registry_availability_reference",
        "resolved_structured_pointer",
        "resolved_pytest_nodeid",
        "blueprint_roadmap_planning_reference",
        "indexer_rule_literal_reference",
    ):
        assert classes.get(expected, 0) > 0
