from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "coordination/registry/execution_dependency_registry_v0_1.yaml"
MAKEFILE = ROOT / "Makefile"


def load_registry() -> dict:
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def test_roadmap_reconciliation_projections_are_persistent_derived() -> None:
    registry = load_registry()
    artifacts = {row["id"]: row for row in registry["artifacts"]}
    for artifact_id in (
        "roadmap_execution_status_projection",
        "roadmap_reconciliation_status_projection",
    ):
        row = artifacts[artifact_id]
        assert row["class"] == "derived_persistent"
        assert row["authority"] == "none"
        assert row["lifecycle"] == "durable_generated"
        assert row["freshness"] == "exact_source_fingerprint"
        assert row["missing_behavior"] == "fail_with_explicit_refresh"
        assert row["producer"] == "roadmap-sync"


def test_control_foundation_program_is_explicit_controller_input() -> None:
    registry = load_registry()
    artifacts = {row["id"]: row for row in registry["artifacts"]}
    row = artifacts["control_foundation_near_horizon_program"]
    assert row["class"] == "canonical_required"
    assert row["authority"] == "canonical_planning_not_execution_authority"
    assert row["lifecycle"] == "durable_canonical"
    assert row["freshness"] == "durable_current"
    assert row["producer"] is None


def test_sync_and_check_depend_on_both_registered_roadmaps() -> None:
    registry = load_registry()
    targets = {row["target"]: row for row in registry["targets"]}
    required_inputs = {
        "assistant_handoff_execution_roadmap",
        "control_foundation_near_horizon_program",
        "continuity_event_store",
        "roadmap_execution_reconciliation_contract",
    }
    assert required_inputs <= set(targets["roadmap-sync"]["requires"])
    assert required_inputs <= set(targets["roadmap-sync-check"]["requires"])
    assert {
        "roadmap_execution_status_projection",
        "roadmap_reconciliation_status_projection",
    } <= set(targets["roadmap-sync-check"]["requires"])


def test_non_mutating_check_does_not_directly_depend_on_mutating_sync() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    check_line = next(
        line for line in makefile.splitlines() if line.startswith("roadmap-sync-check:")
    )
    assert "roadmap-sync" not in check_line.split()[1:]

    check_core = next(line for line in makefile.splitlines() if line.startswith("check-core:"))
    assert "roadmap-sync-check" in check_core.split()
    assert "roadmap-sync" not in check_core.split()


def test_root_surface_keeps_non_mutating_reconciliation_gate() -> None:
    registry = load_registry()
    root = next(row for row in registry["root_surfaces"] if row["target"] == "check-core")
    assert "roadmap-sync-check" in root["requires_targets"]
    assert "roadmap-sync" not in root["requires_targets"]


def test_roadmap_projection_artifacts_use_dedicated_namespace() -> None:
    registry = load_registry()
    artifacts = {row["id"]: row for row in registry["artifacts"]}
    assert artifacts["roadmap_execution_status_projection"]["path"] == (
        "coordination/roadmap_execution/projections/ROADMAP_EXECUTION_STATUS.yaml"
    )
    assert artifacts["roadmap_reconciliation_status_projection"]["path"] == (
        "coordination/roadmap_execution/projections/ROADMAP_RECONCILIATION_STATUS.yaml"
    )
