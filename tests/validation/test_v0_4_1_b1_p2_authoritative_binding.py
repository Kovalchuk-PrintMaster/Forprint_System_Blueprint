from __future__ import annotations

import copy
import hashlib
import inspect
from pathlib import Path

import pytest
import yaml

from scripts.coordination import completion_discovery_and_intake_v0_4 as discovery
from scripts.coordination import manage_outgoing_prompt as release_tool
from scripts.coordination import prompt_execution_events_v0_1 as event_tool
from scripts.coordination import validate_completion_packet_v0_4 as completion_tool


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def contract_data(
    *,
    module_id: str,
    prompt_id: str,
    contract_id: str,
    source_sha256: str,
    b1: bool = True,
) -> dict:
    data = {
        "schema_version": "module_prompt_contract_v0_4",
        "metadata": {
            "contract_id": contract_id,
            "module_id": module_id,
            "prompt_id": prompt_id,
            "immutable": True,
        },
        "source_prompt": {
            "path": "coordination/prompt_contracts/demo/source_prompt_snapshot.md",
            "sha256": source_sha256,
        },
        "integrity": {
            "algorithm": "sha256",
            "payload_sha256": "b" * 64,
        },
    }
    if b1:
        data["execution_baseline_policy"] = {
            "schema_version": "module_execution_baseline_policy_v0_1",
            "release_baseline": {
                "blueprint_commit": "a" * 40,
                "module_commit": "b" * 40,
                "module_branch": "feature/demo",
            },
        }
    return data


def contract_binding(root: Path, path: Path, contract: dict) -> dict:
    return {
        "schema_version": "module_prompt_contract_v0_4",
        "contract_id": contract["metadata"]["contract_id"],
        "path": path.relative_to(root).as_posix(),
        "file_sha256": sha_bytes(path.read_bytes()),
        "payload_sha256": contract["integrity"]["payload_sha256"],
        "source_prompt_sha256": contract["source_prompt"]["sha256"],
    }


def preflight_report(
    *,
    module_id: str,
    prompt_id: str,
    contract_id: str,
    release_baseline: dict,
    fingerprint: str,
) -> dict:
    return {
        "schema_version": "blueprint_execution_preflight_v0_1",
        "result": "READY",
        "status": "READY_EXACT",
        "contract": {
            "contract_id": contract_id,
            "module_id": module_id,
            "prompt_id": prompt_id,
            "path": "/copied/module/contract.yaml",
        },
        "release_baseline": copy.deepcopy(release_baseline),
        "execution_baseline": {
            "blueprint": {"head": "c" * 40},
            "module": {"head": "d" * 40},
        },
        "blueprint_status": "READY_EXACT",
        "module_status": "MODULE_EXACT",
        "revalidation": {
            "previous_preflight_fingerprint_sha256": None,
            "current_preflight_fingerprint_sha256": fingerprint,
            "revalidation_performed": False,
        },
        "execution_identity": {
            "execution_epoch_id": fingerprint,
            "claim_must_bind_preflight_fingerprint": True,
            "head_chasing_after_claim_allowed": False,
        },
        "preflight_fingerprint_sha256": fingerprint,
        "boundaries": {
            "blueprint_repository_writes": False,
            "module_repository_writes": False,
            "operator_decision_created": False,
            "automatic_acceptance": False,
        },
    }


def test_release_resolver_binds_exact_prepared_b1_contract(
    tmp_path: Path,
) -> None:
    module_id = "demo"
    prompt_id = "demo_prompt_v0_1"
    prepared = "exact prepared prompt bytes\n"
    source_sha = hashlib.sha256(prepared.encode()).hexdigest()
    contract = contract_data(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id="demo_contract_v0_1",
        source_sha256=source_sha,
    )
    path = (
        tmp_path
        / "coordination/prompt_contracts"
        / module_id
        / prompt_id
        / "demo_contract_v0_1.yaml"
    )
    write_yaml(path, contract)

    binding = release_tool._resolve_prompt_contract_binding(
        root=tmp_path,
        module=module_id,
        prompt_id=prompt_id,
        prepared_text=prepared,
    )

    assert binding == contract_binding(tmp_path, path, contract)


