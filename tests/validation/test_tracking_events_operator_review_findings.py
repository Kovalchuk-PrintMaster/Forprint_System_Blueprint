from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

FINDINGS = (
    ROOT / "coordination/internal_work/blueprint/governance/"
    "2026-08-07__blueprint__tracking_events_operator_review_findings_v0_1.yaml"
)
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"

PROMPT_ID = "logistics_service_tracking_events_v0_1"

REQUIRED_FLAGS = [
    "no_automatic_posting",
    "no_live_external_integrations",
    "no_production_api",
    "no_production_write",
    "no_real_1c_sync",
]


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_tracking_events_findings_preserve_operator_gate() -> None:
    findings = load_yaml(FINDINGS)

    assert findings["metadata"]["module_id"] == "forprint_system_blueprint"
    assert findings["metadata"]["subject_module_id"] == "logistics_service"
    assert findings["subject"]["prompt_id"] == PROMPT_ID

    intake = findings["intake_findings"]
    assert intake["status"] == "BLOCKED"
    assert intake["blocker_code"] == "SAFETY_CONFIRMATION_INVALID"
    assert intake["failure_class"] == "protocol_compatibility"
    assert intake["remediation_owner"] == "module"
    assert intake["implementation_failure_proven"] is False
    assert intake["required_positive_confirmations"] == REQUIRED_FLAGS

    decision = findings["operator_gate"]
    assert decision["decision"] is None
    assert decision["automatic_acceptance"] is False
    assert decision["automatic_return"] is False
    assert decision["processed_review_record_created"] is False


def test_findings_require_superseding_packet_only_if_returned() -> None:
    findings = load_yaml(FINDINGS)

    remediation = findings["conditional_remediation"]
    assert remediation["trigger"] == "explicit_RETURN_WITH_FINDINGS_only"
    assert remediation["owner"] == "logistics_service"
    assert remediation["rewrite_historical_packet"] is False
    assert remediation["superseding_packet_required"] is True
    assert remediation["target_schema"] == "module_completion_packet_v0_2"
    assert remediation["target_protocol"] == "blueprint_completion_intake_v0_2"


def test_handoff_keeps_tracking_events_pending_and_telegram_gated() -> None:
    handoff = load_yaml(HANDOFF)

    pending = next(
        item for item in handoff["pending_operator_decisions"] if item["subject"] == PROMPT_ID
    )
    assert pending["state"] == "PENDING_OPERATOR_REVIEW"
    assert pending["operator_decision"] is None
    assert pending["reference_intake_status"] == "REFERENCE_VALIDATION_READY"
    assert pending["blocker_code"] == "PROMPT_CONTRACT_FIDELITY_INCOMPLETE"
    assert pending["implementation_failure_proven"] is False
    assert pending["automatic_acceptance"] is False
    assert pending["automatic_return"] is False

    gate = next(
        item
        for item in handoff["dependency_gates"]
        if item["consumer"] == "telegram_bot" and item["dependency"] == PROMPT_ID
    )
    assert gate["state"] == "GATED"

    assert handoff["next_10_steps"][0]["id"] == (
        "blueprint_v0_4_coordination_source_registry_v0_1"
    )
