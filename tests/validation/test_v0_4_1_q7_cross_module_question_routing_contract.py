from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/cross_module_question_routing_contract_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q7_cross_module_question_routing_contract.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_exact_route_directions() -> None:
    routing = load_contract()["routing"]
    assert routing["route_directions"] == [
        "module_to_blueprint_or_operator",
        "module_to_module",
        "blueprint_to_module",
    ]
    assert routing["route_direction_count"] == 3
    assert routing["unknown_route_direction_allowed"] is False
    assert routing["logical_identity_not_transport_address"] is True


def test_q1_identity_is_preserved_across_rerouting() -> None:
    identity = load_contract()["q1_identity_preservation"]
    assert identity["question_id_stable_across_reroute"] is True
    assert identity["correlation_id_stable_across_reroute"] is True
    assert identity["routing_rewrites_q1_thread"] is False
    assert identity["requester_target_remain_logical_actor_refs"] is True


def test_routing_records_are_append_only_and_reroute_gets_new_record_id() -> None:
    record = load_contract()["routing_record"]
    assert record["append_only"] is True
    assert record["prior_record_mutation_allowed"] is False
    assert record["reroute_creates_new_routing_id"] is True
    assert set(record["routing_outcomes"]) == {
        "routed",
        "no_eligible_route",
        "operator_escalation_required",
    }


def test_q2_five_round_budget_remains_per_thread_and_route_does_not_consume_round() -> None:
    rounds = load_contract()["round_budget"]
    assert rounds["owner"] == "Q2"
    assert rounds["maximum_unresolved_round_trips_per_question_thread"] == 5
    assert rounds["scope"] == "per_question_thread"
    assert rounds["routing_alone_consumes_round"] is False
    assert rounds["rerouting_alone_consumes_round"] is False
    assert rounds["failed_route_consumes_round"] is False
    assert rounds["round_six_allowed"] is False
    assert rounds["round_advances_only_after"] == "completed_answer_attempt_evaluated_insufficient"


def test_routed_answers_require_evidence_refs() -> None:
    answer = load_contract()["answer_evidence"]
    assert answer["evidence_refs_min_items"] == 1
    assert answer["answer_without_evidence_refs_valid"] is False
    assert answer["secret_values_allowed"] is False
    assert answer["secret_references_allowed"] is True


def test_strategic_ambiguity_escalates_instead_of_module_guessing() -> None:
    strategy = load_contract()["strategic_ambiguity"]
    assert strategy["must_escalate_to_blueprint_or_operator"] is True
    assert strategy["module_to_module_guess_allowed"] is False
    assert strategy["routing_escalation_is_operator_decision"] is False
    assert strategy["q4_authority_preserved"] is True


def test_access_can_route_to_operator_without_granting_access() -> None:
    access = load_contract()["access_and_secrets"]
    assert access["may_route_directly_to_operator"] is True
    assert access["routing_grants_access"] is False
    assert access["secret_values_allowed"] is False
    assert access["secret_references_allowed"] is True


def test_cross_repository_writes_are_all_disabled() -> None:
    assert all(value is False for value in load_contract()["cross_repository_boundary"].values())


def test_routing_does_not_infer_governance_authority() -> None:
    assert all(value is False for value in load_contract()["authority_boundary"].values())


def test_q5_q6_integration_is_semantic_only() -> None:
    data = load_contract()
    events = data["q5_event_integration"]
    assert events["adds_fields_to_q5_envelope"] is False
    assert events["persistent_event_runtime_implemented"] is False
    assert "clarification.routed" in events["semantic_event_types"]
    attention = data["q6_attention_integration"]
    assert attention["redefines_q6_attention_lifecycle"] is False
    assert attention["transport_implemented_by_q7"] is False


def test_q8_and_runtime_remain_deferred() -> None:
    data = load_contract()
    assert all(data["deferred_boundaries"].values())
    assert all(value is False for value in data["current_capabilities"].values())


def test_human_standard_fragments() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "Routing selects a logical respondent",
        "Canonical route directions",
        "`module_to_blueprint_or_operator`",
        "`module_to_module`",
        "`blueprint_to_module`",
        "Q1 identity is preserved",
        "Routing record",
        "Routing outcomes",
        "Routing or rerouting by itself does not consume a round.",
        "No Q7 rule allows round 6.",
        "Every routed answer must carry",
        "`evidence_refs` must contain at least one stable evidence reference.",
        "Strategic ambiguity",
        "may route directly to the operator",
        "No cross-repository writes",
        "No inferred authority",
        "Separation from Q8",
        "Runtime boundary",
    ):
        assert fragment in text


def test_q7_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q7 cross-module question routing validation PASSED" in cp.stdout


def test_q7_validator_is_in_canonical_check_catalog() -> None:
    checks = {check.check_id: check for check in build_checks()}
    check = checks["q7_cross_module_question_routing_validation"]
    assert check.title == "Q7 cross-module question routing"
    assert check.command[-1] == "scripts/validation/validate_q7_cross_module_question_routing_contract.py"
