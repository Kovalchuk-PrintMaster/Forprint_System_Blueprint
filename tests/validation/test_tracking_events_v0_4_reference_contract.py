from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = ROOT / (
    "coordination/outgoing_prompts/logistics_service/approved/"
    "2026-07-29__logistics_service__tracking_events_v0_1.md"
)
LEGACY = ROOT / (
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1.yaml"
)
CONTRACT = ROOT / (
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1/"
    "logistics_service_tracking_events_v0_1__contract_v0_4_reference_v0_2.yaml"
)
SNAPSHOT = CONTRACT.parent / "source_prompt_snapshot.md"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def validator_module():
    path = ROOT / "scripts/coordination/validate_prompt_contract_v0_4.py"
    spec = importlib.util.spec_from_file_location("validate_prompt_contract_v0_4", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tracking_events_v0_4_reference_contract_passes_validator() -> None:
    report = validator_module().validate_contract(ROOT, CONTRACT)
    assert report["result"] == "PASSED", report
    assert report["errors"] == []


def test_source_snapshot_is_byte_identical_and_hash_stable() -> None:
    assert SNAPSHOT.read_bytes() == ORIGIN.read_bytes()
    digest = hashlib.sha256(ORIGIN.read_bytes()).hexdigest()
    contract = load(CONTRACT)
    assert digest == "8158ff1feb9c2416aac97f70ce20110de3195d5239a343be940705d096242094"
    assert contract["source_prompt"]["sha256"] == digest
    assert contract["source_prompt"]["origin_sha256_at_capture"] == digest


def test_legacy_v0_3_contract_is_preserved_as_historical_input() -> None:
    legacy = load(LEGACY)
    contract = load(CONTRACT)
    assert legacy["schema_version"] == "module_prompt_contract_v0_3"
    assert legacy["contract_id"] == "logistics_service_tracking_events_v0_1_contract_v0_3"
    assert contract["schema_version"] == "module_prompt_contract_v0_4"
    assert contract["metadata"]["contract_id"] != legacy["contract_id"]


def test_dark_zone_categories_are_explicit_source_obligations() -> None:
    contract = load(CONTRACT)
    by_id = {x["obligation_id"]: x for x in contract["source_obligations"]}
    for obligation_id in {
        "SRC-012",
        "SRC-014",
        "SRC-015",
        "SRC-017",
        "SRC-018",
        "SRC-019",
        "SRC-020",
        "SRC-024",
        "SRC-R01",
        "SRC-R02",
    }:
        assert obligation_id in by_id
        assert by_id[obligation_id]["required"] is True

    summaries = " ".join(x["summary"] for x in contract["source_obligations"]).lower()
    for term in {
        "exact focused",
        "check-report totals",
        "telegram handoff",
        "generated reports",
        "completion automation",
        "upstream-divergence",
    }:
        assert term in summaries

    r01 = by_id["SRC-R01"]["summary"].lower()
    assert "blueprint governance" in r01
    assert "coordination sources" in r01
    assert "approved blueprint pull" in r01
    assert "prompt-navigation workflow" in r01

    r02 = by_id["SRC-R02"]["summary"].lower()
    assert "accepted provider contract" in r02
    assert "runbook" in r02
    assert "recovery evidence" in r02
    assert "authoritative logistics" in r02
    assert "authoritative paths" in r02
    assert "duplicate domain hierarchies" in r02


def test_required_source_obligations_are_all_mapped() -> None:
    contract = load(CONTRACT)
    source_ids = {
        x["obligation_id"]
        for x in contract["source_obligations"]
        if x["required"] is True
    }
    mapped_ids = {
        x["source_obligation_id"]
        for x in contract["source_obligation_fidelity_ledger"]
    }
    assert source_ids == mapped_ids
    assert len(source_ids) == 26


def test_reference_remains_candidate_only_pending_human_review() -> None:
    contract = load(CONTRACT)
    assert contract["metadata"]["status"] == "candidate_reference_only"
    assert contract["semantic_fidelity"] == {
        "human_review_required": True,
        "execution_fingerprint_sufficient": False,
        "review_state": "pending_operator_review",
    }
    assert contract["promotion"]["normal_acceptance_allowed"] is False
    assert contract["promotion"]["promotion_performed"] is False
