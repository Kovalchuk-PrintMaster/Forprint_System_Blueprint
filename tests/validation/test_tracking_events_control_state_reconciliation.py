from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ROADMAP = ROOT / "coordination/roadmaps/logistics_service.yaml"
QUEUE = ROOT / "coordination/outgoing_prompts/logistics_service/index.yaml"
EVIDENCE = (
    ROOT / "coordination/internal_work/blueprint/governance/"
    "2026-08-07__blueprint__tracking_events_control_state_reconciliation_v0_1.yaml"
)

PROMPT_ID = "logistics_service_tracking_events_v0_1"
COMPLETION_COMMIT = "1f0b73df4dd7f5dc2cf04ffddff11fc8465c741a"
REPORT = (
    "coordination/reports/completion/"
    "2026-08-07__logistics_service__tracking_events_v0_1_completion_superseding_v0_2.md"
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_tracking_events_control_state_reflects_module_completion() -> None:
    roadmap = load_yaml(ROADMAP)
    queue = load_yaml(QUEUE)

    step = next(item for item in roadmap["roadmap"] if item["step_id"] == PROMPT_ID)
    prompt = next(item for item in queue["prompt_queue"] if item["prompt_id"] == PROMPT_ID)

    assert step["status"] == "active"
    assert step["evidence"]["completion_commit"] == COMPLETION_COMMIT
    assert step["evidence"]["completion_report"] == REPORT
    assert step["evidence"]["blueprint_review_status"] == "not_started"

    execution = prompt["module_execution"]
    assert execution["status"] == "completed_by_module"
    assert execution["completion_commit"] == COMPLETION_COMMIT
    assert execution["completion_report"] == REPORT
    assert execution["completed_at"] == "2026-08-07"

    review = prompt["blueprint_review"]
    assert review["status"] == "not_started"
    assert review["acceptance_commit"] is None
    assert review["accepted_at"] is None


def test_reconciliation_does_not_claim_acceptance_or_return() -> None:
    evidence = load_yaml(EVIDENCE)

    assert evidence["intake_after_reconciliation"]["status"] == ("READY_FOR_OPERATOR_REVIEW")
    assert evidence["operator_gate"]["decision"] is None
    assert evidence["operator_gate"]["automatic_acceptance"] is False
    assert evidence["operator_gate"]["automatic_return"] is False
    assert evidence["operator_gate"]["processed_review_record_created"] is False
    assert evidence["dependency_state"]["telegram_bot"] == "GATED"
    assert evidence["boundaries"]["module_repository_write"] is False
