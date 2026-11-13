#!/usr/bin/env python3
"""Bounded repository seal mechanics with explicit preserved dirty paths.

The module owns only two operator-invoked mechanics:

* ``stage-exact`` stages exactly an explicitly declared candidate path set while
  preserving an explicitly declared inherited dirty path set.
* ``push`` pushes one explicitly named current branch and verifies local/remote
  HEAD agreement while preserving the declared inherited dirty path set.

It does not commit, reset, restore, checkout, stash, clean, merge, rebase, or
otherwise mutate preserved worktree content.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import posixpath
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class RepositorySealError(RuntimeError):
    """Raised when a repository seal contract cannot be proven safely."""


def _run_git(
    repo: Path,
    *args: str,
    text: bool = True,
) -> str | bytes:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        check=False,
        shell=False,
    )
    if cp.returncode != 0:
        stdout = cp.stdout if isinstance(cp.stdout, str) else cp.stdout.decode(
            "utf-8", errors="replace"
        )
        stderr = cp.stderr if isinstance(cp.stderr, str) else cp.stderr.decode(
            "utf-8", errors="replace"
        )
        raise RepositorySealError(
            "git command failed rc="
            + str(cp.returncode)
            + ": git "
            + " ".join(args)
            + "\n"
            + stdout
            + stderr
        )
    return cp.stdout


def _exact_repo_root(repo: Path | str) -> Path:
    candidate = Path(repo).expanduser().resolve()
    if not candidate.is_dir():
        raise RepositorySealError(
            "repository root must be an existing directory"
        )
    observed = str(
        _run_git(candidate, "rev-parse", "--show-toplevel")
    ).strip()
    observed_path = Path(observed).resolve()
    if observed_path != candidate:
        raise RepositorySealError(
            "repository path must be the exact Git repository root"
        )
    return candidate


def _normalize_paths(
    values: Iterable[str],
    *,
    label: str,
) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise RepositorySealError(
                f"{label} paths must be non-empty strings"
            )
        raw = value.strip()
        if "\x00" in raw or "\n" in raw or "\r" in raw:
            raise RepositorySealError(
                f"{label} path contains forbidden control characters"
            )
        if "\\" in raw:
            raise RepositorySealError(
                f"{label} path must use repository POSIX separators: {raw}"
            )
        if raw.startswith("/"):
            raise RepositorySealError(
                f"{label} path must be repository-relative: {raw}"
            )

        clean = posixpath.normpath(raw)
        if clean in {"", ".", ".."} or clean.startswith("../"):
            raise RepositorySealError(
                f"{label} path escapes repository root: {raw}"
            )
        first = clean.split("/", 1)[0]
        if first == ".git":
            raise RepositorySealError(
                f"{label} path cannot address Git internals: {raw}"
            )
        normalized.append(clean)

    return sorted(set(normalized))


def normalize_path_sets(
    *,
    candidate_paths: Iterable[str],
    preserve_paths: Iterable[str],
) -> dict[str, list[str]]:
    """Normalize and prove disjoint candidate/preserved path sets."""

    candidate = _normalize_paths(
        candidate_paths,
        label="candidate",
    )
    preserve = _normalize_paths(
        preserve_paths,
        label="preserve",
    )
    overlap = sorted(set(candidate).intersection(preserve))
    if overlap:
        raise RepositorySealError(
            "candidate and preserve path sets must be disjoint; overlap="
            + ",".join(overlap)
        )
    return {
        "candidate_paths": candidate,
        "preserve_paths": preserve,
    }


def _split_path_argument(value: str) -> list[str]:
    if not isinstance(value, str):
        raise RepositorySealError("path argument must be a string")
    if not value.strip():
        return []
    try:
        return shlex.split(value)
    except ValueError as exc:
        raise RepositorySealError(
            f"invalid quoted path list: {exc}"
        ) from exc


def _name_list(repo: Path, *args: str) -> list[str]:
    raw = str(_run_git(repo, *args))
    return sorted({line for line in raw.splitlines() if line})


def _dirty_paths(repo: Path) -> list[str]:
    values = set(
        _name_list(
            repo,
            "diff",
            "--name-only",
            "--no-renames",
        )
    )
    values.update(
        _name_list(
            repo,
            "diff",
            "--cached",
            "--name-only",
            "--no-renames",
        )
    )
    values.update(
        _name_list(
            repo,
            "ls-files",
            "--others",
            "--exclude-standard",
        )
    )
    return sorted(values)


def _staged_paths(repo: Path) -> list[str]:
    return _name_list(
        repo,
        "diff",
        "--cached",
        "--name-only",
        "--no-renames",
    )


def _tracked_unstaged_paths(repo: Path) -> list[str]:
    return _name_list(
        repo,
        "diff",
        "--name-only",
        "--no-renames",
    )


def _untracked_paths(repo: Path) -> list[str]:
    return _name_list(
        repo,
        "ls-files",
        "--others",
        "--exclude-standard",
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _path_state_digest(repo: Path, path: str) -> str:
    """Hash the observable unstaged/untracked state for one preserved path."""

    status = _run_git(
        repo,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        path,
        text=False,
    )
    unstaged = _run_git(
        repo,
        "diff",
        "--binary",
        "--",
        path,
        text=False,
    )
    staged = _run_git(
        repo,
        "diff",
        "--cached",
        "--binary",
        "--",
        path,
        text=False,
    )
    untracked_raw = _run_git(
        repo,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        path,
        text=False,
    )

    if not all(
        isinstance(item, bytes)
        for item in (status, unstaged, staged, untracked_raw)
    ):
        raise RepositorySealError(
            "internal preserved-state evidence type drift"
        )

    material = bytearray()
    for label, value in (
        (b"status\0", status),
        (b"unstaged\0", unstaged),
        (b"staged\0", staged),
        (b"untracked-index\0", untracked_raw),
    ):
        material.extend(label)
        material.extend(value)

    untracked_names = [
        name.decode("utf-8", errors="strict")
        for name in untracked_raw.split(b"\0")
        if name
    ]
    for relative in sorted(untracked_names):
        file_path = (repo / relative).resolve()
        try:
            file_path.relative_to(repo)
        except ValueError as exc:
            raise RepositorySealError(
                "untracked preserved evidence escaped repository root"
            ) from exc
        material.extend(b"untracked-file\0")
        material.extend(relative.encode("utf-8"))
        material.extend(b"\0")
        if file_path.is_file() and not file_path.is_symlink():
            material.extend(file_path.read_bytes())
        elif file_path.is_symlink():
            material.extend(b"SYMLINK\0")
            material.extend(os.readlink(file_path).encode("utf-8"))
        else:
            material.extend(b"NON_REGULAR\0")

    return _sha256_bytes(bytes(material))


def _preserved_state(
    repo: Path,
    preserve_paths: Iterable[str],
) -> dict[str, str]:
    return {
        path: _path_state_digest(repo, path)
        for path in sorted(preserve_paths)
    }


def _assert_exact_dirty_surface(
    *,
    observed: list[str],
    expected: list[str],
    label: str,
) -> None:
    if observed != expected:
        observed_set = set(observed)
        expected_set = set(expected)
        unexpected = sorted(observed_set - expected_set)
        missing = sorted(expected_set - observed_set)
        raise RepositorySealError(
            f"{label} dirty surface mismatch; "
            f"unexpected={unexpected}; missing={missing}; "
            f"expected={expected}; observed={observed}"
        )


def stage_exact(
    *,
    repo: Path | str,
    candidate_paths: Iterable[str],
    preserve_paths: Iterable[str],
) -> dict[str, Any]:
    """Stage exactly candidate paths while preserving declared dirty paths."""

    root = _exact_repo_root(repo)
    sets = normalize_path_sets(
        candidate_paths=candidate_paths,
        preserve_paths=preserve_paths,
    )
    candidate = sets["candidate_paths"]
    preserve = sets["preserve_paths"]
    if not candidate:
        raise RepositorySealError(
            "candidate path set must be non-empty"
        )

    expected_dirty = sorted(set(candidate).union(preserve))
    dirty_before = _dirty_paths(root)
    _assert_exact_dirty_surface(
        observed=dirty_before,
        expected=expected_dirty,
        label="pre-stage",
    )

    staged_before = _staged_paths(root)
    staged_outside_candidate = sorted(
        set(staged_before) - set(candidate)
    )
    if staged_outside_candidate:
        protected_staged = sorted(
            set(staged_outside_candidate).intersection(preserve)
        )
        raise RepositorySealError(
            "pre-existing staged paths outside candidate set are forbidden; "
            f"staged={staged_outside_candidate}; "
            f"preserve/protected={protected_staged}"
        )

    preserved_before = _preserved_state(root, preserve)

    cp = subprocess.run(
        ["git", "-C", str(root), "add", "--", *candidate],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
    )
    if cp.returncode != 0:
        raise RepositorySealError(
            "git add candidate set failed rc="
            + str(cp.returncode)
            + "\n"
            + cp.stdout
            + cp.stderr
        )

    staged_after = _staged_paths(root)
    if staged_after != candidate:
        raise RepositorySealError(
            "exact staged candidate mismatch; "
            f"expected={candidate}; observed={staged_after}"
        )

    if set(staged_after).intersection(preserve):
        raise RepositorySealError(
            "preserve/protected paths became staged"
        )

    dirty_after = _dirty_paths(root)
    _assert_exact_dirty_surface(
        observed=dirty_after,
        expected=expected_dirty,
        label="post-stage",
    )

    tracked_unstaged = set(_tracked_unstaged_paths(root))
    untracked = set(_untracked_paths(root))
    preserved_dirty = sorted(
        path
        for path in preserve
        if path in tracked_unstaged or path in untracked
    )
    if preserved_dirty != preserve:
        raise RepositorySealError(
            "preserve/protected dirty state changed during staging; "
            f"expected={preserve}; observed={preserved_dirty}"
        )

    preserved_after = _preserved_state(root, preserve)
    if preserved_after != preserved_before:
        raise RepositorySealError(
            "preserve/protected path evidence changed during staging"
        )

    return {
        "state": "PASS",
        "operation": "STAGE_EXACT",
        "candidate_paths": candidate,
        "preserve_paths": preserve,
        "dirty_union_verified": True,
        "staged_paths": staged_after,
        "preserved_dirty_paths": preserved_dirty,
        "preserved_paths_unchanged": True,
        "git_add_scope": candidate,
        "commit_performed": False,
        "push_performed": False,
    }


def _branch_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepositorySealError("branch must be a non-empty string")
    branch = value.strip()
    if (
        branch.startswith("-")
        or any(ch.isspace() for ch in branch)
        or "\x00" in branch
    ):
        raise RepositorySealError("branch name is unsafe")
    return branch


def _remote_name(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RepositorySealError("remote must be a non-empty string")
    remote = value.strip()
    if (
        remote.startswith("-")
        or any(ch.isspace() for ch in remote)
        or "\x00" in remote
    ):
        raise RepositorySealError("remote name is unsafe")
    return remote


def _remote_head(
    *,
    repo: Path,
    remote: str,
    branch: str,
) -> str:
    raw = str(
        _run_git(
            repo,
            "ls-remote",
            "--heads",
            remote,
            branch,
        )
    )
    rows = [line.split() for line in raw.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) < 2:
        raise RepositorySealError(
            "remote branch HEAD could not be resolved exactly once"
        )
    return rows[0][0]


def push_exact(
    *,
    repo: Path | str,
    branch: str,
    preserve_paths: Iterable[str],
    remote: str = "origin",
) -> dict[str, Any]:
    """Push one exact branch while preserving declared dirty worktree state."""

    root = _exact_repo_root(repo)
    expected_branch = _branch_name(branch)
    remote_name = _remote_name(remote)
    preserve = _normalize_paths(
        preserve_paths,
        label="preserve",
    )

    current_branch = str(
        _run_git(root, "branch", "--show-current")
    ).strip()
    if current_branch != expected_branch:
        raise RepositorySealError(
            "current branch mismatch; "
            f"expected={expected_branch}; observed={current_branch}"
        )

    staged_before = _staged_paths(root)
    if staged_before:
        raise RepositorySealError(
            "staged changes are forbidden before push; staged="
            + ",".join(staged_before)
        )

    dirty_before = _dirty_paths(root)
    _assert_exact_dirty_surface(
        observed=dirty_before,
        expected=preserve,
        label="pre-push",
    )
    preserved_before = _preserved_state(root, preserve)
    local_head = str(
        _run_git(root, "rev-parse", "HEAD")
    ).strip()

    cp = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "push",
            remote_name,
            expected_branch,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        shell=False,
    )
    if cp.returncode != 0:
        raise RepositorySealError(
            "git push failed rc="
            + str(cp.returncode)
            + "\n"
            + cp.stdout
            + cp.stderr
        )

    remote_head = _remote_head(
        repo=root,
        remote=remote_name,
        branch=expected_branch,
    )
    if remote_head != local_head:
        raise RepositorySealError(
            "remote HEAD mismatch after push; "
            f"local={local_head}; remote={remote_head}"
        )

    staged_after = _staged_paths(root)
    if staged_after:
        raise RepositorySealError(
            "staged changes appeared during push; staged="
            + ",".join(staged_after)
        )

    dirty_after = _dirty_paths(root)
    _assert_exact_dirty_surface(
        observed=dirty_after,
        expected=preserve,
        label="post-push",
    )
    preserved_after = _preserved_state(root, preserve)
    if preserved_after != preserved_before:
        raise RepositorySealError(
            "preserve/protected path evidence changed across push"
        )

    return {
        "state": "PASS",
        "operation": "PUSH_EXACT",
        "branch": expected_branch,
        "remote": remote_name,
        "local_head": local_head,
        "remote_head": remote_head,
        "pre_push_dirty_paths": dirty_before,
        "post_push_dirty_paths": dirty_after,
        "preserve_paths": preserve,
        "preserved_paths_unchanged": True,
        "staged_paths": [],
        "merge_performed": False,
    }


def _print_stage_result(result: dict[str, Any]) -> None:
    print("REPOSITORY_SEAL_STAGE_EXACT=PASS")
    print(f"STAGED_PATH_COUNT={len(result['staged_paths'])}")
    for path in result["staged_paths"]:
        print(path)
    print(
        "PRESERVED_DIRTY_PATH_COUNT="
        + str(len(result["preserved_dirty_paths"]))
    )
    for path in result["preserved_dirty_paths"]:
        print(f"PRESERVED={path}")
    print("PRESERVED_PATHS_UNCHANGED=true")


def _print_push_result(result: dict[str, Any]) -> None:
    print("REPOSITORY_SEAL_PUSH=PASS")
    print(f"BRANCH={result['branch']}")
    print(f"LOCAL_HEAD={result['local_head']}")
    print(f"REMOTE_HEAD={result['remote_head']}")
    print(
        "PRESERVED_DIRTY_PATH_COUNT="
        + str(len(result["post_push_dirty_paths"]))
    )
    for path in result["post_push_dirty_paths"]:
        print(f"PRESERVED={path}")
    print("PRESERVED_PATHS_UNCHANGED=true")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ForPrint bounded repository seal mechanics"
    )
    parser.add_argument("--repo", default=".")
    subparsers = parser.add_subparsers(
        dest="operation",
        required=True,
    )

    stage_parser = subparsers.add_parser("stage-exact")
    stage_parser.add_argument("--candidate-paths", required=True)
    stage_parser.add_argument("--preserve-paths", default="")

    push_parser = subparsers.add_parser("push")
    push_parser.add_argument("--branch", required=True)
    push_parser.add_argument("--preserve-paths", default="")

    args = parser.parse_args()

    try:
        if args.operation == "stage-exact":
            result = stage_exact(
                repo=args.repo,
                candidate_paths=_split_path_argument(
                    args.candidate_paths
                ),
                preserve_paths=_split_path_argument(
                    args.preserve_paths
                ),
            )
            _print_stage_result(result)
            return 0

        if args.operation == "push":
            result = push_exact(
                repo=args.repo,
                branch=args.branch,
                preserve_paths=_split_path_argument(
                    args.preserve_paths
                ),
                remote="origin",
            )
            _print_push_result(result)
            return 0

        raise RepositorySealError(
            f"unsupported operation: {args.operation}"
        )
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        RepositorySealError,
    ) as exc:
        print(
            "REPOSITORY_SEAL=FAIL "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
