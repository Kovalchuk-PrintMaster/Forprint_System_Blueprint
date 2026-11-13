from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/common_coordination_event_envelope_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q5_common_coordination_event_envelope.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_q5_envelope_field_set_is_exact() -> None:
    envelope = load_contract()["envelope"]
    assert set(envelope["required_fields"]) == {
        "event_id",
        "event_type",
        "occurred_at",
        "producer",
        "target",
        "module_id",
        "prompt_id",
        "roadmap_step_id",
        "correlation_id",
        "causation_id",
        "severity",
        "blocking",
        "schema_version",
        "payload",
        "evidence_refs",
        "idempotency_key",
    }
    assert envelope["exact_envelope_field_count"] == 17
    assert envelope["unknown_envelope_fields_allowed"] is False
    assert set(envelope["nullable_fields"]) == {
        "module_id",
        "prompt_id",
        "roadmap_step_id",
        "causation_id",
    }


def test_q5_initial_event_family_set_is_exact() -> None:
    event_type = load_contract()["event_type"]
    assert event_type["format"] == "<family>.<action>"
    assert set(event_type["canonical_initial_families"]) == {
        "claim_status",
        "clarification",
        "answer_resolution",
        "execution_blocker",
        "unable_to_execute",
        "operator_attention",
        "operator_decision",
        "completion_publication",
    }
    assert event_type["initial_family_count"] == 8
    assert event_type["unknown_family_allowed"] is False


def test_events_are_immutable_and_state_is_projection() -> None:
    model = load_contract()["immutability_and_projection"]
    assert model["events_are_immutable_observations"] is True
    assert model["published_event_edit_allowed"] is False
    assert model["published_event_delete_allowed"] is False
    assert model["correction_requires_new_event"] is True
    assert model["current_state_is_projection"] is True
    assert model["projection_is_independent_source_of_truth"] is False
    assert model["q5_projection_engine_implemented"] is False
    assert model["occurred_at_is_total_order"] is False
    assert model["journal_order_field_added_to_envelope"] is False


def test_correlation_causation_are_distinct() -> None:
    corr = load_contract()["correlation_and_causation"]
    assert corr["correlation_id_required"] is True
    assert corr["causation_id_nullable"] is True
    assert corr["nonnull_causation_refs_immediate_predecessor_event_id"] is True
    assert corr["fabricate_unknown_causation_allowed"] is False
    assert corr["correlation_implies_direct_causation"] is False


def test_idempotency_collision_fails_closed() -> None:
    idem = load_contract()["idempotency"]
    assert idem["idempotency_key_required"] is True
    assert idem["same_logical_retry_reuses_key"] is True
    assert idem["same_key_equivalent_content_is_duplicate_attempt"] is True
    assert idem["same_key_materially_different_content_is_conflict"] is True
    assert idem["conflict_fail_closed"] is True
    assert idem["new_key_to_bypass_conflict_allowed"] is False
    assert idem["q5_idempotency_store_implemented"] is False


def test_event_time_is_offset_aware_utc() -> None:
    time = load_contract()["time_semantics"]
    assert time["occurred_at_utc_required"] is True
    assert time["offset_aware_required"] is True
    assert set(time["canonical_utc_suffixes"]) == {"Z", "+00:00"}
    assert time["local_naive_timestamp_allowed"] is False


def test_blocking_and_severity_do_not_create_governance_authority() -> None:
    semantic = load_contract()["semantic_boundaries"]
    assert semantic["blocking_implies_return"] is False
    assert semantic["blocking_implies_hold"] is False
    assert semantic["blocking_implies_accept"] is False
    assert semantic["blocking_implies_whole_prompt_block"] is False
    assert semantic["severity_implies_operator_notification"] is False
    assert semantic["severity_is_authority_grant"] is False
    assert semantic["event_is_prompt_disposition"] is False


def test_q5_reserves_attention_family_but_defers_q6_semantics() -> None:
    data = load_contract()
    assert data["family_ownership"]["operator_attention"]["semantic_owner"] == "Q6"
    assert data["family_ownership"]["operator_attention"]["transport_implemented_by_q5"] is False
    assert data["semantic_boundaries"]["operator_attention_semantics_defined_by_q5"] is False


def test_q1_q4_histories_and_git_truth_are_not_rewritten() -> None:
    semantic = load_contract()["semantic_boundaries"]
    assert semantic["payload_may_rewrite_q1_q4_history"] is False
    assert semantic["event_replaces_git_project_truth"] is False
    assert semantic["completion_publication_is_operator_acceptance"] is False
    ownership = load_contract()["family_ownership"]
    assert ownership["clarification"]["authoritative_contract"] == "Q1_Q2"
    assert ownership["execution_blocker"]["authoritative_contract"] == "Q3"
    assert ownership["operator_decision"]["authoritative_contract"] == "Q4"


def test_q6_q8_and_runtime_remain_deferred() -> None:
    data = load_contract()
    assert all(data["deferred_boundaries"].values())
    assert all(value is False for value in data["current_capabilities"].values())


def test_human_standard_contains_required_q5_semantics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "Events are immutable observations; current state is a projection derived from events.",
        "Canonical envelope",
        "`event_id`",
        "`correlation_id`",
        "`causation_id`",
        "`idempotency_key`",
        "Initial canonical families",
        "`<family>.<action>`",
        "Immutable observation rule",
        "State projection rule",
        "Idempotency",
        "idempotency conflict",
        "occurred_at",
        "Q6 owns attention reasons",
        "does not automatically mean",
        "Separation from Q6-Q8",
        "Runtime boundary",
    ):
        assert fragment in text


def test_q5_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q5 common coordination event envelope validation PASSED" in cp.stdout


def test_q5_validator_is_in_canonical_check_catalog() -> None:
    checks = {check.check_id: check for check in build_checks()}
    check = checks["q5_common_coordination_event_envelope_validation"]
    assert check.title == "Q5 coordination event envelope"
    assert check.command[-1] == "scripts/validation/validate_q5_common_coordination_event_envelope.py"
