from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
POLICY = ROOT / "coordination/standards/governance/coordination_health_policy_v0_1.yaml"
MASTER = ROOT / "coordination/instruction_intake/bootstrap/2026-08-13__forprint_system_blueprint__completion_exchange_closed_loop_coordination_v0_4_master.md"

RECONCILIATION_ID = "blueprint_v0_4_closed_loop_baseline_and_roadmap_reconciliation_v0_1"
LIFECYCLE_ID = "blueprint_v0_4_closed_loop_lifecycle_standard_v0_1"
OLD_INVENTORY_ID = "blueprint_inventory_acceptance_packet_integrity_gate_v0_1"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def by_id(items: list[dict], key: str, value: str) -> dict:
    return next(item for item in items if item[key] == value)


def test_reconciliation_acceptance_remains_historical_fact() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)

    reconciliation = by_id(roadmap["steps"], "step_id", RECONCILIATION_ID)
    prompt = by_id(queue["prompts"], "prompt_id", RECONCILIATION_ID)

    assert reconciliation["status"] == "completed"
    assert reconciliation["operator_decision"] == "ACCEPT"
    assert prompt["status"] == "completed"
    assert prompt["execution_status"] == "accepted"
    assert "/prompt_queue/completed/" in prompt["path"]
    assert (ROOT / prompt["path"]).is_file()


def test_lifecycle_step_is_completed_after_explicit_accept() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)

    step = by_id(roadmap["steps"], "step_id", LIFECYCLE_ID)
    prompt = by_id(queue["prompts"], "prompt_id", LIFECYCLE_ID)

    assert step["status"] == "completed"
    assert step["operator_decision"] == "ACCEPT"
    assert prompt["status"] == "completed"
    assert prompt["execution_status"] == "accepted"
    assert "/prompt_queue/completed/" in prompt["path"]
    assert (ROOT / prompt["path"]).is_file()


def test_current_active_is_consistent_across_roadmap_queue_and_handoff() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    handoff = load(HANDOFF)

    current_id = roadmap["metadata"]["current_step_id"]
    assert queue["metadata"]["active_prompt_id"] == current_id
    assert handoff["current_blueprint_plan"]["active_blueprint_step"]["id"] == current_id
    assert handoff["next_10_steps"][0]["id"] == current_id

    step = by_id(roadmap["steps"], "step_id", current_id)
    prompt = by_id(queue["prompts"], "prompt_id", current_id)

    assert step["status"] == "active"
    assert prompt["status"] == "approved"
    assert prompt["execution_status"] == "ready_for_module_pull"
    assert "/prompt_queue/approved/" in prompt["path"]
    assert (ROOT / prompt["path"]).is_file()


def test_roadmap_horizon_is_policy_driven() -> None:
    roadmap = load(ROADMAP)
    policy = load(POLICY)["roadmap"]

    current = by_id(
        roadmap["steps"],
        "step_id",
        roadmap["metadata"]["current_step_id"],
    )
    future = [
        item
        for item in roadmap["steps"]
        if item["sequence"] > current["sequence"]
        and item["status"] in {"active", "planned", "ready"}
    ]

    assert len(future) >= policy["minimum_future_steps"]
    assert policy["target_future_steps"] == 8
    assert policy["maximum_future_steps"] is None


def test_prompt_buffer_health_matches_policy() -> None:
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


def test_old_inventory_chain_remains_deferred() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)

    old_step = by_id(roadmap["deferred_steps"], "step_id", OLD_INVENTORY_ID)
    old_prompt = by_id(queue["prompts"], "prompt_id", OLD_INVENTORY_ID)

    assert old_step["status"] == "deferred"
    assert old_step["release_after"] == "blueprint_v0_4_promotion_decision_v0_1"
    assert old_prompt["status"] == "draft"
    assert old_prompt["execution_status"] == "deferred"
    assert "/prompt_queue/draft/" in old_prompt["path"]


def test_handoff_preserves_reconciliation_history_and_bootstrap_context() -> None:
    handoff = load(HANDOFF)
    accepted = handoff["current_blueprint_plan"]["accepted_reconciliation"]

    assert accepted["prompt_id"] == RECONCILIATION_ID
    assert accepted["operator_decision"] == "ACCEPT"
    assert accepted["next_prompt_id"] == LIFECYCLE_ID

    assert handoff["current_workstream_bootstrap"]["executable_prompt"] is False
    assert MASTER.is_file()
    assert handoff["hard_boundaries"]["automatic_acceptance"] is False
    assert handoff["hard_boundaries"]["automatic_return"] is False
