from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.prompt_execution_events_v0_1 import (
    discover_execution_events,
)

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = Path("coordination/self_coordination/roadmap.yaml")
QUEUE = Path("coordination/self_coordination/prompt_queue/index.yaml")
POLICY = Path("coordination/standards/governance/coordination_health_policy_v0_1.yaml")
REGISTRY = Path("coordination/registry/coordination_source_registry_v0_1.yaml")

STABLE_CODE_CATALOG = {
    "ROADMAP_HORIZON_BELOW_MINIMUM": "warning",
    "ROADMAP_HORIZON_BELOW_TARGET": "advisory",
    "PROMPT_BUFFER_BELOW_MINIMUM": "warning",
    "PROMPT_BUFFER_BELOW_TARGET": "advisory",
    "ACTIVE_PROMPT_MISSING": "warning",
    "MULTIPLE_ACTIVE_PROMPTS": "error",
    "QUEUE_ROADMAP_ACTIVE_ID_MISMATCH": "error",
    "QUEUE_ROADMAP_REFERENCE_MISSING": "error",
    "QUEUE_ROADMAP_STATE_DRIFT": "error",
    "PROMPT_FILE_MISSING": "error",
    "PHYSICAL_DRAFT_COUNT_MISMATCH": "error",
    "QUEUE_METADATA_COUNT_DRIFT": "error",
    "COMPLETION_PENDING_COUNT_UNAVAILABLE": "warning",
    "PROMPT_EXECUTION_EVENT_INVALID": "error",
    "PROMPT_EXECUTION_TRANSITION_INVALID": "error",
    "PROMPT_EXECUTION_QUEUE_STATE_DRIFT": "error",
    "PROMPT_EXECUTION_WIP_VIOLATION": "error",
    "PROMPT_EXECUTION_SOURCE_UNAVAILABLE": "warning",
}


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping: {path}")
    return value


def add_code(
    buckets: dict[str, list[str]],
    code: str,
) -> None:
    severity = STABLE_CODE_CATALOG[code]
    key = {
        "error": "errors",
        "warning": "warnings",
        "advisory": "advisories",
    }[severity]
    if code not in buckets[key]:
        buckets[key].append(code)


def roadmap_health(
    future_count: int,
    minimum: int,
    target: int,
) -> tuple[str, list[str]]:
    if future_count < minimum:
        return "below_minimum", ["ROADMAP_HORIZON_BELOW_MINIMUM"]
    if future_count < target:
        return "minimum_met_target_not_met", ["ROADMAP_HORIZON_BELOW_TARGET"]
    return "healthy", []


def prompt_buffer_health(
    dispatchable_count: int,
    minimum: int,
    target: int,
) -> tuple[str, list[str]]:
    if dispatchable_count < minimum:
        return "below_minimum", ["PROMPT_BUFFER_BELOW_MINIMUM"]
    if dispatchable_count < target:
        return "minimum_met_target_not_met", ["PROMPT_BUFFER_BELOW_TARGET"]
    return "target_met", []


def active_prompt_health(
    active_count: int,
    maximum: int,
) -> tuple[str, list[str]]:
    if active_count == 0:
        return "missing", ["ACTIVE_PROMPT_MISSING"]
    if active_count > maximum:
        return "multiple", ["MULTIPLE_ACTIVE_PROMPTS"]
    return "healthy", []


