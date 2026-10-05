from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

from scripts.coordination.control_plane.operator_console import (
    protected_terminal as oc01_terminal,
)
from scripts.coordination.control_plane.worker_runtime import (
    structured_command_executor as executor,
)

ROOT = Path(__file__).resolve().parents[4]


def _request(
    tmp_path: Path,
    *,
    capability_id: str = "repo_head",
    capability_version: str = "0.1.0",
    parameters: dict | None = None,
) -> dict:
    request = {
        "capability_id": capability_id,
        "capability_version": capability_version,
        "execution_scope": {
            "kind": "GIT_REPOSITORY_ROOT",
            "root": str(ROOT.resolve()),
        },
        "exact_cwd": str(ROOT.resolve()),
        "parameters": dict(parameters or {}),
        "timeout_seconds": 60,
        "evidence_destination": str((tmp_path / "evidence").resolve()),
        "execution_identity": {
            "attempt_id": "cf10-shared-executor-test-a001",
            "actor_type": "internal_worker",
        },
        "consumer_id": "CF10_TEST",
        "request_id": "cf10-shared-executor-test-request",
    }
    request["authorization_envelope"] = {
        "schema_version": "forprint_structured_execution_authorization_envelope_v0_1",
        "decision": "ALLOW_EXACT_STRUCTURED_EXECUTION",
        "consumer_id": request["consumer_id"],
        "request_id": request["request_id"],
        "capability_id": request["capability_id"],
        "capability_version": request["capability_version"],
        "execution_identity": copy.deepcopy(request["execution_identity"]),
        "execution_scope": copy.deepcopy(request["execution_scope"]),
        "exact_cwd": request["exact_cwd"],
        "parameters": dict(request["parameters"]),
        "timeout_seconds": request["timeout_seconds"],
        "evidence_destination": request["evidence_destination"],
        "authority": {
            "consumer_policy_validated": True,
            "executor_grants_authority": False,
            "canonical_write_allowed": False,
            "safe_write_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
            "arbitrary_shell_allowed": False,
        },
    }
    return request


def test_registry_is_authority_neutral_and_contains_foundation_capabilities() -> None:
    registry = executor.load_capability_registry(ROOT)
    assert registry["registry_grants_authority"] is False
    assert registry["shell"] is False
    assert registry["arbitrary_command_text_allowed"] is False
    assert set(registry["capabilities"]) == {
        "repo_status",
        "repo_head",
        "repo_diff_check",
        "validation_suite",
    }


@pytest.mark.parametrize(
    "capability_id",
    ["repo_status", "repo_head", "repo_diff_check"],
)
def test_fixed_git_recipes_remain_compatible_with_oc01(
    tmp_path: Path,
    capability_id: str,
) -> None:
    plan = executor.build_execution_plan(
        root=ROOT,
        request=_request(tmp_path, capability_id=capability_id),
    )
    argv = plan["execution"]["argv"]
    assert argv[1] == "--no-optional-locks"
    assert tuple(argv[2:]) == oc01_terminal.READ_ONLY_CAPABILITIES[capability_id]
    assert plan["execution"]["shell"] is False


@pytest.mark.parametrize(
    "forbidden_key, value",
    [
        ("argv", ["rm", "-rf", "."]),
        ("shell", True),
        ("command", "rm -rf ."),
        ("executable", "/bin/bash"),
    ],
)
def test_request_rejects_raw_execution_material(
    tmp_path: Path,
    forbidden_key: str,
    value: object,
) -> None:
    request = _request(tmp_path)
    request[forbidden_key] = value
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="unsupported keys",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_unknown_capability_fails_closed(tmp_path: Path) -> None:
    request = _request(tmp_path, capability_id="bash")
    request["authorization_envelope"]["capability_id"] = "bash"
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="unknown capability",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_validation_suite_builds_typed_registered_argv(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        capability_id="validation_suite",
        parameters={"suite_id": "cf10-worker-pipeline"},
    )
    plan = executor.build_execution_plan(root=ROOT, request=request)
    argv = plan["execution"]["argv"]

    assert argv[0] == sys.executable
    assert argv[1:] == [
        "scripts/validation/run_validation_suite_v0_1.py",
        "--suite",
        "cf10-worker-pipeline",
    ]
    assert plan["capability"]["side_effect_class"] == "READ_ONLY_VALIDATION"


