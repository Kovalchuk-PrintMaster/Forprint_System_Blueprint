from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "coordination"
    / "standards"
    / "governance"
    / "clarification_question_lifecycle_v0_1.yaml"
)
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts" / "validation" / "validate_q1_clarification_question_lifecycle.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_q1_normal_and_terminal_lifecycle_is_exact() -> None:
    data = load_contract()
    lifecycle = data["lifecycle"]
    assert lifecycle["normal_order"] == [
        "OPEN",
        "ROUTED",
        "ANSWERED",
        "CONFIRMED",
        "RESOLVED",
    ]
    assert set(lifecycle["alternative_terminals"]) == {
        "ESCALATED",
        "CANCELLED",
        "EXPIRED",
    }
    assert set(lifecycle["terminal_states"]) == {
        "RESOLVED",
        "ESCALATED",
        "CANCELLED",
        "EXPIRED",
    }
    assert lifecycle["terminal_transition_out_allowed"] is False


def test_q1_minimum_identity_is_complete_without_q3_or_transport_binding() -> None:
    data = load_contract()
    identity = data["thread_identity"]
    assert set(identity["required_fields"]) == {
        "question_id",
        "module_id",
        "prompt_id",
        "roadmap_step_id",
        "requester",
        "target",
        "correlation_id",
        "blocking",
        "question_class",
        "round",
        "question",
        "answer",
        "evidence_refs",
        "timestamps",
    }
    assert identity["question_id_stable_and_immutable"] is True
    assert identity["requester_and_target_are_logical_actor_refs"] is True
    assert identity["transport_specific_address_required"] is False
    assert identity["question_class_vocabulary_owned_by_q1"] is False


def test_q1_answer_confirmation_and_prompt_acceptance_remain_distinct() -> None:
    data = load_contract()
    lifecycle = data["lifecycle"]
    answer = data["thread_identity"]["answer"]
    assert answer["nullable_before_answered"] is True
    assert answer["must_be_present_from_state"] == "ANSWERED"
    assert lifecycle["answered_is_not_confirmed"] is True
    assert lifecycle["confirmed_is_not_prompt_acceptance"] is True
    assert lifecycle["resolved_is_not_prompt_acceptance"] is True


def test_question_does_not_mean_return_or_hold() -> None:
    data = load_contract()
    core = data["core_rule"]
    coupling = data["prompt_coupling"]
    assert core["question_is_prompt_disposition"] is False
    assert core["question_creation_implies_return"] is False
    assert core["question_creation_implies_hold"] is False
    assert coupling["prompt_status_may_remain"] == "in_progress"
    assert coupling["coordination_condition"] == "waiting_on_clarification"
    assert coupling["condition_is_return"] is False
    assert coupling["condition_is_hold"] is False
    assert coupling["blocking_true_means_whole_prompt_return"] is False
    assert coupling["blocking_true_means_whole_prompt_hold"] is False


def test_q2_limit_and_q3_q8_semantics_remain_deferred() -> None:
    data = load_contract()
    round_rule = data["thread_identity"]["round"]
    lifecycle = data["lifecycle"]
    deferred = data["deferred_boundaries"]
    assert round_rule["maximum_defined_by_q1"] is False
    assert round_rule["bounded_limit_owner"] == "Q2"
    assert lifecycle["automatic_escalation_threshold_defined_by_q1"] is False
    assert lifecycle["bounded_escalation_owner"] == "Q2"
    assert all(deferred.values())


def test_reporting_bridge_does_not_collapse_question_into_returned_for_fix() -> None:
    data = load_contract()
    bridge = data["reporting_bridge"]
    assert bridge["next_questions_for_blueprint_may_surface_questions"] is True
    assert bridge["next_questions_for_blueprint_is_q1_authority"] is False
    assert bridge["returned_for_fix_is_explicit_review_disposition"] is True
    assert bridge["question_automatically_produces_returned_for_fix"] is False


def test_q1_does_not_enable_runtime_autonomy_transport_or_cross_repo_writes() -> None:
    data = load_contract()
    storage = data["storage_boundary"]
    caps = data["current_capabilities"]
    assert storage["semantic_contract_only"] is True
    assert storage["database_backend_bound_by_q1"] is False
    assert storage["database_file_created_by_q1"] is False
    assert storage["live_sqlite_runtime_enabled"] is False
    assert caps
    assert all(value is False for value in caps.values())


def test_human_contract_contains_required_q1_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "## First-class question thread",
        "OPEN -> ROUTED -> ANSWERED -> CONFIRMED -> RESOLVED",
        "ESCALATED",
        "CANCELLED",
        "EXPIRED",
        "waiting_on_clarification",
        "A question is a clarification object, not a prompt disposition.",
        "## Relationship to existing reporting artifacts",
        "returned_for_fix",
        "## Storage boundary",
        "## Deferred boundaries",
        "Q2 five-round unresolved clarification limit",
        "automatic ACCEPT",
    ):
        assert fragment in text


def test_q1_validator_passes() -> None:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout
    assert "Q1 clarification question lifecycle validation PASSED" in completed.stdout
