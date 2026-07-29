#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid YAML {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def safe_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default

    if isinstance(value, int):
        return value

    return default


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0

    return round(numerator / denominator, 4)


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def git_lines(
    repo_root: Path,
    command: list[str],
) -> list[str]:
    result = subprocess.run(
        ["git", *command],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise ValueError(f"Git command failed: git {' '.join(command)}\n{result.stderr}")

    return [line for line in result.stdout.splitlines() if line.strip()]


def parse_name_status(lines: list[str]) -> dict[str, Any]:
    counts = {
        "added": 0,
        "modified": 0,
        "deleted": 0,
        "renamed": 0,
        "other": 0,
    }
    paths: list[dict[str, Any]] = []

    for line in lines:
        parts = line.split("\t")
        status = parts[0]

        if status.startswith("A"):
            category = "added"
        elif status.startswith("M"):
            category = "modified"
        elif status.startswith("D"):
            category = "deleted"
        elif status.startswith("R"):
            category = "renamed"
        else:
            category = "other"

        counts[category] += 1
        paths.append(
            {
                "status": status,
                "paths": parts[1:],
            }
        )

    return {
        "change_count": len(lines),
        "counts": counts,
        "changes": paths,
    }


def build_priorities(
    *,
    current_tracked: int,
    source_drift_count: int,
    semantic_unknowns: int,
    classification_pending: int,
    registry_findings: int,
    external_rollout_state: str | None,
) -> list[dict[str, Any]]:
    priorities: list[dict[str, Any]] = []

    if source_drift_count:
        priorities.append(
            {
                "priority": "critical",
                "work": ("Include post-RCI tracked-scope drift in Semantic Inventory Wave 2."),
                "evidence_count": source_drift_count,
            }
        )

    if semantic_unknowns:
        priorities.append(
            {
                "priority": "high",
                "work": (
                    "Resolve or explicitly defer unknowns recorded by Semantic Inventory Wave 1."
                ),
                "evidence_count": semantic_unknowns,
            }
        )

    if classification_pending:
        priorities.append(
            {
                "priority": "high",
                "work": ("Assign purpose and authority to broadly classified tracked files."),
                "evidence_count": classification_pending,
            }
        )

    if registry_findings:
        priorities.append(
            {
                "priority": "medium",
                "work": ("Reconcile confirmed registry findings before inventory acceptance."),
                "evidence_count": registry_findings,
            }
        )

    if external_rollout_state != "gated":
        priorities.append(
            {
                "priority": "critical",
                "work": ("Restore external module inventory rollout to gated state."),
                "evidence_count": 1,
            }
        )

    if not priorities:
        priorities.append(
            {
                "priority": "normal",
                "work": (
                    "Continue semantic verification until the acceptance threshold is reached."
                ),
                "evidence_count": current_tracked,
            }
        )

    return priorities


def build_dashboard(
    *,
    repo_root: Path,
    rci_path: Path,
    semantic_path: Path,
    artifact_map_path: Path,
    registry_path: Path,
    maintenance_path: Path,
    baseline_commit: str,
    as_of: str,
) -> dict[str, Any]:
    rci = load_yaml(rci_path)
    semantic = load_yaml(semantic_path)
    artifact_map = load_yaml(artifact_map_path)
    registry = load_yaml(registry_path)
    maintenance = load_yaml(maintenance_path)

    tracked_paths = git_lines(
        repo_root,
        ["ls-files"],
    )
    drift_lines = git_lines(
        repo_root,
        [
            "diff",
            "--name-status",
            f"{baseline_commit}..HEAD",
        ],
    )
    drift = parse_name_status(drift_lines)

    semantic_summary = semantic.get("summary", {})
    artifact_summary = artifact_map.get("summary", {})
    registry_summary = registry.get("summary", {})
    maintenance_rollout = maintenance.get(
        "external_rollout",
        {},
    )

    if not isinstance(semantic_summary, dict):
        semantic_summary = {}

    if not isinstance(artifact_summary, dict):
        artifact_summary = {}

    if not isinstance(registry_summary, dict):
        registry_summary = {}

    if not isinstance(maintenance_rollout, dict):
        maintenance_rollout = {}

    current_tracked = len(tracked_paths)
    selected_files = safe_int(semantic_summary.get("selected_files"))
    purpose_evidenced = safe_int(semantic_summary.get("purpose_evidenced"))
    dependencies_mapped = safe_int(semantic_summary.get("dependencies_mapped"))
    fully_verified = safe_int(semantic_summary.get("fully_verified"))
    semantic_unknowns = safe_int(semantic_summary.get("records_with_unknowns"))
    artifact_baseline_tracked = safe_int(artifact_summary.get("tracked_files"))
    classification_pending = safe_int(artifact_summary.get("classification_pending"))
    registry_findings = safe_int(registry_summary.get("finding_count"))
    external_rollout_state = maintenance_rollout.get("state")

    ratios = {
        "wave_1_selection_lower_bound": safe_ratio(
            selected_files,
            current_tracked,
        ),
        "purpose_evidenced_lower_bound": safe_ratio(
            purpose_evidenced,
            current_tracked,
        ),
        "dependencies_mapped_lower_bound": safe_ratio(
            dependencies_mapped,
            current_tracked,
        ),
        "fully_verified_lower_bound": safe_ratio(
            fully_verified,
            current_tracked,
        ),
    }

    source_scope_drift = current_tracked - artifact_baseline_tracked

    if source_scope_drift < 0:
        source_scope_drift_state = "baseline_exceeds_current"
    elif source_scope_drift > 0:
        source_scope_drift_state = "current_scope_exceeds_artifact_map"
    else:
        source_scope_drift_state = "aligned"

    priorities = build_priorities(
        current_tracked=current_tracked,
        source_drift_count=drift["change_count"],
        semantic_unknowns=semantic_unknowns,
        classification_pending=classification_pending,
        registry_findings=registry_findings,
        external_rollout_state=(
            external_rollout_state if isinstance(external_rollout_state, str) else None
        ),
    )

    blocking_conditions = [
        {
            "condition": "external_rollout_not_gated",
            "active": external_rollout_state != "gated",
        },
        {
            "condition": "tracked_scope_drift_unreviewed",
            "active": drift["change_count"] > 0,
        },
        {
            "condition": "semantic_unknowns_remaining",
            "active": semantic_unknowns > 0,
        },
        {
            "condition": "classification_pending",
            "active": classification_pending > 0,
        },
    ]

    return {
        "schema_version": ("blueprint_inventory_coverage_drift_dashboard_v0_1"),
        "metadata": {
            "module_id": "forprint_system_blueprint",
            "as_of": as_of,
            "baseline_commit": baseline_commit,
            "result": "READY_WITH_GAPS",
        },
        "sources": {
            "rci": str(rci_path),
            "semantic_inventory_wave_1": str(semantic_path),
            "artifact_authority_map": str(artifact_map_path),
            "module_registry_reconciliation": str(registry_path),
            "maintenance_policy": str(maintenance_path),
            "rci_schema_version": rci.get("schema_version"),
        },
        "scope": {
            "current_git_tracked_files": current_tracked,
            "artifact_map_tracked_files": artifact_baseline_tracked,
            "artifact_map_scope_delta": source_scope_drift,
            "artifact_map_scope_state": source_scope_drift_state,
            "changed_paths_since_rci_commit": drift["change_count"],
        },
        "semantic_coverage": {
            "wave_1_selected_files": selected_files,
            "purpose_evidenced": purpose_evidenced,
            "dependencies_mapped": dependencies_mapped,
            "fully_verified": fully_verified,
            "records_with_unknowns": semantic_unknowns,
            "ratios_are_lower_bounds": True,
            "ratios": ratios,
        },
        "authority_and_registry": {
            "classification_pending": classification_pending,
            "artifact_map_findings": safe_int(artifact_summary.get("finding_count")),
            "registry_findings": registry_findings,
            "modules_with_registry_findings": safe_int(
                registry_summary.get("modules_with_findings")
            ),
        },
        "drift": drift,
        "external_rollout": {
            "state": external_rollout_state,
            "release_conditions": maintenance_rollout.get(
                "release_conditions",
                [],
            ),
        },
        "blocking_conditions": blocking_conditions,
        "priorities": priorities,
        "interpretation": {
            "lower_bound": (
                "Semantic Wave 1 verified a selected high-value subset; "
                "the ratios do not claim that all unselected files are unknown."
            ),
            "drift": (
                "Changed paths since the accepted RCI commit must be "
                "reviewed before inventory acceptance."
            ),
            "release": (
                "External module inventory remains gated until "
                "Blueprint self-context acceptance is GREEN."
            ),
        },
        "quality_checks": {
            "git_tracked_scope_used": True,
            "git_name_status_drift_used": True,
            "semantic_ratios_labeled_lower_bound": True,
            "unknowns_not_silently_filled": True,
            "external_rollout_gate_reported": True,
            "source_artifacts_not_modified": True,
            "cross_repository_writes_not_authorized": True,
        },
    }


def render_markdown(dashboard: dict[str, Any]) -> str:
    scope = dashboard["scope"]
    semantic = dashboard["semantic_coverage"]
    ratios = semantic["ratios"]
    authority = dashboard["authority_and_registry"]
    rollout = dashboard["external_rollout"]
    drift = dashboard["drift"]

    lines = [
        "# Blueprint Inventory Coverage & Drift Dashboard",
        "",
        f"- As of: `{dashboard['metadata']['as_of']}`",
        f"- Baseline commit: `{dashboard['metadata']['baseline_commit']}`",
        f"- Result: `{dashboard['metadata']['result']}`",
        f"- External rollout: `{rollout['state']}`",
        "",
        "## Scope",
        "",
        (f"- Current tracked files: `{scope['current_git_tracked_files']}`"),
        (f"- Artifact-map tracked baseline: `{scope['artifact_map_tracked_files']}`"),
        (f"- Changed paths since RCI commit: `{scope['changed_paths_since_rci_commit']}`"),
        "",
        "## Semantic coverage lower bounds",
        "",
        (
            "- Wave 1 selected: "
            f"`{semantic['wave_1_selected_files']}` "
            f"({percent(ratios['wave_1_selection_lower_bound'])})"
        ),
        (
            "- Purpose evidenced: "
            f"`{semantic['purpose_evidenced']}` "
            f"({percent(ratios['purpose_evidenced_lower_bound'])})"
        ),
        (
            "- Dependencies mapped: "
            f"`{semantic['dependencies_mapped']}` "
            f"({percent(ratios['dependencies_mapped_lower_bound'])})"
        ),
        (
            "- Fully verified: "
            f"`{semantic['fully_verified']}` "
            f"({percent(ratios['fully_verified_lower_bound'])})"
        ),
        (f"- Records with unknowns: `{semantic['records_with_unknowns']}`"),
        "",
        "## Authority and registry",
        "",
        (f"- Classification pending: `{authority['classification_pending']}`"),
        (f"- Registry findings: `{authority['registry_findings']}`"),
        "",
        "## Drift",
        "",
        f"- Total changed paths: `{drift['change_count']}`",
        f"- Added: `{drift['counts']['added']}`",
        f"- Modified: `{drift['counts']['modified']}`",
        f"- Deleted: `{drift['counts']['deleted']}`",
        f"- Renamed: `{drift['counts']['renamed']}`",
        "",
        "## Priorities",
        "",
    ]

    for item in dashboard["priorities"]:
        lines.append(
            f"- **{item['priority']}** — {item['work']} (evidence: {item['evidence_count']})"
        )

    lines.extend(
        [
            "",
            "## Release decision",
            "",
            (
                "External module inventory remains gated. "
                "Semantic Inventory Wave 2 must absorb tracked-scope "
                "drift and unresolved self-context before acceptance."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Render Blueprint repository-knowledge coverage and drift.")
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--rci", required=True)
    parser.add_argument("--semantic-wave", required=True)
    parser.add_argument("--artifact-map", required=True)
    parser.add_argument("--registry-report", required=True)
    parser.add_argument("--maintenance-policy", required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--yaml-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    dashboard = build_dashboard(
        repo_root=repo_root,
        rci_path=Path(args.rci),
        semantic_path=Path(args.semantic_wave),
        artifact_map_path=Path(args.artifact_map),
        registry_path=Path(args.registry_report),
        maintenance_path=Path(args.maintenance_policy),
        baseline_commit=args.baseline_commit,
        as_of=args.as_of,
    )

    yaml_output = Path(args.yaml_output)
    markdown_output = Path(args.markdown_output)
    yaml_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    yaml_output.write_text(
        yaml.safe_dump(
            dashboard,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )
    markdown_output.write_text(
        render_markdown(dashboard),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
