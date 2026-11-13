#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml

ALLOWED_CLASSES = {
    "canonical_control",
    "immutable_snapshot",
    "decision_evidence",
    "generated_rebuildable_view",
    "executable_validation",
}
ALLOWED_MUTATIONS = {
    "owner_workflow_only",
    "append_new_version_only",
    "controlled_evidence_update",
    "generator_only",
    "reviewed_code_change",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def tracked(root: Path, relative: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def validate_policy(
    policy_path: Path,
    *,
    repo_root: Path,
) -> dict[str, Any]:
    policy = load_yaml(policy_path)
    errors: list[str] = []
    class_results: list[dict[str, Any]] = []
    target_results: list[dict[str, Any]] = []

    if policy.get("schema_version") != ("artifact_authority_policy_v0_1"):
        errors.append("schema mismatch")

    governance = policy.get("governance")

    if not isinstance(governance, dict):
        governance = {}
        errors.append("governance missing")

    for flag in (
        "unknown_authority_is_blocking",
        "historical_snapshots_are_immutable",
        "generated_views_are_not_authority",
        "cross_repository_writes_forbidden",
    ):
        if governance.get(flag) is not True:
            errors.append(f"governance flag must be true: {flag}")

    rollout = policy.get("external_rollout")

    if not isinstance(rollout, dict) or rollout.get("state") != "gated":
        errors.append("external rollout must remain gated")

    classes = policy.get("artifact_classes")

    if not isinstance(classes, list) or not classes:
        classes = []
        errors.append("artifact classes missing")

    class_ids: list[str] = []

    for item in classes:
        item_errors: list[str] = []

        if not isinstance(item, dict):
            class_results.append(
                {
                    "class_id": None,
                    "status": "FAILED",
                    "errors": ["class must be a mapping"],
                }
            )
            continue

        class_id = item.get("class_id")
        authority = item.get("authority_class")
        mutation = item.get("mutation_policy")
        representatives = item.get("representative_paths")

        if not isinstance(class_id, str) or not class_id:
            item_errors.append("class_id missing")
        else:
            class_ids.append(class_id)

        if authority not in ALLOWED_CLASSES:
            item_errors.append("unsupported authority class")

        if mutation not in ALLOWED_MUTATIONS:
            item_errors.append("unsupported mutation policy")

        if not item.get("retention"):
            item_errors.append("retention missing")

        if not isinstance(representatives, list) or not representatives:
            representatives = []
            item_errors.append("representative paths missing")

        for relative in representatives:
            if not isinstance(relative, str):
                item_errors.append("invalid representative path")
                continue

            if not (repo_root / relative).is_file():
                item_errors.append(f"representative missing: {relative}")

            if item.get("tracked_required") is True and not tracked(
                repo_root,
                relative,
            ):
                item_errors.append(f"representative not tracked: {relative}")

        if authority == "generated_rebuildable_view" and not item.get("generator"):
            item_errors.append("generated class needs generator")

        class_results.append(
            {
                "class_id": class_id,
                "status": ("PASSED" if not item_errors else "FAILED"),
                "errors": item_errors,
            }
        )

    duplicates = sorted({class_id for class_id in class_ids if class_ids.count(class_id) > 1})

    if duplicates:
        errors.append("duplicate class IDs: " + ", ".join(duplicates))

    targets = policy.get("enforcement_targets")

    if not isinstance(targets, list) or not targets:
        targets = []
        errors.append("enforcement targets missing")

    for item in targets:
        item_errors: list[str] = []

        if not isinstance(item, dict):
            target_results.append(
                {
                    "path": None,
                    "status": "FAILED",
                    "errors": ["target must be a mapping"],
                }
            )
            continue

        relative = item.get("path")

        if not isinstance(relative, str):
            item_errors.append("target path missing")
        else:
            if not (repo_root / relative).is_file():
                item_errors.append(f"target missing: {relative}")

            if not tracked(repo_root, relative):
                item_errors.append(f"target not tracked: {relative}")

        if item.get("role") not in {"generator", "validator"}:
            item_errors.append("target role invalid")

        if not item.get("enforced_rules"):
            item_errors.append("enforced rules missing")

        target_results.append(
            {
                "path": relative,
                "status": ("PASSED" if not item_errors else "FAILED"),
                "errors": item_errors,
            }
        )

    failed_classes = [item for item in class_results if item.get("status") != "PASSED"]
    failed_targets = [item for item in target_results if item.get("status") != "PASSED"]
    passed = not errors and not failed_classes and not failed_targets

    return {
        "schema_version": ("artifact_authority_policy_report_v0_1"),
        "metadata": {"result": "PASSED" if passed else "FAILED"},
        "summary": {
            "artifact_classes": len(class_results),
            "failed_classes": len(failed_classes),
            "enforcement_targets": len(target_results),
            "failed_targets": len(failed_targets),
            "policy_errors": len(errors),
        },
        "errors": errors,
        "class_results": class_results,
        "target_results": target_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate_policy(
        Path(args.policy),
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
