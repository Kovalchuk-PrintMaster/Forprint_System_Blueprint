#!/usr/bin/env python3
# Explicit Blueprint adapter over portable continuity core.

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination import build_assistant_handoff_archive as handoff  # noqa: E402
from scripts.coordination import build_continuity_projections as portable  # noqa: E402
from scripts.coordination import roadmap_execution_reconciliation as reconciliation  # noqa: E402

CONTROL_FOUNDATION_ROADMAP_ID = "control_foundation_near_horizon"

BLUEPRINT_CONTROL_FOUNDATION_ROADMAP = Path(
    "coordination/roadmaps/details/forprint_system_blueprint/"
    "control_foundation_near_horizon_program_v0_1.yaml"
)
BLUEPRINT_STRATEGIC_VECTOR_MD = Path(
    "coordination/global_policy/strategic_transition_vector_v0_1.md"
)
BLUEPRINT_STRATEGIC_VECTOR_YAML = Path(
    "coordination/global_policy/strategic_transition_vector_v0_1.yaml"
)
BLUEPRINT_ARCHITECTURE_HORIZON_MD = Path(
    "coordination/global_policy/architecture_improvement_horizon_v0_1.md"
)
BLUEPRINT_ARCHITECTURE_HORIZON_YAML = Path(
    "coordination/global_policy/architecture_improvement_horizon_v0_1.yaml"
)
BLUEPRINT_PROJECT_ONBOARD_CANONICAL_SOURCES = (
    BLUEPRINT_CONTROL_FOUNDATION_ROADMAP,
    BLUEPRINT_STRATEGIC_VECTOR_MD,
    BLUEPRINT_STRATEGIC_VECTOR_YAML,
    BLUEPRINT_ARCHITECTURE_HORIZON_MD,
    BLUEPRINT_ARCHITECTURE_HORIZON_YAML,
)


class BlueprintContinuityAdapterError(RuntimeError):
    pass


def next_horizon(
    root: Path = ROOT,
    *,
    event_root: Path | None = None,
) -> dict[str, Any]:
    execution, sync = reconciliation.compute(root, event_root=event_root)

    sync_state = sync.get("roadmap_sync")
    if sync_state != "IN_SYNC":
        raise BlueprintContinuityAdapterError(
            "BLUEPRINT_NEXT_HORIZON_ROADMAP_NOT_IN_SYNC="
            + str(sync_state)
        )

    roadmaps = execution.get("roadmaps")
    if not isinstance(roadmaps, list):
        raise BlueprintContinuityAdapterError(
            "BLUEPRINT_ROADMAP_EXECUTION_SET_MISSING"
        )

    roadmap = next(
        (
            row
            for row in roadmaps
            if isinstance(row, dict)
            and row.get("roadmap_id") == CONTROL_FOUNDATION_ROADMAP_ID
        ),
        None,
    )
    if not isinstance(roadmap, dict):
        raise BlueprintContinuityAdapterError(
            "BLUEPRINT_CONTROL_FOUNDATION_CURSOR_MISSING"
        )

    steps = roadmap.get("steps")
    if not isinstance(steps, list):
        raise BlueprintContinuityAdapterError(
            "BLUEPRINT_CONTROL_FOUNDATION_STEPS_MISSING"
        )

    current_step = roadmap.get("current_step")
    next_step = roadmap.get("next_step")
    next_ready_step = roadmap.get("next_ready_step")
    ready_candidates = roadmap.get("ready_candidates")
    if not isinstance(ready_candidates, list):
        ready_candidates = []

    remaining = [
        row
        for row in steps
        if isinstance(row, dict)
        and row.get("derived_state") != "COMPLETE"
    ]
    remaining.sort(
        key=lambda row: (
            int(row.get("order") or 0),
            str(row.get("step_id") or ""),
        )
    )

    selected = remaining[:10]
    if not 5 <= len(selected) <= 10:
        raise BlueprintContinuityAdapterError(
            "BLUEPRINT_NEXT_HORIZON_COUNT_OUT_OF_CONTRACT="
            + str(len(selected))
        )

    actions: list[dict[str, Any]] = []
    for position, row in enumerate(selected, start=1):
        step_id = row.get("step_id")
        relation = "UPCOMING"

        if step_id == current_step:
            relation = "CURRENT"
        elif step_id == next_step:
            relation = "NEXT"
        elif step_id == next_ready_step:
            relation = "NEXT_READY"
        elif step_id in ready_candidates:
            relation = "READY"
        elif str(row.get("derived_state", "")).startswith("BLOCKED"):
            relation = "BLOCKED_FUTURE"

        actions.append(
            {
                "order": position,
                "id": step_id,
                "roadmap_order": row.get("order"),
                "relation": relation,
                "derived_state": row.get("derived_state"),
                "lifecycle_state": row.get("lifecycle_state"),
                "work_id": row.get("work_id"),
                "dependencies_complete": row.get("dependencies_complete"),
            }
        )

    return {
        "derivation_mode": (
            "blueprint_roadmap_execution_reconciliation_cursor"
        ),
        "authority_source": (
            "roadmap_spec_plus_continuity_event_store_via_"
            "roadmap_execution_reconciliation"
        ),
        "portable_mode": False,
        "current_operational_horizon": True,
        "roadmap_id": CONTROL_FOUNDATION_ROADMAP_ID,
        "roadmap_sync": sync_state,
        "source_latest_event_sequence": roadmap.get("latest_event_sequence"),
        "source_roadmap_sha256": roadmap.get("roadmap_sha256"),
        "current_step": current_step,
        "next_step": next_step,
        "next_step_state": roadmap.get("next_step_state"),
        "next_ready_step": next_ready_step,
        "ready_candidates": ready_candidates,
        "action_count": len(actions),
        "actions": actions,
    }


