from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"

spec = importlib.util.spec_from_file_location("_cf10_dispatch_exception", SOURCE)
assert spec and spec.loader
dispatch_intent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch_intent
spec.loader.exec_module(dispatch_intent)


EXACT = dict(dispatch_intent.CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1)


def validate(**overrides):
    values = dict(EXACT)
    values.update(overrides)
    return dispatch_intent.validate_cf10_internal_zero_stage_exception(
        work_id=values["work_id"],
        module=values["module"],
        work_front=values["work_front"],
        task_prompt_id=values["task_prompt_id"],
        task_module_root=values["task_module_root"],
        execution_profile=values["execution_profile"],
        procedure_id=values["procedure_id"],
        worker_id=values["worker_id"],
        attempt_id=values["attempt_id"],
        blueprint_ai_trial_ready=values.get("blueprint_ai_trial_ready", False),
    )


def test_exact_cf10_binding_is_eligible_but_not_dispatch_authority() -> None:
    result = validate()
    assert result["eligible"] is True
    assert result["scope"] == "CF10_U180J_EXACT_BINDING_ONLY"
    assert result["broad_blueprint_ai_trial_ready_required"] is False
    assert result["broad_blueprint_ai_trial_ready_observed"] is False
    assert result["assistant_ack_validated"] is False
    assert result["explicit_dispatch_decision_recorded"] is False
    assert result["worker_process_launch_allowed"] is False
    assert result["canonical_attempt_ledger_append_allowed"] is False
    assert all(value is False for value in result["authority"].values())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("work_id", "u999"),
        ("module", "logistics_service"),
        ("work_front", "coordination/work_fronts/other.yaml"),
        ("task_prompt_id", "other-task"),
        ("task_module_root", "/tmp/other"),
        ("execution_profile", "deep-dev"),
        ("procedure_id", "other_procedure"),
        ("worker_id", "worker-02"),
        ("attempt_id", "cf10-u180j-a003"),
    ],
)
def test_any_binding_mismatch_fails_closed(field: str, value: str) -> None:
    with pytest.raises(ValueError, match="binding mismatch"):
        validate(**{field: value})


def test_broad_trial_ready_true_is_not_the_cf10_exception() -> None:
    with pytest.raises(ValueError, match="BLUEPRINT_AI_TRIAL_READY=false"):
        validate(blueprint_ai_trial_ready=True)


def test_prepare_wrapper_stops_at_ack_gate(monkeypatch) -> None:
    def fake_prepare(**kwargs):
        assert kwargs["module"] == "forprint_system_blueprint"
        assert kwargs["execution_profile"] == "light-maintenance"
        assert kwargs["procedure_id"] == "governed_canonical_mutation"
        return {
            "mode": "TASK_EXECUTION",
            "state": "AWAITING_ASSISTANT_ACK",
            "assistant_ack_validated": False,
            "authority": {
                "execution_authority_granted": False,
                "dispatch_authority_granted": False,
                "worker_dispatch_performed": False,
                "external_dispatch_allowed": False,
                "release_allowed": False,
                "push_allowed": False,
                "merge_allowed": False,
            },
            "next_required_human_boundary": "ASSISTANT_ACK_REQUIRED",
        }

    monkeypatch.setattr(
        dispatch_intent,
        "prepare_cf09_task_execution",
        fake_prepare,
    )
    prepared = dispatch_intent.prepare_cf10_internal_zero_stage_pre_dispatch(
        root=ROOT,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a001",
    )
    assert prepared["state"] == "AWAITING_ASSISTANT_ACK"
    assert prepared["assistant_ack_validated"] is False
    assert prepared["worker_process_launch_allowed"] is False
    assert prepared["canonical_attempt_ledger_append_allowed"] is False
    assert prepared["cf10_internal_zero_stage_exception"]["eligible"] is True
