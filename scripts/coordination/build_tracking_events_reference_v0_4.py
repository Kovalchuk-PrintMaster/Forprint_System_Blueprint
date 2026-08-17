from __future__ import annotations

import argparse
import hashlib
import importlib.util
import sys
from pathlib import Path

import yaml

PROMPT_ID = "logistics_service_tracking_events_v0_1"
MODULE_ID = "logistics_service"
CONTRACT_ID = "logistics_service_tracking_events_v0_1__contract_v0_4_reference_v0_2"
ORIGIN = Path(
    "coordination/outgoing_prompts/logistics_service/approved/"
    "2026-07-29__logistics_service__tracking_events_v0_1.md"
)
LEGACY = Path(
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1.yaml"
)
INSTANCE_DIR = Path(
    "coordination/prompt_contracts/logistics_service/"
    "logistics_service_tracking_events_v0_1"
)
SNAPSHOT = INSTANCE_DIR / "source_prompt_snapshot.md"
CONTRACT = INSTANCE_DIR / f"{CONTRACT_ID}.yaml"
FINDINGS = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-17__blueprint__tracking_events_v0_4_reference_implementation_v0_2.yaml"
)

SOURCE_OBLIGATIONS = [
    ("SRC-001", "Accepted foundation + Required Git workflow",
     "Preserve the accepted Provider Adapter base, use the dedicated Tracking Events feature branch, and report branch/base/worktree/prompt/roadmap state without merging, deleting, or renaming the branch."),
    ("SRC-002", "Ownership boundaries",
     "Keep shipment truth and provider-neutral event semantics in Logistics, Telegram presentation/conversation ownership in Telegram Bot, future canonical persistence outside Logistics, and prohibit cross-repository writes."),
    ("SRC-003", "Main implementation scope 1",
     "Provide one authoritative provider-neutral taxonomy with shipment_created, tracking_updated, arrived, delivered, failed, and needs_attention; define semantics and keep provider names out of canonical event types."),
    ("SRC-004", "Main implementation scope 2",
     "Provide a typed, versioned, deterministically serializable event envelope with the required identity, timing, shipment/tracking, provider-safe, state, correlation, causation, idempotency, source, preview/live, details, summary, and warning fields plus the stated invariants."),
    ("SRC-005", "Main implementation scope 3",
     "Define deterministic provider-neutral lifecycle transitions including creation, repeated updates, arrived-to-delivered, failure, needs-attention, duplicate, out-of-order, terminal-state, and provider-normalization behavior without a production workflow engine."),
    ("SRC-006", "Main implementation scope 4",
     "Provide a channel-neutral notification projection with the required identifiers, event/shipment/tracking/provider/timing/recipient/fact/priority/correlation/idempotency/preview fields and exclude Telegram UI state, credentials, raw sensitive responses, canonical client/order data, and database details."),
    ("SRC-007", "Main implementation scope 5",
     "Define deterministic correlation, causation, event and notification idempotency, logical duplicate detection, replay safety, repeated same-status snapshot handling, out-of-order observation handling, and event-version compatibility."),
    ("SRC-008", "Main implementation scope 6",
     "Provide synthetic fixtures for creation, updates, arrival, delivery, provider failure, manual attention, duplicate and out-of-order updates, Telegram projection, and replay/idempotency using no real customer data or credentials."),
    ("SRC-009", "Main implementation scope 7",
     "Provide a deterministic Make-first read-only preview demonstrating taxonomy, envelope, lifecycle transition, normalized update, notification projection, idempotency, preview_only=true, live_write=false, and provider_call_performed=false with no network/provider/Telegram/cross-repository/database/background-worker mutations."),
    ("SRC-010", "Main implementation scope 8",
     "Document taxonomy, envelope, lifecycle, provider normalization, notification boundary, Telegram ownership, idempotency/replay, preview workflow, recovery, future local persistence, and future central database migration; recovery must describe file-scoped rollback and post-recovery checks."),
    ("SRC-011", "Local persistence boundary",
     "Do not implement SQLite or production persistence; allow only persistence-ready serialization/interfaces and clearly test-only in-memory fixtures, with no migrations, canonical customer/order tables, cross-module DB ownership, hidden SQL domain dependencies, or DB-specific public fields."),
    ("SRC-012", "Telegram coordination boundary",
     "Provide Telegram handoff evidence containing one canonical projection schema, sample payloads for every required event type, field ownership, required/optional fields, version compatibility, idempotency, error/unsupported-version behavior, and explicit no-cross-repository-write confirmation."),
    ("SRC-013", "Telegram coordination boundary / questions",
     "Record Telegram-side agreement questions in coordination/status/next_questions_for_blueprint.md without blocking provider-neutral implementation on wording or UI choices."),
    ("SRC-014", "Required tests",
     "Test all required event types; envelope typing; timezone-aware timestamps; event-version validation; deterministic serialization; valid/invalid/terminal lifecycle behavior; provider normalization; duplicate/out-of-order handling; correlation/causation; deterministic idempotency; notification projection/replay; safe rendering; no credentials; no provider/Telegram/cross-repository calls or writes; preview command; Make contract; and report generation."),
    ("SRC-015", "Required tests / totals",
     "Report exact focused and full-suite collection/pass totals separately from check-report totals."),
    ("SRC-016", "Required commands",
     "Run at minimum make tracking-events-check, governance-check, coordination-check, check, check-report, check-report-full, module-validate, git diff --check, and git status --short, or document the canonical focused-target equivalent."),
    ("SRC-017", "Generated reports and diagnostics",
     "Do not leave generated reports or diagnostics staged/committed unless repository policy explicitly classifies them as tracked evidence."),
    ("SRC-018", "Completion workflow / required outputs",
     "Use module-side completion automation and provide completion packet record, completion report, reports index, current_status.yaml, current_status.md, and next_questions_for_blueprint.md."),
    ("SRC-019", "Completion workflow / required report content",
     "Completion packet/report must carry prompt, branch/base/implementation/completion commits, changed files, authoritative event contract, taxonomy, lifecycle summary, notification path, Telegram examples, idempotency rules, focused/full test totals, check-report totals, warnings/blockers, generated-artifact handling, all safety confirmations, open questions or explicit none, and push/upstream-divergence evidence."),
    ("SRC-020", "Completion workflow / automation",
     "Completion automation must be valid and idempotent, including safe repeated execution and superseding behavior when revising historical completion evidence."),
    ("SRC-021", "Completion workflow / final handoff",
     "Final assistant handoff must be compact and link to detailed evidence instead of reproducing full logs."),
    ("SRC-022", "Explicit non-goals",
     "Do not implement local/central DB integration, live/read-only provider APIs, bookings or TTN creation, Telegram code/API, production queues/schedulers/workers, live shipment mutations, credentials, canonical client/order ownership, pricing/payment/accounting/warehouse/CRM/Website/Calculator/Gateway writes."),
    ("SRC-023", "Definition of done / implementation semantics",
     "Done requires authoritative taxonomy and all six event types, typed envelope, deterministic tested lifecycle, provider normalization, explicit correlation/causation/idempotency, Telegram-ready channel-neutral projections, required synthetic fixtures, read-only Make preview, preview_only=true, live_write=false, no real provider/Telegram calls, no DB implementation, and architecture/runbook/recovery docs."),
    ("SRC-024", "Definition of done / delivery evidence",
     "Done additionally requires valid idempotent completion automation, passing full checks, committed and pushed feature branch, and complete Blueprint review evidence."),
    ("SRC-R01", "Required reading before implementation / Blueprint sources",
     "Read the current required Blueprint governance and coordination sources through the approved Blueprint pull and prompt-navigation workflow before implementation."),
    ("SRC-R02", "Required reading before implementation / accepted Logistics evidence",
     "Review the accepted provider contract, runbook, recovery evidence, and existing authoritative Logistics equivalents; reuse actual authoritative paths and do not create duplicate domain hierarchies."),
]

