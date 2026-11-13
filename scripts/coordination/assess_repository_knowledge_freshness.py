#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "repository_knowledge_snapshot_comparison_gate_v0_1"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            "git " + " ".join(args) + " failed: " + (result.stderr.strip() or result.stdout.strip())
        )
    return result.stdout.strip()


def classify(path: str) -> str:
    if path == "Makefile" or path.startswith(("scripts/", "tests/")):
        return "executable_control"
    if path.startswith("coordination/repository_knowledge/"):
        return "repository_knowledge"
    if path.startswith("coordination/self_coordination/"):
        return "self_coordination"
    if path.startswith("coordination/internal_work/"):
        return "decision_evidence"
    if path.startswith(("coordination/roadmaps/", "coordination/outgoing_prompts/")):
        return "managed_module_control"
    if path.startswith("reports/"):
        return "generated_view"
    return "other"


def assess_item(
    item: dict[str, Any],
    *,
    repo: Path,
    head: str,
) -> dict[str, Any]:
    errors: list[str] = []
    current = item.get("current")
    expected_hash = item.get("current_sha256")

    if not isinstance(current, str) or not current:
        return {
            "comparison_id": item.get("comparison_id"),
            "status": "FAILED",
            "freshness": "FAILED",
            "errors": ["current snapshot path is missing"],
        }

    path = repo / current
    actual_hash = sha256(path) if path.is_file() else None

    if not path.is_file():
        errors.append("current snapshot is missing")
        baseline = None
        changes: list[str] = []
    else:
        if actual_hash != expected_hash:
            errors.append("current snapshot SHA-256 drift")

        try:
            baseline = git(repo, "log", "-1", "--format=%H", "--", current)
        except ValueError as exc:
            errors.append(str(exc))
            baseline = None

        if not baseline:
            errors.append("snapshot baseline commit is missing")
            changes = []
        else:
            output = git(repo, "diff", "--name-only", f"{baseline}..{head}")
            changes = sorted({line.strip() for line in output.splitlines() if line.strip()})

    classes = Counter(classify(relative) for relative in changes)
    relevant = [
        relative for relative in changes if classify(relative) not in {"generated_view", "other"}
    ]

    if errors:
        freshness = "FAILED"
    elif changes:
        freshness = "BOUNDED_REFRESH_REQUIRED"
    else:
        freshness = "FRESH"

    return {
        "comparison_id": item.get("comparison_id"),
        "artifact_type": item.get("artifact_type"),
        "current_snapshot": current,
        "expected_sha256": expected_hash,
        "actual_sha256": actual_hash,
        "baseline_commit": baseline,
        "head_commit": head,
        "changed_path_count": len(changes),
        "knowledge_relevant_changed_path_count": len(relevant),
        "change_class_counts": dict(sorted(classes.items())),
        "changed_paths": changes,
        "knowledge_relevant_changed_paths": relevant,
        "freshness": freshness,
        "status": "PASSED" if not errors else "FAILED",
        "errors": errors,
    }


def assess(
    manifest_path: Path,
    *,
    repo: Path,
) -> dict[str, Any]:
    manifest = load_yaml(manifest_path)
    policy_errors: list[str] = []

    if manifest.get("schema_version") != SCHEMA:
        policy_errors.append("snapshot gate schema mismatch")

    rollout = manifest.get("external_rollout")
    if not isinstance(rollout, dict) or rollout.get("state") != "gated":
        policy_errors.append("external rollout must remain gated")

    comparisons = manifest.get("comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        policy_errors.append("snapshot comparisons are missing")
        comparisons = []

    head = git(repo, "rev-parse", "HEAD")
    snapshots = [
        assess_item(item, repo=repo, head=head) for item in comparisons if isinstance(item, dict)
    ]
    failed = [item for item in snapshots if item["status"] != "PASSED"]
    fresh = [item for item in snapshots if item["freshness"] == "FRESH"]
    bounded = [item for item in snapshots if item["freshness"] == "BOUNDED_REFRESH_REQUIRED"]

    changed_union = sorted({path for item in snapshots for path in item.get("changed_paths", [])})
    relevant_union = sorted(
        {path for item in snapshots for path in item.get("knowledge_relevant_changed_paths", [])}
    )
    classes = Counter(classify(path) for path in changed_union)

    if policy_errors or failed:
        result = "FAILED"
        decision = "BLOCK_RCI_ENRICHMENT"
    elif bounded:
        result = "PASSED"
        decision = "PROCEED_WITH_BOUNDED_REFRESH"
    else:
        result = "PASSED"
        decision = "PROCEED_AS_FRESH"

    return {
        "schema_version": "repository_knowledge_freshness_report_v0_1",
        "metadata": {
            "result": result,
            "head_commit": head,
            "external_rollout_state": "gated",
        },
        "summary": {
            "snapshot_count": len(snapshots),
            "fresh_snapshot_count": len(fresh),
            "bounded_refresh_snapshot_count": len(bounded),
            "failed_snapshot_count": len(failed),
            "changed_path_union_count": len(changed_union),
            "knowledge_relevant_changed_path_union_count": len(relevant_union),
            "policy_error_count": len(policy_errors),
            "release_decision": decision,
        },
        "policy_errors": policy_errors,
        "change_class_counts": dict(sorted(classes.items())),
        "changed_path_union": changed_union,
        "knowledge_relevant_changed_path_union": relevant_union,
        "snapshots": snapshots,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = assess(
        Path(args.manifest),
        repo=Path(args.repo_root).resolve(),
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
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
