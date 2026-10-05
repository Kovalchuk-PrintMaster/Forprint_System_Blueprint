from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.coordination.control_plane.operator_console.protected_terminal import (
    CANCEL_STATE,
    COMMAND_REPRESENTATION,
    ProtectedTerminalError,
    build_terminal_plan,
    execute_terminal_plan,
    list_capabilities,
    load_terminal_history,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    build_session_projection,
)


def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo.resolve()


def session(actor_type: str = "human_terminal") -> dict:
    return build_session_projection(
        launch_request={
            "identity": {
                "module_id": "forprint_system_blueprint",
                "prompt_id": "oc01-mini2-test",
            }
        },
        worker_invocation={
            "attempt_id": "oc01-mini2-attempt",
            "worker_id": "worker-01",
            "workspace_repo": "/tmp/unused-workspace",
        },
        actor_type=actor_type,
        actor_id="actor-01",
    )


def test_capability_catalog_is_default_off_and_bounded() -> None:
    data = list_capabilities()
    assert data["default_enabled"] is False
    assert data["command_representation"] == "ARGV_NO_SHELL"
    assert data["arbitrary_command_text_allowed"] is False
    assert data["shell"] is False
    assert {row["capability_id"] for row in data["capabilities"]} == {
        "repo_status",
        "repo_head",
        "repo_diff_check",
    }
    assert data["safe_write"]["execution_state"] == "BLOCKED"
    assert data["cancel"]["state"] == CANCEL_STATE


def test_default_off_requires_explicit_enable(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    with pytest.raises(ProtectedTerminalError, match="default-off"):
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=session(),
        )


