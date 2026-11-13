from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.coordination.control_plane.tasking import (
    compile_task_envelope,
    validate_task_envelope,
)
from scripts.coordination.control_plane.tasking.sources import (
    external_prompt_queue_source,
    manual_internal_source,
)

COMMON = dict(
    work_id="u180j",
    work_front_id="wf-cf10-fixture",
    objective="One bounded test.",
    instructions=["Inspect and change only the declared target."],
    acceptance=["Focused validation passes."],
    stop_conditions=["Stop if scope widening is required."],
    execution_profile_id="light-maintenance",
    execution_profile_revision="r1",
    procedure_id="governed_canonical_mutation",
    procedure_revision="0.1.0",
)


def test_sources_share_core_envelope_shape() -> None:
    manual = compile_task_envelope(
        task_id="manual",
        module_id="forprint_system_blueprint",
        source=manual_internal_source(
            artifact_ref="coordination/internal_work/blueprint/worker_tasks/manual.yaml"
        ),
        **COMMON,
    )
    external = compile_task_envelope(
        task_id="external",
        module_id="logistics_service",
        source=external_prompt_queue_source(
            queue_ref="coordination/outgoing_prompts/logistics_service/index.yaml",
            prompt_id="fixture",
            approved_prompt_ref=(
                "coordination/outgoing_prompts/logistics_service/approved/fixture.md"
            ),
        ),
        **COMMON,
    )
    for key in (
        "work", "objective", "instructions", "acceptance", "stop_conditions",
        "execution_profile", "procedure", "authority",
    ):
        assert manual[key] == external[key]


def test_task_envelope_never_grants_execution_authority() -> None:
    envelope = compile_task_envelope(
        task_id="manual",
        module_id="forprint_system_blueprint",
        source=manual_internal_source(
            artifact_ref="coordination/internal_work/blueprint/worker_tasks/manual.yaml"
        ),
        **COMMON,
    )
    assert envelope["authority"] == {
        "execution_authority_source": "WORK_FRONT",
        "task_envelope_grants_authority": False,
        "widening_requested": False,
    }


def test_manual_internal_is_not_external_module_bypass() -> None:
    with pytest.raises(ValueError, match="restricted"):
        compile_task_envelope(
            task_id="bad",
            module_id="logistics_service",
            source=manual_internal_source(
                artifact_ref="coordination/internal_work/blueprint/worker_tasks/bad.yaml"
            ),
            **COMMON,
        )


def test_raw_chat_cannot_be_manual_internal_artifact() -> None:
    with pytest.raises(ValueError, match="durable artifact"):
        manual_internal_source(artifact_ref="chat:latest")


def test_forbidden_authority_field_is_rejected_recursively() -> None:
    envelope = compile_task_envelope(
        task_id="manual",
        module_id="forprint_system_blueprint",
        source=manual_internal_source(
            artifact_ref="coordination/internal_work/blueprint/worker_tasks/manual.yaml"
        ),
        **COMMON,
    )
    broken = deepcopy(envelope)
    broken["source"]["release_authority"] = False
    errors = validate_task_envelope(broken)
    assert any("forbidden authority field" in error for error in errors)
