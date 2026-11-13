from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest
import yaml

from scripts.coordination.validate_completion_packet_v0_4 import (
    canonical_payload_sha256 as completion_packet_payload_sha256,
)
from scripts.coordination.validate_prompt_contract_v0_4 import (
    canonical_payload_sha256,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "scripts/coordination/review_roadmap_queue_transaction_v0_4.py"


def tool_module():
    spec = importlib.util.spec_from_file_location(
        "review_tx_module_schema_test",
        TOOL,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def fixture_state(tmp_path: Path) -> dict[str, Path]:
    roadmap = tmp_path / "coordination/roadmaps/demo.yaml"
    queue = tmp_path / "coordination/outgoing_prompts/demo/index.yaml"
    approved = (
        tmp_path
        / "coordination/outgoing_prompts/demo/approved/demo_prompt.md"
    )

    roadmap.parent.mkdir(parents=True, exist_ok=True)
    queue.parent.mkdir(parents=True, exist_ok=True)
    approved.parent.mkdir(parents=True, exist_ok=True)

    roadmap.write_text(
        yaml.safe_dump(
            {
                "schema_version": "module_development_roadmap_v0_1",
                "module": "demo",
                "metadata": {
                    "current_step_id": "demo_prompt",
                    "updated_at": "2026-08-17",
                },
                "roadmap": [
                    {
                        "sequence": 1,
                        "step_id": "demo_prompt",
                        "title": "Demo",
                        "status": "active",
                        "priority": "critical",
                        "owner_module": "demo",
                        "depends_on": [],
                        "expected_outputs": [],
                        "evidence": {
                            "blueprint_review_status": "not_started",
                        },
                    },
                    {
                        "sequence": 2,
                        "step_id": "demo_next",
                        "title": "Next",
                        "status": "planned",
                        "priority": "high",
                        "owner_module": "demo",
                        "depends_on": [
                            {
                                "type": "module_step",
                                "module": "demo",
                                "step_id": "demo_prompt",
                                "status": "pending",
                            }
                        ],
                        "expected_outputs": [],
                        "evidence": {},
                    },
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    queue.write_text(
        yaml.safe_dump(
            {
                "schema_version": "prompt_queue_v0_2",
                "module": "demo",
                "prompt_queue": [
                    {
                        "prompt_id": "demo_prompt",
                        "sequence": 1,
                        "title": "Demo",
                        "file": "approved/demo_prompt.md",
                        "target_module": "demo",
                        "phase": "demo",
                        "priority": "critical",
                        "module_execution": {
                            "status": "completed_by_module",
                            "completion_commit": "abc",
                            "completion_report": "report.md",
                            "completed_at": "2026-08-17",
                        },
                        "blueprint_review": {
                            "status": "not_started",
                            "acceptance_commit": None,
                            "accepted_at": None,
                            "review_notes": None,
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    approved.write_text("# Demo prompt\n", encoding="utf-8")
    return {
        "root": tmp_path,
        "roadmap": roadmap,
        "queue": queue,
        "approved": approved,
    }


def request_for(
    module,
    paths: dict[str, Path],
    decision: str,
    *,
    decision_id: str = "decision_demo_001",
) -> dict:
    return {
        "schema_version": (
            "blueprint_review_roadmap_queue_transaction_request_v0_4"
        ),
        "review_candidate": {
            "module_id": "demo",
            "prompt_id": "demo_prompt",
            "event_id": "event_demo_001",
            "event_path": (
                "coordination/completion_outbox/records/event_demo_001.yaml"
            ),
            "event_sha256": "a" * 64,
            "packet_path": (
                "coordination/completion_packets/records/packet_demo_001.yaml"
            ),
            "packet_sha256": "b" * 64,
            "intake_state": "READY_FOR_BLUEPRINT_REVIEW",
            "operator_decision_created": False,
            "discovery_fingerprint_sha256": "c" * 64,
        },
        "decision": {
            "decision_id": decision_id,
            "operator_decision": decision,
            "explicit_operator_input": True,
            "decided_at": "2026-08-18T19:30:00+03:00",
            "review_notes": "explicit operator review",
        },
        "targets": {
            "roadmap_path": str(paths["roadmap"].relative_to(paths["root"])),
            "prompt_queue_path": str(
                paths["queue"].relative_to(paths["root"])
            ),
            "prompt_path": str(
                paths["approved"].relative_to(paths["root"])
            ),
            "review_evidence_path": (
                "coordination/review_packets/demo/processed/"
                f"{decision_id}.yaml"
            ),
            "roadmap_step_id": "demo_prompt",
        },
        "preconditions": {
            "roadmap_sha256": module.file_sha256(paths["roadmap"]),
            "prompt_queue_sha256": module.file_sha256(paths["queue"]),
            "prompt_sha256": module.file_sha256(paths["approved"]),
        },
    }


def enable_acceptance_oracle(
    module,
    paths: dict[str, Path],
    request: dict,
    *,
    include_evaluation: bool = True,
    result: str = "PASS",
    evidence_refs: list[str] | None = None,
    waiver: bool = False,
    requirement_ref: str = "IMP-001",
    contract_payload_valid: bool = True,
) -> None:
    root = paths["root"]
    contract = (
        root
        / "coordination/prompt_contracts/demo/demo_prompt/"
        "demo_prompt__contract_v0_4.yaml"
    )
    contract.parent.mkdir(parents=True, exist_ok=True)

    snapshot = contract.parent / "source_prompt_snapshot.md"
    snapshot.write_bytes(paths["approved"].read_bytes())
    source_sha = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    source_rel = snapshot.relative_to(root).as_posix()
    origin_rel = paths["approved"].relative_to(root).as_posix()

    contract_data = {
        "schema_version": "module_prompt_contract_v0_4",
        "metadata": {
            "contract_id": "demo_prompt__contract_v0_4",
            "module_id": "demo",
            "prompt_id": "demo_prompt",
            "created_at": "2026-08-19",
            "status": "candidate_reference_only",
            "immutable": True,
        },
        "source_prompt": {
            "path": source_rel,
            "sha256": source_sha,
            "origin_path_at_capture": origin_rel,
            "origin_sha256_at_capture": source_sha,
        },
        "integrity": {
            "algorithm": "sha256",
            "payload_sha256": "",
            "payload_hash_scope": (
                "canonical JSON of entire document excluding "
                "integrity.payload_sha256"
            ),
        },
        "source_obligations": [
            {
                "obligation_id": "SRC-001",
                "source_locator": "demo source",
                "required": True,
                "summary": "Demo source obligation",
            }
        ],
        "implementation_obligations": [
            {"obligation_id": "IMP-001", "summary": "Implement demo"}
        ],
        "verification_obligations": [
            {"obligation_id": "VER-001", "summary": "Verify demo"}
        ],
        "completion_evidence_obligations": [
            {"obligation_id": "CE-001", "summary": "Record demo evidence"}
        ],
        "source_obligation_fidelity_ledger": [
            {
                "source_obligation_id": "SRC-001",
                "target_obligation_ids": [
                    "IMP-001",
                    "VER-001",
                    "CE-001",
                ],
            }
        ],
        "semantic_fidelity": {
            "human_review_required": True,
            "execution_fingerprint_sufficient": False,
            "review_state": "pending_operator_review",
        },
        "promotion": {
            "state": "candidate_reference_only",
            "normal_acceptance_allowed": False,
            "explicit_promotion_required": True,
            "promotion_performed": False,
        },
    }
    contract_data["integrity"]["payload_sha256"] = canonical_payload_sha256(
        contract_data
    )
    if not contract_payload_valid:
        contract_data["implementation_obligations"][0]["summary"] = (
            "tampered after payload hash"
        )
    write_yaml(contract, contract_data)

    contract_rel = contract.relative_to(root).as_posix()
    contract_sha = hashlib.sha256(contract.read_bytes()).hexdigest()

    oracle = (
        root
        / "coordination/acceptance_oracles/demo/"
        "demo_prompt_acceptance_oracle_v0_1.yaml"
    )
    oracle.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(
        oracle,
        {
            "schema_version": "blueprint_acceptance_oracle_v0_1",
            "metadata": {
                "oracle_id": "demo_prompt_acceptance_oracle_v0_1",
                "module_id": "demo",
                "prompt_id": "demo_prompt",
                "step_id": "demo_prompt",
                "owner": "forprint_system_blueprint",
                "immutable": True,
            },
            "source_prompt_contract": {
                "path": contract_rel,
                "sha256": contract_sha,
            },
            "criteria": [
                {
                    "criterion_id": "AC-001",
                    "step_id": "demo_prompt",
                    "requirement_refs": [requirement_ref],
                    "summary": "Demo acceptance criterion",
                    "blocking": True,
                    "verification": {
                        "kind": "command",
                        "locator": "make check",
                        "expected_observation": "all required checks pass",
                    },
                    "evidence_required": ["EV-FULL-GATE"],
                }
            ],
        },
    )
    oracle_rel = oracle.relative_to(root).as_posix()
    oracle_sha = hashlib.sha256(oracle.read_bytes()).hexdigest()

    roadmap = load(paths["roadmap"])
    roadmap["roadmap"][0]["acceptance"] = {
        "oracle_required": True,
        "oracle_path": oracle_rel,
        "oracle_sha256": oracle_sha,
    }
    write_yaml(paths["roadmap"], roadmap)
    request["preconditions"]["roadmap_sha256"] = module.file_sha256(
        paths["roadmap"]
    )

    evidence_file = (
        root
        / "coordination/reports/completion/"
        "demo_full_gate.txt"
    )
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text(
        "canonical demo completion evidence\n",
        encoding="utf-8",
    )
    evidence_sha = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
    evidence_rel = evidence_file.relative_to(root).as_posix()

    packet_path = root / request["review_candidate"]["packet_path"]
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet = {
        "schema_version": "module_completion_packet_v0_4",
        "protocol_version": "module_completion_packet_protocol_v0_4",
        "completion_id": packet_path.stem,
        "module_id": "demo",
        "prompt_id": "demo_prompt",
        "phase": "demo",
        "created_at": "2026-08-19T19:00:00+03:00",
        "status": "completed_in_module_pending_blueprint_review",
        "immutable": True,
        "report_id": "demo_completion_report",
        "report_path": evidence_rel,
        "report_sha256": evidence_sha,
        "implementation_base_commit": "1" * 40,
        "implementation_commit": "2" * 40,
        "branch": "feature/demo",
        "prompt_contract": {
            "schema_version": "module_prompt_contract_v0_4",
            "contract_id": contract_data["metadata"]["contract_id"],
            "path": contract_rel,
            "file_sha256": contract_sha,
            "payload_sha256": contract_data["integrity"]["payload_sha256"],
            "source_prompt_sha256": contract_data["source_prompt"]["sha256"],
        },
        "requirement_results": [
            {
                "obligation_id": "IMP-001",
                "category": "implementation",
                "result": "satisfied",
                "evidence_ids": ["EV-FULL-GATE"],
            },
            {
                "obligation_id": "VER-001",
                "category": "verification",
                "result": "satisfied",
                "evidence_ids": ["EV-FULL-GATE"],
            },
            {
                "obligation_id": "CE-001",
                "category": "completion_evidence",
                "result": "satisfied",
                "evidence_ids": ["EV-FULL-GATE"],
            },
        ],
        "checks": {
            "check_report": "passed",
            "tests": "passed",
            "governance_check": "passed",
            "check_report_passed": 1,
            "check_report_warnings": 0,
            "check_report_failed": 0,
        },
        "check_results": [
            {
                "check_id": "CHK-FULL-GATE",
                "command": "make check",
                "result": "passed",
                "evidence_ids": ["EV-FULL-GATE"],
            }
        ],
        "evidence_manifest": [
            {
                "evidence_id": "EV-FULL-GATE",
                "kind": "test_output",
                "path": evidence_rel,
                "sha256": evidence_sha,
            }
        ],
        "boundary_confirmations": {
            "automatic_acceptance_performed": False,
            "automatic_return_performed": False,
            "historical_evidence_rewritten": False,
            "prompt_contract_mutated": False,
            "rollout_or_production_write_performed": False,
            "module_write_scope_respected": True,
        },
        "semantic_fidelity": {
            "module_attests_requirement_results_complete": True,
            "human_blueprint_review_required": True,
            "execution_fingerprint_sufficient": False,
        },
        "publication": {
            "completion_commit_embedded": False,
            "remote_containment_claimed_by_packet": False,
            "external_publication_verification_required": True,
            "automatic_commit": False,
            "automatic_push": False,
        },
        "revision": {
            "supersedes_completion_id": None,
            "supersedes_packet_path": None,
            "revision_reason": None,
        },
        "promotion": {
            "state": "candidate_reference_only",
            "normal_acceptance_allowed": False,
            "promotion_performed": False,
        },
        "integrity": {
            "algorithm": "sha256",
            "payload_sha256": "",
            "payload_hash_scope": (
                "canonical JSON of entire packet excluding "
                "integrity.payload_sha256"
            ),
        },
    }
    packet["integrity"]["payload_sha256"] = completion_packet_payload_sha256(
        packet
    )
    write_yaml(packet_path, packet)
    packet_sha = hashlib.sha256(packet_path.read_bytes()).hexdigest()
    request["review_candidate"]["packet_sha256"] = packet_sha

    if include_evaluation:
        request["acceptance_oracle_evaluation"] = {
            "oracle_path": oracle_rel,
            "oracle_sha256": oracle_sha,
            "evidence_basis": {
                "event_sha256": request["review_candidate"]["event_sha256"],
                "packet_sha256": request["review_candidate"]["packet_sha256"],
                "discovery_fingerprint_sha256": request["review_candidate"][
                    "discovery_fingerprint_sha256"
                ],
            },
            "criteria_results": [
                {
                    "criterion_id": "AC-001",
                    "result": result,
                    "observed": (
                        "observed expected result"
                        if result in {"PASS", "FAIL"}
                        else None
                    ),
                    "evidence_refs": (
                        ["EV-FULL-GATE"]
                        if evidence_refs is None
                        else evidence_refs
                    ),
                }
            ],
            "waivers": (
                [
                    {
                        "criterion_id": "AC-001",
                        "explicit_operator_authorization": True,
                        "reason": "explicit bounded operator waiver",
                    }
                ]
                if waiver
                else []
            ),
        }


def test_oracle_required_accept_blocks_without_evaluation(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        include_evaluation=False,
    )
    before = {
        key: paths[key].read_bytes()
        for key in ("roadmap", "queue", "approved")
    }

    with pytest.raises(
        module.TransactionError,
        match="acceptance oracle evaluation is required",
    ):
        module.prepare_transaction(paths["root"], request)

    assert all(
        paths[key].read_bytes() == before[key]
        for key in ("roadmap", "queue", "approved")
    )


def test_oracle_blocking_fail_blocks_accept(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request, result="FAIL")

    with pytest.raises(
        module.TransactionError,
        match="unsatisfied blocking acceptance criteria",
    ):
        module.prepare_transaction(paths["root"], request)


def test_oracle_pass_requires_declared_evidence(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        result="PASS",
        evidence_refs=[],
    )

    with pytest.raises(
        module.TransactionError,
        match="unsatisfied blocking acceptance criteria",
    ):
        module.prepare_transaction(paths["root"], request)


def test_oracle_rejects_unknown_contract_requirement_ref(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        requirement_ref="IMP-999",
    )

    with pytest.raises(
        module.TransactionError,
        match="unknown contract refs",
    ):
        module.prepare_transaction(paths["root"], request)


def test_oracle_pass_allows_accept_and_records_summary(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)

    plan = module.prepare_transaction(paths["root"], request)
    assert plan["acceptance_oracle"]["required"] is True
    assert plan["acceptance_oracle"]["gate"] == "PASS"
    assert plan["acceptance_oracle"]["pass_count"] == 1
    assert plan["acceptance_oracle"]["waived_count"] == 0

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    assert result["result_state"] == "ACCEPT_APPLIED"

    evidence = load(
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    )
    oracle = evidence["acceptance_oracle"]
    assert oracle["required"] is True
    assert oracle["gate"] == "PASS"
    assert oracle["criteria_results"][0]["criterion_id"] == "AC-001"
    assert oracle["criteria_results"][0]["evidence_complete"] is True


def test_oracle_explicit_waiver_allows_accept_and_is_recorded(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        result="FAIL",
        waiver=True,
    )

    plan = module.prepare_transaction(paths["root"], request)
    assert plan["acceptance_oracle"]["gate"] == "PASS"
    assert plan["acceptance_oracle"]["waived_count"] == 1

    module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    evidence = load(
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    )
    assert evidence["acceptance_oracle"]["waivers"][0][
        "explicit_operator_authorization"
    ] is True


def test_return_does_not_require_oracle_evaluation(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "RETURN")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        include_evaluation=False,
    )

    plan = module.prepare_transaction(paths["root"], request)
    assert plan["acceptance_oracle"] == {
        "required": False,
        "gate": "NOT_APPLICABLE_TO_RETURN_HOLD",
    }


def test_oracle_reuses_canonical_prompt_contract_validator(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        contract_payload_valid=False,
    )

    with pytest.raises(
        module.TransactionError,
        match="canonical validation failed",
    ):
        module.prepare_transaction(paths["root"], request)


def test_oracle_evaluation_is_bound_to_exact_completion_candidate(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)
    request["acceptance_oracle_evaluation"]["evidence_basis"][
        "packet_sha256"
    ] = "d" * 64

    with pytest.raises(
        module.TransactionError,
        match="evidence_basis does not match",
    ):
        module.prepare_transaction(paths["root"], request)


def test_legacy_accept_rejects_stray_oracle_evaluation(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    request["acceptance_oracle_evaluation"] = {"unexpected": True}

    with pytest.raises(
        module.TransactionError,
        match="does not require an oracle",
    ):
        module.prepare_transaction(paths["root"], request)


def test_oracle_same_decision_exact_evaluation_is_idempotent(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)

    first = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    second = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    assert first["result_state"] == "ACCEPT_APPLIED"
    assert second["result_state"] == "ALREADY_APPLIED"
    assert second["idempotent_noop"] is True


def test_oracle_same_decision_changed_observation_fails_safely(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)

    module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    changed = copy.deepcopy(request)
    changed["acceptance_oracle_evaluation"]["criteria_results"][0][
        "observed"
    ] = "different observed evidence"

    with pytest.raises(
        module.TransactionError,
        match="review evidence collision with a different decision identity",
    ):
        module.apply_transaction(
            paths["root"],
            changed,
            operator_confirmation="decision_demo_001",
        )


def test_oracle_same_decision_changed_waiver_reason_fails_safely(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        result="FAIL",
        waiver=True,
    )

    module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    changed = copy.deepcopy(request)
    changed["acceptance_oracle_evaluation"]["waivers"][0][
        "reason"
    ] = "different waiver authorization basis"

    with pytest.raises(
        module.TransactionError,
        match="review evidence collision with a different decision identity",
    ):
        module.apply_transaction(
            paths["root"],
            changed,
            operator_confirmation="decision_demo_001",
        )


def test_oracle_same_decision_changed_candidate_hash_fails_safely(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)

    module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    changed = copy.deepcopy(request)
    changed["review_candidate"]["packet_sha256"] = "e" * 64

    with pytest.raises(
        module.TransactionError,
        match="review evidence collision with a different decision identity",
    ):
        module.apply_transaction(
            paths["root"],
            changed,
            operator_confirmation="decision_demo_001",
        )


def test_oracle_rejects_evidence_ref_not_in_completion_packet(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(
        module,
        paths,
        request,
        evidence_refs=["EV-FABRICATED"],
    )

    with pytest.raises(
        module.TransactionError,
        match="not present in the validated completion packet evidence_manifest",
    ):
        module.prepare_transaction(paths["root"], request)


def test_oracle_pass_is_grounded_in_validated_packet_evidence(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)

    plan = module.prepare_transaction(paths["root"], request)
    oracle = plan["acceptance_oracle"]
    assert oracle["completion_packet"]["canonical_validation"] == "PASSED"
    assert oracle["criteria_results"][0][
        "required_evidence_manifested"
    ] is True
    assert oracle["criteria_results"][0][
        "requirement_evidence_complete"
    ] is True
    assert oracle["criteria_results"][0]["evidence_complete"] is True


def test_oracle_rejects_candidate_packet_sha_drift(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")
    enable_acceptance_oracle(module, paths, request)

    packet_path = paths["root"] / request["review_candidate"]["packet_path"]
    packet_path.write_text(
        packet_path.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )

    with pytest.raises(
        module.TransactionError,
        match="completion packet SHA mismatch",
    ):
        module.prepare_transaction(paths["root"], request)


def test_module_schema_accept_plan_is_read_only(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    before = {
        key: paths[key].read_bytes()
        for key in ("roadmap", "queue", "approved")
    }

    plan = module.prepare_transaction(paths["root"], request)

    assert plan["result_state"] == "READY_TO_APPLY"
    assert plan["transaction"]["roadmap_status_before"] == "active"
    assert plan["transaction"]["roadmap_status_after"] == "accepted"
    assert plan["transaction"]["queue_status_before"] == "approved"
    assert plan["transaction"]["queue_status_after"] == "completed"
    assert (
        plan["transaction"]["queue_execution_status_after"]
        == "completed_by_module"
    )
    assert (
        plan["transaction"]["queue_review_status_after"]
        == "accepted_by_blueprint"
    )
    assert plan["boundaries"]["next_prompt_activation_performed"] is False

    for key in ("roadmap", "queue", "approved"):
        assert paths[key].read_bytes() == before[key]


def test_module_schema_accept_applies_canonical_fields(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])
    step = roadmap["roadmap"][0]
    next_step = roadmap["roadmap"][1]
    prompt = queue["prompt_queue"][0]

    completed = (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    )
    evidence_path = (
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    )

    assert result["result_state"] == "ACCEPT_APPLIED"
    assert result["module_repository_writes"] is False
    assert result["next_prompt_selection_performed"] is False
    assert result["next_prompt_activation_performed"] is False
    assert result["global_v0_4_promotion_performed"] is False

    assert step["status"] == "accepted"
    assert step["operator_decision"] == "ACCEPT"
    assert step["evidence"]["blueprint_review_status"] == (
        "accepted_by_blueprint"
    )
    assert next_step["depends_on"][0]["status"] == "accepted"

    assert prompt["module_execution"]["status"] == "completed_by_module"
    assert prompt["blueprint_review"]["status"] == "accepted_by_blueprint"
    assert prompt["blueprint_review"]["accepted_at"] == "2026-08-18"
    assert prompt["operator_decision"] == "ACCEPT"
    assert prompt["file"] == "completed/demo_prompt.md"

    assert not paths["approved"].exists()
    assert completed.is_file()
    assert completed.read_text(encoding="utf-8") == "# Demo prompt\n"
    assert evidence_path.is_file()

    evidence = load(evidence_path)
    assert evidence["result"] == "ACCEPTED"
    assert evidence["decision"]["explicit_operator_input"] is True
    assert evidence["transaction"]["queue_review_status_before"] == (
        "not_started"
    )
    assert evidence["transaction"]["queue_review_status_after"] == (
        "accepted_by_blueprint"
    )
    assert evidence["transaction"]["eligible_step_ids_after_transaction"] == [
        "demo_next"
    ]


def test_module_schema_accept_is_idempotent(tmp_path: Path) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    first = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )
    roadmap_after = paths["roadmap"].read_bytes()
    queue_after = paths["queue"].read_bytes()

    second = module.apply_transaction(
        paths["root"],
        copy.deepcopy(request),
        operator_confirmation="decision_demo_001",
    )

    assert first["result_state"] == "ACCEPT_APPLIED"
    assert second["result_state"] == "ALREADY_APPLIED"
    assert second["idempotent_noop"] is True
    assert paths["roadmap"].read_bytes() == roadmap_after
    assert paths["queue"].read_bytes() == queue_after


def test_module_schema_accept_rolls_back_exactly(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "ACCEPT")

    before = {
        key: paths[key].read_bytes()
        for key in ("roadmap", "queue", "approved")
    }

    def fail() -> None:
        raise RuntimeError("synthetic post-write validation failure")

    with pytest.raises(
        RuntimeError,
        match="synthetic post-write validation failure",
    ):
        module.apply_transaction(
            paths["root"],
            request,
            operator_confirmation="decision_demo_001",
            post_write_validator=fail,
        )

    for key in ("roadmap", "queue", "approved"):
        assert paths[key].read_bytes() == before[key]

    assert not (
        paths["root"]
        / "coordination/outgoing_prompts/demo/completed/demo_prompt.md"
    ).exists()
    assert not (
        paths["root"]
        / "coordination/review_packets/demo/processed/"
        "decision_demo_001.yaml"
    ).exists()


def test_module_schema_return_uses_legacy_status_contract(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "RETURN")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])

    assert result["result_state"] == "RETURN_APPLIED"
    assert roadmap["roadmap"][0]["status"] == "active"
    assert queue["prompt_queue"][0]["module_execution"]["status"] == (
        "returned_for_fix"
    )
    assert queue["prompt_queue"][0]["blueprint_review"]["status"] == (
        "returned_for_fix"
    )
    assert queue["prompt_queue"][0]["file"] == "approved/demo_prompt.md"
    assert paths["approved"].is_file()


def test_module_schema_hold_preserves_module_completion(
    tmp_path: Path,
) -> None:
    module = tool_module()
    paths = fixture_state(tmp_path)
    request = request_for(module, paths, "HOLD")

    result = module.apply_transaction(
        paths["root"],
        request,
        operator_confirmation="decision_demo_001",
    )

    roadmap = load(paths["roadmap"])
    queue = load(paths["queue"])

    assert result["result_state"] == "HOLD_APPLIED"
    assert roadmap["roadmap"][0]["status"] == "active"
    assert queue["prompt_queue"][0]["module_execution"]["status"] == (
        "completed_by_module"
    )
    assert queue["prompt_queue"][0]["blueprint_review"]["status"] == (
        "pending_review"
    )
    assert paths["approved"].is_file()
