from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"

WORKSTREAM_ID = "blueprint_coordination_protocol_revision_and_legacy_simplification_v0_1"
ACTIVE_ID = "blueprint_v0_4_completion_packet_v0_1"


def load_roadmap() -> dict:
    value = yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_protocol_revision_workstream_is_deferred_not_active() -> None:
    roadmap = load_roadmap()

    assert roadmap["metadata"]["current_step_id"] in {
        ACTIVE_ID,
        "blueprint_v0_4_completion_outbox_v0_1",
    }
    assert len(roadmap["steps"]) == 29

    assert all(
        step.get("step_id") != WORKSTREAM_ID for step in roadmap["steps"] if isinstance(step, dict)
    )

    matches = [
        item
        for item in roadmap["deferred_steps"]
        if isinstance(item, dict) and item.get("step_id") == WORKSTREAM_ID
    ]
    assert len(matches) == 1

    workstream = matches[0]
    assert workstream["status"] == "deferred"
    assert workstream["release_after"] == ("blueprint_inventory_operational_readiness_review_v0_1")


def test_protocol_revision_prefers_one_canonical_current_revision() -> None:
    roadmap = load_roadmap()
    workstream = next(
        item for item in roadmap["deferred_steps"] if item.get("step_id") == WORKSTREAM_ID
    )

    model = workstream["target_architecture"]["canonical_revision_model"]
    assert model["revision_field"] == "coordination_revision"
    assert model["one_active_revision"] is True
    assert model["legacy_runtime_fallback"] is False
    assert model["historical_revision_handling"] == ("recognition_and_migration_only")
    assert model["unknown_revision_behavior"] == ("classify_and_generate_upgrade_instruction")


def test_legacy_tools_are_isolated_only_after_audit() -> None:
    roadmap = load_roadmap()
    workstream = next(
        item for item in roadmap["deferred_steps"] if item.get("step_id") == WORKSTREAM_ID
    )

    legacy = workstream["target_architecture"]["legacy_isolation"]
    assert legacy["move_only_after_audit_and_consumer_check"] is True
    assert legacy["active_runtime_dependency_allowed"] is False
    assert legacy["candidate_roots"] == [
        "coordination/legacy/",
        "scripts/legacy/",
    ]

    migration = workstream["target_architecture"]["module_migration"]
    assert migration["blueprint_repairs_module_artifacts"] is False
    assert migration["module_upgrade_via_prompt"] is True
