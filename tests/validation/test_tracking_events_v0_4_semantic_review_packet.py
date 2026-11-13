from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / (
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_semantic_fidelity_review_packet_v0_1.yaml"
)


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_semantic_review_packet_is_complete_and_non_decisional() -> None:
    packet = load(PACKET)
    assert packet["metadata"]["state"] == "READY_FOR_OPERATOR_SEMANTIC_FIDELITY_DECISION"
    assert packet["assistant_review"]["result"] == "PASS_RECOMMENDED"
    assert packet["assistant_review"]["covered_source_obligations"] == 26
    assert packet["assistant_review"]["uncovered_source_obligations"] == 0
    assert packet["assistant_review"]["blocking_semantic_gaps"] == []

    items = packet["review_items"]
    assert len(items) == 26
    assert all(item["assistant_semantic_assessment"] == "COVERED" for item in items)
    assert all(item["mapped_target_obligation_ids"] for item in items)

    gate = packet["operator_gate"]
    assert gate["decision_required"] is True
    assert gate["decision"] is None
    assert gate["decision_recorded_automatically"] is False
    assert gate["tracking_events_lifecycle_acceptance_implied"] is False


def test_semantic_review_packet_preserves_hard_boundaries() -> None:
    boundaries = load(PACKET)["boundaries"]
    assert boundaries == {
        "module_repository_writes": False,
        "completion_packet_v0_4_fabricated_by_blueprint": False,
        "completion_outbox_v0_4_fabricated_by_blueprint": False,
        "tracking_events_acceptance_created": False,
        "dark_zone_audit_run": False,
        "global_v0_4_promotion_performed": False,
        "automatic_commit": False,
        "automatic_push": False,
        "rollout_or_production_write": False,
    }
