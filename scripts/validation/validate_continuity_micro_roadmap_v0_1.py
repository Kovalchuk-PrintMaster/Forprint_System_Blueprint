#!/usr/bin/env python3
"""Validate the current Continuity / Assistant Handoff micro-roadmap."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)

EXPECTED_IDS = [
    "dependency_closure_audit",
    "execution_dependency_contract",
    "dependency_registry_graph_explain",
    "normalize_make_check_dag",
    "non_mutating_public_make_check_acceptance",
    "continuity_contract",
    "immutable_checkpoints",
    "generated_operational_projections",
    "assistant_handoff_compiler",
    "lifecycle_enforcement",
    "zero_context_acceptance",
    "module_transfer_reference_implementation",
]


def fail(message: str) -> int:
    print("CONTINUITY_MICRO_ROADMAP=FAIL")
    print("ERROR=" + message)
    return 1


def main() -> int:
    if not ROADMAP.is_file():
        return fail("ROADMAP_MISSING")

    data = yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))
    if data.get("status") != "completed_execution_micro_roadmap":
        return fail("STATUS")
    if data.get("authority") != "blueprint_coordination_execution_plan":
        return fail("AUTHORITY")

    boundary = data.get("startup_authority_boundary", {})
    expected_startup = [
        "AGENTS.md",
        "coordination/bootstrap/START_HERE.md",
        "coordination/bootstrap/index_v0_1.yaml",
        "make assistant-context-pack",
    ]
    if boundary.get("canonical_startup_entry") != expected_startup:
        return fail("STARTUP_AUTHORITY_CHAIN")
    if boundary.get("chat_transcript_is_source_of_truth") is not False:
        return fail("CHAT_TRANSCRIPT_AUTHORITY")

    steps = data.get("steps", [])
    if len(steps) != 12:
        return fail("STEP_COUNT")
    if [row.get("order") for row in steps] != list(range(1, 13)):
        return fail("STEP_ORDER")
    if [row.get("id") for row in steps] != EXPECTED_IDS:
        return fail("STEP_IDS")

    if any("state" in row for row in steps):
        return fail("MANUAL_EXECUTION_STATE_FORBIDDEN")
    historical = data.get("historical_completion_evidence", {})
    if historical.get("schema_version") != "forprint_legacy_roadmap_completion_evidence_v0_1":
        return fail("HISTORICAL_COMPLETION_EVIDENCE_SCHEMA")
    if historical.get("authority") != "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE":
        return fail("HISTORICAL_COMPLETION_EVIDENCE_AUTHORITY")
    if historical.get("step_state_fields_retired") is not True:
        return fail("HISTORICAL_STEP_STATE_RETIREMENT")
    if historical.get("completed_step_ids") != EXPECTED_IDS:
        return fail("HISTORICAL_COMPLETION_STEP_SET")
    if steps[5].get("work") != "u179b":
        return fail("STEP_6_WORK_ID")
    if steps[6].get("work") != "u179c":
        return fail("STEP_7_WORK_ID")
    if steps[7].get("work") != "u179d":
        return fail("STEP_8_WORK_ID")
    if steps[8].get("work") != "u179e":
        return fail("STEP_9_WORK_ID")
    if steps[9].get("work") != "u179f":
        return fail("STEP_10_WORK_ID")
    if steps[10].get("work") != "u179g":
        return fail("STEP_11_WORK_ID")
    if steps[11].get("work") != "u179h":
        return fail("STEP_12_WORK_ID")

    completion = data.get("completion", {})
    if completion.get("foundation_state") != "complete":
        return fail("FOUNDATION_STATE")
    if completion.get("last_completed_work_id") != "u179h":
        return fail("FOUNDATION_LAST_WORK")
    if completion.get("close_event_id") != "evt-u179h-closed-repair-20260912t141557412734z":
        return fail("FOUNDATION_CLOSE_EVENT")

    next_action = data.get("next_action", {})
    if next_action.get("step") is not None:
        return fail("NEXT_ACTION_STEP")
    if next_action.get("id") != "control_foundation_near_horizon":
        return fail("NEXT_ACTION_ID")
    if next_action.get("source") != (
        "coordination/roadmaps/details/forprint_system_blueprint/"
        "control_foundation_near_horizon_program_v0_1.yaml"
    ):
        return fail("NEXT_ACTION_SOURCE")
    if next_action.get("activation_requires_operator") is not True:
        return fail("NEXT_ACTION_OPERATOR_GATE")
    if next_action.get("worker_dispatch_allowed") is not False:
        return fail("WORKER_DISPATCH_WIDENED")
    if next_action.get("release_allowed") is not False:
        return fail("RELEASE_WIDENED")

    rules = data.get("execution_rules", {})
    required_true = (
        "dirty_working_tree_is_valid_baseline",
        "source_mutation_via_mutation_compiler",
        "public_make_check_must_be_non_mutating",
        "hidden_execution_dependency_is_defect",
        "assistant_scripts_show_progress_by_default",
        "checkpoint_hashes_bind_final_applied_artifacts",
    )
    for key in required_true:
        if rules.get(key) is not True:
            return fail("RULE_TRUE:" + key)

    # The two "...forbidden" fields must be true; only clean_git_required is false.
    if rules.get("clean_git_required") is not False:
        return fail("CLEAN_GIT_REQUIRED")
    if rules.get("automatic_commit_push_release_forbidden") is not True:
        return fail("COMMIT_PUSH_RELEASE_POLICY")
    if rules.get("automatic_worker_dispatch_forbidden") is not True:
        return fail("WORKER_DISPATCH_POLICY")

    target = data.get("continuity_target_model", {})
    if target.get("event_state_machine") != [
        "PLANNED",
        "ACTIVE",
        "CHECKPOINTED",
        "VALIDATED",
        "CLOSED",
    ]:
        return fail("STATE_MACHINE")
    if "ACTIVE->CLOSED" not in target.get("forbidden_transition", []):
        return fail("FORBIDDEN_DIRECT_CLOSE")

    checkpoint_fields = set(target.get("checkpoint_must_capture", []))
    required_checkpoint_fields = {
        "what_changed",
        "why",
        "evidence",
        "decision_rationale",
        "blockers",
        "unknowns",
        "next_5_to_10_actions",
        "source_state_fingerprint",
        "final_applied_artifact_hashes",
    }
    if not required_checkpoint_fields.issubset(checkpoint_fields):
        return fail("CHECKPOINT_FIELDS")

    projections = set(target.get("generated_projections", []))
    required_projections = {
        "CURRENT_WORKFRONT",
        "RECENT_ACTIVITY",
        "DECISIONS",
        "BLOCKERS",
        "NEXT_HORIZON",
        "SOURCE_STATE",
        "WORKER_PORTFOLIO",
    }
    if not required_projections.issubset(projections):
        return fail("PROJECTIONS")

    print("CONTINUITY_MICRO_ROADMAP=PASS")
    print("STEP_COUNT=12")
    print("COMPLETE_STEPS=12")
    print("MANUAL_EXECUTION_STATE=false")
    print("HISTORICAL_COMPLETION_EVIDENCE=EXPLICIT")
    print("NEXT_PROGRAM=control_foundation_near_horizon")
    print("CONTINUITY_FOUNDATION_COMPLETE=true")
    print("CHAT_TRANSCRIPT_AUTHORITY=false")
    print("WORKER_DISPATCH_ALLOWED=false")
    print("RELEASE_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
