#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REGISTRY = Path(
    "coordination/standards/adoption/"
    "blueprint_command_applicability_v0_1.yaml"
)
SELF_AUDIT_EVIDENCE = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-02__blueprint__self_audit_completion_v0_1.yaml"
)
SELF_AUDIT_SCHEMA = (
    "blueprint_self_audit_completion_evidence_v0_1"
)
CANONICAL_GATE_EVIDENCE = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-02__blueprint__command_applicability_"
    "canonical_gate_integration_v0_1.yaml"
)
CANONICAL_GATE_SCHEMA = (
    "blueprint_command_applicability_"
    "canonical_gate_integration_evidence_v0_1"
)
PROMPT_WORKFLOW_EVIDENCE = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-02__blueprint__prompt_workflow_"
    "operator_integration_v0_1.yaml"
)
PROMPT_WORKFLOW_SCHEMA = (
    "blueprint_prompt_workflow_operator_"
    "integration_evidence_v0_1"
)
MODULE_MAKE_TEMPLATE = Path(
    "coordination/templates/"
    "module_makefile_standard.template.mk"
)
SCHEMA = "blueprint_command_applicability_v0_1"

EXPECTED_TARGETS = {
    "prompt-prepare": True,
    "prompt-release": True,
    "prompt-status": True,
    "completion-intake-preview": True,
    "completion-intake-check": True,
    "completion-accept": True,
    "completion-return": True,
    "module-workflow-check": True,
    "standards-check": True,
    "check-report": True,
    "coordination-check": True,
    "blueprint-self-audit": True,
    "blueprint-self-status": True,
    "blueprint-self-report-full": True,
    "modules-self-status": True,
}

EXPECTED_BLOCKERS: set[str] = set()


