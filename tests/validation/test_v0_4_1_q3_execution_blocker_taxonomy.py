from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts.run_blueprint_checks import build_checks

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/governance/execution_blocker_taxonomy_v0_1.yaml"
DOC = CONTRACT.with_suffix(".md")
VALIDATOR = ROOT / "scripts/validation/validate_q3_execution_blocker_taxonomy.py"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_q3_separates_conditions_outcome_and_dispositions() -> None:
    sep = load_contract()["semantic_separation"]
    assert sep["coordination_conditions"] == ["clarification_required", "execution_blocked"]
    assert sep["executor_outcomes"] == ["unable_to_execute"]
    assert sep["governance_dispositions"] == ["RETURN", "HOLD"]
    assert sep["conditions_are_prompt_dispositions"] is False
    assert sep["unable_to_execute_is_prompt_disposition"] is False
    assert sep["automatic_condition_to_return_hold"] is False


def test_q3_reason_taxonomy_is_exact_and_closed() -> None:
    reasons = load_contract()["reason_taxonomy"]
    assert set(reasons["canonical_reason_codes"]) == {
        "missing_input",
        "ambiguous_requirement",
        "access_required",
        "credential_or_token_expired",
        "external_resource_unavailable",
        "dependency_contract_missing",
        "dependency_module_blocked",
        "provider_api_unavailable",
        "environment_failure",
        "policy_conflict",
        "unsupported_capability",
        "security_boundary",
        "manual_decision_required",
    }
    assert reasons["unknown_reason_allowed"] is False
    assert set(reasons["definitions"]) == set(reasons["canonical_reason_codes"])


def test_execution_blocked_is_scope_bound_not_prompt_disposition() -> None:
    b = load_contract()["blocking_semantics"]
    assert b["execution_blocked_requires_blocking_true"] is True
    assert b["blocking_applies_only_to_declared_affected_scope"] is True
    assert b["whole_prompt_block_requires_explicit_whole_prompt_scope"] is True
    assert b["independent_work_may_continue_when_contract_allows"] is True
    assert b["active_blocker_implies_return"] is False
    assert b["active_blocker_implies_hold"] is False
    assert b["active_blocker_mutates_released_prompt"] is False


def test_blocker_record_requires_scope_reason_and_evidence() -> None:
    blocker = load_contract()["blocker_record"]
    assert blocker["affected_scope_refs_min_items"] == 1
    assert blocker["evidence_refs_required"] is True
    assert "reason_code" in blocker["required_fields"]
    assert "affected_scope_refs" in blocker["required_fields"]
    assert "evidence_refs" in blocker["required_fields"]
    assert blocker["secret_values_allowed"] is False


def test_unable_to_execute_is_executor_evidence_only() -> None:
    unable = load_contract()["unable_to_execute_evidence"]
    assert unable["is_executor_evidence"] is True
    assert unable["is_blueprint_decision"] is False
    assert unable["automatically_returns_prompt"] is False
    assert unable["automatically_holds_prompt"] is False
    assert unable["safe_next_options_are_advisory"] is True
    assert "attempted_or_verified" in unable["required_fields"]


def test_q2_bridge_preserves_question_history() -> None:
    q2 = load_contract()["q2_bridge"]
    assert q2["q2_question_thread_remains_authoritative"] is True
    assert q2["q3_may_rewrite_q2_question_history"] is False
    assert q2["escalated_blocking_question_may_project_execution_blocked"] is True
    assert q2["projection_requires_explicit_q3_reason"] is True


def test_q4_q8_and_runtime_remain_deferred() -> None:
    data = load_contract()
    assert all(data["deferred_boundaries"].values())
    assert all(value is False for value in data["current_capabilities"].values())


def test_human_standard_contains_required_distinctions() -> None:
    text = DOC.read_text(encoding="utf-8")
    for fragment in (
        "A blocker is evidence/condition, not an automatic prompt disposition.",
        "`clarification_required`",
        "`execution_blocked`",
        "`unable_to_execute`",
        "`RETURN`",
        "`HOLD`",
        "Canonical blocker reason codes",
        "affected scope",
        "Independent prompt work may continue",
        "does not itself issue RETURN/HOLD",
        "Separation from Q4-Q8",
        "Runtime boundary",
    ):
        assert fragment in text


def test_q3_validator_passes() -> None:
    cp = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    assert "Q3 execution blocker taxonomy validation PASSED" in cp.stdout


def test_q3_validator_is_in_canonical_check_catalog() -> None:
    checks = {check.check_id: check for check in build_checks()}
    check = checks["q3_execution_blocker_taxonomy_validation"]
    assert check.title == "Q3 execution blocker taxonomy"
    assert check.command[-1] == "scripts/validation/validate_q3_execution_blocker_taxonomy.py"
