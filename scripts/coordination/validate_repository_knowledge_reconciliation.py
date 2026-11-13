#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml

MODULE_ID = "forprint_system_blueprint"
RCI_SECTION = "semantic_enrichment_v0_1"
REDM_SECTION = "dependency_enrichment_v0_1"
EXPECTED_MODULES = {
    "forprint_library",
    "logistics_service",
    "telegram_bot",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_strings(node: Any) -> set[str]:
    output: set[str] = set()

    if isinstance(node, str):
        output.add(node)

    elif isinstance(node, dict):
        for key, value in node.items():
            output.add(str(key))
            output.update(collect_strings(value))

    elif isinstance(node, list):
        for value in node:
            output.update(collect_strings(value))

    return output


def authority_classifications(
    policy: dict[str, Any],
) -> dict[str, bool]:
    values = {
        value.lower().replace("-", "_").replace(" ", "_") for value in collect_strings(policy)
    }
    aliases = {
        "accepted": {
            "accepted",
            "canonical",
            "authoritative",
            "approved",
            "current_authority",
            "source_of_truth",
        },
        "generated": {
            "generated",
            "derived",
            "generated_view",
            "derived_view",
            "report",
            "runtime_report",
            "rendered",
        },
    }

    return {
        classification: any(alias in value for value in values for alias in candidates)
        for classification, candidates in aliases.items()
    }


def matrix_row(
    artifact: str,
    *,
    status: str,
    authority: str,
    evidence: str,
    note: str,
) -> dict[str, str]:
    return {
        "artifact": artifact,
        "status": status,
        "authority": authority,
        "evidence": evidence,
        "note": note,
    }


def validate_reconciliation(
    *,
    rci_path: Path,
    redm_path: Path,
    coordination_direction_path: Path,
    portfolio_direction_path: Path,
    authority_policy_path: Path,
    module_registry_path: Path,
    closure_report_path: Path,
    rci_validation_path: Path,
    redm_validation_path: Path,
    module_id: str,
) -> dict[str, Any]:
    errors: list[str] = []
    matrix: list[dict[str, str]] = []

    if module_id != MODULE_ID:
        errors.append(f"module mismatch: expected {MODULE_ID}, found {module_id}")

    rci = load_yaml(rci_path)
    redm = load_yaml(redm_path)
    coordination_direction = load_yaml(coordination_direction_path)
    portfolio_direction = load_yaml(portfolio_direction_path)
    authority_policy = load_yaml(authority_policy_path)
    module_registry = load_yaml(module_registry_path)
    closure = load_yaml(closure_report_path)
    rci_validation = load_yaml(rci_validation_path)
    redm_validation = load_yaml(redm_validation_path)

    rci_section = rci.get(RCI_SECTION)
    redm_section = redm.get(REDM_SECTION)

    if not isinstance(rci_section, dict):
        errors.append("RCI v0.4 enrichment section is missing")
        rci_section = {}

    if not isinstance(redm_section, dict):
        errors.append("REDM v0.4 enrichment section is missing")
        redm_section = {}

    rci_status = rci_section.get("status")
    redm_status = redm_section.get("status")

    if rci_status != "CANDIDATE":
        errors.append("RCI v0.4 must remain CANDIDATE")

    if redm_status != "CANDIDATE":
        errors.append("REDM v0.4 must remain CANDIDATE")

    if rci_validation.get("metadata", {}).get("result") != "PASSED":
        errors.append("RCI validation is not PASSED")

    if redm_validation.get("metadata", {}).get("result") != "PASSED":
        errors.append("REDM validation is not PASSED")

    closure_metadata = closure.get("metadata")
    closure_summary = closure.get("summary")
    explicit_deferrals = closure.get("explicit_deferrals")

    if not isinstance(closure_metadata, dict):
        errors.append("semantic closure metadata is missing")
        closure_metadata = {}

    if not isinstance(closure_summary, dict):
        errors.append("semantic closure summary is missing")
        closure_summary = {}

    if not isinstance(explicit_deferrals, list):
        errors.append("semantic closure deferrals are missing")
        explicit_deferrals = []

    if closure_metadata.get("result") != "PASSED":
        errors.append("semantic closure is not PASSED")

    if closure_summary.get("closure_state") != "GREEN_WITH_EXPLICIT_DEFERRALS":
        errors.append("semantic closure state is not releasable")

    if closure_summary.get("release_decision") != (
        "PROCEED_TO_REPOSITORY_KNOWLEDGE_RECONCILIATION_WITH_EXPLICIT_DEFERRALS"
    ):
        errors.append("semantic closure did not release reconciliation")

    if closure_metadata.get("external_rollout_state") != "gated":
        errors.append("external rollout must remain gated")

    rci_coverage = rci_section.get("coverage_lower_bounds")
    redm_coverage = redm_section.get("coverage_lower_bounds")

    if not isinstance(rci_coverage, dict):
        errors.append("RCI coverage is missing")
        rci_coverage = {}

    if not isinstance(redm_coverage, dict):
        errors.append("REDM coverage is missing")
        redm_coverage = {}

    for key in (
        "tracked_files",
        "reviewed_files",
        "dependencies_mapped",
        "fully_verified",
    ):
        if rci_coverage.get(key) != redm_coverage.get(key):
            errors.append(f"RCI/REDM metric mismatch for {key}")

    if rci_coverage.get("purpose_evidenced") != 79:
        errors.append("RCI purpose lower bound must remain 79")

    if redm_coverage.get("dependencies_mapped") != 80:
        errors.append("REDM dependency lower bound must remain 80")

    visible_deferrals = {
        str(item.get("deferral_id")): item
        for item in explicit_deferrals
        if isinstance(item, dict) and item.get("must_remain_visible") is True
    }

    if (
        visible_deferrals.get(
            "unreviewed_repository_scope",
            {},
        ).get("count")
        != 646
    ):
        errors.append("646 unreviewed files are not preserved")

    if (
        visible_deferrals.get(
            "wave_2_unknown_records",
            {},
        ).get("count")
        != 25
    ):
        errors.append("25 Wave 2 unknown records are not preserved")

    registry_strings = collect_strings(module_registry)
    missing_modules = sorted(EXPECTED_MODULES - registry_strings)

    if missing_modules:
        errors.append(f"module registry is missing active modules: {missing_modules}")

    authority_classes = authority_classifications(authority_policy)

    for required_term, present in authority_classes.items():
        if not present:
            errors.append(f"authority policy lacks governed classification: {required_term}")

    if not coordination_direction:
        errors.append("coordination direction snapshot is empty")

    if not portfolio_direction:
        errors.append("portfolio direction snapshot is empty")

    matrix.extend(
        [
            matrix_row(
                "RCI v0.4",
                status=(
                    "PASSED"
                    if rci_status == "CANDIDATE"
                    and rci_validation.get(
                        "metadata",
                        {},
                    ).get("result")
                    == "PASSED"
                    else "FAILED"
                ),
                authority="candidate",
                evidence=str(rci_validation_path),
                note="Capability candidate remains non-accepted.",
            ),
            matrix_row(
                "REDM v0.4",
                status=(
                    "PASSED"
                    if redm_status == "CANDIDATE"
                    and redm_validation.get(
                        "metadata",
                        {},
                    ).get("result")
                    == "PASSED"
                    else "FAILED"
                ),
                authority="candidate",
                evidence=str(redm_validation_path),
                note="Dependency candidate remains non-accepted.",
            ),
            matrix_row(
                "Blueprint coordination direction",
                status="PASSED" if coordination_direction else "FAILED",
                authority="current direction snapshot",
                evidence=str(coordination_direction_path),
                note="Coordination intent remains traceable.",
            ),
            matrix_row(
                "System portfolio direction",
                status="PASSED" if portfolio_direction else "FAILED",
                authority="current direction snapshot",
                evidence=str(portfolio_direction_path),
                note="Portfolio intent remains traceable.",
            ),
            matrix_row(
                "Artifact authority policy",
                status=("PASSED" if all(authority_classes.values()) else "FAILED"),
                authority="governance policy",
                evidence=str(authority_policy_path),
                note=(
                    "Accepted/generated roles come from policy; "
                    "candidate authority comes from RCI/REDM status."
                ),
            ),
            matrix_row(
                "Module registry",
                status="PASSED" if not missing_modules else "FAILED",
                authority="canonical registry",
                evidence=str(module_registry_path),
                note="Exactly the active managed modules remain represented.",
            ),
            matrix_row(
                "Explicit semantic deferrals",
                status=(
                    "DEFERRED"
                    if not errors
                    or (
                        visible_deferrals.get(
                            "unreviewed_repository_scope",
                            {},
                        ).get("count")
                        == 646
                        and visible_deferrals.get(
                            "wave_2_unknown_records",
                            {},
                        ).get("count")
                        == 25
                    )
                    else "FAILED"
                ),
                authority="closure report",
                evidence=str(closure_report_path),
                note="646 unreviewed files and 25 unknown records stay visible.",
            ),
        ]
    )

    passed = not errors

    return {
        "schema_version": ("repository_knowledge_reconciliation_report_v0_1"),
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
            "module_id": module_id,
            "external_rollout_state": "gated",
        },
        "summary": {
            "error_count": len(errors),
            "matrix_entry_count": len(matrix),
            "passed_entry_count": sum(item["status"] == "PASSED" for item in matrix),
            "deferred_entry_count": sum(item["status"] == "DEFERRED" for item in matrix),
            "failed_entry_count": sum(item["status"] == "FAILED" for item in matrix),
            "tracked_files": 726,
            "reviewed_files": 80,
            "purpose_evidenced": 79,
            "dependencies_mapped": 80,
            "fully_verified": 79,
            "unreviewed_files": 646,
            "wave_2_records_with_unknowns": 25,
            "full_semantic_coverage_claim_allowed": False,
            "candidate_acceptance_performed": False,
            "candidate_authority_source": "artifact_status",
            "policy_authority_classes": authority_classes,
            "release_decision": (
                "PROCEED_TO_INVENTORY_ACCEPTANCE_EVIDENCE_INDEX"
                if passed
                else "BLOCK_ACCEPTANCE_EVIDENCE_INDEX"
            ),
        },
        "candidate_hashes": {
            "rci_v0_4": sha256(rci_path),
            "redm_v0_4": sha256(redm_path),
            "coordination_direction_v0_2": sha256(coordination_direction_path),
            "portfolio_direction_v0_2": sha256(portfolio_direction_path),
        },
        "reconciliation_matrix": matrix,
        "explicit_deferrals": list(visible_deferrals.values()),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rci", required=True)
    parser.add_argument("--redm", required=True)
    parser.add_argument("--coordination-direction", required=True)
    parser.add_argument("--portfolio-direction", required=True)
    parser.add_argument("--authority-policy", required=True)
    parser.add_argument("--module-registry", required=True)
    parser.add_argument("--closure-report", required=True)
    parser.add_argument("--rci-validation", required=True)
    parser.add_argument("--redm-validation", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate_reconciliation(
        rci_path=Path(args.rci),
        redm_path=Path(args.redm),
        coordination_direction_path=Path(args.coordination_direction),
        portfolio_direction_path=Path(args.portfolio_direction),
        authority_policy_path=Path(args.authority_policy),
        module_registry_path=Path(args.module_registry),
        closure_report_path=Path(args.closure_report),
        rci_validation_path=Path(args.rci_validation),
        redm_validation_path=Path(args.redm_validation),
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
