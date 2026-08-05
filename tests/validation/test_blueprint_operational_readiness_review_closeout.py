from __future__ import annotations

import hashlib
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
VALIDATOR = (
    ROOT
    / "scripts/validation/"
    "validate_module_workflow_adoption_matrix.py"
)
VALIDATOR_HASH = "fcb341339672a61008e2b8d60ab8b0838b27471122b9039ed7e398b2a6eaef9f"
CLOSEOUT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-04__blueprint__operational_readiness_review_"
    "closeout_v0_1.yaml"
)
WRITE_FLOW_CLOSEOUT = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__write_flow_recovery_closeout_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)
REVIEW_REPORT = (
    ROOT
    / "tmp/blueprint_operational_readiness_final_review/"
    "operational_readiness_final_review.yaml"
)
REVIEW_SUMMARY = (
    ROOT
    / "tmp/blueprint_operational_readiness_final_review/"
    "operational_readiness_final_review.md"
)

REVIEW_REPORT_SHA256 = (
    "e8e5304d28f3af285f01f7f25cea4053510d33e77f73ce84e101401fbc16cc41"
)
REVIEW_SUMMARY_SHA256 = (
    "c194b9033892a0dca7a97c15d8bb30f1194fa3e625f80b4fcbbd6cb3b4b7c9b4"
)
CLOSED = {
    "blueprint_operational_readiness_review_not_completed"
}
CURRENT_REMAINING = {
    "reference_pilot_migration_not_authorized"
}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _snapshot(matrix: dict) -> dict:
    return next(
        row
        for row in matrix["assessment_snapshot"]["repositories"]
        if row["repository_id"] == "forprint_system_blueprint"
    )


def test_source_review_artifacts_are_exact() -> None:
    assert _sha256(REVIEW_REPORT) == REVIEW_REPORT_SHA256
    assert _sha256(REVIEW_SUMMARY) == REVIEW_SUMMARY_SHA256

    review = _load(REVIEW_REPORT)
    assert review["metadata"]["status"] == (
        "passed_ready_for_governance_closeout"
    )
    assert review["decision"]["review_result"] == "PASS"
    assert review["decision"][
        "operational_readiness_review_closeout_eligible"
    ] is True
    assert review["decision"]["close_only"] == list(CLOSED)
    assert review["decision"]["do_not_close"] == list(
        CURRENT_REMAINING
    )


def test_validator_contract_matches_completed_review() -> None:
    assert _sha256(VALIDATOR) == VALIDATOR_HASH

    validator_text = VALIDATOR.read_text(encoding="utf-8")
    assert (
        '"operational_readiness_review": "completed_pass"'
        in validator_text
    )
    assert (
        '"reference_pilot_migration_authorization_decision"'
        in validator_text
    )
    assert (
        '6: ("blueprint_operational_readiness_review", "completed")'
        in validator_text
    )


def test_current_matrix_closes_only_review_blocker() -> None:
    matrix = _load(MATRIX)
    implementation = matrix["governance"]["implementation_progress"]
    snapshot = _snapshot(matrix)

    assert implementation["next_required_step"] == (
        "reference_pilot_migration_authorization_decision"
    )

    step_6 = next(
        row
        for row in matrix["migration_sequence"]
        if row["step"] == 6
    )
    assert step_6["step"] == 6
    assert step_6["action"] == (
        "blueprint_operational_readiness_review"
    )
    assert step_6["status"] == "completed"
    assert step_6["owner"] == "forprint_system_blueprint"
    assert step_6["rollout_effect"] == "none"

    assert implementation[
        "operational_readiness_review_state"
    ] == "completed_pilot_gated"
    assert set(snapshot["known_gaps"]) == CURRENT_REMAINING
    assert CLOSED.isdisjoint(snapshot["known_gaps"])
    assert snapshot["target_conformance"] == (
        "operational_readiness_review_completed_pilot_gated"
    )
    assert snapshot["rollout_authorized"] is False
    assert snapshot["next_required_step"] == (
        "reference_pilot_migration_authorization_decision"
    )


def test_progress_passes_review_but_keeps_pilot_gated() -> None:
    progress = _load(PROGRESS)
    state = progress["implementation_state"]
    review = progress["verified_behavior"][
        "operational_readiness_final_review"
    ]
    boundaries = progress["boundaries"]

    assert state["operational_readiness_state"] == (
        "review_completed_pilot_gated"
    )
    assert state["operational_readiness_review"] == "completed_pass"
    assert state["reference_pilot_migration"] == "not_authorized"
    assert state["external_rollout"] == "gated"
    assert progress["next_required_step"]["action"] == (
        "reference_pilot_migration_authorization_decision"
    )

    assert review["review_result"] == "PASS"
    assert review["canonical_gate_ok"] == 27
    assert review["canonical_gate_total"] == 27
    assert review["remaining_technical_recovery_blockers"] == 0
    assert review["review_closeout_eligible"] is True
    assert review["operational_readiness_review_blocker_closed"] is True
    assert review["reference_pilot_migration_authorized"] is False
    assert review["external_rollout"] == "gated"

    assert boundaries["operational_readiness_remains_blocked"] is False
    assert set(
        boundaries["operational_readiness_review_closed_blockers"]
    ) == CLOSED
    assert set(
        boundaries["operational_readiness_remaining_blockers"]
    ) == CURRENT_REMAINING
    assert boundaries[
        "reference_pilot_migration_remains_blocked"
    ] is True
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout_released"] is False


def test_closeout_does_not_authorize_pilot() -> None:
    closeout = _load(CLOSEOUT)

    assert closeout["metadata"]["status"] == "completed_pilot_gated"
    assert set(closeout["closed_blockers"]) == CLOSED
    assert set(closeout["remaining_readiness_blockers"]) == (
        CURRENT_REMAINING
    )

    decision = closeout["decision"]
    assert decision["operational_readiness_review"] == "completed_pass"
    assert decision["operational_readiness_state"] == (
        "review_completed_pilot_gated"
    )
    assert decision["reference_pilot_migration_authorized"] is False
    assert decision["external_module_prompts_released"] is False
    assert decision["external_rollout"] == "gated"
    assert decision["release_policy_modified"] is False

    boundaries = closeout["boundaries"]
    assert boundaries["rollout_authorized"] is False
    assert boundaries["pilot_authorized"] is False
    assert boundaries["release_policy_state"] == "gated"
    assert boundaries["cross_repository_writes"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False


def test_prior_write_flow_closeout_remains_historical() -> None:
    write_flow = _load(WRITE_FLOW_CLOSEOUT)

    assert set(write_flow["closed_blockers"]) == {
        "write_flow_recovery_not_fully_verified"
    }
    assert set(write_flow["remaining_readiness_blockers"]) == {
        "blueprint_operational_readiness_review_not_completed",
        "reference_pilot_migration_not_authorized",
    }
    assert write_flow["boundaries"]["operational_readiness"] == (
        "blocked"
    )
    assert write_flow["boundaries"][
        "reference_pilot_migration_authorized"
    ] is False
    assert write_flow["boundaries"]["external_rollout"] == "gated"


def test_release_policy_remains_fail_closed() -> None:
    policy = _load(RELEASE_POLICY)

    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
