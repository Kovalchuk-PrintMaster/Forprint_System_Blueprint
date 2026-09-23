from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

EPHEMERAL_DIR_NAMES = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "__pycache__",
    "node_modules",
    "target",
    "dist",
    "build",
}
EPHEMERAL_PREFIXES = (".venv", "venv")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_state(root: Path, rel: Path) -> dict[str, Any]:
    path = root / rel
    if path.is_symlink():
        return {"exists": True, "kind": "symlink", "target": str(path.readlink())}
    if path.is_file():
        stat = path.stat()
        return {
            "exists": True,
            "kind": "file",
            "sha256": sha256(path),
            "bytes": stat.st_size,
            "mode": stat.st_mode & 0o777,
        }
    if path.exists():
        return {"exists": True, "kind": "other"}
    return {"exists": False, "kind": "missing"}


def _skip_dir(name: str) -> bool:
    return name in EPHEMERAL_DIR_NAMES or name.startswith(EPHEMERAL_PREFIXES)


def durable_tree_state(
    root: Path,
    target_paths: set[str],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for current, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current)
        dirnames[:] = [
            name
            for name in dirnames
            if not _skip_dir(name) and not (current_path == root and name == "tmp")
        ]
        for name in filenames:
            path = current_path / name
            rel = path.relative_to(root)
            rel_text = rel.as_posix()
            if rel_text in target_paths:
                continue
            result[rel_text] = file_state(root, rel)
    return result


def capture_external_baseline(
    root: Path,
    target_paths: set[str],
) -> dict[str, dict[str, Any]]:
    return durable_tree_state(root, target_paths)


def verify_external_baseline(
    root: Path,
    target_paths: set[str],
    baseline: dict[str, dict[str, Any]],
) -> tuple[bool, list[str]]:
    current = durable_tree_state(root, target_paths)
    problems: list[str] = []

    added = sorted(set(current) - set(baseline))
    removed = sorted(set(baseline) - set(current))
    changed = sorted(rel for rel in set(current) & set(baseline) if current[rel] != baseline[rel])

    if added:
        problems.append(f"added external durable paths: {added}")
    if removed:
        problems.append(f"removed external durable paths: {removed}")
    if changed:
        problems.append(f"changed external durable paths: {changed}")

    return not problems, problems
