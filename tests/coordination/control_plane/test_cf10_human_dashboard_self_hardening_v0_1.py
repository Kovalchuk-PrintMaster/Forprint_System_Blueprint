from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/human_dashboard.py"

spec = importlib.util.spec_from_file_location(
    "_cf10_human_dashboard_self_hardening_test",
    SOURCE,
)
assert spec is not None and spec.loader is not None
dashboard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dashboard
spec.loader.exec_module(dashboard)


def projection(*attempts: dict) -> dict:
    return {
        "schema_version": "forprint_local_operator_projection_v0_1",
        "attempts": list(attempts),
    }


def test_rendering_is_deterministic_and_preserves_task50_facts() -> None:
    facts = projection(
        {
            "attempt_id": "cf10-u180j-a020",
            "attempt_stage": "FINISHED",
            "result_state": "FAILED",
            "state": "FINISHED",
            "reason": "terminal_ledger_fact",
        }
    )

    rendered = dashboard.render_dashboard(facts)

    assert rendered == dashboard.render_dashboard(facts)
    for fact in (
        "cf10-u180j-a020",
        "attempt_stage: FINISHED",
        "result_state: FAILED",
        "outcome: FAILED",
        "derived_state: FINISHED",
        "reason: terminal_ledger_fact",
    ):
        assert fact in rendered


def test_terminal_outcomes_remain_distinguishable_from_runtime_state() -> None:
    facts = projection(
        {
            "attempt_id": "success",
            "attempt_stage": "FINISHED",
            "result_state": "SUCCEEDED",
            "state": "FINISHED",
            "reason": "ledger_and_completion_evidence",
        },
        {
            "attempt_id": "failure",
            "attempt_stage": "FAILED",
            "result_state": "FAILED",
            "state": "FINISHED",
            "reason": "terminal_ledger_fact",
        },
        {
            "attempt_id": "blocked",
            "attempt_stage": "BLOCKED",
            "result_state": "BLOCKED",
            "state": "FINISHED",
            "reason": "terminal_ledger_fact",
        },
    )

    rendered = dashboard.render_dashboard(facts)

    for outcome in ("SUCCEEDED", "FAILED", "BLOCKED"):
        assert f"result_state: {outcome}" in rendered
        assert f"outcome: {outcome}" in rendered
        assert "derived_state: FINISHED" in rendered


def test_missing_or_invalid_attempt_facts_remain_unknown() -> None:
    rendered = dashboard.render_dashboard(
        projection({"attempt_id": "partial", "state": "not-a-runtime-state"})
    )

    for fact in (
        "attempt_stage: UNKNOWN",
        "result_state: UNKNOWN",
        "outcome: UNKNOWN",
        "derived_state: UNKNOWN",
        "reason: UNKNOWN",
        "Projection freshness: UNKNOWN",
    ):
        assert fact in rendered

    empty = dashboard.render_dashboard({})
    assert "Attempt history: UNKNOWN" in empty


def test_default_history_is_bounded_to_final_projection_entries() -> None:
    attempts = [
        {
            "attempt_id": f"attempt-{index:02}",
            "attempt_stage": "FINISHED",
            "result_state": "SUCCEEDED",
            "state": "FINISHED",
            "reason": "terminal_ledger_fact",
        }
        for index in range(12)
    ]

    rendered = dashboard.render_dashboard(projection(*attempts))

    assert "attempt_id: attempt-00" not in rendered
    assert "attempt_id: attempt-01" not in rendered
    assert "attempt_id: attempt-02" in rendered
    assert "attempt_id: attempt-11" in rendered
    assert rendered.count("  attempt_id: ") == dashboard.DEFAULT_HISTORY_LIMIT
    assert "recency is not independently verifiable" in rendered


def test_dashboard_provenance_and_authority_are_explicit() -> None:
    rendered = dashboard.render_dashboard(projection())

    assert "Task50 operator projection" in rendered
    assert "derived, non-authoritative view" in rendered
    assert (
        "no execution, dispatch, ledger-mutation, approval, or acceptance authority"
        in rendered
    )
    assert "execution_authority" not in rendered
    assert "dispatch_authority" not in rendered


def test_history_limit_must_be_a_positive_integer() -> None:
    for invalid_limit in (0, -1, True, 1.5):
        try:
            dashboard.render_dashboard(projection(), history_limit=invalid_limit)
        except ValueError:
            continue
        raise AssertionError(f"accepted invalid history limit: {invalid_limit!r}")
