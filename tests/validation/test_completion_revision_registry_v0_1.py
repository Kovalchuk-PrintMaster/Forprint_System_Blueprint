from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "coordination/revisions/current.yaml"
HISTORY = ROOT / "coordination/revisions/history.yaml"
PROTOCOL = ROOT / "coordination/standards/governance/module_completion_exchange_protocol_v0_3.md"
PROMPT_TEMPLATE = ROOT / "coordination/templates/module_prompt_contract_v0_3.example.yaml"
PACKET_TEMPLATE = ROOT / "coordination/templates/module_completion_packet_v0_3.example.yaml"
TRACKING_CONTRACT = (
    ROOT / "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1.yaml"
)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_revision_registry_has_one_operational_and_one_candidate() -> None:
    current = load_yaml(CURRENT)

    operational = current["operational_current"]
    candidate = current["candidate_next"]

    assert operational["completion_packet"] == "module_completion_packet_v0_2"
    assert operational["completion_intake"] == "blueprint_completion_intake_v0_2"
    assert operational["normal_acceptance_allowed"] is True

    assert candidate["prompt_contract"] == "module_prompt_contract_v0_3"
    assert candidate["completion_packet"] == "module_completion_packet_v0_3"
    assert candidate["completion_intake"] == "blueprint_completion_intake_v0_3"
    assert candidate["activation_state"] == "reference_validation"
    assert candidate["normal_acceptance_allowed"] is False

    legacy = current["legacy_policy"]
    assert legacy["normal_runtime_fallback"] is False
    assert legacy["unknown_revision_behavior"] == ("classify_and_generate_upgrade_instruction")


def test_revision_history_and_templates_are_explicit() -> None:
    history = load_yaml(HISTORY)
    by_revision = {item["revision"]: item for item in history["revisions"]}

    assert by_revision["v0_1"]["status"] == "legacy"
    assert by_revision["v0_2"]["status"] == "operational_current_transition"
    assert by_revision["v0_3"]["status"] == "candidate_reference_validation"
    assert by_revision["v0_3"]["supersedes_revision"] == "v0_2"

    assert load_yaml(PROMPT_TEMPLATE)["schema_version"] == ("module_prompt_contract_v0_3")
    packet = load_yaml(PACKET_TEMPLATE)
    assert packet["schema_version"] == "module_completion_packet_v0_3"
    assert packet["protocol_version"] == "blueprint_completion_intake_v0_3"


def test_tracking_events_reference_contract_is_bound_to_original_prompt() -> None:
    contract = load_yaml(TRACKING_CONTRACT)

    assert contract["schema_version"] == "module_prompt_contract_v0_3"
    assert contract["prompt_id"] == "logistics_service_tracking_events_v0_1"
    assert contract["implementation_base_commit"] == ("4812047963427043d616871075ac807a35e51aff")
    assert len(contract["requirements"]) == 10
    assert len(contract["required_checks"]) == 9
    assert contract["required_checks"][-1]["command"] == "git status --short"


def test_protocol_document_defines_candidate_gate_and_evolution() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")

    for required in (
        "module_prompt_contract_v0_3",
        "module_completion_packet_v0_3",
        "blueprint_completion_intake_v0_3",
        "REFERENCE_VALIDATION_READY",
        "implementation_range",
        "requirement_results",
        "check_results",
        "Revision upgrades are normal project evolution",
    ):
        assert required in text


def test_revision_status_cli_is_green() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/coordination/completion_revision_status.py",
            "--root",
            ".",
            "--output-format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"result": "passed"' in result.stdout