def test_validation_suite_unknown_suite_fails_before_launch(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        capability_id="validation_suite",
        parameters={"suite_id": "not-registered"},
    )
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="unknown validation suite",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_validation_suite_tier_mismatch_fails_before_launch(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        capability_id="validation_suite",
        parameters={
            "suite_id": "cf10-worker-pipeline",
            "require_tier": "CORE",
        },
    )
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="does not match registered tier",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_validation_suite_rejects_unimplemented_profile_parameter(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        capability_id="validation_suite",
        parameters={
            "suite_id": "cf10-worker-pipeline",
            "profile": True,
        },
    )
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="unsupported parameters",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_exact_cwd_must_be_bound_git_root(tmp_path: Path) -> None:
    subdir = ROOT / "scripts"
    request = _request(tmp_path)
    request["exact_cwd"] = str(subdir.resolve())
    request["execution_scope"]["root"] = str(subdir.resolve())
    request["authorization_envelope"]["execution_scope"]["root"] = str(
        subdir.resolve()
    )

    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="GIT_REPOSITORY_ROOT",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_evidence_destination_inside_execution_scope_is_rejected() -> None:
    request = _request(ROOT / "tmp")
    request["evidence_destination"] = str(
        (ROOT / "tmp" / "structured-executor-evidence").resolve()
    )
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="outside exact_cwd",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_authorization_envelope_binding_drift_fails_closed(tmp_path: Path) -> None:
    request = _request(tmp_path)
    request["authorization_envelope"]["request_id"] = "other-request"
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="authorization envelope binding drift",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_authorization_envelope_cannot_widen_authority(tmp_path: Path) -> None:
    request = _request(tmp_path)
    request["authorization_envelope"]["authority"]["safe_write_allowed"] = True
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="widened authority",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_execution_reuses_shared_launcher_and_writes_bound_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = executor.build_execution_plan(
        root=ROOT,
        request=_request(tmp_path, capability_id="repo_head"),
    )
    observed: dict[str, object] = {}

    def fake_launch_process(**kwargs):
        observed.update(kwargs)
        stdout_path = Path(kwargs["stdout_path"])
        stderr_path = Path(kwargs["stderr_path"])
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text("HEAD\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        return {
            "pid": 123,
            "started_at": "2026-10-05T10:00:00Z",
            "finished_at": "2026-10-05T10:00:01Z",
            "elapsed_seconds": 1.0,
            "return_code": 0,
            "timed_out": False,
            "outcome": "completed",
            "heartbeat_observations": [],
            "stall_detected": False,
            "stall_evidence": [],
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "process_started": True,
            "cwd": kwargs["cwd"],
            "argv_sha256": plan["execution"]["argv_digest"],
            "shell": False,
        }

    monkeypatch.setattr(executor, "launch_process", fake_launch_process)

    result = executor.execute_execution_plan(root=ROOT, plan=plan)

    assert observed["argv"] == plan["execution"]["argv"]
    assert observed["cwd"] == plan["execution"]["cwd"]
    assert result["request_id"] == plan["request"]["request_id"]
    assert result["execution_id"] == plan["execution_id"]
    assert result["return_code"] == 0
    assert result["shell"] is False
    assert result["evidence_digest"]
    assert Path(result["result_evidence_path"]).is_file()
    assert all(value is False for value in result["authority"].values())


def test_execution_rejects_plan_argv_tampering(tmp_path: Path) -> None:
    plan = executor.build_execution_plan(
        root=ROOT,
        request=_request(tmp_path),
    )
    plan["execution"]["argv"].append("--tampered")
    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="execution plan drift",
    ):
        executor.execute_execution_plan(root=ROOT, plan=plan)


def test_makefile_exposes_stable_executor_surfaces() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in (
        "structured-command-executor-list",
        "structured-command-executor-check",
        "structured-command-executor-proof",
    ):
        assert f".PHONY: {target}" in text
        assert f"{target}:" in text

def test_authorization_envelope_binds_execution_parameters(
    tmp_path: Path,
) -> None:
    request = _request(
        tmp_path,
        capability_id="validation_suite",
        parameters={"suite_id": "cf10-worker-pipeline"},
    )
    request["authorization_envelope"]["parameters"] = {
        "suite_id": "cf10-worker-pipeline"
    }
    request["parameters"] = {"suite_id": "different-suite"}

    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="authorization envelope binding drift",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_authorization_envelope_binds_timeout(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request["timeout_seconds"] = 61

    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="authorization envelope binding drift",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_authorization_envelope_binds_evidence_destination(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    request["evidence_destination"] = str(
        (tmp_path / "other-evidence").resolve()
    )

    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="authorization envelope binding drift",
    ):
        executor.build_execution_plan(root=ROOT, request=request)


def test_execution_rejects_launcher_argv_binding_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = executor.build_execution_plan(
        root=ROOT,
        request=_request(tmp_path),
    )

    def fake_launch_process(**kwargs):
        stdout = Path(kwargs["stdout_path"])
        stderr = Path(kwargs["stderr_path"])
        stdout.parent.mkdir(parents=True, exist_ok=True)
        stdout.write_text("", encoding="utf-8")
        stderr.write_text("", encoding="utf-8")

        return {
            "process_started": True,
            "shell": False,
            "cwd": kwargs["cwd"],
            "argv_sha256": "wrong-digest",
            "stdout_path": str(stdout),
            "stderr_path": str(stderr),
            "return_code": 0,
            "timed_out": False,
            "outcome": "completed",
        }

    monkeypatch.setattr(
        executor,
        "launch_process",
        fake_launch_process,
    )

    with pytest.raises(
        executor.StructuredCommandExecutorError,
        match="launcher result binding drift",
    ):
        executor.execute_execution_plan(root=ROOT, plan=plan)
