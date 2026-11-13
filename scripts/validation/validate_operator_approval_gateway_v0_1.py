from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination import build_operator_approval_decision as gateway

ROOT = Path(__file__).resolve().parents[2]
Q4 = ROOT / Path("coordination") / "standards" / "governance" / "immutable_prompt_adjustment_and_decision_v0_1.yaml"
Q5 = ROOT / Path("coordination") / "standards" / "governance" / "common_coordination_event_envelope_v0_1.yaml"
Q6 = ROOT / Path("coordination") / "standards" / "governance" / "operator_attention_semantics_v0_1.yaml"


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be mapping")
    return data


def main() -> int:
    required_api = [
        "GatewayEvaluation",
        "DispatchApprovalValidation",
        "evaluate_gateway",
        "build_operator_decision",
        "write_operator_decision",
        "validate_approval_for_dispatch",
    ]
    missing = [name for name in required_api if not hasattr(gateway, name)]
    if missing:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL missing=" + ",".join(missing))
        return 1

    if gateway.DECISIONS != ("APPROVE", "HOLD", "REJECT"):
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL decision_enum")
        return 1
    if gateway.TRANSPORTS != ("FILESYSTEM", "CLI"):
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL transport_enum")
        return 1

    q4 = _load(Q4)
    if "operator_decision" not in q4["artifact_model"]["canonical_artifact_types"]:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL q4_operator_decision")
        return 1
    if "operator_decision" not in q4["authority_boundary"]["manual_authority_required_artifact_types"]:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL q4_manual_authority")
        return 1

    q5 = _load(Q5)
    if "operator_decision" not in q5["event_type"]["canonical_initial_families"]:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL q5_operator_decision_family")
        return 1
    if q5["family_ownership"]["operator_decision"]["event_replaces_durable_decision_artifact"] is not False:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL q5_artifact_boundary")
        return 1

    q6 = _load(Q6)
    if "operator_acceptance_required" not in q6["attention_reasons"]["canonical_reasons"]:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL q6_attention_reason")
        return 1
    if q6["reason_constraints"]["operator_acceptance_required"]["attention_is_acceptance"] is not False:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL q6_attention_boundary")
        return 1

    source = Path(gateway.__file__).read_text(encoding="utf-8")
    required_tokens = [
        "forprint_operator_approval_decision_v0_1",
        "forprint_operator_approval_input_v0_1",
        "APPROVE",
        "HOLD",
        "REJECT",
        "FILESYSTEM",
        "CLI",
        "APPROVAL_EXPIRED",
        "LAUNCH_REQUEST_FINGERPRINT_DRIFT",
        "direct_worker_dispatch_allowed_by_gateway",
        "blueprint_accept",
        "q4_artifact_type",
        "q5_event_family",
        "q6_attention_reason",
    ]
    absent = [token for token in required_tokens if token not in source]
    if absent:
        print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=FAIL tokens=" + ",".join(absent))
        return 1

    print("OPERATOR_APPROVAL_GATEWAY_CONTRACT=PASS")
    print("Q4_OPERATOR_DECISION_REUSED=true")
    print("Q5_OPERATOR_DECISION_FAMILY_REUSED=true")
    print("Q6_OPERATOR_ACCEPTANCE_ATTENTION_REUSED=true")
    print("FILESYSTEM_CLI_TRANSPORT=true")
    print("TELEGRAM_REQUIRED=false")
    print("WORKER_DISPATCH_PERFORMED=false")
    print("BLUEPRINT_ACCEPT_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
