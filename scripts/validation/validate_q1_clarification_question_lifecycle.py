#!/usr/bin/env python3
from __future__ import annotations

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

EXPECTED_NORMAL = [
    "OPEN",
    "ROUTED",
    "ANSWERED",
    "CONFIRMED",
    "RESOLVED",
]
EXPECTED_ALT_TERMINALS = {
    "ESCALATED",
    "CANCELLED",
    "EXPIRED",
}
EXPECTED_REQUIRED_FIELDS = {
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
EXPECTED_DEFERRED = {
    "Q2_bounded_five_round_escalation",
    "Q3_blocker_taxonomy",
    "Q4_operator_decision_adjustment_model",
    "Q5_common_event_envelope",
    "Q6_operator_attention_semantics",
    "Q7_cross_module_routing_mechanics",
    "Q8_logistics_reference_validation",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "contract root must be mapping")
    return data


def validate(data: dict) -> None:
    metadata = data["metadata"]
    require(metadata["hardening_slice"] == "Q1", "hardening slice must be Q1")
    require(
        metadata["stable_id"] == "blueprint_v0_4_1_clarification_question_lifecycle_v0_1",
        "Q1 stable id mismatch",
    )

    core = data["core_rule"]
    require(core["question_is_prompt_disposition"] is False, "question became disposition")
    require(core["question_creation_implies_return"] is False, "question implies RETURN")
    require(core["question_creation_implies_hold"] is False, "question implies HOLD")
    require(
        core["question_lifecycle_mutates_released_prompt"] is False,
        "question lifecycle may not mutate released prompt",
    )
    require(core["released_prompt_remains_immutable"] is True, "prompt immutability lost")
    require(
        {"ACCEPT", "RETURN", "HOLD"}.issubset(set(core["separate_decision_required_for"])),
        "ACCEPT/RETURN/HOLD must remain separate decisions",
    )

    identity = data["thread_identity"]
    require(
        set(identity["required_fields"]) == EXPECTED_REQUIRED_FIELDS,
        "minimum Q1 identity field set drift",
    )
    require(identity["question_id_stable_and_immutable"] is True, "question_id not immutable")
    require(
        identity["requester_and_target_are_logical_actor_refs"] is True,
        "requester/target must be logical actor refs",
    )
    require(
        identity["transport_specific_address_required"] is False,
        "Q1 must be transport-neutral",
    )
    require(
        identity["question_class_vocabulary_owned_by_q1"] is False,
        "Q1 must not preempt Q3 taxonomy",
    )
    round_rule = identity["round"]
    require(round_rule["required"] is True, "round field must be required")
    require(round_rule["minimum"] == 1, "round minimum must be one")
    require(
        round_rule["maximum_defined_by_q1"] is False,
        "Q1 must not implement the Q2 five-round limit",
    )
    require(round_rule["bounded_limit_owner"] == "Q2", "round limit owner must be Q2")
    answer = identity["answer"]
    require(
        answer["nullable_before_answered"] is True,
        "answer must be nullable before ANSWERED",
    )
    require(
        answer["must_be_present_from_state"] == "ANSWERED",
        "answer state rule drift",
    )
    evidence = identity["evidence_refs"]
    require(
        evidence["secret_values_allowed"] is False,
        "secret values must not enter evidence",
    )
    require(
        evidence["secret_references_allowed"] is True,
        "secret refs should remain representable",
    )

    lifecycle = data["lifecycle"]
    require(lifecycle["normal_order"] == EXPECTED_NORMAL, "normal lifecycle order drift")
    require(
        set(lifecycle["alternative_terminals"]) == EXPECTED_ALT_TERMINALS,
        "alternative terminal set drift",
    )
    require(
        set(lifecycle["terminal_states"]) == {"RESOLVED", *EXPECTED_ALT_TERMINALS},
        "terminal state set drift",
    )
    require(
        lifecycle["terminal_transition_out_allowed"] is False,
        "terminal threads must not reopen",
    )
    require(
        lifecycle["answered_is_not_confirmed"] is True,
        "ANSWERED collapsed into CONFIRMED",
    )
    require(
        lifecycle["confirmed_is_not_prompt_acceptance"] is True,
        "CONFIRMED collapsed into prompt ACCEPT",
    )
    require(
        lifecycle["resolved_is_not_prompt_acceptance"] is True,
        "RESOLVED collapsed into prompt ACCEPT",
    )
    require(
        lifecycle["automatic_escalation_threshold_defined_by_q1"] is False,
        "Q1 must not implement automatic escalation threshold",
    )
    require(
        lifecycle["bounded_escalation_owner"] == "Q2",
        "bounded escalation owner drift",
    )

    timestamps = data["timestamps"]
    require(
        set(timestamps["always_required"]) == {"created_at", "state_changed_at"},
        "always-required timestamps drift",
    )
    require(
        "answered_at" in timestamps["state_specific"]["ANSWERED"],
        "ANSWERED timestamp missing",
    )
    require(
        "confirmed_at" in timestamps["state_specific"]["CONFIRMED"],
        "CONFIRMED timestamp missing",
    )
    require(
        "resolved_at" in timestamps["state_specific"]["RESOLVED"],
        "RESOLVED timestamp missing",
    )
    for terminal in EXPECTED_ALT_TERMINALS:
        require(
            "terminal_at" in timestamps["state_specific"][terminal],
            f"{terminal} terminal_at missing",
        )
    require(
        timestamps["live_runtime_implemented_by_q1"] is False,
        "Q1 must not implement live runtime",
    )

    coupling = data["prompt_coupling"]
    require(
        coupling["prompt_status_may_remain"] == "in_progress",
        "prompt status coupling drift",
    )
    require(
        coupling["coordination_condition"] == "waiting_on_clarification",
        "waiting condition drift",
    )
    require(coupling["condition_is_return"] is False, "waiting condition became RETURN")
    require(coupling["condition_is_hold"] is False, "waiting condition became HOLD")
    require(
        coupling["blocking_field_required"] is True,
        "blocking field must remain explicit",
    )
    require(
        coupling["blocking_true_means_whole_prompt_return"] is False,
        "blocking question must not auto-RETURN prompt",
    )
    require(
        coupling["blocking_true_means_whole_prompt_hold"] is False,
        "blocking question must not auto-HOLD prompt",
    )

    bridge = data["reporting_bridge"]
    require(
        bridge["next_questions_for_blueprint_is_q1_authority"] is False,
        "legacy reporting artifact became Q1 authority",
    )
    require(
        bridge["returned_for_fix_is_explicit_review_disposition"] is True,
        "returned_for_fix distinction lost",
    )
    require(
        bridge["question_automatically_produces_returned_for_fix"] is False,
        "clarification collapsed into returned_for_fix",
    )

    storage = data["storage_boundary"]
    require(
        storage["semantic_contract_only"] is True,
        "Q1 must remain semantic contract only",
    )
    require(
        set(storage["future_schema_families"]) == {"question_threads", "question_messages"},
        "future question schema family binding drift",
    )
    require(
        storage["database_backend_bound_by_q1"] is False,
        "Q1 bound a DB backend",
    )
    require(
        storage["database_file_created_by_q1"] is False,
        "Q1 created a DB file",
    )
    require(
        storage["live_sqlite_runtime_enabled"] is False,
        "Q1 enabled SQLite runtime",
    )

    deferred = data["deferred_boundaries"]
    require(set(deferred) == EXPECTED_DEFERRED, "Q1 deferred boundary set drift")
    require(
        all(value is True for value in deferred.values()),
        "Q1 consumed deferred Q work",
    )

    capabilities = data["current_capabilities"]
    require(capabilities, "current_capabilities missing")
    require(
        all(value is False for value in capabilities.values()),
        f"forbidden capability enabled: {capabilities}",
    )

    acceptance = data["acceptance"]
    require(
        acceptance and all(value is True for value in acceptance.values()),
        "acceptance declaration incomplete",
    )


def main() -> int:
    data = load_contract()
    validate(data)
    print("Q1 clarification question lifecycle validation PASSED")
    print(f"contract={CONTRACT.relative_to(ROOT)}")
    print(f"normal_states={len(data['lifecycle']['normal_order'])}")
    print(f"alternative_terminals={len(data['lifecycle']['alternative_terminals'])}")
    print(f"required_identity_fields={len(data['thread_identity']['required_fields'])}")
    print("question_implies_return=false")
    print("question_implies_hold=false")
    print("q2_bounded_round_limit_implemented=false")
    print("live_sqlite_runtime_enabled=false")
    print("autonomous_execution_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
