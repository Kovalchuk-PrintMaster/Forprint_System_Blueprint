from __future__ import annotations

import argparse
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

CONTRACT_REL = Path(
    "coordination/standards/automation/execution_profile_registry_contract_v0_1.yaml"
)
REGISTRY_REL = Path("coordination/registry/execution_profiles_v0_1.yaml")
PROFILE_REF_RE = re.compile(r"^(?P<profile>[a-z0-9][a-z0-9-]{1,79})@(?P<revision>r[1-9][0-9]*)$")
BUDGET_RANK = {"LIGHT": 0, "STANDARD": 1, "HIGH": 2}


class ExecutionProfileError(RuntimeError):
    pass


def load_contract(root: Path) -> dict[str, Any]:
    value = yaml.safe_load((root / CONTRACT_REL).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExecutionProfileError("contract root must be a mapping")
    validate_contract(value)
    return value


def load_registry(root: Path) -> dict[str, Any]:
    value = yaml.safe_load((root / REGISTRY_REL).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExecutionProfileError("registry root must be a mapping")
    validate_registry(value, load_contract(root))
    return value


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "forprint_execution_profile_registry_contract_v0_1":
        raise ExecutionProfileError("unexpected contract schema")

    precedence = contract.get("authority_precedence")
    if not isinstance(precedence, dict):
        raise ExecutionProfileError("authority_precedence missing")
    if precedence.get("order") != [
        "PROJECT_CONSTITUTION",
        "MODULE_POLICY",
        "EXECUTION_PROFILE",
        "WORK_FRONT",
    ]:
        raise ExecutionProfileError("authority precedence order mismatch")
    if precedence.get("lower_layer_may_narrow") is not True:
        raise ExecutionProfileError("narrowing rule missing")
    if precedence.get("lower_layer_may_silently_widen") is not False:
        raise ExecutionProfileError("silent widening must be false")
    if precedence.get("effective_authority_is_intersection") is not True:
        raise ExecutionProfileError("authority intersection rule missing")
    if precedence.get("profile_permissions_are_ceiling_not_grant") is not True:
        raise ExecutionProfileError("profile ceiling semantics missing")

    reasoning = contract.get("reasoning_policy")
    if not isinstance(reasoning, dict):
        raise ExecutionProfileError("reasoning_policy missing")
    if reasoning.get("backend_replaceable") is not True:
        raise ExecutionProfileError("model backend must remain replaceable")
    if reasoning.get("provider_or_model_identity_in_canonical_profile") != "forbidden":
        raise ExecutionProfileError("provider/model identity must be forbidden")

    selection = contract.get("selection")
    if not isinstance(selection, dict):
        raise ExecutionProfileError("selection missing")
    if selection.get("dispatcher_recommendation_is_dispatch_authority") is not False:
        raise ExecutionProfileError("recommendation cannot be dispatch authority")
    if selection.get("override_never_bypasses_higher_authority") is not True:
        raise ExecutionProfileError("override higher-authority boundary missing")


def _strings(value: Any, *, non_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not non_empty)
        and all(isinstance(item, str) and bool(item) for item in value)
    )


def validate_registry(
    registry: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    expected_registry_schema = contract["registry"]["registry_schema_version"]
    expected_profile_schema = contract["registry"]["profile_schema_version"]
    if registry.get("schema_version") != expected_registry_schema:
        raise ExecutionProfileError("registry schema mismatch")

    profiles = registry.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ExecutionProfileError("profiles must be a non-empty list")

    seen: set[tuple[str, str]] = set()
    allowed_reasoning = set(contract["reasoning_policy"]["abstract_tiers"])
    allowed_budget = set(contract["budget_policy"]["abstract_tiers"])
    allowed_context = set(contract["context_policy"]["abstract_tiers"])
    known_caps = set(contract["authority_policy"]["known_profile_capabilities"])
    forbidden_caps = set(contract["authority_policy"]["forbidden_profile_capabilities"])

    for profile in profiles:
        if not isinstance(profile, dict):
            raise ExecutionProfileError("profile must be a mapping")
        if profile.get("schema_version") != expected_profile_schema:
            raise ExecutionProfileError("profile schema mismatch")

        profile_id = profile.get("profile_id")
        revision = profile.get("revision")
        if not isinstance(profile_id, str) or not isinstance(revision, str):
            raise ExecutionProfileError("profile identity missing")
        ref = f"{profile_id}@{revision}"
        if PROFILE_REF_RE.fullmatch(ref) is None:
            raise ExecutionProfileError(f"invalid profile ref: {ref}")
        key = (profile_id, revision)
        if key in seen:
            raise ExecutionProfileError(f"duplicate profile revision: {ref}")
        seen.add(key)

        reasoning = profile.get("reasoning_policy")
        authority = profile.get("authority_policy")
        budget = profile.get("budget_policy")
        context = profile.get("context_policy")
        selection = profile.get("selection")
        if not all(
            isinstance(value, dict) for value in (reasoning, authority, budget, context, selection)
        ):
            raise ExecutionProfileError(f"incomplete composition: {ref}")

        if reasoning.get("tier") not in allowed_reasoning:
            raise ExecutionProfileError(f"invalid reasoning tier: {ref}")
        if reasoning.get("backend") != "replaceable":
            raise ExecutionProfileError(f"backend must be replaceable: {ref}")
        if any(key in reasoning for key in ("provider", "model", "model_id")):
            raise ExecutionProfileError(f"provider/model binding forbidden: {ref}")

        caps = authority.get("capability_ceiling")
        if not _strings(caps, non_empty=True):
            raise ExecutionProfileError(f"capability_ceiling invalid: {ref}")
        cap_set = set(caps)
        if not cap_set <= known_caps:
            raise ExecutionProfileError(f"unknown capability in profile: {ref}")
        if cap_set & forbidden_caps:
            raise ExecutionProfileError(f"forbidden authority capability: {ref}")

        if budget.get("tier") not in allowed_budget:
            raise ExecutionProfileError(f"invalid budget tier: {ref}")
        if context.get("tier") not in allowed_context:
            raise ExecutionProfileError(f"invalid context tier: {ref}")
        if context.get("fresh_context_required") is not True:
            raise ExecutionProfileError(f"fresh context must be required: {ref}")
        if context.get("raw_chat_is_authority") is not False:
            raise ExecutionProfileError(f"raw chat cannot be authority: {ref}")
        if selection.get("dispatcher_recommendable") is not True:
            raise ExecutionProfileError(f"profile not recommendable: {ref}")
        if selection.get("operator_override_supported") is not True:
            raise ExecutionProfileError(f"operator override not supported: {ref}")
        if not _strings(selection.get("recommendation_tags"), non_empty=True):
            raise ExecutionProfileError(f"recommendation tags invalid: {ref}")


def profile_ref(profile: dict[str, Any]) -> str:
    return f"{profile['profile_id']}@{profile['revision']}"


def parse_profile_ref(value: str) -> tuple[str, str]:
    match = PROFILE_REF_RE.fullmatch(value)
    if match is None:
        raise ExecutionProfileError(f"invalid profile reference: {value}")
    return match.group("profile"), match.group("revision")


def get_profile(
    root: Path,
    ref: str,
) -> dict[str, Any]:
    profile_id, revision = parse_profile_ref(ref)
    registry = load_registry(root)
    matches = [
        row
        for row in registry["profiles"]
        if row.get("profile_id") == profile_id and row.get("revision") == revision
    ]
    if len(matches) != 1:
        raise ExecutionProfileError(f"profile ref not found: {ref}")
    return deepcopy(matches[0])


def list_profile_refs(root: Path) -> list[str]:
    registry = load_registry(root)
    return [profile_ref(row) for row in registry["profiles"]]


def _budget_min(*tiers: str) -> str:
    unknown = [tier for tier in tiers if tier not in BUDGET_RANK]
    if unknown:
        raise ExecutionProfileError(f"unknown budget tier: {unknown[0]}")
    return min(tiers, key=lambda tier: BUDGET_RANK[tier])


def resolve_profile(
    root: Path,
    ref: str,
    *,
    higher_authority_permissions: set[str],
    higher_budget_tier: str,
    work_front_permissions: set[str] | None = None,
    work_front_budget_tier: str | None = None,
) -> dict[str, Any]:
    profile = get_profile(root, ref)
    contract = load_contract(root)

    forbidden = set(contract["authority_policy"]["forbidden_profile_capabilities"])
    profile_ceiling = set(profile["authority_policy"]["capability_ceiling"])
    if higher_authority_permissions & forbidden:
        # Higher authority may contain capabilities that this profile layer is
        # never allowed to confer. They are deliberately removed by intersection.
        pass

    effective = set(higher_authority_permissions) & profile_ceiling
    if work_front_permissions is not None:
        effective &= set(work_front_permissions)

    budget_inputs = [
        higher_budget_tier,
        profile["budget_policy"]["tier"],
    ]
    if work_front_budget_tier is not None:
        budget_inputs.append(work_front_budget_tier)
    effective_budget = _budget_min(*budget_inputs)

    return {
        "profile_ref_or_revision": profile_ref(profile),
        "reasoning_policy": deepcopy(profile["reasoning_policy"]),
        "effective_authority_permissions": sorted(effective),
        "effective_budget_tier": effective_budget,
        "context_policy": deepcopy(profile["context_policy"]),
        "dispatch_authority": False,
        "release_authority": False,
        "foreign_repository_write_authority": False,
    }


def _is_wider_profile(
    recommended: dict[str, Any],
    override: dict[str, Any],
) -> bool:
    rec_caps = set(recommended["authority_policy"]["capability_ceiling"])
    over_caps = set(override["authority_policy"]["capability_ceiling"])
    authority_wider = not over_caps <= rec_caps
    budget_wider = (
        BUDGET_RANK[override["budget_policy"]["tier"]]
        > BUDGET_RANK[recommended["budget_policy"]["tier"]]
    )
    return authority_wider or budget_wider


def select_profile(
    root: Path,
    recommended_ref: str,
    *,
    operator_override_ref: str | None = None,
    escalation_evidence: str | None = None,
) -> dict[str, Any]:
    recommended = get_profile(root, recommended_ref)
    selected = recommended
    basis = "DISPATCHER_RECOMMENDATION"

    if operator_override_ref is not None:
        override = get_profile(root, operator_override_ref)
        if _is_wider_profile(recommended, override):
            if not isinstance(escalation_evidence, str) or not escalation_evidence.strip():
                raise ExecutionProfileError(
                    "operator override widens authority or budget; "
                    "explicit escalation evidence required"
                )
            basis = "OPERATOR_OVERRIDE_WITH_ESCALATION_EVIDENCE"
        else:
            basis = "OPERATOR_OVERRIDE_NON_WIDENING"
        selected = override

    return {
        "recommended_profile_ref": profile_ref(recommended),
        "selected_profile_ref": profile_ref(selected),
        "selection_basis": basis,
        "dispatch_authority": False,
    }


def recommend_profile(
    root: Path,
    *,
    mutation_expected: bool,
    complexity: str,
    maintenance: bool = False,
) -> dict[str, Any]:
    complexity = complexity.upper()
    if complexity not in {"DEEP", "STANDARD", "LIGHT"}:
        raise ExecutionProfileError("complexity must be DEEP, STANDARD or LIGHT")

    if not mutation_expected:
        ref = "deep-readonly-analysis@r1"
    elif maintenance and complexity == "LIGHT":
        ref = "light-maintenance@r1"
    elif complexity == "DEEP":
        ref = "deep-dev@r1"
    else:
        ref = "standard-dev@r1"

    get_profile(root, ref)
    return {
        "recommended_profile_ref": ref,
        "recommendation_only": True,
        "dispatch_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")

    show = sub.add_parser("show")
    show.add_argument("--profile", required=True)

    resolve = sub.add_parser("resolve")
    resolve.add_argument("--profile", required=True)
    resolve.add_argument("--higher-permission", action="append", default=[])
    resolve.add_argument("--higher-budget", required=True)
    resolve.add_argument("--front-permission", action="append")
    resolve.add_argument("--front-budget")

    recommend = sub.add_parser("recommend")
    recommend.add_argument("--mutation-expected", action="store_true")
    recommend.add_argument(
        "--complexity",
        required=True,
        choices=["DEEP", "STANDARD", "LIGHT"],
    )
    recommend.add_argument("--maintenance", action="store_true")

    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "list":
        for ref in list_profile_refs(root):
            print(ref)
        return 0

    if args.command == "show":
        print(
            yaml.safe_dump(
                get_profile(root, args.profile),
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )
        return 0

    if args.command == "resolve":
        result = resolve_profile(
            root,
            args.profile,
            higher_authority_permissions=set(args.higher_permission),
            higher_budget_tier=args.higher_budget,
            work_front_permissions=(
                set(args.front_permission) if args.front_permission is not None else None
            ),
            work_front_budget_tier=args.front_budget,
        )
        print(
            yaml.safe_dump(
                result,
                sort_keys=False,
                allow_unicode=True,
            ).rstrip()
        )
        return 0

    result = recommend_profile(
        root,
        mutation_expected=args.mutation_expected,
        complexity=args.complexity,
        maintenance=args.maintenance,
    )
    print(
        yaml.safe_dump(
            result,
            sort_keys=False,
            allow_unicode=True,
        ).rstrip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