def roadmap_records(roadmap: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for section in ("steps", "deferred_steps"):
        for item in roadmap.get(section, []):
            if isinstance(item, dict) and isinstance(item.get("step_id"), str):
                values[item["step_id"]] = item
    return values



def _load_completion_discovery_module(root: Path):
    path = root / "scripts/coordination/completion_discovery_and_intake_v0_4.py"
    spec = importlib.util.spec_from_file_location(
        "forprint_completion_discovery_intake_v04_for_pulse",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load completion discovery module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completion_discovery_report(
    root: Path,
    registry_path: Path,
) -> dict[str, Any]:
    module = _load_completion_discovery_module(root)
    return module.discover_completions(
        blueprint_root=root,
        registry_path=registry_path,
    )


def evaluate(root: Path = ROOT) -> dict[str, Any]:
    roadmap = load_yaml(root / ROADMAP)
    queue = load_yaml(root / QUEUE)
    policy = load_yaml(root / POLICY)
    registry_path = root / REGISTRY
    registry = load_yaml(registry_path)
    completion_discovery = _completion_discovery_report(root, registry_path)
    execution_discovery = discover_execution_events(
        blueprint_root=root,
        registry_path=registry_path,
    )

    codes: dict[str, list[str]] = {
        "errors": [],
        "warnings": [],
        "advisories": [],
    }

    execution_summary = execution_discovery.get("summary", {})
    if int(execution_summary.get("invalid_events", 0)):
        add_code(codes, "PROMPT_EXECUTION_EVENT_INVALID")
    if int(execution_summary.get("transition_errors", 0)):
        add_code(codes, "PROMPT_EXECUTION_TRANSITION_INVALID")
    if int(execution_summary.get("queue_state_errors", 0)):
        add_code(codes, "PROMPT_EXECUTION_QUEUE_STATE_DRIFT")
    if int(execution_summary.get("wip_errors", 0)):
        add_code(codes, "PROMPT_EXECUTION_WIP_VIOLATION")
    if int(execution_summary.get("source_errors", 0)):
        add_code(codes, "PROMPT_EXECUTION_SOURCE_UNAVAILABLE")

    records = roadmap_records(roadmap)
    current_id = str(roadmap["metadata"]["current_step_id"])
    current = records[current_id]
    current_sequence = int(current["sequence"])

    future = [
        item
        for item in roadmap.get("steps", [])
        if isinstance(item, dict)
        and isinstance(item.get("sequence"), int)
        and item["sequence"] > current_sequence
        and item.get("status") in {"active", "planned", "ready"}
    ]
    future.sort(key=lambda item: item["sequence"])

    roadmap_policy = policy["roadmap"]
    roadmap_state, roadmap_codes = roadmap_health(
        len(future),
        int(roadmap_policy["minimum_future_steps"]),
        int(roadmap_policy["target_future_steps"]),
    )
    for code in roadmap_codes:
        add_code(codes, code)

    prompts = [x for x in queue.get("prompts", []) if isinstance(x, dict)]
    active_prompts = [x for x in prompts if x.get("status") == "approved"]
    active_policy = policy["active_prompt"]
    active_state, active_codes = active_prompt_health(
        len(active_prompts),
        int(active_policy["maximum"]),
    )
    for code in active_codes:
        add_code(codes, code)

    queue_active_id = queue.get("metadata", {}).get("active_prompt_id")
    if queue_active_id != current_id:
        add_code(codes, "QUEUE_ROADMAP_ACTIVE_ID_MISMATCH")

    physical_draft_files = sorted(
        (root / "coordination/self_coordination/prompt_queue/draft").glob("*.md")
    )
    indexed_drafts = [x for x in prompts if x.get("status") == "draft"]
    dispatchable = [
        x
        for x in indexed_drafts
        if x.get("dispatch_ready") is True and x.get("execution_status") != "deferred"
    ]

    buffer_policy = policy["prompt_buffer"]
    buffer_state, buffer_codes = prompt_buffer_health(
        len(dispatchable),
        int(buffer_policy["minimum_dispatchable_drafts"]),
        int(buffer_policy["target_dispatchable_drafts"]),
    )
    for code in buffer_codes:
        add_code(codes, code)

    if len(physical_draft_files) != len(indexed_drafts):
        add_code(codes, "PHYSICAL_DRAFT_COUNT_MISMATCH")

    queue_meta = queue.get("metadata", {})
    metadata_drift: list[str] = []
    expected_counts = {
        "approved_prompt_count": len(active_prompts),
        "draft_prompt_count": len(indexed_drafts),
        "completed_prompt_count": sum(1 for x in prompts if x.get("status") == "completed"),
        "dispatchable_draft_count": len(dispatchable),
        "deferred_prompt_count": sum(1 for x in prompts if x.get("execution_status") == "deferred"),
    }
    for key, expected in expected_counts.items():
        if queue_meta.get(key) != expected:
            metadata_drift.append(key)
    if metadata_drift:
        add_code(codes, "QUEUE_METADATA_COUNT_DRIFT")

    workstream_id = str(roadmap.get("metadata", {}).get("v0_4_workstream", {}).get("id", ""))
    current_workstream_prompts = [
        item for item in prompts if item.get("workstream") == workstream_id
    ]

    missing_references: list[str] = []
    state_drift: list[str] = []
    missing_files: list[str] = []

    for prompt in current_workstream_prompts:
        prompt_id = str(prompt.get("prompt_id", ""))
        step_id = prompt.get("roadmap_step_id")
        if not isinstance(step_id, str) or step_id not in records:
            missing_references.append(prompt_id)
            continue

        step = records[step_id]
        pstatus = prompt.get("status")
        execution = prompt.get("execution_status")
        sstatus = step.get("status")

        compatible = (
            (pstatus == "completed" and sstatus == "completed")
            or (pstatus == "approved" and sstatus == "active")
            or (pstatus == "draft" and execution == "deferred" and sstatus == "deferred")
            or (pstatus == "draft" and execution != "deferred" and sstatus in {"planned", "ready"})
        )
        if not compatible:
            state_drift.append(prompt_id)

        path_value = prompt.get("path")
        if not isinstance(path_value, str) or not (root / path_value).is_file():
            missing_files.append(prompt_id)

    if missing_references:
        add_code(codes, "QUEUE_ROADMAP_REFERENCE_MISSING")
    if state_drift:
        add_code(codes, "QUEUE_ROADMAP_STATE_DRIFT")
    if missing_files:
        add_code(codes, "PROMPT_FILE_MISSING")

    modules = [x for x in registry.get("modules", []) if isinstance(x, dict)]
    discovery_summary = completion_discovery.get("summary", {})
    observed_states = discovery_summary.get("observed_source_states", {})
    if not isinstance(observed_states, dict):
        observed_states = {}

    outbox_present = int(observed_states.get("present", 0)) + int(
        observed_states.get("present_empty", 0)
    )
    outbox_not_present_yet = int(observed_states.get("not_present_yet", 0))
    outbox_other = max(
        0,
        len(modules) - outbox_present - outbox_not_present_yet,
    )

    review_candidate_count = int(discovery_summary.get("review_candidates", 0))
    invalid_event_count = int(discovery_summary.get("invalid_events", 0))
    source_error_count = int(discovery_summary.get("source_errors", 0))

    if outbox_present == 0:
        completion_state = "not_available_yet"
        pending_count: int | None = None
    elif invalid_event_count or source_error_count:
        completion_state = "discovery_attention_required"
        pending_count = None
    else:
        pending_count = review_candidate_count
        completion_state = (
            "review_candidates_available"
            if review_candidate_count
            else "outbox_present_no_review_candidates"
        )

    overall = "healthy"
    if codes["errors"]:
        overall = "error"
    elif codes["warnings"]:
        overall = "warning"
    elif codes["advisories"]:
        overall = "advisory"

    return {
        "schema_version": "coordination_pulse_v0_1",
        "mode": "local_read_only",
        "network_independent": True,
        "overall_state": overall,
        "roadmap": {
            "current_step_id": current_id,
            "current_sequence": current_sequence,
            "future_steps": len(future),
            "minimum_future_steps": int(roadmap_policy["minimum_future_steps"]),
            "target_future_steps": int(roadmap_policy["target_future_steps"]),
            "maximum_future_steps": roadmap_policy.get("maximum_future_steps"),
            "state": roadmap_state,
        },
        "prompt_queue": {
            "active_prompt_id": queue_active_id,
            "active_prompt_count": len(active_prompts),
            "desired_active_prompts": int(active_policy["desired"]),
            "maximum_active_prompts": int(active_policy["maximum"]),
            "active_state": active_state,
            "physical_draft_files": len(physical_draft_files),
            "indexed_drafts": len(indexed_drafts),
            "dispatchable_drafts": len(dispatchable),
            "minimum_dispatchable_drafts": int(buffer_policy["minimum_dispatchable_drafts"]),
            "target_dispatchable_drafts": int(buffer_policy["target_dispatchable_drafts"]),
            "buffer_state": buffer_state,
            "metadata_count_drift": sorted(metadata_drift),
        },
        "prompt_execution": {
            "result_state": execution_discovery.get("result_state"),
            "events_discovered": int(
                execution_summary.get("events_discovered", 0)
            ),
            "current_observations": int(
                execution_summary.get("current_projections", 0)
            ),
            "historical_observations": int(
                execution_summary.get("historical_projections", 0)
            ),
            "invalid_events": int(
                execution_summary.get("invalid_events", 0)
            ),
            "transition_errors": int(
                execution_summary.get("transition_errors", 0)
            ),
            "queue_state_errors": int(
                execution_summary.get("queue_state_errors", 0)
            ),
            "wip_errors": int(
                execution_summary.get("wip_errors", 0)
            ),
            "source_errors": int(
                execution_summary.get("source_errors", 0)
            ),
            "projections": execution_discovery.get("projections", []),
            "observation_source": "prompt_execution_events_v0_1",
        },
        "completions": {
            "pending_completions": pending_count,
            "state": completion_state,
            "registered_module_sources": len(modules),
            "outbox_present_sources": outbox_present,
            "outbox_not_present_yet_sources": outbox_not_present_yet,
            "outbox_other_sources": outbox_other,
            "review_candidates": review_candidate_count,
            "invalid_events": invalid_event_count,
            "source_errors": source_error_count,
            "discovery_result_state": completion_discovery.get("result_state"),
            "observation_source": "completion_discovery_and_intake_v0_4",
        },
        "queue_roadmap_drift": {
            "scope_workstream": workstream_id,
            "missing_references": sorted(missing_references),
            "state_drift": sorted(state_drift),
            "missing_prompt_files": sorted(missing_files),
            "count": (len(missing_references) + len(state_drift) + len(missing_files)),
        },
        "codes": {
            "errors": sorted(codes["errors"]),
            "warnings": sorted(codes["warnings"]),
            "advisories": sorted(codes["advisories"]),
        },
        "stable_code_catalog": dict(sorted(STABLE_CODE_CATALOG.items())),
        "policy": {
            "path": str(POLICY),
            "schema_version": policy.get("schema_version"),
            "status": policy.get("metadata", {}).get("status"),
        },
    }


def render_text(data: dict[str, Any]) -> str:
    r = data["roadmap"]
    q = data["prompt_queue"]
    e = data["prompt_execution"]
    c = data["completions"]
    d = data["queue_roadmap_drift"]
    codes = data["codes"]
    lines = [
        "ForPrint Coordination Pulse v0.1",
        f"overall: {data['overall_state']}",
        "mode: local_read_only",
        "network_independent: true",
        "",
        "ROADMAP",
        f"current: {r['current_step_id']}",
        (
            "future: "
            f"{r['future_steps']} "
            f"(minimum={r['minimum_future_steps']}, target={r['target_future_steps']})"
        ),
        f"state: {r['state']}",
        "",
        "PROMPT QUEUE",
        f"active_prompt_count: {q['active_prompt_count']}",
        f"active_prompt_id: {q['active_prompt_id']}",
        f"physical_drafts: {q['physical_draft_files']}",
        f"dispatchable_drafts: {q['dispatchable_drafts']}",
        (
            "dispatchable_policy: "
            f"minimum={q['minimum_dispatchable_drafts']}, "
            f"target={q['target_dispatchable_drafts']}"
        ),
        f"buffer_state: {q['buffer_state']}",
        "",
        "MODULE EXECUTION",
        f"state: {e['result_state']}",
        f"events_discovered: {e['events_discovered']}",
        f"current_observations: {e['current_observations']}",
        (
            "observed: "
            + (
                ",".join(
                    f"{item.get('module_id')}/"
                    f"{item.get('prompt_id')}="
                    f"{item.get('observed_status')}"
                    for item in e["projections"]
                )
                if e["projections"]
                else "-"
            )
        ),
        "",
        "COMPLETIONS",
        (
            "pending_completions: "
            + (str(c["pending_completions"]) if c["pending_completions"] is not None else "unknown")
        ),
        f"state: {c['state']}",
        f"outbox_present_sources: {c['outbox_present_sources']}",
        f"outbox_not_present_yet_sources: {c['outbox_not_present_yet_sources']}",
        "",
        "QUEUE<->ROADMAP DRIFT",
        f"count: {d['count']}",
        f"missing_references: {','.join(d['missing_references']) or '-'}",
        f"state_drift: {','.join(d['state_drift']) or '-'}",
        f"missing_prompt_files: {','.join(d['missing_prompt_files']) or '-'}",
        "",
        "CODES",
        f"errors: {','.join(codes['errors']) or '-'}",
        f"warnings: {','.join(codes['warnings']) or '-'}",
        f"advisories: {','.join(codes['advisories']) or '-'}",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output-format",
        choices=("text", "yaml"),
        default="text",
    )
    args = parser.parse_args()

    data = evaluate(args.root.resolve())
    if args.output_format == "yaml":
        print(yaml.safe_dump(data, sort_keys=False).rstrip())
    else:
        print(render_text(data))

    return 1 if data["codes"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
