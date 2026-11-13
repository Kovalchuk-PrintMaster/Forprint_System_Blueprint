#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA = "repository_knowledge_snapshot_comparison_gate_v0_1"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def tracked(repo_root: Path, relative: str) -> bool:
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


def contains_reference(node: Any, expected: str) -> bool:
    expected_name = Path(expected).name

    if isinstance(node, str):
        return node == expected or node.endswith(expected_name)

    if isinstance(node, dict):
        return any(contains_reference(value, expected) for value in node.values())

    if isinstance(node, list):
        return any(contains_reference(value, expected) for value in node)

    return False


def command_for_cli(
    *,
    python_executable: str,
    cli_path: Path,
    previous: Path,
    current: Path,
    output: Path,
) -> list[str]:
    help_result = subprocess.run(
        [python_executable, str(cli_path), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    if help_result.returncode != 0:
        raise ValueError("Could not inspect snapshot comparison CLI interface")

    help_text = help_result.stdout + help_result.stderr
    option_pairs = (
        ("--previous", "--current"),
        ("--baseline", "--current"),
        ("--before", "--after"),
        ("--old", "--new"),
        ("--source", "--target"),
    )

    for previous_option, current_option in option_pairs:
        if previous_option in help_text and current_option in help_text and "--output" in help_text:
            return [
                python_executable,
                str(cli_path),
                previous_option,
                str(previous),
                current_option,
                str(current),
                "--output",
                str(output),
            ]

    raise ValueError(
        "Unsupported snapshot comparison CLI interface. "
        "Expected one recognized previous/current option pair."
    )


def validate_manifest(
    manifest_path: Path,
    *,
    repo_root: Path,
    execute_cli: bool,
    python_executable: str,
    work_dir: Path,
) -> dict[str, Any]:
    manifest = load_yaml(manifest_path)
    policy_errors: list[str] = []
    comparison_results: list[dict[str, Any]] = []

    if manifest.get("schema_version") != EXPECTED_SCHEMA:
        policy_errors.append("schema_version mismatch")

    rollout = manifest.get("external_rollout")

    if not isinstance(rollout, dict) or rollout.get("state") != "gated":
        policy_errors.append("external rollout must remain gated")

    cli_relative = manifest.get("comparison_cli")

    if not isinstance(cli_relative, str):
        policy_errors.append("comparison_cli is missing")
        cli_relative = ""

    cli_path = repo_root / cli_relative

    if not cli_path.is_file():
        policy_errors.append("comparison CLI is missing")

    comparisons = manifest.get("comparisons")

    if not isinstance(comparisons, list) or not comparisons:
        policy_errors.append("comparisons must be non-empty")
        comparisons = []

    comparison_ids: list[str] = []

    for item in comparisons:
        errors: list[str] = []

        if not isinstance(item, dict):
            comparison_results.append(
                {
                    "comparison_id": None,
                    "status": "FAILED",
                    "errors": ["comparison must be a mapping"],
                }
            )
            continue

        comparison_id = item.get("comparison_id")
        previous_relative = item.get("previous")
        current_relative = item.get("current")
        previous_sha = item.get("previous_sha256")
        current_sha = item.get("current_sha256")

        if not isinstance(comparison_id, str):
            errors.append("comparison_id is missing")
        else:
            comparison_ids.append(comparison_id)

        if not isinstance(previous_relative, str):
            errors.append("previous path is missing")
            previous_relative = ""

        if not isinstance(current_relative, str):
            errors.append("current path is missing")
            current_relative = ""

        previous_path = repo_root / previous_relative
        current_path = repo_root / current_relative

        for label, relative, path in (
            ("previous", previous_relative, previous_path),
            ("current", current_relative, current_path),
        ):
            if not path.is_file():
                errors.append(f"{label} snapshot missing: {relative}")
            elif not tracked(repo_root, relative):
                errors.append(f"{label} snapshot is not Git tracked: {relative}")

        if previous_path.is_file():
            actual_previous_sha = sha256(previous_path)

            if previous_sha != actual_previous_sha:
                errors.append("previous snapshot SHA-256 drift")

        if current_path.is_file():
            actual_current_sha = sha256(current_path)

            if current_sha != actual_current_sha:
                errors.append("current snapshot SHA-256 drift")

            current_data = load_yaml(current_path)

            if not contains_reference(
                current_data,
                previous_relative,
            ):
                errors.append("current snapshot does not reference previous snapshot")

        cli_output = None
        cli_exit_code = None

        if execute_cli and not errors:
            work_dir.mkdir(parents=True, exist_ok=True)
            cli_output = work_dir / f"{comparison_id}.yaml"

            try:
                command = command_for_cli(
                    python_executable=python_executable,
                    cli_path=cli_path,
                    previous=previous_path,
                    current=current_path,
                    output=cli_output,
                )
            except ValueError as exc:
                errors.append(str(exc))
            else:
                result = subprocess.run(
                    command,
                    cwd=repo_root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                cli_exit_code = result.returncode

                if result.returncode != 0:
                    errors.append(
                        "snapshot comparison CLI failed: "
                        + (result.stderr.strip() or result.stdout.strip() or "no diagnostic")
                    )
                elif not cli_output.is_file():
                    errors.append("snapshot comparison CLI produced no output")

        comparison_results.append(
            {
                "comparison_id": comparison_id,
                "artifact_type": item.get("artifact_type"),
                "previous": previous_relative,
                "current": current_relative,
                "accepted_change_count": item.get("accepted_change_count"),
                "cli_exit_code": cli_exit_code,
                "cli_output": (str(cli_output) if cli_output is not None else None),
                "status": ("PASSED" if not errors else "FAILED"),
                "errors": errors,
            }
        )

    duplicates = sorted(
        {
            comparison_id
            for comparison_id in comparison_ids
            if comparison_ids.count(comparison_id) > 1
        }
    )

    if duplicates:
        policy_errors.append("duplicate comparison IDs: " + ", ".join(duplicates))

    failed = [result for result in comparison_results if result.get("status") != "PASSED"]
    passed = not policy_errors and not failed

    return {
        "schema_version": ("repository_knowledge_snapshot_comparison_gate_report_v0_1"),
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
            "execute_cli": execute_cli,
        },
        "summary": {
            "comparison_count": len(comparison_results),
            "passed_comparisons": (len(comparison_results) - len(failed)),
            "failed_comparisons": len(failed),
            "policy_error_count": len(policy_errors),
            "accepted_change_count_total": sum(
                int(result.get("accepted_change_count") or 0) for result in comparison_results
            ),
        },
        "policy_errors": policy_errors,
        "comparisons": comparison_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate_manifest(
        Path(args.manifest),
        repo_root=Path(args.repo_root).resolve(),
        execute_cli=True,
        python_executable=sys.executable,
        work_dir=Path(args.work_dir),
    )
    Path(args.output).write_text(
        yaml.safe_dump(
            report,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    return 0 if report["metadata"]["result"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
