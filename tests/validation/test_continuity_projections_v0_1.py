from __future__ import annotations

import json
from pathlib import Path

import yaml

from scripts.coordination import blueprint_continuity_adapter_v0_1 as blueprint_adapter
from scripts.coordination import build_continuity_projections as projections
from scripts.coordination import continuity

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "coordination/continuity/projections"


def _state(
    *,
    fingerprint: str,
    head: str = "a" * 40,
    branch: str = "test",
    status: dict[str, str] | None = None,
    content: dict[str, dict] | None = None,
) -> dict:
    status = status or {}
    content = content or {}
    return {
        "fingerprint_sha256": fingerprint,
        "git_head": head,
        "git_branch": branch,
        "durable_dirty_paths": sorted(status),
        "dirty_path_status": status,
        "dirty_path_content_or_symlink_fingerprint": content,
    }


def test_state_delta_detects_and_clears_material_change() -> None:
    before = _state(fingerprint="1" * 64)
    same = _state(fingerprint="1" * 64)
    assert projections._state_delta(before, same)["material"] is False

    changed = _state(
        fingerprint="2" * 64,
        status={"AGENTS.md": " M"},
        content={
            "AGENTS.md": {
                "kind": "file",
                "sha256": "3" * 64,
                "bytes": 10,
            }
        },
    )
    delta = projections._state_delta(before, changed)
    assert delta["material"] is True
    assert delta["added_paths"] == ["AGENTS.md"]


def test_current_projection_set_is_exact_and_complete() -> None:
    ok, errors = blueprint_adapter.check_projections(ROOT)
    assert ok, errors
    expected = {f"{item}.yaml" for item in projections.PROJECTION_IDS}
    actual = {path.name for path in OUTPUT_ROOT.glob("*.yaml")}
    assert actual == expected


def test_projection_surfaces_are_non_authoritative() -> None:
    for projection_id in projections.PROJECTION_IDS:
        data = yaml.safe_load((OUTPUT_ROOT / f"{projection_id}.yaml").read_text(encoding="utf-8"))
        assert data["projection_id"] == projection_id
        assert data["authority"] == "none"
        assert data["generated_only"] is True
        assert data["manual_edit_forbidden"] is True


def test_next_horizon_is_bounded_to_five_through_ten_actions() -> None:
    data = yaml.safe_load((OUTPUT_ROOT / "NEXT_HORIZON.yaml").read_text(encoding="utf-8"))
    actions = data["payload"]["actions"]
    assert 5 <= len(actions) <= 10
    assert data["payload"]["action_count"] == len(actions)


def test_source_state_and_delta_projection_agree() -> None:
    source = yaml.safe_load((OUTPUT_ROOT / "SOURCE_STATE.yaml").read_text(encoding="utf-8"))
    delta = yaml.safe_load(
        (OUTPUT_ROOT / "UNRECONCILED_CURRENT_DELTA.yaml").read_text(encoding="utf-8")
    )
    assert source["payload"]["current_matches_latest_checkpoint"] is (
        not delta["payload"]["material"]
    )


def test_worker_portfolio_has_no_dispatch_authority() -> None:
    data = yaml.safe_load((OUTPUT_ROOT / "WORKER_PORTFOLIO.yaml").read_text(encoding="utf-8"))
    assert data["payload"]["worker_dispatch_authority"] is False
    assert data["payload"]["worker_specific_event_model_implemented"] is False


def test_isolated_validation_baseline_is_frozen_and_rebinds_final_hashes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("FORPRINT_NON_MUTATING_CHECK_ISOLATED", raising=False)
    monkeypatch.delenv("FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE", raising=False)
    monkeypatch.delenv("FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT", raising=False)

    before = continuity.build_source_state(
        ROOT,
        bounded_final_applied_artifact_hashes={"scripts/example.py": "1" * 64},
    )
    baseline_path = tmp_path / "source_state_baseline.json"
    baseline_path.write_text(
        json.dumps(before),
        encoding="utf-8",
    )

    monkeypatch.setenv("FORPRINT_NON_MUTATING_CHECK_ISOLATED", "1")
    monkeypatch.setenv(
        "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE",
        str(baseline_path),
    )
    monkeypatch.setenv(
        "FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT",
        str(ROOT),
    )

    rebound = continuity.build_source_state(
        ROOT,
        bounded_final_applied_artifact_hashes={"scripts/example.py": "2" * 64},
    )
    assert rebound["durable_dirty_paths"] == before["durable_dirty_paths"]
    assert rebound["dirty_path_status"] == before["dirty_path_status"]
    assert (
        rebound["dirty_path_content_or_symlink_fingerprint"]
        == before["dirty_path_content_or_symlink_fingerprint"]
    )
    assert rebound["bounded_final_applied_artifact_hashes"] == {"scripts/example.py": "2" * 64}
    assert rebound["fingerprint_sha256"] != before["fingerprint_sha256"]

def test_portable_next_horizon_stays_checkpoint_derived() -> None:
    documents = projections.build_projection_documents(ROOT)
    horizon = documents["NEXT_HORIZON"]["payload"]

    assert (
        horizon["derivation_mode"]
        == "checkpoint_next_actions_portable_compatibility"
    )
    assert (
        horizon["authority_source"]
        == "checkpoint_historical_intent_snapshot"
    )
    assert horizon["portable_mode"] is True
    assert horizon["current_operational_horizon"] is False
    assert "source_checkpoint_event_id" in horizon
    assert 5 <= horizon["action_count"] <= 10
    assert horizon["action_count"] == len(horizon["actions"])


def test_blueprint_next_horizon_uses_roadmap_execution_cursor() -> None:
    from scripts.coordination import (
        blueprint_continuity_adapter_v0_1 as blueprint_adapter,
    )
    from scripts.coordination import (
        roadmap_execution_reconciliation as roadmap_reconciliation,
    )

    documents = blueprint_adapter.build_projection_documents(ROOT)
    horizon = documents["NEXT_HORIZON"]["payload"]

    execution, reconciliation = roadmap_reconciliation.compute(ROOT)
    control = next(
        row
        for row in execution["roadmaps"]
        if row["roadmap_id"] == "control_foundation_near_horizon"
    )

    assert reconciliation["roadmap_sync"] == "IN_SYNC"
    assert (
        horizon["derivation_mode"]
        == "blueprint_roadmap_execution_reconciliation_cursor"
    )
    assert horizon["authority_source"] == (
        "roadmap_spec_plus_continuity_event_store_via_"
        "roadmap_execution_reconciliation"
    )
    assert horizon["portable_mode"] is False
    assert horizon["current_operational_horizon"] is True
    assert horizon["roadmap_id"] == "control_foundation_near_horizon"
    assert horizon["roadmap_sync"] == "IN_SYNC"
    assert (
        horizon["source_latest_event_sequence"]
        == control["latest_event_sequence"]
    )
    assert horizon["source_roadmap_sha256"] == control["roadmap_sha256"]
    assert horizon["current_step"] == control["current_step"]
    assert horizon["next_step"] == control["next_step"]
    assert horizon["next_step_state"] == control["next_step_state"]
    assert horizon["next_ready_step"] == control["next_ready_step"]
    assert horizon["ready_candidates"] == control["ready_candidates"]
    assert "source_checkpoint_event_id" not in horizon

    action_ids = [row["id"] for row in horizon["actions"]]
    remaining_ids = [
        row["step_id"]
        for row in control["steps"]
        if row["derived_state"] != "COMPLETE"
    ][:10]

    assert action_ids == remaining_ids
    assert horizon["action_count"] == len(action_ids)
    assert 5 <= horizon["action_count"] <= 10

