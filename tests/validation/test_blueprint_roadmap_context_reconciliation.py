from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

INVENTORY_PLAN = (
    ROOT / "coordination/internal_work/blueprint/inventory_refresh/"
    "2026-07-29__blueprint__inventory_refresh_plan_v0_1.yaml"
)
SELF_ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
PROMPT_INDEX = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
FRESHNESS_REVIEW = (
    ROOT / "coordination/internal_work/blueprint/governance/"
    "2026-08-07__blueprint__assistant_bootstrap_"
    "roadmap_freshness_review_v0_1.yaml"
)
RECONCILIATION = (
    ROOT / "coordination/internal_work/blueprint/governance/"
    "2026-08-07__blueprint__roadmap_context_reconciliation_v0_1.yaml"
)

HISTORICAL_ACTIVE_ID = "blueprint_inventory_acceptance_packet_integrity_gate_v0_1"
SUPERSEDING_RECONCILIATION_ID = (
    "blueprint_v0_4_closed_loop_baseline_and_roadmap_reconciliation_v0_1"
)
CURRENT_V04_ID = (
    "blueprint_v0_4_immutable_prompt_contract_v0_1"
)
COMPLETION_PACKET_ID = "blueprint_v0_4_completion_packet_v0_1"

PREREQUISITE_IDS = [
    "completion_intake_acceptance_governance_v0_1",
    "completion_intake_protocol_tooling_v0_1",
    "historical_acceptance_reconciliation_v0_1",
    "assistant_bootstrap_handoff_contract_v0_1",
]

EXPECTED_INVENTORY_FUTURE = [
    "blueprint_inventory_acceptance_packet_integrity_gate_v0_1",
    "blueprint_inventory_acceptance_decision_readiness_review_v0_1",
    "blueprint_inventory_merge_rollback_readiness_v0_1",
    "blueprint_inventory_acceptance_merge_gate_v0_1",
    "blueprint_inventory_post_merge_integrity_verification_v0_1",
    "blueprint_inventory_operational_handoff_readiness_v0_1",
    "blueprint_inventory_operational_readiness_review_v0_1",
    "blueprint_inventory_maintenance_baseline_activation_v0_1",
    "blueprint_ecosystem_inventory_rollout_release_review_v0_1",
    "ecosystem_inventory_rollout_wave_b_v0_1",
]


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def step_by_id(values: list[dict], step_id: str) -> dict:
    matches = [
        item
        for item in values
        if isinstance(item, dict) and item.get("step_id") == step_id
    ]
    assert len(matches) == 1
    return matches[0]


def ids_from_sequence(data: dict, first_sequence: int) -> list[str]:
    selected = [
        step
        for step in data["steps"]
        if isinstance(step, dict)
        and isinstance(step.get("sequence"), int)
        and step["sequence"] >= first_sequence
    ]
    selected.sort(key=lambda step: step["sequence"])
    return [str(step["step_id"]) for step in selected]


def test_historical_reconciliation_evidence_remains_exact_snapshot() -> None:
    reconciliation = load_yaml(RECONCILIATION)

    assert reconciliation["metadata"]["module_id"] == "forprint_system_blueprint"
    assert reconciliation["metadata"]["status"] == "completed"
    assert reconciliation["result"] == "BLUEPRINT_ROADMAP_CONTEXT_RECONCILED"
    assert reconciliation["roadmap_state"]["self_roadmap_step_count"] == 25
    assert reconciliation["roadmap_state"]["active_step_id"] == HISTORICAL_ACTIVE_ID
    assert reconciliation["roadmap_state"]["future_sequence_preserved"] is True
    assert reconciliation["boundaries"]["operator_decision_created"] is False
    assert reconciliation["boundaries"]["directive_activation"] is False
    assert reconciliation["boundaries"]["module_repository_write"] is False


