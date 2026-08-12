from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ("scripts/validation/validate_mutation_precommit_surface.py")


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "mutation_precommit_surface_validator",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
    )
    return result.stdout


def init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    run_git(root, "init", "-q")
    run_git(root, "config", "user.email", "tests@example.invalid")
    run_git(root, "config", "user.name", "ForPrint Tests")
    (root / "tracked.txt").write_text("base\n", encoding="utf-8")
    run_git(root, "add", "tracked.txt")
    run_git(root, "commit", "-q", "-m", "base")
    return root


def index_hash(root: Path) -> str:
    raw = run_git(root, "rev-parse", "--git-path", "index").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_clean_modified_path_passes_without_real_staging(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)
    before = index_hash(root)
    (root / "tracked.txt").write_text("changed\n", encoding="utf-8")

    result = validator.validate(root, ["tracked.txt"])

    assert result["result"] == "MUTATION_PRECOMMIT_SURFACE_VALID"
    assert index_hash(root) == before
    assert run_git(root, "diff", "--cached", "--name-status") == ""


def test_new_untracked_file_is_covered_and_passes(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)
    before = index_hash(root)
    (root / "new.txt").write_text("clean\n", encoding="utf-8")

    result = validator.validate(root, ["new.txt"])

    assert result["expected_paths"] == ["new.txt"]
    assert index_hash(root) == before
    assert run_git(root, "diff", "--cached", "--name-status") == ""


def test_new_untracked_file_with_trailing_whitespace_fails(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)
    (root / "new.txt").write_text("bad  \n", encoding="utf-8")

    try:
        validator.validate(root, ["new.txt"])
    except validator.ValidationFailure as error:
        message = str(error)
    else:
        raise AssertionError("expected trailing-whitespace validation failure")

    assert "git diff --cached --check failed" in message
    assert "trailing whitespace" in message


def test_modified_tracked_file_with_trailing_whitespace_fails(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)
    (root / "tracked.txt").write_text("bad \n", encoding="utf-8")

    try:
        validator.validate(root, ["tracked.txt"])
    except validator.ValidationFailure as error:
        message = str(error)
    else:
        raise AssertionError("expected trailing-whitespace validation failure")

    assert "git diff --cached --check failed" in message
    assert "trailing whitespace" in message


def test_unexpected_dirty_path_fails(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)
    (root / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (root / "unexpected.txt").write_text("extra\n", encoding="utf-8")

    try:
        validator.validate(root, ["tracked.txt"])
    except validator.ValidationFailure as error:
        message = str(error)
    else:
        raise AssertionError("expected dirty-path mismatch")

    assert "working-tree mutation path set mismatch" in message
    assert "unexpected.txt" in message


def test_preexisting_real_index_change_fails_without_mutating_index(
    tmp_path: Path,
) -> None:
    root = init_repo(tmp_path)
    (root / "tracked.txt").write_text("staged\n", encoding="utf-8")
    run_git(root, "add", "tracked.txt")
    before = index_hash(root)

    try:
        validator.validate(root, ["tracked.txt"])
    except validator.ValidationFailure as error:
        message = str(error)
    else:
        raise AssertionError("expected real-index precondition failure")

    assert "real Git index must be clean" in message
    assert index_hash(root) == before
    assert "tracked.txt" in run_git(
        root,
        "diff",
        "--cached",
        "--name-status",
    )
