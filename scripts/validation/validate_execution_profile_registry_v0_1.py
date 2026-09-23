from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import yaml

PROFILE_IDS = {
    "deep-readonly-analysis",
    "deep-dev",
    "standard-dev",
    "light-maintenance",
}


def load_runtime(root: Path):
    source = root / "scripts/coordination/execution_profiles_v0_1.py"
    spec = importlib.util.spec_from_file_location(
        "_execution_profiles_validator_runtime",
        source,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("execution profile runtime import spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fail(reason: str) -> int:
    print("EXECUTION_PROFILE_REGISTRY_VALIDATION=FAIL")
    print("REASON=" + reason)
    return 1


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(root: Path, *, contract_only: bool = False) -> int:
    try:
        runtime = load_runtime(root)
        contract = runtime.load_contract(root)
        registry = runtime.load_registry(root)

        ids = {
            row.get("profile_id") for row in registry.get("profiles", []) if isinstance(row, dict)
        }
        if ids != PROFILE_IDS:
            return fail("INITIAL_PROFILE_IDS")

        refs = set(runtime.list_profile_refs(root))
        if refs != {f"{profile_id}@r1" for profile_id in PROFILE_IDS}:
            return fail("INITIAL_PROFILE_REFS")

        for row in registry["profiles"]:
            reasoning = row["reasoning_policy"]
            if reasoning.get("backend") != "replaceable":
                return fail("MODEL_BACKEND_NOT_REPLACEABLE")
            if any(key in reasoning for key in ("provider", "model", "model_id")):
                return fail("CANONICAL_MODEL_PROVIDER_BINDING")
            capabilities = set(row["authority_policy"]["capability_ceiling"])
            if capabilities & {"dispatch", "release", "foreign_repository_write"}:
                return fail("PROFILE_AUTHORITY_WIDENING")

        readonly = runtime.get_profile(
            root,
            "deep-readonly-analysis@r1",
        )
        if set(readonly["authority_policy"]["capability_ceiling"]) != {"read"}:
            return fail("READONLY_PROFILE_WRITABLE")

        resolution = runtime.resolve_profile(
            root,
            "deep-dev@r1",
            higher_authority_permissions={"read"},
            higher_budget_tier="STANDARD",
            work_front_permissions={"read", "write_blueprint"},
            work_front_budget_tier="HIGH",
        )
        if resolution["effective_authority_permissions"] != ["read"]:
            return fail("AUTHORITY_INTERSECTION")
        if resolution["effective_budget_tier"] != "STANDARD":
            return fail("BUDGET_MINIMUM")
        if any(
            resolution[key] is not False
            for key in (
                "dispatch_authority",
                "release_authority",
                "foreign_repository_write_authority",
            )
        ):
            return fail("RESOLUTION_GRANTED_FORBIDDEN_AUTHORITY")

        recommendation = runtime.recommend_profile(
            root,
            mutation_expected=True,
            complexity="DEEP",
        )
        if recommendation.get("recommended_profile_ref") != "deep-dev@r1":
            return fail("RECOMMENDATION")
        if recommendation.get("dispatch_authority") is not False:
            return fail("RECOMMENDATION_DISPATCH_AUTHORITY")

        try:
            runtime.select_profile(
                root,
                "light-maintenance@r1",
                operator_override_ref="deep-dev@r1",
            )
        except runtime.ExecutionProfileError:
            pass
        else:
            return fail("WIDENING_OVERRIDE_LACKS_ESCALATION_GATE")

        override = runtime.select_profile(
            root,
            "light-maintenance@r1",
            operator_override_ref="deep-dev@r1",
            escalation_evidence="operator:test-explicit-escalation",
        )
        if override.get("dispatch_authority") is not False:
            return fail("OVERRIDE_DISPATCH_AUTHORITY")

        if contract["selection"]["override_never_bypasses_higher_authority"] is not True:
            return fail("OVERRIDE_HIGHER_AUTHORITY_BOUNDARY")
    except Exception as exc:
        return fail(type(exc).__name__ + ":" + str(exc))

    print("EXECUTION_PROFILE_REGISTRY_CONTRACT=PASS")
    print("INITIAL_PROFILE_COUNT=4")
    print("MODEL_BACKEND_REPLACEABLE=true")
    print("PROFILE_PERMISSIONS_ARE_CEILING_NOT_GRANT=true")
    print("EFFECTIVE_AUTHORITY_IS_INTERSECTION=true")
    print("EFFECTIVE_BUDGET_IS_MOST_RESTRICTIVE_TIER=true")
    print("DISPATCHER_RECOMMENDATION_IS_AUTHORITY=false")
    print("HIGHER_BUDGET_OR_AUTHORITY_REQUIRES_ESCALATION=true")
    if contract_only:
        print("EXECUTION_PROFILE_REGISTRY_VALIDATION=PASS")
        return 0

    constitution = load_yaml(
        root / "coordination/standards/governance/project_constitution_v0_1.yaml"
    )
    if not isinstance(constitution, dict):
        return fail("PROJECT_CONSTITUTION")
    hierarchy = constitution.get("authority_precedence")
    if not isinstance(hierarchy, dict):
        return fail("PROJECT_CONSTITUTION_AUTHORITY_PRECEDENCE")
    if hierarchy.get("order") != [
        "PROJECT_CONSTITUTION",
        "MODULE_POLICY",
        "EXECUTION_PROFILE",
        "WORK_FRONT",
    ]:
        return fail("PROJECT_CONSTITUTION_PRECEDENCE")
    if hierarchy.get("lower_layer_may_narrow") is not True:
        return fail("PROJECT_CONSTITUTION_NARROWING")
    if hierarchy.get("lower_layer_may_widen_without_explicit_gate") is not False:
        return fail("PROJECT_CONSTITUTION_WIDENING")

    work_front = load_yaml(root / "coordination/standards/automation/work_front_contract_v0_1.yaml")
    if not isinstance(work_front, dict):
        return fail("WORK_FRONT_CONTRACT")
    scope = work_front.get("scope_exclusions")
    if not isinstance(scope, dict) or scope.get("execution_profiles") != "CF-06":
        return fail("WORK_FRONT_CF06_BINDING")

    attempt = load_yaml(
        root / "coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml"
    )
    if not isinstance(attempt, dict):
        return fail("ATTEMPT_LEDGER_CONTRACT")
    schema = attempt.get("record_schema")
    if not isinstance(schema, dict):
        return fail("ATTEMPT_LEDGER_SCHEMA")
    fields = set(schema.get("required_fields") or [])
    if "profile_ref_or_revision" not in fields:
        return fail("ATTEMPT_PROFILE_REF_FIELD")

    standards = load_yaml(root / "coordination/standards/index.yaml")
    rows = standards.get("standards") if isinstance(standards, dict) else None
    if not isinstance(rows, list):
        return fail("STANDARDS_INDEX")
    matches = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("file") == "automation/execution_profile_registry_contract_v0_1.yaml"
    ]
    if len(matches) != 1:
        return fail("STANDARDS_REGISTRATION")

    makefile = (root / "Makefile").read_text(encoding="utf-8")
    if ".PHONY: execution-profile-registry-check" not in makefile:
        return fail("MAKE_TARGET")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")),
        "",
    )
    if "execution-profile-registry-check" not in check_core.split():
        return fail("CHECK_CORE_BINDING")

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    if "<!-- FORPRINT_EXECUTION_PROFILE_REGISTRY_START -->" not in agents:
        return fail("AGENTS_BINDING")

    print("PROFILE_REVISION_RECORDABLE_IN_ATTEMPT_LEDGER=true")
    print("WORK_FRONT_EXECUTION_AUTHORITY_PRESERVED=true")
    print("CF07_IMPLEMENTED=false")
    print("WORKER_DISPATCH_AUTHORITY=false")
    print("EXECUTION_PROFILE_REGISTRY_VALIDATION=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()
    return validate(
        Path(args.root).resolve(),
        contract_only=args.contract_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())
