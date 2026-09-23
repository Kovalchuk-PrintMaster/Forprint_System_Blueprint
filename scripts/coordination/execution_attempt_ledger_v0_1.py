from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

CONTRACT_REL = Path("coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")


def load_contract(root: Path) -> dict[str, Any]:
    value = yaml.safe_load((root / CONTRACT_REL).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Execution Attempt Ledger contract root must be a mapping")
    validate_contract_shape(value)
    return value


def validate_contract_shape(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "forprint_execution_attempt_ledger_contract_v0_1":
        raise ValueError("unexpected Execution Attempt Ledger contract schema")
    model = contract.get("authority_model")
    if not isinstance(model, dict):
        raise ValueError("authority_model missing")
    for key in (
        "generated_projections_are_authority",
        "raw_chat_is_execution_authority",
        "grants_worker_dispatch_authority",
        "grants_release_authority",
        "grants_foreign_repository_write_authority",
    ):
        if model.get(key) is not False:
            raise ValueError(f"authority_model.{key} must be false")
    if model.get("work_front_contract_is_execution_authority") is not True:
        raise ValueError("Work Front authority binding missing")
    if model.get("lifecycle_event_store_is_roadmap_execution_authority") is not True:
        raise ValueError("Lifecycle authority binding missing")
    if model.get("attempt_ledger_is_fact_authority_only") is not True:
        raise ValueError("attempt ledger fact-only authority binding missing")
    storage = contract.get("storage")
    if not isinstance(storage, dict) or storage.get("model") != "append_only_immutable_files":
        raise ValueError("append-only storage model missing")

    history = contract.get("attempt_history_semantics")
    if not isinstance(history, dict):
        raise ValueError("attempt_history_semantics missing")
    if history.get("model") != "one_ledger_append_only_attempt_history":
        raise ValueError("attempt history model invalid")
    identity = history.get("record_identity")
    if not isinstance(identity, dict):
        raise ValueError("attempt history record_identity missing")
    if identity.get("persisted_record_id_required") is not False:
        raise ValueError("persisted attempt record_id must remain unnecessary")
    same_attempt = history.get("same_attempt_append")
    if not isinstance(same_attempt, dict):
        raise ValueError("same_attempt_append missing")
    if same_attempt.get("exact_record_reappend_allowed") is not False:
        raise ValueError("exact record reappend must remain forbidden")
    if (
        same_attempt.get("previous_latest_result_state_required")
        != "PENDING"
    ):
        raise ValueError("same-attempt previous state must be PENDING")
    if same_attempt.get("new_result_state_must_not_be") != "PENDING":
        raise ValueError("same-attempt append must terminalize PENDING")
    if same_attempt.get("recorded_at_strictly_increases") is not True:
        raise ValueError("same-attempt recorded_at monotonicity missing")
    if same_attempt.get("post_terminal_append_allowed") is not False:
        raise ValueError("post-terminal same-attempt append must be forbidden")
    stable = same_attempt.get("stable_fields")
    if not isinstance(stable, list) or not stable:
        raise ValueError("same-attempt stable_fields missing")


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, *, non_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (bool(value) or not non_empty)
        and all(_non_empty_string(item) for item in value)
    )


def _timestamp(value: Any) -> bool:
    if not _non_empty_string(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_record_data(
    record: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    schema = contract["record_schema"]
    for field in schema["required_fields"]:
        if field not in record:
            errors.append(f"missing field: {field}")
    if errors:
        return errors

    if record["schema_version"] != schema["schema_version"]:
        errors.append("schema_version mismatch")
    for key in ("attempt_id", "work_front_id"):
        if not _non_empty_string(record[key]) or not ID_RE.fullmatch(record[key]):
            errors.append(f"{key} invalid")
    for key in (
        "actor_or_worker_ref",
        "where",
        "why",
        "source_fingerprint",
    ):
        if not _non_empty_string(record[key]):
            errors.append(f"{key} must be non-empty string")
    if not _timestamp(record["recorded_at"]):
        errors.append("recorded_at must be ISO-8601")

    nullable = set(schema.get("nullable_when_unavailable", []))
    for key in nullable:
        value = record[key]
        if value is not None and not _non_empty_string(value):
            errors.append(f"{key} must be null or non-empty string")

    if record["attempt_stage"] not in schema["attempt_stages"]:
        errors.append("attempt_stage invalid")
    if record["result_state"] not in schema["result_states"]:
        errors.append("result_state invalid")
    if record["validator_outcome"] not in schema["validator_outcomes"]:
        errors.append("validator_outcome invalid")
    if not _string_list(record["result_refs"]):
        errors.append("result_refs must be a string list")
    if not _string_list(record["validator_evidence_refs"]):
        errors.append("validator_evidence_refs must be a string list")

    resume = record["resume"]
    if not isinstance(resume, dict):
        errors.append("resume must be a mapping")
    else:
        for key in schema["resume_required_fields"]:
            if key not in resume:
                errors.append(f"resume missing field: {key}")
        if not errors:
            latest = resume["latest_accepted_ref"]
            if latest is not None and not _non_empty_string(latest):
                errors.append("resume.latest_accepted_ref invalid")
            if not _string_list(resume["resume_coordinates"]):
                errors.append("resume.resume_coordinates must be a string list")
            if not _string_list(resume["replay_forbidden_refs"]):
                errors.append("resume.replay_forbidden_refs must be a string list")
            partial = (
                record["result_state"] == "PARTIAL" or record["attempt_stage"] == "INTERRUPTED"
            )
            if partial and not (resume["resume_coordinates"] or _non_empty_string(latest)):
                errors.append("partial/interrupted attempt requires durable resume coordinate")

    retry_of = record.get("retry_of_attempt_id")
    if retry_of is not None and (not _non_empty_string(retry_of) or not ID_RE.fullmatch(retry_of)):
        errors.append("retry_of_attempt_id invalid")

    for key in schema.get("forbidden_authority_fields", []):
        if key in record:
            errors.append(f"forbidden authority field: {key}")
    return errors


def record_digest(record: dict[str, Any]) -> str:
    payload = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def store_root(root: Path, contract: dict[str, Any], override: Path | None) -> Path:
    if override is not None:
        return override
    return root / contract["storage"]["default_root"]


def iter_records(store: Path) -> list[dict[str, Any]]:
    if not store.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(store.glob("*.yaml")):
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(value, dict):
            records.append(value)
    return records



def _recorded_at_value(record: dict[str, Any]) -> datetime:
    raw = record.get("recorded_at")
    if not _non_empty_string(raw):
        raise ValueError("recorded_at must be a non-empty ISO-8601 string")
    try:
        value = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("recorded_at must be ISO-8601") from exc
    return value


def records_for_attempt(
    store: Path,
    attempt_id: str,
) -> list[dict[str, Any]]:
    records = [
        row
        for row in iter_records(store)
        if row.get("attempt_id") == attempt_id
    ]
    return sorted(
        records,
        key=lambda row: (
            _recorded_at_value(row),
            record_digest(row),
        ),
    )


def latest_attempt_record(
    store: Path,
    attempt_id: str,
) -> dict[str, Any] | None:
    records = records_for_attempt(store, attempt_id)
    return records[-1] if records else None


def latest_attempt_records(
    store: Path,
    *,
    work_front_id: str | None = None,
) -> list[dict[str, Any]]:
    records = iter_records(store)
    if work_front_id is not None:
        records = [
            row
            for row in records
            if row.get("work_front_id") == work_front_id
        ]

    latest_by_attempt: dict[str, dict[str, Any]] = {}
    for record in records:
        attempt_id = record.get("attempt_id")
        if not isinstance(attempt_id, str):
            raise ValueError("attempt_id must be a non-empty string")
        current = latest_by_attempt.get(attempt_id)
        if current is None or (
            _recorded_at_value(record),
            record_digest(record),
        ) > (
            _recorded_at_value(current),
            record_digest(current),
        ):
            latest_by_attempt[attempt_id] = record
    return [
        latest_by_attempt[attempt_id]
        for attempt_id in sorted(latest_by_attempt)
    ]


def _validate_same_attempt_append(
    record: dict[str, Any],
    latest: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    history = contract["attempt_history_semantics"]
    same_attempt = history["same_attempt_append"]

    required_previous = same_attempt[
        "previous_latest_result_state_required"
    ]
    if latest.get("result_state") != required_previous:
        raise FileExistsError(
            "attempt_id already terminal: "
            + str(record["attempt_id"])
        )

    forbidden_new = same_attempt["new_result_state_must_not_be"]
    if record.get("result_state") == forbidden_new:
        raise ValueError(
            "same-attempt append must terminalize PENDING result_state"
        )

    if (
        same_attempt.get("recorded_at_strictly_increases") is True
        and _recorded_at_value(record) <= _recorded_at_value(latest)
    ):
        raise ValueError(
            "same-attempt recorded_at must be strictly greater than latest"
        )

    stable_fields = same_attempt["stable_fields"]
    drift = [
        field
        for field in stable_fields
        if record.get(field) != latest.get(field)
    ]
    if drift:
        raise ValueError(
            "same-attempt stable field drift: " + ", ".join(drift)
        )


def append_record(
    root: Path,
    record: dict[str, Any],
    *,
    store_override: Path | None = None,
) -> Path:
    contract = load_contract(root)
    errors = validate_record_data(record, contract)
    if errors:
        raise ValueError("; ".join(errors))

    store = store_root(root, contract, store_override)
    store.mkdir(parents=True, exist_ok=True)
    records = iter_records(store)
    attempt_id = record["attempt_id"]

    digest = record_digest(record)
    if any(record_digest(existing) == digest for existing in records):
        raise FileExistsError(
            f"record already exists for attempt_id: {attempt_id}"
        )

    same_attempt_records = [
        existing
        for existing in records
        if existing.get("attempt_id") == attempt_id
    ]
    if same_attempt_records:
        latest = latest_attempt_record(store, attempt_id)
        if latest is None:
            raise ValueError(
                f"attempt history unexpectedly empty: {attempt_id}"
            )
        _validate_same_attempt_append(record, latest, contract)

    retry_of = record.get("retry_of_attempt_id")
    if retry_of is not None and not any(
        existing.get("attempt_id") == retry_of for existing in records
    ):
        raise ValueError(f"retry_of_attempt_id not found: {retry_of}")

    path = store / f"{attempt_id}__{digest[:12]}.yaml"
    payload = yaml.safe_dump(record, sort_keys=False, allow_unicode=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
    return path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--record", required=True)

    append = sub.add_parser("append")
    append.add_argument("--record", required=True)
    append.add_argument("--store-root")

    listing = sub.add_parser("list")
    listing.add_argument("--work-front-id")
    listing.add_argument("--store-root")

    status = sub.add_parser("status")
    status.add_argument("--work-front-id")
    status.add_argument("--store-root")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    contract = load_contract(root)

    if args.command == "validate":
        record = yaml.safe_load((root / args.record).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("record root must be a mapping")
        errors = validate_record_data(record, contract)
        if errors:
            print("EXECUTION_ATTEMPT_RECORD_VALIDATION=FAIL")
            for error in errors:
                print("ERROR=" + error)
            return 1
        print("EXECUTION_ATTEMPT_RECORD_VALIDATION=PASS")
        return 0

    override = Path(args.store_root).resolve() if args.store_root else None
    if args.command == "append":
        record = yaml.safe_load((root / args.record).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("record root must be a mapping")
        path = append_record(root, record, store_override=override)
        print("EXECUTION_ATTEMPT_APPEND=PASS")
        print("RECORD_PATH=" + str(path))
        print("DISPATCH_AUTHORITY=false")
        return 0

    store = store_root(root, contract, override)
    if args.command == "status":
        records = latest_attempt_records(
            store,
            work_front_id=args.work_front_id,
        )
    else:
        records = iter_records(store)
        if args.work_front_id:
            records = [
                row
                for row in records
                if row.get("work_front_id") == args.work_front_id
            ]
    print(yaml.safe_dump(records, sort_keys=False, allow_unicode=True).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
