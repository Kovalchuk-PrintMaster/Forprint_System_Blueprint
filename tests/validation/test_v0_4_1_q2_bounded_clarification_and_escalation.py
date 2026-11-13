from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/bounded_clarification_and_escalation_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q2_bounded_clarification_and_escalation.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_limit_is_five_per_thread_not_prompt() -> None:
    b = load_contract()["round_budget"]
    assert b["maximum_unresolved_round_trips_per_question_thread"] == 5
    assert b["scope"] == "per_question_thread"
    assert b["prompt_shared_counter"] is False
    assert b["new_question_thread_has_independent_counter"] is True


def test_round_advance_is_completed_insufficient_evaluation_only() -> None:
    b = load_contract()["round_budget"]
    assert b["round_advances_only_after"] == "completed_answer_attempt_evaluated_insufficient"
    assert b["missing_answer_does_not_consume_completed_round_trip"] is True
    assert b["answer_not_yet_evaluated_does_not_advance"] is True
    assert b["resolved_answer_does_not_advance"] is True


def test_round_five_can_resolve_or_escalate_but_never_six() -> None:
    data = load_contract()
    flow = data["round_flow"]
    assert flow["round_5"]["if_answer_sufficient"] == ["CONFIRMED", "RESOLVED"]
    assert "ESCALATED" in flow["round_5"]["if_answer_insufficient"]
    assert "stop_further_autonomous_dialogue_for_thread" in flow["round_5"]["if_answer_insufficient"]
    assert data["round_budget"]["round_six_allowed"] is False
    assert flow["same_thread_round_6_after_escalation_allowed"] is False


def test_thread_identity_and_round_history_are_preserved() -> None:
    data = load_contract()
    b = data["round_budget"]
    assert b["thread_question_id_stable_across_rounds"] is True
    assert b["thread_correlation_id_stable_across_rounds"] is True
    assert b["history_append_only"] is True
    assert data["round_record"]["prior_round_mutation_allowed"] is False


def test_escalation_packet_is_complete() -> None:
    esc = load_contract()["escalation"]
    assert esc["resulting_thread_state"] == "ESCALATED"
    assert esc["round_history_must_cover"] == [1, 2, 3, 4, 5]
    required = set(esc["required_packet_fields"])
    for field in (
        "original_question", "round_history", "evidence_refs", "unresolved_fact",
        "impact", "safe_options", "recommended_next_action", "trigger", "escalated_at",
    ):
        assert field in required
    assert esc["recommended_next_action_is_advisory"] is True
    assert esc["safe_options_are_not_automatic_actions"] is True


def test_blocking_escalation_is_not_return_hold_or_q3_taxonomy() -> None:
    c = load_contract()["prompt_coupling"]
    assert c["blocking_escalated_thread_condition"] == "waiting_on_clarification_escalation"
    assert c["blocking_scope_progress_allowed"] is False
    assert c["condition_is_return"] is False
    assert c["condition_is_hold"] is False
    assert c["condition_is_prompt_acceptance"] is False
    assert c["q3_blocker_taxonomy_defined_here"] is False


def test_q3_q8_and_runtime_remain_deferred() -> None:
    data = load_contract()
    assert all(data["deferred_boundaries"].values())
    assert data["storage_boundary"]["semantic_contract_only"] is True
    assert data["storage_boundary"]["live_sqlite_runtime_enabled"] is False
    assert all(v is False for v in data["current_capabilities"].values())


def test_human_contract_contains_required_semantics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "maximum_unresolved_round_trips_per_question_thread: 5",
        "per unresolved question thread",
        "What counts as a round trip",
        "Round 5 boundary",
        "do not create round six",
        "Escalation packet",
        "waiting_on_clarification_escalation",
        "does not imply `RETURN` or `HOLD`",
        "This Q2 condition is not the Q3 blocker taxonomy.",
        "Runtime boundary",
        "deterministic same-phase closeout",
    ):
        assert fragment in text


def test_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q2 bounded clarification and escalation validation PASSED" in cp.stdout


def test_validator_is_in_canonical_check_catalog() -> None:
    checks = {c.check_id: c for c in build_checks()}
    check = checks["q2_bounded_clarification_and_escalation_validation"]
    assert check.title == "Q2 bounded clarification"
    assert check.command[-1] == "scripts/validation/validate_q2_bounded_clarification_and_escalation.py"
