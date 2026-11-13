#!/usr/bin/env python3
"""Build deterministic non-authoritative continuity projections v0.1."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.continuity import (  # noqa: E402
    build_source_state,
    event_files,
    read_event,
    sha256_file,
)

EVENT_ROOT = ROOT / "coordination/continuity/events"
OUTPUT_ROOT = ROOT / "coordination/continuity/projections"
SCHEMA_VERSION = "forprint_continuity_projection_v0_1"

PROJECTION_IDS = (
    "CURRENT_WORKFRONT",
    "RECENT_ACTIVITY",
    "DECISIONS",
    "BLOCKERS",
    "NEXT_HORIZON",
    "SOURCE_STATE",
    "WORKER_PORTFOLIO",
    "UNRECONCILED_CURRENT_DELTA",
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


class ProjectionError(RuntimeError):
    pass


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def _event_rows(event_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in event_files(event_root):
        event = read_event(path)
        rows.append(
            {
                "path": path,
                "sha256": sha256_file(path),
                "event": event,
            }
        )
    if not rows:
        raise ProjectionError("continuity event store is empty")
    return rows


def _latest_checkpoint(rows: list[dict[str, Any]]) -> dict[str, Any]:
    matches = [row for row in rows if row["event"].get("event_type") == "CHECKPOINT_RECORDED"]
    if not matches:
        raise ProjectionError("no checkpoint event exists")
    return matches[-1]


def _state_delta(
    checkpoint_state: dict[str, Any],
    current_state: dict[str, Any],
) -> dict[str, Any]:
    expected_paths = set(checkpoint_state.get("durable_dirty_paths", []))
    current_paths = set(current_state.get("durable_dirty_paths", []))

    added = sorted(current_paths - expected_paths)
    removed = sorted(expected_paths - current_paths)

    expected_status = checkpoint_state.get("dirty_path_status", {})
    current_status = current_state.get("dirty_path_status", {})
    expected_content = checkpoint_state.get(
        "dirty_path_content_or_symlink_fingerprint",
        {},
    )
    current_content = current_state.get(
        "dirty_path_content_or_symlink_fingerprint",
        {},
    )

    changed: list[str] = []
    for rel in sorted(expected_paths & current_paths):
        if expected_status.get(rel) != current_status.get(rel) or expected_content.get(
            rel
        ) != current_content.get(rel):
            changed.append(rel)

    head_changed = checkpoint_state.get("git_head") != current_state.get("git_head")
    branch_changed = checkpoint_state.get("git_branch") != current_state.get("git_branch")
    fingerprint_match = checkpoint_state.get("fingerprint_sha256") == current_state.get(
        "fingerprint_sha256"
    )
    material = bool(
        added or removed or changed or head_changed or branch_changed or not fingerprint_match
    )
    return {
        "material": material,
        "checkpoint_fingerprint": checkpoint_state.get("fingerprint_sha256"),
        "current_fingerprint": current_state.get("fingerprint_sha256"),
        "head_changed": head_changed,
        "branch_changed": branch_changed,
        "added_paths": added,
        "removed_paths": removed,
        "changed_paths": changed,
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
    }


def _latest_state_per_work(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        event = row["event"]
        work_id = event.get("work_id")
        if not isinstance(work_id, str) or not work_id:
            continue
        state = STATE_BY_EVENT_TYPE.get(event.get("event_type"))
        if state is None:
            continue
        latest[work_id] = {
            "work_id": work_id,
            "lifecycle_state": state,
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "occurred_at": event.get("occurred_at"),
            "summary": event.get("summary"),
            "bootstrap_historical_import": bool(event.get("bootstrap_historical_import", False)),
        }
    return latest


def _basis(
    rows: list[dict[str, Any]],
    latest_checkpoint: dict[str, Any],
    current_state: dict[str, Any],
) -> dict[str, Any]:
    latest = rows[-1]
    latest_event = latest["event"]
    checkpoint_event = latest_checkpoint["event"]
    return {
        "event_count": len(rows),
        "latest_event_id": latest_event.get("event_id"),
        "latest_event_sha256": latest["sha256"],
        "latest_checkpoint_id": checkpoint_event.get("event_id"),
        "latest_checkpoint_sha256": latest_checkpoint["sha256"],
        "latest_checkpoint_source_state_ref": checkpoint_event.get("source_state_ref"),
        "current_source_state_fingerprint": current_state.get("fingerprint_sha256"),
    }


# NEXT_HORIZON_PORTABLE_INJECTION_V0_1
def _portable_checkpoint_horizon(
    checkpoint_event: dict[str, Any],
    checkpoint: dict[str, Any],
) -> dict[str, Any]:
    # Portable mode preserves checkpoint intent without claiming current Blueprint authority.
    actions = checkpoint.get("next_actions")
    if not isinstance(actions, list) or not 5 <= len(actions) <= 10:
        raise ProjectionError(
            "latest checkpoint next_actions must contain five to ten actions"
        )

    return {
        "derivation_mode": "checkpoint_next_actions_portable_compatibility",
        "authority_source": "checkpoint_historical_intent_snapshot",
        "portable_mode": True,
        "current_operational_horizon": False,
        "source_checkpoint_event_id": checkpoint_event.get("event_id"),
        "action_count": len(actions),
        "actions": actions,
    }


def _validated_injected_horizon(
    value: dict[str, Any],
) -> dict[str, Any]:
    # Non-portable operational horizon must be supplied explicitly.
    if not isinstance(value, dict):
        raise ProjectionError("injected NEXT_HORIZON must be a mapping")
    if value.get("portable_mode") is not False:
        raise ProjectionError(
            "injected NEXT_HORIZON must declare portable_mode=false"
        )
    if value.get("current_operational_horizon") is not True:
        raise ProjectionError(
            "injected NEXT_HORIZON must declare current_operational_horizon=true"
        )

    for key in ("derivation_mode", "authority_source"):
        if not isinstance(value.get(key), str) or not value.get(key):
            raise ProjectionError(f"injected NEXT_HORIZON {key} missing")

    actions = value.get("actions")
    if not isinstance(actions, list) or not 5 <= len(actions) <= 10:
        raise ProjectionError(
            "injected NEXT_HORIZON actions must contain five to ten actions"
        )
    if value.get("action_count") != len(actions):
        raise ProjectionError("injected NEXT_HORIZON action_count mismatch")

    return dict(value)


def build_projection_documents(
    root: Path = ROOT,
    *,
    event_root: Path | None = None,
    next_horizon: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    root = root.resolve()
    events = (
        event_root.resolve() if event_root is not None else root / "coordination/continuity/events"
    )
    rows = _event_rows(events)
    checkpoint_row = _latest_checkpoint(rows)
    checkpoint_event = checkpoint_row["event"]
    checkpoint = checkpoint_event.get("checkpoint")
    if not isinstance(checkpoint, dict):
        raise ProjectionError("latest checkpoint payload is not a mapping")

    final_hashes = checkpoint.get("final_applied_artifact_hashes")
    if not isinstance(final_hashes, dict) or not final_hashes:
        raise ProjectionError("latest checkpoint final hashes are missing")

    current_state = build_source_state(
        root,
        bounded_final_applied_artifact_hashes=final_hashes,
    )
    checkpoint_state = checkpoint.get("source_state_after")
    if not isinstance(checkpoint_state, dict):
        raise ProjectionError("latest checkpoint source_state_after missing")

    delta = _state_delta(checkpoint_state, current_state)
    basis = _basis(rows, checkpoint_row, current_state)
    status = (
        "derived_non_authoritative_current"
        if not delta["material"]
        else "derived_non_authoritative_unreconciled"
    )

    latest_by_work = _latest_state_per_work(rows)
    active_work = [
        row
        for _, row in sorted(latest_by_work.items())
        if row["lifecycle_state"] != "CLOSED" and not row["bootstrap_historical_import"]
    ]
    historical_excluded = sum(
        1 for row in latest_by_work.values() if row["bootstrap_historical_import"]
    )

    recent = []
    for row in reversed(rows[-20:]):
        event = row["event"]
        recent.append(
            {
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "work_id": event.get("work_id"),
                "occurred_at": event.get("occurred_at"),
                "summary": event.get("summary"),
                "event_sha256": row["sha256"],
                "bootstrap_historical_import": bool(
                    event.get("bootstrap_historical_import", False)
                ),
            }
        )

    decisions = []
    for row in reversed(rows):
        event = row["event"]
        checkpoint_payload = event.get("checkpoint")
        if not isinstance(checkpoint_payload, dict):
            continue
        decisions.append(
            {
                "event_id": event.get("event_id"),
                "work_id": event.get("work_id"),
                "occurred_at": event.get("occurred_at"),
                "decision_rationale": checkpoint_payload.get("decision_rationale"),
                "rejected_alternative_when_material": (
                    checkpoint_payload.get("rejected_alternative_when_material")
                ),
            }
        )
        if len(decisions) >= 20:
            break

    latest_checkpoint_by_work: dict[str, dict[str, Any]] = {}
    for row in rows:
        event = row["event"]
        checkpoint_payload = event.get("checkpoint")
        work_id = event.get("work_id")
        if isinstance(checkpoint_payload, dict) and isinstance(work_id, str):
            latest_checkpoint_by_work[work_id] = event

    blockers = []
    for work_id, event in sorted(latest_checkpoint_by_work.items()):
        state = latest_by_work.get(work_id, {}).get("lifecycle_state")
        if state == "CLOSED":
            continue
        checkpoint_payload = event["checkpoint"]
        for blocker in checkpoint_payload.get("blockers", []):
            blockers.append(
                {
                    "work_id": work_id,
                    "checkpoint_event_id": event.get("event_id"),
                    "blocker": blocker,
                }
            )

    horizon_payload = (
        _portable_checkpoint_horizon(checkpoint_event, checkpoint)
        if next_horizon is None
        else _validated_injected_horizon(next_horizon)
    )

    common = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "authority": "none",
        "generated_only": True,
        "manual_edit_forbidden": True,
        "basis": basis,
    }

    documents = {
        "CURRENT_WORKFRONT": {
            **common,
            "projection_id": "CURRENT_WORKFRONT",
            "payload": {
                "active_work_count": len(active_work),
                "historical_import_work_count_excluded": historical_excluded,
                "work_items": active_work,
                "lifecycle_enforcement_pending": False,
                "lifecycle_enforcement_version": "v0_1",
            },
        },
        "RECENT_ACTIVITY": {
            **common,
            "projection_id": "RECENT_ACTIVITY",
            "payload": {
                "maximum_events": 20,
                "event_count": len(recent),
                "events": recent,
            },
        },
        "DECISIONS": {
            **common,
            "projection_id": "DECISIONS",
            "payload": {
                "maximum_decisions": 20,
                "decision_count": len(decisions),
                "decisions": decisions,
                "derivation_mode": "checkpoint_decision_rationale",
            },
        },
        "BLOCKERS": {
            **common,
            "projection_id": "BLOCKERS",
            "payload": {
                "unresolved_blocker_count": len(blockers),
                "blockers": blockers,
                "derivation_mode": "latest_checkpoint_per_open_work",
            },
        },
        "NEXT_HORIZON": {
            **common,
            "projection_id": "NEXT_HORIZON",
            "payload": horizon_payload,
        },
        "SOURCE_STATE": {
            **common,
            "projection_id": "SOURCE_STATE",
            "payload": {
                "source_mode": "working_tree",
                "checkpoint_fingerprint": checkpoint_state.get("fingerprint_sha256"),
                "current_fingerprint": current_state.get("fingerprint_sha256"),
                "current_matches_latest_checkpoint": not delta["material"],
                "checkpoint_git_head": checkpoint_state.get("git_head"),
                "current_git_head": current_state.get("git_head"),
                "checkpoint_git_branch": checkpoint_state.get("git_branch"),
                "current_git_branch": current_state.get("git_branch"),
                "current_durable_dirty_path_count": len(
                    current_state.get("durable_dirty_paths", [])
                ),
            },
        },
        "WORKER_PORTFOLIO": {
            **common,
            "projection_id": "WORKER_PORTFOLIO",
            "payload": {
                "worker_dispatch_authority": False,
                "workers_recorded": [],
                "work_packages": active_work,
                "worker_specific_event_model_implemented": False,
            },
        },
        "UNRECONCILED_CURRENT_DELTA": {
            **common,
            "projection_id": "UNRECONCILED_CURRENT_DELTA",
            "payload": {
                **delta,
                "blocks_closed_state_when_material": True,
                "may_be_material_during_active_work": True,
            },
        },
    }
    return documents


def render_projection(document: dict[str, Any]) -> str:
    return yaml.dump(
        document,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    )


def expected_rendered(
    root: Path = ROOT,
    *,
    event_root: Path | None = None,
    next_horizon: dict[str, Any] | None = None,
) -> dict[str, str]:
    documents = build_projection_documents(
        root,
        event_root=event_root,
        next_horizon=next_horizon,
    )
    return {
        projection_id: render_projection(documents[projection_id])
        for projection_id in PROJECTION_IDS
    }


def _unexpected_yaml(output_root: Path) -> list[str]:
    expected = {f"{projection_id}.yaml" for projection_id in PROJECTION_IDS}
    return sorted(path.name for path in output_root.glob("*.yaml") if path.name not in expected)


def apply_projections(
    root: Path = ROOT,
    *,
    output_root: Path | None = None,
    next_horizon: dict[str, Any] | None = None,
) -> list[Path]:
    root = root.resolve()
    target_root = (
        output_root.resolve()
        if output_root is not None
        else root / "coordination/continuity/projections"
    )
    target_root.mkdir(parents=True, exist_ok=True)

    unexpected = _unexpected_yaml(target_root)
    if unexpected:
        raise ProjectionError("unexpected projection YAML files: " + ",".join(unexpected))

    rendered = expected_rendered(root, next_horizon=next_horizon)
    staged: list[tuple[Path, Path]] = []
    try:
        for projection_id in PROJECTION_IDS:
            target = target_root / f"{projection_id}.yaml"
            temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            temporary.write_text(
                rendered[projection_id],
                encoding="utf-8",
            )
            staged.append((temporary, target))

        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _target in staged:
            if temporary.exists():
                temporary.unlink()

    return [target_root / f"{projection_id}.yaml" for projection_id in PROJECTION_IDS]


def check_projections(
    root: Path = ROOT,
    *,
    output_root: Path | None = None,
    next_horizon: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    root = root.resolve()
    target_root = (
        output_root.resolve()
        if output_root is not None
        else root / "coordination/continuity/projections"
    )
    rendered = expected_rendered(root, next_horizon=next_horizon)
    errors: list[str] = []

    if not target_root.is_dir():
        errors.append(f"missing projection root: {target_root.relative_to(root)}")
        return False, errors

    unexpected = _unexpected_yaml(target_root)
    if unexpected:
        errors.append("unexpected projection YAML: " + ",".join(unexpected))

    for projection_id in PROJECTION_IDS:
        target = target_root / f"{projection_id}.yaml"
        if not target.is_file():
            errors.append(f"missing={target.relative_to(root)}")
            continue
        if target.read_text(encoding="utf-8") != rendered[projection_id]:
            errors.append(f"stale={target.relative_to(root)}")

    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        if args.check:
            ok, errors = check_projections(
                args.root,
                output_root=args.output_root,
            )
            if not ok:
                print("CONTINUITY_PROJECTIONS_CHECK=FAIL")
                for error in errors:
                    print("ERROR=" + error)
                return 1
            print("CONTINUITY_PROJECTIONS_CHECK=PASS")
            print(f"PROJECTION_COUNT={len(PROJECTION_IDS)}")
            print("MUTATION_PERFORMED=false")
            return 0

        written = apply_projections(
            args.root,
            output_root=args.output_root,
        )
        print("CONTINUITY_PROJECTIONS_APPLY=PASS")
        print(f"PROJECTION_COUNT={len(written)}")
        for path in written:
            try:
                display = path.relative_to(args.root.resolve())
            except ValueError:
                display = path
            print(f"PROJECTION={display}")
        return 0
    except (OSError, ValueError, yaml.YAMLError, ProjectionError) as exc:
        print(f"CONTINUITY_PROJECTIONS=FAIL {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