def test_release_fails_closed_when_b1_contract_does_not_bind_prepared_bytes(
    tmp_path: Path,
) -> None:
    module_id = "demo"
    prompt_id = "demo_prompt_v0_1"
    contract = contract_data(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id="demo_contract_v0_1",
        source_sha256="1" * 64,
    )
    path = (
        tmp_path
        / "coordination/prompt_contracts"
        / module_id
        / prompt_id
        / "demo_contract_v0_1.yaml"
    )
    write_yaml(path, contract)

    with pytest.raises(
        release_tool.WorkflowError,
        match="exact prepared prompt bytes",
    ):
        release_tool._resolve_prompt_contract_binding(
            root=tmp_path,
            module=module_id,
            prompt_id=prompt_id,
            prepared_text="different prepared bytes\n",
        )


def test_release_prompt_wires_contract_binding_into_queue_record() -> None:
    source = inspect.getsource(release_tool.release_prompt)
    assert "_resolve_prompt_contract_binding(" in source
    assert '"prompt_contract": prompt_contract_binding' in source


def test_queue_b1_discriminator_requires_claim_identity_and_preflight_evidence(
    tmp_path: Path,
) -> None:
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    module.mkdir(parents=True)

    module_id = "demo"
    prompt_id = "demo_prompt_v0_1"
    fingerprint = "e" * 64
    contract = contract_data(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id="demo_contract_v0_1",
        source_sha256="f" * 64,
    )
    contract_path = (
        blueprint
        / "coordination/prompt_contracts"
        / module_id
        / prompt_id
        / "demo_contract_v0_1.yaml"
    )
    write_yaml(contract_path, contract)
    binding = contract_binding(blueprint, contract_path, contract)

    b1, observed_binding, observed_contract, errors = (
        event_tool._queue_contract_binding_state(
            blueprint,
            {"prompt_contract": binding},
            module_id,
            prompt_id,
        )
    )
    assert b1 is True
    assert errors == []
    assert observed_binding == binding
    assert observed_contract == contract

    report = preflight_report(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id=contract["metadata"]["contract_id"],
        release_baseline=contract["execution_baseline_policy"][
            "release_baseline"
        ],
        fingerprint=fingerprint,
    )
    rel = event_tool._expected_preflight_evidence_path(
        prompt_id,
        fingerprint,
    )
    evidence_path = module / rel
    write_yaml(evidence_path, report)
    identity = {
        "schema_version": "module_execution_identity_v0_1",
        "execution_epoch_id": fingerprint,
        "preflight_fingerprint_sha256": fingerprint,
        "preflight_evidence": {
            "path": rel,
            "sha256": sha_bytes(evidence_path.read_bytes()),
        },
    }

    assert event_tool._validate_bound_preflight_evidence(
        identity,
        repository_root=module,
        module_id=module_id,
        prompt_id=prompt_id,
        contract_binding=binding,
        contract=contract,
    ) == []

    bad = copy.deepcopy(identity)
    bad["preflight_evidence"]["path"] = (
        "coordination/execution_preflight/records/other.yaml"
    )
    assert any(
        "canonical" in item
        for item in event_tool._validate_bound_preflight_evidence(
            bad,
            repository_root=module,
            module_id=module_id,
            prompt_id=prompt_id,
            contract_binding=binding,
            contract=contract,
        )
    )

    validate_source = inspect.getsource(event_tool.validate_event)
    assert "_queue_contract_binding_state(" in validate_source
    assert "_validate_bound_preflight_evidence(" in validate_source
    assert "B1-bound Prompt Contract requires " in validate_source
    assert "execution_identity on every execution event" in validate_source


def valid_provenance(
    packet: dict,
    *,
    fingerprint: str,
    report: dict,
    evidence_path: Path,
    root: Path,
) -> dict:
    return {
        "schema_version": "module_completion_provenance_v0_1",
        "release_baseline": copy.deepcopy(report["release_baseline"]),
        "execution_baseline": copy.deepcopy(report["execution_baseline"]),
        "execution_identity": {
            "execution_epoch_id": fingerprint,
            "preflight_fingerprint_sha256": fingerprint,
        },
        "preflight_evidence": {
            "path": evidence_path.relative_to(root).as_posix(),
            "sha256": sha_bytes(evidence_path.read_bytes()),
        },
        "revalidation": copy.deepcopy(report["revalidation"]),
        "completion_baseline": {
            "implementation_base_commit": packet[
                "implementation_base_commit"
            ],
            "final_implementation_commit": packet[
                "implementation_commit"
            ],
            "branch": packet["branch"],
        },
        "boundaries": {
            "blueprint_acceptance_claimed": False,
            "operator_decision_created": False,
        },
    }


