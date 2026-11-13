#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
DETAIL_ROOT = ROOT / "coordination/roadmaps/details/forprint_system_blueprint"
REGISTRY = ROOT / "coordination/standards/governance/document_type_registry_v0_1.yaml"
BASELINE = (
    ROOT
    / "coordination/internal_work/blueprint/normalization/"
    "2026-09-01__document_surface_normalization_baseline_v0_1.yaml"
)
PROJECTION_MD = DETAIL_ROOT / "portfolio_full_horizon_target_states_v0_1.md"

EXPECTED_PROJECTION_STATUS = "PROPOSED_PORTFOLIO_BASELINE_REQUIRES_OWNER_REVIEW"

VARIANT_SCHEMAS = {
    "planning_template": {
        "forprint_module_baseline_progress_assessment_v0_1": {
            "module_id",
            "baseline_date",
            "roadmap_snapshot_ref",
            "estimated_total_weight",
            "accepted_completed_weight",
            "estimated_progress_percent",
            "confidence",
            "assessment_notes",
            "evidence_refs",
        },
        "forprint_module_roadmap_v0_2_template": {
            "module_id",
            "roadmap_status",
            "target_state",
            "baseline",
            "steps",
        },
    },
    "specialized_planning_seed": {
        "forprint_dependency_matrix_seed_v0_1": {
            "dependency_types",
            "required_fields",
            "dependencies",
            "note",
        },
        "forprint_portfolio_module_inventory_seed_v0_1": {
            "identity_notes",
            "modules",
        },
        "forprint_requirements_backlog_seed_v0_1": {
            "requirements",
        },
    },
}

