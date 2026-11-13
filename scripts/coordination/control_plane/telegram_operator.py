from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECTION_SCHEMA = "forprint_local_operator_projection_v0_1"
TERMINAL_RESULT_STATES = {"SUCCEEDED", "FAILED", "BLOCKED", "PARTIAL", "CANCELLED"}
TERMINAL_ATTEMPT_STAGES = {"FINISHED", "FAILED", "BLOCKED", "INTERRUPTED"}


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _as_now(value: datetime | str | None) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return None
        return value.astimezone(UTC)
    return _timestamp(value)


def _is_ledger_terminal(record: Mapping[str, Any]) -> bool:
    return (
        record.get("result_state") in TERMINAL_RESULT_STATES
        or record.get("attempt_stage") in TERMINAL_ATTEMPT_STAGES
    )


def _classify(
    record: Mapping[str, Any],
    evidence: Mapping[str, Any] | None,
    *,
    now: datetime | None,
    max_evidence_age: timedelta,
) -> tuple[str, str]:
    evidence = evidence or {}
    process_alive = evidence.get("process_alive")
    timed_out = (
        evidence.get("timed_out") is True
        or evidence.get("outcome") == "timeout"
    )
    timeout_flag = evidence.get("timed_out")
    outcome = evidence.get("outcome")
    if (
        isinstance(timeout_flag, bool)
        and isinstance(outcome, str)
        and (timeout_flag != (outcome == "timeout"))
    ):
        return "UNKNOWN", "contradictory_timeout_facts"
    finished_at = _timestamp(evidence.get("finished_at"))
    process_completed = (
        finished_at is not None
        and evidence.get("process_started") is True
        and isinstance(evidence.get("return_code"), int)
        and not isinstance(evidence.get("return_code"), bool)
    )
    finished = (
        process_completed
        and evidence.get("timed_out") is False
    )
    if timed_out:
        if process_alive is True or not process_completed:
            return "UNKNOWN", "contradictory_runtime_facts"
        return "TIMEOUT", "explicit_timeout_evidence"

    if finished:
        if process_alive is True:
            return "UNKNOWN", "contradictory_runtime_facts"
        if _is_ledger_terminal(record):
            return "FINISHED", "ledger_and_completion_evidence"
        return "FINISHED", "final_completion_evidence"

    if process_alive is True:
        observed_at = _timestamp(evidence.get("observed_at"))
        if (
            observed_at is None
            or now is None
            or observed_at > now
            or now - observed_at > max_evidence_age
        ):
            return "UNKNOWN", "live_evidence_missing_or_stale"
        if _is_ledger_terminal(record) or finished:
            return "UNKNOWN", "contradictory_attempt_and_runtime_facts"
        if evidence.get("stall_detected") is True:
            return "STALLED", "fresh_stall_evidence"
        if evidence.get("stall_detected") is False:
            return "ACTIVE", "fresh_live_process_evidence"
        return "UNKNOWN", "progress_evidence_insufficient"

    if _is_ledger_terminal(record):
        return "FINISHED", "terminal_ledger_fact"
    return "UNKNOWN", "live_evidence_missing_or_insufficient"


def build_operator_projection(
    *,
    attempt_records: Sequence[Mapping[str, Any]],
    watchdog_evidence: Mapping[str, Mapping[str, Any]] | None = None,
    now: datetime | str | None = None,
    max_evidence_age_seconds: int = 60,
) -> dict[str, Any]:
    if (
        not isinstance(max_evidence_age_seconds, int)
        or isinstance(max_evidence_age_seconds, bool)
        or max_evidence_age_seconds <= 0
    ):
        raise ValueError("max_evidence_age_seconds must be a positive integer")

    evidence_by_attempt = watchdog_evidence or {}
    reference_time = _as_now(now)
    freshness_window = timedelta(seconds=max_evidence_age_seconds)
    attempts: list[dict[str, Any]] = []
    for record in sorted(
        attempt_records,
        key=lambda item: str(item.get("attempt_id", "")),
    ):
        attempt_id = record.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            raise ValueError("each ledger fact must include a non-empty attempt_id")
        evidence = evidence_by_attempt.get(attempt_id)
        if evidence is not None and not isinstance(evidence, Mapping):
            raise ValueError("watchdog evidence must be a mapping")
        state, reason = _classify(
            record,
            evidence,
            now=reference_time,
            max_evidence_age=freshness_window,
        )
        attempts.append(
            {
                "attempt_id": attempt_id,
                "attempt_stage": record.get("attempt_stage"),
                "result_state": record.get("result_state"),
                "state": state,
                "reason": reason,
            }
        )

    return {
        "schema_version": PROJECTION_SCHEMA,
        "attempts": attempts,
        "authority": {
            "projection_authority": False,
            "execution_authority": False,
            "dispatch_authority": False,
            "ledger_mutation_authority": False,
            "telegram_transport_authority": False,
        },
    }


def build_projection_from_ledger(
    *,
    root: Path,
    work_front_id: str | None = None,
    store_override: Path | None = None,
    watchdog_evidence: Mapping[str, Mapping[str, Any]] | None = None,
    now: datetime | str | None = None,
    max_evidence_age_seconds: int = 60,
) -> dict[str, Any]:
    from scripts.coordination.execution_attempt_ledger_v0_1 import (
        load_contract,
        latest_attempt_records,
        store_root,
    )

    contract = load_contract(root)
    records = latest_attempt_records(
        store_root(root, contract, store_override),
        work_front_id=work_front_id,
    )
    return build_operator_projection(
        attempt_records=records,
        watchdog_evidence=watchdog_evidence,
        now=now,
        max_evidence_age_seconds=max_evidence_age_seconds,
    )


def render_telegram_text(projection: Mapping[str, Any]) -> str:
    attempts = projection.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return "Worker status: UNKNOWN"
    lines = []
    for index, attempt in enumerate(attempts, start=1):
        state = attempt.get("state") if isinstance(attempt, Mapping) else None
        if state not in {"ACTIVE", "STALLED", "TIMEOUT", "FINISHED", "UNKNOWN"}:
            state = "UNKNOWN"
        lines.append(f"Worker {index}: {state}")
    return "\n".join(lines)
