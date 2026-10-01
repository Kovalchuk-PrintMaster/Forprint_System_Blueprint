from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DEFAULT_HISTORY_LIMIT = 10
RUNTIME_STATES = {"ACTIVE", "STALLED", "TIMEOUT", "FINISHED", "UNKNOWN"}
UNKNOWN = "UNKNOWN"


def _display(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return UNKNOWN
    return " ".join(value.split())


def _runtime_state(value: Any) -> str:
    state = _display(value)
    return state if state in RUNTIME_STATES else UNKNOWN


def render_dashboard(
    projection: Mapping[str, Any],
    *,
    history_limit: int = DEFAULT_HISTORY_LIMIT,
) -> str:
    if (
        not isinstance(history_limit, int)
        or isinstance(history_limit, bool)
        or history_limit <= 0
    ):
        raise ValueError("history_limit must be a positive integer")

    attempts = projection.get("attempts")
    if not isinstance(attempts, list):
        attempts = []
    visible_attempts = attempts[-history_limit:]

    lines = [
        "CF-10 Worker dashboard",
        "Source: Task50 operator projection "
        "(scripts/coordination/control_plane/telegram_operator.py).",
        "Projection freshness: UNKNOWN (the source payload has no snapshot timestamp).",
        "Authority: derived, non-authoritative view; no execution, dispatch, "
        "ledger-mutation, approval, or acceptance authority.",
        (
            f"Attempts shown: up to {history_limit} final entries in Task50 "
            "projection order; recency is not independently verifiable."
        ),
    ]
    if not visible_attempts:
        lines.append("Attempt history: UNKNOWN (no attempt facts supplied).")
        return "\n".join(lines)

    for index, attempt in enumerate(visible_attempts, start=1):
        if not isinstance(attempt, Mapping):
            attempt = {}
        result_state = _display(attempt.get("result_state"))
        lines.extend(
            (
                f"Attempt {index}:",
                f"  attempt_id: {_display(attempt.get('attempt_id'))}",
                f"  attempt_stage: {_display(attempt.get('attempt_stage'))}",
                f"  result_state: {result_state}",
                f"  outcome: {result_state}",
                f"  derived_state: {_runtime_state(attempt.get('state'))}",
                f"  reason: {_display(attempt.get('reason'))}",
            )
        )
    return "\n".join(lines)
