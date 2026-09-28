from __future__ import annotations

from scripts.coordination.control_plane import governed_worker_cycle as cycle


def facts(**overrides):
    value = {
        "task_resolved": False,
        "workspace_prepared": False,
        "assistant_ack_validated": False,
        "explicit_dispatch_authorized": False,
        "worker_process_started": False,
        "worker_process_finished": False,
        "candidate_validation_passed": False,
        "handoff_validated": False,
        "attempt_terminal_pass": False,
        "attempt_terminal_failed": False,
        "operator_review_passed": False,
        "candidate_promoted": False,
        "canonical_validation_passed": False,
        "publication_approved": False,
        "commit_performed": False,
        "remote_containment_verified": False,
        "blocked": False,
    }
    value.update(overrides)
    return value


def test_empty_facts_start_at_resolve_task() -> None:
    result = cycle.derive_cycle_projection(facts())
    assert result["state"] == "RESOLVE_TASK"
    assert result["next_boundary"] == "RESOLVE_AUTHORITATIVE_TASK"
    assert result["derived_non_authoritative"] is True
    assert all(value is False for value in result["authority"].values())


def test_prepared_cycle_stops_at_assistant_ack() -> None:
    result = cycle.derive_cycle_projection(
        facts(task_resolved=True, workspace_prepared=True)
    )
    assert result["state"] == "AWAITING_ASSISTANT_ACK"
    assert result["next_boundary"] == "EXPLICIT_ASSISTANT_ACK"


def test_terminal_pass_stops_at_operator_review() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
        )
    )
    assert result["state"] == "AWAITING_OPERATOR_REVIEW"
    assert result["next_boundary"] == "OPERATOR_REVIEW"


def test_promoted_candidate_requires_canonical_validation() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
            operator_review_passed=True,
            candidate_promoted=True,
        )
    )
    assert result["state"] == "CANONICAL_VALIDATION"


def test_canonical_validation_stops_before_publication() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
            operator_review_passed=True,
            candidate_promoted=True,
            canonical_validation_passed=True,
        )
    )
    assert result["state"] == "AWAITING_PUBLICATION_APPROVAL"
    assert result["next_boundary"] == "PUBLICATION_APPROVAL"


def test_remote_containment_is_terminal_published_state() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
            operator_review_passed=True,
            candidate_promoted=True,
            canonical_validation_passed=True,
            publication_approved=True,
            commit_performed=True,
            remote_containment_verified=True,
        )
    )
    assert result["state"] == "PUBLISHED"


def test_impossible_state_fails_closed_to_unknown() -> None:
    result = cycle.derive_cycle_projection(
        facts(candidate_promoted=True)
    )
    assert result["state"] == "UNKNOWN"
    assert result["contradictions"]
    assert result["next_boundary"] == (
        "INSPECT_CONTRADICTORY_OR_INSUFFICIENT_EVIDENCE"
    )
