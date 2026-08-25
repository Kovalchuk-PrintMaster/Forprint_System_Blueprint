#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/cross_module_question_routing_contract_v0_1.yaml"


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
    require(meta["hardening_slice"] == "Q7", "hardening slice must be Q7")
    require(
        meta["stable_id"] == "blueprint_v0_4_1_cross_module_question_routing_contract_v0_1",
        "Q7 stable id drift",
    )

    inherits = data["inherits"]
    for key in (
        "q1_contract_path",
        "q2_contract_path",
        "q3_contract_path",
        "q4_contract_path",
        "q5_contract_path",
        "q6_contract_path",
    ):
        path = ROOT / inherits[key]
        require(path.is_file(), f"inherited contract missing: {path}")
        require(sha(path) == inherits[key.replace("_path", "_sha256")], f"inherited SHA drift: {path}")

    routing = data["routing"]
    require(
        routing["route_directions"]
        == [
            "module_to_blueprint_or_operator",
            "module_to_module",
            "blueprint_to_module",
        ],
        "route direction vocabulary drift",
    )
    require(routing["route_direction_count"] == 3, "route direction count drift")
    require(routing["unknown_route_direction_allowed"] is False, "unknown route direction allowed")
    require(routing["logical_identity_not_transport_address"] is True, "transport address required")
    require(routing["routing_grants_mutation_authority"] is False, "routing grants mutation authority")

    identity = data["q1_identity_preservation"]
    require(identity["question_id_stable_across_reroute"] is True, "question_id unstable across reroute")
    require(identity["correlation_id_stable_across_reroute"] is True, "correlation_id unstable across reroute")
    require(identity["routing_rewrites_q1_thread"] is False, "routing rewrites Q1 thread")
    require(identity["requester_target_remain_logical_actor_refs"] is True, "actor refs semantics drift")

    record = data["routing_record"]
    required = {
        "routing_id",
        "question_id",
        "module_id",
        "prompt_id",
        "roadmap_step_id",
        "requester",
        "target",
        "route_direction",
        "correlation_id",
        "blocking",
        "question_class",
        "round",
        "routing_reason",
        "routing_outcome",
        "evidence_refs",
        "routed_at",
    }
    require(set(record["required_fields"]) == required, "routing record field set drift")
    require(record["append_only"] is True, "routing records not append-only")
    require(record["prior_record_mutation_allowed"] is False, "prior routing record mutable")
    require(record["reroute_creates_new_routing_id"] is True, "reroute reuses routing record id")
    require(
        set(record["routing_outcomes"])
        == {"routed", "no_eligible_route", "operator_escalation_required"},
        "routing outcome set drift",
    )

    rounds = data["round_budget"]
    require(rounds["owner"] == "Q2", "round-budget owner drift")
    require(rounds["maximum_unresolved_round_trips_per_question_thread"] == 5, "five-round limit drift")
    require(rounds["scope"] == "per_question_thread", "round budget not per thread")
    require(rounds["routing_alone_consumes_round"] is False, "routing consumes round")
    require(rounds["rerouting_alone_consumes_round"] is False, "rerouting consumes round")
    require(rounds["failed_route_consumes_round"] is False, "failed route consumes round")
    require(rounds["round_six_allowed"] is False, "round six allowed")
    require(
        rounds["round_advances_only_after"] == "completed_answer_attempt_evaluated_insufficient",
        "round advancement semantics drift",
    )

    answer = data["answer_evidence"]
    require(
        set(answer["required_fields"])
        == {
            "question_id",
            "responder",
            "correlation_id",
            "round",
            "answer",
            "evidence_refs",
            "answered_at",
        },
        "answer evidence field set drift",
    )
    require(answer["evidence_refs_min_items"] == 1, "answer may omit evidence")
    require(answer["answer_without_evidence_refs_valid"] is False, "evidence-free answer valid")
    require(answer["secret_values_allowed"] is False, "secret values allowed in answer")
    require(answer["secret_references_allowed"] is True, "secret references forbidden")

    strategy = data["strategic_ambiguity"]
    require(strategy["must_escalate_to_blueprint_or_operator"] is True, "strategic ambiguity may be guessed")
    require(strategy["module_to_module_guess_allowed"] is False, "strategic module guess allowed")
    require(strategy["routing_escalation_is_operator_decision"] is False, "routing escalation became decision")
    require(strategy["q4_authority_preserved"] is True, "Q4 authority not preserved")

    access = data["access_and_secrets"]
    require(access["may_route_directly_to_operator"] is True, "direct operator access route disabled")
    require(access["routing_grants_access"] is False, "routing grants access")
    require(access["secret_values_allowed"] is False, "secret values allowed")
    require(access["secret_references_allowed"] is True, "secret refs disabled")

    writes = data["cross_repository_boundary"]
    require(writes and all(value is False for value in writes.values()), f"cross-repo write enabled: {writes}")

    authority = data["authority_boundary"]
    require(authority and all(value is False for value in authority.values()), f"inferred authority enabled: {authority}")

    events = data["q5_event_integration"]
    require(events["adds_fields_to_q5_envelope"] is False, "Q7 changed Q5 envelope")
    require(events["persistent_event_runtime_implemented"] is False, "Q7 implemented event runtime")
    require(
        set(events["semantic_event_types"])
        == {
            "clarification.routed",
            "clarification.rerouted",
            "clarification.route_failed",
            "clarification.escalated",
            "answer_resolution.received",
        },
        "Q5 event integration drift",
    )

    attention = data["q6_attention_integration"]
    require(attention["redefines_q6_attention_lifecycle"] is False, "Q7 redefines Q6 lifecycle")
    require(attention["transport_implemented_by_q7"] is False, "Q7 implemented attention transport")
    require(
        set(attention["allowed_attention_reasons"])
        == {
            "clarification_escalated",
            "access_required",
            "manual_review_required",
            "dependency_blocked",
        },
        "Q6 attention integration drift",
    )

    deferred = data["deferred_boundaries"]
    require(set(deferred) == {"Q8_logistics_reference_validation"}, "deferred boundary set drift")
    require(all(deferred.values()), "Q8 consumed by Q7")

    caps = data["current_capabilities"]
    require(caps and all(value is False for value in caps.values()), f"forbidden capability enabled: {caps}")

    acceptance = data["acceptance"]
    require(acceptance and all(value is True for value in acceptance.values()), "Q7 acceptance incomplete")


def main() -> int:
    data = load(CONTRACT)
    validate(data)
    print("Q7 cross-module question routing validation PASSED")
    print("canonical_route_directions=3")
    print("question_id_stable_across_reroute=true")
    print("correlation_id_stable_across_reroute=true")
    print("maximum_unresolved_round_trips_per_question_thread=5")
    print("routing_alone_consumes_round=false")
    print("answer_evidence_refs_min_items=1")
    print("strategic_ambiguity_escalates=true")
    print("access_may_route_directly_to_operator=true")
    print("cross_repository_writes=false")
    print("live_routing_runtime=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
