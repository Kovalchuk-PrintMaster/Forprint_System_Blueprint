from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/telegram_operator.py"

spec = importlib.util.spec_from_file_location(
    "_cf10_local_operator_surface_test",
    SOURCE,
)
assert spec is not None and spec.loader is not None
operator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = operator
spec.loader.exec_module(operator)

NOW = datetime(2026, 9, 27, 17, 30, tzinfo=UTC)
NOW_TEXT = NOW.isoformat().replace("+00:00", "Z")


def ledger_fact(
    attempt_id: str,
    *,
    stage: str = "STARTED",
    result: str = "PENDING",
) -> dict:
    return {
        "attempt_id": attempt_id,
        "attempt_stage": stage,
        "result_state": result,
    }


def state_for(record: dict, evidence: dict | None = None) -> str:
    projection = operator.build_operator_projection(
        attempt_records=[record],
        watchdog_evidence=(
            {record["attempt_id"]: evidence} if evidence is not None else None
        ),
        now=NOW_TEXT,
    )
    return projection["attempts"][0]["state"]


def test_projects_fresh_active_stalled_and_timeout_evidence() -> None:
    active = {
        "process_alive": True,
        "observed_at": NOW_TEXT,
        "stall_detected": False,
    }
    stalled = {
        "process_alive": True,
        "observed_at": NOW_TEXT,
        "stall_detected": True,
    }
    timeout = {
        "timed_out": True,
        "outcome": "timeout",
        "finished_at": NOW_TEXT,
        "process_started": True,
        "return_code": -15,
        "process_alive": False,
    }

    assert state_for(ledger_fact("active"), active) == "ACTIVE"
    assert state_for(ledger_fact("stalled"), stalled) == "STALLED"
    assert state_for(ledger_fact("timeout"), timeout) == "TIMEOUT"


def test_finished_uses_terminal_ledger_or_final_completion_evidence() -> None:
    assert state_for(
        ledger_fact("ledger-finished", stage="FINISHED", result="SUCCEEDED")
    ) == "FINISHED"
    completion = {
        "process_started": True,
        "process_alive": False,
        "finished_at": NOW_TEXT,
        "timed_out": False,
        "return_code": 0,
    }
    assert state_for(ledger_fact("completed"), completion) == "FINISHED"


def test_missing_stale_and_contradictory_live_facts_are_unknown() -> None:
    record = ledger_fact("pending")
    assert state_for(record) == "UNKNOWN"
    assert state_for(record, {"process_alive": True}) == "UNKNOWN"
    assert state_for(
        record,
        {
            "process_alive": True,
            "observed_at": (
                NOW - timedelta(seconds=61)
            ).isoformat().replace("+00:00", "Z"),
            "stall_detected": False,
        },
    ) == "UNKNOWN"
    assert state_for(
        record,
        {
            "process_alive": True,
            "observed_at": NOW_TEXT,
            "stall_detected": True,
            "timed_out": True,
        },
    ) == "UNKNOWN"
    assert state_for(
        record,
        {
            "timed_out": True,
            "finished_at": NOW_TEXT,
            "outcome": "completed",
            "process_started": True,
            "return_code": 1,
        },
    ) == "UNKNOWN"


def test_start_and_pending_alone_never_imply_activity() -> None:
    projection = operator.build_operator_projection(
        attempt_records=[ledger_fact("pending")],
    )
    assert projection["attempts"][0]["state"] == "UNKNOWN"


def test_projection_is_deterministic_read_only_and_has_false_authority() -> None:
    records = [ledger_fact("z"), ledger_fact("a")]
    first = operator.build_operator_projection(
        attempt_records=records,
        now=NOW_TEXT,
    )
    second = operator.build_operator_projection(
        attempt_records=records,
        now=NOW_TEXT,
    )
    assert first == second
    assert [item["attempt_id"] for item in first["attempts"]] == ["a", "z"]
    assert all(value is False for value in first["authority"].values())
    assert records == [ledger_fact("z"), ledger_fact("a")]


def test_rendering_is_deterministic_and_contains_no_action_surface_terms() -> None:
    projection = operator.build_operator_projection(
        attempt_records=[
            ledger_fact("a", stage="FINISHED", result="SUCCEEDED"),
            ledger_fact("b"),
        ],
        now=NOW_TEXT,
    )
    rendered = operator.render_telegram_text(projection)
    assert rendered == "Worker 1: FINISHED\nWorker 2: UNKNOWN"
    lowered = rendered.lower()
    assert all(term not in lowered for term in ("dispatch", "retry", "approve"))
