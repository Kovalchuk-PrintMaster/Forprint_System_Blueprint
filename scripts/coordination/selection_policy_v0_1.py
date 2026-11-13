from __future__ import annotations

from typing import Any

DEFAULT_SELECTION_SOURCE = "dependency_eligibility_priority_stable_id"
EXPLICIT_OVERRIDE_SOURCE = "explicit_validated_override"
LEGACY_SELECTION_SOURCES = {"deterministic_queue_order"}

PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
    "reference": 4,
}

DEPENDENCY_SATISFIED_STATUSES = {
    "module_step": {"completed", "accepted"},
    "prompt": {"completed", "accepted", "accepted_by_blueprint"},
    "document": {"acknowledged", "completed", "accepted"},
    "contract": {"completed", "accepted"},
    "external_decision": {"completed", "accepted", "resolved"},
    "manual_review": {"completed", "accepted", "resolved"},
}


class SelectionPolicyError(ValueError):
    """Raised when canonical next-work selection metadata is invalid."""


def priority_rank(value: Any) -> int:
    priority = str(value or "").strip().lower()
    if priority not in PRIORITY_ORDER:
        raise SelectionPolicyError(
            f"unsupported canonical priority: {value!r}"
        )
    return PRIORITY_ORDER[priority]


def priority_then_stable_id_key(
    record: dict[str, Any],
    *,
    id_field: str,
) -> tuple[int, str]:
    stable_id = record.get(id_field)
    if not isinstance(stable_id, str) or not stable_id:
        raise SelectionPolicyError(
            f"{id_field} must be a non-empty stable id"
        )
    return (
        priority_rank(record.get("priority")),
        stable_id,
    )


def roadmap_dependency_reasons(
    *,
    roadmap_module: str,
    steps: list[dict[str, Any]],
    step: dict[str, Any],
) -> list[str]:
    """Return fail-closed dependency reasons for one roadmap step."""

    by_id = {
        item.get("step_id"): item
        for item in steps
        if isinstance(item, dict)
        and isinstance(item.get("step_id"), str)
    }
    reasons: list[str] = []

    for dependency in step.get("depends_on") or []:
        if isinstance(dependency, str):
            target = by_id.get(dependency)
            if not isinstance(target, dict):
                reasons.append(f"UNKNOWN_LOCAL_DEPENDENCY:{dependency}")
                continue
            if (
                target.get("status")
                not in DEPENDENCY_SATISFIED_STATUSES["module_step"]
            ):
                reasons.append(
                    f"LOCAL_DEPENDENCY_NOT_DONE:{dependency}"
                )
            continue

        if not isinstance(dependency, dict):
            reasons.append("INVALID_DEPENDENCY_RECORD")
            continue

        dependency_type = dependency.get("type")
        if not isinstance(dependency_type, str) or not dependency_type:
            if isinstance(dependency.get("step_id"), str):
                dependency_type = "module_step"
            else:
                reasons.append("DEPENDENCY_TYPE_MISSING")
                continue

        satisfied_statuses = DEPENDENCY_SATISFIED_STATUSES.get(
            dependency_type
        )
        if satisfied_statuses is None:
            reasons.append(
                f"UNSUPPORTED_DEPENDENCY_TYPE:{dependency_type}"
            )
            continue

        snapshot_status = dependency.get("status")

        if dependency_type == "module_step":
            dependency_id = dependency.get("step_id")
            if not isinstance(dependency_id, str) or not dependency_id:
                reasons.append("MODULE_STEP_ID_MISSING")
                continue

            dependency_module = dependency.get("module")
            if dependency_module is None:
                dependency_module = roadmap_module

            if dependency_module == roadmap_module:
                target = by_id.get(dependency_id)
                if not isinstance(target, dict):
                    reasons.append(
                        f"UNKNOWN_LOCAL_DEPENDENCY:{dependency_id}"
                    )
                    continue
                if target.get("status") not in satisfied_statuses:
                    reasons.append(
                        f"LOCAL_DEPENDENCY_NOT_DONE:{dependency_id}"
                    )
                continue

            if snapshot_status not in satisfied_statuses:
                reasons.append(
                    "CROSS_MODULE_DEPENDENCY_NOT_DONE:"
                    f"{dependency_module}:{dependency_id}"
                )
            continue

        if snapshot_status not in satisfied_statuses:
            reference = (
                dependency.get("reference")
                or dependency.get("prompt_id")
                or dependency.get("contract_id")
                or dependency.get("decision_id")
                or dependency.get("review_id")
                or "unknown"
            )
            reasons.append(
                f"{dependency_type.upper()}_DEPENDENCY_NOT_SATISFIED:"
                f"{reference}"
            )

    return reasons
