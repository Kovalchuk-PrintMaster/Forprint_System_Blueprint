from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/automation/continuity_contract_v0_1.yaml"
ROADMAP = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_continuity_contract_validator_passes() -> None:
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validation/validate_continuity_contract_v0_1.py",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "CONTINUITY_CONTRACT=PASS" in cp.stdout


def test_lifecycle_has_no_direct_active_to_closed_transition() -> None:
    lifecycle = load(CONTRACT)["lifecycle"]
    assert lifecycle["states"] == [
        "PLANNED",
        "ACTIVE",
        "CHECKPOINTED",
        "VALIDATED",
        "CLOSED",
    ]
    assert "ACTIVE->CLOSED" in lifecycle["forbidden_transitions"]
    assert "ACTIVE->CLOSED" not in lifecycle["normal_transitions"]
    assert lifecycle["closed_state"]["reopen_same_work_id_forbidden"] is True


def test_checkpoint_binds_post_repair_hashes_and_source_state() -> None:
    checkpoint = load(CONTRACT)["checkpoint_model"]
    fields = set(checkpoint["required_fields"])
    assert {
        "source_state_before",
        "source_state_after",
        "final_applied_artifact_hashes",
        "evidence",
        "next_actions",
    } <= fields
    evidence = checkpoint["evidence_binding"]
    assert evidence["final_artifact_hashes_are_post_repair"] is True
    assert evidence["raw_candidate_hashes_do_not_substitute_for_final_hashes"] is True
    assert evidence["tmp_path_alone_is_sufficient"] is False


def test_source_state_accepts_dirty_tree_and_avoids_self_reference() -> None:
    source = load(CONTRACT)["source_state_fingerprint"]
    assert source["source_mode"] == "working_tree"
    assert source["dirty_working_tree_is_valid"] is True
    assert source["clean_git_required"] is False
    assert "__pycache__" in source["explicit_runtime_exclusions"]
    assert "tmp" in source["explicit_runtime_exclusions"]
    assert "tmp.py" in source["explicit_runtime_exclusions"]
    assert "indexes" in source["non_source_metadata_exclusions"]
    assert "coordination/continuity/events" in source["non_source_metadata_exclusions"]
    assert source["reports_are_implicitly_excluded"] is False
    assert source["self_reference_is_forbidden"] is True


def test_checkpoint_store_is_content_addressed_append_only() -> None:
    store = load(CONTRACT)["checkpoint_store"]
    assert store["path"] == "coordination/continuity/events"
    assert store["content_addressed_filenames"] is True
    assert store["accepted_events_append_only"] is True
    assert store["generic_knowledge_index_excludes_event_ledger"] is True
    assert store["manual_in_place_edit_forbidden"] is True


def test_projections_are_generated_non_authoritative_and_exact_checked() -> None:
    contract = load(CONTRACT)
    projections = contract["projection_model"]
    assert projections["generated_only"] is True
    assert projections["manual_edit_forbidden"] is True
    store = contract["projection_store"]
    assert store["path"] == "coordination/continuity/projections"
    assert store["exact_check_is_non_mutating"] is True
    assert store["manual_edit_forbidden"] is True
    implementation = contract["implementation_sequence"]
    assert implementation["checkpoint_writer_implemented_here"] is True
    assert implementation["projections_implemented_here"] is True
    assert implementation["current_step"] == "module_transfer_reference_implementation"
    assert implementation["current_step_state"] == "complete"
    assert implementation["current_work_id"] == "u179h"
    assert implementation["next_step"] is None
    assert implementation["continuity_foundation_complete"] is True
    assert implementation["next_program"] == "control_foundation_near_horizon"
    assert implementation["handoff_compiler_implemented_here"] is True
    assert implementation["lifecycle_enforcement_implemented_here"] is True


def test_handoff_model_is_zero_context_and_chat_independent() -> None:
    handoff = load(CONTRACT)["assistant_handoff_model"]
    assert handoff["one_archive_zero_context_goal"] is True
    assert handoff["chat_transcript_included_by_default"] is False
    assert handoff["deterministic_payload_required"] is True
    assert "00_READ_FIRST.md" in handoff["required_payload"]
    assert "latest_checkpoint" in handoff["required_payload"]
    assert "NEXT_HORIZON" in handoff["required_payload"]


