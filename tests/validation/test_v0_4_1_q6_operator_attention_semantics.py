from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/operator_attention_semantics_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q6_operator_attention_semantics.py"


def data() -> dict:
    value = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_exact_attention_reasons() -> None:
    reasons = data()["attention_reasons"]
    assert reasons["canonical_reason_count"] == 11
    assert set(reasons["canonical_reasons"]) == {
        "clarification_escalated", "access_required", "execution_blocked", "unable_to_execute",
        "no_dispatchable_work", "operator_execution_required", "operator_acceptance_required",
        "manual_review_required", "coordination_freshness_stale", "dependency_blocked",
        "repeated_verification_failure",
    }
    assert reasons["unknown_reason_allowed"] is False


def test_ack_is_not_resolution_acceptance_or_transport_receipt() -> None:
    lifecycle = data()["attention_lifecycle"]
    assert lifecycle["states"] == ["OPEN", "ACKNOWLEDGED", "RESOLVED", "CANCELLED"]
    assert lifecycle["acknowledged_is_resolution"] is False
    assert lifecycle["acknowledged_is_prompt_acceptance"] is False
    assert lifecycle["acknowledged_is_transport_receipt"] is False
    assert lifecycle["resolved_requires_evidence"] is True


def test_q5_attention_family_is_reused_without_envelope_change() -> None:
    q5 = data()["q5_event_integration"]
    assert q5["family"] == "operator_attention"
    assert q5["canonical_actions"] == ["opened", "acknowledged", "refreshed", "resolved", "cancelled"]
    assert q5["adds_fields_to_q5_envelope"] is False
    assert q5["attention_id_stable_per_thread"] is True
    assert q5["reason_change_requires_new_attention_id"] is True


def test_payload_identity_action_and_resolution_fields() -> None:
    q5 = data()["q5_event_integration"]
    assert set(q5["required_payload_fields"]) == {
        "attention_id", "reason", "attention_state", "subject_refs",
        "attention_owner", "requested_action", "resolution_criteria",
    }
    assert q5["subject_refs_min_items"] == 1


def test_severity_has_no_governance_authority() -> None:
    severity = data()["severity_semantics"]
    assert severity["values"] == ["notice", "action_required", "urgent", "critical"]
    assert severity["severity_grants_authority"] is False
    assert severity["severity_implies_return_hold_accept"] is False
    assert severity["critical_inferred_from_reason_alone"] is False
    assert severity["critical_requires_explicit_evidence"] is True


def test_transport_is_independent_from_attention_state() -> None:
    transport = data()["transport_independence"]
    assert transport["attention_state_independent_from_transport"] is True
    assert transport["telegram_transport_defined_by_q6"] is False
    assert transport["delivery_receipt_is_semantic_ack"] is False
    assert transport["read_receipt_is_semantic_ack"] is False
    assert transport["api_success_is_semantic_ack"] is False
    assert transport["transport_retry_changes_attention_state"] is False


def test_attention_neither_creates_nor_clears_underlying_blocking() -> None:
    blocking = data()["blocking_semantics"]
    assert blocking["attention_itself_creates_blocking"] is False
    assert blocking["q5_blocking_reflects_underlying_contract"] is True
    assert blocking["blocking_true_implies_whole_prompt_block"] is False
    assert blocking["blocking_true_implies_return_hold_accept"] is False
    assert blocking["acknowledgement_clears_blocking"] is False


def test_resolution_cannot_fabricate_q1_q4_truth() -> None:
    resolution = data()["resolution_semantics"]
    assert resolution["resolution_requires_same_attention_id"] is True
    assert resolution["resolution_requires_q5_evidence_refs"] is True
    assert resolution["q1_q2_truth_may_be_fabricated_by_q6"] is False
    assert resolution["q3_truth_may_be_fabricated_by_q6"] is False
    assert resolution["q4_truth_may_be_fabricated_by_q6"] is False
    assert resolution["refresh_rewrites_prior_event"] is False
    assert resolution["refresh_may_change_reason"] is False


def test_reason_constraints_preserve_authority() -> None:
    c = data()["reason_constraints"]
    assert c["clarification_escalated"]["related_question_id_required"] is True
    assert c["execution_blocked"]["related_blocker_id_required"] is True
    assert c["unable_to_execute"]["related_report_id_required"] is True
    assert c["no_dispatchable_work"]["implies_project_complete"] is False
    assert c["operator_acceptance_required"]["attention_is_acceptance"] is False
    assert c["dependency_blocked"]["authorizes_dependency_override"] is False
    assert c["coordination_freshness_stale"]["implies_incompatibility"] is False
    assert c["access_required"]["secret_values_allowed"] is False


def test_q7_q8_and_runtime_remain_deferred() -> None:
    value = data()
    assert all(value["deferred_boundaries"].values())
    assert all(flag is False for flag in value["current_capabilities"].values())


def test_human_standard_fragments() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "Attention state is semantic coordination state, not transport state and not governance authority.",
        "Canonical attention reasons", "`clarification_escalated`", "`no_dispatchable_work`",
        "`operator_acceptance_required`", "`repeated_verification_failure`", "Attention lifecycle",
        "`OPEN -> ACKNOWLEDGED -> RESOLVED`", "Acknowledgement means only", "It does **not** mean",
        "Q5 event integration", "`operator_attention.opened`", "Transport independence",
        "Operator acknowledgement versus transport acknowledgement", "Resolution evidence",
        "does not mean the project, phase or module is complete", "Separation from Q7-Q8", "Runtime boundary",
    ):
        assert fragment in text


def test_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q6 operator attention semantics validation PASSED" in cp.stdout


def test_validator_is_in_canonical_check_catalog() -> None:
    checks = {item.check_id: item for item in build_checks()}
    check = checks["q6_operator_attention_semantics_validation"]
    assert check.title == "Q6 operator attention semantics"
    assert check.command[-1] == "scripts/validation/validate_q6_operator_attention_semantics.py"
