from __future__ import annotations

import copy
import hashlib
import importlib.util
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STANDARD = ROOT / "coordination/standards/governance/module_completion_packet_v0_4.yaml"
TEMPLATE = ROOT / "coordination/templates/module_completion_packet_v0_4.example.yaml"
VALIDATOR = ROOT / "scripts/coordination/validate_completion_packet_v0_4.py"
HANDOFF = ROOT / "coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml"
ROADMAP = ROOT / "coordination/self_coordination/roadmap.yaml"
QUEUE = ROOT / "coordination/self_coordination/prompt_queue/index.yaml"
REVISION = ROOT / "coordination/revisions/current.yaml"
PROMPT_CONTRACT = ROOT / (
    "coordination/prompt_contracts/forprint_system_blueprint/"
    "blueprint_v0_4_immutable_prompt_contract_v0_1/"
    "blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml"
)
STEP22 = "blueprint_v0_4_completion_packet_v0_1"


def load(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def validator_module():
    spec = importlib.util.spec_from_file_location("completion_packet_v0_4", VALIDATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(tmp_path: Path) -> tuple[Path, dict, object]:
    module = validator_module()
    root = tmp_path / "module"
    contract_rel = Path(
        "coordination/prompt_contracts/forprint_system_blueprint/"
        "blueprint_v0_4_immutable_prompt_contract_v0_1/"
        "blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml"
    )
    contract_path = root / contract_rel
    contract_path.parent.mkdir(parents=True)
    shutil.copyfile(PROMPT_CONTRACT, contract_path)
    contract = load(contract_path)

    report_rel = Path("reports/completion.md")
    report_path = root / report_rel
    report_path.parent.mkdir(parents=True)
    report_path.write_text("completion evidence\n", encoding="utf-8")
    report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest()

    expected: list[tuple[str, str]] = []
    for field, category in (
        ("implementation_obligations", "implementation"),
        ("verification_obligations", "verification"),
        ("completion_evidence_obligations", "completion_evidence"),
    ):
        expected.extend((item["obligation_id"], category) for item in contract[field])

    completion_id = "fixture_completion_v0_1"
    packet_path = root / "coordination/completion_packets/records" / f"{completion_id}.yaml"
    packet_path.parent.mkdir(parents=True)

    packet = {
        "schema_version": "module_completion_packet_v0_4",
        "protocol_version": "module_completion_packet_protocol_v0_4",
        "completion_id": completion_id,
        "module_id": contract["metadata"]["module_id"],
        "prompt_id": contract["metadata"]["prompt_id"],
        "phase": "implementation",
        "created_at": "2026-08-15T20:16:00+03:00",
        "status": "completed_in_module_pending_blueprint_review",
        "immutable": True,
        "report_id": "fixture_report_v0_1",
        "report_path": report_rel.as_posix(),
        "report_sha256": report_sha,
        "implementation_base_commit": "1" * 40,
        "implementation_commit": "2" * 40,
        "branch": "feature/fixture",
        "prompt_contract": {
            "schema_version": "module_prompt_contract_v0_4",
            "contract_id": contract["metadata"]["contract_id"],
            "path": contract_rel.as_posix(),
            "file_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            "payload_sha256": contract["integrity"]["payload_sha256"],
            "source_prompt_sha256": contract["source_prompt"]["sha256"],
        },
        "requirement_results": [
            {
                "obligation_id": obligation_id,
                "category": category,
                "result": "satisfied",
                "evidence_ids": ["EV-001"],
                "notes": "fixture",
            }
            for obligation_id, category in expected
        ],
        "checks": {
            "check_report": "passed",
            "tests": "passed",
            "governance_check": "passed",
            "check_report_passed": 3,
            "check_report_warnings": 0,
            "check_report_failed": 0,
        },
        "check_results": [
            {
                "check_id": "CHECK-REPORT",
                "command": "make check",
                "result": "passed",
                "evidence_ids": ["EV-001"],
            },
            {
                "check_id": "TESTS",
                "command": "python -m pytest -q",
                "result": "passed",
                "evidence_ids": ["EV-001"],
            },
            {
                "check_id": "GOVERNANCE",
                "command": "make governance-check",
                "result": "passed",
                "evidence_ids": ["EV-001"],
            },
        ],
        "evidence_manifest": [
            {
                "evidence_id": "EV-001",
                "kind": "report",
                "path": report_rel.as_posix(),
                "sha256": report_sha,
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
                "canonical JSON of entire packet excluding integrity.payload_sha256"
            ),
        },
    }
    packet["integrity"]["payload_sha256"] = module.canonical_payload_sha256(packet)
    packet_path.write_text(
        yaml.safe_dump(packet, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return root, packet_path, packet, module


def recompute(packet: dict, module: object) -> None:
    packet["integrity"]["payload_sha256"] = module.canonical_payload_sha256(packet)


def test_standard_is_candidate_reference_only_and_non_promoting() -> None:
    standard = load(STANDARD)
    assert standard["schema_version"] == "module_completion_packet_standard_v0_4"
    assert standard["metadata"]["status"] == "candidate_reference_only"
    assert standard["instance"]["immutable"] is True
    assert standard["instance"]["historical_packet_mutation_allowed"] is False
    assert standard["semantic_fidelity"]["human_blueprint_review_required"] is True
    assert standard["semantic_fidelity"]["execution_fingerprint_sufficient"] is False
    assert standard["publication"]["completion_commit_embedded_in_packet"] is False
    assert standard["publication"]["remote_containment_claimed_by_packet"] is False
    assert standard["promotion"]["normal_acceptance_allowed"] is False
    assert standard["promotion"]["promotion_performed"] is False


def test_template_passes_template_validation() -> None:
    module = validator_module()
    report = module.validate_packet(ROOT, TEMPLATE, template_mode=True)
    assert report["result"] == "PASSED", report
    assert report["errors"] == []


def test_valid_packet_covers_all_bound_prompt_contract_obligations(tmp_path: Path) -> None:
    root, packet_path, _, module = fixture(tmp_path)
    report = module.validate_packet(root, packet_path)
    assert report["result"] == "PASSED", report
    assert report["errors"] == []
    assert report["summary"]["bound_contract_obligations"] == 19
    assert report["summary"]["requirement_results"] == 19


def test_contract_file_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["prompt_contract"]["file_sha256"] = "0" * 64
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert "prompt contract file SHA-256 mismatch" in report["errors"]


def test_missing_and_unknown_contract_obligations_are_rejected(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["requirement_results"].pop()
    packet["requirement_results"].append(
        {
            "obligation_id": "UNKNOWN-001",
            "category": "implementation",
            "result": "satisfied",
            "evidence_ids": ["EV-001"],
        }
    )
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert any(
        x.startswith("missing prompt-contract obligation results:") for x in report["errors"]
    )
    assert any(
        x.startswith("unknown prompt-contract obligation results:") for x in report["errors"]
    )


def test_duplicate_requirement_ids_are_rejected(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["requirement_results"].append(copy.deepcopy(packet["requirement_results"][0]))
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert any(x.startswith("duplicate requirement obligation_id:") for x in report["errors"])


def test_unknown_evidence_reference_is_rejected(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["requirement_results"][0]["evidence_ids"] = ["NO-EVIDENCE"]
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert any("unknown evidence reference" in x for x in report["errors"])


def test_required_check_failure_is_rejected(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["checks"]["tests"] = "failed"
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert "checks.tests is not successful" in report["errors"]


def test_superseding_revision_requires_complete_triple(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["revision"]["supersedes_completion_id"] = "old_completion"
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert "superseding packet fields must be provided together" in report["errors"]


def test_module_packet_cannot_create_blueprint_operator_decision(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["operator_decision"] = "ACCEPT"
    recompute(packet, module)
    report = module.validate_packet(root, packet_path, packet)
    assert any(
        "must not contain Blueprint decision field: operator_decision" in x
        for x in report["errors"]
    )


def test_packet_payload_integrity_is_enforced(tmp_path: Path) -> None:
    root, packet_path, packet, module = fixture(tmp_path)
    packet["branch"] = "tampered"
    report = module.validate_packet(root, packet_path, packet)
    assert "completion packet payload SHA-256 mismatch" in report["errors"]


def test_step22_implementation_does_not_advance_lifecycle_or_promote() -> None:
    roadmap = load(ROADMAP)
    queue = load(QUEUE)
    handoff = load(HANDOFF)

    step22 = next(x for x in roadmap["steps"] if x["step_id"] == STEP22)
    packet_state = handoff["completion_packet_v0_4"]
    current_id = roadmap["metadata"]["current_step_id"]
    step23 = "blueprint_v0_4_completion_outbox_v0_1"
    step24 = "blueprint_v0_4_completion_discovery_and_intake_v0_1"

    assert current_id in {STEP22, step23, step24}
    assert queue["metadata"]["active_prompt_id"] == current_id

    prompt22 = next(x for x in queue["prompts"] if x["prompt_id"] == STEP22)
    if current_id == STEP22:
        assert step22["status"] == "active"
        assert prompt22["status"] == "approved"
        assert prompt22["execution_status"] == "ready_for_module_pull"
        assert packet_state["implementation_status"] == "READY_FOR_OPERATOR_REVIEW"
        assert packet_state["operator_decision_created"] is False
    else:
        assert step22["status"] == "completed"
        assert step22["operator_decision"] == "ACCEPT"
        assert prompt22["status"] == "completed"
        assert prompt22["execution_status"] == "accepted"
        assert prompt22["operator_decision"] == "ACCEPT"
        assert packet_state["implementation_status"] == "accepted_v0_4"
        assert packet_state["operator_decision_created"] is True
        assert packet_state["operator_decision"] == "ACCEPT"

    if current_id == step23:
        prompt23 = next(
            x for x in queue["prompts"] if x["prompt_id"] == step23
        )
        assert prompt23["status"] == "approved"
        assert prompt23["execution_status"] == "ready_for_module_pull"
    elif current_id == step24:
        prompt23 = next(
            x for x in queue["prompts"] if x["prompt_id"] == step23
        )
        prompt24 = next(
            x for x in queue["prompts"] if x["prompt_id"] == step24
        )
        assert prompt23["status"] == "completed"
        assert prompt23["execution_status"] == "accepted"
        assert prompt23["operator_decision"] == "ACCEPT"
        assert prompt24["status"] == "approved"
        assert prompt24["execution_status"] == "ready_for_module_pull"

    assert packet_state["status"] == "candidate_reference_only"
    assert packet_state["promotion_performed"] is False
    assert packet_state["completion_outbox_implemented"] is False
    assert packet_state["completion_discovery_or_intake_implemented"] is False
    assert packet_state["module_repository_writes"] is False
    assert packet_state["automatic_commit"] is False
    assert packet_state["automatic_push"] is False

def test_operational_v02_and_candidate_v03_revision_registry_are_unchanged() -> None:
    revision = load(REVISION)
    operational = revision["operational_current"]
    candidate = revision["candidate_next"]
    assert operational["completion_packet"] == "module_completion_packet_v0_2"
    assert operational["completion_intake"] == "blueprint_completion_intake_v0_2"
    assert operational["normal_acceptance_allowed"] is True
    assert candidate["prompt_contract"] == "module_prompt_contract_v0_3"
    assert candidate["completion_packet"] == "module_completion_packet_v0_3"
    assert candidate["completion_intake"] == "blueprint_completion_intake_v0_3"
    assert candidate["activation_state"] == "reference_validation"
    assert candidate["normal_acceptance_allowed"] is False
