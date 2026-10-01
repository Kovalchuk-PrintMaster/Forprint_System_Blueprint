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

