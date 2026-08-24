#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "coordination/standards/governance/phase_boundary_progression_gate_policy_v0_1.yaml"
CURRENT = ROOT / "coordination/releases/current.yaml"
SEQUENCE = ROOT / (
    "coordination/roadmaps/details/forprint_system_blueprint/continuity/prompt_sequence_v0_1.yaml"
)
Q2 = ROOT / (
    "coordination/internal_work/blueprint/governance/"
    "2026-08-24__blueprint__q2_bounded_clarification_activation_v0_1.yaml"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"{path}: root must be mapping")
    return data


def validate() -> None:
    policy = load(POLICY)
    require(
        policy["metadata"]["standard_id"] == "phase_boundary_progression_gate_policy_v0_1",
        "policy id drift",
    )

    manual = policy["manual_progress_confirmation"]
    require(manual["scope"] == "phase_boundary_only", "manual gate scope drift")
    require(
        manual["required_for_same_phase_advance"] is False, "same-phase manual gate reintroduced"
    )
    require(
        manual["silence_counts_as_boundary_approval"] is False, "boundary silence cannot approve"
    )
    require(
        set(manual["required_at_boundaries"]) == {"B->Q", "Q->H10", "H10->H11", "H11->AUT"},
        "phase boundary set drift",
    )

    intra = policy["intra_phase_progression"]
    require(intra["deterministic_closure_authorized"] is True, "deterministic closure disabled")
    require(
        intra["deterministic_next_activation_authorized"] is True, "same-phase activation disabled"
    )
    require(
        intra["new_operator_accept_token_required"] is False, "same-phase ACCEPT token required"
    )
    require(
        intra["new_operator_activate_token_required"] is False, "same-phase ACTIVATE token required"
    )
    require(intra["gate_failure_effect"] == "stop_fail_closed", "gate failure must stop")
    required_gates = set(intra["required_gates"])
    for gate in (
        "git_release_authority_revalidated",
        "dependency_eligibility_revalidated",
        "package_semantic_oracle_pass",
        "canonical_project_checks_pass",
        "publication_remote_containment_satisfied",
        "wip_one_preserved",
        "no_pending_manual_authority_decision",
        "next_package_same_phase_and_eligible",
    ):
        require(gate in required_gates, f"required gate missing: {gate}")

    operating = policy["current_operating_mode"]
    require(operating["transaction_execution"] == "explicit_user_run", "current mode drift")
    require(operating["background_commit_enabled"] is False, "background commit enabled")
    require(operating["background_push_enabled"] is False, "background push enabled")
    require(
        operating["manual_semantic_progress_confirmation_per_same_phase_package"] is False,
        "same-phase manual progress confirmation reintroduced",
    )

    semantics = policy["acceptance_semantics"]
    require(
        "deterministic_phase_gate"
        in semantics["blueprint_internal_package_acceptance_basis_allowed"],
        "deterministic phase acceptance basis missing",
    )
    require(
        semantics["deterministic_phase_gate_is_module_prompt_accept"] is False,
        "package closure collapsed into module prompt ACCEPT",
    )
    require(
        semantics["module_or_business_prompt_automatic_accept_authorized"] is False,
        "module/business automatic ACCEPT enabled",
    )
    require(
        semantics["automatic_return_or_hold_authorized"] is False,
        "automatic RETURN/HOLD enabled",
    )

    q_track = policy["q_track"]
    require(q_track["phase_id"] == "Q", "Q phase id drift")
    require(
        q_track["same_phase_packages"] == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8"],
        "Q phase package map drift",
    )
    require(
        q_track["q2_to_q3_manual_progress_confirmation_required"] is False,
        "Q2->Q3 manual gate reintroduced",
    )
    require(
        q_track["q8_to_h10_manual_phase_boundary_confirmation_required"] is True,
        "Q->H10 manual phase gate lost",
    )

    require(
        all(value is False for value in policy["runtime_boundaries"].values()),
        "runtime/destructive capability enabled",
    )

    current = load(CURRENT)
    current_policy = current["progression_gate_policy"]
    require(
        current_policy["standard_id"] == policy["metadata"]["standard_id"],
        "current policy id mismatch",
    )
    require(current_policy["current_phase"] == "Q", "current phase must be Q")
    require(
        current_policy["intra_phase_operator_accept_confirmation_required"] is False,
        "current release same-phase ACCEPT gate drift",
    )
    require(
        current_policy["intra_phase_operator_activation_confirmation_required"] is False,
        "current release same-phase activation gate drift",
    )
    require(
        current_policy["background_push_enabled"] is False,
        "current release enabled background push",
    )

    sequence = load(SEQUENCE)
    seq_policy = sequence["phase_boundary_progression_policy"]
    require(
        seq_policy["standard_id"] == policy["metadata"]["standard_id"],
        "sequence policy id mismatch",
    )
    require(seq_policy["current_phase"] == "Q", "sequence current phase drift")
    require(
        seq_policy["intra_phase_operator_accept_confirmation_required"] is False,
        "sequence same-phase ACCEPT gate drift",
    )
    require(
        seq_policy["intra_phase_operator_activation_confirmation_required"] is False,
        "sequence same-phase activation gate drift",
    )

    q2 = load(Q2)
    reconcile = q2["progression_policy_reconciliation"]
    require(
        reconcile["policy_id"] == policy["metadata"]["standard_id"],
        "Q2 reconciliation policy mismatch",
    )
    require(reconcile["q2_to_q3_same_phase"] is True, "Q2->Q3 same-phase relation lost")
    require(
        reconcile["q2_to_q3_operator_progress_confirmation_required"] is False,
        "Q2->Q3 manual progress gate reintroduced",
    )
    boundaries = q2["boundaries"]
    require(
        boundaries["same_phase_deterministic_next_activation_authorized"] is True,
        "Q2 same-phase deterministic advance disabled",
    )
    require(
        boundaries["automatic_module_or_business_prompt_acceptance"] is False,
        "Q2 enabled module/business automatic accept",
    )
    require(
        boundaries["unbounded_or_cross_phase_automatic_next_activation"] is False,
        "Q2 enabled cross-phase automatic advance",
    )


def main() -> int:
    validate()
    print("Phase-boundary progression gate policy validation PASSED")
    print("manual_progress_confirmation_scope=phase_boundary_only")
    print("same_phase_manual_accept_confirmation_required=false")
    print("same_phase_manual_activation_confirmation_required=false")
    print("same_phase_deterministic_progression_authorized=true")
    print("module_business_automatic_accept_authorized=false")
    print("manual_exception_authority_preserved=true")
    print("q2_to_q3_manual_progress_confirmation_required=false")
    print("q8_to_h10_manual_phase_boundary_confirmation_required=true")
    print("background_push_enabled=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
