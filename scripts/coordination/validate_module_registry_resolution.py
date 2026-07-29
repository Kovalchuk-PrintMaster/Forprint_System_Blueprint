#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA = "module_registry_resolution_v0_1"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid YAML {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def is_git_tracked(repo_root: Path, relative: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "--",
            relative,
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def validate_manifest(
    manifest_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    manifest = load_yaml(manifest_path)
    policy_errors: list[str] = []
    module_results: list[dict[str, Any]] = []

    if manifest.get("schema_version") != EXPECTED_SCHEMA:
        policy_errors.append("schema_version mismatch")

    policy = manifest.get("policy")

    if not isinstance(policy, dict):
        policy_errors.append("policy section is missing")
        policy = {}

    require_tracked = policy.get("require_git_tracked_sources") is True

    if policy.get("canonical_id_unique") is not True:
        policy_errors.append("canonical_id_unique must be true")

    if policy.get("cross_repository_writes_forbidden") is not True:
        policy_errors.append("cross_repository_writes_forbidden must be true")

    external_rollout = manifest.get("external_rollout")

    if not isinstance(external_rollout, dict):
        policy_errors.append("external_rollout section is missing")
    elif external_rollout.get("state") != "gated":
        policy_errors.append("external rollout must remain gated")

    modules = manifest.get("modules")

    if not isinstance(modules, list) or not modules:
        policy_errors.append("modules must be a non-empty list")
        modules = []

    canonical_ids: list[str] = []
    source_owners: dict[str, str] = {}

    for record in modules:
        errors: list[str] = []

        if not isinstance(record, dict):
            module_results.append(
                {
                    "module_id": None,
                    "status": "FAILED",
                    "errors": ["module record must be a mapping"],
                }
            )
            continue

        module_id = record.get("module_id")
        canonical_sources = record.get("canonical_sources")

        if not isinstance(module_id, str) or not module_id:
            errors.append("module_id is required")
        else:
            canonical_ids.append(module_id)

        if not isinstance(canonical_sources, list) or len(canonical_sources) < 2:
            errors.append("at least two canonical_sources are required")
            canonical_sources = []

        source_kinds: set[str] = set()

        for source in canonical_sources:
            if not isinstance(source, dict):
                errors.append("canonical source must be a mapping")
                continue

            source_kind = source.get("kind")
            relative_path = source.get("path")

            if not isinstance(source_kind, str) or not source_kind:
                errors.append("canonical source kind is required")
            else:
                source_kinds.add(source_kind)

            if not isinstance(relative_path, str) or not relative_path:
                errors.append("canonical source path is required")
                continue

            absolute = repo_root / relative_path

            if not absolute.is_file():
                errors.append(f"canonical source missing: {relative_path}")

            if require_tracked and not is_git_tracked(
                repo_root,
                relative_path,
            ):
                errors.append(f"canonical source is not Git tracked: {relative_path}")

            previous_owner = source_owners.get(relative_path)

            if previous_owner is not None and previous_owner != module_id:
                errors.append(f"canonical source collision with {previous_owner}: {relative_path}")
            elif isinstance(module_id, str):
                source_owners[relative_path] = module_id

        required_kinds = {
            "module_roadmap",
            "prompt_queue_index",
        }
        missing_kinds = sorted(required_kinds - source_kinds)

        if missing_kinds:
            errors.append("missing canonical source kinds: " + ", ".join(missing_kinds))

        module_results.append(
            {
                "module_id": module_id,
                "status": ("PASSED" if not errors else "FAILED"),
                "canonical_source_count": len(canonical_sources),
                "errors": errors,
            }
        )

    duplicates = sorted(
        {module_id for module_id in canonical_ids if canonical_ids.count(module_id) > 1}
    )

    if duplicates:
        policy_errors.append("duplicate canonical module IDs: " + ", ".join(duplicates))

    expected_modules = manifest.get("expected_active_module_ids")

    if not isinstance(expected_modules, list):
        policy_errors.append("expected_active_module_ids is missing")
        expected_modules = []

    expected_set = {value for value in expected_modules if isinstance(value, str)}
    canonical_set = set(canonical_ids)

    if canonical_set != expected_set:
        policy_errors.append(
            "canonical module coverage mismatch: "
            f"expected={sorted(expected_set)!r}, "
            f"actual={sorted(canonical_set)!r}"
        )

    failed_modules = [result for result in module_results if result.get("status") != "PASSED"]
    passed = not policy_errors and not failed_modules

    return {
        "schema_version": ("module_registry_resolution_report_v0_1"),
        "metadata": {
            "manifest": str(manifest_path),
            "repo_root": str(repo_root),
            "result": ("PASSED" if passed else "FAILED"),
        },
        "summary": {
            "module_count": len(module_results),
            "passed_modules": sum(result.get("status") == "PASSED" for result in module_results),
            "failed_modules": len(failed_modules),
            "canonical_source_count": len(source_owners),
            "policy_error_count": len(policy_errors),
        },
        "policy_errors": policy_errors,
        "modules": module_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Validate canonical Blueprint module registry resolution and source coverage.")
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_manifest(
        Path(args.manifest),
        repo_root=Path(args.repo_root).resolve(),
    )
    rendered = yaml.safe_dump(
        report,
        sort_keys=False,
        allow_unicode=True,
        width=112,
    )

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0 if report["metadata"]["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
