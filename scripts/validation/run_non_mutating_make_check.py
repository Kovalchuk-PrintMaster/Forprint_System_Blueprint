#!/usr/bin/env python3
"""Run a Blueprint Make validation target in a disposable repository mirror.

The durable Blueprint working tree is treated as read-only input. A private Git
clone is created, the current dirty working tree is faithfully overlaid into that
clone, including top-level reports when present, and the requested Make target is
executed there. Optional sibling module state is mirrored the same way.

This runner provides input fidelity and mutation isolation. Deliberately removing
runtime artifacts to test dependency closure is a separate sterile-audit concern.

This runner does not stage, commit, push, reset, stash, rebase, or mutate the
source repositories.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

CONTRACT = "coordination/standards/automation/non_mutating_check_contract_v0_1.yaml"

TOP_LEVEL_NON_MIRRORED_ROOTS = {
    ".git",
    ".venv_blueprint",
    "tmp",
}

RECURSIVE_CACHE_EXCLUDES = {
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    "__pycache__",
    "node_modules",
}


class IsolationError(RuntimeError):
    """Raised when an isolated check cannot be prepared safely."""


def _run(
    cwd: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env=env,
    )
    if check and cp.returncode:
        raise IsolationError(f"command failed rc={cp.returncode}: {' '.join(args)}\n{cp.stdout}")
    return cp


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _state(path: Path) -> dict:
    mode = stat.S_IMODE(path.lstat().st_mode)
    if path.is_symlink():
        return {
            "kind": "symlink",
            "target": os.readlink(path),
            "mode": mode,
        }
    if path.is_file():
        return {
            "kind": "file",
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "mode": mode,
        }
    return {"kind": "other", "mode": mode}


def _is_excluded_relative_path(rel: Path) -> bool:
    if not rel.parts:
        return False
    if rel.parts[0] in TOP_LEVEL_NON_MIRRORED_ROOTS:
        return True
    return any(part in RECURSIVE_CACHE_EXCLUDES for part in rel.parts)


def durable_fingerprint(root: Path) -> dict[str, dict]:
    """Hash durable state using explicit repository-relative exclusion rules."""

    result: dict[str, dict] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if _is_excluded_relative_path(rel):
            continue
        if any(_secret_like_name(part) for part in rel.parts):
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        result[rel.as_posix()] = _state(path)
    return result


def _clear_clone_worktree(destination: Path) -> None:
    for child in destination.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def _secret_like_name(name: str) -> bool:
    return name == ".env" or name.startswith(".env.")


def _copy_entry(source: Path, destination: Path) -> None:
    if source.is_symlink():
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(
                *RECURSIVE_CACHE_EXCLUDES,
                ".git",
                ".env",
                ".env.*",
            ),
        )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def overlay_worktree(source: Path, destination: Path) -> None:
    """Make clone worktree faithfully reflect current source state except explicit non-mirrored roots."""

    _clear_clone_worktree(destination)
    for child in source.iterdir():
        if (
            child.name in TOP_LEVEL_NON_MIRRORED_ROOTS
            or child.name in RECURSIVE_CACHE_EXCLUDES
            or _secret_like_name(child.name)
        ):
            continue
        _copy_entry(child, destination / child.name)


def prepare_repository_mirror(source: Path, destination: Path) -> None:
    """Create an independent local clone and overlay current dirty state."""

    if not (source / ".git").exists():
        raise IsolationError(f"not a Git repository: {source}")

    _run(
        source,
        "git",
        "clone",
        "--quiet",
        "--no-hardlinks",
        str(source),
        str(destination),
    )
    overlay_worktree(source, destination)

    original_venv = source / ".venv_blueprint"
    if original_venv.exists():
        mirror_venv = destination / ".venv_blueprint"
        if mirror_venv.exists() or mirror_venv.is_symlink():
            if mirror_venv.is_dir() and not mirror_venv.is_symlink():
                shutil.rmtree(mirror_venv)
            else:
                mirror_venv.unlink()
        mirror_venv.symlink_to(original_venv, target_is_directory=True)


def _resolve_module_root(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    return candidate


def run_isolated_check(
    *,
    root: Path,
    target: str,
    module_root: Path | None,
    keep_workspace: bool,
) -> int:
    root = root.resolve()
    before_root = durable_fingerprint(root)
    before_module = (
        durable_fingerprint(module_root)
        if module_root is not None and module_root.is_dir()
        else None
    )

    temp_parent = Path(tempfile.mkdtemp(prefix="forprint_non_mutating_check_")).resolve()
    workspace = temp_parent / root.name
    isolated_module: Path | None = None
    continuity_baseline_path = temp_parent / "continuity_source_state_baseline.json"
    source_continuity_cli = root / "scripts/coordination/continuity.py"

    try:
        # Freeze continuity source state from the durable source repository
        # before creating the disposable mirror. The mirror faithfully copies
        # working-tree bytes but has an independent Git index, so deriving the
        # baseline inside the mirror would lose staged/index status semantics.
        if source_continuity_cli.is_file():
            baseline_cp = _run(
                root,
                sys.executable,
                "scripts/coordination/continuity.py",
                "fingerprint",
                "--root",
                ".",
                "--output",
                str(continuity_baseline_path),
                check=False,
            )
            if baseline_cp.returncode:
                raise IsolationError(
                    "failed to freeze continuity source-state baseline\n"
                    + baseline_cp.stdout
                )
            if not continuity_baseline_path.is_file():
                raise IsolationError(
                    "continuity source-state baseline was not created"
                )

        prepare_repository_mirror(root, workspace)

        if module_root is not None and module_root.is_dir():
            isolated_module = temp_parent / module_root.name
            prepare_repository_mirror(module_root, isolated_module)

        env = os.environ.copy()
        env["FORPRINT_NON_MUTATING_CHECK_ISOLATED"] = "1"
        if continuity_baseline_path.is_file():
            env["FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE"] = str(continuity_baseline_path)
            env["FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT"] = str(workspace.resolve())
        env.pop("MAKEFLAGS", None)
        env.pop("MFLAGS", None)
        env.pop("MAKELEVEL", None)

        command = [
            "make",
            "--no-print-directory",
            target,
            f"PYTHON={sys.executable}",
        ]
        if isolated_module is not None:
            command.append(f"MODULE_ROOT={isolated_module}")

        cp = _run(
            workspace,
            *command,
            check=False,
            env=env,
        )

        after_root = durable_fingerprint(root)
        if after_root != before_root:
            raise IsolationError("source Blueprint durable state changed during isolated check")

        if before_module is not None and module_root is not None:
            after_module = durable_fingerprint(module_root)
            if after_module != before_module:
                raise IsolationError("source module durable state changed during isolated check")

        sys.stdout.write(cp.stdout)
        if cp.returncode:
            print(
                f"NON_MUTATING_CHECK=FAIL inner_return_code={cp.returncode}",
                file=sys.stderr,
            )
            return cp.returncode

        print("NON_MUTATING_CHECK=PASS")
        print(f"ISOLATED_TARGET={target}")
        print("SOURCE_BLUEPRINT_PRESERVED=true")
        if before_module is not None:
            print("SOURCE_MODULE_PRESERVED=true")
        return 0
    finally:
        if keep_workspace:
            print(f"ISOLATED_WORKSPACE={temp_parent}")
        else:
            shutil.rmtree(temp_parent, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    parser.add_argument("--target", default="check-core")
    parser.add_argument("--module-root", default=None)
    parser.add_argument("--keep-workspace", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[2]
    module_root = _resolve_module_root(root, args.module_root)

    try:
        return run_isolated_check(
            root=root,
            target=args.target,
            module_root=module_root,
            keep_workspace=args.keep_workspace,
        )
    except IsolationError as exc:
        print(f"NON_MUTATING_CHECK=FAIL {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
