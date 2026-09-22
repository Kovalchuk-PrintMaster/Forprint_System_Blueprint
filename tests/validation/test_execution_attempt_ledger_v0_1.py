from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/coordination/execution_attempt_ledger_v0_1.py"
spec = importlib.util.spec_from_file_location("_attempt_test_runtime", SOURCE)
assert spec is not None and spec.loader is not None
attempt = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = attempt
spec.loader.exec_module(attempt)


def record(attempt_id: str = "attempt-test-001") -> dict:
    return {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": attempt_id,
        "work_front_id": "wf-test-001",
        "recorded_at": "2026-09-14T13:00:00Z",
        "actor_or_worker_ref": "test",
        "where": "blueprint",
        "why": "bounded CF-05 test",
        "source_fingerprint": "sha256:test-source",
        "profile_ref_or_revision": None,
        "pack_hash_or_context_hash": None,
        "launch_or_invocation_ref": None,
        "attempt_stage": "FAILED",
        "result_state": "FAILED",
        "result_refs": [],
        "validator_outcome": "FAIL",
        "validator_evidence_refs": ["pytest:self"],
        "failure_or_retry_ref": "failure:test",
        "resume": {
            "latest_accepted_ref": None,
            "resume_coordinates": [],
            "replay_forbidden_refs": [],
        },
    }


def test_contract_preserves_authority_separation() -> None:
    contract = attempt.load_contract(ROOT)
    model = contract["authority_model"]
    assert model["work_front_contract_is_execution_authority"] is True
    assert model["lifecycle_event_store_is_roadmap_execution_authority"] is True
    assert model["attempt_ledger_is_fact_authority_only"] is True
    assert model["grants_worker_dispatch_authority"] is False


def test_valid_failed_attempt_passes() -> None:
    assert attempt.validate_record_data(record(), attempt.load_contract(ROOT)) == []


def test_partial_attempt_requires_resume_coordinate() -> None:
    value = record()
    value["attempt_stage"] = "INTERRUPTED"
    value["result_state"] = "PARTIAL"
    errors = attempt.validate_record_data(value, attempt.load_contract(ROOT))
    assert "partial/interrupted attempt requires durable resume coordinate" in errors
    value["resume"]["latest_accepted_ref"] = "mutation:accepted-001"
    assert attempt.validate_record_data(value, attempt.load_contract(ROOT)) == []


def test_retry_preserves_failed_attempt(tmp_path: Path) -> None:
    failed = record("attempt-test-001")
    retry = record("attempt-test-002")
    retry.update(
        {
            "retry_of_attempt_id": "attempt-test-001",
            "attempt_stage": "FINISHED",
            "result_state": "SUCCEEDED",
            "validator_outcome": "PASS",
            "validator_evidence_refs": ["pytest:retry"],
            "failure_or_retry_ref": "retry:attempt-test-001",
        }
    )
    attempt.append_record(ROOT, failed, store_override=tmp_path)
    attempt.append_record(ROOT, retry, store_override=tmp_path)
    records = attempt.iter_records(tmp_path)
    assert {row["attempt_id"] for row in records} == {
        "attempt-test-001",
        "attempt-test-002",
    }


def test_retry_must_reference_prior_attempt(tmp_path: Path) -> None:
    retry = record("attempt-test-002")
    retry["retry_of_attempt_id"] = "attempt-test-missing"
    with pytest.raises(ValueError, match="retry_of_attempt_id not found"):
        attempt.append_record(ROOT, retry, store_override=tmp_path)


def test_duplicate_attempt_id_is_rejected(tmp_path: Path) -> None:
    value = record()
    attempt.append_record(ROOT, value, store_override=tmp_path)
    with pytest.raises(FileExistsError):
        attempt.append_record(ROOT, value, store_override=tmp_path)


def test_authority_fields_are_forbidden() -> None:
    value = record()
    value["release_authority"] = True
    errors = attempt.validate_record_data(value, attempt.load_contract(ROOT))
    assert "forbidden authority field: release_authority" in errors


