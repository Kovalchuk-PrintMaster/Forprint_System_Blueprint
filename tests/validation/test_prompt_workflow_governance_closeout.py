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
    "2026-08-03__blueprint__prompt_workflow_"
    "governance_closeout_v0_1.yaml"
)
APPLICABILITY = (
    ROOT
    / "coordination/standards/adoption/"
    "blueprint_command_applicability_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)
SELF_AUDIT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-02__blueprint__self_audit_completion_v0_1.yaml"
)

CLOSED = {
    "prompt_prepare_not_implemented",
    "prompt_release_not_implemented",
}
PROMPT_CLOSEOUT_REMAINING = {
    "metadata_consistency_not_verified",
    "module_identity_not_reconciled",
    "artifact_authority_and_retention_not_enforced",
    "write_flow_recovery_not_fully_verified",
    "blueprint_operational_readiness_review_not_completed",
    "reference_pilot_migration_not_authorized",
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
    repositories = matrix["assessment_snapshot"]["repositories"]
    return next(
        row
        for row in repositories
        if row["repository_id"] == "forprint_system_blueprint"
    )


def test_matrix_records_prompt_workflow_closeout() -> None:
    matrix = _load(MATRIX)
    progress = matrix["governance"]["implementation_progress"]

    assert progress["state"] == "blueprint_internal_in_progress"
    assert progress["prompt_workflow_state"] == "implemented_gated"
    assert progress["next_required_step"] == (
        "blueprint_operational_readiness_review"
    )

    capabilities = set(progress["completed_capabilities"])
    assert {
        "blueprint_outgoing_prompt_workflow_core",
        "blueprint_prompt_workflow_operator_commands",
        "blueprint_prompt_workflow_release_policy_gate",
        "blueprint_prompt_workflow_governance_closeout",
    } <= capabilities

    snapshot = _blueprint_snapshot(matrix)
    gaps = set(snapshot["known_gaps"])
    assert gaps == CURRENT_REMAINING
    assert CLOSED.isdisjoint(gaps)
    assert snapshot["target_conformance"] == (
        "implementation_in_progress"
    )
    assert snapshot["rollout_authorized"] is False
    assert snapshot["next_required_step"] == (
        "blueprint_operational_readiness_review"
    )


def test_progress_records_implemented_gated_workflow() -> None:
    progress = _load(PROGRESS)
    state = progress["implementation_state"]
    behavior = progress["verified_behavior"]["prompt_workflow"]
    boundaries = progress["boundaries"]

    assert state["prompt_workflow_core"] == "completed"
    assert state["prompt_prepare_operator_command"] == "completed"
    assert (
        state["prompt_release_operator_command"]
        == "completed_gated"
    )
    assert state["prompt_release_policy"] == "gated"
    assert state["operational_readiness_state"] == "blocked"
    assert state["reference_pilot_migration"] == "not_authorized"
    assert state["external_rollout"] == "gated"

    assert behavior["prepare_preview_is_read_only"] is True
    assert behavior["release_preview_is_read_only"] is True
    assert (
        behavior[
            "release_apply_requires_explicit_governance_authorization"
        ]
        is True
    )
    assert (
        behavior[
            "module_template_exposes_blueprint_mutation_targets"
        ]
        is False
    )
    assert behavior["ready_for_module_pull_is_execution_authority"] is True
    assert behavior["legacy_dispatch_index_is_mutated"] is False
    assert behavior["sent_directory_is_release_state"] is False

    assert boundaries["prompt_workflow_release_policy_gated"] is True
    assert (
        boundaries["prompt_workflow_external_release_authorized"]
        is False
    )
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["cross_repository_writes"] is False


def test_closeout_evidence_is_exact_and_gated() -> None:
    closeout = _load(CLOSEOUT)

    assert closeout["schema_version"] == (
        "blueprint_prompt_workflow_governance_closeout_v0_1"
    )
    assert set(closeout["closed_blockers"]) == CLOSED
    assert (
        set(closeout["remaining_readiness_blockers"])
        == PROMPT_CLOSEOUT_REMAINING
    )
    assert closeout["validation"]["canonical_gate"] == {
        "total": 27,
        "ok": 27,
        "warnings": 0,
        "failed": 0,
    }

    boundaries = closeout["boundaries"]
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
    assert closeout["result"] == (
        "BLUEPRINT_PROMPT_WORKFLOW_GOVERNANCE_"
        "CLOSEOUT_COMPLETED_GATED"
    )


def test_current_applicability_and_release_policy_remain_gated() -> None:
    applicability = _load(APPLICABILITY)
    commands = {
        row["command_id"]: row
        for row in applicability["commands"]
    }

    assert commands["prompt-prepare"]["conformance"] == "pass"
    assert commands["prompt-release"]["conformance"] == "pass"
    assert (
        commands["prompt-release"]["release_policy_state"]
        == "gated"
    )
    assert applicability["result"]["blockers"] == []
    assert applicability["result"]["external_rollout"] == "gated"

    policy = _load(RELEASE_POLICY)
    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["result"]["operational_state"] == "gated"


def test_historical_self_audit_is_not_rewritten() -> None:
    audit = _load(SELF_AUDIT)

    assert CLOSED <= set(audit["readiness_blockers"])
    assert audit["subject"]["operational_readiness"] == "blocked"
    assert (
        audit["boundaries"]["reference_pilot_migration_authorized"]
        is False
    )
