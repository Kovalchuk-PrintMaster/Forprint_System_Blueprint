#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/immutable_prompt_adjustment_and_decision_v0_1.yaml"


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
    require(meta["hardening_slice"] == "Q4", "hardening slice must be Q4")
    require(
        meta["stable_id"] == "blueprint_v0_4_1_immutable_prompt_adjustment_and_decision_v0_1",
        "Q4 stable id drift",
    )

    inherits = data["inherits"]
    for key in ("q1_contract_path", "q2_contract_path", "q3_contract_path"):
        path = ROOT / inherits[key]
        require(path.is_file(), f"inherited contract missing: {path}")
        sha_key = key.replace("_path", "_sha256")
        require(sha(path) == inherits[sha_key], f"inherited contract SHA drift: {path}")

    immutable = data["released_prompt_immutability"]
    require(immutable["released_prompt_is_immutable_execution_contract"] is True, "prompt immutability lost")
    require(immutable["edit_released_requirements_allowed"] is False, "released requirements editable")
    require(immutable["delete_released_requirements_allowed"] is False, "released requirements deletable")
    require(immutable["silent_rewrite_allowed"] is False, "silent rewrite allowed")
    require(immutable["post_release_change_requires_correlated_artifact"] is True, "change artifact not required")
    require(immutable["unexecuted_requirement_may_disappear"] is False, "requirement may disappear")

    expected_types = {
        "operator_decision",
        "scope_adjustment",
        "waiver",
        "skip_optional",
        "clarification_resolution",
        "blocker_resolution",
        "cancellation",
        "follow_up_prompt",
        "superseding_prompt",
    }
    artifacts = data["artifact_model"]
    require(set(artifacts["canonical_artifact_types"]) == expected_types, "artifact type set drift")
    require(artifacts["published_artifacts_append_only"] is True, "decision artifacts not append-only")
    require(artifacts["correction_rewrites_prior_artifact"] is False, "correction rewrites prior artifact")
    require(artifacts["correction_uses_superseding_artifact"] is True, "superseding correction missing")

    required = {
        "decision_id",
        "artifact_type",
        "prompt_id",
        "module_id",
        "roadmap_step_id",
        "correlation_id",
        "target_refs",
        "actor",
        "reason_code",
        "explanation",
        "execution_effect",
        "acceptance_effect",
        "evidence_refs",
        "decided_at",
    }
    require(set(artifacts["required_fields"]) == required, "Q4 required field set drift")
    require(
        set(artifacts["optional_fields"])
        == {
            "execution_id",
            "related_question_id",
            "related_blocker_id",
            "related_event_id",
            "supersedes_decision_id",
        },
        "Q4 optional field set drift",
    )
    require(artifacts["target_refs_min_items"] == 1, "target refs may be empty")
    require(artifacts["evidence_refs_required"] is True, "decision evidence not required")
    require(artifacts["whole_prompt_effect_requires_explicit_whole_prompt_target"] is True, "whole prompt scope implicit")
    require(artifacts["secret_values_allowed"] is False, "secret values allowed")

    exec_effects = set(data["execution_effects"]["values"])
    require(
        exec_effects
        == {
            "no_execution_change",
            "clarify_only",
            "apply_scope_adjustment",
            "skip_optional",
            "resume_affected_scope",
            "cancel_affected_scope",
            "cancel_prompt",
            "require_follow_up_prompt",
            "supersede_prompt",
        },
        "execution effect vocabulary drift",
    )
    require(data["execution_effects"]["effect_is_authority_grant"] is False, "execution effect became authority grant")

    acceptance_effects = set(data["acceptance_effects"]["values"])
    require(
        acceptance_effects
        == {
            "no_acceptance_change",
            "acceptance_scope_adjusted",
            "waived_requirement",
            "optional_item_excluded",
            "completion_requires_follow_up",
            "prompt_cancelled",
            "prompt_superseded",
        },
        "acceptance effect vocabulary drift",
    )
    require(
        data["acceptance_effects"]["effect_is_automatic_prompt_acceptance"] is False,
        "acceptance effect became automatic ACCEPT",
    )

    authority = data["authority_boundary"]
    require(
        set(authority["manual_authority_required_artifact_types"])
        == {
            "operator_decision",
            "scope_adjustment",
            "waiver",
            "skip_optional",
            "cancellation",
            "superseding_prompt",
        },
        "manual authority artifact set drift",
    )
    require(authority["scope_adjustment_manual"] is True, "scope adjustment not manual")
    require(authority["waiver_manual"] is True, "waiver not manual")
    require(authority["waiver_inferred_from_omission"] is False, "waiver inferred from omission")
    require(authority["waiver_inferred_from_unable_to_execute"] is False, "waiver inferred from inability")
    require(authority["clarification_resolution_may_bypass_manual_scope_change"] is False, "clarification bypasses scope authority")
    require(authority["blocker_resolution_may_bypass_manual_scope_change"] is False, "blocker bypasses scope authority")
    require(authority["follow_up_prompt_auto_release"] is False, "follow-up prompt auto releases")

    semantics = data["artifact_semantics"]
    require(semantics["skip_optional_required_target_allowed"] is False, "skip_optional can skip required work")
    require(semantics["clarification_resolution_rewrites_q1_q2_history"] is False, "Q1/Q2 history rewritable")
    require(semantics["material_clarification_change_requires_additional_adjustment_artifact"] is True, "material clarification can silently change scope")
    require(semantics["blocker_resolution_rewrites_q3_history"] is False, "Q3 blocker history rewritable")
    require(semantics["superseded_prompt_history_deleted"] is False, "superseded prompt history deleted")

    correlation = data["correlation"]
    require(correlation["correlation_id_required"] is True, "correlation id not required")
    require(
        set(correlation["typed_optional_refs"])
        == {
            "related_question_id",
            "related_blocker_id",
            "related_event_id",
            "supersedes_decision_id",
        },
        "correlation ref set drift",
    )
    require(correlation["q5_causation_id_defined_by_q4"] is False, "Q4 consumed Q5 causation")
    require(correlation["event_envelope_defined_by_q4"] is False, "Q4 consumed Q5 event envelope")

    completion = data["completion_reporting"]
    require(
        completion["required_section"] == "Execution deviations / operator decisions",
        "completion section name drift",
    )
    require(completion["section_omission_allowed"] is False, "completion section may be omitted")
    require(completion["explicit_none_allowed"] is True, "explicit none not allowed")
    require(completion["decision_ids_required_when_present"] is True, "decision IDs not required in report")
    require(completion["target_refs_required_when_present"] is True, "target refs not required in report")

    deferred = data["deferred_boundaries"]
    require(
        set(deferred)
        == {
            "Q5_common_event_envelope",
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
    require(acceptance and all(value is True for value in acceptance.values()), "Q4 acceptance incomplete")


def main() -> int:
    data = load(CONTRACT)
    validate(data)
    print("Q4 immutable prompt adjustment and operator decision validation PASSED")
    print("released_prompt_immutable=true")
    print("canonical_artifact_types=9")
    print("unexecuted_requirement_may_disappear=false")
    print("scope_adjustment_manual=true")
    print("waiver_manual=true")
    print("completion_deviations_section_required=true")
    print("automatic_prompt_acceptance=false")
    print("automatic_follow_up_prompt_release=false")
    print("q5_event_envelope_defined_by_q4=false")
    print("live_sqlite_runtime_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
