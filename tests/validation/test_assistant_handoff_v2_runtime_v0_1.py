from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py"
spec = importlib.util.spec_from_file_location("assistant_handoff_v2_runtime", RUNTIME)
assert spec is not None and spec.loader is not None
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def test_project_onboard_runtime_is_bounded() -> None:
    manifest = runtime.compile_runtime_manifest(ROOT, launch_mode="PROJECT_ONBOARD")
    assert manifest["launch_mode"] == "PROJECT_ONBOARD"
    assert manifest["authority"]["execution_authority_granted"] is False
    assert manifest["authority"]["dispatch_authority_granted"] is False
    assert manifest["s2_scope"]["dispatcher_integration_deferred_to_cf09"] is True
    assert len(manifest["handoff_manifest_sha256"]) == 64


def test_project_onboard_rejects_task_bindings() -> None:
    with pytest.raises(runtime.RuntimeErrorV2, match="does not accept task-execution bindings"):
        runtime.compile_runtime_manifest(
            ROOT, launch_mode="PROJECT_ONBOARD", profile_id="standard-dev"
        )


def test_task_execution_requires_front_first() -> None:
    with pytest.raises(runtime.RuntimeErrorV2, match="TASK_EXECUTION requires --front"):
        runtime.compile_runtime_manifest(ROOT, launch_mode="TASK_EXECUTION")


def test_manifest_hash_is_self_excluding() -> None:
    manifest = runtime.compile_runtime_manifest(ROOT, launch_mode="PROJECT_ONBOARD")
    assert runtime._manifest_hash(manifest) == manifest["handoff_manifest_sha256"]


def test_only_two_launch_modes_exist() -> None:
    assert runtime.LAUNCH_MODES == ("PROJECT_ONBOARD", "TASK_EXECUTION")


def test_task_context_evidence_carries_manual_internal_work_id(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runtime,
        "_run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=(
                "TASK_CONTEXT_COMPILER=PASS\n"
                "TASK_CONTEXT_ADAPTER=CONTROL_PLANE\n"
                "TASK_CONTEXT_MODE=MANUAL_INTERNAL\n"
                "TASK_CONTEXT_ID=" + ("a" * 64) + "\n"
                "TASK_ID=fixture-task\n"
                "MODULE_ID=forprint_system_blueprint\n"
                "WORK_ID=u180j\n"
                "MUTATION_PERFORMED=false\n"
            ),
        ),
    )

    evidence = runtime._task_context_evidence(
        ROOT,
        "fixture-task",
        ".",
        "forprint_system_blueprint",
    )

    assert evidence["task_context_mode"] == "MANUAL_INTERNAL"
    assert evidence["work_id"] == "u180j"


def test_task70_runtime_resume_uses_exact_internal_work_binding() -> None:
    manifest = runtime.compile_runtime_manifest(
        ROOT,
        launch_mode="TASK_EXECUTION",
        front=(
            "coordination/work_fronts/"
            "cf10_validation_check_pipeline_profile_and_optimization_v0_1.yaml"
        ),
        profile_id="light-maintenance",
        procedure_id="governed_canonical_mutation",
        prompt_id=(
            "cf10-validation-check-pipeline-profile-and-optimization-v0-1"
        ),
        module_root=".",
        module="forprint_system_blueprint",
    )

    task_context = manifest["base_context"]["task_execution_context"]
    resume = manifest["resume_coordinates"]
    cursor = manifest["lifecycle_roadmap_cursor"]

    assert task_context["task_context_mode"] == "MANUAL_INTERNAL"
    assert task_context["work_id"] == "u180j"
    assert resume["work_id"] == "u180j"
    assert resume["work_state"] == cursor["open_work"]["u180j"]