IMPLEMENTATION_OBLIGATIONS = [
    ("IMP-001", "Preserve accepted implementation base and dedicated feature-branch workflow."),
    ("IMP-002", "Maintain one authoritative six-event provider-neutral taxonomy with documented semantics."),
    ("IMP-003", "Maintain the typed versioned deterministic event envelope and its safety invariants."),
    ("IMP-004", "Maintain deterministic lifecycle and provider-normalization behavior including duplicate/out-of-order/terminal rules."),
    ("IMP-005", "Maintain the channel-neutral Telegram-ready notification projection and ownership exclusions."),
    ("IMP-006", "Maintain correlation, causation, idempotency, replay, duplicate, ordering, and version-compatibility rules."),
    ("IMP-007", "Maintain the complete synthetic fixture set using synthetic-only data."),
    ("IMP-008", "Maintain a Make-first deterministic read-only Tracking Events preview/check workflow."),
    ("IMP-009", "Maintain architecture, boundary, runbook, and recovery documentation with file-scoped rollback guidance."),
    ("IMP-010", "Preserve persistence-ready boundaries without implementing SQLite or central persistence."),
    ("IMP-011", "Maintain the detailed Telegram handoff contract and question-recording boundary."),
    ("IMP-012", "Preserve all explicit safety, ownership, integration, and non-goal boundaries."),
    ("IMP-013", "Resolve and read the required current Blueprint governance sources through the approved coordination workflow before implementation."),
    ("IMP-014", "Review and reuse accepted authoritative Logistics artifacts and paths instead of creating duplicate domain hierarchies."),
]

