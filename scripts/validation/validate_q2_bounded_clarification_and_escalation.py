#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/bounded_clarification_and_escalation_v0_1.yaml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"{path}: root must be mapping")
    return data


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(data: dict) -> None:
    meta = data["metadata"]
    require(meta["hardening_slice"] == "Q2", "hardening slice must be Q2")
    require(meta["stable_id"] == "blueprint_v0_4_1_bounded_clarification_and_escalation_v0_1", "stable id drift")

    inherits = data["inherits"]
    q1 = ROOT / inherits["q1_contract_path"]
    require(q1.is_file(), "Q1 contract missing")
    require(sha(q1) == inherits["q1_contract_sha256"], "Q1 contract SHA drift")
    for key in (
        "q1_question_identity_preserved",
        "q1_terminal_states_preserved",
        "released_prompt_immutability_preserved",
        "question_remains_distinct_from_prompt_disposition",
    ):
        require(inherits[key] is True, f"Q1 inheritance lost: {key}")

    budget = data["round_budget"]
    require(budget["setting_name"] == "maximum_unresolved_round_trips_per_question_thread", "setting drift")
    require(budget["maximum_unresolved_round_trips_per_question_thread"] == 5, "limit must be five")
    require(budget["scope"] == "per_question_thread", "limit must be per thread")
    require(budget["prompt_shared_counter"] is False, "prompt-shared counter forbidden")
    require(budget["new_question_thread_has_independent_counter"] is True, "thread counter must be independent")
    require(budget["initial_round"] == 1, "initial round must be one")
    require(budget["maximum_autonomous_round"] == 5, "max autonomous round must be five")
    require(budget["round_six_allowed"] is False, "round six forbidden")
    require(budget["thread_question_id_stable_across_rounds"] is True, "question id must remain stable")
    require(budget["thread_correlation_id_stable_across_rounds"] is True, "correlation id must remain stable")
    require(budget["history_append_only"] is True, "history must be append-only")
    require(budget["round_advances_only_after"] == "completed_answer_attempt_evaluated_insufficient", "advance rule drift")
    require(budget["missing_answer_does_not_consume_completed_round_trip"] is True, "missing answer consumed round")
    require(budget["answer_not_yet_evaluated_does_not_advance"] is True, "unevaluated answer advanced")
    require(budget["resolved_answer_does_not_advance"] is True, "resolved answer advanced")

    flow = data["round_flow"]
    require(flow["rounds_1_through_4"]["if_answer_sufficient"] == ["CONFIRMED", "RESOLVED"], "early resolve drift")
    require("increment_round" in flow["rounds_1_through_4"]["if_answer_insufficient"], "early retry missing")
    require(flow["round_5"]["if_answer_sufficient"] == ["CONFIRMED", "RESOLVED"], "round five resolve drift")
    require("ESCALATED" in flow["round_5"]["if_answer_insufficient"], "round five escalation missing")
    require("stop_further_autonomous_dialogue_for_thread" in flow["round_5"]["if_answer_insufficient"], "stop missing")
    require(flow["terminal_thread_reopen_allowed"] is False, "terminal thread may reopen")
    require(flow["same_thread_round_6_after_escalation_allowed"] is False, "round six after escalation allowed")

    record = data["round_record"]
    require(set(record["required_fields"]) == {
        "round", "question", "answer", "evidence_refs",
        "asked_at", "answered_at", "evaluation", "evaluated_at",
    }, "round record fields drift")
    require(set(record["evaluation_values"]) == {"sufficient", "insufficient"}, "evaluation values drift")
    require(record["prior_round_mutation_allowed"] is False, "prior round mutation allowed")
    require(record["secret_values_allowed"] is False, "secret values allowed")

    esc = data["escalation"]
    require(esc["trigger"] == "round_5_completed_and_evaluated_insufficient", "trigger drift")
    require(esc["resulting_thread_state"] == "ESCALATED", "state drift")
    require(esc["terminal"] is True, "ESCALATED must be terminal")
    require(esc["further_autonomous_dialogue_for_same_thread"] is False, "dialogue continues")
    require(set(esc["required_packet_fields"]) == {
        "question_id", "module_id", "prompt_id", "roadmap_step_id", "requester", "target",
        "correlation_id", "blocking", "original_question", "round_history", "evidence_refs",
        "unresolved_fact", "impact", "safe_options", "recommended_next_action", "trigger", "escalated_at",
    }, "escalation packet fields drift")
    require(esc["round_history_must_cover"] == [1, 2, 3, 4, 5], "round history coverage drift")
    require(esc["recommended_next_action_is_advisory"] is True, "recommendation became authority")
    require(esc["safe_options_are_not_automatic_actions"] is True, "safe options became actions")
    require(esc["transport_or_attention_owner_defined_by_q2"] is False, "Q2 preempted Q6")

    coupling = data["prompt_coupling"]
    require(coupling["blocking_escalated_thread_condition"] == "waiting_on_clarification_escalation", "condition drift")
    require(coupling["blocking_scope_progress_allowed"] is False, "blocking scope may continue")
    require(coupling["condition_is_return"] is False, "condition became RETURN")
    require(coupling["condition_is_hold"] is False, "condition became HOLD")
    require(coupling["condition_is_prompt_acceptance"] is False, "condition became acceptance")
    require(coupling["q3_blocker_taxonomy_defined_here"] is False, "Q2 consumed Q3")

    deferred = data["deferred_boundaries"]
    require(set(deferred) == {
        "Q3_blocker_taxonomy", "Q4_operator_decision_adjustment_model", "Q5_common_event_envelope",
        "Q6_operator_attention_semantics", "Q7_cross_module_routing_mechanics", "Q8_logistics_reference_validation",
    }, "deferred boundary set drift")
    require(all(deferred.values()), "deferred Q work consumed")

    storage = data["storage_boundary"]
    require(storage["semantic_contract_only"] is True, "Q2 must remain semantic-only")
    require(storage["live_question_store_created"] is False, "live question store created")
    require(storage["database_backend_bound_by_q2"] is False, "DB backend bound")
    require(storage["live_sqlite_runtime_enabled"] is False, "SQLite enabled")

    caps = data["current_capabilities"]
    require(caps and all(v is False for v in caps.values()), f"forbidden capability enabled: {caps}")
    acceptance = data["acceptance"]
    require(acceptance and all(v is True for v in acceptance.values()), "acceptance declaration incomplete")


def main() -> int:
    data = load(CONTRACT)
    validate(data)
    print("Q2 bounded clarification and escalation validation PASSED")
    print("maximum_unresolved_round_trips_per_question_thread=5")
    print("round_limit_scope=per_question_thread")
    print("round_five_unresolved=ESCALATED")
    print("round_six_allowed=false")
    print("prompt_shared_counter=false")
    print("condition_is_return=false")
    print("condition_is_hold=false")
    print("live_sqlite_runtime_enabled=false")
    print("autonomous_execution_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