def validate_self_audit_evidence(
    path: Path,
) -> list[str]:
    issues: list[str] = []
    try:
        data = yaml.safe_load(
            path.read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except yaml.YAMLError as error:
        return [f"{path}: invalid YAML: {error}"]

    if not isinstance(data, dict):
        return [f"{path}: YAML root must be a mapping"]
    if data.get("schema_version") != SELF_AUDIT_SCHEMA:
        issues.append(
            f"{path}: unsupported self-audit schema_version"
        )

    subject = data.get("subject")
    if not isinstance(subject, dict):
        issues.append(f"{path}: subject must be a mapping")
    else:
        expected = {
            "workflow_id": "blueprint_self_audit",
            "run_id": "bsa-20260802T142628Z",
            "request_id": "bsa-20260802T142628Z",
            "source_commit": "2f89443be1a5b9893d666eed7baa696c17c0b904",
            "runtime_stage": "completed",
            "workflow_result": "READY",
            "governance_interpretation": "READY_WITH_UNKNOWNS",
            "operational_readiness": "blocked",
        }
        for key, value in expected.items():
            if subject.get(key) != value:
                issues.append(
                    f"{path}: subject.{key} must be {value!r}"
                )

    integrity = data.get("integrity")
    if not isinstance(integrity, dict):
        issues.append(f"{path}: integrity must be a mapping")
    else:
        expected = {
            "uploaded_archive_sha256": (
                "f50bceaca42d4c09b9fcb4592f48c181"
                "a130f7393abe6dde54c940118ecebb98"
            ),
            "source_content_checksum": (
                "34b9ae5970f5efa41d25fe4d11148b08"
                "cbb74a0a4944316d328624cc4a9f192b"
            ),
            "external_response_status": "provided",
            "external_analysis_confidence": "medium",
            "bundle_manifest_files_verified": 11,
            "bundle_manifest_integrity": "passed",
        }
        for key, value in expected.items():
            if integrity.get(key) != value:
                issues.append(
                    f"{path}: integrity.{key} must be {value!r}"
                )

    blockers = data.get("readiness_blockers")
    expected_blockers = {
        "prompt_prepare_not_implemented",
        "prompt_release_not_implemented",
        "command_applicability_validator_not_in_canonical_gate",
        "metadata_consistency_not_verified",
        "module_identity_not_reconciled",
        "artifact_authority_and_retention_not_enforced",
        "write_flow_recovery_not_fully_verified",
    }
    if (
        not isinstance(blockers, list)
        or set(blockers) != expected_blockers
    ):
        issues.append(
            f"{path}: readiness_blockers do not match audit"
        )

    boundaries = data.get("boundaries")
    if not isinstance(boundaries, dict):
        issues.append(f"{path}: boundaries must be a mapping")
    else:
        for key in (
            "reference_pilot_migration_authorized",
            "external_module_prompts_released",
            "external_rollout_released",
            "cross_repository_writes",
        ):
            if boundaries.get(key) is not False:
                issues.append(
                    f"{path}: boundaries.{key} must be false"
                )

    if data.get("result") != (
        "BLUEPRINT_SELF_AUDIT_COMPLETED_WITH_UNKNOWNS"
    ):
        issues.append(
            f"{path}: result must preserve completed unknowns"
        )

    return issues

def validate_canonical_gate_evidence(
    path: Path,
) -> list[str]:
    issues: list[str] = []
    try:
        data = yaml.safe_load(
            path.read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except yaml.YAMLError as error:
        return [f"{path}: invalid YAML: {error}"]

    if not isinstance(data, dict):
        return [f"{path}: YAML root must be a mapping"]
    if data.get("schema_version") != CANONICAL_GATE_SCHEMA:
        issues.append(
            f"{path}: unsupported canonical gate schema_version"
        )

    subject = data.get("subject")
    expected_subject = {
        "base_commit": (
            "7ed4f3dfce584cfae62fcf8990a8e9eb554c15b0"
        ),
        "catalog": "scripts/run_blueprint_checks.py",
        "check_id": (
            "blueprint_command_applicability_validation"
        ),
        "check_title": "Blueprint command applicability",
        "check_group": "documentation",
        "validator": (
            "scripts/validation/"
            "validate_blueprint_command_applicability.py"
        ),
        "catalog_state": "integrated",
        "expected_check_total": 27,
    }
    if not isinstance(subject, dict):
        issues.append(f"{path}: subject must be a mapping")
    else:
        for key, value in expected_subject.items():
            if subject.get(key) != value:
                issues.append(
                    f"{path}: subject.{key} must be {value!r}"
                )

    governance = data.get("governance")
    if not isinstance(governance, dict):
        issues.append(f"{path}: governance must be a mapping")
    else:
        expected_governance = {
            "blocker_closed": (
                "command_applicability_validator_"
                "not_in_canonical_gate"
            ),
            "operational_readiness": "blocked",
            "reference_pilot_migration": "not_authorized",
            "external_rollout": "gated",
            "makefile_modified": False,
            "canonical_module_template_modified": False,
            "historical_self_audit_evidence_modified": False,
        }
        for key, value in expected_governance.items():
            if governance.get(key) != value:
                issues.append(
                    f"{path}: governance.{key} must be {value!r}"
                )

    if data.get("result") != (
        "BLUEPRINT_COMMAND_APPLICABILITY_"
        "CANONICAL_GATE_INTEGRATED"
    ):
        issues.append(
            f"{path}: result must confirm canonical integration"
        )

    return issues


def validate_prompt_workflow_evidence(
    path: Path,
) -> list[str]:
    issues: list[str] = []
    try:
        data = yaml.safe_load(
            path.read_text(encoding="utf-8")
        )
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except yaml.YAMLError as error:
        return [f"{path}: invalid YAML: {error}"]

    if not isinstance(data, dict):
        return [f"{path}: YAML root must be a mapping"]
    if data.get("schema_version") != PROMPT_WORKFLOW_SCHEMA:
        issues.append(
            f"{path}: unsupported prompt workflow schema_version"
        )

    subject = data.get("subject")
    expected_subject = {
        "base_commit": (
            "51cc478add62cdadf853e95eef2f4874767b33ec"
        ),
        "blueprint_makefile": "Makefile",
        "module_make_template": (
            "coordination/templates/"
            "module_makefile_standard.template.mk"
        ),
        "implementation": (
            "scripts/coordination/"
            "manage_outgoing_prompt.py"
        ),
        "release_policy": (
            "coordination/standards/governance/"
            "outgoing_prompt_release_policy_v0_1.yaml"
        ),
        "prompt_prepare_target": "implemented",
        "prompt_release_target": "implemented_gated",
    }
    if not isinstance(subject, dict):
        issues.append(f"{path}: subject must be a mapping")
    else:
        for key, value in expected_subject.items():
            if subject.get(key) != value:
                issues.append(
                    f"{path}: subject.{key} must be {value!r}"
                )

    integrity = data.get("integrity")
    expected_integrity = {
        "blueprint_makefile_sha256": (
            "020977f3e26da599f23142a68fbeb7a2"
            "b659f68272469b51396d9e6ac9c8cc3f"
        ),
        "module_make_template_sha256": (
            "c68de5660c5c980f5b5119455174c7aa"
            "1913ffbe351784ea66412aea81e8a589"
        ),
    }
    if not isinstance(integrity, dict):
        issues.append(f"{path}: integrity must be a mapping")
    else:
        for key, value in expected_integrity.items():
            if integrity.get(key) != value:
                issues.append(
                    f"{path}: integrity.{key} must be {value!r}"
                )

    boundaries = data.get("boundaries")
    expected_boundaries = {
        "release_policy_state": "gated",
        "external_module_prompts_released": False,
        "reference_pilot_migration_authorized": False,
        "external_rollout": "gated",
        "cross_repository_writes": False,
        "automatic_commit_push_or_merge": False,
    }
    if not isinstance(boundaries, dict):
        issues.append(f"{path}: boundaries must be a mapping")
    else:
        for key, value in expected_boundaries.items():
            if boundaries.get(key) != value:
                issues.append(
                    f"{path}: boundaries.{key} must be {value!r}"
                )

    if data.get("result") != (
        "BLUEPRINT_PROMPT_WORKFLOW_OPERATOR_"
        "INTEGRATION_COMPLETED_GATED"
    ):
        issues.append(
            f"{path}: result must confirm gated integration"
        )

    return issues


def validate_prompt_workflow_contracts(
    root: Path,
    commands: dict[str, dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    registry_path = root / REGISTRY
    implementation = (
        "scripts/coordination/manage_outgoing_prompt.py"
    )

    prepare = commands.get("prompt-prepare", {})
    expected_prepare = {
        "implementation": implementation,
        "implementation_state": "implemented",
        "default_mode": "preview",
        "apply_requires_explicit": True,
        "replacement_requires_explicit": True,
        "external_repository_writes": False,
        "git_behavior": "none",
        "conformance": "pass",
    }
    for key, value in expected_prepare.items():
        if prepare.get(key) != value:
            issues.append(
                f"{registry_path}: prompt-prepare.{key} "
                f"must be {value!r}"
            )

    release = commands.get("prompt-release", {})
    expected_release = {
        "implementation": implementation,
        "implementation_state": "implemented",
        "default_mode": "preview",
        "apply_requires_explicit": True,
        "module_argument_requires_explicit_command_line_value": True,
        "release_policy": (
            "coordination/standards/governance/"
            "outgoing_prompt_release_policy_v0_1.yaml"
        ),
        "release_policy_state": "gated",
        "external_repository_writes": False,
        "git_behavior": "none",
        "conformance": "pass",
    }
    for key, value in expected_release.items():
        if release.get(key) != value:
            issues.append(
                f"{registry_path}: prompt-release.{key} "
                f"must be {value!r}"
            )

    template_path = root / MODULE_MAKE_TEMPLATE
    try:
        template_text = template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.append(f"{template_path}: file does not exist")
        return issues

    template_targets = set(
        re.findall(
            r"^([A-Za-z0-9_.-]+):(?:\s|$)",
            template_text,
            flags=re.MULTILINE,
        )
    )
    for forbidden in ("prompt-prepare", "prompt-release"):
        if forbidden in template_targets:
            issues.append(
                f"{template_path}: Blueprint-only target "
                f"{forbidden!r} must not exist in module template"
            )

    required_template_text = (
        "Blueprint-owned prompt mutations (intentionally unavailable here):",
        "Approved files are inventory only; readiness comes from Prompt Queue v0.2.",
        "`module_execution.status` is `ready_for_module_pull`",
    )
    for required in required_template_text:
        if required not in template_text:
            issues.append(
                f"{template_path}: missing prompt ownership contract: "
                f"{required!r}"
            )

    return issues


def validate(root: Path) -> list[str]:
    issues: list[str] = []
    path = root / REGISTRY

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{path}: file does not exist"]
    except yaml.YAMLError as error:
        return [f"{path}: invalid YAML: {error}"]

    if not isinstance(data, dict):
        return [f"{path}: YAML root must be a mapping"]
    if data.get("schema_version") != SCHEMA:
        issues.append(f"{path}: unsupported schema_version")

    profile = data.get("repository_profile")
    expected_profile = {
        "repository_id": "forprint_system_blueprint",
        "repository_class": "blueprint",
        "control_role": "blueprint_internal_control",
        "operational_readiness": "blocked",
        "self_audit_state": "completed_with_unknowns",
        "self_audit_evidence": "coordination/internal_work/blueprint/governance/2026-08-02__blueprint__self_audit_completion_v0_1.yaml",
        "canonical_gate_state": "integrated",
        "canonical_gate_evidence": "coordination/internal_work/blueprint/governance/2026-08-02__blueprint__command_applicability_canonical_gate_integration_v0_1.yaml",
        "prompt_workflow_state": "implemented_gated",
        "prompt_workflow_evidence": "coordination/internal_work/blueprint/governance/2026-08-02__blueprint__prompt_workflow_operator_integration_v0_1.yaml",
        "external_rollout": "gated",
    }
    if not isinstance(profile, dict):
        issues.append(f"{path}: repository_profile must be a mapping")
    else:
        for key, value in expected_profile.items():
            if profile.get(key) != value:
                issues.append(
                    f"{path}: repository_profile.{key} "
                    f"must be {value!r}"
                )

    issues.extend(
        validate_self_audit_evidence(
            root / SELF_AUDIT_EVIDENCE
        )
    )
    issues.extend(
        validate_canonical_gate_evidence(
            root / CANONICAL_GATE_EVIDENCE
        )
    )
    issues.extend(
        validate_prompt_workflow_evidence(
            root / PROMPT_WORKFLOW_EVIDENCE
        )
    )

    rows = data.get("commands")
    if not isinstance(rows, list):
        return [*issues, f"{path}: commands must be a list"]

    commands: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            issues.append(f"{path}: command row must be a mapping")
            continue
        command_id = row.get("command_id")
        if not isinstance(command_id, str):
            issues.append(f"{path}: command_id must be a string")
            continue
        if command_id in commands:
            issues.append(f"{path}: duplicate command_id {command_id!r}")
        commands[command_id] = row

    if set(commands) != set(EXPECTED_TARGETS):
        issues.append(f"{path}: command set is incomplete")

    target_set = set(
        re.findall(
            r"^([A-Za-z0-9_.-]+):(?:\s|$)",
            (root / "Makefile").read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )

    for command_id, expected_present in EXPECTED_TARGETS.items():
        row = commands.get(command_id, {})
        target = row.get("public_target")
        if target != command_id:
            issues.append(
                f"{path}: {command_id}.public_target "
                f"must be {command_id!r}"
            )
            continue
        if row.get("target_present") is not expected_present:
            issues.append(
                f"{path}: {command_id}.target_present "
                f"must be {expected_present!r}"
            )
        if ((target in target_set) is not expected_present):
            issues.append(
                f"{path}: actual target presence drift for {target!r}"
            )

        implementation = row.get("implementation")
        state = row.get("implementation_state")
        if state == "not_implemented":
            if implementation is not None:
                issues.append(
                    f"{path}: {command_id}.implementation must be null"
                )
        elif not isinstance(implementation, str):
            issues.append(
                f"{path}: {command_id}.implementation must be a path"
            )
        elif not (root / implementation).is_file():
            issues.append(
                f"{path}: implementation file missing: {implementation}"
            )

    issues.extend(
        validate_prompt_workflow_contracts(
            root,
            commands,
        )
    )

    prompt = commands.get("prompt-status", {})
    route = prompt.get("blueprint_route")
    if not isinstance(route, dict):
        issues.append(f"{path}: prompt-status.blueprint_route missing")
    else:
        if route.get("source") != (
            "coordination/self_coordination/prompt_queue/index.yaml"
        ):
            issues.append(
                f"{path}: prompt-status source must be self_coordination"
            )
        if route.get("external_module_queue_allowed") is not False:
            issues.append(
                f"{path}: external module queue must remain forbidden"
            )

    coordination = commands.get("coordination-check", {})
    if coordination.get("applicability") != "not_applicable":
        issues.append(
            f"{path}: coordination-check must be not_applicable"
        )
    if coordination.get("not_applicable_reason") != (
        "module_coordination_metadata_contract"
    ):
        issues.append(
            f"{path}: coordination-check reason is invalid"
        )

    self_audit = commands.get("blueprint-self-audit", {})
    if self_audit.get("runtime_state") != (
        "completed_with_unknowns"
    ):
        issues.append(
            f"{path}: blueprint-self-audit.runtime_state "
            "must be completed_with_unknowns"
        )
    if self_audit.get("conformance") != "pass":
        issues.append(
            f"{path}: blueprint-self-audit.conformance "
            "must be pass"
        )

    self_report = commands.get(
        "blueprint-self-report-full",
        {},
    )
    if self_report.get("runtime_state") != "available":
        issues.append(
            f"{path}: blueprint-self-report-full.runtime_state "
            "must be available"
        )
    if self_report.get("conformance") != "pass":
        issues.append(
            f"{path}: blueprint-self-report-full.conformance "
            "must be pass"
        )

    result = data.get("result")
    if not isinstance(result, dict):
        issues.append(f"{path}: result must be a mapping")
    else:
        if result.get("inventory_state") != "completed":
            issues.append(f"{path}: inventory_state must be completed")
        if result.get("conformance_state") != "pass":
            issues.append(f"{path}: conformance_state must be pass")
        if result.get("canonical_gate_state") != "integrated":
            issues.append(
                f"{path}: canonical_gate_state must be integrated"
            )
        if result.get("prompt_workflow_state") != "implemented_gated":
            issues.append(
                f"{path}: prompt_workflow_state must be implemented_gated"
            )
        blockers = result.get("blockers")
        if not isinstance(blockers, list) or set(blockers) != EXPECTED_BLOCKERS:
            issues.append(f"{path}: blockers do not match inventory")
        if result.get("reference_pilot_migration") != "not_authorized":
            issues.append(f"{path}: pilot must remain not_authorized")
        if result.get("external_rollout") != "gated":
            issues.append(f"{path}: external rollout must remain gated")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    issues = validate(Path(args.root).resolve())
    if issues:
        print("❌ Blueprint command applicability validation failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("✅ Blueprint command applicability validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
