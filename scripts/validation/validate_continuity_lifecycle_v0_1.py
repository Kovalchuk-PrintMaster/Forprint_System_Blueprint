#!/usr/bin/env python3
"""Validate ForPrint continuity lifecycle enforcement v0.1."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.coordination.continuity_lifecycle import (  # noqa: E402
    LIFECYCLE_EVENT_TYPES,
    STATE_BY_EVENT_TYPE,
    UTC_Z_RE,
    _event_rows,
)
from scripts.validation.validate_continuity_event_store_v0_1 import (  # noqa: E402
    validate_store,
)

CONTRACT = ROOT / "coordination/standards/automation/continuity_contract_v0_1.yaml"
EVENT_ROOT = ROOT / "coordination/continuity/events"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(message: str) -> int:
    print(f"CONTINUITY_LIFECYCLE=FAIL {message}")
    return 1


def _contract(root: Path) -> dict[str, Any]:
    path = root / "coordination/standards/automation/continuity_contract_v0_1.yaml"
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("continuity contract must be a mapping")
    return value


def validate_lifecycle_semantics(
    *,
    root: Path,
    event_root: Path,
) -> tuple[bool, str, dict[str, Any]]:
    contract = _contract(root)
    lifecycle_contract = contract.get("lifecycle")
    event_model = contract.get("event_model")
    if not isinstance(lifecycle_contract, dict):
        return False, "contract_lifecycle_missing", {}
    if not isinstance(event_model, dict):
        return False, "contract_event_model_missing", {}

    enforcement = lifecycle_contract.get("enforcement")
    if not isinstance(enforcement, dict):
        return False, "contract_enforcement_missing", {}
    if enforcement.get("enabled") is not True:
        return False, "contract_enforcement_not_enabled", {}

    boundary = enforcement.get("pre_enforcement_boundary_sequence")
    boundary_event_id = enforcement.get("pre_enforcement_boundary_event_id")
    if not isinstance(boundary, int) or boundary < 1:
        return False, "invalid_pre_enforcement_boundary_sequence", {}
    if not isinstance(boundary_event_id, str) or not boundary_event_id:
        return False, "invalid_pre_enforcement_boundary_event_id", {}

    allowed_event_types = set(event_model.get("event_types", []))
    if not LIFECYCLE_EVENT_TYPES.issubset(allowed_event_types):
        return False, "contract_missing_lifecycle_event_types", {}

    rows = _event_rows(event_root)
    if len(rows) < boundary:
        return False, "event_store_shorter_than_enforcement_boundary", {}
    if rows[boundary - 1]["event"].get("event_id") != boundary_event_id:
        return False, "enforcement_boundary_event_id_mismatch", {}

    work_state: dict[str, str] = {}
    work_state_row: dict[str, dict[str, Any]] = {}
    latest_checkpoint_by_work: dict[str, dict[str, Any]] = {}
    latest_validation_by_work: dict[str, dict[str, Any]] = {}
    seen_work_ids: set[str] = set()

    for row in rows:
        event = row["event"]
        sequence = row["sequence"]
        event_type = event.get("event_type")
        work_id = event.get("work_id")

        if event_type not in allowed_event_types:
            return False, f"unknown_event_type={event_type}", {}
        for field in (
            "event_id",
            "event_type",
            "work_id",
            "occurred_at",
            "actor",
            "summary",
            "source_state_ref",
        ):
            if field not in event:
                return False, f"missing_common_field={sequence}:{field}", {}
        if not isinstance(work_id, str) or not work_id:
            return False, f"invalid_work_id={sequence}", {}
        prior_identity = work_id in seen_work_ids
        if not UTC_Z_RE.fullmatch(str(event.get("occurred_at", ""))):
            return False, f"occurred_at_not_utc_z={sequence}", {}
        source_ref = event.get("source_state_ref")
        if not isinstance(source_ref, str) or not HEX64_RE.fullmatch(source_ref):
            return False, f"invalid_source_state_ref={sequence}", {}

        prior_state = work_state.get(work_id)
        prior_row = work_state_row.get(work_id)

        if event_type == "CHECKPOINT_RECORDED":
            if event.get("bootstrap_historical_import") is True:
                if sequence > boundary:
                    return False, f"historical_import_post_boundary={work_id}", {}
                seen_work_ids.add(work_id)
                continue
            if sequence > boundary and prior_state != "ACTIVE":
                return (
                    False,
                    f"checkpoint_requires_active={work_id}:{prior_state}",
                    {},
                )
            work_state[work_id] = "CHECKPOINTED"
            work_state_row[work_id] = row
            latest_checkpoint_by_work[work_id] = row
            seen_work_ids.add(work_id)
            continue

        if event_type not in LIFECYCLE_EVENT_TYPES:
            continue

        payload = event.get("lifecycle")
        if not isinstance(payload, dict):
            return False, f"lifecycle_payload_missing={sequence}", {}
        to_state = STATE_BY_EVENT_TYPE[event_type]
        if payload.get("to_state") != to_state:
            return False, f"lifecycle_to_state={sequence}", {}

        if prior_state == "CLOSED":
            return False, f"closed_state_is_immutable={work_id}", {}

        if event_type == "WORK_PLANNED":
            if prior_identity:
                return False, f"plan_requires_unused_work_id={work_id}", {}
            if prior_state is not None:
                return False, f"plan_requires_no_state={work_id}", {}
            if payload.get("from_state") is not None:
                return False, f"plan_from_state={work_id}", {}

        elif event_type == "WORK_ACTIVATED":
            remediation = payload.get("remediation") is True
            if remediation and not str(payload.get("reason", "")).strip():
                return False, f"activate_remediation_reason={work_id}", {}
            expected = {"CHECKPOINTED", "VALIDATED"} if remediation else {"PLANNED"}
            if prior_state not in expected:
                return (
                    False,
                    f"activate_transition={work_id}:{prior_state}",
                    {},
                )
            if payload.get("from_state") != prior_state:
                return False, f"activate_from_state={work_id}", {}

        elif event_type == "VALIDATION_PASSED":
            if prior_state != "CHECKPOINTED":
                return False, f"validate_requires_checkpoint={work_id}", {}
            checkpoint_row = latest_checkpoint_by_work.get(work_id)
            if checkpoint_row is None or prior_row != checkpoint_row:
                return False, f"validation_checkpoint_order={work_id}", {}
            if payload.get("checkpoint_event_id") != checkpoint_row["event"].get("event_id"):
                return False, f"validation_checkpoint_ref={work_id}", {}
            if payload.get("checkpoint_event_sha256") != checkpoint_row["sha256"]:
                return False, f"validation_checkpoint_sha={work_id}", {}
            evidence = payload.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                return False, f"validation_evidence={work_id}", {}
            continuity = payload.get("continuity_validation")
            if (
                not isinstance(continuity, dict)
                or continuity.get("current_source_state_match") is not True
            ):
                return False, f"validation_continuity_gate={work_id}", {}
            current_fp = continuity.get("current_fingerprint")
            checkpoint_fp = continuity.get("checkpoint_fingerprint")
            if (
                not isinstance(current_fp, str)
                or not HEX64_RE.fullmatch(current_fp)
                or current_fp != checkpoint_fp
            ):
                return False, f"validation_continuity_fingerprint={work_id}", {}
            latest_validation_by_work[work_id] = row

        elif event_type == "VALIDATION_FAILED":
            if prior_state not in {"CHECKPOINTED", "VALIDATED"}:
                return False, f"validation_failed_transition={work_id}", {}
            if not str(payload.get("reason", "")).strip():
                return False, f"validation_failed_reason={work_id}", {}

        elif event_type == "WORK_CLOSED":
            if prior_state != "VALIDATED":
                return False, f"close_requires_validated={work_id}", {}
            checkpoint_row = latest_checkpoint_by_work.get(work_id)
            validation_row = latest_validation_by_work.get(work_id)
            if checkpoint_row is None or validation_row is None:
                return False, f"close_evidence_chain={work_id}", {}
            if payload.get("checkpoint_event_id") != checkpoint_row["event"].get("event_id"):
                return False, f"close_checkpoint_ref={work_id}", {}
            if payload.get("validation_event_id") != validation_row["event"].get("event_id"):
                return False, f"close_validation_ref={work_id}", {}
            evidence = payload.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                return False, f"close_evidence={work_id}", {}
            gate = payload.get("close_gate")
            required_true = {
                "checkpoint_exists",
                "latest_checkpoint_validation_passed",
                "continuity_validation_passed",
                "current_source_delta_reconciled",
            }
            if not isinstance(gate, dict):
                return False, f"close_gate_missing={work_id}", {}
            for key in required_true:
                if gate.get(key) is not True:
                    return False, f"close_gate_{key}={work_id}", {}
            current_fp = gate.get("current_fingerprint")
            checkpoint_fp = gate.get("checkpoint_fingerprint")
            if (
                not isinstance(current_fp, str)
                or not HEX64_RE.fullmatch(current_fp)
                or current_fp != checkpoint_fp
            ):
                return False, f"close_fingerprint={work_id}", {}
            blocker_count = gate.get("blocker_count")
            if not isinstance(blocker_count, int) or blocker_count < 0:
                return False, f"close_blocker_count={work_id}", {}
            if blocker_count and gate.get("blockers_explicitly_deferred") is not True:
                return False, f"close_blocker_deferral={work_id}", {}

        elif event_type == "WORK_SUPERSEDED":
            if payload.get("migration_only") is not True:
                return False, f"supersede_not_migration={work_id}", {}
            if not str(payload.get("reason", "")).strip():
                return False, f"supersede_reason={work_id}", {}
            if prior_state != "CHECKPOINTED" or prior_row is None:
                return False, f"supersede_state={work_id}:{prior_state}", {}
            if prior_row["sequence"] > boundary:
                return False, f"supersede_post_boundary={work_id}", {}
            if payload.get("enforcement_boundary_sequence") != boundary:
                return False, f"supersede_boundary={work_id}", {}
            replacement = payload.get("superseded_by_work_id")
            if not isinstance(replacement, str) or not replacement or replacement == work_id:
                return False, f"supersede_replacement={work_id}", {}

        work_state[work_id] = to_state
        work_state_row[work_id] = row
        seen_work_ids.add(work_id)

    return (
        True,
        "PASS",
        {
            "boundary_sequence": boundary,
            "boundary_event_id": boundary_event_id,
            "event_count": len(rows),
            "work_states": {key: work_state[key] for key in sorted(work_state)},
            "closed_work_ids": sorted(
                key for key, value in work_state.items() if value == "CLOSED"
            ),
            "open_work_ids": sorted(key for key, value in work_state.items() if value != "CLOSED"),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--event-root", type=Path, default=None)
    parser.add_argument(
        "--require-current-state-match",
        action="store_true",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    event_root = (
        args.event_root.resolve()
        if args.event_root is not None
        else root / "coordination/continuity/events"
    )

    store_ok, store_reason, _ = validate_store(
        root=root,
        event_root=event_root,
        require_current_state_match=args.require_current_state_match,
    )
    if not store_ok:
        return fail(f"event_store:{store_reason}")

    try:
        ok, reason, details = validate_lifecycle_semantics(
            root=root,
            event_root=event_root,
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return fail(f"{type(exc).__name__}:{exc}")
    if not ok:
        return fail(reason)

    print("CONTINUITY_LIFECYCLE=PASS")
    print(f"ENFORCEMENT_BOUNDARY_SEQUENCE={details['boundary_sequence']}")
    print(f"ENFORCEMENT_BOUNDARY_EVENT_ID={details['boundary_event_id']}")
    print(f"EVENT_COUNT={details['event_count']}")
    print("CLOSED_WORK_IDS=" + ",".join(details["closed_work_ids"]))
    print("OPEN_WORK_IDS=" + ",".join(details["open_work_ids"]))
    print("ACTIVE_TO_CLOSED_FORBIDDEN=true")
    print("CLOSED_STATE_IMMUTABLE=true")
    print("CLOSE_REQUIRES_RECONCILED_SOURCE=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
