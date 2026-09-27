from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py"


def load_runtime():
    name = "_cf10_handoff_v2_task_execution_freshness_regression"
    spec = importlib.util.spec_from_file_location(name, RUNTIME)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def task_manifest(procedure_classification: str = "GRAPH_REQUIRED") -> dict:
    procedure = (
        {
            "classification": "GRAPH_REQUIRED",
            "procedure_id": "governed_canonical_mutation",
            "revision": "0.1.0",
            "registry_sha256": "a" * 64,
        }
        if procedure_classification == "GRAPH_REQUIRED"
        else {
            "classification": "NOT_REQUIRED",
            "reason": "read-only projection task",
        }
    )
    return {
        "schema_version": "forprint_assistant_handoff_v2_runtime_manifest_v0_1",
        "launch_mode": "TASK_EXECUTION",
        "handoff_manifest_sha256": "b" * 64,
        "source_state_fingerprint": "c" * 64,
        "lifecycle_roadmap_cursor": {"roadmap_sync": "IN_SYNC"},
        "work_front_or_project_onboard_not_applicable_reason": {
            "front": (
                "coordination/work_fronts/"
                "cf10_local_dispatcher_telegram_operator_surface_v0_1.yaml"
            ),
            "work_front_id": (
                "wf-cf10-local-dispatcher-telegram-operator-surface-v0-1"
            ),
            "validation": "PASS",
        },
        "execution_profile_revision_for_task_execution": {
            "profile_id": "light-maintenance",
            "revision": "r1",
        },
        "governed_procedure_revision_or_not_required_reason": procedure,
        "resume_coordinates": {
            "launch_mode": "TASK_EXECUTION",
            "front": (
                "coordination/work_fronts/"
                "cf10_local_dispatcher_telegram_operator_surface_v0_1.yaml"
            ),
            "profile_id": "light-maintenance",
            "prompt_id": "cf10-local-dispatcher-telegram-operator-surface-v0-1",
            "module_root": ".",
            "procedure_id": (
                "governed_canonical_mutation"
                if procedure_classification == "GRAPH_REQUIRED"
                else None
            ),
        },
        "base_context": {
            "task_execution_context": {
                "prompt_id": "cf10-local-dispatcher-telegram-operator-surface-v0-1",
                "module_root": ".",
                "module": "forprint_system_blueprint",
                "task_context_id": "d" * 64,
                "validation": "PASS",
            }
        },
    }


def result_for(manifest: dict) -> dict:
    return {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": manifest["handoff_manifest_sha256"],
        "attempt_id": "cf10-u180j-a014",
        "status": "PASS",
        "changed_paths": [
            "scripts/coordination/control_plane/telegram_operator.py"
        ],
        "validation_evidence": ["pytest:PASS"],
        "self_repair_attempts": [],
        "resume_coordinates": {
            "attempt_id": "cf10-u180j-a014",
            "handoff_manifest_sha256": manifest["handoff_manifest_sha256"],
            "source_state_fingerprint": manifest["source_state_fingerprint"],
            "lifecycle_roadmap_cursor": manifest["lifecycle_roadmap_cursor"],
        },
        "unresolved_findings": [],
    }


def install_stubs(monkeypatch, runtime, origin):
    monkeypatch.setattr(
        runtime,
        "_load_result_runtime",
        lambda root: SimpleNamespace(
            validate_with_bounded_self_repair=lambda *args, **kwargs: {
                "valid": True,
                "result": result_for(origin),
                "errors": [],
                "repair_attempt_count": 0,
            }
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_load_freshness_resume_runtime",
        lambda root: SimpleNamespace(
            validate_freshness_and_resume=lambda *args, **kwargs: {
                "valid": True,
                "errors": [],
            }
        ),
    )


def test_task_execution_replays_exact_bindings(monkeypatch) -> None:
    runtime = load_runtime()
    origin = task_manifest()
    install_stubs(monkeypatch, runtime, origin)
    observed = {}

    def fake_compile(root, *, launch_mode, **kwargs):
        observed["launch_mode"] = launch_mode
        observed.update(kwargs)
        return dict(origin)

    monkeypatch.setattr(runtime, "compile_runtime_manifest", fake_compile)
    report = runtime.validate_result_for_return(ROOT, origin, result_for(origin))

    assert report["valid"] is True
    assert observed == {
        "launch_mode": "TASK_EXECUTION",
        "front": (
            "coordination/work_fronts/"
            "cf10_local_dispatcher_telegram_operator_surface_v0_1.yaml"
        ),
        "profile_id": "light-maintenance",
        "prompt_id": "cf10-local-dispatcher-telegram-operator-surface-v0-1",
        "module_root": ".",
        "module": "forprint_system_blueprint",
        "procedure_id": "governed_canonical_mutation",
        "procedure_not_required_reason": None,
    }


def test_not_required_procedure_is_replayed(monkeypatch) -> None:
    runtime = load_runtime()
    origin = task_manifest("NOT_REQUIRED")
    install_stubs(monkeypatch, runtime, origin)
    observed = {}

    def fake_compile(root, *, launch_mode, **kwargs):
        observed.update(kwargs)
        return dict(origin)

    monkeypatch.setattr(runtime, "compile_runtime_manifest", fake_compile)
    report = runtime.validate_result_for_return(ROOT, origin, result_for(origin))

    assert report["valid"] is True
    assert observed["procedure_id"] is None
    assert observed["procedure_not_required_reason"] == "read-only projection task"


def test_missing_origin_binding_fails_closed() -> None:
    runtime = load_runtime()
    origin = task_manifest()
    del origin["resume_coordinates"]["front"]
    del origin["work_front_or_project_onboard_not_applicable_reason"]["front"]

    with pytest.raises(
        runtime.RuntimeErrorV2,
        match="TASK_EXECUTION origin binding missing: front",
    ):
        runtime._task_execution_recompile_bindings(origin)


def test_project_onboard_remains_launch_mode_only(monkeypatch) -> None:
    runtime = load_runtime()
    origin = {
        "launch_mode": "PROJECT_ONBOARD",
        "handoff_manifest_sha256": "b" * 64,
        "source_state_fingerprint": "c" * 64,
        "lifecycle_roadmap_cursor": {"roadmap_sync": "IN_SYNC"},
    }
    result = {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": "b" * 64,
        "attempt_id": "cf10-u180j-a014",
        "status": "PASS",
        "changed_paths": [],
        "validation_evidence": ["pytest:PASS"],
        "self_repair_attempts": [],
        "resume_coordinates": {},
        "unresolved_findings": [],
    }

    monkeypatch.setattr(
        runtime,
        "_load_result_runtime",
        lambda root: SimpleNamespace(
            validate_with_bounded_self_repair=lambda *args, **kwargs: {
                "valid": True,
                "result": result,
                "errors": [],
            }
        ),
    )
    monkeypatch.setattr(
        runtime,
        "_load_freshness_resume_runtime",
        lambda root: SimpleNamespace(
            validate_freshness_and_resume=lambda *args, **kwargs: {
                "valid": True,
                "errors": [],
            }
        ),
    )

    calls = []

    def fake_compile(root, *, launch_mode, **kwargs):
        calls.append((launch_mode, kwargs))
        return dict(origin)

    monkeypatch.setattr(runtime, "compile_runtime_manifest", fake_compile)
    report = runtime.validate_result_for_return(ROOT, origin, result)

    assert report["valid"] is True
    assert calls == [("PROJECT_ONBOARD", {})]
