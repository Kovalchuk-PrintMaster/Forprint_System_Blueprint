from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import yaml

CONTRACT = Path(
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1/"
    "logistics_service_tracking_events_v0_1__contract_v0_4_reference_v0_2.yaml"
)
REVIEW_PACKET = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_semantic_fidelity_review_packet_v0_1.yaml"
)
OUTPUT = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_semantic_fidelity_operator_decision_v0_1.yaml"
)

EXPECTED_CONTRACT_FILE_SHA256 = "73f0fe602398536c940f3a6295a3b7d3263f302fba65b68e21d5c90355250981"
EXPECTED_CONTRACT_PAYLOAD_SHA256 = "02775affa37cd6b21c8251dd05f379cb727bfecd9bebe6f948d2ac8b987c2138"

ALLOWED = {
    "ACCEPT_SEMANTIC_FIDELITY",
    "RETURN_FOR_SEMANTIC_REVISION",
    "HOLD_SEMANTIC_FIDELITY",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected YAML mapping: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--decision", required=True)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    decision = args.decision.strip()

    if decision not in ALLOWED:
        raise RuntimeError(
            f"unsupported decision {decision!r}; allowed={sorted(ALLOWED)}"
        )

    contract_path = root / CONTRACT
    review_path = root / REVIEW_PACKET

    for path in (contract_path, review_path):
        if not path.is_file():
            raise RuntimeError(f"missing required review artifact: {path}")

    contract_file_sha = sha256_file(contract_path)
    if contract_file_sha != EXPECTED_CONTRACT_FILE_SHA256:
        raise RuntimeError(
            "immutable v0.2 contract file hash mismatch: "
            f"{contract_file_sha}"
        )

    contract = load_yaml(contract_path)
    payload_sha = contract["integrity"]["payload_sha256"]
    if payload_sha != EXPECTED_CONTRACT_PAYLOAD_SHA256:
        raise RuntimeError(
            "immutable v0.2 payload hash mismatch: "
            f"{payload_sha}"
        )

    review = load_yaml(review_path)
    if review["metadata"]["state"] != "READY_FOR_OPERATOR_SEMANTIC_FIDELITY_DECISION":
        raise RuntimeError("semantic review packet is not ready for operator decision")
    if review["assistant_review"]["result"] != "PASS_RECOMMENDED":
        raise RuntimeError("semantic review packet does not recommend PASS")
    if review["assistant_review"]["covered_source_obligations"] != 26:
        raise RuntimeError("semantic review coverage is not 26/26")
    if review["assistant_review"]["uncovered_source_obligations"] != 0:
        raise RuntimeError("semantic review has uncovered obligations")
    if review["assistant_review"]["blocking_semantic_gaps"]:
        raise RuntimeError("semantic review still contains blocking gaps")

    gate = review["operator_gate"]
    if gate["decision"] is not None:
        raise RuntimeError("review packet unexpectedly already contains a decision")
    if decision not in gate["allowed_decisions"]:
        raise RuntimeError("decision is not allowed by semantic review packet")

    review_sha = sha256_file(review_path)

    record = {
        "schema_version": "blueprint_tracking_events_v0_4_semantic_fidelity_operator_decision_v0_1",
        "metadata": {
            "owner": "forprint_system_blueprint",
            "step_id": "blueprint_v0_4_tracking_events_reference_v0_1",
            "subject": "logistics_service_tracking_events_v0_1",
            "created_at": "2026-08-17",
            "state": "RECORDED",
        },
        "decision": {
            "value": decision,
            "scope": "prompt_contract_semantic_fidelity_only",
            "contract": str(CONTRACT),
            "contract_file_sha256": contract_file_sha,
            "contract_payload_sha256": payload_sha,
            "semantic_review_packet": str(REVIEW_PACKET),
            "semantic_review_packet_sha256": review_sha,
            "semantic_coverage": "26/26",
            "assistant_recommendation": "PASS",
        },
        "effects": {
            "semantic_fidelity_accepted": decision == "ACCEPT_SEMANTIC_FIDELITY",
            "tracking_events_completion_accepted": False,
            "tracking_events_lifecycle_decision_created": False,
            "roadmap_advanced": False,
            "prompt_queue_advanced": False,
            "module_repository_writes": False,
            "completion_packet_v0_4_fabricated_by_blueprint": False,
            "completion_outbox_v0_4_fabricated_by_blueprint": False,
            "dark_zone_audit_run": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
            "rollout_or_production_write": False,
        },
        "next_gate": {
            "if_accepted": (
                "seal Blueprint-owned STEP27 prompt-contract semantic layer, then "
                "proceed to module-owned v0.4 completion evidence"
            ),
            "tracking_events_acceptance_still_requires_separate_operator_decision": True,
        },
    }

    content = yaml.safe_dump(
        record,
        sort_keys=False,
        allow_unicode=True,
        width=110,
    )

    output = root / OUTPUT
    if output.exists():
        existing = output.read_text(encoding="utf-8")
        if existing != content:
            raise RuntimeError(
                f"existing operator decision record differs; refusing overwrite: {output}"
            )
        print(f"UNCHANGED: {output}")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"CREATED: {output}")

    print(f"DECISION={decision}")
    print("SEMANTIC_COVERAGE=26/26")
    print(
        "SEMANTIC_FIDELITY_ACCEPTED="
        + str(decision == "ACCEPT_SEMANTIC_FIDELITY").lower()
    )
    print("TRACKING_EVENTS_COMPLETION_ACCEPTED=false")
    print("ROADMAP_ADVANCED=false")
    print("MODULE_REPOSITORY_WRITES=false")
    print("DARK_ZONE_AUDIT_RUN=false")
    print("GLOBAL_V0_4_PROMOTION_PERFORMED=false")
    print("RESULT: TRACKING_EVENTS_V0_4_SEMANTIC_FIDELITY_DECISION_RECORDED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