def test_b1_completion_requires_provenance_and_exact_preflight_binding(
    tmp_path: Path,
) -> None:
    module_id = "demo"
    prompt_id = "demo_prompt_v0_1"
    fingerprint = "e" * 64
    contract = contract_data(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id="demo_contract_v0_1",
        source_sha256="f" * 64,
    )
    prompt_contract = {
        "schema_version": "module_prompt_contract_v0_4",
        "contract_id": contract["metadata"]["contract_id"],
        "path": "coordination/prompt_contracts/demo/demo.yaml",
        "file_sha256": "1" * 64,
        "payload_sha256": contract["integrity"]["payload_sha256"],
        "source_prompt_sha256": contract["source_prompt"]["sha256"],
    }
    packet = {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "implementation_base_commit": "1" * 40,
        "implementation_commit": "2" * 40,
        "branch": "feature/demo",
    }

    missing_errors: list[str] = []
    completion_tool._validate_b1_completion_binding(
        tmp_path,
        packet,
        prompt_contract,
        contract,
        missing_errors,
        template_mode=False,
    )
    assert any(
        "requires completion_provenance" in item
        for item in missing_errors
    )

    report = preflight_report(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id=contract["metadata"]["contract_id"],
        release_baseline=contract["execution_baseline_policy"][
            "release_baseline"
        ],
        fingerprint=fingerprint,
    )
    evidence_rel = completion_tool._expected_preflight_evidence_path(
        prompt_id,
        fingerprint,
    )
    evidence_path = tmp_path / evidence_rel
    write_yaml(evidence_path, report)
    packet["completion_provenance"] = valid_provenance(
        packet,
        fingerprint=fingerprint,
        report=report,
        evidence_path=evidence_path,
        root=tmp_path,
    )

    errors: list[str] = []
    completion_tool._validate_b1_completion_binding(
        tmp_path,
        packet,
        prompt_contract,
        contract,
        errors,
        template_mode=False,
    )
    assert errors == []

    tampered = copy.deepcopy(packet)
    tampered["completion_provenance"]["execution_baseline"] = {
        "different": True
    }
    mismatch_errors: list[str] = []
    completion_tool._validate_b1_completion_binding(
        tmp_path,
        tampered,
        prompt_contract,
        contract,
        mismatch_errors,
        template_mode=False,
    )
    assert any("execution_baseline" in item for item in mismatch_errors)


def test_revalidation_previous_fingerprint_semantics_are_fail_closed() -> None:
    fingerprint = "e" * 64
    packet = {
        "implementation_base_commit": "1" * 40,
        "implementation_commit": "2" * 40,
        "branch": "feature/demo",
        "completion_provenance": {
            "schema_version": "module_completion_provenance_v0_1",
            "release_baseline": {"x": 1},
            "execution_baseline": {"y": 1},
            "execution_identity": {
                "execution_epoch_id": fingerprint,
                "preflight_fingerprint_sha256": fingerprint,
            },
            "revalidation": {
                "revalidation_performed": True,
                "previous_preflight_fingerprint_sha256": None,
                "current_preflight_fingerprint_sha256": fingerprint,
            },
            "completion_baseline": {
                "implementation_base_commit": "1" * 40,
                "final_implementation_commit": "2" * 40,
                "branch": "feature/demo",
            },
            "boundaries": {
                "blueprint_acceptance_claimed": False,
                "operator_decision_created": False,
            },
        },
    }
    errors: list[str] = []
    completion_tool._validate_completion_provenance(
        packet,
        errors,
        template_mode=False,
    )
    assert any(
        "required when revalidation_performed=true" in item
        for item in errors
    )

    packet["completion_provenance"]["revalidation"] = {
        "revalidation_performed": False,
        "previous_preflight_fingerprint_sha256": "a" * 64,
        "current_preflight_fingerprint_sha256": fingerprint,
    }
    errors = []
    completion_tool._validate_completion_provenance(
        packet,
        errors,
        template_mode=False,
    )
    assert any(
        "must be null when revalidation_performed=false" in item
        for item in errors
    )


