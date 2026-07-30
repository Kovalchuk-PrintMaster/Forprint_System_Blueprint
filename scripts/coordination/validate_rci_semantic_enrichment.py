#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
from pathlib import Path
from typing import Any

import yaml

SECTION = "semantic_enrichment_v0_1"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_path(
    value: str | Path,
    *,
    repo_root: Path | None = None,
) -> Path:
    path = Path(value)

    if not path.is_absolute():
        base = repo_root.resolve() if repo_root is not None else Path.cwd().resolve()
        path = base / path

    return path.resolve()


def references_path(
    reference: Any,
    actual_path: Path,
    *,
    repo_root: Path | None = None,
) -> bool:
    if not isinstance(reference, str) or not reference:
        return False

    return normalized_path(
        reference,
        repo_root=repo_root,
    ) == normalized_path(
        actual_path,
        repo_root=repo_root,
    )


def validate(
    *,
    source_path: Path,
    candidate_path: Path,
    enrichment_record_path: Path,
    expected_source_sha256: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    source = load_yaml(source_path)
    candidate = load_yaml(candidate_path)
    record = load_yaml(enrichment_record_path)

    effective_root = repo_root.resolve() if repo_root is not None else Path.cwd().resolve()
    actual_source_sha256 = sha256(source_path)

    if expected_source_sha256 is not None and actual_source_sha256 != expected_source_sha256:
        errors.append("accepted RCI v0.3 SHA-256 drift")

    section = candidate.get(SECTION)

    if not isinstance(section, dict):
        errors.append("semantic enrichment section is missing")
        section = {}

    base_candidate = copy.deepcopy(candidate)
    base_candidate.pop(SECTION, None)

    if base_candidate != source:
        errors.append(
            "candidate modifies accepted RCI content outside the additive enrichment section"
        )

    if section.get("status") != "CANDIDATE":
        errors.append("enrichment status must be CANDIDATE")

    if not references_path(
        section.get("source_snapshot"),
        source_path,
        repo_root=effective_root,
    ):
        errors.append("source_snapshot does not reference RCI v0.3")

    evidence_sources = section.get("evidence_sources")

    if not isinstance(evidence_sources, list) or len(evidence_sources) < 4:
        errors.append("at least four evidence sources are required")

    coverage = section.get("coverage_lower_bounds")

    if not isinstance(coverage, dict):
        errors.append("coverage lower bounds are missing")
        coverage = {}

    expected_coverage = {
        "tracked_files": 726,
        "reviewed_files": 80,
        "purpose_evidenced": 79,
        "dependencies_mapped": 80,
        "fully_verified": 79,
    }

    for key, expected in expected_coverage.items():
        if coverage.get(key) != expected:
            errors.append(
                f"coverage mismatch for {key}: expected {expected!r}, found {coverage.get(key)!r}"
            )

    freshness = section.get("freshness")

    if not isinstance(freshness, dict):
        errors.append("freshness section is missing")
        freshness = {}

    if freshness.get("release_decision") not in {
        "PROCEED_AS_FRESH",
        "PROCEED_WITH_BOUNDED_REFRESH",
    }:
        errors.append("freshness release decision is not releasable")

    unresolved = section.get("unresolved_scope")

    if not isinstance(unresolved, dict):
        errors.append("unresolved scope is missing")
        unresolved = {}

    if unresolved.get("unreviewed_files") != 646:
        errors.append("unreviewed file count must remain explicit")

    if unresolved.get("wave_2_records_with_unknowns") != 25:
        errors.append("Wave 2 unknown record count must remain explicit")

    policy = section.get("evidence_policy")

    if not isinstance(policy, dict):
        errors.append("evidence policy is missing")
        policy = {}

    for key in (
        "only_verified_claims",
        "unknowns_not_silently_resolved",
        "source_snapshot_immutable",
        "external_rollout_gated",
    ):
        if policy.get(key) is not True:
            errors.append(f"evidence policy flag must be true: {key}")

    index_entries = section.get("evidence_index_entries")

    if not isinstance(index_entries, list) or not index_entries:
        errors.append("evidence index entries are missing")

    if not references_path(
        record.get("candidate_rci"),
        candidate_path,
        repo_root=effective_root,
    ):
        errors.append("enrichment record candidate path mismatch")

    if not references_path(
        record.get("source_rci"),
        source_path,
        repo_root=effective_root,
    ):
        errors.append("enrichment record source path mismatch")

    passed = not errors

    return {
        "schema_version": "rci_semantic_enrichment_validation_report_v0_1",
        "metadata": {
            "result": "PASSED" if passed else "FAILED",
        },
        "summary": {
            "error_count": len(errors),
            "additive_only": base_candidate == source,
            "path_references_normalized": True,
            "evidence_source_count": (
                len(evidence_sources) if isinstance(evidence_sources, list) else 0
            ),
            "evidence_index_entry_count": (
                len(index_entries) if isinstance(index_entries, list) else 0
            ),
            "source_sha256": actual_source_sha256,
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--enrichment-record", required=True)
    parser.add_argument("--expected-source-sha256")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = validate(
        source_path=Path(args.source),
        candidate_path=Path(args.candidate),
        enrichment_record_path=Path(args.enrichment_record),
        expected_source_sha256=args.expected_source_sha256,
        repo_root=Path(args.repo_root),
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
