#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/logistics_clarification_reference_validation_v0_1.yaml"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"{path}: root must be mapping")
    return data


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_ref(refs: dict, key: str) -> tuple[Path, dict]:
    path = ROOT / refs[f"{key}_path"]
    require(path.is_file(), f"reference missing: {path}")
    require(sha(path) == refs[f"{key}_sha256"], f"reference SHA drift: {path}")
    return path, load(path)


def validate(data: dict) -> None:
    meta = data["metadata"]
    require(meta["hardening_slice"] == "Q8", "hardening slice must be Q8")
    require(
        meta["stable_id"] == "blueprint_v0_4_1_logistics_clarification_reference_validation_v0_1",
        "Q8 stable id drift",
    )

    refs = data["references"]
    _, h9 = resolve_ref(refs, "h9_acceptance")
    _, b1 = resolve_ref(refs, "b1_logistics_validation")
    _, q1 = resolve_ref(refs, "q1")
    _, q2 = resolve_ref(refs, "q2")
    _, q3 = resolve_ref(refs, "q3")
    _, q4 = resolve_ref(refs, "q4")
    _, q5 = resolve_ref(refs, "q5")
    _, q6 = resolve_ref(refs, "q6")
    _, q7 = resolve_ref(refs, "q7")
    _, phase = resolve_ref(refs, "phase_policy")

    # Accepted Logistics provenance.
    require(h9["metadata"]["status"] == "accepted", "H9 acceptance status drift")
    require(h9["scope"]["task_id"] == "H9", "H9 task id drift")
    require(h9["scope"]["module_id"] == "logistics_service", "H9 module id drift")
    require(h9["operator_decision"]["decision"] == "ACCEPT", "H9 operator acceptance missing")
    require(h9["operator_decision"]["explicit_operator_input"] is True, "H9 acceptance not explicit")
    require(h9["operator_decision"]["automatic_acceptance"] is False, "H9 automatic acceptance drift")
    require(h9["subject"]["repository"] == "forprint_logistics_service", "H9 subject repository drift")
    require(
        h9["subject"]["implementation_commit"] == "4a3a8cf3d2809c3a7f49268fa62334ed24b5fa90",
        "H9 implementation provenance drift",
    )
    require(
        h9["subject"]["publication_seal_commit"] == "96284d829bb5cdcd564f44c51bdbe681f9d26cae",
        "H9 publication seal drift",
    )
    require(h9["subject"]["remote_containment_verified"] is True, "H9 remote containment lost")
    require(h9["acceptance_evidence"]["domain_runtime_changes"] is False, "H9 domain runtime changed")
    require(
        h9["acceptance_evidence"]["blueprint_repository_write_during_module_execution"] is False,
        "H9 Blueprint write boundary drift",
    )
    require(h9["acceptance_evidence"]["business_prompt_claim_created"] is False, "H9 business prompt claim drift")
    require(h9["decision_effect"]["logistics_business_prompt_released"] is False, "H9 business prompt release drift")

    # Prior Logistics reference validation.
    require(
        b1["decision"]["result"] == "B1_LOGISTICS_REFERENCE_VALIDATION_PASS",
        "B1 Logistics reference validation no longer PASS",
    )
    require(b1["decision"]["logistics_reference_validation_complete"] is True, "B1 Logistics validation incomplete")
    e2e = b1["evidence"]["e2e_validation"]
    require(e2e["lifecycle_scenarios_passed"] == 9, "B1 Logistics passed-scenario count drift")
    require(e2e["lifecycle_scenarios_total"] == 9, "B1 Logistics total-scenario count drift")
    require(e2e["invalid_events"] == 0, "B1 Logistics invalid events present")
    require(e2e["source_errors"] == 0, "B1 Logistics source errors present")
    require(e2e["decision_evidence_errors"] == 0, "B1 Logistics decision evidence errors present")
    require(e2e["discovery_idempotent"] is True, "B1 Logistics discovery not idempotent")
    require(e2e["discovery_read_only"] is True, "B1 Logistics discovery not read-only")
    require(e2e["live_blueprint_unchanged"] is True, "B1 validation mutated Blueprint")
    require(e2e["live_logistics_unchanged"] is True, "B1 validation mutated Logistics")
    require(b1["evidence"]["final_project_gate"]["blockers"] == 0, "B1 Logistics blockers present")

    assertions = data["reference_assertions"]
    expected_assertions = {
        "recoverable_clarification_does_not_return_prompt",
        "module_and_operator_routing_identities_representable",
        "five_round_escalation_deterministic",
        "blocker_reason_explicit",
        "released_prompt_immutable",
        "scope_adjustment_separate_evidence",
        "completion_preserves_deviations",
        "attention_state_visible",
        "no_automatic_module_business_prompt_accept",
        "no_unbounded_or_cross_phase_automatic_next_release",
        "no_blueprint_write_into_module_repo",
    }
    require(set(assertions) == expected_assertions, "Q8 reference assertion set drift")
    require(all(value is True for value in assertions.values()), "Q8 assertion not PASS")

    # Q1: recoverable clarification is not RETURN/HOLD.
    require(q1["core_rule"]["question_creation_implies_return"] is False, "Q1 question implies RETURN")
    require(q1["core_rule"]["question_creation_implies_hold"] is False, "Q1 question implies HOLD")
    require(q1["prompt_coupling"]["prompt_status_may_remain"] == "in_progress", "Q1 in-progress path lost")
    require(q1["prompt_coupling"]["condition_is_return"] is False, "Q1 waiting condition became RETURN")
    require(q1["prompt_coupling"]["condition_is_hold"] is False, "Q1 waiting condition became HOLD")

    # Q2: exact five-round deterministic escalation.
    rb = q2["round_budget"]
    require(rb["maximum_unresolved_round_trips_per_question_thread"] == 5, "Q2 round limit drift")
    require(rb["scope"] == "per_question_thread", "Q2 round limit not per thread")
    require(rb["round_six_allowed"] is False, "Q2 round six allowed")
    require(rb["round_advances_only_after"] == "completed_answer_attempt_evaluated_insufficient", "Q2 round semantics drift")
    require(q2["escalation"]["trigger"] == "round_5_completed_and_evaluated_insufficient", "Q2 escalation trigger drift")
    require(q2["escalation"]["resulting_thread_state"] == "ESCALATED", "Q2 escalation state drift")

    # Q3: explicit blocker reason and affected scope.
    blocker = q3["blocker_record"]
    require("reason_code" in blocker["required_fields"], "Q3 blocker reason_code not required")
    require(q3["reason_taxonomy"]["unknown_reason_allowed"] is False, "Q3 unknown blocker reason allowed")
    require(q3["blocking_semantics"]["blocking_applies_only_to_declared_affected_scope"] is True, "Q3 scope binding lost")
    require(q3["blocking_semantics"]["whole_prompt_block_requires_explicit_whole_prompt_scope"] is True, "Q3 whole-prompt scope implicit")

    # Q4: immutable prompt, separate adjustment evidence, completion deviations.
    imm = q4["released_prompt_immutability"]
    require(imm["released_prompt_is_immutable_execution_contract"] is True, "Q4 prompt immutability lost")
    require(imm["post_release_change_requires_correlated_artifact"] is True, "Q4 change artifact requirement lost")
    require("scope_adjustment" in q4["artifact_model"]["canonical_artifact_types"], "Q4 scope_adjustment missing")
    require(q4["artifact_model"]["published_artifacts_append_only"] is True, "Q4 artifacts not append-only")
    completion = q4["completion_reporting"]
    require(completion["required_section"] == "Execution deviations / operator decisions", "Q4 completion deviations section drift")
    require(completion["section_omission_allowed"] is False, "Q4 deviations section may be omitted")
    require(completion["explicit_none_allowed"] is True, "Q4 explicit none lost")

    # Q5/Q6: visible attention semantics, no transport/runtime coupling.
    require("operator_attention" in q5["event_type"]["canonical_initial_families"], "Q5 operator_attention family missing")
    require(q5["immutability_and_projection"]["events_are_immutable_observations"] is True, "Q5 event immutability lost")
    lifecycle = q6["attention_lifecycle"]
    require(lifecycle["states"] == ["OPEN", "ACKNOWLEDGED", "RESOLVED", "CANCELLED"], "Q6 attention states drift")
    require(lifecycle["acknowledged_is_resolution"] is False, "Q6 ACK became resolution")
    require(lifecycle["acknowledged_is_prompt_acceptance"] is False, "Q6 ACK became acceptance")
    require(lifecycle["acknowledged_is_transport_receipt"] is False, "Q6 ACK became transport receipt")
    require(q6["transport_independence"]["attention_state_independent_from_transport"] is True, "Q6 attention coupled to transport")
    require(q6["transport_independence"]["telegram_transport_defined_by_q6"] is False, "Q6 Telegram transport enabled")

    # Q7: representable routes, evidence-backed answer, no cross-repo writes.
    routing = q7["routing"]
    require(
        routing["route_directions"]
        == ["module_to_blueprint_or_operator", "module_to_module", "blueprint_to_module"],
        "Q7 route directions drift",
    )
    require(q7["answer_evidence"]["evidence_refs_min_items"] == 1, "Q7 answer evidence minimum drift")
    require(q7["answer_evidence"]["answer_without_evidence_refs_valid"] is False, "Q7 evidence-free answer allowed")
    require(all(value is False for value in q7["cross_repository_boundary"].values()), "Q7 cross-repo write enabled")
    require(q7["round_budget"]["routing_alone_consumes_round"] is False, "Q7 routing consumes round")
    require(q7["round_budget"]["rerouting_alone_consumes_round"] is False, "Q7 rerouting consumes round")

    # Phase boundary: Q8 -> H10 is manual and not silently crossable.
    require(
        phase["q_track"]["q8_to_h10_manual_phase_boundary_confirmation_required"] is True,
        "Q8->H10 manual boundary protection lost",
    )
    require("Q->H10" in phase["manual_progress_confirmation"]["required_at_boundaries"], "Q->H10 boundary missing")
    require(phase["manual_progress_confirmation"]["silence_counts_as_boundary_approval"] is False, "silence became phase approval")

    capabilities = data["current_capabilities"]
    require(capabilities and all(value is False for value in capabilities.values()), f"forbidden capability enabled: {capabilities}")

    acceptance = data["acceptance"]
    require(acceptance and all(value is True for value in acceptance.values()), "Q8 acceptance incomplete")


def main() -> int:
    data = load(CONTRACT)
    validate(data)
    print("Q8 Logistics clarification reference validation PASSED")
    print("canonical_reference_assertions=11")
    print("h9_logistics_reference_accepted=true")
    print("b1_logistics_reference_validation=PASS_9_OF_9")
    print("recoverable_clarification_does_not_return_prompt=true")
    print("routing_identities_representable=true")
    print("five_round_escalation_deterministic=true")
    print("blocker_reason_explicit=true")
    print("released_prompt_immutable=true")
    print("scope_adjustment_separate_evidence=true")
    print("completion_preserves_deviations=true")
    print("attention_state_visible=true")
    print("automatic_module_business_accept=false")
    print("q8_to_h10_manual_phase_boundary=true")
    print("blueprint_write_into_module_repo=false")
    print("live_runtime=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
