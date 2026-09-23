from __future__ import annotations

import importlib.util
from pathlib import Path

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
