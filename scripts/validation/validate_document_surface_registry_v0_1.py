#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"
BASELINE = ROOT / "coordination/internal_work/blueprint/normalization/2026-09-01__document_surface_normalization_baseline_v0_1.yaml"


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def tracked_and_untracked() -> list[str]:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.splitlines()
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.splitlines()
    return sorted(set(tracked + untracked))


def match(pattern: str, rel: str) -> bool:
    # Slash-aware repository matching:
    # - '*' stays inside one path segment;
    # - '**/*' preserves recursive-prefix semantics.
    if "**/*" in pattern:
        prefix, suffix = pattern.split("**/*", 1)

        if not rel.startswith(prefix):
            return False

        remainder = rel[len(prefix):]

        if not remainder:
            return False

        if not suffix:
            return True

        return PurePosixPath(remainder).match("*" + suffix)

    return PurePosixPath(rel).match(pattern)


def _profile_specificity(pattern: str) -> tuple[int, int]:
    literal_segments = sum(
        1
        for segment in pattern.split("/")
        if "*" not in segment and "?" not in segment
    )

    literal_chars = len(
        pattern.replace("*", "").replace("?", "")
    )

    return literal_segments, literal_chars


def effective_profile(
    entry: dict[str, Any],
    rel: str,
) -> dict[str, Any]:
    matching_subclasses: list[dict[str, Any]] = []

    for subclass in entry.get("strict_subclasses", []):
        if not isinstance(subclass, dict):
            continue

        pattern = subclass.get("path_pattern")

        if not isinstance(pattern, str) or not pattern:
            continue

        if match(pattern, rel):
            matching_subclasses.append(subclass)

    if not matching_subclasses:
        return entry

    matching_subclasses.sort(
        key=lambda item: _profile_specificity(
            str(item.get("path_pattern", ""))
        ),
        reverse=True,
    )

    if len(matching_subclasses) > 1:
        first_specificity = _profile_specificity(
            str(
                matching_subclasses[0].get(
                    "path_pattern",
                    "",
                )
            )
        )

        second_specificity = _profile_specificity(
            str(
                matching_subclasses[1].get(
                    "path_pattern",
                    "",
                )
            )
        )

        if first_specificity == second_specificity:
            raise ValueError(
                f"AMBIGUOUS_STRICT_SUBCLASS:{rel}:"
                f"{matching_subclasses[0].get('subclass_id')}:"
                f"{matching_subclasses[1].get('subclass_id')}"
            )

    merged = dict(entry)
    merged.update(matching_subclasses[0])

    return merged


def baseline_paths(data: dict[str, Any]) -> set[str]:
    result = set()
    for key in ("yaml_debt", "markdown_debt"):
        for item in data.get(key, []):
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                result.add(item["path"])
    return result


def main() -> int:
    if not REGISTRY.is_file() or not BASELINE.is_file():
        print("DOCUMENT_SURFACE_REGISTRY_VALIDATION=FAIL")
        print("ERROR=REGISTRY_OR_BASELINE_MISSING")
        return 1

    registry = load_yaml(REGISTRY)
    baseline = load_yaml(BASELINE)

    if registry.get("schema_version") != "forprint_document_type_registry_v0_1":
        print("DOCUMENT_SURFACE_REGISTRY_VALIDATION=FAIL")
        print("ERROR=BAD_REGISTRY_SCHEMA")
        return 1

    types = registry.get("types")
    if not isinstance(types, list) or not types:
        print("DOCUMENT_SURFACE_REGISTRY_VALIDATION=FAIL")
        print("ERROR=EMPTY_TYPE_REGISTRY")
        return 1

    known_debt = baseline_paths(baseline)
    repo_files = tracked_and_untracked()
    errors: list[str] = []

    for entry in types:
        if not isinstance(entry, dict):
            errors.append("INVALID_TYPE_ENTRY")
            continue

        doc_type = entry.get("document_type")
        patterns = entry.get("path_patterns", [])
        if not isinstance(doc_type, str) or not doc_type:
            errors.append("TYPE_WITHOUT_ID")
            continue
        if not isinstance(patterns, list) or not patterns:
            errors.append(f"TYPE_WITHOUT_PATTERNS:{doc_type}")
            continue

        for rel in repo_files:
            if not any(match(str(pattern), rel) for pattern in patterns):
                continue

            path = ROOT / rel

            try:
                profile = effective_profile(
                    entry,
                    rel,
                )
            except ValueError as exc:
                errors.append(str(exc))
                continue

            fmt = profile.get(
                "format",
                entry.get("format"),
            )

            required = profile.get(
                "required_top_level",
                entry.get(
                    "required_top_level",
                    [],
                ),
            )

            if fmt == "yaml" and path.suffix.lower() in {".yaml", ".yml"}:
                try:
                    data = load_yaml(path)
                except Exception as exc:
                    if rel not in known_debt:
                        errors.append(f"YAML_PARSE:{rel}:{exc}")
                    continue

                if isinstance(required, list) and required and isinstance(data, dict):
                    missing = [
                        str(key)
                        for key in required
                        if key not in data
                    ]

                    if missing and rel not in known_debt:
                        errors.append(
                            f"REQUIRED_METADATA:{rel}:{','.join(missing)}"
                        )

                expected_schema = profile.get("schema_version")

                if (
                    isinstance(expected_schema, str)
                    and expected_schema
                    and isinstance(data, dict)
                    and data.get("schema_version") != expected_schema
                    and rel not in known_debt
                ):
                    errors.append(
                        f"SCHEMA_VERSION:{rel}:"
                        f"expected={expected_schema}:"
                        f"actual={data.get('schema_version')}"
                    )

    p = subprocess.run(
        [sys.executable, "scripts/generate_module_policy_docs.py", "--check"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if p.returncode:
        errors.append("GENERATED_MODULE_POLICY_DRIFT")

    if errors:
        print("DOCUMENT_SURFACE_REGISTRY_VALIDATION=FAIL")
        for err in errors:
            print("ERROR=" + err)
        return 1

    print("DOCUMENT_SURFACE_REGISTRY_VALIDATION=PASS")
    print("REGISTERED_TYPE_COUNT=" + str(len(types)))
    print("BASELINE_DEBT_PATH_COUNT=" + str(len(known_debt)))
    print("GENERATED_MODULE_POLICY_DRIFT=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
