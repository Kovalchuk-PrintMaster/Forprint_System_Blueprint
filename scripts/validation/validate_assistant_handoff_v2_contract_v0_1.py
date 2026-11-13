#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("coordination/standards/automation/assistant_handoff_v2_contract_v0_1.yaml")

ACK_FIELDS = [
    "schema_version",
    "handoff_manifest_sha256",
    "launch_mode",
    "context_fingerprint",
    "authority_ack",
    "work_front_ack",
    "profile_ack",
    "procedure_ack",
    "freshness_ack",
]
RESULT_FIELDS = [
    "schema_version",
    "handoff_manifest_sha256",
    "attempt_id",
    "status",
    "changed_paths",
    "validation_evidence",
    "self_repair_attempts",
    "resume_coordinates",
    "unresolved_findings",
]
REQUIRED_BINDINGS = [
    "project_laws_or_constitution_revision",
    "work_front_or_project_onboard_not_applicable_reason",
    "execution_profile_revision_for_task_execution",
    "governed_procedure_revision_or_not_required_reason",
    "dependency_health_slice",
    "source_state_fingerprint",
    "lifecycle_roadmap_cursor",
    "resume_coordinates",
    "expected_result_schema_revision",
]
DEFERRED = [
    "dispatcher_integration",
    "actual_worker_launch",
    "central_retry_orchestration",
    "result_routing_to_operator",
]