def build_projection_documents(
    root: Path = ROOT,
    *,
    event_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    return portable.build_projection_documents(
        root,
        event_root=event_root,
        next_horizon=next_horizon(root, event_root=event_root),
    )


def check_projections(
    root: Path = ROOT,
    *,
    output_root: Path | None = None,
) -> tuple[bool, list[str]]:
    return portable.check_projections(
        root,
        output_root=output_root,
        next_horizon=next_horizon(root),
    )


def refresh_projections(
    root: Path = ROOT,
    *,
    output_root: Path | None = None,
) -> list[Path]:
    return portable.apply_projections(
        root,
        output_root=output_root,
        next_horizon=next_horizon(root),
    )


def expected_archive(
    root: Path = ROOT,
) -> tuple[bytes, dict[str, Any], str]:
    return handoff.expected_archive(
        root,
        projection_documents=build_projection_documents(root),
        project_onboard_sources=BLUEPRINT_PROJECT_ONBOARD_CANONICAL_SOURCES,
    )


def validate_handoff(root: Path = ROOT) -> None:
    blob1, manifest1, _name1 = expected_archive(root)
    blob2, manifest2, _name2 = expected_archive(root)
    if blob1 != blob2 or manifest1 != manifest2:
        raise BlueprintContinuityAdapterError(
            "BLUEPRINT_HANDOFF_NON_DETERMINISTIC"
        )


def write_handoff(root: Path = ROOT) -> Path:
    return handoff.write_archive(
        root,
        projection_documents=build_projection_documents(root),
        project_onboard_sources=BLUEPRINT_PROJECT_ONBOARD_CANONICAL_SOURCES,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-root", type=Path, default=None)

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--handoff-validate", action="store_true")
    mode.add_argument("--handoff-write", action="store_true")
    mode.add_argument("--status", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()

    try:
        if args.status:
            horizon = next_horizon(root)
            print("BLUEPRINT_CONTINUITY_ADAPTER=PASS")
            print("PORTABLE_MODE=false")
            print("CURRENT_OPERATIONAL_HORIZON=true")
            print("DERIVATION_MODE=" + horizon["derivation_mode"])
            print("CURRENT_STEP=" + str(horizon["current_step"]))
            print("NEXT_STEP=" + str(horizon["next_step"]))
            print("NEXT_READY_STEP=" + str(horizon["next_ready_step"]))
            print("ACTION_COUNT=" + str(horizon["action_count"]))
            print("MUTATION_PERFORMED=false")
            return 0

        if args.check:
            ok, errors = check_projections(
                root,
                output_root=args.output_root,
            )
            if not ok:
                print("BLUEPRINT_CONTINUITY_PROJECTIONS_CHECK=FAIL")
                for error in errors:
                    print("ERROR=" + error)
                print("MUTATION_PERFORMED=false")
                return 1

            print("BLUEPRINT_CONTINUITY_PROJECTIONS_CHECK=PASS")
            print("PORTABLE_MODE=false")
            print("CURRENT_OPERATIONAL_HORIZON=true")
            print("MUTATION_PERFORMED=false")
            return 0

        if args.refresh:
            written = refresh_projections(
                root,
                output_root=args.output_root,
            )
            print("BLUEPRINT_CONTINUITY_PROJECTIONS_APPLY=PASS")
            print("PORTABLE_MODE=false")
            print("CURRENT_OPERATIONAL_HORIZON=true")
            print("PROJECTION_COUNT=" + str(len(written)))
            return 0

        if args.handoff_validate:
            validate_handoff(root)
            print("BLUEPRINT_ASSISTANT_HANDOFF_COMPILER=PASS")
            print("PORTABLE_MODE=false")
            print("CURRENT_OPERATIONAL_HORIZON=true")
            print("VALIDATE_ONLY=true")
            print("MUTATION_PERFORMED=false")
            return 0

        target = write_handoff(root)
        print("BLUEPRINT_ASSISTANT_HANDOFF_WRITE=PASS")
        print("PORTABLE_MODE=false")
        print("CURRENT_OPERATIONAL_HORIZON=true")
        print("ARCHIVE=" + str(target))
        return 0

    except Exception as exc:
        print(
            "BLUEPRINT_CONTINUITY_ADAPTER=FAIL "
            + type(exc).__name__
            + ":"
            + str(exc)
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
