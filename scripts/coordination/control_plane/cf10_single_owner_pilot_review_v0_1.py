"""CF10 r044: read-only single-owner pilot design review. NEVER launch or grant authority."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Mapping

import yaml

SCHEMA = "cf10_single_owner_pilot_design_v0_1"
POLICY = "coordination/standards/governance/cf10_single_owner_pilot_design_v0_1.yaml"
LEGACY = "scripts/coordination/control_plane/cf10_s01_release_gate_candidate_v0_1.py"
SOURCES = {
    "Makefile": (
        "cf10-s01-runtime-launch-preflight:",
        "QUARANTINED_NEEDS_INDEPENDENT_REBIND",
        "governed-worker-cycle-advance: cf10-s01-runtime-launch-preflight",
    ),
    "scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py": (
        "def launch_once(", "_owner_claim(", "assert_cutover_ready()",
    ),
    "scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py": (
        "def assert_cutover_ready()", "LIVE_CUTOVER_ENABLED is not True",
    ),
    "scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py": (
        "LIVE_CUTOVER_ENABLED=False",
    ),
    "scripts/coordination/control_plane/cf10_r037_finalizer_boundary_v0_1.py": (
        "def review(", "cf10_r036_independent_result_crosscheck_v0_1",
    ),
    LEGACY: ("INDEPENDENT_PROOF_DIGEST_SET_INCOMPLETE", "INDEPENDENT_REVIEWER_NOT_DISTINCT_OR_UNTRUSTED"),
}
PROOFS = frozenset({
    "source_frozen_and_remote_head_verified", "exact_work_front_and_write_set",
    "existing_enforced_writer_lock_and_single_active_writer",
    "root_owned_one_use_claim_before_spawn", "sealed_systemd_no_popen_fallback",
    "durable_pre_and_post_terminal_receipts", "independent_systemd_kernel_result_readback",
    "strict_worker_result_and_delta_verification", "immutable_terminal_ledger_and_no_retry_on_unknown",
    "tmp_deletion_does_not_change_execution_truth", "operator_review_before_acceptance_or_promotion",
})
MILESTONES = (
    "SOURCE_GOVERNANCE_RECONCILIATION_AND_NON_AUTHORIZING_CONTRACT",
    "SEPARATE_BOUNDED_PILOT_ADMISSION_WITH_NEGATIVE_TESTS",
    "LIVE_SYSTEMD_AND_TMP_UNAVAILABLE_PROOF",
    "EXPLICIT_SINGLE_ATTEMPT_CUTOVER_APPROVAL",
    "NEW_TASK70_END_TO_END_OPERATOR_REVIEW",
)


def validate_contract(doc: Mapping) -> list[str]:
    """Pure policy validation: no runtime read, no authority and no mutation."""
    bad: list[str] = []
    if not isinstance(doc, dict):
        return ["POLICY_NOT_MAPPING"]
    required = {
        "schema_version": SCHEMA,
        "owner": "forprint_system_blueprint",
        "status": "OWNER_SELECTED_DESIGN_NON_AUTHORIZING",
        "decision": "SELECT_SINGLE_OWNER_BOUNDED_PILOT",
    }
    for key, value in required.items():
        if doc.get(key) != value:
            bad.append("INVALID_" + key.upper())
    scope = doc.get("scope")
    if not isinstance(scope, dict) or any(type(scope.get(k)) is not type(v) or scope.get(k) != v for k, v in {
        "module": "forprint_system_blueprint", "worker_id": "worker-01",
        "first_live_task_family": "Task70", "attempt": "NEW_UNCONSUMED_ONLY",
        "simultaneous_writable_workers_max": 1, "broader_modules_allowed": False,
        "automatic_next_task": False,
    }.items()):
        bad.append("UNBOUNDED_SCOPE")
    auth = doc.get("operator_authentication")
    if not isinstance(auth, dict) or any(auth.get(k) is not v if isinstance(v, bool) else auth.get(k) != v
            for k, v in {
                "method": "EXISTING_INTERACTIVE_SUDO_PAM", "confirmation": "EXACT_TASK_AND_ATTEMPT_BEFORE_CLAIM",
                "reusable_signing_lease_required": False, "operator_password_stored": False,
                "owner_decision_substitutes_independent_human_signer_for_bounded_pilot_only": True,
            }.items()):
        bad.append("OWNER_AUTH_CONTRACT_INVALID")
    protections = doc.get("independent_technical_protections")
    if not isinstance(protections, list) or len(protections) != len(PROOFS) or set(protections) != PROOFS:
        bad.append("TECHNICAL_PROOFS_INCOMPLETE")
    old = doc.get("historical_conflict")
    if not isinstance(old, dict) or any(old.get(k) != v for k, v in {
        "existing_policy": "EIGHT_INDEPENDENT_PROOFS_AND_DISTINCT_SIGNER",
        "selected_alternative": "NO_SECOND_HUMAN_SIGNER_FOR_ONE_OWNER_PILOT",
        "reconciliation_required": True,
        "legacy_live_release_must_remain_unchanged_until_separate_cutover": True,
    }.items()):
        bad.append("HISTORICAL_AUTHORITY_CONFLICT_NOT_RETAINED")
    cut = doc.get("live_cutover")
    if not isinstance(cut, dict) or any(cut.get(k) is not v for k, v in {
        "granted_by_this_design": False, "make_quarantine_must_remain": True,
        "systemd_live_cutover_must_remain_disabled": True,
        "separate_runtime_authorization_implementation_required": True,
        "distinct_pilot_release_review_required": True,
        "no_automatic_worker_retry": True, "no_automatic_acceptance": True,
        "no_automatic_publication": True,
    }.items()):
        bad.append("UNAUTHORIZED_CUTOVER_WIDENING")
    if tuple(doc.get("next_engineering_milestones", [])) != MILESTONES:
        bad.append("NEXT_STEP_CONTRACT_INVALID")
    return sorted(set(bad))


def inspect(root: Path, *, source_text: Mapping[str, str] | None = None,
            doc: Mapping | None = None) -> dict:
    """Never infer release authority from a PASS design review."""
    blockers = []
    if doc is None:
        file = root / POLICY
        if file.is_symlink() or not file.is_file():
            return {"status": "BLOCKED_POLICY_UNAVAILABLE", "authority_granted": False,
                    "production_cutover": False, "blockers": ["POLICY_UNAVAILABLE"]}
        doc = yaml.safe_load(file.read_text(encoding="utf-8"))
    blockers.extend(validate_contract(doc))
    source_checks: dict[str, str] = {}
    for rel, tokens in SOURCES.items():
        if source_text is None:
            file = root / rel
            if file.is_symlink() or not file.is_file():
                blockers.append("SOURCE_MISSING_OR_SYMLINK:" + rel)
                source_checks[rel] = "MISSING"
                continue
            source = file.read_text(encoding="utf-8")
        else:
            source = source_text.get(rel, "")
        if any(token not in source for token in tokens):
            blockers.append("CANONICAL_SOURCE_BOUNDARY_CHANGED:" + rel)
            source_checks[rel] = "MISMATCH"
        else:
            source_checks[rel] = "SOURCE_FENCE_PRESENT_NON_AUTHORIZING"
    if blockers:
        state = "BLOCKED_SOURCE_OR_POLICY_RECONCILIATION"
        next_step = "RECONCILE_SOURCE_OR_POLICY_BEFORE_PILOT_ADMISSION"
    else:
        state = "OWNER_SELECTED_DESIGN_RELEASE_BLOCKED"
        next_step = "IMPLEMENT_SEPARATE_BOUNDED_PILOT_ADMISSION_AND_NEGATIVE_TESTS"
    return {
        "schema_version": "cf10_r044_single_owner_pilot_review_v0_1",
        "status": state,
        "authority_granted": False,
        "production_cutover": False,
        "worker_launched": False,
        "operator_claim_consumed": False,
        "independent_release_legacy": "PRESERVED_NOT_REINTERPRETED",
        "operator_profile": "SINGLE_OWNER_BOUNDED_PILOT_DESIGN_SELECTED",
        "source_checks": source_checks,
        "blockers": sorted(set(blockers)),
        "next_action": next_step,
        "remaining_release_boundaries": list(MILESTONES[1:]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("inspect", "validate"), default="inspect")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--format", choices=("json", "yaml"), default="json")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        report = inspect(root)
        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True))
        return 2 if report["blockers"] else 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print("CF10_R044_BLOCKED=" + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
