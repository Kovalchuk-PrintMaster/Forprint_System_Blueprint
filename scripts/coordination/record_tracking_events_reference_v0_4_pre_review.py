from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

V0_1_CONTRACT = Path(
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1/"
    "logistics_service_tracking_events_v0_1__contract_v0_4_reference_v0_1.yaml"
)
OUTPUT = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_reference_semantic_pre_review_findings_v0_1.yaml"
)
EXPECTED_PAYLOAD = "2fb3e14490e8a75693a37e2a19f136148f253a5375f1b662212e1482858df301"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    contract_path = root / V0_1_CONTRACT
    if not contract_path.is_file():
        raise RuntimeError(f"missing v0.1 candidate: {contract_path}")

    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    payload = contract["integrity"]["payload_sha256"]
    if payload != EXPECTED_PAYLOAD:
        raise RuntimeError(
            f"unexpected v0.1 payload hash: {payload}; expected {EXPECTED_PAYLOAD}"
        )

    evidence = {
        "schema_version": "blueprint_tracking_events_v0_4_semantic_pre_review_findings_v0_1",
        "metadata": {
            "owner": "forprint_system_blueprint",
            "step_id": "blueprint_v0_4_tracking_events_reference_v0_1",
            "subject": "logistics_service_tracking_events_v0_1",
            "created_at": "2026-08-17",
            "state": "REVISION_REQUIRED_BEFORE_OPERATOR_SEMANTIC_REVIEW",
        },
        "candidate": {
            "contract": str(V0_1_CONTRACT),
            "payload_sha256": payload,
            "machine_validation": "PASSED",
            "source_obligation_count": len(contract["source_obligations"]),
        },
        "semantic_findings": [
            {
                "finding_id": "TE-V04-FIDELITY-001",
                "severity": "blocking",
                "source_locator": "Required reading before implementation",
                "finding": (
                    "The v0.1 reference candidate did not model the mandatory reading "
                    "of current Blueprint governance sources through the approved "
                    "Blueprint pull and prompt-navigation workflow as an explicit source obligation."
                ),
            },
            {
                "finding_id": "TE-V04-FIDELITY-002",
                "severity": "blocking",
                "source_locator": "Required reading before implementation / existing equivalents",
                "finding": (
                    "The v0.1 reference candidate did not separately model review/reuse "
                    "of accepted Logistics provider-contract/runbook/recovery evidence, "
                    "authoritative-path reuse, and the prohibition on duplicate domain hierarchies."
                ),
            },
        ],
        "recommended_revision": {
            "disposition": "REVISE_CANDIDATE",
            "new_contract_id": (
                "logistics_service_tracking_events_v0_1__"
                "contract_v0_4_reference_v0_2"
            ),
            "preserve_v0_1_instance": True,
            "required_new_source_obligations": 2,
            "operator_semantic_review_after_revision": True,
        },
        "boundaries": {
            "operator_lifecycle_decision_created": False,
            "module_repository_writes": False,
            "completion_packet_v0_4_fabricated_by_blueprint": False,
            "completion_outbox_v0_4_fabricated_by_blueprint": False,
            "dark_zone_audit_run": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }

    content = yaml.safe_dump(
        evidence, sort_keys=False, allow_unicode=True, width=110
    )
    out = root / OUTPUT
    if out.exists():
        if out.read_text(encoding="utf-8") != content:
            raise RuntimeError(f"existing findings differ; refusing overwrite: {out}")
        print(f"UNCHANGED: {out}")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"CREATED: {out}")

    print("semantic_gate: REVISION_REQUIRED")
    print("operator_lifecycle_decision_created: false")
    print("module_repository_writes: false")
    print("RESULT: TRACKING_EVENTS_V0_4_PRE_REVIEW_FINDINGS_RECORDED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
