from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX = (
    ROOT
    / "coordination/standards/adoption/"
    "module_workflow_adoption_matrix_v0_1.yaml"
)
PROGRESS = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-01__blueprint__module_workflow_command_"
    "implementation_progress_v0_1.yaml"
)
CLOSEOUT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__write_flow_recovery_closeout_v0_1.yaml"
)
METADATA_CLOSEOUT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__metadata_consistency_closeout_v0_1.yaml"
)
FIXER = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__coordination_metadata_fixer_"
    "recovery_remediation_v0_1.yaml"
)
SHARED = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__shared_writer_recovery_"
    "contract_v0_1.yaml"
)
CONTROLLED = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__controlled_failure_write_flow_"
    "contract_v0_1.yaml"
)
BOUNDED = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__bounded_output_writer_"
    "contract_v0_1.yaml"
)
EXPLICIT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__explicit_write_flow_recovery_"
    "contract_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

CLOSED = {"write_flow_recovery_not_fully_verified"}
CURRENT_REMAINING = {
    "blueprint_operational_readiness_review_not_completed",
    "reference_pilot_migration_not_authorized",
}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _blueprint_snapshot(matrix: dict) -> dict:
    return next(
        row
        for row in matrix["assessment_snapshot"]["repositories"]
        if row["repository_id"] == "forprint_system_blueprint"
    )


def test_current_matrix_closes_only_write_flow_blocker() -> None:
    matrix = _load(MATRIX)
    implementation = matrix["governance"]["implementation_progress"]
    snapshot = _blueprint_snapshot(matrix)

    assert implementation["write_flow_recovery_state"] == (
        "verified_closed_blocked"
    )
    assert set(snapshot["known_gaps"]) == CURRENT_REMAINING
    assert CLOSED.isdisjoint(snapshot["known_gaps"])
    assert snapshot["target_conformance"] == (
        "implementation_in_progress"
    )
    assert snapshot["rollout_authorized"] is False
    assert snapshot["next_required_step"] == (
        "blueprint_operational_readiness_review"
    )


def test_progress_records_complete_write_flow_verification() -> None:
    progress = _load(PROGRESS)
    state = progress["implementation_state"]
    behavior = progress["verified_behavior"]["write_flow_recovery"]
    boundaries = progress["boundaries"]

    assert state["write_flow_recovery"] == "verified_current_head"
    assert state["write_flow_recovery_closeout"] == (
        "completed_blocked"
    )
    assert state["operational_readiness_state"] == "blocked"
    assert state["operational_readiness_review"] == "pending"
    assert state["reference_pilot_migration"] == "not_authorized"
    assert state["external_rollout"] == "gated"

    assert behavior["reviewed_path_count"] == 49
    assert behavior["initial_closeout_candidate_count"] == 25
    assert behavior["initial_manual_blocker_count"] == 24
    assert behavior["metadata_fixer_duplicate_execution_closed"] is True
    assert behavior["shared_writer_primitive_count"] == 3
    assert behavior["controlled_failure_flow_count"] == 4
    assert behavior["bounded_output_writer_count"] == 15
    assert behavior["explicit_recovery_flow_count"] == 2
    assert behavior["remaining_manual_blocker_count"] == 0
    assert behavior["write_flow_recovery_blocker_closed"] is True
    assert behavior["operational_readiness_green"] is False

    assert set(boundaries["write_flow_recovery_closed_blockers"]) == (
        CLOSED
    )
    assert boundaries["write_flow_recovery_remains_blocked"] is False
    assert set(boundaries["operational_readiness_remaining_blockers"]) == (
        CURRENT_REMAINING
    )
    assert boundaries["operational_readiness_remains_blocked"] is True
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout_released"] is False
    assert boundaries["cross_repository_writes"] is False


def test_closeout_is_exact_and_fail_closed() -> None:
    closeout = _load(CLOSEOUT)

    assert closeout["schema_version"] == (
        "blueprint_write_flow_recovery_closeout_v0_1"
    )
    assert set(closeout["closed_blockers"]) == CLOSED
    assert set(closeout["remaining_readiness_blockers"]) == (
        CURRENT_REMAINING
    )

    verification = closeout["verification"]
    assert verification["classified_script_count"] == 49
    assert verification["initial_closeout_candidate_count"] == 25
    assert verification["initial_manual_blocker_count"] == 24
    assert verification["verified_groups"] == {
        "shared_writer_primitives": 3,
        "controlled_failure_flows": 4,
        "bounded_output_writers": 15,
        "explicit_recovery_flows": 2,
    }
    assert verification["verified_manual_blocker_total"] == 24
    assert verification["remaining_manual_blocker_count"] == 0
    assert verification["self_audit_atomic_publication_count"] == 3
    assert verification["canonical_gate"] == {
        "total": 27,
        "ok": 27,
        "warnings": 0,
        "failed": 0,
    }

    boundaries = closeout["boundaries"]
    assert boundaries["operational_readiness_review"] == "in_progress"
    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["write_flow_recovery_state"] == "verified_closed"
    assert boundaries["release_policy_state"] == "gated"
    assert boundaries["reference_pilot_migration_authorized"] is False
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["cross_repository_writes"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False


def test_evidence_chain_remains_historical_and_complete() -> None:
    metadata = _load(METADATA_CLOSEOUT)
    fixer = _load(FIXER)
    shared = _load(SHARED)
    controlled = _load(CONTROLLED)
    bounded = _load(BOUNDED)
    explicit = _load(EXPLICIT)

    assert "write_flow_recovery_not_fully_verified" in (
        metadata["remaining_readiness_blockers"]
    )
    assert fixer["metadata"]["status"] == "implemented_not_closed"
    assert shared["metadata"]["status"] == "verified_not_closed"
    assert controlled["metadata"]["status"] == "verified_not_closed"
    assert bounded["metadata"]["status"] == "verified_not_closed"
    assert explicit["metadata"]["status"] == (
        "implemented_ready_for_closeout"
    )
    assert explicit["per_flow_state"][
        "remaining_manual_blocker_count_after_this_evidence"
    ] == 0
    assert explicit["blocker_state"]["closed_in_this_evidence"] is False
    assert explicit["blocker_state"]["closeout_eligible"] is True


def test_release_policy_and_rollout_remain_gated() -> None:
    policy = _load(RELEASE_POLICY)

    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
