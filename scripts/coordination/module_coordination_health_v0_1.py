from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.manage_outgoing_prompt import (
    ALLOWED_PREPARED_STATES,
    WorkflowError,
    _parse_artifact,
)
from scripts.coordination.module_roadmap import (
    load_yaml_file,
    resolve_roadmap_path,
    validate_roadmap_document,
)
from scripts.coordination.selection_policy_v0_1 import (
    priority_then_stable_id_key,
    roadmap_dependency_reasons,
)

ROOT = Path(__file__).resolve().parents[2]
HEALTH_POLICY = Path(
    "coordination/standards/governance/coordination_health_policy_v0_1.yaml"
)
PILOT_DECISION = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-08-21__blueprint__v0_4_1_logistics_pilot_scope_decision_v0_1.yaml"
)
OUTGOING_ROOT = Path("coordination/outgoing_prompts")

FUTURE_STATUSES = {"planned", "ready"}

ROADMAP_BELOW_MINIMUM = "ROADMAP_HORIZON_BELOW_MINIMUM"
ROADMAP_BELOW_TARGET = "ROADMAP_HORIZON_BELOW_TARGET"
PROMPT_BUFFER_BELOW_MINIMUM = "PROMPT_BUFFER_BELOW_MINIMUM"
PROMPT_BUFFER_BELOW_TARGET = "PROMPT_BUFFER_BELOW_TARGET"
PROMPT_BUFFER_INVALID_ARTIFACT = "PROMPT_BUFFER_INVALID_ARTIFACT"
PROMPT_BUFFER_MISSING_BINDING = "PROMPT_BUFFER_MISSING_BINDING"
PROMPT_BUFFER_UNKNOWN_STEP = "PROMPT_BUFFER_UNKNOWN_STEP"
PROMPT_BUFFER_NON_FUTURE_STEP = "PROMPT_BUFFER_NON_FUTURE_STEP"
PROMPT_BUFFER_DUPLICATE_STEP_BINDING = "PROMPT_BUFFER_DUPLICATE_STEP_BINDING"


class ModuleHealthError(RuntimeError):
    """Raised when module health cannot be evaluated safely."""


