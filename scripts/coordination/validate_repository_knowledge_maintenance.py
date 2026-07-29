#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import yaml

EXPECTED_SCHEMA = "repository_knowledge_inventory_maintenance_v0_1"


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid YAML {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def parse_snapshot_date(path: Path) -> date:
    prefix = path.name[:10]

    try:
        return date.fromisoformat(prefix)
    except ValueError as exc:
        raise ValueError(f"Snapshot filename has no YYYY-MM-DD prefix: {path}") from exc


def extract_previous_snapshot(document: dict[str, Any]) -> str | None:
    snapshot = document.get("snapshot")

    if not isinstance(snapshot, dict):
        return None

    value = snapshot.get("previous_snapshot")

    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


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


def validate_family(
    family: dict[str, Any],
    *,
    repo_root: Path,
    as_of: date,
    require_tracked: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    family_id = family.get("family_id")
    previous = family.get("previous")
    current = family.get("current")
    maximum_age_days = family.get("maximum_age_days")
    maximum_interval_days = family.get("maximum_interval_days")

    if not isinstance(family_id, str) or not family_id:
        errors.append("family_id is required")

    for field_name, value in (
        ("previous", previous),
        ("current", current),
    ):
        if not isinstance(value, str) or not value:
            errors.append(f"{field_name} path is required")

    if not isinstance(maximum_age_days, int) or maximum_age_days < 0:
        errors.append("maximum_age_days must be a non-negative integer")

    if not isinstance(maximum_interval_days, int) or maximum_interval_days < 0:
        errors.append("maximum_interval_days must be a non-negative integer")

    if errors:
        return {
            "family_id": family_id,
            "status": "FAILED",
            "errors": errors,
            "warnings": warnings,
        }

    previous_path = repo_root / previous
    current_path = repo_root / current

    if not previous_path.is_file():
        errors.append(f"previous snapshot missing: {previous}")

    if not current_path.is_file():
        errors.append(f"current snapshot missing: {current}")

    if require_tracked:
        if not is_git_tracked(repo_root, previous):
            errors.append(f"previous snapshot is not tracked: {previous}")

        if not is_git_tracked(repo_root, current):
            errors.append(f"current snapshot is not tracked: {current}")

    previous_date: date | None = None
    current_date: date | None = None

    try:
        previous_date = parse_snapshot_date(previous_path)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        current_date = parse_snapshot_date(current_path)
    except ValueError as exc:
        errors.append(str(exc))

    if previous_date is not None and current_date is not None:
        if current_date <= previous_date:
            errors.append("current snapshot date must be later than previous")

        interval_days = (current_date - previous_date).days

        if interval_days > maximum_interval_days:
            errors.append(
                f"snapshot interval exceeds maximum: {interval_days} > {maximum_interval_days}"
            )

        age_days = (as_of - current_date).days

        if age_days < 0:
            errors.append("current snapshot date is later than as-of date")
        elif age_days > maximum_age_days:
            errors.append(f"current snapshot is stale: {age_days} > {maximum_age_days} days")
    else:
        interval_days = None
        age_days = None

    previous_link = None

    if current_path.is_file():
        try:
            current_document = load_yaml(current_path)
            previous_link = extract_previous_snapshot(current_document)
        except ValueError as exc:
            errors.append(str(exc))

    if previous_link is None:
        errors.append("current snapshot has no snapshot.previous_snapshot link")
    elif previous_link != previous:
        errors.append(f"current snapshot previous link mismatch: {previous_link!r} != {previous!r}")

    return {
        "family_id": family_id,
        "artifact_type": family.get("artifact_type"),
        "owner": family.get("owner"),
        "status": "PASSED" if not errors else "FAILED",
        "previous": previous,
        "current": current,
        "previous_snapshot_link": previous_link,
        "age_days": age_days,
        "interval_days": interval_days,
        "errors": errors,
        "warnings": warnings,
    }


def validate_config(
    config_path: Path,
    *,
    repo_root: Path,
    as_of: date,
) -> dict[str, Any]:
    config = load_yaml(config_path)
    errors: list[str] = []

    if config.get("schema_version") != EXPECTED_SCHEMA:
        errors.append("maintenance config schema_version mismatch")

    policy = config.get("policy")

    if not isinstance(policy, dict):
        errors.append("policy section is missing")
        policy = {}

    require_tracked = policy.get("require_git_tracked_snapshots") is True
    families = config.get("artifact_families")

    if not isinstance(families, list) or not families:
        errors.append("artifact_families must be a non-empty list")
        families = []

    family_results = [
        validate_family(
            family,
            repo_root=repo_root,
            as_of=as_of,
            require_tracked=require_tracked,
        )
        for family in families
        if isinstance(family, dict)
    ]

    family_failures = [result for result in family_results if result.get("status") != "PASSED"]

    external_rollout = config.get("external_rollout")

    if not isinstance(external_rollout, dict):
        errors.append("external_rollout section is missing")
    else:
        if external_rollout.get("state") != "gated":
            errors.append(
                "external rollout must remain gated during Blueprint inventory acceptance"
            )

        release_conditions = external_rollout.get("release_conditions")

        if not isinstance(release_conditions, list) or not release_conditions:
            errors.append("external rollout release_conditions are required")

    passed = not errors and not family_failures

    return {
        "schema_version": ("repository_knowledge_inventory_maintenance_report_v0_1"),
        "metadata": {
            "config": str(config_path),
            "repo_root": str(repo_root),
            "as_of": as_of.isoformat(),
            "result": "PASSED" if passed else "FAILED",
        },
        "summary": {
            "family_count": len(family_results),
            "passed_families": sum(result.get("status") == "PASSED" for result in family_results),
            "failed_families": len(family_failures),
            "policy_errors": len(errors),
            "external_rollout_state": (
                external_rollout.get("state") if isinstance(external_rollout, dict) else None
            ),
        },
        "policy_errors": errors,
        "families": family_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate repository-knowledge snapshot freshness, lineage and rollout gating."
        )
    )
    parser.add_argument("--config", required=True)
    parser.add_argument(
        "--repo-root",
        default=".",
    )
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    as_of = date.fromisoformat(args.as_of)
    report = validate_config(
        Path(args.config),
        repo_root=Path(args.repo_root).resolve(),
        as_of=as_of,
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