def test_discovery_compares_packet_contract_to_queue_authority(
    tmp_path: Path,
) -> None:
    module_id = "demo"
    prompt_id = "demo_prompt_v0_1"
    binding = {
        "schema_version": "module_prompt_contract_v0_4",
        "contract_id": "demo_contract_v0_1",
        "path": "coordination/prompt_contracts/demo/demo_prompt_v0_1/demo.yaml",
        "file_sha256": "1" * 64,
        "payload_sha256": "2" * 64,
        "source_prompt_sha256": "3" * 64,
    }
    queue = {
        "schema_version": "prompt_queue_v0_2",
        "module": module_id,
        "prompt_queue": [
            {
                "prompt_id": prompt_id,
                "prompt_contract": binding,
            }
        ],
    }
    queue_path = (
        tmp_path
        / "coordination/outgoing_prompts"
        / module_id
        / "index.yaml"
    )
    write_yaml(queue_path, queue)

    observed, errors = discovery._queue_prompt_contract_binding(
        tmp_path,
        module_id,
        prompt_id,
    )
    assert errors == []
    assert observed == binding
    assert discovery._packet_queue_contract_errors(
        copy.deepcopy(binding),
        binding,
    ) == []

    bad = copy.deepcopy(binding)
    bad["file_sha256"] = "4" * 64
    mismatch = discovery._packet_queue_contract_errors(bad, binding)
    assert any("file_sha256" in item for item in mismatch)

    source = inspect.getsource(discovery._discover_module)
    assert "_queue_prompt_contract_binding(" in source
    assert "_packet_queue_contract_errors(" in source