def _started_record(attempt_id: str = "attempt-test-terminal-001") -> dict:
    value = record(attempt_id)
    value.update(
        {
            "recorded_at": "2026-09-14T13:10:00Z",
            "attempt_stage": "STARTED",
            "result_state": "PENDING",
            "validator_outcome": "NOT_RUN",
            "validator_evidence_refs": [],
            "failure_or_retry_ref": None,
        }
    )
    return value


def _terminal_record(
    attempt_id: str = "attempt-test-terminal-001",
    *,
    recorded_at: str = "2026-09-14T13:11:00Z",
) -> dict:
    value = _started_record(attempt_id)
    value.update(
        {
            "recorded_at": recorded_at,
            "attempt_stage": "FINISHED",
            "result_state": "SUCCEEDED",
            "validator_outcome": "PASS",
            "validator_evidence_refs": ["pytest:terminal"],
        }
    )
    return value


def test_contract_declares_append_only_multi_record_attempt_history() -> None:
    contract = attempt.load_contract(ROOT)
    history = contract["attempt_history_semantics"]
    assert history["model"] == "one_ledger_append_only_attempt_history"
    assert history["attempt_identity"] == "attempt_id"
    assert history["record_identity"]["persisted_record_id_required"] is False
    assert history["latest_state"]["stored"] is False
    assert history["historical_migration_required"] is False


def test_started_pending_can_append_terminal_record_and_derive_latest(
    tmp_path: Path,
) -> None:
    started = _started_record()
    terminal = _terminal_record()

    first_path = attempt.append_record(
        ROOT,
        started,
        store_override=tmp_path,
    )
    second_path = attempt.append_record(
        ROOT,
        terminal,
        store_override=tmp_path,
    )

    assert first_path != second_path
    assert first_path.is_file()
    assert second_path.is_file()

    rows = attempt.records_for_attempt(
        tmp_path,
        started["attempt_id"],
    )
    assert [row["result_state"] for row in rows] == [
        "PENDING",
        "SUCCEEDED",
    ]

    latest = attempt.latest_attempt_record(
        tmp_path,
        started["attempt_id"],
    )
    assert latest is not None
    assert latest["attempt_stage"] == "FINISHED"
    assert latest["result_state"] == "SUCCEEDED"


def test_same_attempt_pending_to_pending_is_rejected(tmp_path: Path) -> None:
    started = _started_record()
    later_pending = _started_record()
    later_pending["recorded_at"] = "2026-09-14T13:11:00Z"

    attempt.append_record(ROOT, started, store_override=tmp_path)

    with pytest.raises(
        ValueError,
        match="must terminalize PENDING",
    ):
        attempt.append_record(
            ROOT,
            later_pending,
            store_override=tmp_path,
        )


def test_same_attempt_stable_field_drift_is_rejected(tmp_path: Path) -> None:
    started = _started_record()
    terminal = _terminal_record()
    terminal["source_fingerprint"] = "sha256:unexpected-drift"

    attempt.append_record(ROOT, started, store_override=tmp_path)

    with pytest.raises(
        ValueError,
        match="same-attempt stable field drift",
    ):
        attempt.append_record(
            ROOT,
            terminal,
            store_override=tmp_path,
        )


def test_same_attempt_recorded_at_must_strictly_increase(
    tmp_path: Path,
) -> None:
    started = _started_record()
    terminal = _terminal_record(
        recorded_at=started["recorded_at"],
    )

    attempt.append_record(ROOT, started, store_override=tmp_path)

    with pytest.raises(
        ValueError,
        match="recorded_at must be strictly greater",
    ):
        attempt.append_record(
            ROOT,
            terminal,
            store_override=tmp_path,
        )


def test_post_terminal_same_attempt_append_is_rejected(
    tmp_path: Path,
) -> None:
    started = _started_record()
    terminal = _terminal_record()
    later = _terminal_record(
        recorded_at="2026-09-14T13:12:00Z",
    )
    later["result_state"] = "FAILED"
    later["attempt_stage"] = "FAILED"

    attempt.append_record(ROOT, started, store_override=tmp_path)
    attempt.append_record(ROOT, terminal, store_override=tmp_path)

    with pytest.raises(
        FileExistsError,
        match="attempt_id already terminal",
    ):
        attempt.append_record(
            ROOT,
            later,
            store_override=tmp_path,
        )
