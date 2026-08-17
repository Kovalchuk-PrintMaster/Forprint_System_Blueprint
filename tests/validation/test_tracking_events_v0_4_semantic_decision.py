from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DECISION = ROOT / (
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_semantic_fidelity_operator_decision_v0_1.yaml"
)


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_semantic_fidelity_operator_decision_is_accepted_and_bounded() -> None:
    record = load(DECISION)

    assert record["metadata"]["state"] == "RECORDED"
    assert record["decision"]["value"] == "ACCEPT_SEMANTIC_FIDELITY"
    assert record["decision"]["scope"] == "prompt_contract_semantic_fidelity_only"
    assert record["decision"]["semantic_coverage"] == "26/26"
    assert record["decision"]["assistant_recommendation"] == "PASS"

    effects = record["effects"]
    assert effects["semantic_fidelity_accepted"] is True
    assert effects["tracking_events_completion_accepted"] is False
    assert effects["tracking_events_lifecycle_decision_created"] is False
    assert effects["roadmap_advanced"] is False
    assert effects["prompt_queue_advanced"] is False
    assert effects["module_repository_writes"] is False
    assert effects["completion_packet_v0_4_fabricated_by_blueprint"] is False
    assert effects["completion_outbox_v0_4_fabricated_by_blueprint"] is False
    assert effects["dark_zone_audit_run"] is False
    assert effects["global_v0_4_promotion_performed"] is False
    assert effects["automatic_commit"] is False
    assert effects["automatic_push"] is False
    assert effects["rollout_or_production_write"] is False


def test_semantic_decision_keeps_tracking_events_acceptance_separate() -> None:
    record = load(DECISION)
    assert (
        record["next_gate"][
            "tracking_events_acceptance_still_requires_separate_operator_decision"
        ]
        is True
    )
