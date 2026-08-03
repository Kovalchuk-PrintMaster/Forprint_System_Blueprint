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
SELF_AUDIT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-02__blueprint__self_audit_completion_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

CLOSED = {
    "module_identity_not_reconciled",
    "artifact_authority_and_retention_not_enforced",
}
CURRENT_REMAINING = {
    "metadata_consistency_not_verified",
    "write_flow_recovery_not_fully_verified",
    "blueprint_operational_readiness_review_not_completed",
    "reference_pilot_migration_not_authorized",
}
PROMPT_CLOSEOUT_REMAINING = CURRENT_REMAINING | CLOSED


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


def test_current_matrix_closes_only_wave1_blockers() -> None:
    matrix = _load(MATRIX)
    progress = matrix["governance"]["implementation_progress"]
    snapshot = _blueprint_snapshot(matrix)

    assert progress["operational_readiness_wave1_state"] == (
        "completed_blocked"
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


def test_progress_records_verified_wave1_and_blocked_readiness() -> None:
    progress = _load(PROGRESS)
    state = progress["implementation_state"]
    behavior = progress["verified_behavior"][
        "operational_readiness_wave1"
    ]
    boundaries = progress["boundaries"]

    assert state["operational_readiness_wave1"] == "completed_blocked"
    assert state["module_identity_reconciliation"] == (
        "verified_current_head"
    )
    assert state["artifact_authority_and_retention"] == (
        "verified_current_head"
    )
    assert state["operational_readiness_state"] == "blocked"
    assert state["operational_readiness_review"] == "pending"
    assert state["reference_pilot_migration"] == "not_authorized"
    assert state["external_rollout"] == "gated"

    assert behavior["module_registry_resolution"] == "passed"
    assert behavior["artifact_authority_policy"] == "passed"
    assert behavior["artifact_retention_consistency"] == "passed"
    assert behavior["module_identity_blocker_closed"] is True
    assert (
        behavior[
            "artifact_authority_and_retention_blocker_closed"
        ]
        is True
    )
    assert behavior["metadata_consistency_assessed"] is False
    assert behavior["write_flow_recovery_assessed"] is False
    assert behavior["operational_readiness_green"] is False

    assert set(
        boundaries["operational_readiness_wave1_closed_blockers"]
    ) == CLOSED
    assert boundaries["operational_readiness_remains_blocked"] is True
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout_released"] is False
    assert boundaries["cross_repository_writes"] is False


def test_wave1_evidence_is_exact_and_fail_closed() -> None:
    evidence = _load(WAVE1)

    assert evidence["schema_version"] == (
        "blueprint_operational_readiness_wave1_closeout_v0_1"
    )
    assert set(evidence["closed_blockers"]) == CLOSED
    assert set(evidence["remaining_readiness_blockers"]) == (
        CURRENT_REMAINING
    )

    verification = evidence["verification"]
    assert verification["module_registry_resolution"]["result"] == (
        "PASSED"
    )
    assert verification["artifact_authority_policy"]["result"] == (
        "PASSED"
    )
    assert (
        verification["artifact_retention_consistency"]["result"]
        == "PASSED"
    )
    assert verification["runtime_reports_committed"] is False
    assert (
        verification[
            "tracked_repository_mutation_during_verification"
        ]
        is False
    )
    assert verification["canonical_gate"] == {
        "total": 27,
        "ok": 27,
        "warnings": 0,
        "failed": 0,
    }

    boundaries = evidence["boundaries"]
    assert boundaries["operational_readiness_review"] == "in_progress"
    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["release_policy_state"] == "gated"
    assert (
        boundaries["reference_pilot_migration_authorized"]
        is False
    )
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["cross_repository_writes"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False


def test_historical_prompt_closeout_remains_immutable() -> None:
    closeout = _load(PROMPT_CLOSEOUT)

    assert set(closeout["remaining_readiness_blockers"]) == (
        PROMPT_CLOSEOUT_REMAINING
    )
    assert closeout["boundaries"]["operational_readiness"] == (
        "blocked"
    )
    assert closeout["boundaries"]["external_rollout"] == "gated"


def test_historical_self_audit_and_release_policy_remain_gated() -> None:
    audit = _load(SELF_AUDIT)
    policy = _load(RELEASE_POLICY)

    assert CLOSED <= set(audit["readiness_blockers"])
    assert audit["subject"]["operational_readiness"] == "blocked"
    assert (
        audit["boundaries"]["reference_pilot_migration_authorized"]
        is False
    )

    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
