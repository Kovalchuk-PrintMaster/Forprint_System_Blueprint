from __future__ import annotations

import hashlib
import importlib
import subprocess
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[4]
MODULE_NAME = (
    "scripts.coordination.control_plane.worker_runtime.repository_seal"
)
MAKEFILE = ROOT / "Makefile"


def _module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def _git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert cp.returncode == 0, cp.stdout
    return cp.stdout


def _init_repo(tmp_path: Path, *, with_remote: bool = False) -> tuple[Path, Path | None]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "cf10@example.invalid")
    _git(repo, "config", "user.name", "CF10 Test")
    _git(repo, "checkout", "-q", "-b", "main")

    (repo / "candidate.txt").write_text("candidate-base\n", encoding="utf-8")
    (repo / "protected.txt").write_text("protected-base\n", encoding="utf-8")
    (repo / "stable.txt").write_text("stable\n", encoding="utf-8")
    _git(repo, "add", "candidate.txt", "protected.txt", "stable.txt")
    _git(repo, "commit", "-q", "-m", "baseline")

    remote: Path | None = None
    if with_remote:
        remote = tmp_path / "origin.git"
        subprocess.run(
            ["git", "init", "--bare", "-q", str(remote)],
            check=True,
            text=True,
            capture_output=True,
        )
        _git(repo, "remote", "add", "origin", str(remote))
        _git(repo, "push", "-q", "-u", "origin", "main")

    return repo.resolve(), remote


def _status_paths(repo: Path) -> list[str]:
    lines = _git(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).splitlines()
    return sorted(line[3:] for line in lines if len(line) >= 4)


def _staged_paths(repo: Path) -> list[str]:
    return sorted(
        x
        for x in _git(
            repo,
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
        ).splitlines()
        if x
    )


def _unstaged_sha(repo: Path, path: str) -> str:
    raw = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", "--", path],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    return hashlib.sha256(raw).hexdigest()


def test_makefile_delegates_seal_mechanics_to_project_native_module() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")

    assert "SEAL_PRESERVE_PATHS ?=" in text
    assert (
        "scripts/coordination/control_plane/worker_runtime/"
        "repository_seal.py"
    ) in text

    stage_start = text.index("seal-stage-exact:")
    review_start = text.index("# Target: seal-staged-review")
    stage_body = text[stage_start:review_start]
    assert "repository_seal.py stage-exact" in stage_body
    assert '--candidate-paths "$(SEAL_PATHS)"' in stage_body
    assert '--preserve-paths "$(SEAL_PRESERVE_PATHS)"' in stage_body
    assert "git add" not in stage_body

    push_start = text.index("seal-push:")
    cleanup_start = text.index("# 05 Cleanup / generated documentation artifacts")
    push_body = text[push_start:cleanup_start]
    assert "repository_seal.py push" in push_body
    assert '--branch "$(SEAL_BRANCH)"' in push_body
    assert '--preserve-paths "$(SEAL_PRESERVE_PATHS)"' in push_body
    assert "git push" not in push_body


def test_normalize_path_sets_reject_overlap_and_unsafe_paths() -> None:
    seal = _module()

    with pytest.raises(seal.RepositorySealError, match="overlap|disjoint"):
        seal.normalize_path_sets(
            candidate_paths=["candidate.txt"],
            preserve_paths=["candidate.txt"],
        )

    for unsafe in ("/absolute.txt", "../escape.txt", ".git/index"):
        with pytest.raises(seal.RepositorySealError):
            seal.normalize_path_sets(
                candidate_paths=[unsafe],
                preserve_paths=[],
            )


def test_stage_exact_backward_compatible_clean_worktree_candidate(
    tmp_path: Path,
) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path)

    (repo / "candidate.txt").write_text("candidate-change\n", encoding="utf-8")

    result = seal.stage_exact(
        repo=repo,
        candidate_paths=["candidate.txt"],
        preserve_paths=[],
    )

    assert result["state"] == "PASS"
    assert result["candidate_paths"] == ["candidate.txt"]
    assert result["preserve_paths"] == []
    assert result["staged_paths"] == ["candidate.txt"]
    assert result["preserved_paths_unchanged"] is True
    assert _staged_paths(repo) == ["candidate.txt"]
    assert _status_paths(repo) == ["candidate.txt"]


def test_stage_exact_preserves_declared_dirty_path_and_stages_only_candidate(
    tmp_path: Path,
) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path)

    (repo / "candidate.txt").write_text("candidate-change\n", encoding="utf-8")
    (repo / "protected.txt").write_text("protected-change\n", encoding="utf-8")
    before_protected_sha = _unstaged_sha(repo, "protected.txt")

    result = seal.stage_exact(
        repo=repo,
        candidate_paths=["candidate.txt"],
        preserve_paths=["protected.txt"],
    )

    assert result["state"] == "PASS"
    assert result["dirty_union_verified"] is True
    assert result["candidate_paths"] == ["candidate.txt"]
    assert result["preserve_paths"] == ["protected.txt"]
    assert result["staged_paths"] == ["candidate.txt"]
    assert result["preserved_dirty_paths"] == ["protected.txt"]
    assert result["preserved_paths_unchanged"] is True
    assert _staged_paths(repo) == ["candidate.txt"]
    assert _status_paths(repo) == ["candidate.txt", "protected.txt"]
    assert _unstaged_sha(repo, "protected.txt") == before_protected_sha


