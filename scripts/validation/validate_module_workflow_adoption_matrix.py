#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

MATRIX = Path("coordination/standards/adoption/module_workflow_adoption_matrix_v0_1.yaml")
PROGRESS = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-01__blueprint__module_workflow_command_"
    "implementation_progress_v0_1.yaml"
)
REFACTOR = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-02__blueprint__make_workflow_"
    "contract_refactor_completion_v0_1.yaml"
)
SCHEMA = "module_workflow_adoption_matrix_v0_1"
PROGRESS_SCHEMA = (
    "blueprint_module_workflow_command_"
    "implementation_progress_v0_1"
)
REFACTOR_SCHEMA = (
    "blueprint_make_workflow_contract_"
    "refactor_completion_v0_1"
)

COMMANDS: dict[str, tuple[str, str, str, str]] = {
    "prompt-prepare": ("blueprint", "mutating", "blueprint_only", "none"),
    "prompt-release": ("blueprint", "mutating", "blueprint_only", "none"),
    "prompt-status": ("blueprint", "read_only", "none", "none"),
    "module-start": ("module", "mutating", "module_only", "none"),
    "module-sync": ("module", "mutating", "module_only", "none"),
    "module-status": ("module", "read_only", "none", "none"),
    "module-validate": ("module", "read_only", "none", "none"),
    "module-finish": ("module", "mutating", "module_only", "no_commit_no_push_no_merge"),
    "module-publish": ("module", "mutating", "module_only", "commit_and_push_current_branch_no_merge"),
    "completion-packet-validate": ("module", "read_only", "none", "none"),
    "completion-packet-check": ("module", "read_only", "none", "none"),
    "completion-packet-preview": ("module", "read_only", "none", "none"),
    "completion-packet-apply": ("module", "mutating", "module_only", "no_commit_no_push_no_merge"),
    "completion-packet-idempotency-check": ("module", "read_only", "isolated_sandbox_only", "none"),
    "completion-intake-preview": ("blueprint", "read_only", "none", "none"),
    "completion-intake-check": ("blueprint", "read_only", "none", "none"),
    "completion-accept": ("blueprint", "mutating", "blueprint_only", "no_commit_no_push_no_merge"),
    "completion-return": ("blueprint", "mutating", "blueprint_only", "no_commit_no_push_no_merge"),
}

PROFILES = {
    "blueprint_workflow": {
        "prompt-prepare", "prompt-release", "prompt-status",
        "completion-intake-preview", "completion-intake-check",
        "completion-accept", "completion-return",
    },
    "standard_module_workflow": {
        "module-start", "module-sync", "module-status", "module-validate",
        "module-finish", "module-publish", "completion-packet-validate",
        "completion-packet-check", "completion-packet-preview",
        "completion-packet-apply", "completion-packet-idempotency-check",
    },
}


