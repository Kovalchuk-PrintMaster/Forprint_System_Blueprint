#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml

MODULE_ID = "forprint_system_blueprint"
REQUIRED_IDS = {
    "rci_v0_4_candidate",
    "redm_v0_4_candidate",
    "coordination_direction_v0_2",
    "portfolio_direction_v0_2",
    "artifact_authority_policy",
    "module_registry_resolution",
    "semantic_unknowns_triage",
    "semantic_closure_review_record",
    "reconciliation_record",
    "rci_validation_report",
    "redm_validation_report",
    "semantic_closure_report",
    "reconciliation_report",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nested_value(
    node: dict[str, Any],
    path: list[Any],
) -> Any:
    value: Any = node

    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(str(key))

    return value


def validate_index(
    *,
    index_path: Path,
    repo_root: Path,
    module_id: str,
) -> dict[str, Any]:
    errors: list[str] = []
    index = load_yaml(index_path)

    if module_id != MODULE_ID:
        errors.append(f"module mismatch: expected {MODULE_ID}, found {module_id}")

    metadata = index.get("metadata")
    summary = index.get("summary")
    entries = index.get("evidence_entries")
    deferrals = index.get("explicit_deferrals")

    if not isinstance(metadata, dict):
        errors.append("index metadata is missing")
        metadata = {}

    if not isinstance(summary, dict):
        errors.append("index summary is missing")
        summary = {}

    if not isinstance(entries, list):
        errors.append("evidence entries are missing")
        entries = []

    if not isinstance(deferrals, list):
        errors.append("explicit deferrals are missing")
        deferrals = []

    if metadata.get("module_id") != MODULE_ID:
        errors.append("index module ID mismatch")

    if metadata.get("state") != "READY_FOR_DRY_RUN":
        errors.append("index state must be READY_FOR_DRY_RUN")

    if metadata.get("external_rollout_state") != "gated":
        errors.append("external rollout must remain gated")

    if summary.get("candidate_acceptance_performed") is not False:
        errors.append("evidence indexing must not accept candidates")

    if summary.get("release_decision") != "PROCEED_TO_INVENTORY_ACCEPTANCE_DRY_RUN":
        errors.append("dry run release decision is missing")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    passed_entries = 0
    stable_entries = 0
    runtime_entries = 0
    candidate_entries: dict[str, dict[str, Any]] = {}

    for position, raw_entry in enumerate(entries):
        if not isinstance(raw_entry, dict):
            errors.append(f"evidence entry {position} is not a mapping")
            continue

        evidence_id = raw_entry.get("evidence_id")
        relative = raw_entry.get("path")
        mode = raw_entry.get("integrity_mode")

        if not isinstance(evidence_id, str) or not evidence_id:
            errors.append(f"evidence entry {position} lacks evidence_id")
            continue

        if evidence_id in seen_ids:
            errors.append(f"duplicate evidence_id: {evidence_id}")
        seen_ids.add(evidence_id)

        if not isinstance(relative, str) or not relative:
            errors.append(f"evidence path is missing: {evidence_id}")
            continue

        if relative in seen_paths:
            errors.append(f"duplicate evidence path: {relative}")
        seen_paths.add(relative)

        path = repo_root / relative

        if not path.is_file():
            errors.append(f"evidence file is missing: {relative}")
            continue

        entry_passed = True

        if mode == "sha256":
            stable_entries += 1
            expected_hash = raw_entry.get("sha256")
            actual_hash = sha256(path)

            if expected_hash != actual_hash:
                errors.append(f"SHA-256 mismatch for {evidence_id}")
                entry_passed = False

        elif mode == "runtime_result":
            runtime_entries += 1
            report = load_yaml(path)
            result_path = raw_entry.get("result_path")
            expected_result = raw_entry.get("expected_result")

            if not isinstance(result_path, list) or not result_path:
                errors.append(f"runtime result_path is missing: {evidence_id}")
                entry_passed = False
            else:
                actual_result = nested_value(
                    report,
                    result_path,
                )

                if actual_result != expected_result:
                    errors.append(
                        f"runtime result mismatch for {evidence_id}: "
                        f"expected {expected_result!r}, "
                        f"found {actual_result!r}"
                    )
                    entry_passed = False

        else:
            errors.append(f"unsupported integrity mode for {evidence_id}: {mode!r}")
            entry_passed = False

        if raw_entry.get("authority") == "candidate":
            candidate_entries[evidence_id] = raw_entry

            candidate_data = load_yaml(path)
            section_name = (
                "semantic_enrichment_v0_1"
                if evidence_id == "rci_v0_4_candidate"
                else "dependency_enrichment_v0_1"
            )
            section = candidate_data.get(section_name)

            if not isinstance(section, dict) or section.get("status") != "CANDIDATE":
                errors.append(f"candidate status mismatch for {evidence_id}")
                entry_passed = False

        if entry_passed:
            passed_entries += 1

    missing_required = sorted(REQUIRED_IDS - seen_ids)

    if missing_required:
        errors.append(f"required evidence entries are missing: {missing_required}")

    for evidence_id in (
        "rci_v0_4_candidate",
        "redm_v0_4_candidate",
    ):
        entry = candidate_entries.get(evidence_id)

        if entry is None:
            errors.append(f"candidate evidence entry is missing: {evidence_id}")
        elif entry.get("authority") != "candidate":
            errors.append(f"candidate authority mismatch: {evidence_id}")

    visible_deferrals = {
        str(item.get("deferral_id")): item
        for item in deferrals
        if isinstance(item, dict) and item.get("must_remain_visible") is True
    }

    if (
        visible_deferrals.get(
            "unreviewed_repository_scope",
            {},
        ).get("count")
        != 646
    ):
        errors.append("646 unreviewed files are not visible")

    if (
        visible_deferrals.get(
            "wave_2_unknown_records",
            {},
        ).get("count")
        != 25
    ):
        errors.append("25 Wave 2 unknown records are not visible")

    if summary.get("evidence_entry_count") != len(entries):
        errors.append("summary evidence_entry_count mismatch")

    if summary.get("stable_hash_entry_count") != stable_entries:
        errors.append("summary stable_hash_entry_count mismatch")

    if summary.get("runtime_result_entry_count") != runtime_entries:
        errors.append("summary runtime_result_entry_count mismatch")

    passed = not errors

    return {
        "schema_version": ("inventory_acceptance_evidence_index_validation_report_v0_1"),
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
            "module_id": module_id,
            "external_rollout_state": "gated",
        },
        "summary": {
            "error_count": len(errors),
            "evidence_entry_count": len(entries),
            "passed_entry_count": passed_entries,
            "stable_hash_entry_count": stable_entries,
            "runtime_result_entry_count": runtime_entries,
            "required_entry_count": len(REQUIRED_IDS),
            "candidate_entry_count": len(candidate_entries),
            "explicit_deferral_count": len(visible_deferrals),
            "candidate_acceptance_performed": False,
            "release_decision": (
                "PROCEED_TO_INVENTORY_ACCEPTANCE_DRY_RUN"
                if passed
                else "BLOCK_INVENTORY_ACCEPTANCE_DRY_RUN"
            ),
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate_index(
        index_path=Path(args.index),
        repo_root=Path(args.repo_root).resolve(),
        module_id=args.module,
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
