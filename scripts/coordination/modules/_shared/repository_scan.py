from __future__ import annotations

import ast
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.coordination.modules._shared.io import WorkflowError, read_yaml_mapping

EXCLUDED_PREFIXES = (
    ".git/",
    ".tmp_blueprint_backups/",
    ".venv",
    "tmp/",
    "operator_input/",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "node_modules/",
    "dist/",
    "build/",
)

MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+):(?:\s|$)", re.MULTILINE)


def _git_files(root: Path) -> list[str]:
    command = (
        "git",
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    )
    completed = subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise WorkflowError(f"git file inventory failed: {detail}")
    paths = [
        value.decode("utf-8", errors="surrogateescape")
        for value in completed.stdout.split(b"\0")
        if value
    ]
    return sorted(
        path
        for path in paths
        if not path.startswith(EXCLUDED_PREFIXES)
        and "/__pycache__/" not in path
    )


def _python_record(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    record: dict[str, Any] = {
        "path": relative,
        "parse_status": "verified",
        "functions": [],
        "classes": [],
        "entrypoint": False,
        "imports": [],
    }
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
    except (UnicodeDecodeError, SyntaxError) as exc:
        record["parse_status"] = "failed"
        record["error"] = str(exc)
        return record

    functions: list[str] = []
    classes: list[str] = []
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    record["functions"] = sorted(set(functions))
    record["classes"] = sorted(set(classes))
    record["imports"] = sorted(imports)
    record["entrypoint"] = 'if __name__ == "__main__"' in source
    return record


def _latest_yaml(root: Path, relative_dir: str) -> Path | None:
    directory = root / relative_dir
    candidates = sorted(directory.glob("*.yaml")) if directory.is_dir() else []
    return candidates[-1] if candidates else None


def _inventory_evidence(root: Path) -> dict[str, Any]:
    inventory_path = _latest_yaml(
        root,
        "coordination/repository_knowledge/inventory",
    )
    if inventory_path is None:
        return {
            "path": None,
            "purpose_paths": [],
            "dependency_paths": [],
            "verified_paths": [],
            "snapshot_created_at": None,
        }

    data = read_yaml_mapping(inventory_path)
    purpose_paths: set[str] = set()
    dependency_paths: set[str] = set()
    verified_paths: set[str] = set()

    for entry in data.get("capability_inventory", []):
        if not isinstance(entry, dict):
            continue
        path_value = entry.get("path")
        if not isinstance(path_value, str) or "*" in path_value:
            continue
        candidate = root / path_value
        if not candidate.is_file():
            continue
        purpose = entry.get("purpose")
        if isinstance(purpose, dict) and purpose.get("status") in {
            "verified",
            "inferred",
        }:
            purpose_paths.add(path_value)
        dependencies = entry.get("dependencies")
        if isinstance(dependencies, dict) and (
            dependencies.get("internal") or dependencies.get("external")
        ):
            dependency_paths.add(path_value)
        if (
            entry.get("tests")
            and entry.get("evidence")
            and not entry.get("unknowns")
            and entry.get("recovery_path")
        ):
            verified_paths.add(path_value)

    snapshot = data.get("snapshot", {})
    created_at = snapshot.get("created_at") if isinstance(snapshot, dict) else None
    return {
        "path": inventory_path.relative_to(root).as_posix(),
        "purpose_paths": sorted(purpose_paths),
        "dependency_paths": sorted(dependency_paths),
        "verified_paths": sorted(verified_paths),
        "snapshot_created_at": created_at,
    }


def _workflow_evidence(root: Path, index_path: str) -> dict[str, Any]:
    index = read_yaml_mapping(root / index_path)
    workflows = index.get("workflows", [])
    records = [item for item in workflows if isinstance(item, dict)]
    documented = sum(
        isinstance(item.get("documentation"), str)
        and (root / item["documentation"]).is_file()
        for item in records
    )
    automated = sum(
        isinstance(item.get("script"), str)
        and (root / item["script"]).is_file()
        and isinstance(item.get("make_targets"), dict)
        and bool(item["make_targets"].get("generic"))
        for item in records
    )
    recovery = sum(
        isinstance(item.get("recovery"), str)
        and (root / item["recovery"]).is_file()
        for item in records
    )
    make_targets: set[str] = set()
    for item in records:
        target_map = item.get("make_targets")
        if not isinstance(target_map, dict):
            continue
        for values in target_map.values():
            if isinstance(values, list):
                make_targets.update(
                    value for value in values if isinstance(value, str)
                )
    return {
        "total": len(records),
        "documented": documented,
        "automated": automated,
        "recovery": recovery,
        "declared_make_targets": sorted(make_targets),
    }


def _freshness_days(created_at: str | None) -> int | None:
    if not created_at:
        return None
    try:
        timestamp = datetime.fromisoformat(created_at)
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    delta = datetime.now(UTC) - timestamp.astimezone(UTC)
    return max(0, delta.days)


def scan_repository(
    root: Path,
    *,
    workflow_index_path: str,
) -> dict[str, Any]:
    files = _git_files(root)
    python_paths = [
        path
        for path in files
        if path.endswith(".py") and (root / path).is_file()
    ]
    python_records = [_python_record(root, path) for path in python_paths]

    makefile = root / "Makefile"
    make_targets = (
        sorted(set(MAKE_TARGET_RE.findall(makefile.read_text(encoding="utf-8"))))
        if makefile.is_file()
        else []
    )
    inventory = _inventory_evidence(root)
    workflows = _workflow_evidence(root, workflow_index_path)

    file_set = set(files)
    purpose_understood = len(file_set.intersection(inventory["purpose_paths"]))
    dependencies_mapped = len(file_set.intersection(inventory["dependency_paths"]))
    fully_verified = len(file_set.intersection(inventory["verified_paths"]))
    declared_targets = set(workflows["declared_make_targets"])
    mapped_targets = len(declared_targets.intersection(make_targets))

    category_counts = Counter(
        path.split("/", 1)[0] if "/" in path else "<root>" for path in files
    )
    suffix_counts = Counter(Path(path).suffix or "<none>" for path in files)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "repository_root": str(root),
        "files": {
            "total": len(files),
            "indexed": len(files),
            "purpose_understood": purpose_understood,
            "dependencies_mapped": dependencies_mapped,
            "fully_verified": fully_verified,
            "unknown": max(0, len(files) - purpose_understood),
            "categories": dict(sorted(category_counts.items())),
            "suffixes": dict(sorted(suffix_counts.items())),
        },
        "python": {
            "files": len(python_records),
            "parsed": sum(item["parse_status"] == "verified" for item in python_records),
            "parse_failures": sum(item["parse_status"] == "failed" for item in python_records),
            "functions": sum(len(item["functions"]) for item in python_records),
            "classes": sum(len(item["classes"]) for item in python_records),
            "entrypoints": sum(bool(item["entrypoint"]) for item in python_records),
            "records": python_records,
        },
        "make": {
            "targets_total": len(make_targets),
            "targets": make_targets,
            "workflow_targets_declared": len(declared_targets),
            "workflow_targets_mapped": mapped_targets,
        },
        "workflows": workflows,
        "repository_knowledge": {
            "inventory_path": inventory["path"],
            "snapshot_created_at": inventory["snapshot_created_at"],
            "freshness_days": _freshness_days(inventory["snapshot_created_at"]),
        },
        "metadata_consistency": {
            "status": "unknown",
            "note": "Queue/roadmap/current-focus consistency audit is not implemented in v0.1.",
        },
    }
