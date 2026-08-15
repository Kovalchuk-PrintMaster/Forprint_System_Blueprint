from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/registry/coordination_source_registry_v0_1.yaml"
VALIDATOR = ROOT / "scripts/coordination/validate_coordination_source_registry.py"
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
BOOTSTRAP = ROOT / "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml"
IMPLEMENTATION = (
    ROOT
    / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_coordination_source_registry_implementation_v0_1.yaml"
)
PUBLICATION = (
    ROOT
    / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_lifecycle_standard_publication_verification_v0_1.yaml"
)

ACTIVE_ID = "blueprint_v0_4_coordination_source_registry_v0_1"
BUFFER_ID = "blueprint_v0_4_completion_packet_v0_1"
EXPECTED_IDS = {
    "forprint_accounting_registry_service",
    "forprint_integration_gateway",
    "forprint_library",
    "logistics_service",
    "forprint_operational_registry",
    "forprint_system_blueprint",
    "website",
    "telegram_bot",
}


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def mod(data: dict, mid: str) -> dict:
    return next(x for x in data["modules"] if x["module_id"] == mid)


def validator_module():
    spec = importlib.util.spec_from_file_location("registry_validator", VALIDATOR)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_source_registry_and_health_steps_are_accepted_before_prompt_contract() -> None:
    roadmap, queue, handoff = load(ROADMAP), load(QUEUE), load(HANDOFF)
    prompt_contract = "blueprint_v0_4_immutable_prompt_contract_v0_1"
    completion_packet = "blueprint_v0_4_completion_packet_v0_1"
    active_id = roadmap["metadata"]["current_step_id"]
    assert active_id in {prompt_contract, completion_packet}
    assert queue["metadata"]["active_prompt_id"] == active_id
    assert handoff["current_blueprint_plan"]["active_blueprint_step"]["id"] == active_id

    step19 = next(x for x in roadmap["steps"] if x["step_id"] == ACTIVE_ID)
    prompt19 = next(x for x in queue["prompts"] if x["prompt_id"] == ACTIVE_ID)
    step20 = next(
        x
        for x in roadmap["steps"]
        if x["step_id"] == "blueprint_v0_4_coordination_health_and_pulse_v0_1"
    )
    prompt20 = next(
        x
        for x in queue["prompts"]
        if x["prompt_id"] == "blueprint_v0_4_coordination_health_and_pulse_v0_1"
    )
    step21 = next(x for x in roadmap["steps"] if x["step_id"] == prompt_contract)
    prompt21 = next(x for x in queue["prompts"] if x["prompt_id"] == prompt_contract)

    assert step19["status"] == "completed"
    assert prompt19["status"] == "completed"
    assert prompt19["execution_status"] == "accepted"
    assert step20["status"] == "completed"
    assert step20["operator_decision"] == "ACCEPT"
    assert prompt20["status"] == "completed"
    assert prompt20["execution_status"] == "accepted"
    if active_id == prompt_contract:
        assert step21["status"] == "active"
        assert prompt21["status"] == "approved"
        assert prompt21["execution_status"] == "ready_for_module_pull"
    else:
        assert step21["status"] == "completed"
        assert step21["operator_decision"] == "ACCEPT"
        assert prompt21["status"] == "completed"
        assert prompt21["execution_status"] == "accepted"
        assert prompt21["operator_decision"] == "ACCEPT"
        step22 = next(x for x in roadmap["steps"] if x["step_id"] == completion_packet)
        prompt22 = next(x for x in queue["prompts"] if x["prompt_id"] == completion_packet)
        assert step22["status"] == "active"
        assert prompt22["status"] == "approved"
        assert prompt22["execution_status"] == "ready_for_module_pull"

def test_registry_exact_source_set_and_identity_separation() -> None:
    data = load(REGISTRY)
    assert data["schema_version"] == "coordination_source_registry_v0_1"
    assert {x["module_id"] for x in data["modules"]} == EXPECTED_IDS
    assert (
        mod(data, "logistics_service")["repository"]["repository_id"]
        == "forprint_logistics_service"
    )
    assert mod(data, "website")["repository"]["repository_id"] == "forprint_website"
    assert data["lookup_policy"]["module_id_is_repository_name"] is False


