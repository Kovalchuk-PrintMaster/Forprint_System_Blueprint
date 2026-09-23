from pathlib import Path

import yaml

ROADMAP = Path("coordination/roadmaps/logistics_service.yaml")
REPORT = Path(
    "coordination/internal_work/blueprint/module_inventory/logistics_service/"
    "2026-09-08__logistics_service__semantic_roadmap_reconciliation_apply_v0_1.yaml"
)


def _roadmap() -> dict:
    return yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))


def _report() -> dict:
    return yaml.safe_load(REPORT.read_text(encoding="utf-8"))


def test_current_front_is_bootstrap_and_step_count_is_preserved() -> None:
    roadmap = _roadmap()
    assert roadmap["metadata"]["current_step_id"] == (
        "logistics_service_authority_lineage_and_module_bootstrap_v0_1"
    )
    assert len(roadmap["roadmap"]) == 33


def test_required_candidates_are_explicit_but_not_numbered_steps() -> None:
    report = _report()
    candidates = {row["capability"] for row in report["required_roadmap_candidates"]}
    assert candidates == {
        "meest_express_read_only_foundation",
        "degraded_survival_modes",
        "first_wave_end_to_end_pilot",
    }
    assert report["canonical_apply"]["numbered_steps_added"] == 0


def test_review_candidates_remain_noncanonical() -> None:
    report = _report()
    candidates = {row["capability"] for row in report["review_candidates"]}
    assert candidates == {
        "bolt_uber_provider_specific_adapters",
        "integration_gateway_handoff",
    }


def test_authority_boundaries_remain_closed() -> None:
    boundary = _report()["authority_boundaries"]
    assert boundary["prompt_release_performed"] is False
    assert boundary["worker_started"] is False
    assert boundary["human_accept_performed"] is False
    assert boundary["logistics_repository_write_performed"] is False
