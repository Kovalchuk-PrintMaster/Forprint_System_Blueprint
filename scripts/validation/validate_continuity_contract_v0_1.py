#!/usr/bin/env python3
"""Validate the ForPrint Continuity Contract v0.1 and roadmap transition."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/automation/continuity_contract_v0_1.yaml"
ROADMAP = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)
STANDARDS_INDEX = ROOT / "coordination/standards/index.yaml"
AGENTS = ROOT / "AGENTS.md"
MAKEFILE = ROOT / "Makefile"

EXPECTED_STATES = [
    "PLANNED",
    "ACTIVE",
    "CHECKPOINTED",
    "VALIDATED",
    "CLOSED",
]
EXPECTED_NORMAL = [
    "PLANNED->ACTIVE",
    "ACTIVE->CHECKPOINTED",
    "CHECKPOINTED->VALIDATED",
    "VALIDATED->CLOSED",
]
EXPECTED_PROJECTIONS = {
    "CURRENT_WORKFRONT",
    "RECENT_ACTIVITY",
    "DECISIONS",
    "BLOCKERS",
    "NEXT_HORIZON",
    "SOURCE_STATE",
    "WORKER_PORTFOLIO",
    "UNRECONCILED_CURRENT_DELTA",
}
EXPECTED_CHECKPOINT_FIELDS = {
    "what_changed",
    "why",
    "evidence",
    "decision_rationale",
    "rejected_alternative_when_material",
    "blockers",
    "unknowns",
    "next_actions",
    "source_state_before",
    "source_state_after",
    "final_applied_artifact_hashes",
    "external_baseline_preserved",
}


def fail(message: str) -> int:
    print(f"CONTINUITY_CONTRACT=FAIL {message}")
    return 1


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"top-level mapping required: {path}")
    return data


def roadmap_step(data: dict, order: int) -> dict:
    matches = [
        row for row in data.get("steps", []) if isinstance(row, dict) and row.get("order") == order
    ]
    if len(matches) != 1:
        raise ValueError(f"roadmap step {order} count={len(matches)}")
    return matches[0]


def main() -> int:
    required_paths = (
        CONTRACT,
        ROADMAP,
        STANDARDS_INDEX,
        AGENTS,
        MAKEFILE,
        ROOT / "coordination/standards/governance/common_coordination_event_envelope_v0_1.yaml",
        ROOT / "coordination/standards/automation/execution_dependency_contract_v0_1.yaml",
        ROOT / "coordination/standards/automation/mutation_compiler_contract_v0_1.yaml",
        ROOT / "coordination/standards/automation/execution_progress_visibility_contract_v0_1.yaml",
        ROOT / "scripts/coordination/continuity.py",
        ROOT / "scripts/validation/validate_continuity_event_store_v0_1.py",
        ROOT / "scripts/coordination/build_continuity_projections.py",
        ROOT / "scripts/validation/validate_continuity_projections_v0_1.py",
        ROOT / "scripts/validation/run_non_mutating_make_check.py",
    )
    for path in required_paths:
        if not path.is_file():
            return fail(f"missing={path.relative_to(ROOT)}")

    try:
        contract = load_yaml(CONTRACT)
        roadmap = load_yaml(ROADMAP)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return fail(f"parse={exc}")

    if any("state" in row for row in roadmap.get("steps", [])):
        return fail("roadmap_manual_execution_state_forbidden")
    historical = roadmap.get("historical_completion_evidence", {})
    if historical.get("schema_version") != "forprint_legacy_roadmap_completion_evidence_v0_1":
        return fail("roadmap_historical_evidence_schema")
    if historical.get("authority") != "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE":
        return fail("roadmap_historical_evidence_authority")
    if historical.get("step_state_fields_retired") is not True:
        return fail("roadmap_historical_state_retirement")
    if historical.get("completed_step_ids") != [row.get("id") for row in roadmap.get("steps", [])]:
        return fail("roadmap_historical_evidence_step_set")

    if contract.get("schema_version") != "forprint_continuity_contract_v0_1":
        return fail("schema_version")
    if contract.get("status") != "active_standard":
        return fail("status")
    if contract.get("authority") != "blueprint_continuity_semantics_standard":
        return fail("authority")

    bounds = contract.get("authority_boundaries", {})
    forbidden_true = (
        "continuity_event_is_release_authority",
        "checkpoint_is_release_authority",
        "projection_is_release_authority",
        "handoff_pack_is_release_authority",
        "continuity_artifacts_are_queue_authority",
        "continuity_artifacts_may_dispatch_workers",
        "operator_approval_is_inferred",
        "foreign_module_write_authority_is_inferred",
    )
    if any(bounds.get(key) is not False for key in forbidden_true):
        return fail("authority_boundary_widened")
    if bounds.get("chat_transcript_is_source_of_truth") is not False:
        return fail("chat_source_of_truth")

    event_model = contract.get("event_model", {})
    if event_model.get("append_only") is not True:
        return fail("event_append_only")
    if event_model.get("immutable_after_append") is not True:
        return fail("event_immutability")
    if event_model.get("correction_model") != "append_superseding_event":
        return fail("event_correction_model")
    if event_model.get("terminal_heartbeat_is_continuity_event") is not False:
        return fail("heartbeat_event_pollution")

    checkpoint = contract.get("checkpoint_model", {})
    actual_checkpoint_fields = set(checkpoint.get("required_fields", []))
    if not EXPECTED_CHECKPOINT_FIELDS.issubset(actual_checkpoint_fields):
        return fail("checkpoint_required_fields")
    next_actions = checkpoint.get("next_actions", {})
    if next_actions.get("minimum") != 5 or next_actions.get("maximum") != 10:
        return fail("next_action_bounds")
    evidence = checkpoint.get("evidence_binding", {})
    if evidence.get("tmp_path_alone_is_sufficient") is not False:
        return fail("tmp_evidence_must_not_be_sufficient")
    if evidence.get("final_artifact_hashes_are_post_repair") is not True:
        return fail("final_hash_binding")
    if evidence.get("raw_candidate_hashes_do_not_substitute_for_final_hashes") is not True:
        return fail("raw_candidate_hash_substitution")

    source_state = contract.get("source_state_fingerprint", {})
    if source_state.get("source_mode") != "working_tree":
        return fail("source_state_mode")
    if source_state.get("dirty_working_tree_is_valid") is not True:
        return fail("dirty_working_tree")
    if source_state.get("clean_git_required") is not False:
        return fail("clean_git_requirement")
    if source_state.get("reports_are_implicitly_excluded") is not False:
        return fail("reports_implicit_exclusion")
    exclusions = set(source_state.get("explicit_runtime_exclusions", []))
    for required in {
        "tmp",
        "tmp.py",
        "__pycache__",
        ".venv_blueprint",
        ".git",
    }:
        if required not in exclusions:
            return fail(f"runtime_exclusion={required}")
    non_source = set(source_state.get("non_source_metadata_exclusions", []))
    for required in {
        "indexes",
        "coordination/continuity/events",
        "coordination/continuity/projections",
    }:
        if required not in non_source:
            return fail(f"non_source_exclusion={required}")
    if source_state.get("self_reference_is_forbidden") is not True:
        return fail("source_state_self_reference")
    isolation = source_state.get("isolated_validation_baseline", {})
    if isolation.get("enabled_only_when_forprint_non_mutating_check_isolated") is not True:
        return fail("isolated_source_state_enablement")
    if isolation.get("baseline_created_before_validation_side_effects") is not True:
        return fail("isolated_source_state_timing")
    if isolation.get("baseline_transport_env") != "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE":
        return fail("isolated_source_state_transport")
    if isolation.get("baseline_root_env") != "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT":
        return fail("isolated_source_state_root_transport")
    if isolation.get("bounded_final_hashes_rebound_per_checkpoint") is not True:
        return fail("isolated_source_state_hash_rebinding")
    if isolation.get("source_repository_preservation_still_required") is not True:
        return fail("isolated_source_state_preservation")
    continuity_source = (ROOT / "scripts/coordination/continuity.py").read_text(encoding="utf-8")
    isolation_runner_source = (
        ROOT / "scripts/validation/run_non_mutating_make_check.py"
    ).read_text(encoding="utf-8")
    for token in (
        "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE",
        "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT",
    ):
        if token not in continuity_source:
            return fail("continuity_isolation_binding=" + token)
        if token not in isolation_runner_source:
            return fail("runner_isolation_binding=" + token)

    lifecycle = contract.get("lifecycle", {})
    if lifecycle.get("states") != EXPECTED_STATES:
        return fail("lifecycle_states")
    if lifecycle.get("normal_transitions") != EXPECTED_NORMAL:
        return fail("normal_transitions")
    forbidden = set(lifecycle.get("forbidden_transitions", []))
    if "ACTIVE->CLOSED" not in forbidden:
        return fail("active_closed_must_be_forbidden")
    if lifecycle.get("closed_state", {}).get("reopen_same_work_id_forbidden") is not True:
        return fail("closed_reopen_rule")

    projections = contract.get("projection_model", {})
    if projections.get("generated_only") is not True:
        return fail("projection_generated_only")
    if projections.get("manual_edit_forbidden") is not True:
        return fail("projection_manual_edit")
    actual_projections = set(projections.get("projections", {}))
    if actual_projections != EXPECTED_PROJECTIONS:
        return fail("projection_set")
    unreconciled = projections.get("unreconciled_delta", {})
    if unreconciled.get("must_not_be_hidden") is not True:
        return fail("unreconciled_delta_hidden")
    if unreconciled.get("must_not_be_silently_folded_into_latest_checkpoint") is not True:
        return fail("unreconciled_delta_folded")

    projection_store = contract.get("projection_store", {})
    if projection_store.get("path") != "coordination/continuity/projections":
        return fail("projection_store_path")
    if projection_store.get("builder") != ("scripts/coordination/build_continuity_projections.py"):
        return fail("projection_builder")
    if projection_store.get("validator") != (
        "scripts/validation/validate_continuity_projections_v0_1.py"
    ):
        return fail("projection_validator")
    if projection_store.get("exact_check_is_non_mutating") is not True:
        return fail("projection_check_mutation")
    if projection_store.get("manual_edit_forbidden") is not True:
        return fail("projection_store_manual_edit")
    if set(projection_store.get("projection_ids", [])) != EXPECTED_PROJECTIONS:
        return fail("projection_store_ids")

    handoff = contract.get("assistant_handoff_model", {})
    if handoff.get("chat_transcript_included_by_default") is not False:
        return fail("handoff_chat_transcript_default")
    if handoff.get("deterministic_payload_required") is not True:
        return fail("handoff_determinism")
    required_payload = set(handoff.get("required_payload", []))
    for required in {
        "00_READ_FIRST.md",
        "manifest",
        "AGENTS.md",
        "latest_checkpoint",
        "CURRENT_WORKFRONT",
        "NEXT_HORIZON",
        "SOURCE_STATE",
    }:
        if required not in required_payload:
            return fail(f"handoff_payload={required}")

    bootstrap = contract.get("bootstrap_migration", {})
    if bootstrap.get("pre_contract_history_is_not_rewritten") is not True:
        return fail("bootstrap_history_rewrite")
    if bootstrap.get("first_checkpoint_implementation_may_emit_genesis_checkpoint") is not True:
        return fail("genesis_checkpoint")

    store = contract.get("checkpoint_store", {})
    if store.get("path") != "coordination/continuity/events":
        return fail("checkpoint_store_path")
    if store.get("content_addressed_filenames") is not True:
        return fail("checkpoint_content_address")
    if store.get("accepted_events_append_only") is not True:
        return fail("checkpoint_append_only")
    if store.get("generic_knowledge_index_excludes_event_ledger") is not True:
        return fail("checkpoint_knowledge_boundary")

    implementation = contract.get("implementation_sequence", {})
    if implementation.get("current_step") != "module_transfer_reference_implementation":
        return fail("implementation_current_step")
    if implementation.get("current_step_state") != "complete":
        return fail("implementation_current_step_state")
    if implementation.get("current_work_id") != "u179h":
        return fail("implementation_current_work_id")
    if implementation.get("next_step") is not None:
        return fail("implementation_next_step")
    if implementation.get("continuity_foundation_complete") is not True:
        return fail("implementation_foundation_complete")
    if implementation.get("next_program") != "control_foundation_near_horizon":
        return fail("implementation_next_program")
    if implementation.get("next_program_source") != (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "control_foundation_near_horizon_program_v0_1.yaml"
    ):
        return fail("implementation_next_program_source")
    if implementation.get("checkpoint_writer_implemented_here") is not True:
        return fail("checkpoint_writer_state")
    if implementation.get("projections_implemented_here") is not True:
        return fail("projection_implementation_boundary")
    if implementation.get("handoff_compiler_implemented_here") is not True:
        return fail("handoff_compiler_implementation_boundary")
    if implementation.get("lifecycle_enforcement_implemented_here") is not True:
        return fail("lifecycle_enforcement_implementation_boundary")

    lifecycle = contract.get("lifecycle", {})
    enforcement = lifecycle.get("enforcement", {})
    if enforcement.get("enabled") is not True:
        return fail("lifecycle_enforcement_enabled")
    if enforcement.get("implementation") != "scripts/coordination/continuity_lifecycle.py":
        return fail("lifecycle_enforcement_implementation")
    if enforcement.get("validator") != "scripts/validation/validate_continuity_lifecycle_v0_1.py":
        return fail("lifecycle_enforcement_validator")
    if enforcement.get("pre_enforcement_boundary_sequence") != 3:
        return fail("lifecycle_enforcement_boundary_sequence")
    if enforcement.get("pre_enforcement_boundary_event_id") != (
        "evt-u179e-assistant-handoff-compiler-20260911t093355510787z"
    ):
        return fail("lifecycle_enforcement_boundary_event")
    if enforcement.get("close_gate_runtime_enforced") is not True:
        return fail("lifecycle_close_gate_runtime")
    if enforcement.get("closed_reopen_same_work_id_forbidden") is not True:
        return fail("lifecycle_closed_immutable_runtime")

    handoff_compiler = contract.get("handoff_compiler", {})
    if handoff_compiler.get("script") != "scripts/coordination/build_assistant_handoff_archive.py":
        return fail("handoff_compiler_script")
    if handoff_compiler.get("make_target") != "assistant-pack":
        return fail("handoff_compiler_make_target")
    if handoff_compiler.get("validation_target") != "assistant-handoff-check":
        return fail("handoff_compiler_validation_target")
    if handoff_compiler.get("authority") != "none":
        return fail("handoff_compiler_authority")
    if handoff_compiler.get("chat_transcript_included") is not False:
        return fail("handoff_chat_transcript")
    deterministic = handoff_compiler.get("deterministic_archive", {})
    if deterministic.get("zip_compression") != "stored":
        return fail("handoff_zip_compression")
    if deterministic.get("entry_order") != "lexicographic":
        return fail("handoff_entry_order")

    step6 = roadmap_step(roadmap, 6)
    step7 = roadmap_step(roadmap, 7)
    step8 = roadmap_step(roadmap, 8)
    step9 = roadmap_step(roadmap, 9)
    step10 = roadmap_step(roadmap, 10)
    step11 = roadmap_step(roadmap, 11)
    step12 = roadmap_step(roadmap, 12)
    if step6.get("id") != "continuity_contract":
        return fail("roadmap_step6_id")
    if step6.get("work") != "u179b":
        return fail("roadmap_step6_work")
    if step7.get("id") != "immutable_checkpoints":
        return fail("roadmap_step7_id")
    if step7.get("work") != "u179c":
        return fail("roadmap_step7_work")
    if step8.get("id") != "generated_operational_projections":
        return fail("roadmap_step8_id")
    if step8.get("work") != "u179d":
        return fail("roadmap_step8_work")
    if step9.get("id") != "assistant_handoff_compiler":
        return fail("roadmap_step9_id")
    if step9.get("work") != "u179e":
        return fail("roadmap_step9_work")
    if step10.get("id") != "lifecycle_enforcement":
        return fail("roadmap_step10_id")
    if step10.get("work") != "u179f":
        return fail("roadmap_step10_work")
    if step11.get("id") != "zero_context_acceptance":
        return fail("roadmap_step11_id")
    if step11.get("work") != "u179g":
        return fail("roadmap_step11_work")
    if step12.get("id") != "module_transfer_reference_implementation":
        return fail("roadmap_step12_id")
    if step12.get("work") != "u179h":
        return fail("roadmap_step12_work")

    completion = roadmap.get("completion", {})
    if completion.get("foundation_state") != "complete":
        return fail("roadmap_foundation_state")
    if completion.get("last_completed_work_id") != "u179h":
        return fail("roadmap_last_completed_work")

    next_action = roadmap.get("next_action", {})
    if next_action.get("step") is not None:
        return fail("roadmap_next_step")
    if next_action.get("id") != "control_foundation_near_horizon":
        return fail("roadmap_next_id")
    if next_action.get("activation_requires_operator") is not True:
        return fail("roadmap_next_operator_gate")
    if next_action.get("worker_dispatch_allowed") is not False:
        return fail("roadmap_worker_dispatch")
    if next_action.get("release_allowed") is not False:
        return fail("roadmap_release")

    standards = STANDARDS_INDEX.read_text(encoding="utf-8")
    if "standard_id: continuity_contract_v0_1" not in standards:
        return fail("standards_index")
    agents = AGENTS.read_text(encoding="utf-8")
    if "<!-- FORPRINT_CONTINUITY_CONTRACT_START -->" not in agents:
        return fail("agents_binding")
    if "continuity.py checkpoint --spec" not in agents:
        return fail("agents_checkpoint_writer_reference")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    if ".PHONY: continuity-event-store-check" not in makefile:
        return fail("event_store_make_target")
    if ".PHONY: continuity-checkpoint" not in makefile:
        return fail("checkpoint_make_target")
    if ".PHONY: continuity-projections-refresh" not in makefile:
        return fail("projection_refresh_make_target")
    if ".PHONY: continuity-projections-check" not in makefile:
        return fail("projection_check_make_target")
    if ".PHONY: assistant-handoff-check" not in makefile:
        return fail("assistant_handoff_check_make_target")
    if ".PHONY: assistant-pack" not in makefile:
        return fail("assistant_pack_make_target")
    if ".PHONY: continuity-lifecycle-check" not in makefile:
        return fail("lifecycle_check_make_target")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")),
        "",
    )
    if "continuity-contract-check" not in check_core.split():
        return fail("contract_check_core_binding")
    if "continuity-event-store-check" not in check_core.split():
        return fail("event_store_check_core_binding")
    if "continuity-projections-check" not in check_core.split():
        return fail("projection_check_core_binding")
    if "assistant-handoff-check" not in check_core.split():
        return fail("assistant_handoff_check_core_binding")
    if "continuity-lifecycle-check" not in check_core.split():
        return fail("lifecycle_check_core_binding")

    print("CONTINUITY_CONTRACT=PASS")
    print("EVENT_MODEL=append_only_immutable")
    print("CHECKPOINT_MODEL=content_addressed_final_hash_bound")
    print("SOURCE_STATE=self_reference_safe_working_tree")
    print("ACTIVE_TO_CLOSED_FORBIDDEN=true")
    print("PROJECTIONS=8")
    print("HANDOFF_ZERO_CONTEXT_MODEL=true")
    print("CHAT_TRANSCRIPT_SOURCE_OF_TRUTH=false")
    print("CHECKPOINT_WRITER_IMPLEMENTED=true")
    print("PROJECTIONS_IMPLEMENTED=true")
    print("HANDOFF_COMPILER_IMPLEMENTED=true")
    print("LIFECYCLE_ENFORCEMENT_IMPLEMENTED=true")
    print("NEXT_PROGRAM=control_foundation_near_horizon")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
