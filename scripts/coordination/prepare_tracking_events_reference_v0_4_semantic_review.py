from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

import yaml

CONTRACT = Path(
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1/"
    "logistics_service_tracking_events_v0_1__contract_v0_4_reference_v0_2.yaml"
)
OUTPUT = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_semantic_fidelity_review_packet_v0_1.yaml"
)
EXPECTED_FILE_SHA256 = "73f0fe602398536c940f3a6295a3b7d3263f302fba65b68e21d5c90355250981"
EXPECTED_PAYLOAD_SHA256 = "02775affa37cd6b21c8251dd05f379cb727bfecd9bebe6f948d2ac8b987c2138"

EXPECTED_IDS = [
    "SRC-001", "SRC-002", "SRC-003", "SRC-004", "SRC-005", "SRC-006",
    "SRC-007", "SRC-008", "SRC-009", "SRC-010", "SRC-011", "SRC-012",
    "SRC-013", "SRC-014", "SRC-015", "SRC-016", "SRC-017", "SRC-018",
    "SRC-019", "SRC-020", "SRC-021", "SRC-022", "SRC-023", "SRC-024",
    "SRC-R01", "SRC-R02",
]

COVERAGE_DIMENSIONS = [
    "accepted foundation and Git workflow",
    "ownership boundaries",
    "canonical event taxonomy",
    "typed event envelope",
    "lifecycle and provider normalization",
    "notification projection",
    "correlation causation idempotency and replay",
    "synthetic fixtures",
    "Make-first read-only preview",
    "architecture runbook and recovery",
    "local persistence boundary",
    "Telegram handoff evidence",
    "Telegram-side questions",
    "detailed required test catalog",
    "exact focused and full-suite totals",
    "required command set",
    "generated artifact handling",
    "completion output paths",
    "completion packet and report content",
    "completion automation idempotency",
    "compact final handoff",
    "explicit non-goals",
    "Definition of Done implementation semantics",
    "Definition of Done delivery evidence",
    "required Blueprint governance reading",
    "accepted Logistics artifact review and authoritative-path reuse",
]


def validator_module(root: Path):
    path = root / "scripts/coordination/validate_prompt_contract_v0_4.py"
    spec = importlib.util.spec_from_file_location("validate_prompt_contract_v0_4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    contract_path = root / CONTRACT
    if not contract_path.is_file():
        raise RuntimeError(f"missing v0.2 contract: {contract_path}")

    file_sha = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    if file_sha != EXPECTED_FILE_SHA256:
        raise RuntimeError(f"immutable contract file hash mismatch: {file_sha}")

    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    payload_sha = contract["integrity"]["payload_sha256"]
    if payload_sha != EXPECTED_PAYLOAD_SHA256:
        raise RuntimeError(f"immutable contract payload hash mismatch: {payload_sha}")

    validation = validator_module(root).validate_contract(root, contract_path)
    if validation["result"] != "PASSED":
        raise RuntimeError(f"machine validator is not PASSED: {validation}")

    obligations = contract["source_obligations"]
    actual_ids = [item["obligation_id"] for item in obligations]
    if actual_ids != EXPECTED_IDS:
        raise RuntimeError(f"unexpected source obligation identity/order: {actual_ids}")

    ledger = {
        item["source_obligation_id"]: item["target_obligation_ids"]
        for item in contract["source_obligation_fidelity_ledger"]
    }
    if set(ledger) != set(EXPECTED_IDS):
        raise RuntimeError("fidelity ledger does not cover exactly 26 source obligations")

    review_items = []
    for index, obligation in enumerate(obligations):
        oid = obligation["obligation_id"]
        targets = ledger[oid]
        if not targets:
            raise RuntimeError(f"unmapped source obligation: {oid}")
        review_items.append(
            {
                "source_obligation_id": oid,
                "source_locator": obligation["source_locator"],
                "required": obligation["required"],
                "summary": obligation["summary"],
                "mapped_target_obligation_ids": targets,
                "assistant_semantic_assessment": "COVERED",
                "coverage_dimension": COVERAGE_DIMENSIONS[index],
            }
        )

    packet = {
        "schema_version": "blueprint_tracking_events_v0_4_semantic_fidelity_review_packet_v0_1",
        "metadata": {
            "owner": "forprint_system_blueprint",
            "step_id": "blueprint_v0_4_tracking_events_reference_v0_1",
            "subject": "logistics_service_tracking_events_v0_1",
            "created_at": "2026-08-17",
            "state": "READY_FOR_OPERATOR_SEMANTIC_FIDELITY_DECISION",
        },
        "candidate": {
            "contract": str(CONTRACT),
            "contract_file_sha256": file_sha,
            "contract_payload_sha256": payload_sha,
            "machine_validation": "PASSED",
            "source_obligation_count": 26,
            "fidelity_mapping_count": 26,
        },
        "review_basis": {
            "source_prompt_snapshot": contract["source_prompt"]["path"],
            "source_prompt_sha256": contract["source_prompt"]["sha256"],
            "legacy_v0_3_contract": (
                "coordination/prompt_contracts/logistics_service/"
                "logistics_service_tracking_events_v0_1.yaml"
            ),
            "pre_review_findings": (
                "coordination/internal_work/blueprint/governance/"
                "2026-08-17__blueprint__tracking_events_v0_4_reference_semantic_pre_review_findings_v0_1.yaml"
            ),
        },
        "assistant_review": {
            "result": "PASS_RECOMMENDED",
            "covered_source_obligations": 26,
            "uncovered_source_obligations": 0,
            "blocking_semantic_gaps": [],
            "rationale": (
                "All mandatory source-prompt sections are represented as explicit "
                "source obligations and mapped to implementation, verification, or "
                "completion-evidence obligations. The two gaps found in v0.1 were "
                "added as SRC-R01 and SRC-R02 in immutable v0.2."
            ),
        },
        "review_items": review_items,
        "operator_gate": {
            "decision_required": True,
            "allowed_decisions": [
                "ACCEPT_SEMANTIC_FIDELITY",
                "RETURN_FOR_SEMANTIC_REVISION",
                "HOLD_SEMANTIC_FIDELITY",
            ],
            "decision": None,
            "decision_recorded_automatically": False,
            "tracking_events_lifecycle_acceptance_implied": False,
        },
        "boundaries": {
            "module_repository_writes": False,
            "completion_packet_v0_4_fabricated_by_blueprint": False,
            "completion_outbox_v0_4_fabricated_by_blueprint": False,
            "tracking_events_acceptance_created": False,
            "dark_zone_audit_run": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
            "rollout_or_production_write": False,
        },
    }

    content = yaml.safe_dump(packet, sort_keys=False, allow_unicode=True, width=110)
    output = root / OUTPUT
    if output.exists():
        if output.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"existing semantic review packet differs: {output}")
        print(f"UNCHANGED: {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"CREATED: {output}")

    print(f"CONTRACT_FILE_SHA256={file_sha}")
    print(f"CONTRACT_PAYLOAD_SHA256={payload_sha}")
    print("SEMANTIC_COVERAGE=26/26")
    print("ASSISTANT_RECOMMENDATION=PASS")
    print("OPERATOR_DECISION_RECORDED=false")
    print("module_repository_writes: false")
    print("tracking_events_acceptance_created: false")
    print("dark_zone_audit_run: false")
    print("global_v0_4_promotion_performed: false")
    print("RESULT: READY_FOR_OPERATOR_SEMANTIC_FIDELITY_DECISION")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