def test_discovery_binds_b1_completion_to_actual_claim_preflight(
    tmp_path: Path,
    monkeypatch,
) -> None:
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    module.mkdir(parents=True)

    module_id = "demo"
    prompt_id = "demo_prompt_v0_1"
    claim_fingerprint = "e" * 64
    other_fingerprint = "d" * 64

    contract = contract_data(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id="demo_contract_v0_1",
        source_sha256="f" * 64,
    )
    contract_path = (
        blueprint
        / "coordination/prompt_contracts"
        / module_id
        / prompt_id
        / "demo_contract_v0_1.yaml"
    )
    write_yaml(contract_path, contract)
    binding = contract_binding(blueprint, contract_path, contract)

    queue_path = (
        blueprint
        / "coordination/outgoing_prompts"
        / module_id
        / "index.yaml"
    )
    write_yaml(
        queue_path,
        {
            "schema_version": "prompt_queue_v0_2",
            "module": module_id,
            "prompt_queue": [
                {
                    "prompt_id": prompt_id,
                    "target_module": module_id,
                    "prompt_contract": binding,
                    "module_execution": {"status": "in_progress"},
                    "blueprint_review": {"status": "pending"},
                }
            ],
        },
    )

    registry_path = (
        blueprint
        / "coordination/registry/coordination_source_registry_v0_1.yaml"
    )
    write_yaml(
        registry_path,
        {
            "modules": [
                {
                    "module_id": module_id,
                    "repository": {"local_path": str(module)},
                    "boundaries": {
                        "blueprint_lookup_mode": "read_only",
                        "blueprint_may_write_repository": False,
                    },
                    "sources": {
                        "prompt_queue": {
                            "owner": "forprint_system_blueprint",
                            "availability": "present",
                            "path": queue_path.relative_to(
                                blueprint
                            ).as_posix(),
                        }
                    },
                }
            ]
        },
    )

    def write_preflight(fingerprint: str) -> tuple[str, str]:
        report = preflight_report(
            module_id=module_id,
            prompt_id=prompt_id,
            contract_id=contract["metadata"]["contract_id"],
            release_baseline=contract["execution_baseline_policy"][
                "release_baseline"
            ],
            fingerprint=fingerprint,
        )
        rel = event_tool._expected_preflight_evidence_path(
            prompt_id,
            fingerprint,
        )
        path = module / rel
        write_yaml(path, report)
        return rel, sha_bytes(path.read_bytes())

    claim_rel, claim_sha = write_preflight(claim_fingerprint)
    other_rel, other_sha = write_preflight(other_fingerprint)

    event_path = (
        module
        / "coordination/prompt_execution_events/records/demo_claim_001.yaml"
    )
    write_yaml(
        event_path,
        {
            "schema_version": "module_prompt_execution_event_v0_1",
            "event_id": "demo_claim_001",
            "module_id": module_id,
            "prompt_id": prompt_id,
            "sequence": 1,
            "event_type": "CLAIMED",
            "occurred_at": "2026-08-23T19:00:00+03:00",
            "immutable": True,
            "execution_identity": {
                "schema_version": "module_execution_identity_v0_1",
                "execution_epoch_id": claim_fingerprint,
                "preflight_fingerprint_sha256": claim_fingerprint,
                "preflight_evidence": {
                    "path": claim_rel,
                    "sha256": claim_sha,
                },
            },
            "execution": {
                "reason": None,
                "reason_code": None,
                "blocking_refs": [],
            },
            "boundaries": {
                "blueprint_repository_write_performed": False,
                "operator_decision_created": False,
                "completion_claimed": False,
                "acceptance_claimed": False,
                "return_or_hold_claimed": False,
            },
        },
    )

    monkeypatch.setattr(
        discovery,
        "_load_module",
        lambda _path, _name: event_tool,
    )

    packet = {
        "module_id": module_id,
        "prompt_id": prompt_id,
        "prompt_contract": binding,
        "completion_provenance": {
            "execution_identity": {
                "execution_epoch_id": other_fingerprint,
                "preflight_fingerprint_sha256": other_fingerprint,
            },
            "preflight_evidence": {
                "path": other_rel,
                "sha256": other_sha,
            },
        },
    }

    mismatch = discovery._b1_completion_claim_binding_errors(
        blueprint_root=blueprint,
        registry_path=registry_path,
        repository_root=module,
        module_id=module_id,
        prompt_id=prompt_id,
        packet=packet,
        queue_binding=binding,
    )
    assert any(
        "execution identity does not match CLAIM" in item
        for item in mismatch
    )
    assert any(
        "path/SHA does not match CLAIM" in item
        for item in mismatch
    )

    packet["completion_provenance"] = {
        "execution_identity": {
            "execution_epoch_id": claim_fingerprint,
            "preflight_fingerprint_sha256": claim_fingerprint,
        },
        "preflight_evidence": {
            "path": claim_rel,
            "sha256": claim_sha,
        },
    }
    assert discovery._b1_completion_claim_binding_errors(
        blueprint_root=blueprint,
        registry_path=registry_path,
        repository_root=module,
        module_id=module_id,
        prompt_id=prompt_id,
        packet=packet,
        queue_binding=binding,
    ) == []

    source = inspect.getsource(discovery._discover_module)
    assert "_b1_completion_claim_binding_errors(" in source


def test_discovery_preserves_non_b1_completion_compatibility(
    tmp_path: Path,
    monkeypatch,
) -> None:
    blueprint = tmp_path / "blueprint"
    module = tmp_path / "module"
    module.mkdir(parents=True)

    module_id = "demo"
    prompt_id = "historical_prompt_v0_1"
    contract = contract_data(
        module_id=module_id,
        prompt_id=prompt_id,
        contract_id="historical_contract_v0_1",
        source_sha256="f" * 64,
        b1=False,
    )
    contract_path = (
        blueprint
        / "coordination/prompt_contracts"
        / module_id
        / prompt_id
        / "historical_contract_v0_1.yaml"
    )
    write_yaml(contract_path, contract)
    binding = contract_binding(blueprint, contract_path, contract)

    monkeypatch.setattr(
        discovery,
        "_load_module",
        lambda _path, _name: event_tool,
    )

    assert discovery._b1_completion_claim_binding_errors(
        blueprint_root=blueprint,
        registry_path=blueprint / "unused_registry.yaml",
        repository_root=module,
        module_id=module_id,
        prompt_id=prompt_id,
        packet={
            "module_id": module_id,
            "prompt_id": prompt_id,
            "prompt_contract": binding,
        },
        queue_binding=binding,
    ) == []
