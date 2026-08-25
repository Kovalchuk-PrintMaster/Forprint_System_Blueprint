from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/logistics_clarification_reference_validation_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q8_logistics_clarification_reference_validation.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_exact_eleven_logistics_reference_assertions() -> None:
    assertions = load_contract()["reference_assertions"]
    assert set(assertions) == {
        "recoverable_clarification_does_not_return_prompt",
        "module_and_operator_routing_identities_representable",
        "five_round_escalation_deterministic",
        "blocker_reason_explicit",
        "released_prompt_immutable",
        "scope_adjustment_separate_evidence",
        "completion_preserves_deviations",
        "attention_state_visible",
        "no_automatic_module_business_prompt_accept",
        "no_unbounded_or_cross_phase_automatic_next_release",
        "no_blueprint_write_into_module_repo",
    }
    assert all(assertions.values())


def test_h9_reference_provenance_is_bound() -> None:
    refs = load_contract()["reference_provenance"]
    assert refs["module_id"] == "logistics_service"
    assert refs["repository"] == "forprint_logistics_service"
    assert refs["implementation_commit"] == "4a3a8cf3d2809c3a7f49268fa62334ed24b5fa90"
    assert refs["publication_seal_commit"] == "96284d829bb5cdcd564f44c51bdbe681f9d26cae"
    assert refs["h9_operator_acceptance_explicit"] is True
    assert refs["h9_automatic_acceptance"] is False


def test_prior_b1_logistics_reference_evidence_is_bound() -> None:
    evidence = load_contract()["prior_b1_logistics_evidence"]
    assert evidence["result"] == "B1_LOGISTICS_REFERENCE_VALIDATION_PASS"
    assert evidence["lifecycle_scenarios_passed"] == 9
    assert evidence["lifecycle_scenarios_total"] == 9
    assert evidence["discovery_read_only"] is True
    assert evidence["discovery_idempotent"] is True
    assert evidence["live_blueprint_unchanged"] is True
    assert evidence["live_logistics_unchanged"] is True


def test_q8_does_not_cross_h10_boundary() -> None:
    boundary = load_contract()["phase_boundary"]
    assert boundary["next_boundary"] == "Q->H10"
    assert boundary["manual_progress_confirmation_required"] is True
    assert boundary["silence_counts_as_approval"] is False
    assert boundary["h10_activated_by_q8_implementation"] is False
    assert boundary["q8_implementation_is_boundary_approval"] is False


def test_q8_runtime_and_cross_repo_capabilities_remain_disabled() -> None:
    assert all(value is False for value in load_contract()["current_capabilities"].values())


def test_human_standard_contains_exact_reference_intent() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "Q8 validates the combined Q1-Q7 semantics against Logistics",
        "Canonical reference assertions",
        "Recoverable clarification does not RETURN the prompt",
        "Module and operator routing identities are representable",
        "Five-round escalation is deterministic",
        "Blocker reason is explicit",
        "Released prompt remains immutable",
        "Scope adjustment is separate evidence",
        "Completion preserves deviations",
        "Attention state is visible",
        "No automatic module/business prompt ACCEPT",
        "No unbounded or cross-phase automatic next release",
        "No Blueprint write into the module repository",
        "`Q8 -> H10`",
        "Silence is not approval.",
        "does not itself close Q8 and does not activate H10",
    ):
        assert fragment in text


def test_q8_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q8 Logistics clarification reference validation PASSED" in cp.stdout


def test_q8_validator_is_in_canonical_check_catalog() -> None:
    checks = {check.check_id: check for check in build_checks()}
    check = checks["q8_logistics_clarification_reference_validation"]
    assert check.title == "Q8 Logistics clarification reference"
    assert check.command[-1] == "scripts/validation/validate_q8_logistics_clarification_reference_validation.py"
