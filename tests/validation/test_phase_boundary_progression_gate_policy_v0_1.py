from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "coordination/standards/governance/phase_boundary_progression_gate_policy_v0_1.yaml"
DOC = POLICY.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_phase_boundary_progression_gate_policy.py"


def load_policy() -> dict:
    data = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_manual_progress_confirmation_is_phase_boundary_only() -> None:
    data = load_policy()
    manual = data["manual_progress_confirmation"]
    assert manual["scope"] == "phase_boundary_only"
    assert manual["required_for_same_phase_advance"] is False
    assert manual["silence_counts_as_boundary_approval"] is False


def test_q_track_is_one_same_phase_sequence() -> None:
    data = load_policy()
    q = data["q_track"]
    assert q["same_phase_packages"] == [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
        "Q7",
        "Q8",
    ]
    assert q["q2_to_q3_manual_progress_confirmation_required"] is False
    assert q["q8_to_h10_manual_phase_boundary_confirmation_required"] is True


def test_same_phase_advance_is_deterministic_but_fail_closed() -> None:
    data = load_policy()
    intra = data["intra_phase_progression"]
    assert intra["deterministic_closure_authorized"] is True
    assert intra["deterministic_next_activation_authorized"] is True
    assert intra["new_operator_accept_token_required"] is False
    assert intra["new_operator_activate_token_required"] is False
    assert intra["gate_failure_effect"] == "stop_fail_closed"
    assert "wip_one_preserved" in intra["required_gates"]
    assert "dependency_eligibility_revalidated" in intra["required_gates"]


def test_module_business_prompt_acceptance_remains_manual_governance() -> None:
    data = load_policy()
    semantics = data["acceptance_semantics"]
    assert semantics["deterministic_phase_gate_is_module_prompt_accept"] is False
    assert semantics["module_or_business_prompt_automatic_accept_authorized"] is False
    assert semantics["automatic_return_or_hold_authorized"] is False


def test_current_operating_mode_keeps_user_run_and_no_background_push() -> None:
    data = load_policy()
    operating = data["current_operating_mode"]
    assert operating["transaction_execution"] == "explicit_user_run"
    assert operating["background_commit_enabled"] is False
    assert operating["background_push_enabled"] is False
    assert operating["manual_semantic_progress_confirmation_per_same_phase_package"] is False


def test_human_policy_contains_scope_distinction_and_exception_rules() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "## Manual gate rule",
        "Within the same phase",
        "## Deterministic intra-phase closure",
        "package closure is not module prompt ACCEPT",
        "## Manual exception decisions remain manual",
        "Q2 -> Q3 does not require",
        "Q8 closure -> H10",
        "transactions remain explicit and user-run",
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
    assert "Phase-boundary progression gate policy validation PASSED" in cp.stdout
