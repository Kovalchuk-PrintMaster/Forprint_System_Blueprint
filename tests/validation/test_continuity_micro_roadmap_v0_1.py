from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)


def load() -> dict:
    return yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))


def test_continuity_micro_roadmap_has_exact_bounded_sequence() -> None:
    data = load()
    steps = data["steps"]
    assert [row["order"] for row in steps] == list(range(1, 13))
    assert all("state" not in row for row in steps)
    historical = data["historical_completion_evidence"]
    assert historical["schema_version"] == "forprint_legacy_roadmap_completion_evidence_v0_1"
    assert historical["authority"] == "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE"
    assert historical["step_state_fields_retired"] is True
    assert historical["completed_step_ids"] == [row["id"] for row in steps]
    assert steps[5]["id"] == "continuity_contract"
    assert steps[5]["work"] == "u179b"
    assert steps[6]["id"] == "immutable_checkpoints"
    assert steps[6]["work"] == "u179c"
    assert steps[7]["id"] == "generated_operational_projections"
    assert steps[7]["work"] == "u179d"
    assert steps[8]["id"] == "assistant_handoff_compiler"
    assert steps[8]["work"] == "u179e"
    assert steps[9]["id"] == "lifecycle_enforcement"
    assert steps[9]["work"] == "u179f"
    assert steps[10]["id"] == "zero_context_acceptance"
    assert steps[10]["work"] == "u179g"
    assert steps[11]["id"] == "module_transfer_reference_implementation"
    assert steps[11]["work"] == "u179h"


def test_continuity_micro_roadmap_keeps_authority_boundaries() -> None:
    data = load()
    boundary = data["startup_authority_boundary"]
    assert boundary["chat_transcript_is_source_of_truth"] is False
    assert boundary["roadmap_is_not_release_authority"] is True
    assert boundary["roadmap_is_not_queue_authority"] is True
    assert data["status"] == "completed_execution_micro_roadmap"
    assert data["completion"]["foundation_state"] == "complete"
    assert data["completion"]["last_completed_work_id"] == "u179h"
    assert data["next_action"]["step"] is None
    assert data["next_action"]["id"] == "control_foundation_near_horizon"
    assert data["next_action"]["activation_requires_operator"] is True
    assert data["next_action"]["worker_dispatch_allowed"] is False
    assert data["next_action"]["release_allowed"] is False


def test_continuity_micro_roadmap_preserves_dirty_baseline_and_progress_rules() -> None:
    rules = load()["execution_rules"]
    assert rules["dirty_working_tree_is_valid_baseline"] is True
    assert rules["clean_git_required"] is False
    assert rules["source_mutation_via_mutation_compiler"] is True
    assert rules["public_make_check_must_be_non_mutating"] is True
    assert rules["assistant_scripts_show_progress_by_default"] is True
    assert rules["checkpoint_hashes_bind_final_applied_artifacts"] is True


def test_continuity_micro_roadmap_validator_passes() -> None:
    cp = subprocess.run(
        [
            sys.executable,
            "scripts/validation/validate_continuity_micro_roadmap_v0_1.py",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "CONTINUITY_MICRO_ROADMAP=PASS" in cp.stdout


def test_continuity_micro_roadmap_resolves_to_strict_document_subclass() -> None:
    from scripts.validation.validate_document_surface_registry_v0_1 import effective_profile

    registry_path = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    roadmap_detail = next(
        item for item in registry["types"] if item["document_type"] == "roadmap_detail"
    )
    profile = effective_profile(roadmap_detail, ROADMAP.relative_to(ROOT).as_posix())
    assert profile["subclass_id"] == "continuity_execution_micro_roadmap"
    assert profile["migration_state"] == "STRICT"
    assert profile["schema_version"] == "forprint_continuity_assistant_handoff_micro_roadmap_v0_1"
    assert "make continuity-micro-roadmap-check" in profile["validation"]
