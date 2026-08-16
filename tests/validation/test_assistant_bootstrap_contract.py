from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
ROADMAP_REVIEW = (
    ROOT
    / "coordination/internal_work/blueprint/governance/2026-08-07__blueprint__assistant_bootstrap_roadmap_freshness_review_v0_1.yaml"
)
READING_ORDER = ROOT / "coordination/instruction_intake/assistant_reading_order.md"
MAKEFILE = ROOT / "Makefile"


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def make_targets() -> set[str]:
    result: set[str] = set()
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    for line in MAKEFILE.read_text(encoding="utf-8").splitlines():
        if not line or line[0].isspace():
            continue
        match = pattern.match(line)
        if match and not match.group(1).startswith("."):
            result.add(match.group(1))
    return result


def test_stable_bootstrap_contract_is_machine_oriented() -> None:
    data = load_yaml(BOOTSTRAP)
    assert data["schema_version"] == "blueprint_assistant_bootstrap_v0_1"
    assert data["metadata"]["module_id"] == "forprint_system_blueprint"
    assert data["metadata"]["machine_first"] is True
    assert data["metadata"]["stateful_snapshot"] is False
    assert data["coordination_role"]["system_role"]
    assert data["startup_protocol"]["required_order"]
    assert data["authority_boundaries"]["blueprint_must_not"]
    assert data["source_of_truth_map"]["blueprint_roadmap"]
    assert data["state_model"]["critical_non_equivalences"]


def test_bootstrap_make_targets_exist() -> None:
    data = load_yaml(BOOTSTRAP)
    assert set(data["make_interface"]["canonical_targets"]) <= make_targets()


def test_handoff_snapshot_contract() -> None:
    data = load_yaml(HANDOFF)
    assert data["schema_version"] == "blueprint_current_handoff_v0_1"
    assert data["metadata"]["state_observed_at_head"] == data["published_base"]["commit"]
    assert data["current_blueprint_plan"]["freshness_verdict"] == "CURRENT_CONTEXT_RECONCILED"
    active_id = data["current_blueprint_plan"]["active_blueprint_step"]["id"]
    step23 = "blueprint_v0_4_completion_outbox_v0_1"
    step24 = "blueprint_v0_4_completion_discovery_and_intake_v0_1"
    assert active_id in {
        "blueprint_v0_4_immutable_prompt_contract_v0_1",
        "blueprint_v0_4_completion_packet_v0_1",
        step23,
        step24,
        "blueprint_v0_4_review_roadmap_queue_transaction_v0_1",
        "blueprint_v0_4_next_prompt_selection_and_activation_v0_1",
    }
    if active_id in {
        "blueprint_v0_4_completion_packet_v0_1",
        step23,
        step24,
    }:
        contract_state = data["prompt_contract_v0_4"]
        assert contract_state["operator_decision_created"] is True
        assert contract_state["operator_decision"] == "ACCEPT"
        assert contract_state["promotion_performed"] is False
    if active_id in {step23, step24}:
        packet_state = data["completion_packet_v0_4"]
        assert packet_state["operator_decision_created"] is True
        assert packet_state["operator_decision"] == "ACCEPT"
        assert packet_state["implementation_status"] == "accepted_v0_4"
        assert packet_state["promotion_performed"] is False
    if active_id == step24:
        outbox_state = data["completion_outbox_v0_4"]
        assert outbox_state["operator_decision_created"] is True
        assert outbox_state["operator_decision"] == "ACCEPT"
        assert outbox_state["implementation_status"] == "accepted_v0_4"
        assert outbox_state["promotion_performed"] is False
    next_steps = data["next_10_steps"]
    assert 1 <= len(next_steps) <= 10
    assert [item["order"] for item in next_steps] == list(
        range(1, len(next_steps) + 1)
    )
    assert next_steps[0]["id"] == active_id
    assert data["hard_boundaries"]["automatic_acceptance"] is False
    assert data["hard_boundaries"]["automatic_return"] is False
    assert data["hard_boundaries"]["directive_activation_authorized"] is False

def test_bootstrap_and_handoff_do_not_narrow_portfolio_to_three_modules() -> None:
    bootstrap = load_yaml(BOOTSTRAP)
    handoff = load_yaml(HANDOFF)

    stable_scope = bootstrap["coordination_role"]["portfolio_scope"]
    assert stable_scope["scope"] == "all_forprint_project_modules"
    assert stable_scope["active_development_subset_is_exhaustive"] is False
    assert (
        "coordination/global_policy/ecosystem_module_map.md"
        in stable_scope["authoritative_inventory_sources"]
    )
    assert (
        "coordination/module_sources/module_git_sources.yaml"
        in stable_scope["authoritative_inventory_sources"]
    )

    current_scope = handoff["portfolio_scope"]
    assert current_scope["coordination_scope"] == "all_forprint_project_modules"
    assert current_scope["active_development_subset_is_exhaustive"] is False
    assert set(current_scope["active_development_subset"]) == {
        "forprint_library",
        "logistics_service",
        "telegram_bot",
    }
    assert handoff["managed_module_state_semantics"]["exhaustive"] is False


def test_roadmap_freshness_review_is_non_mutating_governance_evidence() -> None:
    data = load_yaml(ROADMAP_REVIEW)
    assert data["metadata"]["module_id"] == "forprint_system_blueprint"
    assert data["freshness_assessment"]["verdict"] == "SEQUENCE_VALID_CONTEXT_STALE"
    assert data["freshness_assessment"]["future_step_order_requires_rewrite"] is False
    assert data["freshness_assessment"]["context_reconciliation_required_before_resume"] is True
    assert data["boundaries"]["roadmap_mutated_by_this_review"] is False
    assert data["boundaries"]["operator_decision_created"] is False


def test_reading_order_surfaces_bootstrap_entrypoint() -> None:
    text = READING_ORDER.read_text(encoding="utf-8")
    assert "## Blueprint assistant bootstrap handoff entrypoint" in text
    assert "coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml" in text
    assert "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml" in text
