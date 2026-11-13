#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/common_coordination_event_envelope_v0_1.yaml"


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
    require(meta["hardening_slice"] == "Q5", "hardening slice must be Q5")
    require(
        meta["stable_id"] == "blueprint_v0_4_1_common_coordination_event_envelope_v0_1",
        "Q5 stable id drift",
    )

    inherits = data["inherits"]
    for key in (
        "q1_contract_path",
        "q2_contract_path",
        "q3_contract_path",
        "q4_contract_path",
    ):
        path = ROOT / inherits[key]
        require(path.is_file(), f"inherited contract missing: {path}")
        sha_key = key.replace("_path", "_sha256")
        require(sha(path) == inherits[sha_key], f"inherited contract SHA drift: {path}")

    envelope = data["envelope"]
    expected_fields = {
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
    require(set(envelope["required_fields"]) == expected_fields, "envelope field set drift")
    require(
        set(envelope["nullable_fields"])
        == {"module_id", "prompt_id", "roadmap_step_id", "causation_id"},
        "nullable field set drift",
    )
    require(envelope["exact_envelope_field_count"] == 17, "envelope field count drift")
    require(envelope["unknown_envelope_fields_allowed"] is False, "unknown envelope fields allowed")
    require(envelope["blocking_type"] == "boolean", "blocking must be boolean")
    require(envelope["payload_type"] == "mapping", "payload must be mapping")
    require(envelope["evidence_refs_type"] == "list", "evidence refs must be list")
    require(envelope["secret_values_allowed"] is False, "secret values allowed")
    require(envelope["secret_references_allowed"] is True, "secret refs unexpectedly forbidden")

    event_type = data["event_type"]
    require(event_type["format"] == "<family>.<action>", "event type format drift")
    require(event_type["family_action_lowercase_token_required"] is True, "event type token policy drift")
    expected_families = {
        "claim_status",
        "clarification",
        "answer_resolution",
        "execution_blocker",
        "unable_to_execute",
        "operator_attention",
        "operator_decision",
        "completion_publication",
    }
    require(set(event_type["canonical_initial_families"]) == expected_families, "event family set drift")
    require(event_type["initial_family_count"] == 8, "event family count drift")
    require(event_type["unknown_family_allowed"] is False, "unknown family silently allowed")
    require(event_type["new_family_requires_versioned_review"] is True, "new family review disabled")

    immutable = data["immutability_and_projection"]
    require(immutable["events_are_immutable_observations"] is True, "events not immutable observations")
    require(immutable["published_event_edit_allowed"] is False, "published event edit allowed")
    require(immutable["published_event_delete_allowed"] is False, "published event delete allowed")
    require(immutable["correction_requires_new_event"] is True, "event correction may rewrite")
    require(immutable["current_state_is_projection"] is True, "state not projection")
    require(immutable["projection_is_independent_source_of_truth"] is False, "projection became source of truth")
    require(immutable["q5_projection_engine_implemented"] is False, "Q5 implemented projection engine")
    require(immutable["occurred_at_is_total_order"] is False, "occurred_at incorrectly treated as total order")
    require(immutable["journal_order_field_added_to_envelope"] is False, "extra journal order field added")

    corr = data["correlation_and_causation"]
    require(corr["correlation_id_required"] is True, "correlation id not required")
    require(corr["causation_id_nullable"] is True, "root event causation not nullable")
    require(corr["nonnull_causation_refs_immediate_predecessor_event_id"] is True, "causation semantics drift")
    require(corr["fabricate_unknown_causation_allowed"] is False, "unknown cause fabrication allowed")
    require(corr["correlation_implies_direct_causation"] is False, "correlation conflated with causation")

    idem = data["idempotency"]
    require(idem["idempotency_key_required"] is True, "idempotency key not required")
    require(idem["same_logical_retry_reuses_key"] is True, "retry key reuse disabled")
    require(idem["same_key_equivalent_content_is_duplicate_attempt"] is True, "duplicate semantics drift")
    require(idem["same_key_materially_different_content_is_conflict"] is True, "collision not conflict")
    require(idem["conflict_fail_closed"] is True, "idempotency collision not fail closed")
    require(idem["new_key_to_bypass_conflict_allowed"] is False, "idempotency conflict bypass allowed")
    require(idem["q5_idempotency_store_implemented"] is False, "Q5 implemented idempotency store")

    time = data["time_semantics"]
    require(time["occurred_at_utc_required"] is True, "UTC not required")
    require(time["offset_aware_required"] is True, "offset-aware time not required")
    require(set(time["canonical_utc_suffixes"]) == {"Z", "+00:00"}, "UTC suffix policy drift")
    require(time["local_naive_timestamp_allowed"] is False, "naive timestamp allowed")

    semantic = data["semantic_boundaries"]
    require(semantic["event_is_prompt_disposition"] is False, "event became prompt disposition")
    require(semantic["blocking_implies_return"] is False, "blocking implies RETURN")
    require(semantic["blocking_implies_hold"] is False, "blocking implies HOLD")
    require(semantic["blocking_implies_accept"] is False, "blocking implies ACCEPT")
    require(semantic["blocking_implies_whole_prompt_block"] is False, "blocking implies whole-prompt block")
    require(semantic["severity_implies_operator_notification"] is False, "severity implies notification")
    require(semantic["severity_is_authority_grant"] is False, "severity became authority grant")
    require(semantic["operator_attention_semantics_defined_by_q5"] is False, "Q5 consumed Q6")
    require(semantic["cross_module_routing_defined_by_q5"] is False, "Q5 consumed Q7")
    require(semantic["payload_may_rewrite_q1_q4_history"] is False, "payload may rewrite Q1-Q4")
    require(semantic["event_replaces_git_project_truth"] is False, "event replaced Git truth")
    require(semantic["completion_publication_is_operator_acceptance"] is False, "completion event became ACCEPT")

    ownership = data["family_ownership"]
    require(set(ownership) == expected_families, "family ownership set drift")
    require(ownership["clarification"]["authoritative_contract"] == "Q1_Q2", "clarification ownership drift")
    require(ownership["execution_blocker"]["authoritative_contract"] == "Q3", "blocker ownership drift")
    require(ownership["unable_to_execute"]["is_blueprint_disposition"] is False, "unable_to_execute became disposition")
    require(ownership["operator_decision"]["authoritative_contract"] == "Q4", "decision ownership drift")
    require(ownership["operator_attention"]["semantic_owner"] == "Q6", "attention owner drift")
    require(ownership["operator_attention"]["transport_implemented_by_q5"] is False, "Q5 attention transport enabled")

    evidence = data["evidence_and_payload"]
    require(evidence["payload_mapping_required"] is True, "payload mapping not required")
    require(evidence["large_logs_embedded_by_default"] is False, "large logs embedded")
    require(evidence["family_payloads_versioned"] is True, "payload versioning disabled")
    require(evidence["canonical_artifact_may_be_referenced"] is True, "canonical artifact refs disabled")
    require(evidence["event_silently_replaces_canonical_artifact"] is False, "event replaces canonical artifact")

    deferred = data["deferred_boundaries"]
    require(
        set(deferred)
        == {
            "Q6_operator_attention_semantics",
            "Q7_cross_module_routing_mechanics",
            "Q8_logistics_reference_validation",
        },
        "deferred boundary set drift",
    )
    require(all(deferred.values()), "deferred Q work consumed")

    caps = data["current_capabilities"]
    require(caps and all(value is False for value in caps.values()), f"forbidden capability enabled: {caps}")

    acceptance = data["acceptance"]
    require(acceptance and all(value is True for value in acceptance.values()), "Q5 acceptance incomplete")


def main() -> int:
    data = load(CONTRACT)
    validate(data)
    print("Q5 common coordination event envelope validation PASSED")
    print("canonical_envelope_fields=17")
    print("canonical_initial_event_families=8")
    print("event_type_format=<family>.<action>")
    print("events_are_immutable_observations=true")
    print("current_state_is_projection=true")
    print("correlation_id_required=true")
    print("causation_id_nullable=true")
    print("idempotency_conflict_fail_closed=true")
    print("blocking_implies_return_hold_accept=false")
    print("operator_attention_semantics_defined_by_q5=false")
    print("live_sqlite_runtime_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
