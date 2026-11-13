#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "module_current_state_evidence_standard_v0_1.yaml"
)
PORTFOLIO = (
    ROOT
    / "coordination/internal_work/blueprint/module_inventory/"
    "module_current_state_evidence_portfolio_v0_1.yaml"
)

REQUIRED_SECTIONS = {
    "role",
    "current_capabilities",
    "owned_data",
    "contracts",
    "interfaces",
    "implemented_components",
    "test_and_acceptance_evidence",
    "blockers",
    "dependencies",
    "target_state",
    "roadmap_position",
    "conflicts_and_stale_material",
    "last_verified",
    "canonical_paths",
}

ALLOWED_PROFILE_STATES = {
    "BLUEPRINT_LOCAL_REPOSITORY_VERIFIED",
    "BLUEPRINT_DOCUMENTED_REPO_EVIDENCE_PENDING",
    "REPO_EVIDENCE_REVIEW_IN_PROGRESS",
    "CURRENT_STATE_PROFILE_VERIFIED",
    "BLOCKED",
}


def fail(message: str) -> None:
    print("MODULE_CURRENT_STATE_EVIDENCE_VALIDATION=FAIL")
    print("ERROR=" + message)
    raise SystemExit(1)


def main() -> None:
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    portfolio = yaml.safe_load(PORTFOLIO.read_text(encoding="utf-8"))

    if policy.get("status") != "ACTIVE":
        fail("POLICY_NOT_ACTIVE")
    if policy.get("authority") != "BLUEPRINT_PORTFOLIO_DOCUMENTATION_GOVERNANCE":
        fail("POLICY_AUTHORITY")

    sections = set(policy.get("required_profile_sections", []))
    if sections != REQUIRED_SECTIONS:
        fail(
            "REQUIRED_SECTION_SET_DRIFT:"
            f"actual={sorted(sections)}:"
            f"expected={sorted(REQUIRED_SECTIONS)}"
        )

    rules = policy.get("portfolio_rules", {})
    if rules.get("canonical_module_count") != 23:
        fail("POLICY_CANONICAL_MODULE_COUNT")
    if rules.get("other_module_repository_verification_started_now") is not False:
        fail("CROSS_MODULE_REPO_VERIFICATION_PREMATURE")
    if rules.get("cross_repo_diagnostics_started_now") is not False:
        fail("CROSS_REPO_DIAGNOSTICS_PREMATURE")
    if rules.get("assistant_distribution_allowed_now") is not False:
        fail("ASSISTANT_DISTRIBUTION_GATE_OPEN")
    if rules.get("module_implementation_allowed_now") is not False:
        fail("MODULE_IMPLEMENTATION_GATE_OPEN")

    if portfolio.get("assistant_distribution_allowed") is not False:
        fail("PORTFOLIO_DISTRIBUTION_GATE_OPEN")
    if portfolio.get("module_implementation_allowed") is not False:
        fail("PORTFOLIO_IMPLEMENTATION_GATE_OPEN")
    if portfolio.get("cross_repo_diagnostics_started") is not False:
        fail("PORTFOLIO_CROSS_REPO_DIAGNOSTICS_STARTED")

    modules = portfolio.get("modules", [])
    if not isinstance(modules, list) or len(modules) != 23:
        fail(f"CANONICAL_MODULE_COUNT:{len(modules) if isinstance(modules, list) else -1}")

    module_ids = [item.get("module_id") for item in modules]
    if len(set(module_ids)) != 23:
        fail("DUPLICATE_MODULE_ID")
    if "forprint_system_blueprint" not in module_ids:
        fail("BLUEPRINT_MODULE_MISSING")

    blueprint_verified = 0
    pending = 0
    for item in modules:
        state = item.get("profile_status")
        if state not in ALLOWED_PROFILE_STATES:
            fail("UNKNOWN_PROFILE_STATE:" + str(state))
        if item.get("required_section_count") != 14:
            fail("REQUIRED_SECTION_COUNT:" + str(item.get("module_id")))
        if item.get("assistant_distribution_allowed") is not False:
            fail("MODULE_DISTRIBUTION_GATE:" + str(item.get("module_id")))
        if item.get("module_implementation_allowed") is not False:
            fail("MODULE_IMPLEMENTATION_GATE:" + str(item.get("module_id")))

        if item["module_id"] == "forprint_system_blueprint":
            if state != "BLUEPRINT_LOCAL_REPOSITORY_VERIFIED":
                fail("BLUEPRINT_NOT_LOCAL_VERIFIED")
            if item.get("repository_evidence_verified") is not True:
                fail("BLUEPRINT_REPO_EVIDENCE_NOT_TRUE")
            blueprint_verified += 1
        else:
            if state != "BLUEPRINT_DOCUMENTED_REPO_EVIDENCE_PENDING":
                fail(
                    "NON_BLUEPRINT_PREMATURE_PROFILE_STATE:"
                    + item["module_id"]
                    + ":"
                    + str(state)
                )
            if item.get("repository_evidence_verified") is not False:
                fail("NON_BLUEPRINT_REPO_EVIDENCE_PREMATURE:" + item["module_id"])
            pending += 1

    digest = hashlib.sha256(
        "\n".join(sorted(module_ids)).encode("utf-8")
    ).hexdigest()
    if portfolio.get("canonical_module_set_sha256") != digest:
        fail("CANONICAL_MODULE_SET_HASH_DRIFT")

    summary = portfolio.get("summary", {})
    if summary.get("canonical_module_count") != 23:
        fail("SUMMARY_CANONICAL_MODULE_COUNT")
    if summary.get("blueprint_local_repository_verified_count") != blueprint_verified:
        fail("SUMMARY_BLUEPRINT_VERIFIED_COUNT")
    if summary.get("repo_evidence_pending_count") != pending:
        fail("SUMMARY_REPO_PENDING_COUNT")

    print("MODULE_CURRENT_STATE_EVIDENCE_VALIDATION=PASS")
    print("REQUIRED_PROFILE_SECTION_COUNT=14")
    print("CANONICAL_MODULE_COUNT=23")
    print(f"BLUEPRINT_LOCAL_REPOSITORY_VERIFIED_COUNT={blueprint_verified}")
    print(f"REPO_EVIDENCE_PENDING_COUNT={pending}")
    print("CURRENT_TARGET_PROPOSED_SEPARATION=REQUIRED")
    print("UNVERIFIED_IMPLEMENTATION_CLAIMS_ALLOWED=false")
    print("CROSS_REPO_DIAGNOSTICS_STARTED=false")
    print("ASSISTANT_DISTRIBUTION_ALLOWED=false")
    print("MODULE_IMPLEMENTATION_ALLOWED=false")


if __name__ == "__main__":
    main()