class DuplicateKeyError(yaml.YAMLError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from error
        if duplicate:
            line = key_node.start_mark.line + 1
            column = key_node.start_mark.column + 1
            raise DuplicateKeyError(f"duplicate key `{key}` at line {line}, column {column}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def issue(path: Path, message: str) -> str:
    return f"{path}: {message}"


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [issue(path, "file does not exist")]
    try:
        data = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as error:
        return None, [issue(path, f"invalid YAML: {error}")]
    if not isinstance(data, dict):
        return None, [issue(path, "YAML root must be a mapping")]
    return data, []


def mapping(path: Path, value: Any, name: str, issues: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        issues.append(issue(path, f"`{name}` must be a mapping"))
        return None
    return value


def listing(path: Path, value: Any, name: str, issues: list[str]) -> list[Any] | None:
    if not isinstance(value, list):
        issues.append(issue(path, f"`{name}` must be a list"))
        return None
    return value


def expect(
    path: Path,
    record: dict[str, Any],
    key: str,
    value: Any,
    issues: list[str],
    prefix: str = "",
) -> None:
    actual = record.get(key)
    if actual != value:
        label = f"{prefix}.{key}" if prefix else key
        issues.append(issue(path, f"`{label}` must be {value!r}; found {actual!r}"))


def validate_commands(path: Path, rows: list[Any], issues: list[str]) -> set[str]:
    catalog: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            issues.append(issue(path, f"`command_catalog[{index}]` must be a mapping"))
            continue
        command_id = row.get("command_id")
        if not isinstance(command_id, str) or not command_id:
            issues.append(issue(path, f"`command_catalog[{index}].command_id` must be a non-empty string"))
            continue
        if command_id in catalog:
            issues.append(issue(path, f"duplicate command_id `{command_id}`"))
            continue
        catalog[command_id] = row

    actual_ids = set(catalog)
    for command_id in sorted(set(COMMANDS) - actual_ids):
        issues.append(issue(path, f"required command is missing: `{command_id}`"))
    for command_id in sorted(actual_ids - set(COMMANDS)):
        issues.append(issue(path, f"unsupported v0.1 command: `{command_id}`"))

    for command_id in sorted(actual_ids & set(COMMANDS)):
        row = catalog[command_id]
        owner, mutability, scope, git_behavior = COMMANDS[command_id]
        expected = {
            "owner_repository_class": owner,
            "mutability": mutability,
            "repository_write_scope": scope,
            "git_behavior": git_behavior,
        }
        for key, value in expected.items():
            expect(path, row, key, value, issues, command_id)
        if not isinstance(row.get("command_class"), str) or not row.get("command_class"):
            issues.append(issue(path, f"`{command_id}.command_class` must be a non-empty string"))
        if mutability == "read_only":
            if row.get("repository_write_scope") not in {"none", "isolated_sandbox_only"}:
                issues.append(issue(path, f"read-only command `{command_id}` has a repository write scope"))
            if row.get("git_behavior") != "none":
                issues.append(issue(path, f"read-only command `{command_id}` must not mutate Git state"))

    expect(
        path,
        catalog.get("completion-packet-check", {}),
        "apply_invocation_allowed",
        False,
        issues,
        "completion-packet-check",
    )
    expect(
        path,
        catalog.get("completion-packet-idempotency-check", {}),
        "live_worktree_apply_allowed",
        False,
        issues,
        "completion-packet-idempotency-check",
    )
    expect(
        path,
        catalog.get("completion-intake-check", {}),
        "module_executable_invocation_allowed",
        False,
        issues,
        "completion-intake-check",
    )
    return actual_ids


def validate_refactor_evidence(
    evidence_path: Path,
    issues: list[str],
) -> None:
    data, evidence_issues = load_yaml(evidence_path)
    issues.extend(evidence_issues)
    if data is None:
        return
    expect(evidence_path, data, "schema_version", REFACTOR_SCHEMA, issues)
    expect(
        evidence_path,
        data,
        "result",
        "BLUEPRINT_MAKE_WORKFLOW_CONTRACT_REFACTOR_COMPLETED",
        issues,
    )
    evidence = mapping(evidence_path, data.get("evidence"), "evidence", issues)
    if evidence is not None:
        expect(
            evidence_path,
            evidence,
            "implementation_commit",
            "1c82c929d8608187b52b73d80c651760884d8a58",
            issues,
            "evidence",
        )
        gate = mapping(
            evidence_path,
            evidence.get("blueprint_gate"),
            "evidence.blueprint_gate",
            issues,
        )
        if gate is not None:
            for key, value in {
                "total": 26,
                "passed": 26,
                "warnings": 0,
                "failed": 0,
            }.items():
                expect(
                    evidence_path,
                    gate,
                    key,
                    value,
                    issues,
                    "evidence.blueprint_gate",
                )


def validate_progress_evidence(
    root: Path,
    evidence_path: Path,
    issues: list[str],
) -> None:
    data, evidence_issues = load_yaml(evidence_path)
    issues.extend(evidence_issues)
    if data is None:
        return

    expect(
        evidence_path,
        data,
        "schema_version",
        PROGRESS_SCHEMA,
        issues,
    )
    expect(
        evidence_path,
        data,
        "result",
        "BLUEPRINT_INTERNAL_IMPLEMENTATION_IN_PROGRESS",
        issues,
    )

    subject = mapping(
        evidence_path,
        data.get("subject"),
        "subject",
        issues,
    )
    if subject is not None:
        refactor_path = subject.get("refactor_completion_evidence")
        if refactor_path != REFACTOR.as_posix():
            issues.append(
                issue(
                    evidence_path,
                    "`subject.refactor_completion_evidence` "
                    f"must be {REFACTOR.as_posix()!r}; "
                    f"found {refactor_path!r}",
                )
            )
        else:
            validate_refactor_evidence(root / REFACTOR, issues)

    commits = mapping(
        evidence_path,
        data.get("evidence_commits"),
        "evidence_commits",
        issues,
    )
    if commits is not None:
        expected_commits = {
            "architecture_approval": (
                "6bfd2daaf9b612026087a151ae5886a1c540dc23"
            ),
            "adoption_matrix_validator": (
                "77633316e41b547b6fdcf26f18d4a25788950329"
            ),
            "completion_intake_check": (
                "fea24ac4cea8eb0c9f0fe263bf58676386114503"
            ),
            "completion_acceptance_gate": (
                "c6a5a51c30f227a6cd61e5bfe96b207f9acda27a"
            ),
            "make_workflow_contract_refactor": (
                "1c82c929d8608187b52b73d80c651760884d8a58"
            ),
        }
        for key, value in expected_commits.items():
            expect(
                evidence_path,
                commits,
                key,
                value,
                issues,
                "evidence_commits",
            )

    state = mapping(
        evidence_path,
        data.get("implementation_state"),
        "implementation_state",
        issues,
    )
    if state is not None:
        expected_state = {
            "architecture": "approved_target_standard",
            "adoption_matrix_schema_and_semantics_validator": (
                "implemented"
            ),
            "command_behavior_classification_validator": "implemented",
            "completion_intake_check": "implemented",
            "completion_acceptance_gate": "implemented",
            "blueprint_makefile_refactor": "completed",
            "canonical_module_make_template_refactor": "completed",
            "operational_readiness_review": "completed_pass",
            "implementation_migration": (
                "blueprint_internal_in_progress"
            ),
            "reference_pilot_migration": "not_authorized",
            "canonical_module_make_template_migration": (
                "not_authorized"
            ),
            "external_rollout": "gated",
        }
        for key, value in expected_state.items():
            expect(
                evidence_path,
                state,
                key,
                value,
                issues,
                "implementation_state",
            )

    boundaries = mapping(
        evidence_path,
        data.get("boundaries"),
        "boundaries",
        issues,
    )
    if boundaries is not None:
        expected_boundaries = {
            "historical_approval_rewritten": False,
            "blueprint_makefile_refactor_completed": True,
            "canonical_make_template_refactor_completed": True,
            "external_module_makefile_changes_authorized": False,
            "canonical_make_template_rollout_authorized": False,
            "reference_pilot_prompt_authorized": False,
            "external_module_prompts_released": False,
            "external_rollout_released": False,
            "cross_repository_writes": False,
        }
        for key, value in expected_boundaries.items():
            expect(
                evidence_path,
                boundaries,
                key,
                value,
                issues,
                "boundaries",
            )

    next_step = mapping(
        evidence_path,
        data.get("next_required_step"),
        "next_required_step",
        issues,
    )
    if next_step is not None:
        expect(
            evidence_path,
            next_step,
            "action",
            "reference_pilot_migration_authorization_decision",
            issues,
            "next_required_step",
        )
        expect(
            evidence_path,
            next_step,
            "external_module_action",
            "none",
            issues,
            "next_required_step",
        )
        expect(
            evidence_path,
            next_step,
            "pilot_action",
            "none",
            issues,
            "next_required_step",
        )


def validate(root: Path) -> list[str]:
    path = root / MATRIX
    data, issues = load_yaml(path)
    if data is None:
        return issues

    expect(path, data, "schema_version", SCHEMA, issues)

    metadata = mapping(path, data.get("metadata"), "metadata", issues)
    scope = mapping(path, data.get("scope_model"), "scope_model", issues)
    governance = mapping(path, data.get("governance"), "governance", issues)
    defaults = mapping(path, data.get("command_contract_defaults"), "command_contract_defaults", issues)
    profiles = mapping(path, data.get("repository_class_profiles"), "repository_class_profiles", issues)
    rows = listing(path, data.get("command_catalog"), "command_catalog", issues)
    publication = mapping(path, data.get("publication_evidence"), "publication_evidence", issues)
    snapshot = mapping(path, data.get("assessment_snapshot"), "assessment_snapshot", issues)
    result = mapping(path, data.get("result"), "result", issues)
    requirements = mapping(path, data.get("validation_requirements"), "validation_requirements", issues)

    if metadata is not None:
        expect(path, metadata, "status", "draft", issues, "metadata")
        expect(path, metadata, "authority", "reference_only", issues, "metadata")
        source = mapping(path, metadata.get("source_standard"), "metadata.source_standard", issues)
        if source is not None:
            expect(path, source, "path", "governance/module_workflow_command_architecture_v0_1.md", issues, "metadata.source_standard")
            expect(path, source, "version", "v0_1", issues, "metadata.source_standard")
            expect(path, source, "relationship", "approved_target_standard", issues, "metadata.source_standard")
            commit = source.get("baseline_commit")
            if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
                issues.append(issue(path, "`metadata.source_standard.baseline_commit` must be a 40-character lowercase Git hash"))
            evidence = source.get("approval_evidence")
            if not isinstance(evidence, str) or not evidence:
                issues.append(issue(path, "`metadata.source_standard.approval_evidence` must be a repository-relative path"))
            else:
                evidence_path = root / evidence
                decision, decision_issues = load_yaml(evidence_path)
                issues.extend(decision_issues)
                if decision is not None:
                    expect(evidence_path, decision, "result", "APPROVED", issues)
                    body = mapping(evidence_path, decision.get("decision"), "decision", issues)
                    if body is not None:
                        expect(evidence_path, body, "outcome", "approved_as_target_standard", issues, "decision")
                        expect(evidence_path, body, "implementation_migration_authorized", False, issues, "decision")
                        expect(evidence_path, body, "external_rollout_authorized", False, issues, "decision")

    if scope is not None:
        expect(path, scope, "filesystem_root_is_scope_authority", False, issues, "scope_model")
        default = mapping(
            path,
            scope.get("default_for_newly_admitted_module"),
            "scope_model.default_for_newly_admitted_module",
            issues,
        )
        if default is not None:
            for key, value in {
                "repository_class": "module",
                "assessment_status": "not_assessed",
                "target_conformance": "unknown",
                "rollout_authorized": False,
                "command_profile": "standard_module_workflow",
            }.items():
                expect(path, default, key, value, issues, "scope_model.default_for_newly_admitted_module")

    if governance is not None:
        for key, value in {
            "implementation_migration": (
                "blueprint_internal_in_progress"
            ),
            "external_rollout": "gated",
            "external_module_prompts_released": False,
            "cross_repository_writes_forbidden": True,
            "module_completion_is_blueprint_acceptance": False,
            "publication_is_merge": False,
            "live_worktree_double_apply_forbidden": True,
            "unlisted_module_is_out_of_scope": False,
            "assessment_snapshot_is_exhaustive": False,
        }.items():
            expect(path, governance, key, value, issues, "governance")
        approval = mapping(path, governance.get("architecture_approval"), "governance.architecture_approval", issues)
        if approval is not None:
            expect(path, approval, "state", "approved", issues, "governance.architecture_approval")
            expect(path, approval, "implementation_authorized", False, issues, "governance.architecture_approval")
            expect(path, approval, "external_rollout_authorized", False, issues, "governance.architecture_approval")

        progress = mapping(
            path,
            governance.get("implementation_progress"),
            "governance.implementation_progress",
            issues,
        )
        if progress is not None:
            expect(
                path,
                progress,
                "state",
                "blueprint_internal_in_progress",
                issues,
                "governance.implementation_progress",
            )
            expect(
                path,
                progress,
                "scope",
                "blueprint_repository_only",
                issues,
                "governance.implementation_progress",
            )
            expect(
                path,
                progress,
                "next_required_step",
                "reference_pilot_migration_authorization_decision",
                issues,
                "governance.implementation_progress",
            )
            evidence = progress.get("evidence")
            if evidence != PROGRESS.as_posix():
                issues.append(
                    issue(
                        path,
                        "`governance.implementation_progress.evidence` "
                        f"must be {PROGRESS.as_posix()!r}; "
                        f"found {evidence!r}",
                    )
                )
            else:
                validate_progress_evidence(
                    root,
                    root / PROGRESS,
                    issues,
                )

    if defaults is not None:
        read_only = mapping(path, defaults.get("read_only"), "command_contract_defaults.read_only", issues)
        if read_only is not None:
            for key in (
                "tracked_writes",
                "untracked_repository_writes",
                "git_index_or_ref_writes",
                "cross_repository_writes",
            ):
                expect(path, read_only, key, False, issues, "command_contract_defaults.read_only")
        mutating = mapping(path, defaults.get("mutating"), "command_contract_defaults.mutating", issues)
        if mutating is not None:
            expect(path, mutating, "cross_repository_writes", False, issues, "command_contract_defaults.mutating")
            expect(path, mutating, "hidden_apply_forbidden", True, issues, "command_contract_defaults.mutating")
        publishing = mapping(path, defaults.get("publication"), "command_contract_defaults.publication", issues)
        if publishing is not None:
            expect(path, publishing, "merge_allowed", False, issues, "command_contract_defaults.publication")
            expect(path, publishing, "protected_branch_merge_allowed", False, issues, "command_contract_defaults.publication")

    command_ids = validate_commands(path, rows, issues) if rows is not None else set()

    if profiles is not None:
        for profile_id, expected_commands in PROFILES.items():
            profile = mapping(path, profiles.get(profile_id), f"repository_class_profiles.{profile_id}", issues)
            if profile is None:
                continue
            commands = listing(path, profile.get("commands"), f"repository_class_profiles.{profile_id}.commands", issues)
            if commands is None:
                continue
            if len(commands) != len(set(commands)):
                issues.append(issue(path, f"profile `{profile_id}` contains duplicate commands"))
            for unknown in sorted(set(commands) - command_ids):
                issues.append(issue(path, f"profile `{profile_id}` references unknown command `{unknown}`"))
            if set(commands) != expected_commands:
                issues.append(issue(path, f"profile `{profile_id}` command set does not match the approved v0.1 architecture"))

    if publication is not None:
        pre = mapping(path, publication.get("pre_publication"), "publication_evidence.pre_publication", issues)
        post = mapping(path, publication.get("post_publication"), "publication_evidence.post_publication", issues)
        remote = mapping(path, publication.get("preferred_remote_check"), "publication_evidence.preferred_remote_check", issues)
        if pre is not None:
            expect(path, pre, "remote_containment", "PENDING_PUBLICATION", issues, "publication_evidence.pre_publication")
            expect(path, pre, "push_status", "PENDING_PUBLICATION", issues, "publication_evidence.pre_publication")
            expect(path, pre, "pending_is_success", False, issues, "publication_evidence.pre_publication")
            expect(path, pre, "pending_is_validation_failure", False, issues, "publication_evidence.pre_publication")
        if post is not None:
            expect(path, post, "remote_containment_must_be_verified", True, issues, "publication_evidence.post_publication")
            expect(path, post, "push_status_must_be_verified", True, issues, "publication_evidence.post_publication")
            expect(path, post, "tracked_packet_rewrite_for_new_commit_hash", "forbidden", issues, "publication_evidence.post_publication")
        if remote is not None:
            expect(path, remote, "command_family", "git_ls_remote", issues, "publication_evidence.preferred_remote_check")
            expect(path, remote, "local_remote_tracking_ref_update", False, issues, "publication_evidence.preferred_remote_check")

    if snapshot is not None:
        expect(path, snapshot, "coverage", "partial", issues, "assessment_snapshot")
        expect(path, snapshot, "exhaustive", False, issues, "assessment_snapshot")
        expect(path, snapshot, "omission_means_out_of_scope", False, issues, "assessment_snapshot")
        repositories = listing(path, snapshot.get("repositories"), "assessment_snapshot.repositories", issues)
        if repositories is not None:
            known: set[str] = set()
            for index, repository in enumerate(repositories):
                if not isinstance(repository, dict):
                    issues.append(issue(path, f"`assessment_snapshot.repositories[{index}]` must be a mapping"))
                    continue
                repository_id = repository.get("repository_id")
                if not isinstance(repository_id, str) or not repository_id:
                    issues.append(issue(path, f"`assessment_snapshot.repositories[{index}].repository_id` must be a non-empty string"))
                    continue
                if repository_id in known:
                    issues.append(issue(path, f"duplicate assessment repository_id `{repository_id}`"))
                known.add(repository_id)
                if repository.get("command_profile") not in (profiles or {}):
                    issues.append(issue(path, f"repository `{repository_id}` references unknown command profile `{repository.get('command_profile')}`"))
                if repository.get("rollout_authorized") is not False:
                    issues.append(issue(path, f"repository `{repository_id}` must keep rollout_authorized false while rollout is gated"))

    sequence = listing(
        path,
        data.get("migration_sequence"),
        "migration_sequence",
        issues,
    )
    if sequence is not None:
        steps: dict[int, dict[str, Any]] = {}
        for index, row in enumerate(sequence):
            if not isinstance(row, dict):
                issues.append(
                    issue(
                        path,
                        f"`migration_sequence[{index}]` must be a mapping",
                    )
                )
                continue
            step = row.get("step")
            if not isinstance(step, int):
                issues.append(
                    issue(
                        path,
                        f"`migration_sequence[{index}].step` "
                        "must be an integer",
                    )
                )
                continue
            if step in steps:
                issues.append(issue(path, f"duplicate migration step `{step}`"))
            steps[step] = row
        expected = {
            1: ("approve_command_architecture", "completed"),
            2: ("validate_adoption_matrix_schema_and_semantics", "completed"),
            3: ("add_command_behavior_classification_validator", "completed"),
            4: ("implement_completion_intake_check", "completed"),
            5: (
                "refactor_blueprint_makefile_and_canonical_module_template",
                "completed",
            ),
            6: ("blueprint_operational_readiness_review", "completed"),
            7: ("authorize_reference_pilot_migration", "not_authorized"),
            8: ("migrate_reference_pilot_completion_check", "blocked"),
            9: ("add_reference_pilot_completion_preview", "blocked"),
            10: ("add_reference_pilot_sandbox_idempotency_check", "blocked"),
            11: ("add_reference_pilot_owned_coordination_validator", "blocked"),
            12: ("validate_reference_pilot_conformance", "blocked"),
            13: (
                "assess_remaining_registered_modules_in_controlled_batches",
                "blocked",
            ),
            14: ("authorize_external_rollout", "not_authorized"),
        }
        if set(steps) != set(expected):
            issues.append(
                issue(
                    path,
                    "`migration_sequence` step set does not match "
                    "the approved internal-to-rollout order",
                )
            )
        for step, (action, status) in expected.items():
            row = steps.get(step, {})
            expect(
                path, row, "action", action, issues,
                f"migration_sequence.step_{step}",
            )
            expect(
                path, row, "status", status, issues,
                f"migration_sequence.step_{step}",
            )

    pilot = data.get("pilot_reference")
    if pilot is not None:
        pilot_map = mapping(path, pilot, "pilot_reference", issues)
        if pilot_map is not None:
            expect(path, pilot_map, "scope_effect", "none", issues, "pilot_reference")
            expect(path, pilot_map, "permanent_architecture_dependency", False, issues, "pilot_reference")

    if result is not None:
        expect(path, result, "architecture_state", "approved_target_standard", issues, "result")
        expect(path, result, "future_module_inheritance", "automatic", issues, "result")
        expect(path, result, "external_rollout", "gated", issues, "result")

    if requirements is not None:
        for key, value in sorted(requirements.items()):
            if value is not True:
                issues.append(issue(path, f"`validation_requirements.{key}` must be true"))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Blueprint module-workflow adoption matrix.")
    parser.add_argument("--root", default=".", help="Blueprint repository root.")
    args = parser.parse_args()
    issues = validate(Path(args.root).resolve())
    if issues:
        print("❌ Module workflow adoption matrix validation failed:")
        for item in issues:
            print(f"  - {item}")
        return 1
    print("✅ Module workflow adoption matrix validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
