#!/usr/bin/env python3
"""Deterministic roadmap/execution-state reconciliation for ForPrint Blueprint.

Roadmap files own desired order, dependencies and work bindings.
The append-only continuity event store owns actual execution state.
This script owns only generated non-authoritative reconciliation projections.

Historical pre-enforcement roadmap completion markers are accepted only for explicitly
registered completed legacy roadmaps during migration. They never override current/future
Control Foundation lifecycle state.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import yaml

EXECUTION_PROJECTION = Path(
    "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml"
)
RECONCILIATION_PROJECTION = Path(
    "coordination/roadmap_execution/projections/ROADMAP_RECONCILIATION_STATUS.yaml"
)
EVENT_ROOT = Path("coordination/continuity/events")

ROADMAPS = {
    "continuity_foundation": {
        "path": (
            "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
            "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
        ),
        "work_field": "work",
        "manual_wip_limit": 1,
        "historical_completion_evidence_allowed": True,
        "historical_shared_work_bindings_allowed": True,
    },
    "control_foundation_near_horizon": {
        "path": (
            "coordination/roadmaps/details/forprint_system_blueprint/"
            "control_foundation_near_horizon_program_v0_1.yaml"
        ),
        "work_field": "work_id",
        "manual_wip_limit": 1,
        "historical_completion_evidence_allowed": False,
        "historical_shared_work_bindings_allowed": False,
    },
}

EVENT_STATE = {
    "WORK_PLANNED": "PLANNED",
    "WORK_ACTIVATED": "ACTIVE",
    "CHECKPOINT_RECORDED": "CHECKPOINTED",
    "VALIDATION_PASSED": "VALIDATED",
    "VALIDATION_FAILED": "CHECKPOINTED",
    "WORK_CLOSED": "CLOSED",
    "WORK_SUPERSEDED": "CLOSED",
}
LIFECYCLE_STATES = {"PLANNED", "ACTIVE", "CHECKPOINTED", "VALIDATED", "CLOSED"}
OPEN_EXECUTION_STATES = {"PLANNED", "ACTIVE", "CHECKPOINTED", "VALIDATED"}


class ReconciliationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ReconciliationError(f"YAML_MAPPING_REQUIRED={path}")
    return value


# ROADMAP_RECONCILIATION_CUSTOM_EVENT_ROOT_V0_1
def load_events(
    root: Path,
    *,
    event_root: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], int]:
    latest: dict[str, dict[str, Any]] = {}
    latest_sequence = 0
    resolved_event_root = (
        event_root.resolve()
        if event_root is not None
        else root / EVENT_ROOT
    )
    if not resolved_event_root.is_dir():
        raise ReconciliationError("EVENT_ROOT_MISSING")
    for path in sorted(resolved_event_root.glob("*.yaml")):
        row = load_yaml(path)
        seq = int(row.get("sequence") or 0)
        latest_sequence = max(latest_sequence, seq)
        work_id = row.get("work_id")
        event_type = row.get("event_type")
        if not isinstance(work_id, str) or event_type not in EVENT_STATE:
            continue
        prior = latest.get(work_id)
        if prior is None or int(prior.get("sequence") or 0) <= seq:
            latest[work_id] = row
    return latest, latest_sequence


def normalize_dependencies(raw: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ReconciliationError("STEP_DEPENDS_ON_MUST_BE_LIST")
    values: list[str] = []
    for item in raw:
        if isinstance(item, str):
            values.append(item)
        elif isinstance(item, dict) and isinstance(item.get("step_id"), str):
            values.append(item["step_id"])
        else:
            raise ReconciliationError("STEP_DEPENDENCY_SHAPE_UNSUPPORTED")
    return values


def external_lifecycle_dependency(value: str) -> tuple[str, str] | None:
    if ":" not in value:
        return None
    work_id, required_state = value.rsplit(":", 1)
    if not work_id or required_state not in LIFECYCLE_STATES:
        return None
    return work_id, required_state


def event_lifecycle_state(events: dict[str, dict[str, Any]], work_id: str) -> str | None:
    event = events.get(work_id)
    if not event:
        return None
    return EVENT_STATE.get(event.get("event_type"))


def historical_completed_step_ids(
    data: dict[str, Any],
    spec: dict[str, Any],
    raw_steps: list[Any],
) -> set[str]:
    # Explicit accepted legacy completion IDs; never infer from steps[].state.
    if not spec.get("historical_completion_evidence_allowed"):
        return set()
    if not str(data.get("status", "")).startswith("completed_"):
        raise ReconciliationError("HISTORICAL_COMPLETION_EVIDENCE_STATUS_INVALID")

    evidence = data.get("historical_completion_evidence")
    if not isinstance(evidence, dict):
        raise ReconciliationError("HISTORICAL_COMPLETION_EVIDENCE_MISSING")
    if evidence.get("schema_version") != "forprint_legacy_roadmap_completion_evidence_v0_1":
        raise ReconciliationError("HISTORICAL_COMPLETION_EVIDENCE_SCHEMA_INVALID")
    if evidence.get("authority") != "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE":
        raise ReconciliationError("HISTORICAL_COMPLETION_EVIDENCE_AUTHORITY_INVALID")
    if evidence.get("step_state_fields_retired") is not True:
        raise ReconciliationError("HISTORICAL_STEP_STATE_RETIREMENT_NOT_DECLARED")

    completed = evidence.get("completed_step_ids")
    if (
        not isinstance(completed, list)
        or not completed
        or not all(isinstance(value, str) for value in completed)
        or len(set(completed)) != len(completed)
    ):
        raise ReconciliationError("HISTORICAL_COMPLETION_EVIDENCE_STEP_SET_INVALID")

    roadmap_step_ids = [
        row.get("id")
        for row in raw_steps
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    ]
    if completed != roadmap_step_ids:
        raise ReconciliationError("HISTORICAL_COMPLETION_EVIDENCE_STEP_SET_MISMATCH")
    if any("state" in row for row in raw_steps if isinstance(row, dict)):
        raise ReconciliationError("HISTORICAL_MANUAL_EXECUTION_STATE_STILL_PRESENT")

    return set(completed)


def normalize_roadmap(
    root: Path,
    roadmap_id: str,
    spec: dict[str, Any],
    events: dict[str, dict[str, Any]],
    latest_event_sequence: int,
) -> dict[str, Any]:
    path = root / spec["path"]
    if not path.is_file():
        return {
            "roadmap_id": roadmap_id,
            "roadmap_path": spec["path"],
            "sync_state": "UNKNOWN",
            "reason_codes": ["ROADMAP_SPEC_MISSING"],
            "latest_event_sequence": latest_event_sequence,
            "steps": [],
        }

    data = load_yaml(path)
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        return {
            "roadmap_id": roadmap_id,
            "roadmap_path": spec["path"],
            "roadmap_sha256": sha256(path),
            "sync_state": "UNKNOWN",
            "reason_codes": ["ROADMAP_STEPS_MISSING"],
            "latest_event_sequence": latest_event_sequence,
            "steps": [],
        }

    historical_completed = historical_completed_step_ids(data, spec, raw_steps)
    historical_accepted = bool(historical_completed)

    reason_codes: list[str] = []
    info_codes: list[str] = []
    steps: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_work: dict[str, str] = {}

    for raw in raw_steps:
        if not isinstance(raw, dict):
            reason_codes.append("ROADMAP_STEP_INVALID")
            continue
        step_id = raw.get("id")
        order = raw.get("order")
        if not isinstance(step_id, str) or not isinstance(order, int):
            reason_codes.append("ROADMAP_STEP_ID_OR_ORDER_INVALID")
            continue
        if step_id in seen_ids:
            reason_codes.append("DUPLICATE_STEP_ID")
        seen_ids.add(step_id)

        work_id = raw.get(spec["work_field"])
        if work_id is not None and not isinstance(work_id, str):
            reason_codes.append("ROADMAP_STEP_WORK_BINDING_INVALID")
            work_id = None

        if isinstance(work_id, str):
            if work_id in seen_work:
                if historical_accepted and spec.get("historical_shared_work_bindings_allowed"):
                    info_codes.append("HISTORICAL_SHARED_WORK_BINDING_USED")
                else:
                    reason_codes.append("DUPLICATE_WORK_BINDING")
            else:
                seen_work[work_id] = step_id

        deps = normalize_dependencies(raw.get("depends_on"))
        for dep in deps:
            if dep == step_id:
                reason_codes.append("SELF_DEPENDENCY")

        event = events.get(work_id) if work_id else None
        observed_event_state = EVENT_STATE.get(event.get("event_type")) if event else None
        lifecycle_state = observed_event_state
        evidence_mode = "EVENT_STORE" if event else None

        if historical_accepted and step_id in historical_completed:
            if lifecycle_state != "CLOSED":
                lifecycle_state = "CLOSED"
                evidence_mode = "LEGACY_PRE_ENFORCEMENT_ACCEPTED_HISTORY"
                info_codes.append("HISTORICAL_PRE_ENFORCEMENT_EVIDENCE_USED")

        steps.append(
            {
                "order": order,
                "step_id": step_id,
                "work_id": work_id,
                "depends_on": deps,
                "lifecycle_state": lifecycle_state,
                "observed_event_lifecycle_state": observed_event_state,
                "evidence_mode": evidence_mode,
                "event_id": event.get("event_id") if event else None,
                "event_sequence": int(event.get("sequence") or 0) if event else None,
            }
        )

    steps.sort(key=lambda row: (row["order"], row["step_id"]))
    if len({row["order"] for row in steps}) != len(steps):
        reason_codes.append("DUPLICATE_STEP_ORDER")

    by_id = {row["step_id"]: row for row in steps}
    for row in steps:
        for dep in row["depends_on"]:
            if dep in by_id:
                continue
            if external_lifecycle_dependency(dep) is None:
                reason_codes.append("DEPENDENCY_STEP_MISSING")

    for row in steps:
        state = row["lifecycle_state"]
        if state == "CLOSED":
            row["derived_state"] = "COMPLETE"
        elif state in OPEN_EXECUTION_STATES:
            row["derived_state"] = state
        else:
            row["derived_state"] = "PENDING"

    def dependency_complete(dep: str) -> bool:
        internal = by_id.get(dep)
        if internal is not None:
            return internal.get("derived_state") == "COMPLETE"
        external = external_lifecycle_dependency(dep)
        if external is None:
            return False
        work_id, required_state = external
        return event_lifecycle_state(events, work_id) == required_state

    # Fixed-point pass makes dependency closure deterministic even if a future roadmap
    # contains a dependency whose listed order is not strictly earlier.
    for _ in range(len(steps) + 1):
        changed = False
        for row in steps:
            deps_complete = all(dependency_complete(dep) for dep in row["depends_on"])
            if row.get("dependencies_complete") != deps_complete:
                row["dependencies_complete"] = deps_complete
                changed = True
            if row["lifecycle_state"] is None:
                new_state = (
                    "READY_UNBOUND"
                    if deps_complete and row["work_id"] is None
                    else "READY_FOR_PLAN"
                    if deps_complete
                    else "BLOCKED_UNBOUND"
                    if row["work_id"] is None
                    else "BLOCKED"
                )
                if row["derived_state"] != new_state:
                    row["derived_state"] = new_state
                    changed = True
        if not changed:
            break

    active_rows = [row for row in steps if row["derived_state"] in OPEN_EXECUTION_STATES]
    if len(active_rows) > int(spec.get("manual_wip_limit", 1)):
        reason_codes.append("MULTIPLE_ACTIVE_WORK_VIOLATES_WIP_POLICY")

    for row in steps:
        if row["derived_state"] == "COMPLETE" and not row["dependencies_complete"]:
            reason_codes.append("CLOSED_STEP_WITH_OPEN_REQUIRED_PREDECESSOR")

    current = active_rows[0]["step_id"] if active_rows else None
    complete_rows = [row for row in steps if row["derived_state"] == "COMPLETE"]
    previous = complete_rows[-1]["step_id"] if complete_rows else None

    next_row = None
    if current is not None:
        current_order = by_id[current]["order"]
        next_row = next((row for row in steps if row["order"] > current_order), None)
    else:
        next_row = next(
            (
                row
                for row in steps
                if row["derived_state"]
                in {"READY_UNBOUND", "READY_FOR_PLAN", "BLOCKED", "BLOCKED_UNBOUND"}
            ),
            None,
        )

    ready_candidates = [
        row["step_id"]
        for row in steps
        if row["derived_state"] in {"READY_UNBOUND", "READY_FOR_PLAN"}
    ]

    blocker_codes = sorted(set(reason_codes))
    conflict_codes = {
        "DUPLICATE_WORK_BINDING",
        "DUPLICATE_STEP_ID",
        "DUPLICATE_STEP_ORDER",
        "DEPENDENCY_STEP_MISSING",
        "SELF_DEPENDENCY",
        "MULTIPLE_ACTIVE_WORK_VIOLATES_WIP_POLICY",
        "CLOSED_STEP_WITH_OPEN_REQUIRED_PREDECESSOR",
    }
    if conflict_codes.intersection(blocker_codes):
        sync_state = "EXECUTION_CONFLICT"
    elif blocker_codes:
        sync_state = "UNKNOWN"
    else:
        sync_state = "IN_SYNC"

    return {
        "schema_version": "forprint_roadmap_execution_status_v0_1",
        "roadmap_id": roadmap_id,
        "roadmap_path": spec["path"],
        "roadmap_sha256": sha256(path),
        "latest_event_sequence": latest_event_sequence,
        "sync_state": sync_state,
        "reason_codes": blocker_codes,
        "informational_codes": sorted(set(info_codes)),
        "previous_step": previous,
        "current_step": current,
        "next_step": next_row["step_id"] if next_row else None,
        "next_step_state": next_row["derived_state"] if next_row else None,
        "next_ready_step": ready_candidates[0] if ready_candidates else None,
        "ready_candidates": ready_candidates,
        "next_activation": "REQUIRES_OPERATOR",
        "steps": steps,
    }


def compute(
    root: Path,
    *,
    event_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    events, latest_sequence = load_events(root, event_root=event_root)
    roadmaps = [
        normalize_roadmap(root, roadmap_id, spec, events, latest_sequence)
        for roadmap_id, spec in ROADMAPS.items()
    ]
    states = [row["sync_state"] for row in roadmaps]
    if "EXECUTION_CONFLICT" in states:
        overall = "EXECUTION_CONFLICT"
    elif "UNKNOWN" in states:
        overall = "UNKNOWN"
    else:
        overall = "IN_SYNC"

    execution = {
        "schema_version": "forprint_roadmap_execution_status_set_v0_1",
        "authority": "generated_non_authoritative_projection",
        "actual_execution_authority": "coordination/continuity/events",
        "manual_activation_required": True,
        "latest_event_sequence": latest_sequence,
        "roadmaps": roadmaps,
    }
    reconciliation = {
        "schema_version": "forprint_roadmap_reconciliation_status_v0_1",
        "authority": "generated_non_authoritative_projection",
        "roadmap_sync": overall,
        "latest_event_sequence": latest_sequence,
        "observed_roadmap_sha256": {
            row["roadmap_id"]: row.get("roadmap_sha256") for row in roadmaps
        },
        "reason_codes": sorted({code for row in roadmaps for code in row.get("reason_codes", [])}),
        "manual_mode": True,
        "auto_next_step_activation_allowed": False,
        "auto_plan_rewrite_allowed": False,
        "worker_dispatch_authority": False,
        "release_authority": False,
    }
    return execution, reconciliation


def dump_yaml(value: dict[str, Any]) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def sync(root: Path) -> int:
    execution, reconciliation = compute(root)
    write_atomic(root / EXECUTION_PROJECTION, dump_yaml(execution))
    write_atomic(root / RECONCILIATION_PROJECTION, dump_yaml(reconciliation))
    print("ROADMAP_SYNC=" + reconciliation["roadmap_sync"])
    print("LATEST_EVENT_SEQUENCE=" + str(reconciliation["latest_event_sequence"]))
    print("MUTATION_SCOPE=GENERATED_PROJECTIONS_ONLY")
    print("AUTO_ACTIVATION_PERFORMED=false")
    return 0 if reconciliation["roadmap_sync"] == "IN_SYNC" else 2


def check(root: Path) -> int:
    execution, reconciliation = compute(root)
    execution_path = root / EXECUTION_PROJECTION
    reconciliation_path = root / RECONCILIATION_PROJECTION
    if not execution_path.is_file() or not reconciliation_path.is_file():
        print("ROADMAP_SYNC=PROJECTION_STALE")
        print("REASON=PROJECTION_MISSING")
        print("MUTATION_PERFORMED=false")
        return 2

    actual_execution = load_yaml(execution_path)
    actual_reconciliation = load_yaml(reconciliation_path)
    if actual_execution != execution or actual_reconciliation != reconciliation:
        print("ROADMAP_SYNC=PROJECTION_STALE")
        print("REASON=PROJECTION_CONTENT_BEHIND_CANONICAL_INPUTS")
        print("LATEST_EVENT_SEQUENCE=" + str(reconciliation["latest_event_sequence"]))
        print("MUTATION_PERFORMED=false")
        return 2

    print("ROADMAP_SYNC=" + reconciliation["roadmap_sync"])
    print("LATEST_EVENT_SEQUENCE=" + str(reconciliation["latest_event_sequence"]))
    print("MUTATION_PERFORMED=false")
    return 0 if reconciliation["roadmap_sync"] == "IN_SYNC" else 3


def status(root: Path) -> int:
    execution, reconciliation = compute(root)
    print("ROADMAP_SYNC=" + reconciliation["roadmap_sync"])
    print("LATEST_EVENT_SEQUENCE=" + str(reconciliation["latest_event_sequence"]))
    for row in execution["roadmaps"]:
        print(
            "ROADMAP_STATUS="
            + row["roadmap_id"]
            + ":previous="
            + str(row["previous_step"])
            + ":current="
            + str(row["current_step"])
            + ":next="
            + str(row["next_step"])
            + ":ready="
            + str(row["next_ready_step"])
        )
    print("MUTATION_PERFORMED=false")
    return 0 if reconciliation["roadmap_sync"] == "IN_SYNC" else 3


def gate(
    root: Path,
    *,
    action: str,
    roadmap_id: str | None,
    step_id: str | None,
    work_id: str | None,
    front: str | None = None,
) -> int:
    if check(root) != 0:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=ROADMAP_NOT_IN_SYNC")
        return 4

    constitution_validator = root / "scripts/validation/validate_project_constitution_v0_1.py"
    if not constitution_validator.is_file():
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=PROJECT_CONSTITUTION_INVALID")
        print("CONSTITUTION_ERROR=VALIDATOR_MISSING")
        return 4
    constitution_check = __import__("subprocess").run(
        [__import__("sys").executable, str(constitution_validator), "--contract-only"],
        cwd=root,
        text=True,
        stdout=__import__("subprocess").PIPE,
        stderr=__import__("subprocess").STDOUT,
        check=False,
    )
    if constitution_check.returncode:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=PROJECT_CONSTITUTION_INVALID")
        print(constitution_check.stdout, end="")
        return 4
    print("PROJECT_CONSTITUTION_GATE=PASS")

    execution, _ = compute(root)
    by_roadmap = {row["roadmap_id"]: row for row in execution["roadmaps"]}

    if action in {"assistant-pack", "dispatch"}:
        work_front_runtime = root / "scripts/coordination/work_front_v0_1.py"
        work_front_contract = (
            root / "coordination/standards/automation/work_front_contract_v0_1.yaml"
        )
        if not work_front_runtime.is_file() or not work_front_contract.is_file():
            print("ROADMAP_GATE=BLOCKED")
            print("GATE_REASON=WORK_FRONT_CONTRACT_INVALID")
            return 4
        if action == "dispatch" and not front:
            print("ROADMAP_GATE=BLOCKED")
            print("GATE_REASON=WORK_FRONT_REQUIRED")
            return 4
        if front:
            front_check = __import__("subprocess").run(
                [
                    __import__("sys").executable,
                    str(work_front_runtime),
                    "--root",
                    str(root),
                    "--front",
                    front,
                    "--action",
                    action,
                ],
                cwd=root,
                text=True,
                stdout=__import__("subprocess").PIPE,
                stderr=__import__("subprocess").STDOUT,
                check=False,
            )
            if front_check.returncode:
                print("ROADMAP_GATE=BLOCKED")
                print("GATE_REASON=WORK_FRONT_INVALID")
                print(front_check.stdout, end="")
                return 4
            print(front_check.stdout, end="")
            print("WORK_FRONT_GATE=PASS")
        else:
            print("WORK_FRONT_GATE=NOT_APPLICABLE_PROJECT_ONBOARD_COMPAT")

    if action == "assistant-pack":
        print("ROADMAP_GATE=PASS")
        print("ACTION=" + action)
        return 0

    if action == "dispatch":
        print("ROADMAP_GATE=PASS_RECONCILIATION")
        print("DISPATCH_AUTHORITY=false")
        print("ROADMAP_GATE=BLOCKED_AUTHORITY")
        return 5

    if roadmap_id not in by_roadmap or not step_id or not work_id:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=ROADMAP_STEP_WORK_REQUIRED")
        return 4

    roadmap = by_roadmap[roadmap_id]
    step = next((row for row in roadmap["steps"] if row["step_id"] == step_id), None)
    if step is None:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=STEP_NOT_FOUND")
        return 4
    if step["work_id"] != work_id:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=WORK_NOT_BOUND_TO_STEP")
        return 4
    if not step["dependencies_complete"]:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=DEPENDENCIES_NOT_COMPLETE")
        return 4

    if action in {"plan", "activate"}:
        other_open = [
            row
            for row in roadmap["steps"]
            if row["work_id"] != work_id and row["derived_state"] in OPEN_EXECUTION_STATES
        ]
        if other_open:
            print("ROADMAP_GATE=BLOCKED")
            print("GATE_REASON=WIP_POLICY_BLOCKED")
            print(
                "OPEN_WORK="
                + ",".join(
                    str(row["work_id"]) for row in other_open if row.get("work_id") is not None
                )
            )
            return 4

    allowed = False
    if action == "plan":
        allowed = step["lifecycle_state"] in {None, "PLANNED"}
    elif action == "activate":
        allowed = step["lifecycle_state"] == "PLANNED"
    elif action == "checkpoint":
        allowed = step["lifecycle_state"] == "ACTIVE"
    elif action == "close":
        allowed = step["lifecycle_state"] == "VALIDATED"
    else:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=UNSUPPORTED_ACTION")
        return 4

    if not allowed:
        print("ROADMAP_GATE=BLOCKED")
        print("GATE_REASON=LIFECYCLE_STATE_NOT_ALLOWED")
        print("OBSERVED_LIFECYCLE_STATE=" + str(step["lifecycle_state"]))
        return 4

    print("ROADMAP_GATE=PASS")
    print("ACTION=" + action)
    print("ROADMAP_ID=" + roadmap_id)
    print("STEP_ID=" + step_id)
    print("WORK_ID=" + work_id)
    print("AUTO_ACTIVATION_PERFORMED=false")
    return 0


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--root", default=".")
    sub = value.add_subparsers(dest="command", required=True)
    sub.add_parser("sync")
    sub.add_parser("check")
    sub.add_parser("status")
    gate_parser = sub.add_parser("gate")
    gate_parser.add_argument(
        "--action",
        required=True,
        choices=[
            "plan",
            "activate",
            "checkpoint",
            "close",
            "assistant-pack",
            "dispatch",
        ],
    )
    gate_parser.add_argument("--roadmap-id")
    gate_parser.add_argument("--step-id")
    gate_parser.add_argument("--work-id")
    gate_parser.add_argument("--front")
    return value


def main() -> int:
    args = parser().parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "sync":
            return sync(root)
        if args.command == "check":
            return check(root)
        if args.command == "status":
            return status(root)
        return gate(
            root,
            action=args.action,
            roadmap_id=args.roadmap_id,
            step_id=args.step_id,
            work_id=args.work_id,
            front=args.front,
        )
    except (OSError, yaml.YAMLError, ReconciliationError) as exc:
        print("ROADMAP_SYNC=UNKNOWN")
        print("ERROR=" + f"{type(exc).__name__}: {exc}")
        print("MUTATION_PERFORMED=false")
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