EXPECTED_SINGLE_SCHEMAS = {
    "knowledge_foundation_program": "forprint_blueprint_knowledge_foundation_program_v0_1",
    "module_bootstrap_plan": "forprint_module_bootstrap_plan_v0_1",
    "roadmap_authority_rebuild_register": "non_blueprint_roadmap_authority_rebuild_register_v0_1",
    "portfolio_target_projection": "forprint_portfolio_full_horizon_target_states_v0_1",
    "portfolio_rebuild_input": "forprint_portfolio_first_pass_status_map_v0_1",
    "evening_architecture_action_matrix": "forprint_evening_architecture_action_matrix_v1_0",
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def one_h1(path: Path) -> bool:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            count += 1
    return count == 1


def run_existing_validator(script: str, issues: list[str]) -> None:
    process = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if process.returncode:
        issues.append(
            f"DELEGATED_VALIDATOR_FAIL:{script}:{process.stdout.strip()}"
        )


def validate_variant(
    subclass_id: str,
    rel: str,
    data: dict[str, Any],
    issues: list[str],
) -> None:
    schema = data.get("schema_version")

    if subclass_id in VARIANT_SCHEMAS:
        variants = VARIANT_SCHEMAS[subclass_id]
        require(
            schema in variants,
            f"{rel}: unsupported schema {schema!r} for {subclass_id}",
            issues,
        )
        if schema in variants:
            missing = sorted(variants[schema] - set(data))
            require(
                not missing,
                f"{rel}: missing variant fields {','.join(missing)}",
                issues,
            )

    elif subclass_id in EXPECTED_SINGLE_SCHEMAS:
        require(
            schema == EXPECTED_SINGLE_SCHEMAS[subclass_id],
            f"{rel}: schema drift for {subclass_id}: {schema!r}",
            issues,
        )


def validate_semantics(
    subclass_id: str,
    rel: str,
    data: dict[str, Any],
    issues: list[str],
) -> None:
    if subclass_id == "planning_template":
        require(
            data.get("status") == "CURRENT_PLANNING_TEMPLATE",
            f"{rel}: planning template status drift",
            issues,
        )
        require(
            data.get("authority")
            == "planning_template_not_release_or_execution_authority",
            f"{rel}: planning template authority drift",
            issues,
        )
        require(
            data.get("module_id") == "REQUIRED",
            f"{rel}: template module_id placeholder drift",
            issues,
        )

    elif subclass_id == "specialized_planning_seed":
        require(
            data.get("authority")
            == "staging_planning_seed_not_release_or_execution_authority",
            f"{rel}: staging seed authority drift",
            issues,
        )
        allowed_status = {
            "STAGING_SEED_REQUIRES_CROSS_MODULE_REVIEW",
            "STAGING_SEED_NOT_YET_AUTHORITY",
            "STAGING_SEED",
        }
        require(
            data.get("status") in allowed_status,
            f"{rel}: staging seed status drift",
            issues,
        )

        if data.get("schema_version") == "forprint_dependency_matrix_seed_v0_1":
            require(
                data.get("dependencies") == [],
                f"{rel}: dependency seed must remain empty until reviewed",
                issues,
            )
            require(
                isinstance(data.get("note"), str)
                and "not auto-invented" in data["note"],
                f"{rel}: dependency seed no-invention note drift",
                issues,
            )

        if data.get("schema_version") == "forprint_requirements_backlog_seed_v0_1":
            requirements = data.get("requirements")
            require(
                isinstance(requirements, list) and bool(requirements),
                f"{rel}: requirements seed empty",
                issues,
            )
            if isinstance(requirements, list):
                ids = [
                    item.get("id")
                    for item in requirements
                    if isinstance(item, dict)
                ]
                require(
                    len(ids) == len(set(ids)),
                    f"{rel}: duplicate requirement IDs",
                    issues,
                )

    elif subclass_id == "knowledge_foundation_program":
        require(
            data.get("status") == "PLANNED_NOT_ACTIVE",
            f"{rel}: knowledge program status drift",
            issues,
        )
        require(
            data.get("authority")
            == "future_planning_program_not_current_release_or_execution_authority",
            f"{rel}: knowledge program authority drift",
            issues,
        )
        boundary = data.get("activation_boundary")
        require(
            isinstance(boundary, dict),
            f"{rel}: activation boundary missing",
            issues,
        )
        if isinstance(boundary, dict):
            require(
                boundary.get("current_release_changed_by_this_file") is False,
                f"{rel}: knowledge program may not change current release",
                issues,
            )
            require(
                boundary.get("current_h10_h11_sequence_preserved") is True,
                f"{rel}: H10/H11 preservation drift",
                issues,
            )

    elif subclass_id == "module_bootstrap_plan":
        require(
            data.get("status") == "PLANNING_BOOTSTRAP_INPUT",
            f"{rel}: bootstrap plan status drift",
            issues,
        )
        require(
            data.get("authority")
            == "planning_bootstrap_input_not_release_or_execution_authority",
            f"{rel}: bootstrap plan authority drift",
            issues,
        )
        modules = data.get("modules")
        require(
            isinstance(modules, list) and bool(modules),
            f"{rel}: bootstrap modules missing",
            issues,
        )
        if isinstance(modules, list):
            required = {
                "module_id",
                "root_path",
                "root_action",
                "blueprint_policy_action",
                "roadmap_action",
            }
            for index, item in enumerate(modules):
                require(
                    isinstance(item, dict) and required <= set(item),
                    f"{rel}: bootstrap modules[{index}] field drift",
                    issues,
                )

    elif subclass_id == "roadmap_authority_rebuild_register":
        require(
            data.get("status") == "ACTIVE_PORTFOLIO_REBUILD_CONTROL",
            f"{rel}: rebuild register status drift",
            issues,
        )
        require(
            data.get("authority")
            == "portfolio_rebuild_control_not_release_or_execution_authority",
            f"{rel}: rebuild register authority drift",
            issues,
        )
        metadata = data.get("metadata")
        require(
            isinstance(metadata, dict) and "status" not in metadata,
            f"{rel}: legacy nested metadata.status must stay retired",
            issues,
        )
        roadmaps = data.get("roadmaps")
        require(
            isinstance(roadmaps, list) and bool(roadmaps),
            f"{rel}: rebuild register roadmaps missing",
            issues,
        )
        if isinstance(roadmaps, list):
            for index, item in enumerate(roadmaps):
                require(
                    isinstance(item, dict)
                    and item.get("post_q_automation_selection_authority") is False
                    and item.get("preserve_historical_prompt_and_acceptance_evidence")
                    is True,
                    f"{rel}: roadmaps[{index}] authority/preservation drift",
                    issues,
                )

    elif subclass_id == "portfolio_target_projection":
        require(
            data.get("status") == EXPECTED_PROJECTION_STATUS,
            f"{rel}: portfolio projection status drift",
            issues,
        )
        require(
            data.get("authority") == "planning_projection_not_release_authority",
            f"{rel}: portfolio projection authority drift",
            issues,
        )
        gate = data.get("global_execution_gate")
        require(
            isinstance(gate, dict)
            and gate.get("ordinary_module_implementation_allowed") is False,
            f"{rel}: ordinary module implementation gate widened",
            issues,
        )
        modules = data.get("modules")
        require(
            isinstance(modules, dict) and len(modules) >= 22,
            f"{rel}: portfolio projection module set unexpectedly shrank",
            issues,
        )
        if isinstance(modules, dict):
            for module_id, item in modules.items():
                require(
                    isinstance(item, dict)
                    and item.get("implementation_eligible_now") is False,
                    f"{rel}: {module_id} implementation eligibility widened",
                    issues,
                )

    elif subclass_id == "portfolio_rebuild_input":
        require(
            data.get("status") == "NON_AUTHORITATIVE_PLANNING_INPUT",
            f"{rel}: rebuild input status drift",
            issues,
        )
        require(
            data.get("authority")
            == "planning_input_not_release_or_execution_authority",
            f"{rel}: rebuild input authority drift",
            issues,
        )
        require(
            "schema" not in data,
            f"{rel}: legacy schema alias reintroduced",
            issues,
        )
        notes = data.get("notes")
        require(
            isinstance(notes, list)
            and any(
                isinstance(note, str)
                and "No entry activates implementation or changes current release authority."
                in note
                for note in notes
            ),
            f"{rel}: non-authority note drift",
            issues,
        )

    elif subclass_id == "evening_architecture_action_matrix":
        require(
            data.get("authority") == "NONE",
            f"{rel}: action matrix authority drift",
            issues,
        )
        boundaries = data.get("protected_boundaries")
        require(
            isinstance(boundaries, dict)
            and all(value is False for value in boundaries.values()),
            f"{rel}: action matrix protected boundary widened",
            issues,
        )


def main() -> int:
    issues: list[str] = []

    run_existing_validator(
        "scripts/validation/validate_portfolio_rebuild_seed_surfaces_v0_1.py",
        issues,
    )
    run_existing_validator(
        "scripts/validation/validate_continuity_roadmap_detail_surfaces_v0_1.py",
        issues,
    )

    registry = load_yaml(REGISTRY)
    baseline = load_yaml(BASELINE)

    roadmap_detail = next(
        (
            item
            for item in registry.get("types", [])
            if isinstance(item, dict)
            and item.get("document_type") == "roadmap_detail"
        ),
        None,
    )
    require(
        isinstance(roadmap_detail, dict),
        "roadmap_detail registry entry missing",
        issues,
    )

    if not isinstance(roadmap_detail, dict):
        print("ROADMAP_DETAIL_SURFACES=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1

    require(
        roadmap_detail.get("migration_state") == "STRICT",
        "roadmap_detail parent class must be STRICT",
        issues,
    )

    try:
        import importlib.util

        source = ROOT / "scripts/validation/validate_document_surface_registry_v0_1.py"
        spec = importlib.util.spec_from_file_location(
            "forprint_document_surface_registry_validator",
            source,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot create validator import spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        effective_profile = module.effective_profile
    except Exception as exc:
        issues.append(f"cannot load effective_profile: {exc}")
        effective_profile = None

    yaml_paths = sorted(DETAIL_ROOT.rglob("*.yaml"))
    markdown_paths = sorted(DETAIL_ROOT.rglob("*.md"))

    subclass_counts: dict[str, int] = {}

    for path in yaml_paths:
        rel = path.relative_to(ROOT).as_posix()
        data = load_yaml(path)

        require(
            isinstance(data, dict),
            f"{rel}: YAML root must be mapping",
            issues,
        )
        if not isinstance(data, dict) or effective_profile is None:
            continue

        try:
            profile = effective_profile(roadmap_detail, rel)
        except Exception as exc:
            issues.append(f"{rel}: profile resolution failed: {exc}")
            continue

        subclass_id = profile.get("subclass_id")
        require(
            isinstance(subclass_id, str) and bool(subclass_id),
            f"{rel}: YAML has no strict roadmap_detail subclass",
            issues,
        )
        if not isinstance(subclass_id, str) or not subclass_id:
            continue

        require(
            profile.get("migration_state") == "STRICT",
            f"{rel}: subclass {subclass_id} is not STRICT",
            issues,
        )
        subclass_counts[subclass_id] = subclass_counts.get(subclass_id, 0) + 1

        required = profile.get("required_top_level", [])
        if isinstance(required, list):
            missing = [key for key in required if key not in data]
            require(
                not missing,
                f"{rel}: missing required metadata {','.join(map(str, missing))}",
                issues,
            )

        validate_variant(subclass_id, rel, data, issues)
        validate_semantics(subclass_id, rel, data, issues)

    for path in markdown_paths:
        rel = path.relative_to(ROOT).as_posix()
        require(
            one_h1(path),
            f"{rel}: Markdown must have exactly one H1",
            issues,
        )

    roadmap_detail_debt = []
    for debt_key in ("yaml_debt", "markdown_debt"):
        for item in baseline.get(debt_key, []):
            if (
                isinstance(item, dict)
                and item.get("document_type") == "roadmap_detail"
            ):
                roadmap_detail_debt.append(
                    f"{debt_key}:{item.get('path')}"
                )

    require(
        not roadmap_detail_debt,
        "roadmap_detail debt remains: " + ",".join(roadmap_detail_debt),
        issues,
    )

    if PROJECTION_MD.is_file():
        projection_text = PROJECTION_MD.read_text(encoding="utf-8")
        require(
            f"Status: `{EXPECTED_PROJECTION_STATUS}`" in projection_text,
            "portfolio projection Markdown status is not synchronized",
            issues,
        )

    expected_current_counts = {
        "portfolio_rebuild_seed": 19,
        "continuity_prompt_sequence": 1,
        "continuity_snapshot": 1,
        "planning_template": 2,
        "specialized_planning_seed": 3,
        "knowledge_foundation_program": 1,
        "module_bootstrap_plan": 1,
        "roadmap_authority_rebuild_register": 1,
        "portfolio_target_projection": 1,
        "portfolio_rebuild_input": 1,
        "evening_architecture_action_matrix": 1,
    }

    for subclass_id, expected_count in expected_current_counts.items():
        require(
            subclass_counts.get(subclass_id) == expected_count,
            (
                f"subclass count drift:{subclass_id}:"
                f"expected={expected_count}:actual={subclass_counts.get(subclass_id, 0)}"
            ),
            issues,
        )

    if issues:
        print("ROADMAP_DETAIL_SURFACES=FAIL")
        for issue in issues:
            print(" - " + issue)
        return 1

    print("ROADMAP_DETAIL_SURFACES=PASS")
    print(f"YAML_COUNT={len(yaml_paths)}")
    print(f"MARKDOWN_COUNT={len(markdown_paths)}")
    print(f"STRICT_SUBCLASS_COUNT={len(subclass_counts)}")
    print("ROADMAP_DETAIL_BASELINE_DEBT_REMAINING=0")
    print("ORDINARY_MODULE_IMPLEMENTATION_ALLOWED=false")
    print("RELEASE_AUTHORITY_WIDENED=false")
    print("SUBCLASS_COUNTS=" + ",".join(
        f"{key}:{subclass_counts[key]}" for key in sorted(subclass_counts)
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
