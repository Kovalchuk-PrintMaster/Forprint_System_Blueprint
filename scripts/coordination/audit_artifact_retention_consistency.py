#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

EXPECTED_POLICY_SCHEMA = "artifact_authority_policy_v0_1"
EXPECTED_GATE_SCHEMA = "repository_knowledge_snapshot_comparison_gate_v0_1"
DATE_VERSION_RE = re.compile(r"^\d{4}-\d{2}-\d{2}__.+_v\d+_\d+\.ya?ml$")


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
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def history_commit_count(
    repo_root: Path,
    relative: str,
) -> int:
    result = subprocess.run(
        ["git", "log", "--format=%H", "--", relative],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        return 0

    return len([line for line in result.stdout.splitlines() if line.strip()])


def matches_any(
    relative: str,
    patterns: list[str],
) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def validate_class(
    item: dict[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    class_id = item.get("class_id")
    authority = item.get("authority_class")
    representatives = item.get("representative_paths")
    patterns = item.get("path_patterns")
    tracked_required = item.get("tracked_required")

    if not isinstance(class_id, str) or not class_id:
        errors.append("class_id is missing")

    if not isinstance(authority, str) or not authority:
        errors.append("authority_class is missing")

    if not isinstance(patterns, list) or not patterns:
        patterns = []
        errors.append("path_patterns are missing")

    if not isinstance(representatives, list) or not representatives:
        representatives = []
        errors.append("representative_paths are missing")

    representative_results: list[dict[str, Any]] = []

    for relative in representatives:
        item_errors: list[str] = []

        if not isinstance(relative, str):
            representative_results.append(
                {
                    "path": None,
                    "status": "FAILED",
                    "errors": ["representative path is invalid"],
                }
            )
            continue

        path = repo_root / relative

        if not path.is_file():
            item_errors.append("representative file is missing")

        if tracked_required is True and not tracked(
            repo_root,
            relative,
        ):
            item_errors.append("representative is not Git tracked")

        if patterns and not matches_any(relative, patterns):
            item_errors.append("representative does not match class path patterns")

        if authority == "canonical_control":
            if relative.startswith(("reports/", "tmp/")):
                item_errors.append("canonical control cannot be generated/runtime output")

        if authority == "generated_rebuildable_view":
            if not relative.startswith("reports/"):
                item_errors.append("generated view representative must be under reports/")

            if tracked_required is not False:
                item_errors.append("generated view must not require Git tracking")

            if not item.get("generator"):
                item_errors.append("generated view class needs generator")

        if authority == "decision_evidence":
            if not relative.startswith(
                (
                    "coordination/internal_work/",
                    "coordination/self_coordination/completion_packets/",
                )
            ):
                item_errors.append(
                    "decision evidence representative is outside approved evidence paths"
                )

        if authority == "executable_validation":
            if path.suffix != ".py":
                item_errors.append("executable validation representative must be Python")

        representative_results.append(
            {
                "path": relative,
                "tracked": tracked(repo_root, relative),
                "status": ("PASSED" if not item_errors else "FAILED"),
                "errors": item_errors,
            }
        )

    failed_representatives = [
        result for result in representative_results if result.get("status") != "PASSED"
    ]

    return {
        "class_id": class_id,
        "authority_class": authority,
        "representative_count": len(representative_results),
        "failed_representatives": len(failed_representatives),
        "status": ("PASSED" if not errors and not failed_representatives else "FAILED"),
        "errors": errors,
        "representatives": representative_results,
    }


def validate_snapshot_pair(
    item: dict[str, Any],
    *,
    repo_root: Path,
    immutable_patterns: list[str],
) -> dict[str, Any]:
    errors: list[str] = []
    review_items: list[str] = []
    comparison_id = item.get("comparison_id")
    previous = item.get("previous")
    current = item.get("current")

    if not isinstance(comparison_id, str):
        errors.append("comparison_id is missing")

    if not isinstance(previous, str):
        errors.append("previous path is missing")
        previous = ""

    if not isinstance(current, str):
        errors.append("current path is missing")
        current = ""

    path_results: list[dict[str, Any]] = []

    for role, relative, expected_hash in (
        ("previous", previous, item.get("previous_sha256")),
        ("current", current, item.get("current_sha256")),
    ):
        path = repo_root / relative
        path_errors: list[str] = []

        if not path.is_file():
            path_errors.append("snapshot file is missing")
        else:
            if not tracked(repo_root, relative):
                path_errors.append("snapshot is not Git tracked")

            if sha256(path) != expected_hash:
                path_errors.append("snapshot SHA-256 drift")

            if not DATE_VERSION_RE.match(path.name):
                path_errors.append("snapshot filename is not dated/versioned")

            if not matches_any(relative, immutable_patterns):
                path_errors.append("snapshot is outside immutable path patterns")

        commit_count = history_commit_count(
            repo_root,
            relative,
        )

        if commit_count > 1:
            review_items.append(f"{role} snapshot has {commit_count} Git commits: {relative}")

        path_results.append(
            {
                "role": role,
                "path": relative,
                "sha256": (sha256(path) if path.is_file() else None),
                "history_commit_count": commit_count,
                "history_review_required": commit_count > 1,
                "status": ("PASSED" if not path_errors else "FAILED"),
                "errors": path_errors,
            }
        )

    if previous == current:
        errors.append("previous and current snapshot paths are identical")

    failed_paths = [result for result in path_results if result.get("status") != "PASSED"]

    return {
        "comparison_id": comparison_id,
        "artifact_type": item.get("artifact_type"),
        "accepted_change_count": item.get("accepted_change_count"),
        "status": ("PASSED" if not errors and not failed_paths else "FAILED"),
        "errors": errors,
        "review_items": review_items,
        "paths": path_results,
    }


def audit_retention(
    policy_path: Path,
    snapshot_gate_path: Path,
    source_map_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    policy = load_yaml(policy_path)
    gate = load_yaml(snapshot_gate_path)
    load_yaml(source_map_path)

    policy_errors: list[str] = []

    if policy.get("schema_version") != EXPECTED_POLICY_SCHEMA:
        policy_errors.append("artifact authority policy schema mismatch")

    if gate.get("schema_version") != EXPECTED_GATE_SCHEMA:
        policy_errors.append("snapshot gate schema mismatch")

    governance = policy.get("governance")

    if not isinstance(governance, dict):
        governance = {}
        policy_errors.append("policy governance is missing")

    for flag in (
        "unknown_authority_is_blocking",
        "historical_snapshots_are_immutable",
        "generated_views_are_not_authority",
        "decision_evidence_must_remain_traceable",
        "cross_repository_writes_forbidden",
    ):
        if governance.get(flag) is not True:
            policy_errors.append(f"governance flag must be true: {flag}")

    rollout = policy.get("external_rollout")

    if not isinstance(rollout, dict) or rollout.get("state") != "gated":
        policy_errors.append("external rollout must remain gated")

    classes = policy.get("artifact_classes")

    if not isinstance(classes, list):
        classes = []
        policy_errors.append("artifact classes are missing")

    class_results = [
        validate_class(item, repo_root=repo_root) for item in classes if isinstance(item, dict)
    ]
    failed_classes = [result for result in class_results if result.get("status") != "PASSED"]

    immutable_classes = [
        item
        for item in classes
        if isinstance(item, dict) and item.get("authority_class") == "immutable_snapshot"
    ]

    if len(immutable_classes) != 1:
        policy_errors.append("exactly one immutable snapshot class is required")
        immutable_patterns: list[str] = []
    else:
        patterns = immutable_classes[0].get("path_patterns")
        immutable_patterns = (
            [str(pattern) for pattern in patterns if isinstance(pattern, str)]
            if isinstance(patterns, list)
            else []
        )

    comparisons = gate.get("comparisons")

    if not isinstance(comparisons, list):
        comparisons = []
        policy_errors.append("snapshot comparisons are missing")

    snapshot_results = [
        validate_snapshot_pair(
            item,
            repo_root=repo_root,
            immutable_patterns=immutable_patterns,
        )
        for item in comparisons
        if isinstance(item, dict)
    ]
    failed_snapshots = [result for result in snapshot_results if result.get("status") != "PASSED"]
    history_review_items = [
        review_item for result in snapshot_results for review_item in result.get("review_items", [])
    ]

    generated_classes = [
        item
        for item in classes
        if isinstance(item, dict) and item.get("authority_class") == "generated_rebuildable_view"
    ]

    generated_paths = {
        str(relative)
        for item in generated_classes
        for relative in item.get("representative_paths", [])
        if isinstance(relative, str)
    }
    snapshot_paths = {
        str(item.get(key))
        for item in comparisons
        if isinstance(item, dict)
        for key in ("previous", "current")
        if isinstance(item.get(key), str)
    }
    generated_snapshot_overlap = sorted(generated_paths.intersection(snapshot_paths))

    if generated_snapshot_overlap:
        policy_errors.append(
            "generated reports cannot be immutable snapshots: "
            + ", ".join(generated_snapshot_overlap)
        )

    passed = not policy_errors and not failed_classes and not failed_snapshots

    return {
        "schema_version": ("artifact_retention_consistency_audit_report_v0_1"),
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
            "source_policy": str(policy_path),
            "source_snapshot_gate": str(snapshot_gate_path),
            "source_authority_map": str(source_map_path),
        },
        "summary": {
            "artifact_class_count": len(class_results),
            "failed_artifact_classes": len(failed_classes),
            "snapshot_pair_count": len(snapshot_results),
            "protected_snapshot_file_count": (len(snapshot_results) * 2),
            "failed_snapshot_pairs": len(failed_snapshots),
            "history_review_item_count": len(history_review_items),
            "generated_snapshot_overlap_count": len(generated_snapshot_overlap),
            "policy_error_count": len(policy_errors),
        },
        "policy_errors": policy_errors,
        "history_review_items": history_review_items,
        "artifact_classes": class_results,
        "snapshot_pairs": snapshot_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    parser.add_argument("--snapshot-gate", required=True)
    parser.add_argument("--source-map", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = audit_retention(
        Path(args.policy),
        Path(args.snapshot_gate),
        Path(args.source_map),
        repo_root=Path(args.repo_root).resolve(),
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
