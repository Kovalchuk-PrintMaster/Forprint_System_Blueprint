from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from scripts.coordination.acceptance_oracle_v0_1 import load_and_validate_oracle
from scripts.coordination.validate_prompt_contract_v0_4 import validate_contract

ROOT = Path(__file__).resolve().parents[2]
MODULE = "logistics_service"
ROADMAP = ROOT / "coordination/roadmaps/logistics_service.yaml"
DRAFTS = ROOT / "coordination/outgoing_prompts/logistics_service/drafts"

PREPARED_IDS = {
    "logistics_service_local_persistence_and_migration_boundary_v0_1",
    "logistics_service_channel_interaction_contract_v0_1",
    "logistics_service_provider_runtime_registry_and_capability_policy_v0_1",
    "logistics_service_normalized_quote_booking_operation_contract_v0_1",
    "logistics_service_nova_poshta_read_only_foundation_v0_1",
    "logistics_service_ukrposhta_read_only_foundation_v0_1",
    "logistics_service_taxi_provider_abstraction_v0_1",
    "logistics_service_uklon_delivery_read_only_foundation_v0_1",
}

PROVIDER_RESEARCH_IDS = {
    "logistics_service_nova_poshta_read_only_foundation_v0_1",
    "logistics_service_ukrposhta_read_only_foundation_v0_1",
    "logistics_service_uklon_delivery_read_only_foundation_v0_1",
}


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def machine(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(.*?)\n```", text, flags=re.DOTALL)
    assert match is not None
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict)
    return data


def roadmap_by_id() -> dict[str, dict]:
    data = load(ROADMAP)
    return {
        step["step_id"]: step
        for step in data["roadmap"]
        if isinstance(step, dict)
    }


def prepared_paths() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in DRAFTS.glob("*.md"):
        if path.name == ".gitkeep":
            continue
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^prompt_id:\s*(\S+)\s*$", text, re.MULTILINE)
        assert match is not None
        result[match.group(1)] = path
    return result


def test_exactly_eight_prepared_steps_are_oracle_bound() -> None:
    steps = roadmap_by_id()
    paths = prepared_paths()
    assert set(paths) == PREPARED_IDS

    bound = {
        step_id
        for step_id, step in steps.items()
        if isinstance(step.get("acceptance"), dict)
        and step["acceptance"].get("oracle_required") is True
    }
    assert bound == PREPARED_IDS

    planning_only = {
        step_id
        for step_id, step in steps.items()
        if step.get("status") in {"planned", "ready"}
        and step_id not in PREPARED_IDS
    }
    assert planning_only
    assert all("acceptance" not in steps[step_id] for step_id in planning_only)


def test_prepared_prompt_contract_oracle_bindings_are_canonical() -> None:
    steps = roadmap_by_id()
    paths = prepared_paths()

    for prompt_id in sorted(PREPARED_IDS):
        prompt_path = paths[prompt_id]
        payload = machine(prompt_path)
        handoff = payload["acceptance_handoff"]

        step = steps[prompt_id]
        acceptance = step["acceptance"]
        oracle_path = ROOT / acceptance["oracle_path"]
        assert sha(oracle_path) == acceptance["oracle_sha256"]

        oracle = load(oracle_path)
        contract_path = ROOT / oracle["source_prompt_contract"]["path"]
        assert sha(contract_path) == oracle["source_prompt_contract"]["sha256"]

        contract = load(contract_path)
        report = validate_contract(ROOT, contract_path, contract)
        assert report["result"] == "PASSED", report["errors"]

        snapshot = contract_path.parent / "source_prompt_snapshot.md"
        assert snapshot.read_bytes() == prompt_path.read_bytes()
        assert contract["source_prompt"]["sha256"] == sha(snapshot)

        normalized = load_and_validate_oracle(
            ROOT,
            oracle_path=acceptance["oracle_path"],
            oracle_sha256=acceptance["oracle_sha256"],
            module_id=MODULE,
            prompt_id=prompt_id,
            step_id=prompt_id,
            roadmap_step=step,
        )
        assert normalized["criteria"]

        substeps = {
            item["substep_id"]
            for item in step["substeps"]
            if item.get("blocking", True)
        }
        criterion_substeps = {
            item["substep_id"]
            for item in normalized["criteria"]
            if item.get("substep_id") is not None
        }
        assert criterion_substeps == substeps

        contract_ids = {
            item["obligation_id"]
            for field in (
                "implementation_obligations",
                "verification_obligations",
                "completion_evidence_obligations",
            )
            for item in contract[field]
        }
        oracle_refs = {
            ref
            for item in normalized["criteria"]
            for ref in item["requirement_refs"]
        }
        assert oracle_refs == contract_ids

        required_evidence = {
            ref
            for item in normalized["criteria"]
            for ref in item["evidence_required"]
        }
        declared = set(
            handoff["completion_packet"]["required_evidence_ids"]
        )
        assert required_evidence <= declared

        if prompt_id in PROVIDER_RESEARCH_IDS:
            assert "EV-PROVIDER-RESEARCH" in declared
            assert any(
                item["criterion_id"] == "AC-902"
                for item in normalized["criteria"]
            )
            research = payload["provider_research_policy"]
            assert research["fail_closed_when_official_evidence_unavailable"] is True
            assert research["invent_capabilities_from_assumptions"] is False


def test_oracle_binding_does_not_release_or_queue_prepared_prompts() -> None:
    queue = load(
        ROOT / "coordination/outgoing_prompts/logistics_service/index.yaml"
    )
    rows = queue.get("prompt_queue", [])
    queued = {
        item.get("prompt_id")
        for item in rows
        if isinstance(item, dict)
    }
    assert PREPARED_IDS.isdisjoint(queued)
