#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
from pathlib import Path


class ValidationFailure(RuntimeError):
    pass


def run_git(
    root: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and result.returncode != 0:
        raise ValidationFailure(
            f"git {' '.join(args)} failed ({result.returncode}):\n{result.stdout}"
        )
    return result


def parse_status_paths(status: str) -> set[str]:
    paths: set[str] = set()
    entries = status.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        if not entry:
            index += 1
            continue
        if len(entry) < 4:
            raise ValidationFailure(f"unexpected porcelain status entry: {entry!r}")

        code = entry[:2]
        path = entry[3:]
        paths.add(path)

        if "R" in code or "C" in code:
            index += 1
            if index >= len(entries) or not entries[index]:
                raise ValidationFailure("rename/copy status entry is missing its peer path")
            paths.add(entries[index])

        index += 1

    return paths


def normalize_expected_paths(
    root: Path,
    raw_paths: list[str],
) -> list[str]:
    if not raw_paths:
        raise ValidationFailure("at least one --path is required")

    normalized: list[str] = []
    seen: set[str] = set()

    for raw in raw_paths:
        candidate = Path(raw)
        if candidate.is_absolute():
            try:
                candidate = candidate.relative_to(root)
            except ValueError as error:
                raise ValidationFailure(f"expected path is outside repository: {raw}") from error

        value = candidate.as_posix()
        if value in {"", "."} or value.startswith("../"):
            raise ValidationFailure(f"invalid repository-relative expected path: {raw}")
        if value in seen:
            raise ValidationFailure(f"duplicate expected path: {value}")

        seen.add(value)
        normalized.append(value)

    return normalized


def git_index_path(root: Path) -> Path:
    value = run_git(
        root,
        ["rev-parse", "--git-path", "index"],
    ).stdout.strip()
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def hash_optional_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(
    root: Path,
    expected_paths: list[str],
) -> dict[str, object]:
    root = root.resolve()

    inside = run_git(
        root,
        ["rev-parse", "--is-inside-work-tree"],
        check=False,
    )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        raise ValidationFailure(f"not a Git working tree: {root}")

    expected = normalize_expected_paths(root, expected_paths)
    expected_set = set(expected)

    head = run_git(root, ["rev-parse", "HEAD"]).stdout.strip()

    real_cached_before = run_git(
        root,
        ["diff", "--cached", "--name-status"],
    ).stdout
    if real_cached_before.strip():
        raise ValidationFailure(
            "real Git index must be clean before temporary-index validation:\n" + real_cached_before
        )

    status_before = run_git(
        root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    ).stdout
    actual_dirty = parse_status_paths(status_before)

    if actual_dirty != expected_set:
        missing = sorted(expected_set - actual_dirty)
        unexpected = sorted(actual_dirty - expected_set)
        raise ValidationFailure(
            f"working-tree mutation path set mismatch; missing={missing}, unexpected={unexpected}"
        )

    real_index = git_index_path(root)
    real_index_hash_before = hash_optional_file(real_index)

    with tempfile.TemporaryDirectory(prefix="forprint-mutation-precommit-index-") as temporary:
        temp_index = Path(temporary) / "index"
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(temp_index)

        run_git(root, ["read-tree", "HEAD"], env=env)
        run_git(
            root,
            ["add", "-A", "--", *expected],
            env=env,
        )

        staged_paths_raw = run_git(
            root,
            [
                "diff",
                "--cached",
                "--name-only",
                "-z",
                "--diff-filter=ACDMRTUXB",
            ],
            env=env,
        ).stdout
        staged_paths = {item for item in staged_paths_raw.split("\0") if item}

        if staged_paths != expected_set:
            missing = sorted(expected_set - staged_paths)
            unexpected = sorted(staged_paths - expected_set)
            raise ValidationFailure(
                "temporary-index staged path set mismatch; "
                f"missing={missing}, unexpected={unexpected}"
            )

        diff_check = run_git(
            root,
            ["diff", "--cached", "--check", "--", *expected],
            env=env,
            check=False,
        )
        if diff_check.returncode != 0:
            raise ValidationFailure(
                "temporary-index git diff --cached --check failed:\n" + diff_check.stdout
            )

    real_index_hash_after = hash_optional_file(real_index)
    if real_index_hash_after != real_index_hash_before:
        raise ValidationFailure("real Git index changed during temporary-index validation")

    real_cached_after = run_git(
        root,
        ["diff", "--cached", "--name-status"],
    ).stdout
    if real_cached_after != real_cached_before:
        raise ValidationFailure("real Git cached diff changed during temporary-index validation")

    status_after = run_git(
        root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    ).stdout
    if status_after != status_before:
        raise ValidationFailure("working-tree status changed during temporary-index validation")

    return {
        "result": "MUTATION_PRECOMMIT_SURFACE_VALID",
        "head": head,
        "expected_paths": sorted(expected_set),
        "real_git_index_changed": False,
        "working_tree_changed_by_validator": False,
        "git_diff_cached_check": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an exact mutation surface with a temporary Git "
            "index without staging the real repository index."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root.",
    )
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        default=[],
        help=("Expected dirty repository-relative path. Repeat for each declared mutation path."),
    )
    args = parser.parse_args()

    try:
        result = validate(Path(args.root), args.paths)
    except ValidationFailure as error:
        print(f"FAILED: {error}")
        print("RESULT: MUTATION_PRECOMMIT_SURFACE_INVALID")
        return 1

    print(f"HEAD: {result['head']}")
    print("Expected mutation paths:")
    for path in result["expected_paths"]:
        print(f"- {path}")
    print("Real Git index changed: False")
    print("Working tree changed by validator: False")
    print("git diff --cached --check: passed")
    print("RESULT: MUTATION_PRECOMMIT_SURFACE_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
