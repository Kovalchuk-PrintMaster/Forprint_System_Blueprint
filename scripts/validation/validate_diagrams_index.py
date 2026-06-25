#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

DIAGRAMS_DIR = Path("diagrams")
INDEX_PATH = DIAGRAMS_DIR / "index.yaml"

ALLOWED_STATUSES = {
    "generated",
    "tracked_manual",
}

ALLOWED_FORMATS = {
    "mermaid",
}


def _issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def _read_yaml(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [_issue(path, "file does not exist")]

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [_issue(path, f"invalid YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [_issue(path, "YAML root must be a mapping")]

    return data, []


def _is_safe_relative_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _validate_artifact(root: Path, artifact: dict[str, Any], index: int) -> list[str]:
    issues: list[str] = []
    index_path = root / INDEX_PATH

    for field_name in ("diagram_id", "file", "title", "format", "status", "purpose"):
        value = artifact.get(field_name)
        if not isinstance(value, str) or not value.strip():
            issues.append(
                _issue(index_path, f"`artifacts[{index}].{field_name}` must be a non-empty string")
            )

    file_value = artifact.get("file")
    if isinstance(file_value, str) and file_value.strip():
        if not _is_safe_relative_path(file_value):
            issues.append(_issue(index_path, f"`artifacts[{index}].file` must be a safe relative path"))
        else:
            diagram_path = root / DIAGRAMS_DIR / file_value
            if not diagram_path.exists():
                issues.append(_issue(index_path, f"diagram file does not exist: {diagram_path}"))
            elif not diagram_path.is_file():
                issues.append(_issue(index_path, f"diagram path is not a file: {diagram_path}"))
            else:
                if diagram_path.suffix != ".mmd":
                    issues.append(_issue(diagram_path, "diagram file must use `.mmd` extension"))

                text = diagram_path.read_text(encoding="utf-8")
                if not text.strip():
                    issues.append(_issue(diagram_path, "diagram file must not be empty"))

                stripped = text.lstrip()
                if stripped.startswith("```"):
                    issues.append(
                        _issue(
                            diagram_path,
                            "diagram `.mmd` files must contain raw Mermaid without markdown fences",
                        )
                    )

    diagram_format = artifact.get("format")
    if isinstance(diagram_format, str) and diagram_format not in ALLOWED_FORMATS:
        issues.append(_issue(index_path, f"unsupported diagram format `{diagram_format}`"))

    status = artifact.get("status")
    if isinstance(status, str) and status not in ALLOWED_STATUSES:
        issues.append(_issue(index_path, f"unsupported diagram status `{status}`"))

    if status == "generated":
        generator = artifact.get("generator")
        if not isinstance(generator, str) or not generator.strip():
            issues.append(_issue(index_path, f"`artifacts[{index}].generator` is required for generated diagrams"))
        elif not _is_safe_relative_path(generator):
            issues.append(_issue(index_path, f"`artifacts[{index}].generator` must be a safe relative path"))
        elif not (root / generator).is_file():
            issues.append(_issue(index_path, f"generator file does not exist: {root / generator}"))

        source_files = artifact.get("source_files")
        if not isinstance(source_files, list) or not source_files:
            issues.append(_issue(index_path, f"`artifacts[{index}].source_files` is required for generated diagrams"))
        else:
            for source_index, source_file in enumerate(source_files):
                if not isinstance(source_file, str) or not source_file.strip():
                    issues.append(
                        _issue(
                            index_path,
                            f"`artifacts[{index}].source_files[{source_index}]` must be a non-empty string",
                        )
                    )
                    continue

                if not _is_safe_relative_path(source_file):
                    issues.append(
                        _issue(
                            index_path,
                            f"`artifacts[{index}].source_files[{source_index}]` must be a safe relative path",
                        )
                    )
                elif not (root / source_file).is_file():
                    issues.append(_issue(index_path, f"source file does not exist: {root / source_file}"))

    return issues


def _indexed_diagram_files(data: dict[str, Any]) -> set[str]:
    root_record = data.get("diagrams_index")
    if not isinstance(root_record, dict):
        return set()

    artifacts = root_record.get("artifacts")
    if not isinstance(artifacts, list):
        return set()

    result: set[str] = set()
    for artifact in artifacts:
        if isinstance(artifact, dict):
            file_value = artifact.get("file")
            if isinstance(file_value, str):
                result.add(file_value)

    return result


def validate_diagrams_index(root: Path) -> list[str]:
    issues: list[str] = []
    index_path = root / INDEX_PATH

    readme_path = root / DIAGRAMS_DIR / "README.md"
    if not readme_path.is_file():
        issues.append(_issue(readme_path, "diagrams README is missing"))

    data, yaml_issues = _read_yaml(index_path)
    issues.extend(yaml_issues)

    if data is None:
        return issues

    root_record = data.get("diagrams_index")
    if not isinstance(root_record, dict):
        return issues + [_issue(index_path, "`diagrams_index` must be a mapping")]

    if root_record.get("version") != "0.1":
        issues.append(_issue(index_path, "`diagrams_index.version` must be `0.1`"))

    if root_record.get("status") != "active":
        issues.append(_issue(index_path, "`diagrams_index.status` must be `active`"))

    artifacts = root_record.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return issues + [_issue(index_path, "`diagrams_index.artifacts` must be a non-empty list")]

    known_ids: set[str] = set()

    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            issues.append(_issue(index_path, f"`artifacts[{index}]` must be a mapping"))
            continue

        diagram_id = artifact.get("diagram_id")
        if isinstance(diagram_id, str):
            if diagram_id in known_ids:
                issues.append(_issue(index_path, f"duplicate diagram_id `{diagram_id}`"))
            known_ids.add(diagram_id)

        issues.extend(_validate_artifact(root, artifact, index))

    indexed_files = _indexed_diagram_files(data)
    actual_mmd_files = {
        path.relative_to(root / DIAGRAMS_DIR).as_posix()
        for path in (root / DIAGRAMS_DIR).glob("*.mmd")
        if path.is_file()
    }

    for file_name in sorted(actual_mmd_files - indexed_files):
        issues.append(_issue(index_path, f"diagram file is not indexed: {file_name}"))

    for file_name in sorted(indexed_files - actual_mmd_files):
        issues.append(_issue(index_path, f"indexed diagram file is missing from diagrams directory: {file_name}"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForPrint Blueprint diagrams index.")
    parser.add_argument("--root", default=".", help="Blueprint repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    issues = validate_diagrams_index(root)

    if issues:
        print("❌ Diagrams index validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Diagrams index validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
