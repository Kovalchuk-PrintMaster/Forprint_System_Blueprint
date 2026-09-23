from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from scripts.coordination import continuity_lifecycle as lifecycle

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/"
    "control_foundation_near_horizon_program_v0_1.yaml"
)
RECONTRACT = (
    ROOT / "coordination/standards/automation/roadmap_execution_reconciliation_contract_v0_1.yaml"
)
CONTINUITY_CONTRACT = ROOT / "coordination/standards/automation/continuity_contract_v0_1.yaml"


def test_active_control_foundation_has_no_step_execution_state_fields() -> None:
    program = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    steps = program["steps"]
    assert steps
    assert [step["id"] for step in steps] == [
        f"CF-{index:02d}" for index in range(1, len(steps) + 1)
    ]
    assert all("state" not in step for step in program["steps"])
    rr = program["roadmap_execution_reconciliation"]
    assert rr["control_foundation_manual_step_state_fields"] == "REMOVED"
    assert rr["lifecycle_choke_points"] == "HARD_GATED_PLAN_ACTIVATE_CHECKPOINT_CLOSE"


def test_contracts_record_hard_gate_and_remaining_legacy_retirement() -> None:
    recon = yaml.safe_load(RECONTRACT.read_text(encoding="utf-8"))
    migration = recon["migration"]
    assert migration["control_foundation_manual_step_state_fields"] == "removed"
    assert (
        migration["legacy_terminal_state_fields"]
        == "retired_to_explicit_historical_completion_evidence"
    )

    continuity = yaml.safe_load(CONTINUITY_CONTRACT.read_text(encoding="utf-8"))
    enforcement = continuity["lifecycle"]["enforcement"]
    assert enforcement["roadmap_reconciliation_gate_runtime_enforced"] is True
    assert enforcement["roadmap_reconciliation_gate_actions"] == [
        "plan",
        "activate",
        "checkpoint",
        "close",
    ]
    assert enforcement["roadmap_reconciliation_gate_fail_closed_when_installed"] is True
    assert enforcement["standalone_portability_without_reconciliation_controller"] is True


def test_lifecycle_choke_points_call_reconciliation_gate() -> None:
    assert "_assert_roadmap_reconciliation_gate" in inspect.getsource(lifecycle.plan)
    assert "_assert_roadmap_reconciliation_gate" in inspect.getsource(lifecycle.activate)
    assert "_assert_roadmap_reconciliation_gate" in inspect.getsource(
        lifecycle.assert_checkpoint_allowed
    )
    assert "_assert_roadmap_reconciliation_gate" in inspect.getsource(lifecycle.close)


def _install_fake_gate(root: Path, *, return_code: int) -> None:
    contract = (
        root / "coordination/standards/automation/"
        "roadmap_execution_reconciliation_contract_v0_1.yaml"
    )
    controller = root / "scripts/coordination/roadmap_execution_reconciliation.py"
    contract.parent.mkdir(parents=True, exist_ok=True)
    controller.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text("schema_version: fixture\n", encoding="utf-8")
    controller.write_text(
        "def compute(root):\n"
        "    return ({'roadmaps': [{'roadmap_id': 'fixture-roadmap', "
        "'steps': [{'step_id': 'fixture-step', 'work_id': 'u-fixture'}]}]}, {})\n\n"
        "def gate(root, *, action, roadmap_id, step_id, work_id):\n"
        f"    return {return_code}\n",
        encoding="utf-8",
    )


def test_programmatic_gate_passes_for_unique_bound_work(tmp_path: Path) -> None:
    _install_fake_gate(tmp_path, return_code=0)
    assert (
        lifecycle._assert_roadmap_reconciliation_gate(
            root=tmp_path,
            action="plan",
            work_id="u-fixture",
        )
        is True
    )


def test_programmatic_gate_fails_closed_when_installed_gate_blocks(
    tmp_path: Path,
) -> None:
    _install_fake_gate(tmp_path, return_code=4)
    with pytest.raises(lifecycle.LifecycleError, match="roadmap reconciliation gate blocked"):
        lifecycle._assert_roadmap_reconciliation_gate(
            root=tmp_path,
            action="plan",
            work_id="u-fixture",
        )


def test_programmatic_gate_preserves_standalone_portability(tmp_path: Path) -> None:
    assert (
        lifecycle._assert_roadmap_reconciliation_gate(
            root=tmp_path,
            action="plan",
            work_id="u-fixture",
        )
        is False
    )
