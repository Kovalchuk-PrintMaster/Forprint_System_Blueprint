#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml

RCI_SECTION = "semantic_enrichment_v0_1"
REDM_SECTION = "dependency_enrichment_v0_1"
MODULE_ID = "forprint_system_blueprint"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_closure(
    *,
    rci_path: Path,
    redm_path: Path,
    rci_validation_path: Path,
    redm_validation_path: Path,
    freshness_path: Path,
    unknowns_path: Path,
    module_id: str,
) -> dict[str, Any]:
    errors: list[str] = []

    if module_id != MODULE_ID:
        errors.append(f"module mismatch: expected {MODULE_ID}, found {module_id}")

    rci = load_yaml(rci_path)
    redm = load_yaml(redm_path)
    rci_validation = load_yaml(rci_validation_path)
    redm_validation = load_yaml(redm_validation_path)
    freshness = load_yaml(freshness_path)
    load_yaml(unknowns_path)

    rci_section = rci.get(RCI_SECTION)
    redm_section = redm.get(REDM_SECTION)

    if not isinstance(rci_section, dict):
        errors.append("RCI semantic enrichment section is missing")
        rci_section = {}

    if not isinstance(redm_section, dict):
        errors.append("REDM dependency enrichment section is missing")
        redm_section = {}

    if rci_section.get("status") != "CANDIDATE":
        errors.append("RCI v0.4 must remain CANDIDATE")

    if redm_section.get("status") != "CANDIDATE":
        errors.append("REDM v0.4 must remain CANDIDATE")

    if rci_validation.get("metadata", {}).get("result") != "PASSED":
        errors.append("RCI enrichment validation is not PASSED")

    if redm_validation.get("metadata", {}).get("result") != "PASSED":
        errors.append("REDM enrichment validation is not PASSED")

    rci_coverage = rci_section.get("coverage_lower_bounds")
    redm_coverage = redm_section.get("coverage_lower_bounds")

    if not isinstance(rci_coverage, dict):
        errors.append("RCI coverage lower bounds are missing")
        rci_coverage = {}

    if not isinstance(redm_coverage, dict):
        errors.append("REDM coverage lower bounds are missing")
        redm_coverage = {}

    expected_rci = {
        "tracked_files": 726,
        "reviewed_files": 80,
        "purpose_evidenced": 79,
        "dependencies_mapped": 80,
        "fully_verified": 79,
    }
    expected_redm = {
        "tracked_files": 726,
        "reviewed_files": 80,
        "dependencies_mapped": 80,
        "fully_verified": 79,
    }

    for key, expected in expected_rci.items():
        actual = rci_coverage.get(key)

        if actual != expected:
            errors.append(f"RCI metric mismatch for {key}: expected {expected}, found {actual}")

    for key, expected in expected_redm.items():
        actual = redm_coverage.get(key)

        if actual != expected:
            errors.append(f"REDM metric mismatch for {key}: expected {expected}, found {actual}")

    for key in ("tracked_files", "reviewed_files"):
        if rci_coverage.get(key) != redm_coverage.get(key):
            errors.append(f"RCI and REDM scopes diverge for {key}")

    rci_unresolved = rci_section.get("unresolved_scope")
    redm_unresolved = redm_section.get("unresolved_scope")

    if not isinstance(rci_unresolved, dict):
        errors.append("RCI unresolved scope is missing")
        rci_unresolved = {}

    if not isinstance(redm_unresolved, dict):
        errors.append("REDM unresolved scope is missing")
        redm_unresolved = {}

    for label, unresolved in (
        ("RCI", rci_unresolved),
        ("REDM", redm_unresolved),
    ):
        if unresolved.get("unreviewed_files") != 646:
            errors.append(f"{label} unreviewed file count must remain 646")

        if unresolved.get("wave_2_records_with_unknowns") != 25:
            errors.append(f"{label} Wave 2 unknown count must remain 25")

    if redm_unresolved.get("dependency_edges_not_inferred") is not True:
        errors.append("REDM unknown dependency edges were inferred")

    rci_policy = rci_section.get("evidence_policy")
    redm_policy = redm_section.get("evidence_policy")

    if not isinstance(rci_policy, dict):
        errors.append("RCI evidence policy is missing")
        rci_policy = {}

    if not isinstance(redm_policy, dict):
        errors.append("REDM evidence policy is missing")
        redm_policy = {}

    for key in (
        "only_verified_claims",
        "unknowns_not_silently_resolved",
        "source_snapshot_immutable",
        "external_rollout_gated",
    ):
        if rci_policy.get(key) is not True:
            errors.append(f"RCI evidence policy flag must be true: {key}")

    for key in (
        "only_verified_edges",
        "unknown_edges_not_silently_resolved",
        "source_snapshot_immutable",
        "capability_context_traceable",
        "external_rollout_gated",
    ):
        if redm_policy.get(key) is not True:
            errors.append(f"REDM evidence policy flag must be true: {key}")

    freshness_summary = freshness.get("summary")
    freshness_metadata = freshness.get("metadata")

    if not isinstance(freshness_summary, dict):
        errors.append("freshness summary is missing")
        freshness_summary = {}

    if not isinstance(freshness_metadata, dict):
        errors.append("freshness metadata is missing")
        freshness_metadata = {}

    freshness_decision = freshness_summary.get("release_decision")

    if freshness_decision not in {
        "PROCEED_AS_FRESH",
        "PROCEED_WITH_BOUNDED_REFRESH",
    }:
        errors.append("repository knowledge freshness is not releasable")

    if freshness_metadata.get("external_rollout_state") != "gated":
        errors.append("external rollout must remain gated")

    tracked = 726
    reviewed = 80
    purpose = 79
    dependencies = 80
    verified = 79

    repository_lower_bound = min(
        reviewed / tracked,
        purpose / tracked,
        dependencies / tracked,
        verified / tracked,
    )
    reviewed_quality_lower_bound = min(
        purpose / reviewed,
        dependencies / reviewed,
        verified / reviewed,
    )

    if errors:
        closure_state = "FAILED"
        release_decision = "BLOCK_RECONCILIATION"
    else:
        closure_state = "GREEN_WITH_EXPLICIT_DEFERRALS"
        release_decision = "PROCEED_TO_REPOSITORY_KNOWLEDGE_RECONCILIATION_WITH_EXPLICIT_DEFERRALS"

    return {
        "schema_version": "semantic_coverage_closure_report_v0_1",
        "metadata": {
            "result": "PASSED" if not errors else "FAILED",
            "module_id": module_id,
            "external_rollout_state": "gated",
        },
        "summary": {
            "error_count": len(errors),
            "closure_state": closure_state,
            "release_decision": release_decision,
            "tracked_files": tracked,
            "reviewed_files": reviewed,
            "purpose_evidenced": purpose,
            "dependencies_mapped": dependencies,
            "fully_verified": verified,
            "unreviewed_files": tracked - reviewed,
            "wave_2_records_with_unknowns": 25,
            "repository_semantic_lower_bound": (repository_lower_bound),
            "reviewed_quality_lower_bound": (reviewed_quality_lower_bound),
            "full_semantic_coverage_claim_allowed": False,
        },
        "candidate_integrity": {
            "rci_candidate": str(rci_path),
            "rci_sha256": sha256(rci_path),
            "rci_validation": "PASSED",
            "redm_candidate": str(redm_path),
            "redm_sha256": sha256(redm_path),
            "redm_validation": "PASSED",
        },
        "explicit_deferrals": [
            {
                "deferral_id": "unreviewed_repository_scope",
                "count": tracked - reviewed,
                "blocking_for_reconciliation": False,
                "must_remain_visible": True,
            },
            {
                "deferral_id": "wave_2_unknown_records",
                "count": 25,
                "blocking_for_reconciliation": False,
                "must_remain_visible": True,
            },
        ],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rci", required=True)
    parser.add_argument("--redm", required=True)
    parser.add_argument("--rci-validation", required=True)
    parser.add_argument("--redm-validation", required=True)
    parser.add_argument("--freshness", required=True)
    parser.add_argument("--unknowns", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate_closure(
        rci_path=Path(args.rci),
        redm_path=Path(args.redm),
        rci_validation_path=Path(args.rci_validation),
        redm_validation_path=Path(args.redm_validation),
        freshness_path=Path(args.freshness),
        unknowns_path=Path(args.unknowns),
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