def test_inventory_plan_history_is_preserved_while_self_roadmap_is_superseded() -> None:
    inventory = load_yaml(INVENTORY_PLAN)
    self_roadmap = load_yaml(SELF_ROADMAP)
    prompt_index = load_yaml(PROMPT_INDEX)

    assert len(inventory["steps"]) == 40
    assert inventory["metadata"]["current_step_id"] == HISTORICAL_ACTIVE_ID
    assert ids_from_sequence(inventory, 31) == EXPECTED_INVENTORY_FUTURE

    assert len(self_roadmap["steps"]) == 29
    active_id = self_roadmap["metadata"]["current_step_id"]
    assert active_id in {
        CURRENT_V04_ID,
        "blueprint_v0_4_completion_packet_v0_1",
        "blueprint_v0_4_completion_outbox_v0_1",
    }
    assert prompt_index["metadata"]["active_prompt_id"] == active_id

    prompt_contract = step_by_id(self_roadmap["steps"], CURRENT_V04_ID)
    if active_id == CURRENT_V04_ID:
        assert prompt_contract["status"] == "active"
    else:
        assert prompt_contract["status"] == "completed"
        assert prompt_contract["operator_decision"] == "ACCEPT"

    if active_id == "blueprint_v0_4_completion_outbox_v0_1":
        packet = step_by_id(
            self_roadmap["steps"],
            "blueprint_v0_4_completion_packet_v0_1",
        )
        assert packet["status"] == "completed"
        assert packet["operator_decision"] == "ACCEPT"

    deferred = step_by_id(
        self_roadmap["deferred_steps"],
        HISTORICAL_ACTIVE_ID,
    )
    assert deferred["status"] == "deferred"
    assert deferred["previous_sequence"] == 17
    assert deferred["release_after"] == "blueprint_v0_4_promotion_decision_v0_1"

def test_historical_context_metadata_is_marked_superseded_for_current_ordering() -> None:
    inventory = load_yaml(INVENTORY_PLAN)
    self_roadmap = load_yaml(SELF_ROADMAP)

    inventory_context = inventory["metadata"]["context_reconciliation"]
    self_context = self_roadmap["metadata"]["context_reconciliation"]

    assert inventory_context["status"] == "completed"
    assert inventory_context["completed_prerequisite_ids"] == PREREQUISITE_IDS

    assert self_context["status"] == "completed"
    assert self_context["completed_prerequisite_ids"] == PREREQUISITE_IDS
    assert self_context["state_scope"] == "historical_2026_08_07_snapshot"
    assert self_context["superseded_for_current_ordering"] is True
    assert self_context["superseded_by_step_id"] == SUPERSEDING_RECONCILIATION_ID

    inventory_active = step_by_id(
        inventory["steps"],
        HISTORICAL_ACTIVE_ID,
    )
    assert [
        item["prerequisite_id"]
        for item in inventory_active["context_prerequisites"]
    ] == PREREQUISITE_IDS


def test_handoff_reports_current_v04_and_links_historical_reconciliation() -> None:
    handoff = load_yaml(HANDOFF)

    observed_head = handoff["metadata"]["state_observed_at_head"]
    assert len(observed_head) == 40
    assert all(character in "0123456789abcdef" for character in observed_head)

    plan = handoff["current_blueprint_plan"]
    assert plan["freshness_verdict"] == "CURRENT_CONTEXT_RECONCILED"
    active_id = plan["active_blueprint_step"]["id"]
    assert active_id in {
        CURRENT_V04_ID,
        "blueprint_v0_4_completion_packet_v0_1",
        "blueprint_v0_4_completion_outbox_v0_1",
    }

    historical = plan["historical_context_reconciliation"]
    assert historical["state"] == "historical_snapshot_superseded_for_current_ordering"
    assert historical["historical_active_step_id"] == HISTORICAL_ACTIVE_ID
    assert historical["historical_evidence_mutated"] is False

    next_steps = handoff["next_10_steps"]
    assert 1 <= len(next_steps) <= 10
    assert [item["order"] for item in next_steps] == list(
        range(1, len(next_steps) + 1)
    )
    assert next_steps[0]["id"] == active_id
    assert handoff["hard_boundaries"]["automatic_acceptance"] is False
    assert handoff["hard_boundaries"]["automatic_return"] is False
    assert handoff["hard_boundaries"]["directive_activation_authorized"] is False

def test_historical_freshness_review_remains_historical() -> None:
    freshness = load_yaml(FRESHNESS_REVIEW)
    reconciliation = load_yaml(RECONCILIATION)

    assert (
        freshness["freshness_assessment"]["verdict"]
        == "SEQUENCE_VALID_CONTEXT_STALE"
    )
    assert freshness["boundaries"]["roadmap_mutated_by_this_review"] is False

    assert reconciliation["roadmap_state"]["active_step_id"] == HISTORICAL_ACTIVE_ID
    assert reconciliation["roadmap_state"]["future_sequence_preserved"] is True
    assert reconciliation["boundaries"]["operator_decision_created"] is False