def load_contract(root: Path) -> dict[str, Any]:
    data = yaml.safe_load((root / CONTRACT).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("contract must be a mapping")
    return data


def validate_contract(data: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []

    if data.get("schema_version") != "forprint_assistant_handoff_v2_contract_v0_1":
        errors.append("schema_version invalid")
    if data.get("contract_id") != "assistant_handoff_v2":
        errors.append("contract_id invalid")
    if data.get("revision") != "0.1.0":
        errors.append("revision invalid")

    authority = data.get("authority")
    if not isinstance(authority, dict):
        errors.append("authority must be mapping")
    else:
        for key in (
            "grants_execution_authority",
            "grants_dispatch_authority",
            "grants_release_authority",
        ):
            if authority.get(key) is not False:
                errors.append(f"authority.{key} must be false")

    relation = data.get("relationship_to_existing")
    expected_relation = {
        "assistant_handoff_v1": "EXTEND",
        "task_context_compiler": "EXTEND",
        "launch_request_fresh_context_gate": "EXTEND",
        "work_front": "REUSE",
        "execution_profiles": "REUSE",
        "execution_attempt_ledger": "REUSE",
        "governed_procedure_graph": "REUSE",
    }
    if not isinstance(relation, dict):
        errors.append("relationship_to_existing must be mapping")
    else:
        for key, value in expected_relation.items():
            if relation.get(key) != value:
                errors.append(f"relationship_to_existing.{key} must be {value}")
        if relation.get("parallel_handoff_framework_allowed") is not False:
            errors.append("parallel handoff framework must be forbidden")

    modes = data.get("launch_modes")
    if not isinstance(modes, dict) or set(modes) != {"PROJECT_ONBOARD", "TASK_EXECUTION"}:
        errors.append("launch_modes must be exactly PROJECT_ONBOARD,TASK_EXECUTION")
    else:
        po = modes["PROJECT_ONBOARD"]
        te = modes["TASK_EXECUTION"]
        if po.get("front_required") is not False:
            errors.append("PROJECT_ONBOARD.front_required must be false")
        if po.get("project_onboard_not_applicable_reason_required") is not True:
            errors.append("PROJECT_ONBOARD not-applicable reason must be required")
        if po.get("execution_authority") is not False:
            errors.append("PROJECT_ONBOARD execution_authority must be false")
        if te.get("front_required") is not True:
            errors.append("TASK_EXECUTION.front_required must be true")
        if te.get("execution_profile_required") is not True:
            errors.append("TASK_EXECUTION.execution_profile_required must be true")
        if te.get("execution_authority") is not False:
            errors.append("TASK_EXECUTION execution_authority must be false")

    if data.get("required_bindings") != REQUIRED_BINDINGS:
        errors.append("required_bindings exact list mismatch")

    ack = data.get("ack_envelope")
    if not isinstance(ack, dict) or ack.get("exact_fields") != ACK_FIELDS:
        errors.append("ACK exact fields mismatch")
    else:
        if ack.get("aliases_allowed") is not False:
            errors.append("ACK aliases must be invalid")
        if ack.get("additional_fields_allowed") is not False:
            errors.append("ACK additional fields must be invalid")

    result = data.get("result_envelope")
    if not isinstance(result, dict) or result.get("exact_fields") != RESULT_FIELDS:
        errors.append("result exact fields mismatch")
    else:
        if result.get("aliases_allowed") is not False:
            errors.append("result aliases must be invalid")
        if result.get("additional_fields_allowed") is not False:
            errors.append("result additional fields must be invalid")

    fail_closed = data.get("fail_closed")
    required_fail = (
        "missing_required_work_front_for_task_execution",
        "missing_effective_authority_resolution",
        "missing_expected_result_schema",
        "missing_required_generated_context",
        "missing_required_freshness_proof",
        "missing_required_manifest_hash",
    )
    if not isinstance(fail_closed, dict):
        errors.append("fail_closed must be mapping")
    else:
        for key in required_fail:
            if fail_closed.get(key) is not True:
                errors.append(f"fail_closed.{key} must be true")

    pack = data.get("generated_pack")
    if not isinstance(pack, dict):
        errors.append("generated_pack must be mapping")
    else:
        for key in (
            "derived",
            "disposable",
            "manifest_hash_bound",
            "source_state_fingerprint_required",
        ):
            if pack.get(key) is not True:
                errors.append(f"generated_pack.{key} must be true")
        if pack.get("chat_transcript_required") is not False:
            errors.append("chat transcript must not be required")

    local = data.get("local_result_validation")
    if not isinstance(local, dict):
        errors.append("local_result_validation must be mapping")
    else:
        for key in (
            "required_before_return",
            "bounded_self_repair_allowed",
            "self_repair_must_remain_within_effective_authority",
            "self_repair_must_record_attempts",
        ):
            if local.get(key) is not True:
                errors.append(f"local_result_validation.{key} must be true")
        if local.get("dispatch_authority_granted") is not False:
            errors.append("local result validation must not grant dispatch authority")

    fresh = data.get("freshness_and_resume")
    if not isinstance(fresh, dict):
        errors.append("freshness_and_resume must be mapping")
    else:
        for key in (
            "reconciled_lifecycle_roadmap_cursor_required",
            "durable_resume_coordinates_required",
            "stale_required_generated_context_blocks_launch",
            "accepted_mutation_or_event_must_not_be_replayed",
        ):
            if fresh.get(key) is not True:
                errors.append(f"freshness_and_resume.{key} must be true")

    refs = data.get("source_contracts")
    if not isinstance(refs, list) or not refs:
        errors.append("source_contracts missing")
    else:
        for rel in refs:
            if not isinstance(rel, str) or not (root / rel).is_file():
                errors.append(f"source contract missing: {rel!r}")

    if data.get("deferred_to_cf09") != DEFERRED:
        errors.append("deferred_to_cf09 exact list mismatch")

    boundary = data.get("cf08_s1_boundary")
    if not isinstance(boundary, dict):
        errors.append("cf08_s1_boundary must be mapping")
    else:
        if boundary.get("contract_and_validation_only") is not True:
            errors.append("S1 must be contract_and_validation_only")
        for key in (
            "runtime_compiler_integration_implemented",
            "dispatcher_implemented",
            "worker_dispatch_performed",
        ):
            if boundary.get(key) is not False:
                errors.append(f"cf08_s1_boundary.{key} must be false")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    data = load_contract(root)
    errors = validate_contract(data, root)
    if errors:
        for error in errors:
            print(f"ERROR={error}")
        print("ASSISTANT_HANDOFF_V2_CONTRACT_VALIDATION=FAIL")
        return 1
    print("ASSISTANT_HANDOFF_V2_CONTRACT=PASS")
    print("LAUNCH_MODES=PROJECT_ONBOARD,TASK_EXECUTION")
    print("EXACT_ACK_FIELDS=true")
    print("EXACT_RESULT_FIELDS=true")
    print("ALIASES_ALLOWED=false")
    print("MANIFEST_HASH_BOUND=true")
    print("LOCAL_RESULT_VALIDATION_REQUIRED=true")
    print("BOUNDED_SELF_REPAIR=true")
    print("DISPATCH_AUTHORITY=false")
    print("CF09_DISPATCHER_DEFERRED=true")
    print("CF08_S1_RUNTIME_INTEGRATION_IMPLEMENTED=false")
    print("ASSISTANT_HANDOFF_V2_CONTRACT_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
