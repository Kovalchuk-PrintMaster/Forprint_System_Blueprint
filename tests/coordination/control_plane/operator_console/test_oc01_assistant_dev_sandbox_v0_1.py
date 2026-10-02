from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.coordination.control_plane.operator_console.assistant_dev_sandbox import (
    AssistantDevSandboxError,
    LOCAL_COMMIT_STATE,
    create_sandbox,
    sandbox_status,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    build_session_projection,
)


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return cp.stdout.strip()


def canonical_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "canonical"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "oc01@example.invalid")
    git(repo, "config", "user.name", "OC01 Test")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-q", "-m", "baseline")
    return repo.resolve()


def session(actor_type: str = "operator_assistant") -> dict:
    return build_session_projection(
        launch_request={
            "identity": {
                "module_id": "forprint_system_blueprint",
                "prompt_id": "oc01-mini3-test",
            }
        },
        worker_invocation={
            "attempt_id": "sandbox-attempt",
            "worker_id": "operator-assistant",
            "workspace_repo": "/tmp/not-yet-bound",
        },
        actor_type=actor_type,
        actor_id="assistant-01",
    )


def create(tmp_path: Path) -> tuple[Path, dict]:
    repo = canonical_repo(tmp_path)
    result = create_sandbox(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
        module_id="forprint_system_blueprint",
        worker_id="operator-assistant",
        attempt_id="sandbox-attempt",
        expected_base_head=git(repo, "rev-parse", "HEAD"),
        session_projection=session(),
    )
    return repo, result


def test_create_reuses_isolated_workspace_and_exact_base_head(
    tmp_path: Path,
) -> None:
    repo, result = create(tmp_path)
    sandbox = result["sandbox"]
    assert result["state"] == "CREATED"
    assert sandbox["isolated"] is True
    assert sandbox["canonical_write_allowed"] is False
    assert Path(sandbox["workspace_repo"]) != repo
    assert result["base"]["base_head"] == git(repo, "rev-parse", "HEAD")
    assert result["environment_delta"]["local_commit_count_observed"] == 0


def test_human_terminal_is_not_assistant_sandbox_actor(tmp_path: Path) -> None:
    repo = canonical_repo(tmp_path)
    with pytest.raises(
        AssistantDevSandboxError,
        match="requires operator_assistant",
    ):
        create_sandbox(
            canonical_repo=repo,
            runtime_root=tmp_path / "runtime",
            module_id="forprint_system_blueprint",
            worker_id="operator-assistant",
            attempt_id="sandbox-attempt",
            expected_base_head=git(repo, "rev-parse", "HEAD"),
            session_projection=session("human_terminal"),
        )


def test_base_head_mismatch_is_rejected(tmp_path: Path) -> None:
    repo = canonical_repo(tmp_path)
    with pytest.raises(AssistantDevSandboxError, match="BASE_HEAD mismatch"):
        create_sandbox(
            canonical_repo=repo,
            runtime_root=tmp_path / "runtime",
            module_id="forprint_system_blueprint",
            worker_id="operator-assistant",
            attempt_id="sandbox-attempt",
            expected_base_head="0" * 40,
            session_projection=session(),
        )


def test_runtime_root_inside_canonical_is_rejected(tmp_path: Path) -> None:
    repo = canonical_repo(tmp_path)
    with pytest.raises(AssistantDevSandboxError):
        create_sandbox(
            canonical_repo=repo,
            runtime_root=repo / "runtime",
            module_id="forprint_system_blueprint",
            worker_id="operator-assistant",
            attempt_id="sandbox-attempt",
            expected_base_head=git(repo, "rev-parse", "HEAD"),
            session_projection=session(),
        )


def test_status_projects_workspace_environment_delta(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    workspace = Path(created["sandbox"]["workspace_repo"])
    manifest = Path(created["sandbox"]["manifest"])

    (workspace / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (workspace / "new.txt").write_text("new\n", encoding="utf-8")

    status = sandbox_status(
        manifest_path=manifest,
        session_projection=session(),
    )
    delta = status["environment_delta"]

    assert delta["projection_authority"] is False
    assert "tracked.txt" in delta["working_paths_against_current_head"]
    assert "new.txt" in delta["untracked_paths"]
    assert {"tracked.txt", "new.txt"}.issubset(set(delta["all_changed_paths"]))
    assert status["authority"]["canonical_write_authority"] is False


def test_sandbox_change_does_not_modify_canonical_repo(tmp_path: Path) -> None:
    repo, created = create(tmp_path)
    workspace = Path(created["sandbox"]["workspace_repo"])
    (workspace / "tracked.txt").write_text("sandbox-only\n", encoding="utf-8")
    assert (repo / "tracked.txt").read_text(encoding="utf-8") == "base\n"


def test_open_uses_existing_manifest_binding(tmp_path: Path) -> None:
    _, created = create(tmp_path)
    status = sandbox_status(
        manifest_path=Path(created["sandbox"]["manifest"]),
        session_projection=session(),
    )
    assert status["state"] == "OPEN"
    assert status["sandbox"]["attempt_id"] == "sandbox-attempt"


def test_tampered_manifest_canonical_write_true_is_rejected(
    tmp_path: Path,
) -> None:
    _, created = create(tmp_path)
    manifest_path = Path(created["sandbox"]["manifest"])
    import yaml

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["canonical_write_allowed"] = True
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(
        AssistantDevSandboxError,
        match="canonical_write_allowed must remain false",
    ):
        sandbox_status(
            manifest_path=manifest_path,
            session_projection=session(),
        )


def test_local_commit_is_observed_but_not_claimed_supported(
    tmp_path: Path,
) -> None:
    _, created = create(tmp_path)
    workspace = Path(created["sandbox"]["workspace_repo"])
    manifest = Path(created["sandbox"]["manifest"])

    git(workspace, "config", "user.email", "oc01@example.invalid")
    git(workspace, "config", "user.name", "OC01 Test")
    (workspace / "tracked.txt").write_text("committed sandbox change\n", encoding="utf-8")
    git(workspace, "add", "tracked.txt")
    git(workspace, "commit", "-q", "-m", "sandbox local commit")

    status = sandbox_status(
        manifest_path=manifest,
        session_projection=session(),
    )
    delta = status["environment_delta"]

    assert delta["local_commit_count_observed"] == 1
    assert delta["local_commit_support"] == LOCAL_COMMIT_STATE
    assert "tracked.txt" in delta["committed_paths_since_base"]


def test_canonical_head_drift_is_visible_not_silently_rebased(
    tmp_path: Path,
) -> None:
    repo, created = create(tmp_path)
    manifest = Path(created["sandbox"]["manifest"])

    (repo / "after.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "after.txt")
    git(repo, "commit", "-q", "-m", "canonical moved")

    status = sandbox_status(
        manifest_path=manifest,
        session_projection=session(),
    )
    assert status["base"]["canonical_head_drifted_since_base"] is True
    assert status["base"]["current_canonical_head"] != status["base"]["base_head"]