VERIFICATION_OBLIGATIONS = [
    ("VER-001", "Verify all six canonical event types, provider-neutral taxonomy semantics, and provider normalization."),
    ("VER-002", "Verify typed envelope validation, timezone-aware timestamps, explicit versioning, deterministic serialization, and credential-safe output."),
    ("VER-003", "Verify valid and invalid lifecycle transitions, terminal-state behavior, duplicate updates, and out-of-order updates."),
    ("VER-004", "Verify correlation/causation metadata, deterministic event idempotency, notification idempotency, and replay safety."),
    ("VER-005", "Verify notification projection schema, safe rendering, ownership exclusions, and Telegram-ready examples."),
    ("VER-006", "Verify preview command and Make target are deterministic/read-only with no provider, Telegram, cross-repository, database, or live writes."),
    ("VER-007", "Run and record the complete required command set including focused, governance, coordination, full, report, module validation, diff, and status checks."),
    ("VER-008", "Record exact focused and full-suite collection/pass totals as distinct evidence."),
    ("VER-009", "Record check-report and check-report-full totals separately from pytest totals."),
    ("VER-010", "Verify required documentation and file-scoped recovery guidance."),
    ("VER-011", "Verify module completion automation is valid and idempotent on repeated execution."),
    ("VER-012", "Verify required-reading resolution, accepted-artifact reuse, authoritative-path reuse, and absence of duplicate domain hierarchy creation."),
]

COMPLETION_EVIDENCE_OBLIGATIONS = [
    ("CE-001", "Record branch, base commit, clean/expected worktree, resolved prompt id, and resolved roadmap step."),
    ("CE-002", "Record changed files, authoritative event contract path, taxonomy, lifecycle summary, notification projection path, and idempotency rules."),
    ("CE-003", "Record Telegram handoff schema/examples for every required event type, ownership/requiredness/version/error/idempotency rules, and no-cross-repository-write confirmation."),
    ("CE-004", "Record exact focused and full-suite collected/pass totals separately."),
    ("CE-005", "Record exact check-report and check-report-full totals separately from pytest totals."),
    ("CE-006", "Record warnings/blockers and generated-report/diagnostic handling."),
    ("CE-007", "Record preview_only=true, live_write=false, provider_call_performed=false, Telegram_API_call=false, cross_repository_write=false, and credentials_added=false."),
    ("CE-008", "Record open questions in next_questions_for_blueprint.md or explicit no-open-questions."),
    ("CE-009", "Record implementation/completion commits plus push and upstream-divergence evidence."),
    ("CE-010", "Record all required module-side completion output paths and superseding chain when revising historical evidence."),
    ("CE-011", "Provide a compact final handoff linking detailed evidence rather than duplicating logs."),
    ("CE-012", "Record completion automation validity and idempotent repeated-run evidence."),
    ("CE-013", "Record required-reading resolution and confirmation that existing authoritative Logistics artifacts/paths were reviewed and reused without duplicate hierarchy creation."),
]