def test_micro_roadmap_closes_module_transfer_and_hands_off_to_control_foundation() -> None:
    roadmap = load(ROADMAP)
    steps = {row["order"]: row for row in roadmap["steps"]}
    assert all("state" not in row for row in roadmap["steps"])
    historical = roadmap["historical_completion_evidence"]
    assert historical["schema_version"] == "forprint_legacy_roadmap_completion_evidence_v0_1"
    assert historical["authority"] == "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE"
    assert historical["step_state_fields_retired"] is True
    assert historical["completed_step_ids"] == [row["id"] for row in roadmap["steps"]]
    assert steps[6]["id"] == "continuity_contract"
    assert steps[7]["id"] == "immutable_checkpoints"
    assert steps[7]["work"] == "u179c"
    assert steps[8]["id"] == "generated_operational_projections"
    assert steps[8]["work"] == "u179d"
    assert steps[9]["id"] == "assistant_handoff_compiler"
    assert steps[9]["work"] == "u179e"
    assert steps[10]["id"] == "lifecycle_enforcement"
    assert steps[10]["work"] == "u179f"
    assert steps[11]["id"] == "zero_context_acceptance"
    assert steps[11]["work"] == "u179g"
    assert steps[12]["id"] == "module_transfer_reference_implementation"
    assert steps[12]["work"] == "u179h"
    assert roadmap["completion"]["foundation_state"] == "complete"
    assert roadmap["completion"]["last_completed_work_id"] == "u179h"
    assert roadmap["next_action"]["step"] is None
    assert roadmap["next_action"]["id"] == "control_foundation_near_horizon"
    assert roadmap["next_action"]["activation_requires_operator"] is True
    assert roadmap["next_action"]["worker_dispatch_allowed"] is False
    assert roadmap["next_action"]["release_allowed"] is False


def test_lifecycle_enforcement_contract_is_bound() -> None:
    lifecycle = load(CONTRACT)["lifecycle"]
    enforcement = lifecycle["enforcement"]
    assert enforcement["enabled"] is True
    assert enforcement["implementation"] == "scripts/coordination/continuity_lifecycle.py"
    assert enforcement["validator"] == "scripts/validation/validate_continuity_lifecycle_v0_1.py"
    assert enforcement["pre_enforcement_boundary_sequence"] == 3
    assert (
        enforcement["pre_enforcement_boundary_event_id"]
        == "evt-u179e-assistant-handoff-compiler-20260911t093355510787z"
    )
    assert enforcement["close_gate_runtime_enforced"] is True
    assert enforcement["closed_reopen_same_work_id_forbidden"] is True


def test_handoff_compiler_is_deterministic_runtime_non_authority() -> None:
    compiler = load(CONTRACT)["handoff_compiler"]
    assert compiler["script"] == "scripts/coordination/build_assistant_handoff_archive.py"
    assert compiler["make_target"] == "assistant-pack"
    assert compiler["validation_target"] == "assistant-handoff-check"
    assert compiler["authority"] == "none"
    assert compiler["chat_transcript_included"] is False
    assert compiler["project_source_mutation_performed"] is False
    deterministic = compiler["deterministic_archive"]
    assert deterministic["entry_order"] == "lexicographic"
    assert deterministic["zip_compression"] == "stored"
    assert deterministic["manifest_self_hash_excluded"] is True


def test_isolated_validation_uses_frozen_source_input_not_runtime_side_effects() -> None:
    source = load(CONTRACT)["source_state_fingerprint"]
    isolation = source["isolated_validation_baseline"]
    assert isolation["enabled_only_when_forprint_non_mutating_check_isolated"] is True
    assert isolation["baseline_created_before_validation_side_effects"] is True
    assert isolation["baseline_transport_env"] == "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE"
    assert isolation["baseline_root_env"] == "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT"
    assert isolation["bounded_final_hashes_rebound_per_checkpoint"] is True
    assert isolation["source_repository_preservation_still_required"] is True
    assert source["reports_are_implicitly_excluded"] is False
