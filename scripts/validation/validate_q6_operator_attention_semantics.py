#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/operator_attention_semantics_v0_1.yaml"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"{path}: root must be mapping")
    return data


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(data: dict) -> None:
    meta = data["metadata"]
    require(meta["hardening_slice"] == "Q6", "hardening slice drift")
    require(meta["stable_id"] == "blueprint_v0_4_1_operator_attention_semantics_v0_1", "stable id drift")

    inherits = data["inherits"]
    for key in ("q1_contract_path", "q2_contract_path", "q3_contract_path", "q4_contract_path", "q5_contract_path"):
        path = ROOT / inherits[key]
        require(path.is_file(), f"missing inherited contract: {path}")
        require(sha(path) == inherits[key.replace("_path", "_sha256")], f"inherited SHA drift: {path}")

    expected_reasons = {
        "clarification_escalated", "access_required", "execution_blocked", "unable_to_execute",
        "no_dispatchable_work", "operator_execution_required", "operator_acceptance_required",
        "manual_review_required", "coordination_freshness_stale", "dependency_blocked",
        "repeated_verification_failure",
    }
    reasons = data["attention_reasons"]
    require(set(reasons["canonical_reasons"]) == expected_reasons, "attention reasons drift")
    require(reasons["canonical_reason_count"] == 11, "attention reason count drift")
    require(reasons["unknown_reason_allowed"] is False, "unknown attention reason allowed")
    require(set(reasons["definitions"]) == expected_reasons, "reason definitions incomplete")

    lifecycle = data["attention_lifecycle"]
    require(lifecycle["states"] == ["OPEN", "ACKNOWLEDGED", "RESOLVED", "CANCELLED"], "states drift")
    require(set(lifecycle["allowed_transitions"]) == {
        "OPEN->ACKNOWLEDGED", "OPEN->RESOLVED", "OPEN->CANCELLED",
        "ACKNOWLEDGED->RESOLVED", "ACKNOWLEDGED->CANCELLED",
    }, "transitions drift")
    require(lifecycle["acknowledged_is_resolution"] is False, "ACK became resolution")
    require(lifecycle["acknowledged_is_prompt_acceptance"] is False, "ACK became acceptance")
    require(lifecycle["acknowledged_is_transport_receipt"] is False, "ACK became receipt")
    require(lifecycle["resolved_requires_evidence"] is True, "resolution evidence missing")
    require(lifecycle["cancelled_means_underlying_issue_resolved"] is False, "cancelled became resolved")

    q5 = data["q5_event_integration"]
    require(q5["family"] == "operator_attention", "Q5 family drift")
    require(q5["canonical_actions"] == ["opened", "acknowledged", "refreshed", "resolved", "cancelled"], "actions drift")
    require(q5["adds_fields_to_q5_envelope"] is False, "Q6 changed Q5 envelope")
    require(set(q5["required_payload_fields"]) == {
        "attention_id", "reason", "attention_state", "subject_refs",
        "attention_owner", "requested_action", "resolution_criteria",
    }, "payload required fields drift")
    require(q5["subject_refs_min_items"] == 1, "empty subject refs allowed")
    require(q5["attention_id_stable_per_thread"] is True, "attention identity unstable")
    require(q5["reason_change_requires_new_attention_id"] is True, "reason can mutate")
    require(q5["published_events_immutable"] is True, "attention events mutable")

    severity = data["severity_semantics"]
    require(severity["values"] == ["notice", "action_required", "urgent", "critical"], "severity drift")
    require(severity["severity_grants_authority"] is False, "severity grants authority")
    require(severity["severity_implies_return_hold_accept"] is False, "severity implies disposition")
    require(severity["critical_inferred_from_reason_alone"] is False, "critical inferred")
    require(severity["critical_requires_explicit_evidence"] is True, "critical evidence missing")

    blocking = data["blocking_semantics"]
    require(blocking["attention_itself_creates_blocking"] is False, "attention creates blocking")
    require(blocking["q5_blocking_reflects_underlying_contract"] is True, "blocking ownership drift")
    require(blocking["blocking_true_implies_whole_prompt_block"] is False, "blocking widened")
    require(blocking["blocking_true_implies_return_hold_accept"] is False, "blocking implies disposition")
    require(blocking["acknowledgement_clears_blocking"] is False, "ACK clears blocking")

    transport = data["transport_independence"]
    require(transport["attention_state_independent_from_transport"] is True, "transport coupled")
    require(transport["telegram_transport_defined_by_q6"] is False, "Telegram enabled")
    require(transport["delivery_receipt_is_semantic_ack"] is False, "delivery became ACK")
    require(transport["read_receipt_is_semantic_ack"] is False, "read became ACK")
    require(transport["api_success_is_semantic_ack"] is False, "API success became ACK")
    require(transport["transport_retry_changes_attention_state"] is False, "retry changes attention")

    resolution = data["resolution_semantics"]
    require(resolution["resolution_requires_same_attention_id"] is True, "resolution identity drift")
    require(resolution["resolution_requires_q5_evidence_refs"] is True, "resolution evidence missing")
    require(resolution["q1_q2_truth_may_be_fabricated_by_q6"] is False, "Q6 fabricates Q1/Q2")
    require(resolution["q3_truth_may_be_fabricated_by_q6"] is False, "Q6 fabricates Q3")
    require(resolution["q4_truth_may_be_fabricated_by_q6"] is False, "Q6 fabricates Q4")
    require(resolution["refresh_rewrites_prior_event"] is False, "refresh rewrites history")
    require(resolution["refresh_may_change_reason"] is False, "refresh changes reason")

    constraints = data["reason_constraints"]
    require(constraints["clarification_escalated"]["related_question_id_required"] is True, "question link missing")
    require(constraints["execution_blocked"]["related_blocker_id_required"] is True, "blocker link missing")
    require(constraints["unable_to_execute"]["related_report_id_required"] is True, "report link missing")
    require(constraints["no_dispatchable_work"]["implies_project_complete"] is False, "no work means project complete")
    require(constraints["operator_acceptance_required"]["attention_is_acceptance"] is False, "attention became acceptance")
    require(constraints["dependency_blocked"]["authorizes_dependency_override"] is False, "override authorized")
    require(constraints["coordination_freshness_stale"]["implies_incompatibility"] is False, "stale became incompatible")
    require(constraints["access_required"]["secret_values_allowed"] is False, "secrets allowed")

    require(all(data["deferred_boundaries"].values()), "deferred Q work consumed")
    require(all(value is False for value in data["current_capabilities"].values()), "runtime capability enabled")
    require(all(data["acceptance"].values()), "Q6 acceptance incomplete")


def main() -> int:
    validate(load(CONTRACT))
    print("Q6 operator attention semantics validation PASSED")
    print("canonical_attention_reasons=11")
    print("attention_states=OPEN,ACKNOWLEDGED,RESOLVED,CANCELLED")
    print("q5_operator_attention_actions=5")
    print("attention_state_independent_from_transport=true")
    print("acknowledgement_is_resolution=false")
    print("acknowledgement_is_prompt_acceptance=false")
    print("delivery_receipt_is_semantic_ack=false")
    print("resolution_requires_evidence=true")
    print("telegram_transport_enabled=false")
    print("live_sqlite_runtime_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