def test_self_lookup_paths_are_present() -> None:
    entry = mod(load(REGISTRY), "forprint_system_blueprint")
    assert entry["sources"]["roadmap"]["path"] == "coordination/self_coordination/roadmap.yaml"
    assert entry["sources"]["roadmap"]["availability"] == "present"
    assert (
        entry["sources"]["prompt_queue"]["path"]
        == "coordination/self_coordination/prompt_queue/index.yaml"
    )
    assert entry["sources"]["prompt_queue"]["availability"] == "present"


def test_outbox_future_path_is_registered_without_fabrication() -> None:
    data = load(REGISTRY)
    for item in data["modules"]:
        outbox = item["sources"]["completion_outbox"]
        assert outbox["owner"] == item["module_id"]
        assert outbox["path"] == "coordination/completion_outbox/records"
        assert outbox["availability"] == "not_present_yet"


def test_module_repositories_are_read_only_from_blueprint() -> None:
    data = load(REGISTRY)
    for item in data["modules"]:
        assert item["boundaries"]["blueprint_lookup_mode"] == "read_only"
        assert item["boundaries"]["blueprint_may_write_repository"] is (
            item["module_id"] == "forprint_system_blueprint"
        )


def test_validator_passes() -> None:
    assert validator_module().validate(REGISTRY) == []


def test_bootstrap_handoff_registry_pointers() -> None:
    bootstrap, handoff = load(BOOTSTRAP), load(HANDOFF)
    path = "coordination/registry/coordination_source_registry_v0_1.yaml"
    assert bootstrap["source_of_truth_map"]["coordination_source_registry"] == path
    assert handoff["coordination_source_registry"]["path"] == path
    assert handoff["coordination_source_registry"]["status"] == "candidate_v0_4"
    assert handoff["coordination_source_registry"]["operator_decision_created"] is True
    assert handoff["coordination_source_registry"]["operator_decision"] == "ACCEPT"

def test_prompt_buffer_restored_to_target_with_completion_packet_draft() -> None:
    queue, handoff = load(QUEUE), load(HANDOFF)
    drafts = [
        x
        for x in queue["prompts"]
        if x.get("status") == "draft"
        and x.get("dispatch_ready") is True
        and x.get("execution_status") != "deferred"
    ]
    assert len(drafts) == 3
    assert queue["metadata"]["dispatchable_draft_count"] == 3
    assert handoff["self_coordination_health"]["prompt_buffer_state"] == "target_met"
    draft_ids = {x["prompt_id"] for x in drafts}
    if BUFFER_ID in draft_ids:
        item = next(x for x in drafts if x["prompt_id"] == BUFFER_ID)
        assert item["execution_status"] == "planned"
        assert (ROOT / item["path"]).is_file()
    else:
        assert draft_ids == {
            "blueprint_v0_4_completion_outbox_v0_1",
            "blueprint_v0_4_completion_discovery_and_intake_v0_1",
            "blueprint_v0_4_review_roadmap_queue_transaction_v0_1",
        }
        for item in drafts:
            assert item["execution_status"] == "planned"
            assert (ROOT / item["path"]).is_file()


def test_evidence_separates_publication_implementation_and_acceptance() -> None:
    implementation, publication = load(IMPLEMENTATION), load(PUBLICATION)
    assert implementation["result"] in {
        "IMPLEMENTATION_IN_PROGRESS",
        "READY_FOR_OPERATOR_REVIEW",
    }
    assert implementation["validation"]["state"] in {"pending", "passed"}
    assert implementation["work"]["operator_decision_created"] is False
    assert implementation["boundaries"]["module_repository_writes"] is False
    assert implementation["boundaries"]["automatic_acceptance"] is False
    assert publication["result"] == "PUBLICATION_VERIFIED"


def test_explicit_step19_acceptance_is_recorded_without_global_v04_promotion() -> None:
    acceptance = load(
        ROOT
        / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_coordination_source_registry_acceptance_v0_1.yaml"
    )
    registry = load(REGISTRY)
    assert acceptance["operator_decision"]["decision"] == "ACCEPT"
    assert acceptance["operator_decision"]["explicit"] is True
    assert acceptance["boundaries"]["global_v0_4_promotion_performed"] is False
    assert acceptance["boundaries"]["module_repository_writes"] is False
    assert acceptance["result"] in {"ACCEPTANCE_IN_PROGRESS", "ACCEPTED"}
    assert registry["metadata"]["status"] == "candidate_v0_4"
