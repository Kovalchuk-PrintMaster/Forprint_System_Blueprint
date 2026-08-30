import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_specialized_index_validator_passes() -> None:
    result = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/validate_blueprint_specialized_indexes.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "BLUEPRINT_SPECIALIZED_INDEX_VALIDATION=PASS" in result.stdout


def test_operations_prompt_queue_identity_is_split_cleanly() -> None:
    data = _load(ROOT / "indexes/prompts.yaml")
    queues = {item["module_id"]: item for item in data["queues"]}

    assert queues["forprint_operations_control_registry"]["identity_state"] == (
        "canonical"
    )
    assert queues["forprint_operations_control_registry"]["authority_state"] == (
        "current_queue_surface"
    )
    assert queues["forprint_operational_registry"]["identity_state"] == (
        "historical_alias"
    )
    assert queues["forprint_operational_registry"]["authority_state"] == (
        "historical_non_authoritative"
    )


def test_blueprint_self_coordination_projections_are_not_effective_roadmap_authority() -> None:
    data = _load(ROOT / "indexes/roadmaps.yaml")

    assert data["effective_release_authority"] == (
        "coordination/releases/current.yaml"
    )
    assert "coordination/self_coordination/roadmap.yaml" in (
        data["historical_non_authoritative_projections"]
    )


def test_governance_index_projects_current_release() -> None:
    data = _load(ROOT / "indexes/governance.yaml")
    release = data["effective_release"]

    assert release["path"] == "coordination/releases/current.yaml"
    assert release["release_status"] == "authoritative_current"


def test_source_coverage_has_no_unknown_registry_ids() -> None:
    data = _load(ROOT / "indexes/source_coverage.yaml")
    assert data["unknown_specialized_registry_ids"] == []


def test_tracking_events_preflight_uses_immutable_source_snapshot() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    snapshot = (
        "coordination/prompt_contracts/logistics_service/"
        "logistics_service_tracking_events_v0_1/source_prompt_snapshot.md"
    )

    assert f"TRACKING_EVENTS_SOURCE_PROMPT ?= {snapshot}" in makefile
    assert (ROOT / snapshot).is_file()


def test_contract_index_contains_machine_and_prompt_contracts() -> None:
    data = _load(ROOT / "indexes/contracts.yaml")
    assert data["machine_contract_count"] > 0
    assert data["prompt_contract_package_count"] > 0
def test_incoming_request_routes_cover_all_canonical_modules() -> None:
    data = _load(ROOT / "indexes/incoming_requests.yaml")
    routes = data["current_routes"]
    identity = _load(ROOT / "machine/module_identity_registry.yaml")

    assert {item["module_id"] for item in routes} == set(
        identity["canonical_module_ids"]
    )
    assert all(item["present"] is True for item in routes)
    assert all(item["new_present"] is True for item in routes)
    assert all(item["reviewed_present"] is True for item in routes)
    assert all(item["archived_present"] is True for item in routes)
    assert all(
        item["authority_state"] == "current_canonical_route"
        for item in routes
    )


def test_legacy_incoming_request_aliases_are_history_only() -> None:
    data = _load(ROOT / "indexes/incoming_requests.yaml")
    aliases = {
        item["alias"]: item
        for item in data["historical_alias_routes"]
    }

    assert aliases["accounting_registry_service"]["canonical_id"] == (
        "forprint_accounting_registry_service"
    )
    assert aliases["forprint_operational_registry"]["canonical_id"] == (
        "forprint_operations_control_registry"
    )
    assert all(
        item["authority_state"] == "historical_alias_route"
        for item in aliases.values()
    )
    assert all(item["current_use_allowed"] is False for item in aliases.values())
    assert data["unknown_directory_ids"] == []


def test_prompt_reporting_standard_uses_current_review_packet_surface() -> None:
    path = (
        ROOT
        / "coordination/standards/governance/"
        "module_prompt_execution_and_reporting_protocol.md"
    )
    text = path.read_text(encoding="utf-8")

    assert "coordination/incoming_reports/" not in text
    assert "coordination/review_packets/<module_id>/processed/" in text

    fence_count = sum(
        1
        for line in text.splitlines()
        if line.strip().startswith("```")
    )
    assert fence_count % 2 == 0


def test_specialized_navigation_indexes_structural_document_roots() -> None:
    roadmaps = _load(ROOT / "indexes/roadmaps.yaml")
    governance = _load(ROOT / "indexes/governance.yaml")
    coverage = _load(ROOT / "indexes/source_coverage.yaml")

    assert roadmaps["blueprint_detail_document_count"] > 0
    assert governance["coordination_template_document_count"] > 0
    assert any(
        item["module_policy_documents"]
        for item in coverage["modules"]
    )
