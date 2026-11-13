from __future__ import annotations

import pytest

from scripts.coordination.control_plane import dispatch_intent as dispatch


def _binding_kwargs(attempt_id: str, *, worker_id: str | None = None) -> dict:
    binding = dict(dispatch.CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1)
    return {
        "work_id": binding["work_id"],
        "module": binding["module"],
        "work_front": binding["work_front"],
        "task_prompt_id": binding["task_prompt_id"],
        "task_module_root": binding["task_module_root"],
        "execution_profile": binding["execution_profile"],
        "procedure_id": binding["procedure_id"],
        "worker_id": worker_id or binding["worker_id"],
        "attempt_id": attempt_id,
        "blueprint_ai_trial_ready": False,
    }


def test_cf10_first_attempt_a001_remains_valid() -> None:
    result = dispatch.validate_cf10_internal_zero_stage_exception(
        **_binding_kwargs("cf10-u180j-a001")
    )
    assert result["attempt_id"] == "cf10-u180j-a001"
    assert result["cf10_retry_binding"]["is_retry"] is False
    assert result["cf10_retry_binding"]["allowed_attempt_ids"] == [
        "cf10-u180j-a001",
        "cf10-u180j-a002",
    ]


def test_cf10_bounded_retry_a002_is_valid() -> None:
    result = dispatch.validate_cf10_internal_zero_stage_exception(
        **_binding_kwargs("cf10-u180j-a002")
    )
    assert result["attempt_id"] == "cf10-u180j-a002"
    assert result["cf10_retry_binding"]["is_retry"] is True
    assert result["cf10_retry_binding"]["retry_of_attempt_id"] == (
        "cf10-u180j-a001"
    )


def test_cf10_a003_is_not_implicitly_authorized() -> None:
    with pytest.raises(
        ValueError,
        match="CF-10 internal zero-stage binding mismatch: attempt_id",
    ):
        dispatch.validate_cf10_internal_zero_stage_exception(
            **_binding_kwargs("cf10-u180j-a003")
        )


def test_cf10_retry_does_not_widen_worker_binding() -> None:
    with pytest.raises(ValueError):
        dispatch.validate_cf10_internal_zero_stage_exception(
            **_binding_kwargs(
                "cf10-u180j-a002",
                worker_id="worker-02",
            )
        )


def test_cf10_retry_does_not_widen_broad_trial_gate() -> None:
    kwargs = _binding_kwargs("cf10-u180j-a002")
    kwargs["blueprint_ai_trial_ready"] = True
    with pytest.raises(ValueError):
        dispatch.validate_cf10_internal_zero_stage_exception(**kwargs)
