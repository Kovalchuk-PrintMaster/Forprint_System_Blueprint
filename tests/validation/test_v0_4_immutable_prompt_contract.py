from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STANDARD = ROOT / "coordination/standards/governance/module_prompt_contract_v0_4.yaml"
CONTRACT = ROOT / (
    "coordination/prompt_contracts/forprint_system_blueprint/"
    "blueprint_v0_4_immutable_prompt_contract_v0_1/"
    "blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml"
)
SOURCE_SNAPSHOT = CONTRACT.parent / "source_prompt_snapshot.md"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
STEP21 = "blueprint_v0_4_immutable_prompt_contract_v0_1"


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


def valid_contract() -> dict:
    return load(CONTRACT)


def test_standard_is_candidate_reference_only_and_immutable() -> None:
    standard = load(STANDARD)
    assert standard["schema_version"] == "module_prompt_contract_standard_v0_4"
    assert standard["metadata"]["status"] == "candidate_reference_only"
    assert standard["immutability"]["published_instance_mutation_allowed"] is False
    assert standard["promotion"]["normal_acceptance_allowed"] is False
    assert standard["promotion"]["promotion_requires_explicit_operator_decision"] is True
    assert standard["promotion"]["step21_acceptance_is_not_global_v0_4_promotion"] is True


def test_self_contract_passes_validator() -> None:
    module = validator_module()
    report = module.validate_contract(ROOT, CONTRACT)
    assert report["result"] == "PASSED", report
    assert report["errors"] == []
    assert report["summary"] == {
        "source_obligations": 12,
        "implementation_obligations": 11,
        "verification_obligations": 6,
        "completion_evidence_obligations": 2,
        "fidelity_mappings": 12,
    }


def test_contract_instance_path_and_source_prompt_hash_are_enforced() -> None:
    module = validator_module()
    data = valid_contract()

    assert data["source_prompt"]["path"] == str(SOURCE_SNAPSHOT.relative_to(ROOT))
    assert data["source_prompt"]["origin_path_at_capture"].endswith(
        "prompt_queue/approved/2026-08-14__forprint_system_blueprint__v0_4_immutable_prompt_contract_v0_1.md"
    )
    assert data["source_prompt"]["origin_sha256_at_capture"] == data["source_prompt"]["sha256"]

    wrong_path = CONTRACT.parent.parent / CONTRACT.name
    report = module.validate_contract(ROOT, wrong_path, data)
    assert "immutable instance path mismatch" in report["errors"]

    bad = copy.deepcopy(data)
    bad["source_prompt"]["sha256"] = "0" * 64
    bad["integrity"]["payload_sha256"] = module.canonical_payload_sha256(bad)
    report = module.validate_contract(ROOT, CONTRACT, bad)
    assert "source prompt SHA-256 mismatch" in report["errors"]


def test_duplicate_obligation_ids_are_rejected() -> None:
    module = validator_module()
    bad = copy.deepcopy(valid_contract())
    bad["verification_obligations"][0]["obligation_id"] = "IMP-001"
    bad["integrity"]["payload_sha256"] = module.canonical_payload_sha256(bad)
    report = module.validate_contract(ROOT, CONTRACT, bad)
    assert any(x.startswith("duplicate obligation IDs:") for x in report["errors"])


def test_unknown_mapping_targets_are_rejected() -> None:
    module = validator_module()
    bad = copy.deepcopy(valid_contract())
    bad["source_obligation_fidelity_ledger"][0]["target_obligation_ids"].append("NOPE-001")
    bad["integrity"]["payload_sha256"] = module.canonical_payload_sha256(bad)
    report = module.validate_contract(ROOT, CONTRACT, bad)
    assert "unknown mapping target: NOPE-001" in report["errors"]


def test_required_unmapped_source_obligations_are_rejected() -> None:
    module = validator_module()
    bad = copy.deepcopy(valid_contract())
    bad["source_obligation_fidelity_ledger"] = [
        x
        for x in bad["source_obligation_fidelity_ledger"]
        if x["source_obligation_id"] != "SRC-006"
    ]
    bad["integrity"]["payload_sha256"] = module.canonical_payload_sha256(bad)
    report = module.validate_contract(ROOT, CONTRACT, bad)
    assert any(
        x.startswith("required source obligations unmapped:") and "SRC-006" in x
        for x in report["errors"]
    )


def test_contract_payload_hash_is_enforced() -> None:
    module = validator_module()
    bad = copy.deepcopy(valid_contract())
    bad["implementation_obligations"][0]["summary"] = "mutated"
    report = module.validate_contract(ROOT, CONTRACT, bad)
    assert "contract payload SHA-256 mismatch" in report["errors"]


def test_semantic_fidelity_and_fingerprint_boundaries_are_enforced() -> None:
    module = validator_module()
    bad = copy.deepcopy(valid_contract())
    bad["semantic_fidelity"]["human_review_required"] = False
    bad["semantic_fidelity"]["execution_fingerprint_sufficient"] = True
    bad["integrity"]["payload_sha256"] = module.canonical_payload_sha256(bad)
    report = module.validate_contract(ROOT, CONTRACT, bad)
    assert "human semantic fidelity review must be required" in report["errors"]
    assert "execution fingerprint must not be complete fidelity proof" in report["errors"]


def test_step21_lifecycle_state_is_coherent() -> None:
    roadmap = load(ROADMAP)
    step21 = next(x for x in roadmap["steps"] if x["step_id"] == STEP21)

    if step21["status"] == "active":
        assert roadmap["metadata"]["current_step_id"] == STEP21
    else:
        assert step21["status"] == "completed"
        assert step21["operator_decision"] == "ACCEPT"


def test_handoff_surfaces_candidate_contract_without_promotion() -> None:
    handoff = load(HANDOFF)
    state = handoff["prompt_contract_v0_4"]
    assert state["status"] == "candidate_reference_only"
    assert state["promotion_performed"] is False
    packet_state = handoff.get("completion_packet_v0_4")
    if packet_state is None:
        assert state["completion_packet_v0_4_implemented"] is False
    else:
        assert state["completion_packet_v0_4_implemented"] is True
        assert packet_state["implementation_status"] in {
            "READY_FOR_OPERATOR_REVIEW",
            "accepted_v0_4",
        }
        assert packet_state["promotion_performed"] is False
