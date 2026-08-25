#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/execution_blocker_taxonomy_v0_1.yaml"


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
    require(meta["hardening_slice"] == "Q3", "hardening slice must be Q3")
    require(
        meta["stable_id"] == "blueprint_v0_4_1_execution_blocker_taxonomy_v0_1",
        "Q3 stable id drift",
    )

    inherits = data["inherits"]
    for key in ("q1_contract_path", "q2_contract_path"):
        path = ROOT / inherits[key]
        require(path.is_file(), f"inherited contract missing: {path}")
        sha_key = key.replace("_path", "_sha256")
        require(sha(path) == inherits[sha_key], f"inherited contract SHA drift: {path}")

    sep = data["semantic_separation"]
    require(
        sep["coordination_conditions"] == ["clarification_required", "execution_blocked"],
        "coordination condition vocabulary drift",
    )
    require(
        sep["executor_outcomes"] == ["unable_to_execute"],
        "executor outcome vocabulary drift",
    )
    require(
        sep["governance_dispositions"] == ["RETURN", "HOLD"],
        "governance disposition vocabulary drift",
    )
    require(sep["conditions_are_prompt_dispositions"] is False, "conditions became dispositions")
    require(sep["unable_to_execute_is_prompt_disposition"] is False, "unable_to_execute became disposition")
    require(sep["automatic_condition_to_return_hold"] is False, "automatic RETURN/HOLD mapping enabled")
    require(sep["released_prompt_mutation_allowed"] is False, "blocker may mutate released prompt")

    expected_reasons = {
        "missing_input",
        "ambiguous_requirement",
        "access_required",
        "credential_or_token_expired",
        "external_resource_unavailable",
        "dependency_contract_missing",
        "dependency_module_blocked",
        "provider_api_unavailable",
        "environment_failure",
        "policy_conflict",
        "unsupported_capability",
        "security_boundary",
        "manual_decision_required",
    }
    reasons = data["reason_taxonomy"]
    require(set(reasons["canonical_reason_codes"]) == expected_reasons, "reason-code set drift")
    require(reasons["reason_code_is_prompt_disposition"] is False, "reason code became disposition")
    require(reasons["unknown_reason_allowed"] is False, "unknown reason silently allowed")
    require(set(reasons["definitions"]) == expected_reasons, "reason definitions incomplete")
    for reason, definition in reasons["definitions"].items():
        require(isinstance(definition, str) and definition.strip(), f"empty reason definition: {reason}")

    blocker = data["blocker_record"]
    expected_fields = {
        "blocker_id",
        "module_id",
        "prompt_id",
        "roadmap_step_id",
        "condition",
        "reason_code",
        "blocking",
        "affected_scope_refs",
        "summary",
        "evidence_refs",
        "created_at",
    }
    require(set(blocker["required_fields"]) == expected_fields, "blocker required fields drift")
    require(set(blocker["optional_fields"]) == {"execution_id", "related_question_id"}, "optional fields drift")
    require(blocker["condition_values"] == ["clarification_required", "execution_blocked"], "condition values drift")
    require(blocker["affected_scope_refs_min_items"] == 1, "affected scope must be non-empty")
    require(blocker["evidence_refs_required"] is True, "blocker evidence refs must be required")
    require(blocker["secret_values_allowed"] is False, "secret values allowed")
    require(blocker["secret_references_allowed"] is True, "secret references unexpectedly forbidden")

    blocking = data["blocking_semantics"]
    require(blocking["execution_blocked_requires_blocking_true"] is True, "execution_blocked not necessarily blocking")
    require(blocking["clarification_required_may_be_blocking_or_nonblocking"] is True, "clarification flexibility lost")
    require(blocking["blocking_applies_only_to_declared_affected_scope"] is True, "blocking scope widened")
    require(blocking["whole_prompt_block_requires_explicit_whole_prompt_scope"] is True, "whole prompt block implicit")
    require(blocking["independent_work_may_continue_when_contract_allows"] is True, "independent work forbidden")
    require(blocking["active_blocker_mutates_released_prompt"] is False, "blocker mutates released prompt")
    require(blocking["active_blocker_implies_return"] is False, "blocker implies RETURN")
    require(blocking["active_blocker_implies_hold"] is False, "blocker implies HOLD")
    require(blocking["resolution_requires_evidence"] is True, "blocker resolution evidence not required")

    unable = data["unable_to_execute_evidence"]
    require(unable["is_executor_evidence"] is True, "unable_to_execute not executor evidence")
    require(unable["is_blueprint_decision"] is False, "unable_to_execute became Blueprint decision")
    require(unable["automatically_returns_prompt"] is False, "unable_to_execute auto RETURN")
    require(unable["automatically_holds_prompt"] is False, "unable_to_execute auto HOLD")
    require(
        set(unable["required_fields"])
        == {
            "report_id",
            "module_id",
            "prompt_id",
            "roadmap_step_id",
            "execution_id",
            "reason_code",
            "affected_scope_refs",
            "summary",
            "attempted_or_verified",
            "evidence_refs",
            "safe_next_options",
            "created_at",
        },
        "unable_to_execute evidence field set drift",
    )
    require(unable["safe_next_options_are_advisory"] is True, "safe next options became authority")

    q2 = data["q2_bridge"]
    require(q2["q2_question_thread_remains_authoritative"] is True, "Q2 authority lost")
    require(q2["q3_may_rewrite_q2_question_history"] is False, "Q3 may rewrite Q2 history")
    require(q2["escalated_blocking_question_may_project_execution_blocked"] is True, "Q2->Q3 projection disabled")
    require(q2["projection_requires_explicit_q3_reason"] is True, "Q2->Q3 reason not explicit")

    deferred = data["deferred_boundaries"]
    require(
        set(deferred)
        == {
            "Q4_operator_decision_adjustment_model",
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
    require(acceptance and all(value is True for value in acceptance.values()), "Q3 acceptance incomplete")


def main() -> int:
    data = load(CONTRACT)
    validate(data)
    print("Q3 execution blocker taxonomy validation PASSED")
    print("conditions=clarification_required,execution_blocked")
    print("executor_outcome=unable_to_execute")
    print("governance_dispositions=RETURN,HOLD")
    print("canonical_reason_codes=13")
    print("execution_blocked_requires_blocking_true=true")
    print("automatic_condition_to_return_hold=false")
    print("released_prompt_mutation_allowed=false")
    print("live_sqlite_runtime_enabled=false")
    print("autonomous_execution_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
