from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
POLICY = ROOT / "coordination/standards/governance/coordination_health_policy_v0_1.yaml"
ACCEPTANCE = ROOT / "coordination/internal_work/blueprint/governance/2026-08-14__blueprint__v0_4_closed_loop_reconciliation_acceptance_v0_1.yaml"

ACCEPTED_ID = "blueprint_v0_4_closed_loop_baseline_and_roadmap_reconciliation_v0_1"
ACTIVE_ID = "blueprint_v0_4_closed_loop_lifecycle_standard_v0_1"
OLD_INVENTORY_ID = "blueprint_inventory_acceptance_packet_integrity_gate_v0_1"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_reconciliation_is_accepted_and_lifecycle_standard_is_current() -> None:
    roadmap = load(ROADMAP)
    assert roadmap["metadata"]["current_step_id"] == ACTIVE_ID
    steps = roadmap["steps"]
    accepted = next(item for item in steps if item["step_id"] == ACCEPTED_ID)
    active = next(item for item in steps if item["step_id"] == ACTIVE_ID)
    assert accepted["status"] == "completed"
    assert accepted["operator_decision"] == "ACCEPT"
    assert accepted["completed_at"] == "2026-08-14"
    assert active["status"] == "active"
    assert active["depends_on"] == [ACCEPTED_ID]


def test_roadmap_horizon_remains_healthy_after_acceptance() -> None:
    roadmap = load(ROADMAP)
    policy = load(POLICY)["roadmap"]
    steps = roadmap["steps"]
    current = next(item for item in steps if item["step_id"] == ACTIVE_ID)
    future = [
        item for item in steps
        if item["sequence"] > current["sequence"]
        and item["status"] in {"active", "planned", "ready"}
    ]
    assert len(future) == 11
    assert len(future) >= policy["target_future_steps"]
    assert policy["minimum_future_steps"] == 5
    assert policy["target_future_steps"] == 8
    assert policy["maximum_future_steps"] is None


def test_old_inventory_chain_remains_deferred_not_completed() -> None:
    roadmap = load(ROADMAP)
    assert all(item.get("step_id") != OLD_INVENTORY_ID for item in roadmap["steps"])
    old = next(
        item for item in roadmap["deferred_steps"]
        if item.get("step_id") == OLD_INVENTORY_ID
    )
    assert old["status"] == "deferred"
    assert old["release_after"] == "blueprint_v0_4_promotion_decision_v0_1"


def test_queue_archives_accepted_prompt_and_activates_next_prompt() -> None:
    queue = load(QUEUE)
    by_id = {item["prompt_id"]: item for item in queue["prompts"]}
    assert queue["metadata"]["active_prompt_id"] == ACTIVE_ID

    accepted = by_id[ACCEPTED_ID]
    assert accepted["status"] == "completed"
    assert accepted["execution_status"] == "accepted"
    assert accepted["dispatch_ready"] is False
    assert accepted["operator_decision"] == "ACCEPT"
    assert "/prompt_queue/completed/" in accepted["path"]

    active = by_id[ACTIVE_ID]
    assert active["status"] == "approved"
    assert active["execution_status"] == "ready_for_module_pull"
    assert active["dispatch_ready"] is True
    assert "/prompt_queue/approved/" in active["path"]

    approved = [item for item in queue["prompts"] if item.get("status") == "approved"]
    assert [item["prompt_id"] for item in approved] == [ACTIVE_ID]


def test_prompt_buffer_meets_minimum_but_is_below_target_advisory() -> None:
    queue = load(QUEUE)
    policy = load(POLICY)["prompt_buffer"]
    dispatchable = [
        item for item in queue["prompts"]
        if item.get("status") == "draft"
        and item.get("dispatch_ready") is True
        and item.get("execution_status") != "deferred"
    ]
    assert len(dispatchable) == 2
    assert len(dispatchable) >= policy["minimum_dispatchable_drafts"]
    assert len(dispatchable) < policy["target_dispatchable_drafts"]


def test_physical_prompt_lifecycle_matches_queue_after_accept() -> None:
    queue = load(QUEUE)
    by_id = {item["prompt_id"]: item for item in queue["prompts"]}
    for prompt_id in (ACCEPTED_ID, ACTIVE_ID):
        path = ROOT / by_id[prompt_id]["path"]
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        closing = text.find("\n---\n", 4)
        assert closing > 0
        frontmatter = yaml.safe_load(text[4:closing])
        assert frontmatter["prompt_id"] == prompt_id
        assert frontmatter["status"] == by_id[prompt_id]["status"]

    assert "/prompt_queue/completed/" in by_id[ACCEPTED_ID]["path"]
    assert "/prompt_queue/approved/" in by_id[ACTIVE_ID]["path"]


def test_acceptance_evidence_records_explicit_operator_decision() -> None:
    decision = load(ACCEPTANCE)
    assert decision["result"] == "ACCEPTED"
    assert decision["decision"]["operator_decision"] == "ACCEPT"
    assert decision["decision"]["automatic_acceptance"] is False
    assert decision["applied_effects"]["accepted_roadmap_step"] == ACCEPTED_ID
    assert decision["applied_effects"]["next_roadmap_step_activated"] == ACTIVE_ID
    health = decision["health_after_transition"]
    assert health["future_roadmap_steps_after_current"] == 11
    assert health["dispatchable_draft_prompts"] == 2
    assert health["advisories"] == ["PROMPT_BUFFER_BELOW_TARGET"]
    assert health["blocking_errors"] == []


def test_handoff_reports_accepted_reconciliation_and_active_step18() -> None:
    handoff = load(HANDOFF)
    plan = handoff["current_blueprint_plan"]
    assert plan["active_blueprint_step"]["id"] == ACTIVE_ID
    assert plan["active_blueprint_step"]["status"] == "active"
    assert plan["reconciliation_state"] == (
        "V0_4_RECONCILIATION_ACCEPTED_LIFECYCLE_STANDARD_ACTIVE"
    )

    accepted = plan["accepted_reconciliation"]
    assert accepted["prompt_id"] == ACCEPTED_ID
    assert accepted["operator_decision"] == "ACCEPT"
    assert accepted["next_prompt_id"] == ACTIVE_ID

    health = handoff["self_coordination_health"]
    assert health["roadmap_state"] == "healthy"
    assert health["prompt_buffer_state"] == "minimum_met_target_not_met"
    assert health["advisories"] == ["PROMPT_BUFFER_BELOW_TARGET"]
    assert health["blocking_errors"] == []
    assert handoff["next_10_steps"][0]["id"] == ACTIVE_ID