LEDGER = {
    "SRC-001": ["IMP-001", "CE-001"],
    "SRC-002": ["IMP-012", "CE-007"],
    "SRC-003": ["IMP-002", "VER-001", "CE-002"],
    "SRC-004": ["IMP-003", "VER-002", "CE-002"],
    "SRC-005": ["IMP-004", "VER-003", "CE-002"],
    "SRC-006": ["IMP-005", "VER-005", "CE-002", "CE-003"],
    "SRC-007": ["IMP-006", "VER-004", "CE-002"],
    "SRC-008": ["IMP-007", "VER-001", "VER-003", "VER-004"],
    "SRC-009": ["IMP-008", "VER-006", "CE-007"],
    "SRC-010": ["IMP-009", "VER-010"],
    "SRC-011": ["IMP-010", "IMP-012", "CE-007"],
    "SRC-012": ["IMP-011", "VER-005", "CE-003"],
    "SRC-013": ["IMP-011", "CE-008"],
    "SRC-014": ["VER-001", "VER-002", "VER-003", "VER-004", "VER-005", "VER-006"],
    "SRC-015": ["VER-008", "VER-009", "CE-004", "CE-005"],
    "SRC-016": ["VER-007", "CE-004", "CE-005"],
    "SRC-017": ["CE-006"],
    "SRC-018": ["CE-010", "CE-012"],
    "SRC-019": ["CE-001", "CE-002", "CE-003", "CE-004", "CE-005", "CE-006", "CE-007", "CE-008", "CE-009", "CE-010"],
    "SRC-020": ["VER-011", "CE-012"],
    "SRC-021": ["CE-011"],
    "SRC-022": ["IMP-012", "VER-006", "CE-007"],
    "SRC-023": ["IMP-002", "IMP-003", "IMP-004", "IMP-005", "IMP-006", "IMP-007", "IMP-008", "IMP-009", "IMP-010", "VER-001", "VER-002", "VER-003", "VER-004", "VER-005", "VER-006", "VER-010"],
    "SRC-024": ["VER-007", "VER-011", "CE-009", "CE-010", "CE-012"],
    "SRC-R01": ["IMP-013", "VER-012", "CE-013"],
    "SRC-R02": ["IMP-014", "VER-012", "CE-013"],
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validator_module(root: Path):
    path = root / "scripts/coordination/validate_prompt_contract_v0_4.py"
    spec = importlib.util.spec_from_file_location("validate_prompt_contract_v0_4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_immutable(path: Path, content: bytes) -> None:
    if path.exists():
        current = path.read_bytes()
        if current != content:
            raise RuntimeError(f"immutable artifact differs and will not be overwritten: {path}")
        print(f"UNCHANGED: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    print(f"CREATED: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    origin = root / ORIGIN
    legacy = root / LEGACY
    snapshot = root / SNAPSHOT
    contract_path = root / CONTRACT
    findings_path = root / FINDINGS

    for path in (origin, legacy):
        if not path.is_file():
            raise RuntimeError(f"missing canonical source: {path}")

    origin_bytes = origin.read_bytes()
    origin_sha = sha256_bytes(origin_bytes)
    legacy_data = yaml.safe_load(legacy.read_text(encoding="utf-8"))
    legacy_sha = sha256_bytes(legacy.read_bytes())

    expected_from_legacy = legacy_data["source_prompt"]["sha256"]
    if origin_sha != expected_from_legacy:
        raise RuntimeError(
            "source prompt drift: current origin hash differs from v0.3 captured hash"
        )

    write_immutable(snapshot, origin_bytes)

    contract = {
        "schema_version": "module_prompt_contract_v0_4",
        "metadata": {
            "contract_id": CONTRACT_ID,
            "module_id": MODULE_ID,
            "prompt_id": PROMPT_ID,
            "created_at": "2026-08-17",
            "status": "candidate_reference_only",
            "immutable": True,
        },
        "source_prompt": {
            "path": str(SNAPSHOT),
            "sha256": origin_sha,
            "origin_path_at_capture": str(ORIGIN),
            "origin_sha256_at_capture": origin_sha,
        },
        "integrity": {
            "algorithm": "sha256",
            "payload_sha256": "",
            "payload_hash_scope": (
                "canonical JSON of entire document excluding integrity.payload_sha256"
            ),
        },
        "source_obligations": [
            {
                "obligation_id": oid,
                "source_locator": locator,
                "required": True,
                "summary": summary,
            }
            for oid, locator, summary in SOURCE_OBLIGATIONS
        ],
        "implementation_obligations": [
            {"obligation_id": oid, "summary": summary}
            for oid, summary in IMPLEMENTATION_OBLIGATIONS
        ],
        "verification_obligations": [
            {"obligation_id": oid, "summary": summary}
            for oid, summary in VERIFICATION_OBLIGATIONS
        ],
        "completion_evidence_obligations": [
            {"obligation_id": oid, "summary": summary}
            for oid, summary in COMPLETION_EVIDENCE_OBLIGATIONS
        ],
        "source_obligation_fidelity_ledger": [
            {
                "source_obligation_id": source_id,
                "target_obligation_ids": targets,
            }
            for source_id, targets in LEDGER.items()
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

    validator = validator_module(root)
    contract["integrity"]["payload_sha256"] = validator.canonical_payload_sha256(
        contract
    )
    contract_yaml = yaml.safe_dump(
        contract,
        sort_keys=False,
        allow_unicode=True,
        width=110,
    ).encode("utf-8")
    write_immutable(contract_path, contract_yaml)

    report = validator.validate_contract(root, contract_path)
    if report["result"] != "PASSED":
        print(yaml.safe_dump(report, sort_keys=False))
        raise RuntimeError("v0.4 Tracking Events contract validation failed")

    findings = {
        "schema_version": "blueprint_tracking_events_v0_4_reference_implementation_v0_1",
        "metadata": {
            "owner": "forprint_system_blueprint",
            "step_id": "blueprint_v0_4_tracking_events_reference_v0_1",
            "subject": PROMPT_ID,
            "created_at": "2026-08-17",
            "state": "READY_FOR_HUMAN_SEMANTIC_FIDELITY_REVIEW",
        },
        "source": {
            "origin_prompt": str(ORIGIN),
            "origin_prompt_sha256": origin_sha,
            "legacy_v0_3_contract": str(LEGACY),
            "legacy_v0_3_contract_sha256": legacy_sha,
        },
        "v0_4_reference": {
            "contract": str(CONTRACT),
            "contract_payload_sha256": contract["integrity"]["payload_sha256"],
            "source_snapshot": str(SNAPSHOT),
            "source_obligation_count": len(SOURCE_OBLIGATIONS),
            "implementation_obligation_count": len(IMPLEMENTATION_OBLIGATIONS),
            "verification_obligation_count": len(VERIFICATION_OBLIGATIONS),
            "completion_evidence_obligation_count": len(COMPLETION_EVIDENCE_OBLIGATIONS),
            "validator_result": report["result"],
            "semantic_fidelity_review_state": "pending_operator_review",
            "candidate_reference_only": True,
        },
        "v0_3_fidelity_gaps_now_explicit": [
            "detailed_required_test_catalog",
            "exact_focused_and_full_collection_pass_totals",
            "separate_check_report_totals",
            "full_completion_packet_and_report_content",
            "detailed_telegram_handoff_evidence",
            "generated_artifact_handling",
            "push_and_upstream_divergence_evidence",
            "completion_automation_idempotency",
        ],
        "boundaries": {
            "module_repository_writes": False,
            "completion_packet_v0_4_fabricated_by_blueprint": False,
            "completion_outbox_v0_4_fabricated_by_blueprint": False,
            "operator_accept_return_hold_created": False,
            "dark_zone_audit_run": False,
            "global_v0_4_promotion_performed": False,
            "automatic_commit": False,
            "automatic_push": False,
            "rollout_or_production_write": False,
        },
    }
    findings_bytes = yaml.safe_dump(
        findings, sort_keys=False, allow_unicode=True, width=110
    ).encode("utf-8")
    if findings_path.exists():
        current = findings_path.read_bytes()
        if current != findings_bytes:
            raise RuntimeError(
                f"existing Blueprint findings differ; refusing overwrite: {findings_path}"
            )
        print(f"UNCHANGED: {findings_path}")
    else:
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_path.write_bytes(findings_bytes)
        print(f"CREATED: {findings_path}")

    print(f"SOURCE_PROMPT_SHA256={origin_sha}")
    print(f"LEGACY_V0_3_CONTRACT_SHA256={legacy_sha}")
    print(f"V0_4_PAYLOAD_SHA256={contract['integrity']['payload_sha256']}")
    print(f"SOURCE_OBLIGATION_COUNT={len(SOURCE_OBLIGATIONS)}")
    print(f"VALIDATOR_RESULT={report['result']}")
    print("module_repository_writes: false")
    print("completion_packet_v0_4_fabricated_by_blueprint: false")
    print("completion_outbox_v0_4_fabricated_by_blueprint: false")
    print("operator_decision_created: false")
    print("dark_zone_audit_run: false")
    print("global_v0_4_promotion_performed: false")
    print("RESULT: TRACKING_EVENTS_V0_4_REFERENCE_CONTRACT_BUILT")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