@dataclass(frozen=True)
class PreparedPromptObservation:
    path: str
    prompt_id: str | None
    roadmap_step_id: str | None
    priority: str | None
    valid_stock: bool
    issue: str | None


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ModuleHealthError(f"file does not exist: {path}") from exc
    except yaml.YAMLError as exc:
        raise ModuleHealthError(f"invalid YAML: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ModuleHealthError(f"YAML root must be mapping: {path}")
    return data


def _state(value: int, minimum: int, target: int) -> str:
    if value < minimum:
        return "below_minimum"
    if value < target:
        return "minimum_met_target_not_met"
    return "target_met"


def _pilot_scope(root: Path) -> tuple[str, dict[str, Any]]:
    data = _load_mapping(root / PILOT_DECISION)
    if data.get("result") != "LOGISTICS_ONLY_PILOT_SCOPE_ACTIVE":
        raise ModuleHealthError("pilot scope decision is not active")
    scope = data.get("pilot_scope")
    if not isinstance(scope, dict):
        raise ModuleHealthError("pilot_scope must be a mapping")
    module = scope.get("pilot_module")
    if not isinstance(module, str) or not module:
        raise ModuleHealthError("pilot_scope.pilot_module is invalid")
    return module, data


def _future_steps(
    *,
    module: str,
    steps: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    future = [
        step
        for step in steps
        if step.get("status") in FUTURE_STATUSES
    ]
    eligible = [
        step
        for step in future
        if not roadmap_dependency_reasons(
            roadmap_module=module,
            steps=steps,
            step=step,
        )
    ]
    return future, eligible


def _prepared_inventory(
    *,
    root: Path,
    module: str,
    future_steps: list[dict[str, Any]],
    all_steps: list[dict[str, Any]],
) -> tuple[list[PreparedPromptObservation], list[str]]:
    drafts_dir = root / OUTGOING_ROOT / module / "drafts"
    paths = (
        sorted(
            path
            for path in drafts_dir.glob("*.md")
            if path.name != ".gitkeep"
        )
        if drafts_dir.is_dir()
        else []
    )

    all_ids = {
        step.get("step_id")
        for step in all_steps
        if isinstance(step.get("step_id"), str)
    }
    future_ids = {
        step.get("step_id")
        for step in future_steps
        if isinstance(step.get("step_id"), str)
    }

    raw: list[PreparedPromptObservation] = []
    bound_counts: dict[str, int] = {}

    for path in paths:
        rel = str(path.relative_to(root))
        try:
            artifact = _parse_artifact(
                path.read_text(encoding="utf-8"),
                path=path,
                allowed_states=ALLOWED_PREPARED_STATES,
            )
        except (WorkflowError, UnicodeDecodeError):
            raw.append(
                PreparedPromptObservation(
                    path=rel,
                    prompt_id=None,
                    roadmap_step_id=None,
                    priority=None,
                    valid_stock=False,
                    issue=PROMPT_BUFFER_INVALID_ARTIFACT,
                )
            )
            continue

        step_id = artifact.roadmap_step_id
        issue: str | None = None
        if step_id is None:
            issue = PROMPT_BUFFER_MISSING_BINDING
        elif step_id not in all_ids:
            issue = PROMPT_BUFFER_UNKNOWN_STEP
        elif step_id not in future_ids:
            issue = PROMPT_BUFFER_NON_FUTURE_STEP

        if issue is None and step_id is not None:
            bound_counts[step_id] = bound_counts.get(step_id, 0) + 1

        raw.append(
            PreparedPromptObservation(
                path=rel,
                prompt_id=artifact.prompt_id,
                roadmap_step_id=step_id,
                priority=artifact.priority,
                valid_stock=issue is None,
                issue=issue,
            )
        )

    duplicate_ids = {
        step_id
        for step_id, count in bound_counts.items()
        if count > 1
    }

    final: list[PreparedPromptObservation] = []
    issues: set[str] = set()
    for item in raw:
        issue = item.issue
        valid = item.valid_stock
        if issue is None and item.roadmap_step_id in duplicate_ids:
            issue = PROMPT_BUFFER_DUPLICATE_STEP_BINDING
            valid = False
        if issue is not None:
            issues.add(issue)
        final.append(
            PreparedPromptObservation(
                path=item.path,
                prompt_id=item.prompt_id,
                roadmap_step_id=item.roadmap_step_id,
                priority=item.priority,
                valid_stock=valid,
                issue=issue,
            )
        )

    return final, sorted(issues)



def _refill_projection(
    *,
    module: str,
    steps: list[dict[str, Any]],
    future_steps: list[dict[str, Any]],
    valid_prepared: list[PreparedPromptObservation],
    minimum: int,
    target: int,
    integrity_issues: list[str],
    enforcement: bool,
) -> dict[str, Any]:
    prepared_step_ids = {
        item.roadmap_step_id
        for item in valid_prepared
        if item.roadmap_step_id is not None
    }

    eligible_now: list[dict[str, Any]] = []
    planning_only: list[tuple[dict[str, Any], list[str]]] = []

    for step in future_steps:
        step_id = step.get("step_id")
        if not isinstance(step_id, str) or step_id in prepared_step_ids:
            continue

        reasons = roadmap_dependency_reasons(
            roadmap_module=module,
            steps=steps,
            step=step,
        )
        if reasons:
            planning_only.append((step, reasons))
        else:
            eligible_now.append(step)

    eligible_now.sort(
        key=lambda item: priority_then_stable_id_key(
            item,
            id_field="step_id",
        )
    )
    planning_only.sort(
        key=lambda pair: (
            pair[0].get("sequence", 10**9),
            str(pair[0].get("step_id", "")),
        )
    )

    shortage_to_minimum = max(0, minimum - len(valid_prepared))
    shortage_to_target = max(0, target - len(valid_prepared))

    blocked_by_integrity = enforcement and bool(integrity_issues)
    proposal: list[dict[str, Any]] = []

    if not blocked_by_integrity:
        for step in eligible_now:
            proposal.append(step)
            if len(proposal) >= shortage_to_target:
                break

        if len(proposal) < shortage_to_target:
            for step, _ in planning_only:
                proposal.append(step)
                if len(proposal) >= shortage_to_target:
                    break

    recommendations: list[dict[str, Any]] = []
    for step in proposal:
        reasons = roadmap_dependency_reasons(
            roadmap_module=module,
            steps=steps,
            step=step,
        )
        recommendations.append(
            {
                "step_id": step.get("step_id"),
                "priority": step.get("priority"),
                "sequence": step.get("sequence"),
                "release_eligible_now": not reasons,
                "dependency_reasons": reasons,
            }
        )

    return {
        "state": (
            "blocked_by_buffer_integrity"
            if blocked_by_integrity
            else (
                "target_met"
                if shortage_to_target == 0
                else "refill_recommended"
            )
        ),
        "operator_action_required": (
            enforcement
            and not blocked_by_integrity
            and shortage_to_target > 0
        ),
        "shortage_to_minimum": shortage_to_minimum,
        "shortage_to_target": shortage_to_target,
        "candidate_capacity": len(eligible_now) + len(planning_only),
        "unfilled_target_shortage": max(
            0,
            shortage_to_target - len(recommendations),
        ),
        "recommendations": recommendations,
        "planning_basis": (
            "dependency_eligible_priority_first_then_future_roadmap_sequence"
        ),
        "execution_selection_performed": False,
        "automatic_prepare": False,
        "automatic_release": False,
    }


def _exit_code(report: dict[str, Any]) -> int:
    if report.get("pilot_enforcement") is True:
        codes = report.get("codes")
        if isinstance(codes, dict) and codes.get("errors"):
            return 2
    return 0

def evaluate_module_health(
    *,
    root: Path = ROOT,
    module: str,
) -> dict[str, Any]:
    root = root.resolve()

    pilot_module, pilot_data = _pilot_scope(root)
    enforcement = module == pilot_module

    roadmap_path = resolve_roadmap_path(root=root, module=module)
    roadmap = load_yaml_file(roadmap_path)
    validation = validate_roadmap_document(roadmap, path=roadmap_path)
    if validation.errors:
        raise ModuleHealthError(
            "roadmap is invalid:\n- " + "\n- ".join(validation.errors)
        )

    raw_steps = roadmap.get("roadmap")
    if not isinstance(raw_steps, list):
        raise ModuleHealthError("roadmap must be a list")
    steps = [step for step in raw_steps if isinstance(step, dict)]

    future, dependency_eligible = _future_steps(
        module=module,
        steps=steps,
    )

    prepared, buffer_issues = _prepared_inventory(
        root=root,
        module=module,
        future_steps=future,
        all_steps=steps,
    )
    valid_prepared = [item for item in prepared if item.valid_stock]

    policy = _load_mapping(root / HEALTH_POLICY)
    road_policy = policy.get("roadmap")
    prompt_policy = policy.get("prompt_buffer")
    if not isinstance(road_policy, dict) or not isinstance(prompt_policy, dict):
        raise ModuleHealthError("coordination health policy shape is invalid")

    road_min = int(road_policy["minimum_future_steps"])
    road_target = int(road_policy["target_future_steps"])
    prompt_min = int(prompt_policy["minimum_dispatchable_drafts"])
    prompt_target = int(prompt_policy["target_dispatchable_drafts"])

    warnings: list[str] = []
    advisories: list[str] = []
    errors: list[str] = []

    shortage_bucket = warnings if enforcement else advisories

    if len(future) < road_min:
        shortage_bucket.append(ROADMAP_BELOW_MINIMUM)
    elif len(future) < road_target:
        advisories.append(ROADMAP_BELOW_TARGET)

    if len(valid_prepared) < prompt_min:
        shortage_bucket.append(PROMPT_BUFFER_BELOW_MINIMUM)
    elif len(valid_prepared) < prompt_target:
        advisories.append(PROMPT_BUFFER_BELOW_TARGET)

    if enforcement:
        errors.extend(buffer_issues)
    else:
        advisories.extend(
            code for code in buffer_issues if code not in advisories
        )

    refill = _refill_projection(
        module=module,
        steps=steps,
        future_steps=future,
        valid_prepared=valid_prepared,
        minimum=prompt_min,
        target=prompt_target,
        integrity_issues=buffer_issues,
        enforcement=enforcement,
    )

    overall = "healthy"
    if errors:
        overall = "error"
    elif warnings:
        overall = "warning"
    elif advisories:
        overall = "advisory"

    return {
        "schema_version": "module_coordination_health_v0_1",
        "module": module,
        "pilot_module": pilot_module,
        "pilot_enforcement": enforcement,
        "mode": "local_read_only",
        "network_independent": True,
        "overall_state": overall,
        "roadmap": {
            "future_steps": len(future),
            "minimum_future_steps": road_min,
            "target_future_steps": road_target,
            "state": _state(len(future), road_min, road_target),
            "future_step_ids": [step.get("step_id") for step in future],
            "dependency_eligible_future_steps": len(dependency_eligible),
            "dependency_eligible_step_ids": [
                step.get("step_id") for step in dependency_eligible
            ],
            "dependency_eligibility_is_separate_from_horizon": True,
        },
        "prompt_buffer": {
            "prepared_artifacts_observed": len(prepared),
            "valid_prepared_prompts": len(valid_prepared),
            "minimum_dispatchable_drafts": prompt_min,
            "target_dispatchable_drafts": prompt_target,
            "state": _state(
                len(valid_prepared),
                prompt_min,
                prompt_target,
            ),
            "stock": [asdict(item) for item in prepared],
            "buffer_is_non_executable": True,
            "release_is_not_health_evaluation": True,
        },
        "operator_refill": refill,
        "codes": {
            "errors": sorted(set(errors)),
            "warnings": sorted(set(warnings)),
            "advisories": sorted(set(advisories)),
        },
        "policy": {
            "health_policy": str(HEALTH_POLICY),
            "pilot_decision": str(PILOT_DECISION),
            "pilot_result": pilot_data.get("result"),
        },
        "boundaries": {
            "automatic_prompt_prepare": False,
            "automatic_prompt_release": False,
            "automatic_accept": False,
            "automatic_return": False,
            "automatic_selection": False,
            "module_repository_writes": False,
            "network_required": False,
            "automatic_commit": False,
            "automatic_push": False,
        },
    }


def render_text(report: dict[str, Any]) -> str:
    road = report["roadmap"]
    buffer = report["prompt_buffer"]
    refill = report["operator_refill"]
    codes = report["codes"]

    lines = [
        "ForPrint Module Coordination Health v0.1",
        f"module: {report['module']}",
        f"pilot_module: {report['pilot_module']}",
        f"pilot_enforcement: {str(report['pilot_enforcement']).lower()}",
        f"overall: {report['overall_state']}",
        "",
        "ROADMAP",
        (
            f"future: {road['future_steps']} "
            f"(minimum={road['minimum_future_steps']}, "
            f"target={road['target_future_steps']})"
        ),
        f"state: {road['state']}",
        (
            "dependency_eligible_future: "
            f"{road['dependency_eligible_future_steps']}"
        ),
        "dependency_eligibility_is_separate_from_horizon: true",
        "",
        "PROMPT BUFFER",
        f"prepared_observed: {buffer['prepared_artifacts_observed']}",
        f"valid_prepared: {buffer['valid_prepared_prompts']}",
        (
            f"policy: minimum={buffer['minimum_dispatchable_drafts']}, "
            f"target={buffer['target_dispatchable_drafts']}"
        ),
        f"state: {buffer['state']}",
        "buffer_is_non_executable: true",
        "",
        "CODES",
        f"errors: {','.join(codes['errors']) or '-'}",
        f"warnings: {','.join(codes['warnings']) or '-'}",
        f"advisories: {','.join(codes['advisories']) or '-'}",
        "",
        "OPERATOR REFILL",
        f"state: {refill['state']}",
        (
            "operator_action_required: "
            f"{str(refill['operator_action_required']).lower()}"
        ),
        f"shortage_to_minimum: {refill['shortage_to_minimum']}",
        f"shortage_to_target: {refill['shortage_to_target']}",
        (
            "execution_selection_performed: "
            f"{str(refill['execution_selection_performed']).lower()}"
        ),
        "automatic_prepare: false",
        "automatic_release: false",
    ]

    for index, item in enumerate(refill["recommendations"], 1):
        lines.append(
            "refill: "
            f"{index}. step={item['step_id']} "
            f"priority={item['priority']} "
            "release_eligible_now="
            f"{str(item['release_eligible_now']).lower()}"
        )

    for item in buffer["stock"]:
        lines.append(
            "stock: "
            f"{item['prompt_id'] or '-'} "
            f"step={item['roadmap_step_id'] or '-'} "
            f"valid={str(item['valid_stock']).lower()} "
            f"issue={item['issue'] or '-'}"
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate per-module coordination buffer health read-only."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--module", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        report = evaluate_module_health(
            root=Path(args.root),
            module=args.module,
        )
    except ModuleHealthError as exc:
        print(f"RESULT: FAILED\nERROR: {exc}")
        return 1

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    return _exit_code(report)


if __name__ == "__main__":
    raise SystemExit(main())
