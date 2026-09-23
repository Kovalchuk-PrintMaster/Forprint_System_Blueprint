#!/usr/bin/env python3
"""Validate generated continuity projections v0.1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.build_continuity_projections import (  # noqa: E402
    PROJECTION_IDS,
    SCHEMA_VERSION,
)

OUTPUT_ROOT = ROOT / "coordination/continuity/projections"


def fail(message: str) -> int:
    print("CONTINUITY_PROJECTIONS=FAIL")
    print("ERROR=" + message)
    return 1


def load_projection(projection_id: str) -> dict:
    path = OUTPUT_ROOT / f"{projection_id}.yaml"
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{projection_id} must be a mapping")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-reconciled", action="store_true")
    args = parser.parse_args()

    # Exact persisted-byte freshness is owned by the explicit Blueprint adapter
    # on Blueprint operator surfaces. This validator checks persisted projection
    # schema and cross-projection semantics without re-deriving NEXT_HORIZON.
    documents = {projection_id: load_projection(projection_id) for projection_id in PROJECTION_IDS}
    basis_values = []
    for projection_id, document in documents.items():
        if document.get("schema_version") != SCHEMA_VERSION:
            return fail(f"schema={projection_id}")
        if document.get("projection_id") != projection_id:
            return fail(f"projection_id={projection_id}")
        if document.get("authority") != "none":
            return fail(f"authority={projection_id}")
        if document.get("generated_only") is not True:
            return fail(f"generated_only={projection_id}")
        if document.get("manual_edit_forbidden") is not True:
            return fail(f"manual_edit={projection_id}")
        basis = document.get("basis")
        if not isinstance(basis, dict):
            return fail(f"basis={projection_id}")
        basis_values.append(basis)

    first_basis = basis_values[0]
    if any(basis != first_basis for basis in basis_values[1:]):
        return fail("basis_divergence")

    horizon = documents["NEXT_HORIZON"]["payload"]
    if not 5 <= horizon.get("action_count", 0) <= 10:
        return fail("next_horizon_bounds")
    if len(horizon.get("actions", [])) != horizon.get("action_count"):
        return fail("next_horizon_count")

    worker = documents["WORKER_PORTFOLIO"]["payload"]
    if worker.get("worker_dispatch_authority") is not False:
        return fail("worker_dispatch_authority")
    if worker.get("worker_specific_event_model_implemented") is not False:
        return fail("worker_event_model_claim")

    source = documents["SOURCE_STATE"]["payload"]
    delta = documents["UNRECONCILED_CURRENT_DELTA"]["payload"]
    reconciled = source.get("current_matches_latest_checkpoint")
    if reconciled is not (not delta.get("material")):
        return fail("source_delta_consistency")
    if delta.get("blocks_closed_state_when_material") is not True:
        return fail("delta_close_gate")
    if args.require_reconciled and not reconciled:
        return fail("current_source_state_unreconciled")

    workfront = documents["CURRENT_WORKFRONT"]["payload"]
    for row in workfront.get("work_items", []):
        if row.get("lifecycle_state") == "CLOSED":
            return fail("closed_work_in_current_workfront")
        if row.get("bootstrap_historical_import"):
            return fail("historical_import_in_current_workfront")

    blockers = documents["BLOCKERS"]["payload"]
    if blockers.get("unresolved_blocker_count") != len(blockers.get("blockers", [])):
        return fail("blocker_count")

    print("CONTINUITY_PROJECTIONS=PASS")
    print(f"PROJECTION_COUNT={len(PROJECTION_IDS)}")
    print("CURRENT_SOURCE_STATE_MATCH=" + str(bool(reconciled)).lower())
    print("UNRECONCILED_CURRENT_DELTA=" + str(bool(delta.get("material"))).lower())
    print(f"NEXT_HORIZON_ACTIONS={horizon.get('action_count')}")
    print("AUTHORITY=none")
    print("WORKER_DISPATCH_AUTHORITY=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
