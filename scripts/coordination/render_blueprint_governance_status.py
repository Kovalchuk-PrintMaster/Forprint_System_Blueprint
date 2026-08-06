#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

PROGRESS = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-01__blueprint__module_workflow_command_"
    "implementation_progress_v0_1.yaml"
)
READINESS_CLOSEOUT = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-04__blueprint__operational_readiness_review_"
    "closeout_v0_1.yaml"
)
ADOPTION_MATRIX = Path(
    "coordination/standards/adoption/"
    "module_workflow_adoption_matrix_v0_1.yaml"
)
RELEASE_POLICY = Path(
    "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)
MUTATION_BUILDER_CONTRACT = Path(
    "coordination/standards/governance/"
    "mutation_builder_contract_v0_1.yaml"
)
CHECK_CATALOG = Path("scripts/run_blueprint_checks.py")

SOURCE_PATHS = (
    PROGRESS,
    READINESS_CLOSEOUT,
    ADOPTION_MATRIX,
    RELEASE_POLICY,
    MUTATION_BUILDER_CONTRACT,
    CHECK_CATALOG,
)

TEN_STEP_FORWARD_PLAN = (
    {
        "step": 1,
        "action": "formalize_canonical_mutation_builder_contract",
        "phase": "governance_foundation",
        "status": "completed",
    },
    {
        "step": 2,
        "action": "integrate_mutation_builder_contract_validator",
        "phase": "canonical_gate",
        "status": "completed",
    },
    {
        "step": 3,
        "action": "establish_current_state_transparency_manifest",
        "phase": "governance_observability",
        "status": "completed",
    },
    {
        "step": 4,
        "action": "add_read_only_governance_status_command",
        "phase": "operator_interface",
        "status": "completed",
    },
    {
        "step": 5,
        "action": "define_reference_pilot_authorization_criteria",
        "phase": "decision_contract",
        "status": "next",
    },
    {
        "step": 6,
        "action": "assess_reference_pilot_candidate",
        "phase": "read_only_assessment",
        "status": "blocked",
    },
    {
        "step": 7,
        "action": "reference_pilot_migration_authorization_decision",
        "phase": "explicit_governance_decision",
        "status": "blocked",
    },
    {
        "step": 8,
        "action": "run_reference_pilot_preview",
        "phase": "read_only_preview",
        "status": "blocked",
    },
    {
        "step": 9,
        "action": "execute_bounded_reference_pilot",
        "phase": "authorized_mutation",
        "status": "blocked",
    },
    {
        "step": 10,
        "action": "close_reference_pilot_and_decide_next_batch",
        "phase": "post_pilot_review",
        "status": "blocked",
    },
)


class TransparencyFailure(RuntimeError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(
            path.read_text(encoding="utf-8"),
            Loader=UniqueKeyLoader,
        )
    except (OSError, yaml.YAMLError) as error:
        raise TransparencyFailure(
            f"Could not load YAML source {path}: {error}"
        ) from error

    if not isinstance(value, dict):
        raise TransparencyFailure(
            f"YAML source root must be a mapping: {path}"
        )
    return value


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TransparencyFailure(f"{label} must be a mapping")
    return value


def require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TransparencyFailure(f"{label} must be a list")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TransparencyFailure(f"{label} must be a non-empty string")
    return value


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise TransparencyFailure(f"{label} must be a boolean")
    return value


def require_key(
    mapping: dict[str, Any],
    key: str,
    label: str,
) -> Any:
    if key not in mapping:
        raise TransparencyFailure(f"{label}.{key} is missing")
    return mapping[key]


def authorization_value(value: Any, label: str) -> bool:
    status = require_string(value, label)
    if status in {"authorized", "completed"}:
        return True
    if status in {"not_authorized", "blocked"}:
        return False
    raise TransparencyFailure(
        f"{label} has unsupported authorization state: {status!r}"
    )


def git_text(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise TransparencyFailure(
            f"Git command failed: git {' '.join(args)}\n{result.stdout}"
        )
    return result.stdout.rstrip("\n")


def read_repository_state(root: Path) -> dict[str, Any]:
    tracked_status = git_text(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
    )
    return {
        "branch": git_text(root, "branch", "--show-current"),
        "head": git_text(root, "rev-parse", "HEAD"),
        "tracked_worktree_clean": not bool(tracked_status),
        "tracked_changes": tracked_status.splitlines(),
    }


def parse_check_catalog(path: Path) -> dict[str, Any]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as error:
        raise TransparencyFailure(
            f"Could not parse canonical check catalog {path}: {error}"
        ) from error

    check_ids: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "CheckDefinition":
            continue
        keywords = {item.arg: item.value for item in node.keywords}
        check_id = keywords.get("check_id")
        if isinstance(check_id, ast.Constant) and isinstance(
            check_id.value,
            str,
        ):
            check_ids.append(check_id.value)

    return {
        "count": len(check_ids),
        "unique_count": len(set(check_ids)),
        "check_ids": check_ids,
        "catalog_consistent": len(check_ids) == len(set(check_ids)),
        "execution_state": "not_executed_by_status_command",
    }


def find_blueprint_assessment(matrix: dict[str, Any]) -> dict[str, Any]:
    snapshot = require_mapping(
        matrix.get("assessment_snapshot"),
        "assessment_snapshot",
    )
    repositories = require_list(
        snapshot.get("repositories"),
        "assessment_snapshot.repositories",
    )
    matches = [
        row
        for row in repositories
        if isinstance(row, dict)
        and row.get("repository_id") == "forprint_system_blueprint"
    ]
    if len(matches) != 1:
        raise TransparencyFailure(
            "Expected exactly one Blueprint assessment record"
        )
    return matches[0]


def find_migration_step(
    migration: list[Any],
    action: str,
) -> dict[str, Any]:
    matches = [
        row
        for row in migration
        if isinstance(row, dict) and row.get("action") == action
    ]
    if len(matches) != 1:
        raise TransparencyFailure(
            f"Expected exactly one migration step for {action!r}"
        )
    return matches[0]


def normalized_string_list(value: Any, label: str) -> list[str]:
    rows = require_list(value, label)
    if not all(isinstance(item, str) and item for item in rows):
        raise TransparencyFailure(f"{label} must contain strings")
    return sorted(rows)


def agreement_check(
    check_id: str,
    observations: dict[str, Any],
    *,
    expected: Any | None = None,
    expected_is_set: bool = False,
) -> dict[str, Any]:
    values = list(observations.values())
    agreed = bool(values) and all(value == values[0] for value in values)
    if expected_is_set:
        agreed = agreed and all(value == expected for value in values)
    return {
        "check_id": check_id,
        "state": "agreed" if agreed else "disagreed",
        "expected": expected if expected_is_set else None,
        "observations": observations,
    }


def build_manifest(
    root: Path,
    *,
    repository_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    missing = [
        relative.as_posix()
        for relative in SOURCE_PATHS
        if not (root / relative).is_file()
    ]
    if missing:
        raise TransparencyFailure(
            "Required transparency sources are missing: "
            + ", ".join(missing)
        )

    progress = load_yaml(root / PROGRESS)
    closeout = load_yaml(root / READINESS_CLOSEOUT)
    matrix = load_yaml(root / ADOPTION_MATRIX)
    release_policy = load_yaml(root / RELEASE_POLICY)
    builder_contract = load_yaml(root / MUTATION_BUILDER_CONTRACT)
    catalog = parse_check_catalog(root / CHECK_CATALOG)
    repository = repository_state or read_repository_state(root)

    implementation = require_mapping(
        progress.get("implementation_state"),
        "progress.implementation_state",
    )
    progress_boundaries = require_mapping(
        progress.get("boundaries"),
        "progress.boundaries",
    )
    progress_next = require_mapping(
        progress.get("next_required_step"),
        "progress.next_required_step",
    )
    closeout_decision = require_mapping(
        closeout.get("decision"),
        "closeout.decision",
    )
    closeout_boundaries = require_mapping(
        closeout.get("boundaries"),
        "closeout.boundaries",
    )
    closeout_next = require_mapping(
        closeout.get("next_required_step"),
        "closeout.next_required_step",
    )
    release = require_mapping(
        release_policy.get("release"),
        "release_policy.release",
    )
    release_result = require_mapping(
        release_policy.get("result"),
        "release_policy.result",
    )
    migration = require_list(
        matrix.get("migration_sequence"),
        "matrix.migration_sequence",
    )
    assessment = find_blueprint_assessment(matrix)
    assessment_evidence = require_mapping(
        assessment.get("evidence"),
        "Blueprint assessment evidence",
    )
    pilot_step = find_migration_step(
        migration,
        "authorize_reference_pilot_migration",
    )

    progress_blockers = normalized_string_list(
        progress_boundaries.get(
            "operational_readiness_remaining_blockers"
        ),
        "progress operational blockers",
    )
    closeout_blockers = normalized_string_list(
        closeout.get("remaining_readiness_blockers"),
        "closeout remaining blockers",
    )
    assessment_blockers = normalized_string_list(
        assessment.get("known_gaps"),
        "Blueprint assessment known gaps",
    )

    next_action_observations = {
        PROGRESS.as_posix(): require_string(
            progress_next.get("action"),
            "progress next action",
        ),
        READINESS_CLOSEOUT.as_posix(): require_string(
            closeout_next.get("action"),
            "closeout next action",
        ),
        ADOPTION_MATRIX.as_posix(): require_string(
            assessment.get("next_required_step"),
            "Blueprint assessment next action",
        ),
    }

    checks = [
        agreement_check(
            "historical_assessment_branch_provenance",
            {
                (
                    f"{ADOPTION_MATRIX}:"
                    "assessment_evidence_branch_recorded"
                ): bool(
                    require_string(
                        assessment_evidence.get("branch"),
                        "Blueprint assessment branch",
                    )
                ),
            },
            expected=True,
            expected_is_set=True,
        ),
        agreement_check(
            "active_blocker_agreement",
            {
                PROGRESS.as_posix(): progress_blockers,
                READINESS_CLOSEOUT.as_posix(): closeout_blockers,
                ADOPTION_MATRIX.as_posix(): assessment_blockers,
            },
        ),
        agreement_check(
            "next_governance_action_agreement",
            next_action_observations,
        ),
        agreement_check(
            "pilot_authorization_boundary",
            {
                f"{PROGRESS}:implementation_state": (
                    authorization_value(
                        implementation.get(
                            "reference_pilot_migration"
                        ),
                        "progress reference pilot migration",
                    )
                ),
                f"{PROGRESS}:boundaries": not require_bool(
                    progress_boundaries.get(
                        "reference_pilot_migration_remains_blocked"
                    ),
                    "progress reference pilot remains blocked",
                ),
                f"{READINESS_CLOSEOUT}:decision": require_bool(
                    closeout_decision.get(
                        "reference_pilot_migration_authorized"
                    ),
                    "closeout pilot authorization",
                ),
                f"{READINESS_CLOSEOUT}:boundaries": require_bool(
                    closeout_boundaries.get("pilot_authorized"),
                    "closeout pilot boundary",
                ),
                f"{ADOPTION_MATRIX}:migration_sequence": (
                    authorization_value(
                        pilot_step.get("status"),
                        "migration pilot authorization step",
                    )
                ),
                f"{RELEASE_POLICY}:result": (
                    authorization_value(
                        release_result.get(
                            "reference_pilot_migration"
                        ),
                        "release policy pilot migration",
                    )
                ),
            },
            expected=False,
            expected_is_set=True,
        ),
        agreement_check(
            "external_prompt_release_boundary",
            {
                f"{PROGRESS}:boundaries": require_bool(
                    progress_boundaries.get(
                        "external_module_prompts_released"
                    ),
                    "progress external prompts released",
                ),
                f"{READINESS_CLOSEOUT}:decision": require_bool(
                    closeout_decision.get(
                        "external_module_prompts_released"
                    ),
                    "closeout decision external prompts released",
                ),
                f"{READINESS_CLOSEOUT}:boundaries": require_bool(
                    closeout_boundaries.get(
                        "external_prompts_released"
                    ),
                    "closeout boundary external prompts released",
                ),
                f"{RELEASE_POLICY}:release": require_bool(
                    release.get("global_enabled"),
                    "release policy global enabled",
                ),
            },
            expected=False,
            expected_is_set=True,
        ),
        agreement_check(
            "external_rollout_boundary",
            {
                f"{PROGRESS}:implementation_state": require_string(
                    implementation.get("external_rollout"),
                    "progress external rollout",
                ),
                f"{READINESS_CLOSEOUT}:decision": require_string(
                    closeout_decision.get("external_rollout"),
                    "closeout decision external rollout",
                ),
                f"{READINESS_CLOSEOUT}:boundaries": require_string(
                    closeout_boundaries.get("release_policy_state"),
                    "closeout release policy state",
                ),
                f"{RELEASE_POLICY}:result.external_rollout": (
                    require_string(
                        release_result.get("external_rollout"),
                        "release policy external rollout",
                    )
                ),
                f"{RELEASE_POLICY}:result.operational_state": (
                    require_string(
                        release_result.get("operational_state"),
                        "release policy operational state",
                    )
                ),
            },
            expected="gated",
            expected_is_set=True,
        ),
        agreement_check(
            "release_authorized_modules_boundary",
            {
                f"{RELEASE_POLICY}:authorized_modules": (
                    require_list(
                        release.get("authorized_modules"),
                        "release policy authorized modules",
                    )
                )
            },
            expected=[],
            expected_is_set=True,
        ),
        agreement_check(
            "release_authorization_evidence_boundary",
            {
                f"{RELEASE_POLICY}:authorization_evidence": (
                    require_key(
                        release,
                        "authorization_evidence",
                        "release policy",
                    )
                )
            },
            expected=None,
            expected_is_set=True,
        ),
        agreement_check(
            "mutation_builder_contract_active",
            {
                f"{MUTATION_BUILDER_CONTRACT}:result": require_mapping(
                    builder_contract.get("result"),
                    "mutation builder result",
                ).get("contract_state")
            },
            expected="active",
            expected_is_set=True,
        ),
        agreement_check(
            "canonical_check_catalog_unique",
            {
                CHECK_CATALOG.as_posix(): catalog[
                    "catalog_consistent"
                ]
            },
            expected=True,
            expected_is_set=True,
        ),
    ]

    disagreements = [
        check
        for check in checks
        if check["state"] != "agreed"
    ]
    source_consistency = {
        "state": "agreed" if not disagreements else "failed",
        "check_count": len(checks),
        "disagreement_count": len(disagreements),
        "checks": checks,
        "disagreements": disagreements,
    }

    historical_verification = require_mapping(
        closeout.get("verification"),
        "closeout.verification",
    )
    historical_gate = require_mapping(
        historical_verification.get("canonical_gate"),
        "closeout historical canonical gate",
    )
    historical_policy = require_mapping(
        closeout.get("historical_evidence_policy"),
        "closeout historical evidence policy",
    )

    manifest = {
        "schema_version": (
            "project_transparency_current_state_manifest_v0_1"
        ),
        "projection": {
            "role": "current_state_projection",
            "independent_authority": False,
            "historical_evidence_rewritten": False,
            "pilot_authorization_effect": "none",
            "release_policy_effect": "none",
        },
        "observed_repository_state": {
            "branch": repository["branch"],
            "head": repository["head"],
            "tracked_worktree_clean": repository[
                "tracked_worktree_clean"
            ],
            "tracked_changes": repository["tracked_changes"],
        },
        "governance_decision_state": {
            "current_phase": implementation.get(
                "implementation_migration"
            ),
            "operational_readiness_state": implementation.get(
                "operational_readiness_state"
            ),
            "active_blockers": progress_blockers,
            "next_required_action": progress_next["action"],
            "migration_dependency_chain": migration,
        },
        "coordination_control_state": {
            "current_phase": (
                "governance_observability_control_layer"
            ),
            "hold": (
                "pilot remains gated until transparency control "
                "layer is committed and accepted"
            ),
            "next_required_action": (
                "define_reference_pilot_authorization_criteria"
            ),
            "authority": "coordination_proposal",
            "authorization_effect": "none",
            "ten_step_forward_plan": [
                dict(item)
                for item in TEN_STEP_FORWARD_PLAN
            ],
        },
        "authorization_evidence": {
            "reference_pilot_authorized": False,
            "external_prompts_released": False,
            "external_rollout": "gated",
            "release_policy_global_enabled": require_bool(
                release.get("global_enabled"),
                "release policy global enabled",
            ),
            "authorized_modules": require_list(
                release.get("authorized_modules"),
                "release policy authorized modules",
            ),
            "release_authorization_evidence": require_key(
                release,
                "authorization_evidence",
                "release policy",
            ),
        },
        "canonical_checks": {
            **catalog,
            "historical_closeout_gate": historical_gate,
            "historical_evidence_immutable": bool(
                historical_policy.get(
                    "prior_closeout_records_remain_immutable"
                )
            ),
        },
        "source_files": {
            relative.as_posix(): {
                "sha256": sha256(root / relative),
            }
            for relative in SOURCE_PATHS
        },
        "source_consistency": source_consistency,
        "boundaries": {
            "read_only_projection": True,
            "tracked_writes": False,
            "git_mutations": False,
            "pilot_authorized_by_rendering": False,
            "release_policy_changed_by_rendering": False,
            "historical_evidence_rewritten": False,
            "external_rollout_authorized": False,
        },
        "result": (
            "PROJECT_TRANSPARENCY_CURRENT_STATE_AGREED"
            if not disagreements
            else "PROJECT_TRANSPARENCY_CURRENT_STATE_FAILED_CLOSED"
        ),
    }
    return manifest


def render_status(manifest: dict[str, Any]) -> str:
    repository = manifest["observed_repository_state"]
    governance = manifest["governance_decision_state"]
    coordination = manifest["coordination_control_state"]
    authorization = manifest["authorization_evidence"]
    checks = manifest["canonical_checks"]
    consistency = manifest["source_consistency"]

    lines = [
        "ForPrint Blueprint Governance Status",
        "",
        "Repository",
        f"  branch: {repository['branch']}",
        f"  HEAD: {repository['head']}",
        (
            "  tracked worktree clean: "
            f"{str(repository['tracked_worktree_clean']).lower()}"
        ),
        "",
        "Observed governance decision state",
        f"  current phase: {governance['current_phase']}",
        (
            "  operational readiness: "
            f"{governance['operational_readiness_state']}"
        ),
        "  active blockers:",
    ]
    blockers = governance["active_blockers"]
    lines.extend(
        f"    - {blocker}" for blocker in blockers
    )
    if not blockers:
        lines.append("    - none")
    lines.extend(
        [
            (
                "  next required action: "
                f"{governance['next_required_action']}"
            ),
            "",
            "Coordination control state",
            f"  current phase: {coordination['current_phase']}",
            f"  hold: {coordination['hold']}",
            (
                "  next coordination action: "
                f"{coordination['next_required_action']}"
            ),
            "  authority: coordination proposal",
            "",
            "Authorization boundaries",
            (
                "  reference pilot authorized: "
                f"{str(authorization['reference_pilot_authorized']).lower()}"
            ),
            (
                "  external prompts released: "
                f"{str(authorization['external_prompts_released']).lower()}"
            ),
            (
                "  external rollout: "
                f"{authorization['external_rollout']}"
            ),
            (
                "  authorized modules: "
                f"{authorization['authorized_modules']}"
            ),
            "",
            "Canonical checks",
            f"  catalog count: {checks['count']}",
            f"  unique count: {checks['unique_count']}",
            f"  execution state: {checks['execution_state']}",
            (
                "  historical closeout: "
                f"{checks['historical_closeout_gate']}"
            ),
            "",
            "Migration dependency chain",
        ]
    )
    for row in governance["migration_dependency_chain"]:
        lines.append(
            "  "
            f"{row.get('step')}. {row.get('action')} "
            f"[{row.get('status')}]"
        )
    lines.extend(["", "Ten-step forward plan"])
    for row in coordination["ten_step_forward_plan"]:
        lines.append(
            "  "
            f"{row['step']}. {row['action']} "
            f"[{row['status']}]"
        )
    lines.extend(
        [
            "",
            "Source consistency",
            f"  state: {consistency['state']}",
            (
                "  disagreements: "
                f"{consistency['disagreement_count']}"
            ),
        ]
    )
    for row in consistency["disagreements"]:
        lines.append(f"    - {row['check_id']}")
    lines.extend(
        [
            "",
            (
                "Result: "
                f"{manifest['result']}"
            ),
        ]
    )
    return "\n".join(lines)


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render the fail-closed Blueprint governance status "
            "and current-state manifest."
        )
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Blueprint repository root.",
    )
    parser.add_argument(
        "--format",
        choices=("status", "yaml", "json"),
        default="status",
        help="Output format. All formats are read-only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_cli().parse_args(argv)
    try:
        manifest = build_manifest(Path(args.repo_root))
    except TransparencyFailure as error:
        print(f"FAILED: {error}")
        print(
            "RESULT: "
            "PROJECT_TRANSPARENCY_CURRENT_STATE_FAILED_CLOSED"
        )
        return 1

    if args.format == "json":
        print(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.format == "yaml":
        print(
            yaml.safe_dump(
                manifest,
                sort_keys=False,
                allow_unicode=True,
                width=120,
            ),
            end="",
        )
    else:
        print(render_status(manifest))

    return (
        0
        if manifest["source_consistency"]["state"] == "agreed"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