def test_unknown_capability_rejected(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    with pytest.raises(
        ProtectedTerminalError,
        match="unknown Protected Terminal capability",
    ):
        build_terminal_plan(
            capability_id="bash",
            cwd=repo,
            session_projection=session(),
            enabled=True,
        )


def test_internal_worker_cannot_be_terminal_actor(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    with pytest.raises(
        ProtectedTerminalError,
        match="operator_assistant or human_terminal",
    ):
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=session("internal_worker"),
            enabled=True,
        )


def test_safe_write_is_blocked_until_lease_proven(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    with pytest.raises(
        ProtectedTerminalError,
        match="EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
    ):
        build_terminal_plan(
            capability_id="future-safe-write",
            cwd=repo,
            session_projection=session(),
            enabled=True,
            capability_class="SAFE_WRITE",
        )


def test_plan_uses_fixed_argv_and_exact_repo_scope(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        timeout_seconds=12,
        evidence_dir=tmp_path / "evidence",
    )
    execution = plan["execution"]
    assert execution["command_representation"] == COMMAND_REPRESENTATION
    assert execution["shell"] is False
    assert execution["argv"][1:] == [
        "--no-optional-locks",
        "status",
        "--short",
        "--untracked-files=all",
    ]
    assert execution["cwd"] == str(repo)
    assert execution["timeout_seconds"] == 12
    assert plan["capability"]["exact_scope"] == str(repo)
    assert all(value is False for value in plan["authority"].values())
    assert plan["cancel"]["state"] == CANCEL_STATE


def test_subdirectory_scope_is_rejected(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    subdir = repo / "sub"
    subdir.mkdir()
    with pytest.raises(
        ProtectedTerminalError,
        match="exact Git repository root scope",
    ):
        build_terminal_plan(
            capability_id="repo_status",
            cwd=subdir,
            session_projection=session(),
            enabled=True,
        )


def test_execute_rejects_argv_tampering(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    plan["execution"]["argv"].append("--ignored")
    with pytest.raises(
        ProtectedTerminalError,
        match="does not match registered capability",
    ):
        execute_terminal_plan(plan)


def test_read_only_capability_executes_through_shared_launcher(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session("operator_assistant"),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    result = execute_terminal_plan(plan)
    assert result["return_code"] == 0
    assert result["timed_out"] is False
    assert result["shell"] is False
    assert Path(result["stdout_path"]).is_file()
    assert Path(result["stderr_path"]).is_file()
    assert result["started_at"]
    assert result["finished_at"]
    assert result["cancel"] == {
        "state": CANCEL_STATE,
        "available": False,
        "cancelled": False,
    }
    assert all(value is False for value in result["authority"].values())


def test_session_projection_authority_widening_is_rejected(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    projection = session()
    projection["authority"]["execution_authority"] = True
    with pytest.raises(
        ProtectedTerminalError,
        match="unexpectedly grants authority",
    ):
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=projection,
            enabled=True,
        )

def test_evidence_dir_inside_repo_is_rejected(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    with pytest.raises(
        ProtectedTerminalError,
        match="evidence_dir must remain outside protected repository scope",
    ):
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=session(),
            enabled=True,
            evidence_dir=repo / "tmp" / "terminal-evidence",
        )


def test_execution_scope_tampering_is_rejected(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q", str(other)], check=True)

    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    plan["execution"]["cwd"] = str(other.resolve())

    with pytest.raises(
        ProtectedTerminalError,
        match="cwd / exact scope drift",
    ):
        execute_terminal_plan(plan)


def test_execution_actor_source_tampering_is_rejected(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    plan["actor"]["source"] = "UNTRUSTED_SOURCE"

    with pytest.raises(
        ProtectedTerminalError,
        match="actor source drift",
    ):
        execute_terminal_plan(plan)


def test_execution_evidence_path_inside_repo_is_rejected(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    plan["execution"]["stdout_path"] = str(repo / "stdout.log")

    with pytest.raises(
        ProtectedTerminalError,
        match="stdout_path must remain outside protected repository scope",
    ):
        execute_terminal_plan(plan)

# OC01-FULL-1 / Protected Terminal policy + audit hardening

def test_full1_capability_catalog_exposes_policy_profiles() -> None:
    data = list_capabilities()
    rows = {row["capability_id"]: row for row in data["capabilities"]}

    assert data["policy"] == {
        "mode": "REGISTERED_CAPABILITY_ONLY",
        "default_decision": "DENY",
        "explicit_enable_required": True,
        "authority_widening_allowed": False,
    }
    assert rows["repo_status"]["profile"]["profile_id"] == "repository_observation"
    assert rows["repo_status"]["profile"]["repository_mutation_allowed"] is False
    assert rows["repo_diff_check"]["profile"]["profile_id"] == "repository_validation"
    assert data["safe_write"]["policy"] == {
        "decision": "DENY",
        "code": "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
    }
    assert data["audit"]["mode"] == "APPEND_ONLY"


def test_full1_safe_write_denial_is_structured_and_retained(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    evidence = tmp_path / "evidence"

    with pytest.raises(ProtectedTerminalError) as caught:
        build_terminal_plan(
            capability_id="future-safe-write",
            cwd=repo,
            session_projection=session(),
            enabled=True,
            capability_class="SAFE_WRITE",
            evidence_dir=evidence,
        )

    assert caught.value.code == "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN"
    assert caught.value.receipt_path == str(
        evidence.resolve() / "denial_receipts_v0_1.jsonl"
    )
    denial_lines = (
        evidence / "denial_receipts_v0_1.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    assert len(denial_lines) == 1

    history = load_terminal_history(evidence)
    assert history["event_count"] == 1
    event = history["events"][0]
    assert event["event_type"] == "POLICY_DENIED"
    assert event["decision"] == "DENY"
    assert event["code"] == "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN"
    assert event["actor"]["actor_type"] == "human_terminal"
    assert event["authority_conferred"] is False
    assert not list(evidence.rglob("stdout.log"))
    assert not list(evidence.rglob("stderr.log"))


def test_full1_unknown_capability_denial_has_stable_code(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    evidence = tmp_path / "evidence"

    with pytest.raises(ProtectedTerminalError) as caught:
        build_terminal_plan(
            capability_id="bash",
            cwd=repo,
            session_projection=session("operator_assistant"),
            enabled=True,
            evidence_dir=evidence,
        )

    assert caught.value.code == "UNKNOWN_CAPABILITY"
    history = load_terminal_history(evidence)
    assert history["events"][-1]["code"] == "UNKNOWN_CAPABILITY"
    assert history["events"][-1]["capability_id"] == "bash"


def test_full1_plan_and_run_append_durable_history(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    evidence = tmp_path / "evidence"
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session("operator_assistant"),
        enabled=True,
        evidence_dir=evidence,
    )

    first = load_terminal_history(evidence)
    assert [row["event_type"] for row in first["events"]] == ["PLAN_ALLOWED"]

    result = execute_terminal_plan(plan)
    history = load_terminal_history(evidence)
    assert [row["event_type"] for row in history["events"]] == [
        "PLAN_ALLOWED",
        "EXECUTION_STARTED",
        "EXECUTION_FINISHED",
    ]
    assert history["events"][-1]["actor"]["actor_type"] == "operator_assistant"
    assert history["events"][-1]["capability_id"] == "repo_status"
    assert history["events"][-1]["cwd"] == str(repo)
    assert result["audit"]["history_path"] == history["history_path"]
    assert result["authority"]["canonical_write_performed"] is False

    tail = load_terminal_history(evidence, limit=1)
    assert tail["event_count"] == 3
    assert tail["returned_count"] == 1
    assert tail["events"][0]["event_type"] == "EXECUTION_FINISHED"


def test_full1_audit_paths_inside_repo_are_rejected(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    plan["audit"]["history_path"] = str(repo / "history.jsonl")

    with pytest.raises(
        ProtectedTerminalError,
        match="history_path must remain outside protected repository scope",
    ):
        execute_terminal_plan(plan)

# OC01-FULL-1 Slice B / bounded runtime observation bridge

import scripts.coordination.control_plane.operator_console.protected_terminal as protected_terminal_module


def test_full1_slice_b_runtime_observation_configuration_is_explicit(
    tmp_path: Path,
) -> None:
    repo = git_repo(tmp_path)
    evidence = tmp_path / "evidence"

    default_plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=evidence,
    )
    assert default_plan["runtime_observation"] == {
        "enabled": False,
        "mode": "BOUNDED_RUNTIME_PROGRESS_EVIDENCE",
        "source": "SHARED_LAUNCHER_HEARTBEAT",
        "heartbeat_seconds": None,
        "stall_threshold_seconds": None,
        "byte_streaming": False,
        "stdout_content_retained_in_history": False,
        "stderr_content_retained_in_history": False,
        "authority_conferred": False,
    }

    with pytest.raises(ProtectedTerminalError) as caught:
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=session(),
            enabled=True,
            evidence_dir=evidence,
            stall_threshold_seconds=2.0,
        )
    assert caught.value.code == "RUNTIME_OBSERVATION_NOT_ENABLED"

    with pytest.raises(ProtectedTerminalError) as caught:
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=session(),
            enabled=True,
            evidence_dir=evidence,
            observe_runtime=True,
            heartbeat_seconds=0,
        )
    assert caught.value.code == "INVALID_HEARTBEAT_SECONDS"

    with pytest.raises(ProtectedTerminalError) as caught:
        build_terminal_plan(
            capability_id="repo_status",
            cwd=repo,
            session_projection=session(),
            enabled=True,
            evidence_dir=evidence,
            observe_runtime=True,
            stall_threshold_seconds=0,
        )
    assert caught.value.code == "INVALID_STALL_THRESHOLD"


def test_full1_slice_b_observation_uses_shared_callback_and_sanitizes_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = git_repo(tmp_path)
    evidence = tmp_path / "evidence"

    def fake_launch_process(**kwargs):
        assert kwargs["heartbeat_seconds"] == 1
        assert kwargs["stall_threshold_seconds"] == 2.0
        callback = kwargs["on_heartbeat"]
        assert callback is not None
        callback(
            {
                "pid": 101,
                "runtime_seconds": 1.0,
                "stdout_bytes": 12,
                "stderr_bytes": 0,
                "stdout_growth_bytes": 12,
                "stderr_growth_bytes": 0,
                "progress_observed": True,
                "stall_detected": False,
                "stdout_chunk": "SECRET_STDOUT_CONTENT",
                "model_thinking": True,
            }
        )
        callback(
            {
                "pid": 101,
                "runtime_seconds": 3.2,
                "stdout_bytes": 12,
                "stderr_bytes": 0,
                "stdout_growth_bytes": 0,
                "stderr_growth_bytes": 0,
                "progress_observed": False,
                "stall_detected": True,
                "no_progress_seconds": 2.2,
                "stall_threshold_seconds": 2.0,
                "stderr_chunk": "SECRET_STDERR_CONTENT",
            }
        )
        return {
            "pid": 101,
            "started_at": "2026-10-04T20:00:00+00:00",
            "finished_at": "2026-10-04T20:00:04+00:00",
            "return_code": 0,
            "timed_out": False,
            "outcome": "completed_with_stall_evidence",
            "shell": False,
            "stdout_path": str(kwargs["stdout_path"]),
            "stderr_path": str(kwargs["stderr_path"]),
            "heartbeat_observations": [],
            "stall_detected": True,
            "stall_evidence": [],
        }

    monkeypatch.setattr(
        protected_terminal_module,
        "launch_process",
        fake_launch_process,
    )

    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session("operator_assistant"),
        enabled=True,
        evidence_dir=evidence,
        observe_runtime=True,
        heartbeat_seconds=1,
        stall_threshold_seconds=2.0,
    )
    result = execute_terminal_plan(plan)
    history = load_terminal_history(evidence)

    assert [row["event_type"] for row in history["events"]] == [
        "PLAN_ALLOWED",
        "EXECUTION_STARTED",
        "RUNTIME_OBSERVATION",
        "RUNTIME_OBSERVATION",
        "EXECUTION_FINISHED",
    ]

    observations = [
        row for row in history["events"]
        if row["event_type"] == "RUNTIME_OBSERVATION"
    ]
    assert len(observations) == 2
    allowed = {
        "pid",
        "runtime_seconds",
        "stdout_bytes",
        "stderr_bytes",
        "stdout_growth_bytes",
        "stderr_growth_bytes",
        "progress_observed",
        "stall_detected",
        "no_progress_seconds",
        "stall_threshold_seconds",
    }
    for row in observations:
        assert set(row["details"]) <= allowed
        assert "stdout_chunk" not in row["details"]
        assert "stderr_chunk" not in row["details"]
        assert "model_thinking" not in row["details"]
        assert row["authority_conferred"] is False

    assert observations[0]["details"]["progress_observed"] is True
    assert observations[1]["details"]["stall_detected"] is True

    assert result["runtime_observation"]["enabled"] is True
    assert result["runtime_observation"]["history_event_count"] == 2
    assert result["runtime_observation"]["stall_detected"] is True
    assert result["runtime_observation"]["byte_streaming"] is False
    assert result["authority"]["canonical_write_performed"] is False
    assert result["cancel"]["available"] is False


def test_full1_slice_b_default_execution_does_not_enable_observation_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = git_repo(tmp_path)
    captured = {}

    def fake_launch_process(**kwargs):
        captured.update(kwargs)
        return {
            "pid": 202,
            "started_at": "2026-10-04T20:00:00+00:00",
            "finished_at": "2026-10-04T20:00:01+00:00",
            "return_code": 0,
            "timed_out": False,
            "outcome": "completed",
            "shell": False,
            "stdout_path": str(kwargs["stdout_path"]),
            "stderr_path": str(kwargs["stderr_path"]),
            "heartbeat_observations": [],
            "stall_detected": False,
            "stall_evidence": [],
        }

    monkeypatch.setattr(
        protected_terminal_module,
        "launch_process",
        fake_launch_process,
    )

    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=tmp_path / "evidence",
    )
    result = execute_terminal_plan(plan)

    assert "on_heartbeat" not in captured
    assert "heartbeat_seconds" not in captured
    assert "stall_threshold_seconds" not in captured
    assert result["runtime_observation"]["enabled"] is False
    assert result["runtime_observation"]["history_event_count"] == 0


def test_full1_slice_b_timeout_remains_distinct_from_stall_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = git_repo(tmp_path)
    evidence = tmp_path / "evidence"

    def fake_launch_process(**kwargs):
        callback = kwargs["on_heartbeat"]
        callback(
            {
                "pid": 303,
                "runtime_seconds": 2.5,
                "stdout_bytes": 0,
                "stderr_bytes": 0,
                "stdout_growth_bytes": 0,
                "stderr_growth_bytes": 0,
                "progress_observed": False,
                "stall_detected": True,
                "no_progress_seconds": 2.5,
                "stall_threshold_seconds": 2.0,
            }
        )
        return {
            "pid": 303,
            "started_at": "2026-10-04T20:00:00+00:00",
            "finished_at": "2026-10-04T20:00:03+00:00",
            "return_code": -15,
            "timed_out": True,
            "outcome": "timeout",
            "shell": False,
            "stdout_path": str(kwargs["stdout_path"]),
            "stderr_path": str(kwargs["stderr_path"]),
            "heartbeat_observations": [],
            "stall_detected": True,
            "stall_evidence": [],
        }

    monkeypatch.setattr(
        protected_terminal_module,
        "launch_process",
        fake_launch_process,
    )

    plan = build_terminal_plan(
        capability_id="repo_status",
        cwd=repo,
        session_projection=session(),
        enabled=True,
        evidence_dir=evidence,
        observe_runtime=True,
        heartbeat_seconds=1,
        stall_threshold_seconds=2.0,
    )
    result = execute_terminal_plan(plan)
    history = load_terminal_history(evidence)

    assert result["timed_out"] is True
    assert result["outcome"] == "timeout"
    assert result["runtime_observation"]["stall_detected"] is True

    finished = history["events"][-1]
    assert finished["event_type"] == "EXECUTION_FINISHED"
    assert finished["details"]["timed_out"] is True
    assert finished["details"]["outcome"] == "timeout"
    assert finished["details"]["stall_detected"] is True
# OC01 FULL-1 Slice C RED v0.3: Protected Terminal approval evidence input
def test_full1_slice_c_plan_exposes_approval_artifact_input() -> None:
    import inspect

    parameters = inspect.signature(build_terminal_plan).parameters
    assert "approval_decision_path" in parameters, (
        "Slice C Protected Terminal plan must accept bounded "
        "approval_decision_path"
    )
