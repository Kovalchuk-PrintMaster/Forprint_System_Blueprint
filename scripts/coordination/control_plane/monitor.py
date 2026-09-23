from __future__ import annotations

from typing import Any

MONITOR_SCHEMA = "forprint_execution_monitor_projection_v0_1"


def _nested(data: dict[str, Any], *keys: str) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def build_monitor_projection(
    *,
    launch_request: dict[str, Any],
    worker_invocation: dict[str, Any],
    dispatch_intent: dict[str, Any],
    approval_decision: dict[str, Any] | None = None,
    observed_event_count: int = 0,
) -> dict[str, Any]:
    launch_state = launch_request.get("state")
    dispatch_state = dispatch_intent.get("state")
    reasons: list[str] = []
    if launch_state == "BLOCKED":
        codes = {
            x.get("code")
            for x in (_nested(launch_request, "eligibility", "blockers") or [])
            if isinstance(x, dict)
        }
        reasons.append(
            "dependency_blocked"
            if "DEPENDENCY_READINESS_NOT_PROVIDED" in codes
            else "execution_blocked"
        )
    elif launch_state == "AWAITING_OPERATOR_APPROVAL" and approval_decision is None:
        reasons.append("operator_acceptance_required")
    elif dispatch_state == "BLOCKED":
        reasons.append("execution_blocked")
    state = (
        "DISPATCH_INTENT_READY" if dispatch_state == "READY_FOR_EXPLICIT_DISPATCH" else "BLOCKED"
    )
    return {
        "schema_version": MONITOR_SCHEMA,
        "identity": {
            "module_id": _nested(launch_request, "identity", "module_id"),
            "prompt_id": _nested(launch_request, "identity", "prompt_id"),
        },
        "state": state,
        "source_states": {
            "launch_request": launch_state,
            "operator_approval": "PRESENT" if approval_decision is not None else "NOT_APPROVED",
            "worker_invocation": worker_invocation.get("state"),
            "dispatch_intent": dispatch_state,
            "worker_execution": "NOT_STARTED",
        },
        "observability": {
            "observed_q5_event_count": observed_event_count,
            "runtime_duration": "not_observable",
            "resource_usage": "not_observable",
            "worker_heartbeat": "not_observable",
        },
        "operator_attention": {
            "required": bool(reasons),
            "reasons": sorted(set(reasons)),
            "attention_is_authority": False,
        },
        "semantic_boundaries": {
            "monitor_is_source_of_truth": False,
            "monitor_may_blueprint_accept": False,
            "monitor_may_release_next_prompt": False,
            "semantic_acceptance_owner": "INSPECTOR_AND_HUMAN_GATE",
        },
    }