def test_stage_exact_rejects_unexpected_extra_dirty_path(tmp_path: Path) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path)

    (repo / "candidate.txt").write_text("candidate-change\n", encoding="utf-8")
    (repo / "protected.txt").write_text("protected-change\n", encoding="utf-8")
    (repo / "unexpected.txt").write_text("unexpected\n", encoding="utf-8")

    with pytest.raises(
        seal.RepositorySealError,
        match="dirty surface|unexpected",
    ):
        seal.stage_exact(
            repo=repo,
            candidate_paths=["candidate.txt"],
            preserve_paths=["protected.txt"],
        )

    assert _staged_paths(repo) == []


def test_stage_exact_rejects_pre_staged_protected_path(tmp_path: Path) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path)

    (repo / "candidate.txt").write_text("candidate-change\n", encoding="utf-8")
    (repo / "protected.txt").write_text("protected-change\n", encoding="utf-8")
    _git(repo, "add", "protected.txt")

    with pytest.raises(
        seal.RepositorySealError,
        match="protected|preserve|staged",
    ):
        seal.stage_exact(
            repo=repo,
            candidate_paths=["candidate.txt"],
            preserve_paths=["protected.txt"],
        )

    assert _staged_paths(repo) == ["protected.txt"]


def test_stage_exact_supports_untracked_candidate_with_tracked_preserve(
    tmp_path: Path,
) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path)

    (repo / "new-candidate.txt").write_text("new\n", encoding="utf-8")
    (repo / "protected.txt").write_text("protected-change\n", encoding="utf-8")
    before_protected_sha = _unstaged_sha(repo, "protected.txt")

    result = seal.stage_exact(
        repo=repo,
        candidate_paths=["new-candidate.txt"],
        preserve_paths=["protected.txt"],
    )

    assert result["staged_paths"] == ["new-candidate.txt"]
    assert result["preserved_dirty_paths"] == ["protected.txt"]
    assert _unstaged_sha(repo, "protected.txt") == before_protected_sha


def test_push_exact_backward_compatible_clean_worktree(tmp_path: Path) -> None:
    seal = _module()
    repo, remote = _init_repo(tmp_path, with_remote=True)
    assert remote is not None

    (repo / "candidate.txt").write_text("published\n", encoding="utf-8")
    _git(repo, "add", "candidate.txt")
    _git(repo, "commit", "-q", "-m", "publish candidate")

    result = seal.push_exact(
        repo=repo,
        branch="main",
        preserve_paths=[],
        remote="origin",
    )

    assert result["state"] == "PASS"
    assert result["branch"] == "main"
    assert result["preserve_paths"] == []
    assert result["local_head"] == result["remote_head"]
    assert result["preserved_paths_unchanged"] is True
    assert _status_paths(repo) == []


def test_push_exact_preserves_declared_dirty_path_and_matches_remote_head(
    tmp_path: Path,
) -> None:
    seal = _module()
    repo, remote = _init_repo(tmp_path, with_remote=True)
    assert remote is not None

    (repo / "candidate.txt").write_text("published\n", encoding="utf-8")
    _git(repo, "add", "candidate.txt")
    _git(repo, "commit", "-q", "-m", "publish candidate")

    (repo / "protected.txt").write_text("still-local\n", encoding="utf-8")
    before_sha = _unstaged_sha(repo, "protected.txt")

    result = seal.push_exact(
        repo=repo,
        branch="main",
        preserve_paths=["protected.txt"],
        remote="origin",
    )

    assert result["state"] == "PASS"
    assert result["local_head"] == result["remote_head"]
    assert result["pre_push_dirty_paths"] == ["protected.txt"]
    assert result["post_push_dirty_paths"] == ["protected.txt"]
    assert result["preserved_paths_unchanged"] is True
    assert _unstaged_sha(repo, "protected.txt") == before_sha
    assert _staged_paths(repo) == []


def test_push_exact_rejects_branch_drift(tmp_path: Path) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path, with_remote=True)

    with pytest.raises(seal.RepositorySealError, match="branch"):
        seal.push_exact(
            repo=repo,
            branch="not-main",
            preserve_paths=[],
            remote="origin",
        )


def test_push_exact_rejects_staged_changes_before_push(tmp_path: Path) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path, with_remote=True)

    (repo / "candidate.txt").write_text("staged\n", encoding="utf-8")
    _git(repo, "add", "candidate.txt")

    with pytest.raises(
        seal.RepositorySealError,
        match="staged",
    ):
        seal.push_exact(
            repo=repo,
            branch="main",
            preserve_paths=[],
            remote="origin",
        )


def test_push_exact_rejects_undeclared_dirty_path(tmp_path: Path) -> None:
    seal = _module()
    repo, _remote = _init_repo(tmp_path, with_remote=True)

    (repo / "protected.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(
        seal.RepositorySealError,
        match="dirty surface|preserve",
    ):
        seal.push_exact(
            repo=repo,
            branch="main",
            preserve_paths=[],
            remote="origin",
        )


def test_repository_seal_module_does_not_define_commit_or_reset_authority() -> None:
    seal = _module()

    forbidden = {
        "commit",
        "reset",
        "restore",
        "checkout",
        "stash",
        "clean",
        "merge",
        "rebase",
    }
    assert not forbidden.intersection(set(dir(seal)))
