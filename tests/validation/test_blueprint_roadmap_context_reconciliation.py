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

ACTIVE_ID = "blueprint_inventory_acceptance_packet_integrity_gate_v0_1"

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

EXPECTED_SELF_FUTURE = [
    "blueprint_inventory_acceptance_packet_integrity_gate_v0_1",
    "blueprint_inventory_acceptance_decision_readiness_review_v0_1",
    "blueprint_inventory_merge_rollback_readiness_v0_1",
    "blueprint_inventory_acceptance_merge_gate_v0_1",
    "blueprint_inventory_post_merge_integrity_verification_v0_1",
    "blueprint_inventory_operational_handoff_readiness_v0_1",
    "blueprint_inventory_operational_readiness_review_v0_1",
    "blueprint_inventory_maintenance_baseline_activation_v0_1",
    "blueprint_ecosystem_inventory_rollout_release_review_v0_1",
]


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def step_by_id(data: dict, step_id: str) -> dict:
    steps = data["steps"]
    assert isinstance(steps, list)
    matches = [step for step in steps if isinstance(step, dict) and step.get("step_id") == step_id]
    assert len(matches) == 1
    return matches[0]


def ids_from_sequence(data: dict, first_sequence: int) -> list[str]:
    steps = data["steps"]
    assert isinstance(steps, list)
    selected = [
        step
        for step in steps
        if isinstance(step, dict)
        and isinstance(step.get("sequence"), int)
        and step["sequence"] >= first_sequence
    ]
    selected.sort(key=lambda step: step["sequence"])
    return [str(step["step_id"]) for step in selected]


def test_reconciliation_preserves_active_gate_and_step_counts() -> None:
    inventory = load_yaml(INVENTORY_PLAN)
    self_roadmap = load_yaml(SELF_ROADMAP)
    prompt_index = load_yaml(PROMPT_INDEX)

    assert len(inventory["steps"]) == 40
    assert len(self_roadmap["steps"]) == 25

    assert inventory["metadata"]["current_step_id"] == ACTIVE_ID
    assert self_roadmap["metadata"]["current_step_id"] == ACTIVE_ID
    assert prompt_index["metadata"]["active_prompt_id"] == ACTIVE_ID

    assert step_by_id(inventory, ACTIVE_ID)["status"] == "active"
    assert step_by_id(self_roadmap, ACTIVE_ID)["status"] == "active"


def test_future_sequence_is_not_rewritten() -> None:
    inventory = load_yaml(INVENTORY_PLAN)
    self_roadmap = load_yaml(SELF_ROADMAP)

    assert ids_from_sequence(inventory, 31) == EXPECTED_INVENTORY_FUTURE
    assert ids_from_sequence(self_roadmap, 17) == EXPECTED_SELF_FUTURE

    inventory_active = step_by_id(inventory, ACTIVE_ID)
    self_active = step_by_id(self_roadmap, ACTIVE_ID)

    assert inventory_active["depends_on"] == ["blueprint_inventory_acceptance_dry_run_v0_1"]
    assert self_active["depends_on"] == ["blueprint_inventory_acceptance_dry_run_v0_1"]


def test_context_prerequisites_are_machine_readable_and_aligned() -> None:
    inventory = load_yaml(INVENTORY_PLAN)
    self_roadmap = load_yaml(SELF_ROADMAP)

    inventory_context = inventory["metadata"]["context_reconciliation"]
    self_context = self_roadmap["metadata"]["context_reconciliation"]

    assert inventory_context["status"] == "completed"
    assert self_context["status"] == "completed"
    assert inventory_context["active_step_preserved"] is True
    assert self_context["active_step_preserved"] is True
    assert inventory_context["future_sequence_preserved"] is True
    assert self_context["future_sequence_preserved"] is True
    assert inventory_context["step_sequences_rewritten"] is False
    assert self_context["step_sequences_rewritten"] is False
    assert inventory_context["completed_prerequisite_ids"] == PREREQUISITE_IDS
    assert self_context["completed_prerequisite_ids"] == PREREQUISITE_IDS

    inventory_active = step_by_id(inventory, ACTIVE_ID)
    self_active = step_by_id(self_roadmap, ACTIVE_ID)
    assert [
        item["prerequisite_id"] for item in inventory_active["context_prerequisites"]
    ] == PREREQUISITE_IDS
    assert [
        item["prerequisite_id"] for item in self_active["context_prerequisites"]
    ] == PREREQUISITE_IDS


def test_handoff_marks_context_reconciled_without_claiming_decisions() -> None:
    handoff = load_yaml(HANDOFF)

    assert handoff["metadata"]["state_observed_at_head"] == (
        "0a3a21696ee517d54cc872c8ef9f16e61c4f3f4d"
    )
    assert handoff["current_blueprint_plan"]["freshness_verdict"] == ("CURRENT_CONTEXT_RECONCILED")
    assert handoff["current_blueprint_plan"]["active_blueprint_step"]["id"] == (ACTIVE_ID)
    assert handoff["current_blueprint_plan"]["context_reconciliation"]["status"] == "completed"

    roadmap_debt = next(
        item
        for item in handoff["known_governance_debt"]
        if item["id"] == "blueprint_roadmap_context_freshness"
    )
    assert roadmap_debt["state"] == "RESOLVED"

    assert len(handoff["next_10_steps"]) == 10
    assert [item["order"] for item in handoff["next_10_steps"]] == list(range(1, 11))

    assert handoff["hard_boundaries"]["automatic_acceptance"] is False
    assert handoff["hard_boundaries"]["automatic_return"] is False
    assert handoff["hard_boundaries"]["directive_activation_authorized"] is False


def test_historical_freshness_review_remains_historical() -> None:
    freshness = load_yaml(FRESHNESS_REVIEW)
    reconciliation = load_yaml(RECONCILIATION)

    assert freshness["freshness_assessment"]["verdict"] == ("SEQUENCE_VALID_CONTEXT_STALE")
    assert freshness["boundaries"]["roadmap_mutated_by_this_review"] is False

    assert reconciliation["metadata"]["module_id"] == ("forprint_system_blueprint")
    assert reconciliation["result"] == ("BLUEPRINT_ROADMAP_CONTEXT_RECONCILED")
    assert reconciliation["roadmap_state"]["active_step_id"] == ACTIVE_ID
    assert reconciliation["roadmap_state"]["future_sequence_preserved"] is True
    assert reconciliation["boundaries"]["operator_decision_created"] is False
    assert reconciliation["boundaries"]["directive_activation"] is False
    assert reconciliation["boundaries"]["module_repository_write"] is False
