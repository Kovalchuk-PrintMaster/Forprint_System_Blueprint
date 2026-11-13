#!/usr/bin/env python3
"""Validate CF-10 isolated workspace + Dispatcher preflight Slice 3."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.control_plane.workspace import plan_workspace  # noqa: E402

SLICE_FRONT = (
    "coordination/work_fronts/"
    "cf10_isolated_workspace_dispatch_preflight_v0_1.yaml"
)
FIRST_WORKER_FRONT = (
    "coordination/work_fronts/"
    "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
)
TASK_ID = "cf10-zero-stage-dispatch-boundary-regression-v0-1"

DISPATCH_SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
spec = importlib.util.spec_from_file_location("_cf10_dispatch_intent", DISPATCH_SOURCE)
assert spec is not None and spec.loader is not None
dispatch_intent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch_intent
spec.loader.exec_module(dispatch_intent)


def main() -> int:
    try:
        front = yaml.safe_load((ROOT / SLICE_FRONT).read_text(encoding="utf-8"))
        if front["work_front_id"] != "wf-cf10-isolated-workspace-dispatch-preflight-v0-1":
            raise RuntimeError("Slice 3 Work Front mismatch")

        plan = plan_workspace(
            canonical_repo=ROOT,
            runtime_root="/srv/software_development/forprint-worker-runtime",
            module_id="forprint_system_blueprint",
            worker_id="worker-01",
            attempt_id="cf10-zero-stage-preflight-plan",
        )
        if plan.layout.attempt_root.exists():
            print("LIVE_ATTEMPT_PATH_ALREADY_EXISTS=true")
        else:
            print("LIVE_ATTEMPT_PATH_ALREADY_EXISTS=false")

        if plan.base_mode != "DETACHED_LOCAL_CLONE":
            raise RuntimeError("workspace base mode mismatch")
        if plan.overlay_mode != "CONTINUITY_DURABLE_DIRTY_PATHS":
            raise RuntimeError("workspace overlay mode mismatch")
        if not plan.source_head:
            raise RuntimeError("workspace plan source HEAD missing")

        prepared = dispatch_intent.prepare_cf09_task_execution(
            root=ROOT,
            work_front=FIRST_WORKER_FRONT,
            execution_profile="light-maintenance",
            task_prompt_id=TASK_ID,
            task_module_root=".",
            module="forprint_system_blueprint",
            procedure_id="governed_canonical_mutation",
        )
        if prepared.get("state") != "AWAITING_ASSISTANT_ACK":
            raise RuntimeError(
                "Dispatcher preflight must stop at AWAITING_ASSISTANT_ACK"
            )
        if prepared.get("assistant_ack_validated") is not False:
            raise RuntimeError("Assistant ACK unexpectedly validated")
        if prepared.get("next_required_human_boundary") != "ASSISTANT_ACK_REQUIRED":
            raise RuntimeError("Dispatcher human boundary mismatch")

        authority = prepared.get("authority")
        if not isinstance(authority, dict):
            raise RuntimeError("prepared authority mapping missing")
        for key in (
            "execution_authority_granted",
            "dispatch_authority_granted",
            "worker_dispatch_performed",
            "external_dispatch_allowed",
            "release_allowed",
            "push_allowed",
            "merge_allowed",
        ):
            if authority.get(key) is not False:
                raise RuntimeError(f"preflight authority widened: {key}")

        print("CF10_ISOLATED_WORKSPACE_DISPATCH_PREFLIGHT_VALIDATION=PASS")
        print("WORKSPACE_PLAN_MODE=NO_WRITE")
        print("WORKSPACE_BASE_MODE=DETACHED_LOCAL_CLONE")
        print("WORKSPACE_OVERLAY_MODE=CONTINUITY_DURABLE_DIRTY_PATHS")
        print(f"SOURCE_HEAD={plan.source_head}")
        print(f"DURABLE_DIRTY_PATH_COUNT={len(plan.durable_dirty_paths)}")
        print("LIVE_WORKSPACE_PROVISIONING_PERFORMED=false")
        print("DISPATCH_PREFLIGHT_STATE=AWAITING_ASSISTANT_ACK")
        print("ASSISTANT_ACK_VALIDATED=false")
        print("DISPATCH_AUTHORITY_GRANTED=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        return 0
    except Exception as exc:
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("CF10_ISOLATED_WORKSPACE_DISPATCH_PREFLIGHT_VALIDATION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
