from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
STANDARDS_INDEX = ROOT / "coordination/standards/index.yaml"
POLICY = ROOT / "coordination/standards/governance/coordination_health_policy_v0_1.yaml"
STANDARD = ROOT / "coordination/standards/governance/closed_loop_coordination_lifecycle_v0_1.md"
PUBLICATION = (
    ROOT
    / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_reconciliation_publication_verification_v0_1.yaml"
)
IMPLEMENTATION = (
    ROOT
    / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_closed_loop_lifecycle_standard_implementation_v0_1.yaml"
)
ACCEPTANCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_closed_loop_lifecycle_standard_acceptance_v0_1.yaml"
)

LIFECYCLE_ID = "blueprint_v0_4_closed_loop_lifecycle_standard_v0_1"
NEXT_ID = "blueprint_v0_4_coordination_source_registry_v0_1"
PROMPT_CONTRACT_ID = "blueprint_v0_4_immutable_prompt_contract_v0_1"
COMPLETION_PACKET_ID = "blueprint_v0_4_completion_packet_v0_1"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def record(items: list[dict], key: str, value: str) -> dict:
    return next(item for item in items if item[key] == value)


def test_lifecycle_step_is_explicitly_accepted_and_next_step_active() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)

    lifecycle = record(roadmap["steps"], "step_id", LIFECYCLE_ID)
    source_registry = record(roadmap["steps"], "step_id", NEXT_ID)
    health_step = record(
        roadmap["steps"],
        "step_id", "blueprint_v0_4_coordination_health_and_pulse_v0_1"
    )
    lifecycle_prompt = record(queue["prompts"], "prompt_id", LIFECYCLE_ID)
    source_registry_prompt = record(queue["prompts"], "prompt_id", NEXT_ID)
    health_prompt = record(
        queue["prompts"],
        "prompt_id", "blueprint_v0_4_coordination_health_and_pulse_v0_1"
    )

    assert lifecycle["status"] == "completed"
    assert lifecycle["operator_decision"] == "ACCEPT"
    assert lifecycle_prompt["status"] == "completed"

    assert source_registry["status"] == "completed"
    assert source_registry_prompt["status"] == "completed"
    assert source_registry_prompt["execution_status"] == "accepted"

    assert health_step["status"] == "completed"
    assert health_step["operator_decision"] == "ACCEPT"
    assert health_prompt["status"] == "completed"
    assert health_prompt["execution_status"] == "accepted"

def test_standard_is_no_longer_draft_reference_only() -> None:
    index = load(STANDARDS_INDEX)
    matches = [
        item
        for item in index["standards"]
        if item.get("standard_id") == "closed_loop_coordination_lifecycle_v0_1"
    ]
    assert len(matches) == 1
    assert matches[0]["status"] != "draft"
    assert matches[0]["adoption_mode"] != "reference_only"

    text = STANDARD.read_text(encoding="utf-8")
    assert "Status: accepted by explicit operator decision" in text


def test_acceptance_evidence_records_only_explicit_operator_accept() -> None:
    evidence = load(ACCEPTANCE)
    assert evidence["result"] == "ACCEPTED"
    assert evidence["decision"]["operator_decision"] == "ACCEPT"
    assert evidence["decision"]["explicit_instruction"] == "ACCEPT STEP18"
    assert evidence["decision"]["automatic_acceptance"] is False
    assert evidence["decision"]["automatic_return"] is False
    assert evidence["applied_effects"]["accepted_roadmap_step"] == LIFECYCLE_ID
    assert evidence["applied_effects"]["next_roadmap_step_activated"] == NEXT_ID


def test_implementation_and_publication_evidence_remain_separate() -> None:
    implementation = load(IMPLEMENTATION)
    publication = load(PUBLICATION)

    assert implementation["result"] == "READY_FOR_OPERATOR_REVIEW"
    assert implementation["work"]["operator_decision_created"] is False
    assert implementation["work"]["operator_acceptance_created"] is False

    assert publication["result"] == "PUBLICATION_VERIFIED"
    assert publication["verification"]["remote_containment_verified"] is True


def test_prompt_buffer_health_is_recalculated_after_next_activation() -> None:
    queue = load(QUEUE)
    handoff = load(HANDOFF)
    policy = load(POLICY)["prompt_buffer"]

    dispatchable = [
        item
        for item in queue["prompts"]
        if item.get("status") == "draft"
        and item.get("dispatch_ready") is True
        and item.get("execution_status") != "deferred"
    ]

    count = len(dispatchable)
    minimum = policy["minimum_dispatchable_drafts"]
    target = policy["target_dispatchable_drafts"]
    health = handoff["self_coordination_health"]

    assert count >= minimum
    assert health["dispatchable_draft_prompts"] == count

    if count >= target:
        assert health["prompt_buffer_state"] == "target_met"
        assert "PROMPT_BUFFER_BELOW_TARGET" not in health["advisories"]
    else:
        assert health["prompt_buffer_state"] == "minimum_met_target_not_met"
        assert "PROMPT_BUFFER_BELOW_TARGET" in health["advisories"]

    assert health["blocking_errors"] == []


def test_prompt_contract_is_active_after_step20_acceptance() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    item = record(queue["prompts"], "prompt_id", PROMPT_CONTRACT_ID)
    step = record(roadmap["steps"], "step_id", PROMPT_CONTRACT_ID)
    if step["status"] == "active":
        assert roadmap["metadata"]["current_step_id"] == PROMPT_CONTRACT_ID
        assert queue["metadata"]["active_prompt_id"] == PROMPT_CONTRACT_ID
        assert item["status"] == "approved"
        assert item["execution_status"] == "ready_for_module_pull"
        assert "/prompt_queue/approved/" in item["path"]
    else:
        assert step["status"] == "completed"
        assert step["operator_decision"] == "ACCEPT"
        assert roadmap["metadata"]["current_step_id"] == COMPLETION_PACKET_ID
        assert queue["metadata"]["active_prompt_id"] == COMPLETION_PACKET_ID
        assert item["status"] == "completed"
        assert item["execution_status"] == "accepted"
        assert item["operator_decision"] == "ACCEPT"
        assert "/prompt_queue/completed/" in item["path"]

    assert (ROOT / item["path"]).is_file()


def test_handoff_reports_source_registry_as_active_after_accept() -> None:
    handoff = load(HANDOFF)
    plan = handoff["current_blueprint_plan"]

    active_id = plan["active_blueprint_step"]["id"]
    assert active_id in {PROMPT_CONTRACT_ID, COMPLETION_PACKET_ID}
    if active_id == COMPLETION_PACKET_ID:
        contract_state = handoff["prompt_contract_v0_4"]
        assert contract_state["operator_decision_created"] is True
        assert contract_state["operator_decision"] == "ACCEPT"
        assert contract_state["promotion_performed"] is False
    registry = handoff["coordination_source_registry"]
    assert registry["operator_decision_created"] is True
    assert registry["operator_decision"] == "ACCEPT"
    assert registry["status"] == "candidate_v0_4"
    assert registry["global_v0_4_promotion_performed"] is False

def test_completed_means_accepted_not_merely_reviewed() -> None:
    queue = load(QUEUE)
    lifecycle = record(queue["prompts"], "prompt_id", LIFECYCLE_ID)

    assert lifecycle["status"] == "completed"
    assert lifecycle["execution_status"] == "accepted"
    assert lifecycle["operator_decision"] == "ACCEPT"
    assert (ROOT / lifecycle["path"]).is_file()
