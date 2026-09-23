import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLANNER = "scripts/coordination/plan_safe_mutation_v0_1.py"
VALIDATOR = "scripts/validation/validate_safe_mutation_pipeline_v0_1.py"


def run_planner(*paths: str) -> dict:
    process = subprocess.run(
        [sys.executable, PLANNER, "--json", *paths],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    return json.loads(process.stdout)


def test_safe_mutation_pipeline_validator_passes() -> None:
    process = subprocess.run(
        [sys.executable, VALIDATOR],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert process.returncode == 0, process.stdout
    assert "SAFE_MUTATION_PIPELINE_VALIDATION=PASS" in process.stdout


def test_governance_standard_requires_standards_validation_and_index_refresh() -> None:
    plan = run_planner(
        "coordination/standards/governance/example_policy.yaml"
    )
    actions = [item["action_id"] for item in plan["actions"]]
    assert "standards_index_validation" in actions
    assert "knowledge_index_build" in actions
    assert "knowledge_index_check" in actions
    assert "EXPLICIT_STANDARDS_INDEX_REGISTRATION" in plan["manual_requirements"]


def test_human_intent_requires_sync_before_final_gates() -> None:
    plan = run_planner(
        "coordination/human_intent/modules/example.yaml"
    )
    actions = [item["action_id"] for item in plan["actions"]]
    assert "human_intent_sync" in actions
    assert actions.index("human_intent_sync") < actions.index("full_pytest")


def test_script_change_gets_index_refresh_lint_and_full_validation() -> None:
    plan = run_planner("scripts/example.py")
    actions = [item["action_id"] for item in plan["actions"]]
    assert "knowledge_index_build" in actions
    assert "ruff_full" in actions
    assert "full_pytest" in actions
    assert "make_check" in actions
    assert "release_authority_guard" in actions
