from __future__ import annotations

import argparse
import collections
import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "forprint_module_roadmap_reconciliation_report_v0_1"
STEP_PATTERN = re.compile(r"\b[a-z0-9][a-z0-9_]+_v\d+_\d+\b")


class ReconciliationError(ValueError):
    pass


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ReconciliationError(f"missing YAML source: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReconciliationError(f"YAML source must be a mapping: {path}")
    return data


def _flatten(node: Any, path: tuple[str, ...] = ()) -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            rows.extend(_flatten(value, path + (str(key),)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            rows.extend(_flatten(value, path + (str(index),)))
    else:
        rows.append((".".join(path), node))
    return rows


def _state_entry(state: dict[str, Any], module_id: str) -> dict[str, Any]:
    rows = state.get("modules")
    if not isinstance(rows, list):
        raise ReconciliationError("module inventory state has no modules list")
    matches = [row for row in rows if isinstance(row, dict) and row.get("module_id") == module_id]
    if len(matches) != 1:
        raise ReconciliationError(
            f"expected one inventory-state row for {module_id}, got {len(matches)}"
        )
    return matches[0]


def _step_ids(data: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    for _, value in _flatten(data):
        if isinstance(value, str):
            found.update(STEP_PATTERN.findall(value))
    return found


def _interesting_fields(data: dict[str, Any]) -> list[dict[str, Any]]:
    keys = (
        "roadmap",
        "capability",
        "gap",
        "recommend",
        "action",
        "lineage",
        "authority",
        "status",
        "current",
    )
    rows: list[dict[str, Any]] = []
    for path, value in _flatten(data):
        if not any(token in path.lower() for token in keys):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append({"path": path, "value": value})
    return rows[:500]


def build_report(
    *,
    root: Path,
    module_id: str,
    roadmap_path: Path,
    state_path: Path,
) -> dict[str, Any]:
    root = root.resolve()
    roadmap = _load_yaml(roadmap_path)
    state = _load_yaml(state_path)
    state_row = _state_entry(state, module_id)

    ref_keys = (
        "inventory_evidence_ref",
        "implementation_lineage_ref",
        "first_wave_reconciliation_ref",
    )
    refs: dict[str, Path] = {}
    for key in ref_keys:
        raw = state_row.get(key)
        if not isinstance(raw, str) or not raw:
            raise ReconciliationError(f"{module_id} inventory state missing {key}")
        refs[key] = root / raw

    evidence = {
        "inventory_completion": _load_yaml(refs["inventory_evidence_ref"]),
        "implementation_lineage": _load_yaml(refs["implementation_lineage_ref"]),
        "reconciliation_input": _load_yaml(refs["first_wave_reconciliation_ref"]),
    }

    steps = roadmap.get("roadmap")
    if not isinstance(steps, list) or not steps:
        raise ReconciliationError("canonical roadmap has no steps")

    step_rows: list[dict[str, Any]] = []
    roadmap_ids: set[str] = set()
    status_counts: collections.Counter[str] = collections.Counter()
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("step_id"), str):
            raise ReconciliationError("invalid roadmap step")
        step_id = step["step_id"]
        roadmap_ids.add(step_id)
        status = str(step.get("status", "UNKNOWN"))
        status_counts[status] += 1
        step_rows.append(
            {
                "sequence": step.get("sequence"),
                "step_id": step_id,
                "title": step.get("title"),
                "status": status,
                "priority": step.get("priority"),
                "evidence_present": bool(step.get("evidence")),
            }
        )

    evidence_ids: set[str] = set()
    for data in evidence.values():
        evidence_ids.update(_step_ids(data))

    current_step_id = roadmap.get("metadata", {}).get("current_step_id")
    current_step = next(
        (row for row in step_rows if row["step_id"] == current_step_id),
        None,
    )

    sources = {
        "canonical_roadmap": {
            "path": roadmap_path.relative_to(root).as_posix(),
            "sha256": _sha(roadmap_path),
        },
        "module_inventory_state": {
            "path": state_path.relative_to(root).as_posix(),
            "sha256": _sha(state_path),
        },
    }
    for label, key in (
        ("inventory_completion", "inventory_evidence_ref"),
        ("implementation_lineage", "implementation_lineage_ref"),
        ("reconciliation_input", "first_wave_reconciliation_ref"),
    ):
        path = refs[key]
        sources[label] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha(path),
        }

    return {
        "schema_version": SCHEMA,
        "module_id": module_id,
        "state": "REVIEW_READY_PENDING_CANONICAL_ROADMAP_APPLY",
        "authority": "BLUEPRINT_RECONCILIATION_EVIDENCE_NOT_EXECUTION_AUTHORITY",
        "auto_apply_performed": False,
        "sources": sources,
        "inventory_program_state_before": {
            "inventory_state": state_row.get("inventory_state"),
            "consolidation_state": state_row.get("consolidation_state"),
            "roadmap_enrichment_state": state_row.get("roadmap_enrichment_state"),
            "module_index_state": state_row.get("module_index_state"),
            "agents_md_state": state_row.get("agents_md_state"),
            "local_inventory_tooling_state": state_row.get("local_inventory_tooling_state"),
            "autonomous_readiness_state": state_row.get("autonomous_readiness_state"),
        },
        "roadmap_summary": {
            "roadmap_version": roadmap.get("metadata", {}).get("roadmap_version"),
            "current_step_id": current_step_id,
            "current_step": current_step,
            "step_count": len(step_rows),
            "status_counts": dict(sorted(status_counts.items())),
            "steps": step_rows,
        },
        "evidence_alignment": {
            "roadmap_step_ids_mentioned_by_inventory_lineage_or_reconciliation": sorted(
                evidence_ids & roadmap_ids
            ),
            "step_like_ids_in_evidence_not_present_in_canonical_roadmap": sorted(
                evidence_ids - roadmap_ids
            ),
            "canonical_roadmap_step_ids_not_mentioned_in_evidence_sources": sorted(
                roadmap_ids - evidence_ids
            ),
        },
        "reconciliation_input_projection": {
            "roadmap_related_scalar_fields": _interesting_fields(evidence["reconciliation_input"])
        },
        "semantic_invariants": {
            "implementation_inventory_roadmap_alignment_required": True,
            "blueprint_assigned_responsibility_must_be_roadmap_visible_or_evidenced": True,
            "unknown_legacy_must_not_be_invented": True,
            "roadmap_status_must_not_be_used_as_prompt_release_authority": True,
        },
        "review_questions": [
            "Which implemented capabilities are absent from the canonical roadmap?",
            "Which roadmap items are already implemented but still projected as future work?",
            "Which roadmap directions are stale, superseded or contradicted by implementation lineage?",
            "Which discovered capabilities should become roadmap enrichment candidates?",
            "Which Blueprint-assigned responsibilities are missing from the module roadmap?",
            "Does current_step_id still represent the intended planning front?",
        ],
        "canonical_apply_gate": {
            "required": True,
            "automatic": False,
            "requires_semantic_review": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(
        root=root,
        module_id=args.module,
        roadmap_path=root / "coordination/roadmaps" / f"{args.module}.yaml",
        state_path=root
        / (
            "coordination/internal_work/blueprint/module_inventory/"
            "2026-09-04__module_inventory_program_state_v0_1.yaml"
        ),
    )
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        yaml.safe_dump(report, sort_keys=False, allow_unicode=True, width=112),
        encoding="utf-8",
    )
    print("MODULE_ROADMAP_RECONCILIATION=PASS")
    print(f"MODULE_ID={args.module}")
    print(f"REPORT={output.relative_to(root)}")
    print(f"REPORT_SHA256={_sha(output)}")
    print(f"STEP_COUNT={report['roadmap_summary']['step_count']}")
    print(f"STATE={report['state']}")
    print("AUTO_APPLY_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
