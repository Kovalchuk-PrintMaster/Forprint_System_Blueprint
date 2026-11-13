from __future__ import annotations

import ast
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXER = ROOT / "scripts/fix_coordination_metadata.py"
EVIDENCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__coordination_metadata_fixer_"
    "recovery_remediation_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def test_fixer_entrypoint_invokes_mutation_once_with_all_flags() -> None:
    tree = ast.parse(
        FIXER.read_text(encoding="utf-8"),
        filename=str(FIXER),
    )
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _call_name(node) == "fix_module_coordination_metadata"
    ]

    assert len(calls) == 1
    keywords = {
        keyword.arg
        for keyword in calls[0].keywords
        if keyword.arg is not None
    }
    assert keywords == {
        "module_root",
        "update_git_commit",
        "mark_pushed_if_upstream_clean",
    }


def test_remediation_evidence_closes_only_concrete_finding() -> None:
    evidence = _load(EVIDENCE)

    assert evidence["metadata"]["status"] == "implemented_not_closed"
    assert evidence["remediation"]["duplicate_execution_removed"] is True
    assert evidence["remediation"]["current_fix_function_call_count"] == 1
    assert evidence["remediation"][
        "cli_regression_test_asserts_exact_call_count"
    ] == 1

    state = evidence["blocker_state"]
    assert state[
        "coordination_metadata_fixer_duplicate_execution"
    ] == "closed"
    assert state[
        "uncovered_blocking_path_scripts_fix_coordination_metadata"
    ] == "closed"
    assert state["write_flow_recovery_not_fully_verified"] == "remains"
    assert state["closeout_eligible"] is False


def test_operational_and_release_boundaries_remain_gated() -> None:
    evidence = _load(EVIDENCE)
    boundaries = evidence["boundaries"]

    assert boundaries["operational_readiness_review"] == "in_progress"
    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["reference_pilot_migration_authorized"] is False
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["cross_repository_writes_by_builder"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False
    assert boundaries["historical_evidence_rewritten"] is False

    policy = _load(RELEASE_POLICY)
    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
