#!/usr/bin/env python3
"""ForPrint continuity lifecycle enforcement v0.1.

Lifecycle events share the accepted append-only continuity event stream.
This module enforces:
PLANNED -> ACTIVE -> CHECKPOINTED -> VALIDATED -> CLOSED,
plus explicit remediation CHECKPOINTED/VALIDATED -> ACTIVE.

It does not grant release, queue, worker-dispatch, foreign-module mutation,
or operator-approval authority.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.continuity import (  # noqa: E402
    EVENT_ID_RE,
    EVENT_NAME_RE,
    EVENT_SCHEMA,
    ContinuityError,
    build_source_state,
    event_files,
    read_event,
    sha256_bytes,
    sha256_file,
    yaml_bytes,
)

STATE_BY_EVENT_TYPE = {
    "WORK_PLANNED": "PLANNED",
    "WORK_ACTIVATED": "ACTIVE",
    "CHECKPOINT_RECORDED": "CHECKPOINTED",
    "VALIDATION_PASSED": "VALIDATED",
    "VALIDATION_FAILED": "ACTIVE",
    "WORK_CLOSED": "CLOSED",
    "WORK_SUPERSEDED": "CLOSED",
}
LIFECYCLE_EVENT_TYPES = {
    "WORK_PLANNED",
    "WORK_ACTIVATED",
    "VALIDATION_PASSED",
    "VALIDATION_FAILED",
    "WORK_CLOSED",
    "WORK_SUPERSEDED",
}
TRANSITION_EVENT_BY_TARGET = {
    "PLANNED": "WORK_PLANNED",
    "ACTIVE": "WORK_ACTIVATED",
    "VALIDATED": "VALIDATION_PASSED",
    "CLOSED": "WORK_CLOSED",
}
UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class LifecycleError(RuntimeError):
    pass


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _event_rows(event_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    previous_id: str | None = None
    previous_sha: str | None = None
    for expected_sequence, path in enumerate(event_files(event_root), start=1):
        match = EVENT_NAME_RE.fullmatch(path.name)
        if match is None:
            raise LifecycleError(f"invalid event filename: {path.name}")
        if int(match.group("sequence")) != expected_sequence:
            raise LifecycleError(f"event sequence gap: {path.name}")
        actual_sha = sha256_file(path)
        if actual_sha[:12] != match.group("sha"):
            raise LifecycleError(f"content address mismatch: {path.name}")
        event = read_event(path)
        if event.get("schema_version") != EVENT_SCHEMA:
            raise LifecycleError(f"event schema mismatch: {path.name}")
        if event.get("sequence") != expected_sequence:
            raise LifecycleError(f"embedded sequence mismatch: {path.name}")
        if event.get("event_id") != match.group("event_id"):
            raise LifecycleError(f"event id filename mismatch: {path.name}")
        if event.get("previous_event_id") != previous_id:
            raise LifecycleError(f"previous event id mismatch: {path.name}")
        if event.get("previous_event_sha256") != previous_sha:
            raise LifecycleError(f"previous event sha mismatch: {path.name}")
        rows.append(
            {
                "path": path,
                "sha256": actual_sha,
                "event": event,
                "sequence": expected_sequence,
            }
        )
        previous_id = str(event.get("event_id"))
        previous_sha = actual_sha
    return rows


def _latest_state(
    rows: list[dict[str, Any]],
    work_id: str,
) -> tuple[str | None, dict[str, Any] | None]:
    state: str | None = None
    state_row: dict[str, Any] | None = None
    for row in rows:
        event = row["event"]
        if event.get("work_id") != work_id:
            continue
        if event.get("bootstrap_historical_import") is True:
            continue
        mapped = STATE_BY_EVENT_TYPE.get(event.get("event_type"))
        if mapped is None:
            continue
        state = mapped
        state_row = row
    return state, state_row


def _roadmap_reconciliation_installation(root: Path) -> tuple[Path, Path] | None:
    contract = (
        root / "coordination/standards/automation/"
        "roadmap_execution_reconciliation_contract_v0_1.yaml"
    )
    controller = root / "scripts/coordination/roadmap_execution_reconciliation.py"
    if not contract.exists() and not controller.exists():
        return None
    if not contract.is_file() or not controller.is_file():
        raise LifecycleError(
            "roadmap reconciliation installation is partial; lifecycle transition blocked"
        )
    return contract, controller


def _roadmap_reconciliation_root_from_event_root(event_root: Path) -> Path | None:
    resolved = event_root.resolve()
    candidates = [resolved, *resolved.parents]
    for candidate in candidates:
        contract = (
            candidate / "coordination/standards/automation/"
            "roadmap_execution_reconciliation_contract_v0_1.yaml"
        )
        controller = candidate / "scripts/coordination/roadmap_execution_reconciliation.py"
        if contract.exists() or controller.exists():
            return candidate
    return None


def _load_roadmap_reconciliation_controller(controller: Path):
    spec = importlib.util.spec_from_file_location(
        "_forprint_runtime_roadmap_execution_reconciliation",
        controller,
    )
    if spec is None or spec.loader is None:
        raise LifecycleError("roadmap reconciliation controller cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_roadmap_reconciliation_gate(
    *,
    root: Path | None,
    action: str,
    work_id: str,
) -> bool:
    """Fail closed through the installed roadmap reconciliation gate.

    A standalone portable continuity core without the reconciliation controller keeps
    its historical portability behavior. Once either reconciliation component exists,
    the installation must be complete and the gate must pass.
    """

    if root is None:
        return False
    installation = _roadmap_reconciliation_installation(root)
    if installation is None:
        return False
    _contract, controller = installation
    module = _load_roadmap_reconciliation_controller(controller)

    execution, _reconciliation = module.compute(root)
    bindings: list[tuple[str, str]] = []
    for roadmap in execution.get("roadmaps", []):
        roadmap_id = roadmap.get("roadmap_id")
        for step in roadmap.get("steps", []):
            if step.get("work_id") == work_id:
                step_id = step.get("step_id")
                if isinstance(roadmap_id, str) and isinstance(step_id, str):
                    bindings.append((roadmap_id, step_id))

    if len(bindings) != 1:
        raise LifecycleError(
            "roadmap reconciliation requires exactly one work binding; "
            f"work_id={work_id} bindings={bindings}"
        )

    roadmap_id, step_id = bindings[0]
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        return_code = module.gate(
            root,
            action=action,
            roadmap_id=roadmap_id,
            step_id=step_id,
            work_id=work_id,
        )
    if return_code != 0:
        detail = output.getvalue().strip().replace("\n", " | ")
        raise LifecycleError(
            "roadmap reconciliation gate blocked: "
            f"action={action} work_id={work_id} detail={detail}"
        )
    return True


def assert_checkpoint_allowed(
    *,
    event_root: Path,
    work_id: str,
) -> None:
    rows = _event_rows(event_root)
    state, _state_row = _latest_state(rows, work_id)
    if state != "ACTIVE":
        raise LifecycleError(f"CHECKPOINT_RECORDED requires ACTIVE; current={state}")
    _assert_roadmap_reconciliation_gate(
        root=_roadmap_reconciliation_root_from_event_root(event_root),
        action="checkpoint",
        work_id=work_id,
    )


def _latest_checkpoint(
    rows: list[dict[str, Any]],
    work_id: str | None = None,
) -> dict[str, Any] | None:
    result: dict[str, Any] | None = None
    for row in rows:
        event = row["event"]
        if event.get("event_type") != "CHECKPOINT_RECORDED":
            continue
        if work_id is not None and event.get("work_id") != work_id:
            continue
        result = row
    return result


def _latest_validation_pass(
    rows: list[dict[str, Any]],
    work_id: str,
) -> dict[str, Any] | None:
    result: dict[str, Any] | None = None
    for row in rows:
        event = row["event"]
        if event.get("work_id") == work_id and event.get("event_type") == "VALIDATION_PASSED":
            result = row
    return result


def _current_matches_checkpoint(
    root: Path,
    checkpoint_row: dict[str, Any],
) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    event = checkpoint_row["event"]
    checkpoint = event.get("checkpoint")
    if not isinstance(checkpoint, dict):
        raise LifecycleError("work checkpoint payload missing")
    expected = checkpoint.get("source_state_after")
    hashes = checkpoint.get("final_applied_artifact_hashes")
    if not isinstance(expected, dict) or not isinstance(hashes, dict):
        raise LifecycleError("work checkpoint source state incomplete")
    current = build_source_state(
        root,
        bounded_final_applied_artifact_hashes={
            str(key): str(value) for key, value in hashes.items()
        },
    )
    return (
        current.get("fingerprint_sha256") == expected.get("fingerprint_sha256"),
        current,
        expected,
    )


def _append_event(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    event_type: str,
    work_id: str,
    actor: str,
    summary: str,
    lifecycle: dict[str, Any],
    occurred_at: str | None = None,
) -> Path:
    if not EVENT_ID_RE.fullmatch(event_id):
        raise LifecycleError(f"invalid event_id: {event_id!r}")
    if event_type not in LIFECYCLE_EVENT_TYPES:
        raise LifecycleError(f"unsupported lifecycle event type: {event_type}")
    if not work_id.strip():
        raise LifecycleError("work_id must be non-empty")
    if not actor.strip():
        raise LifecycleError("actor must be non-empty")
    if not summary.strip():
        raise LifecycleError("summary must be non-empty")

    rows = _event_rows(event_root)
    existing_ids = {str(row["event"].get("event_id")) for row in rows}
    if event_id in existing_ids:
        raise LifecycleError(f"duplicate event_id: {event_id}")

    current_state = build_source_state(root)
    sequence = len(rows) + 1
    previous_id = rows[-1]["event"].get("event_id") if rows else None
    previous_sha = rows[-1]["sha256"] if rows else None
    timestamp = occurred_at or _now_z()
    if not UTC_Z_RE.fullmatch(timestamp):
        raise LifecycleError("occurred_at must be UTC Z timestamp")

    event: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA,
        "event_id": event_id,
        "event_type": event_type,
        "sequence": sequence,
        "previous_event_id": previous_id,
        "previous_event_sha256": previous_sha,
        "work_id": work_id,
        "occurred_at": timestamp,
        "actor": actor,
        "summary": summary,
        "source_state_ref": current_state["fingerprint_sha256"],
        "bootstrap_historical_import": False,
        "lifecycle": lifecycle,
    }

    payload = yaml_bytes(event)
    digest = sha256_bytes(payload)
    target = event_root / (f"{sequence:06d}__{event_id}__{digest[:12]}.yaml")
    event_root.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        target,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        raise
    return target


def plan(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    work_id: str,
    actor: str,
    summary: str,
    reason: str,
) -> Path:
    rows = _event_rows(event_root)
    if any(row["event"].get("work_id") == work_id for row in rows):
        state, _ = _latest_state(rows, work_id)
        raise LifecycleError(f"WORK_PLANNED requires unused work_id; current={state}")
    _assert_roadmap_reconciliation_gate(
        root=root,
        action="plan",
        work_id=work_id,
    )
    return _append_event(
        root=root,
        event_root=event_root,
        event_id=event_id,
        event_type="WORK_PLANNED",
        work_id=work_id,
        actor=actor,
        summary=summary,
        lifecycle={
            "from_state": None,
            "to_state": "PLANNED",
            "reason": reason,
            "evidence": [],
        },
    )


def activate(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    work_id: str,
    actor: str,
    summary: str,
    reason: str,
    remediation: bool = False,
) -> Path:
    if remediation and not reason.strip():
        raise LifecycleError("remediation activation requires explicit reason")
    rows = _event_rows(event_root)
    state, state_row = _latest_state(rows, work_id)
    allowed = {"PLANNED"} if not remediation else {"CHECKPOINTED", "VALIDATED"}
    if state not in allowed:
        raise LifecycleError(f"WORK_ACTIVATED invalid from {state}; allowed={sorted(allowed)}")
    if state == "CLOSED":
        raise LifecycleError("CLOSED work is immutable")
    if not remediation:
        _assert_roadmap_reconciliation_gate(
            root=root,
            action="activate",
            work_id=work_id,
        )
    return _append_event(
        root=root,
        event_root=event_root,
        event_id=event_id,
        event_type="WORK_ACTIVATED",
        work_id=work_id,
        actor=actor,
        summary=summary,
        lifecycle={
            "from_state": state,
            "to_state": "ACTIVE",
            "reason": reason,
            "remediation": remediation,
            "prior_event_id": (
                state_row["event"].get("event_id") if state_row is not None else None
            ),
            "evidence": [],
        },
    )


def validation_passed(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    work_id: str,
    actor: str,
    summary: str,
    evidence: list[str],
) -> Path:
    if not evidence:
        raise LifecycleError("VALIDATION_PASSED requires evidence")
    rows = _event_rows(event_root)
    state, state_row = _latest_state(rows, work_id)
    if state != "CHECKPOINTED":
        raise LifecycleError(f"VALIDATION_PASSED requires CHECKPOINTED; current={state}")
    checkpoint_row = _latest_checkpoint(rows, work_id)
    if checkpoint_row is None:
        raise LifecycleError("validation requires work checkpoint")
    if state_row is None or state_row["sequence"] != checkpoint_row["sequence"]:
        raise LifecycleError("latest work state is not its checkpoint")
    matched, current, expected = _current_matches_checkpoint(root, checkpoint_row)
    if not matched:
        raise LifecycleError("current source delta is unreconciled")
    return _append_event(
        root=root,
        event_root=event_root,
        event_id=event_id,
        event_type="VALIDATION_PASSED",
        work_id=work_id,
        actor=actor,
        summary=summary,
        lifecycle={
            "from_state": "CHECKPOINTED",
            "to_state": "VALIDATED",
            "checkpoint_event_id": checkpoint_row["event"].get("event_id"),
            "checkpoint_event_sha256": checkpoint_row["sha256"],
            "evidence": evidence,
            "continuity_validation": {
                "current_source_state_match": True,
                "current_fingerprint": current.get("fingerprint_sha256"),
                "checkpoint_fingerprint": expected.get("fingerprint_sha256"),
            },
        },
    )


def validation_failed(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    work_id: str,
    actor: str,
    summary: str,
    reason: str,
    evidence: list[str],
) -> Path:
    if not reason.strip():
        raise LifecycleError("VALIDATION_FAILED requires explicit reason")
    rows = _event_rows(event_root)
    state, state_row = _latest_state(rows, work_id)
    if state not in {"CHECKPOINTED", "VALIDATED"}:
        raise LifecycleError(f"VALIDATION_FAILED invalid from {state}")
    return _append_event(
        root=root,
        event_root=event_root,
        event_id=event_id,
        event_type="VALIDATION_FAILED",
        work_id=work_id,
        actor=actor,
        summary=summary,
        lifecycle={
            "from_state": state,
            "to_state": "ACTIVE",
            "reason": reason,
            "prior_event_id": (
                state_row["event"].get("event_id") if state_row is not None else None
            ),
            "evidence": evidence,
        },
    )


def close(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    work_id: str,
    actor: str,
    summary: str,
    evidence: list[str],
    defer_all_blockers: bool = False,
    defer_rationale: str = "",
) -> Path:
    if not evidence:
        raise LifecycleError("WORK_CLOSED requires evidence")
    rows = _event_rows(event_root)
    state, state_row = _latest_state(rows, work_id)
    if state != "VALIDATED":
        raise LifecycleError(f"WORK_CLOSED requires VALIDATED; current={state}")
    checkpoint_row = _latest_checkpoint(rows, work_id)
    validation_row = _latest_validation_pass(rows, work_id)
    if checkpoint_row is None or validation_row is None:
        raise LifecycleError("close requires checkpoint and validation pass")
    if validation_row["sequence"] <= checkpoint_row["sequence"]:
        raise LifecycleError("validation pass must follow checkpoint")
    if state_row is None or state_row["sequence"] != validation_row["sequence"]:
        raise LifecycleError("latest work state is not validation pass")

    checkpoint = checkpoint_row["event"].get("checkpoint")
    if not isinstance(checkpoint, dict):
        raise LifecycleError("work checkpoint payload missing")
    blockers = checkpoint.get("blockers")
    if not isinstance(blockers, list):
        raise LifecycleError("work checkpoint blockers must be a list")
    if blockers and not defer_all_blockers:
        raise LifecycleError("non-empty blockers require explicit --defer-all-blockers")
    if blockers and not defer_rationale.strip():
        raise LifecycleError("deferred blockers require --defer-rationale")

    matched, current, expected = _current_matches_checkpoint(root, checkpoint_row)
    if not matched:
        raise LifecycleError("current source delta is unreconciled")

    _assert_roadmap_reconciliation_gate(
        root=root,
        action="close",
        work_id=work_id,
    )

    return _append_event(
        root=root,
        event_root=event_root,
        event_id=event_id,
        event_type="WORK_CLOSED",
        work_id=work_id,
        actor=actor,
        summary=summary,
        lifecycle={
            "from_state": "VALIDATED",
            "to_state": "CLOSED",
            "checkpoint_event_id": checkpoint_row["event"].get("event_id"),
            "validation_event_id": validation_row["event"].get("event_id"),
            "evidence": evidence,
            "close_gate": {
                "checkpoint_exists": True,
                "latest_checkpoint_validation_passed": True,
                "continuity_validation_passed": True,
                "current_source_delta_reconciled": True,
                "current_fingerprint": current.get("fingerprint_sha256"),
                "checkpoint_fingerprint": expected.get("fingerprint_sha256"),
                "blocker_count": len(blockers),
                "blockers_explicitly_deferred": bool(blockers),
                "deferred_blockers": blockers if blockers else [],
                "defer_rationale": defer_rationale if blockers else "",
            },
        },
    )


def supersede_legacy(
    *,
    root: Path,
    event_root: Path,
    event_id: str,
    work_id: str,
    actor: str,
    summary: str,
    superseded_by_work_id: str,
    enforcement_boundary_sequence: int,
    reason: str,
) -> Path:
    if not reason.strip():
        raise LifecycleError("WORK_SUPERSEDED requires explicit reason")
    rows = _event_rows(event_root)
    state, state_row = _latest_state(rows, work_id)
    if state == "CLOSED":
        raise LifecycleError("CLOSED work is immutable")
    if state_row is None or state != "CHECKPOINTED":
        raise LifecycleError("legacy supersede requires CHECKPOINTED pre-enforcement work")
    if state_row["sequence"] > enforcement_boundary_sequence:
        raise LifecycleError("work is newer than lifecycle enforcement migration boundary")
    if not superseded_by_work_id.strip() or superseded_by_work_id == work_id:
        raise LifecycleError("invalid superseded_by_work_id")
    return _append_event(
        root=root,
        event_root=event_root,
        event_id=event_id,
        event_type="WORK_SUPERSEDED",
        work_id=work_id,
        actor=actor,
        summary=summary,
        lifecycle={
            "from_state": "CHECKPOINTED",
            "to_state": "CLOSED",
            "migration_only": True,
            "enforcement_boundary_sequence": enforcement_boundary_sequence,
            "superseded_by_work_id": superseded_by_work_id,
            "reason": reason,
            "evidence": [],
        },
    )


def work_states(event_root: Path) -> dict[str, dict[str, Any]]:
    rows = _event_rows(event_root)
    states: dict[str, dict[str, Any]] = {}
    for row in rows:
        event = row["event"]
        if event.get("bootstrap_historical_import") is True:
            continue
        work_id = event.get("work_id")
        mapped = STATE_BY_EVENT_TYPE.get(event.get("event_type"))
        if not isinstance(work_id, str) or mapped is None:
            continue
        states[work_id] = {
            "state": mapped,
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "sequence": row["sequence"],
        }
    return states


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--event-root",
        type=Path,
        default=None,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status")
    status.add_argument("--work-id", default=None)

    transition = sub.add_parser("transition")
    transition.add_argument(
        "--action",
        required=True,
        choices=(
            "plan",
            "activate",
            "validate-pass",
            "validate-fail",
            "close",
            "supersede-legacy",
        ),
    )
    transition.add_argument("--event-id", required=True)
    transition.add_argument("--work-id", required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--summary", required=True)
    transition.add_argument("--reason", default="")
    transition.add_argument("--evidence", action="append", default=[])
    transition.add_argument("--remediation", action="store_true")
    transition.add_argument("--defer-all-blockers", action="store_true")
    transition.add_argument("--defer-rationale", default="")
    transition.add_argument("--superseded-by-work-id", default="")
    transition.add_argument("--enforcement-boundary-sequence", type=int)

    args = parser.parse_args()
    root = args.root.resolve()
    event_root = (
        args.event_root.resolve()
        if args.event_root is not None
        else root / "coordination/continuity/events"
    )

    try:
        if args.command == "status":
            states = work_states(event_root)
            if args.work_id is not None:
                row = states.get(args.work_id)
                if row is None:
                    raise LifecycleError(f"work_id not found: {args.work_id}")
                print(yaml.safe_dump(row, sort_keys=False), end="")
            else:
                print(
                    yaml.safe_dump(
                        {"work_states": states},
                        sort_keys=False,
                    ),
                    end="",
                )
            return 0

        common = {
            "root": root,
            "event_root": event_root,
            "event_id": args.event_id,
            "work_id": args.work_id,
            "actor": args.actor,
            "summary": args.summary,
        }
        if args.action == "plan":
            target = plan(**common, reason=args.reason)
        elif args.action == "activate":
            target = activate(
                **common,
                reason=args.reason,
                remediation=args.remediation,
            )
        elif args.action == "validate-pass":
            target = validation_passed(
                **common,
                evidence=args.evidence,
            )
        elif args.action == "validate-fail":
            target = validation_failed(
                **common,
                reason=args.reason,
                evidence=args.evidence,
            )
        elif args.action == "close":
            target = close(
                **common,
                evidence=args.evidence,
                defer_all_blockers=args.defer_all_blockers,
                defer_rationale=args.defer_rationale,
            )
        elif args.action == "supersede-legacy":
            if args.enforcement_boundary_sequence is None:
                raise LifecycleError("supersede-legacy requires --enforcement-boundary-sequence")
            target = supersede_legacy(
                **common,
                superseded_by_work_id=args.superseded_by_work_id,
                enforcement_boundary_sequence=(args.enforcement_boundary_sequence),
                reason=args.reason,
            )
        else:
            raise LifecycleError(f"unsupported action: {args.action}")

        print("CONTINUITY_LIFECYCLE_TRANSITION=PASS")
        print(f"EVENT_PATH={target}")
        print(f"EVENT_SHA256={sha256_file(target)}")
        return 0
    except (OSError, ValueError, yaml.YAMLError, ContinuityError, LifecycleError) as exc:
        print(f"CONTINUITY_LIFECYCLE_TRANSITION=FAIL {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
