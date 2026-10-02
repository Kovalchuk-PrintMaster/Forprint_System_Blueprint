from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.operator_console import (
    protected_terminal_proof,
)
from scripts.coordination.control_plane.operator_console.protected_terminal_proof import (
    CAPABILITIES,
    ProtectedTerminalProofError,
    run_real_protected_terminal_proof,
)


def git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    return cp.stdout


def fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "canonical"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "oc01@example.invalid")
    git(repo, "config", "user.name", "OC01 Test")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-q", "-m", "baseline")
    (repo / "tracked.txt").write_text("dirty-but-valid\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    return repo.resolve()


def snapshot(repo: Path) -> tuple[str, str, str, str]:
    return (
        git(repo, "rev-parse", "HEAD"),
        git(repo, "status", "--porcelain=v1", "--untracked-files=all"),
        git(repo, "diff", "--binary"),
        git(repo, "diff", "--cached", "--binary"),
    )


def test_real_proof_runs_three_capabilities_and_preserves_repo(
    tmp_path: Path,
) -> None:
    repo = fixture_repo(tmp_path)
    before = snapshot(repo)
    runtime = tmp_path / "runtime"

    result = run_real_protected_terminal_proof(
        canonical_repo=repo,
        runtime_root=runtime,
    )

    assert result["state"] == "PASS"
    assert result["capabilities"] == list(CAPABILITIES)
    assert {x["capability_id"] for x in result["commands"]} == set(CAPABILITIES)
    assert all(x["return_code"] == 0 for x in result["commands"])
    assert all(x["timed_out"] is False for x in result["commands"])
    assert all(x["shell"] is False for x in result["commands"])
    assert result["before"] == result["after"]
    assert snapshot(repo) == before
    assert Path(result["evidence_path"]).is_file()


def test_real_proof_flows_through_console_api_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = fixture_repo(tmp_path)
    runtime = tmp_path / "runtime"
    original = protected_terminal_proof.dispatch_action
    calls: list[str] = []

    def spy(**kwargs):
        calls.append(kwargs["action"])
        return original(**kwargs)

    monkeypatch.setattr(
        protected_terminal_proof,
        "dispatch_action",
        spy,
    )
    run_real_protected_terminal_proof(
        canonical_repo=repo,
        runtime_root=runtime,
    )
    assert calls == ["terminal_run", "terminal_run", "terminal_run"]


def test_real_proof_evidence_and_command_logs_are_outside_canonical(
    tmp_path: Path,
) -> None:
    repo = fixture_repo(tmp_path)
    runtime = tmp_path / "runtime"

    result = run_real_protected_terminal_proof(
        canonical_repo=repo,
        runtime_root=runtime,
    )

    for item in result["commands"]:
        for key in ("stdout_path", "stderr_path"):
            path = Path(item[key]).resolve()
            assert repo not in path.parents
            assert path != repo
    proof = Path(result["evidence_path"]).resolve()
    assert repo not in proof.parents
    assert proof != repo


def test_real_proof_rejects_runtime_inside_canonical(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    with pytest.raises(ProtectedTerminalProofError, match="outside canonical"):
        run_real_protected_terminal_proof(
            canonical_repo=repo,
            runtime_root=repo / "runtime",
        )


def test_real_proof_is_immutable_for_same_runtime_root(tmp_path: Path) -> None:
    repo = fixture_repo(tmp_path)
    runtime = tmp_path / "runtime"
    run_real_protected_terminal_proof(
        canonical_repo=repo,
        runtime_root=runtime,
    )
    with pytest.raises(
        ProtectedTerminalProofError,
        match="already contains immutable",
    ):
        run_real_protected_terminal_proof(
            canonical_repo=repo,
            runtime_root=runtime,
        )


def test_proof_package_records_no_write_or_git_release_authority(
    tmp_path: Path,
) -> None:
    repo = fixture_repo(tmp_path)
    result = run_real_protected_terminal_proof(
        canonical_repo=repo,
        runtime_root=tmp_path / "runtime",
    )
    assert all(value is False for value in result["authority"].values())
    assert all(value is False for value in result["actions_performed"].values())

    stored = yaml.safe_load(
        Path(result["evidence_path"]).read_text(encoding="utf-8")
    )
    assert stored["package_sha256"] == result["package_sha256"]
    assert stored["manual_ssh_command_copying_required"] is False
