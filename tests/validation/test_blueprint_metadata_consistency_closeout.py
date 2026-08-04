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
    "2026-08-03__blueprint__metadata_consistency_"
    "closeout_v0_1.yaml"
)
INTEGRATION = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__metadata_consistency_"
    "validator_integration_v0_1.yaml"
)
WAVE1 = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__operational_readiness_"
    "wave1_closeout_v0_1.yaml"
)
PROMPT_CLOSEOUT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__prompt_workflow_"
    "governance_closeout_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

METADATA_CLOSED = {"metadata_consistency_not_verified"}
METADATA_REMAINING = {
    "write_flow_recovery_not_fully_verified",
    "blueprint_operational_readiness_review_not_completed",
    "reference_pilot_migration_not_authorized",
}
CURRENT_CLOSED = {
    "metadata_consistency_not_verified",
    "write_flow_recovery_not_fully_verified",
}
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


def test_current_matrix_closes_only_metadata_blocker() -> None:
    matrix = _load(MATRIX)
    implementation = matrix["governance"][
        "implementation_progress"
    ]
    snapshot = _blueprint_snapshot(matrix)

    assert implementation["metadata_consistency_state"] == (
        "verified_closed_blocked"
    )
    assert set(snapshot["known_gaps"]) == CURRENT_REMAINING
    assert CURRENT_CLOSED.isdisjoint(snapshot["known_gaps"])
    assert snapshot["target_conformance"] == (
        "implementation_in_progress"
    )
    assert snapshot["rollout_authorized"] is False
    assert snapshot["next_required_step"] == (
        "blueprint_operational_readiness_review"
    )


def test_progress_records_metadata_closeout_and_blocked_state() -> None:
    progress = _load(PROGRESS)
    state = progress["implementation_state"]
    behavior = progress["verified_behavior"]["metadata_consistency"]
    boundaries = progress["boundaries"]

    assert state["metadata_consistency_validator"] == "implemented"
    assert state["metadata_consistency"] == "verified_current_head"
    assert state["metadata_consistency_closeout"] == (
        "completed_blocked"
    )
    assert state["operational_readiness_state"] == "blocked"
    assert state["operational_readiness_review"] == "pending"
    assert state["reference_pilot_migration"] == "not_authorized"
    assert state["external_rollout"] == "gated"

    assert behavior["current_repository_validation"] == "passed"
    assert behavior["governance_yaml_validation"] == "passed"
    assert behavior["prompt_index_validation"] == "passed"
    assert (
        behavior["cross_index_prompt_identity_validation"]
        == "passed"
    )
    assert behavior["path_containment_validation"] == "passed"
    assert behavior["legacy_governance_compatibility"] == "passed"
    assert behavior["metadata_consistency_blocker_closed"] is True
    assert behavior["write_flow_recovery_assessed"] is True
    assert behavior["operational_readiness_green"] is False

    assert set(boundaries["metadata_consistency_closed_blockers"]) == (
        METADATA_CLOSED
    )
    assert boundaries["write_flow_recovery_remains_blocked"] is False
    assert boundaries["operational_readiness_remains_blocked"] is True
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout_released"] is False
    assert boundaries["cross_repository_writes"] is False


def test_metadata_closeout_is_exact_and_fail_closed() -> None:
    closeout = _load(CLOSEOUT)

    assert closeout["schema_version"] == (
        "blueprint_metadata_consistency_closeout_v0_1"
    )
    assert set(closeout["closed_blockers"]) == METADATA_CLOSED
    assert set(closeout["remaining_readiness_blockers"]) == (
        METADATA_REMAINING
    )

    verification = closeout["verification"]
    assert verification["current_repository_validation"] == "PASSED"
    assert verification["governance_yaml_records"] == "PASSED"
    assert verification["outgoing_prompt_indexes"] == "PASSED"
    assert verification["cross_index_prompt_identity"] == "PASSED"
    assert verification["negative_tests"] == "PASSED"
    assert (
        verification["tracked_repository_mutation_by_validator"]
        is False
    )
    assert verification["canonical_gate"] == {
        "total": 27,
        "ok": 27,
        "warnings": 0,
        "failed": 0,
    }

    boundaries = closeout["boundaries"]
    assert boundaries["operational_readiness_review"] == "in_progress"
    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["write_flow_recovery_state"] == "blocked"
    assert boundaries["release_policy_state"] == "gated"
    assert (
        boundaries["reference_pilot_migration_authorized"]
        is False
    )
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["cross_repository_writes"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False


def test_prior_evidence_remains_historical() -> None:
    integration = _load(INTEGRATION)
    wave1 = _load(WAVE1)
    prompt = _load(PROMPT_CLOSEOUT)

    assert integration["metadata"]["status"] == "implemented_not_closed"
    assert integration["governance_state"][
        "metadata_consistency_not_verified"
    ] == "remains_until_separate_closeout"
    assert "metadata_consistency_not_verified" in (
        wave1["remaining_readiness_blockers"]
    )
    assert "metadata_consistency_not_verified" in (
        prompt["remaining_readiness_blockers"]
    )


def test_release_policy_and_rollout_remain_gated() -> None:
    policy = _load(RELEASE_POLICY)

    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
