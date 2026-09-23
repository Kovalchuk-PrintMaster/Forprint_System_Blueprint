from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

CONTRACT_REL = Path("coordination/standards/automation/workfront_history_contract_v0_1.yaml")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")


def load_contract(root: Path) -> dict[str, Any]:
    value = yaml.safe_load((root / CONTRACT_REL).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Workfront History contract root must be a mapping")
    validate_contract_shape(value)
    return value


def validate_contract_shape(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "forprint_workfront_history_contract_v0_1":
        raise ValueError("unexpected Workfront History contract schema")
    model = contract.get("authority_model")
    if not isinstance(model, dict):
        raise ValueError("authority_model missing")
    required_false = (
        "generated_projections_are_authority",
        "raw_chat_is_execution_authority",
        "grants_worker_dispatch_authority",
        "grants_release_authority",
        "grants_foreign_repository_write_authority",
    )
    for key in required_false:
        if model.get(key) is not False:
            raise ValueError(f"authority_model.{key} must be false")
    if model.get("work_front_contract_is_execution_authority") is not True:
        raise ValueError("Work Front authority binding missing")
    if model.get("lifecycle_event_store_is_roadmap_execution_authority") is not True:
        raise ValueError("Lifecycle authority binding missing")
    if model.get("history_is_fact_authority_only") is not True:
        raise ValueError("history fact-only authority binding missing")
    storage = contract.get("storage")
    if not isinstance(storage, dict) or storage.get("model") != "append_only_immutable_files":
        raise ValueError("append-only storage model missing")


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
    raw = str(value).replace("Z", "+00:00")
    try:
        datetime.fromisoformat(raw)
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
    for key in ("history_record_id", "work_front_id"):
        if not _non_empty_string(record[key]) or not ID_RE.fullmatch(record[key]):
            errors.append(f"{key} invalid")
    for key in (
        "actor",
        "reason",
        "source_fingerprint",
        "work_front_snapshot_or_hash",
    ):
        if not _non_empty_string(record[key]):
            errors.append(f"{key} must be non-empty string")
    if not _timestamp(record["recorded_at"]):
        errors.append("recorded_at must be ISO-8601")
    if not _string_list(record["provenance_refs"], non_empty=True):
        errors.append("provenance_refs must be a non-empty string list")

    for key in schema.get("optional_fields", []):
        value = record.get(key)
        if value is not None and not _non_empty_string(value):
            errors.append(f"{key} must be null or non-empty string")

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

    record_id = record["history_record_id"]
    for existing in iter_records(store):
        if existing.get("history_record_id") == record_id:
            raise FileExistsError(f"history_record_id already exists: {record_id}")

    digest = record_digest(record)
    path = store / f"{record_id}__{digest[:12]}.yaml"
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

    args = parser.parse_args()
    root = Path(args.root).resolve()
    contract = load_contract(root)

    if args.command == "validate":
        record = yaml.safe_load((root / args.record).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("record root must be a mapping")
        errors = validate_record_data(record, contract)
        if errors:
            print("WORKFRONT_HISTORY_RECORD_VALIDATION=FAIL")
            for error in errors:
                print("ERROR=" + error)
            return 1
        print("WORKFRONT_HISTORY_RECORD_VALIDATION=PASS")
        return 0

    override = Path(args.store_root).resolve() if args.store_root else None
    if args.command == "append":
        record = yaml.safe_load((root / args.record).read_text(encoding="utf-8"))
        if not isinstance(record, dict):
            raise ValueError("record root must be a mapping")
        path = append_record(root, record, store_override=override)
        print("WORKFRONT_HISTORY_APPEND=PASS")
        print("RECORD_PATH=" + str(path))
        print("DISPATCH_AUTHORITY=false")
        return 0

    records = iter_records(store_root(root, contract, override))
    if args.work_front_id:
        records = [row for row in records if row.get("work_front_id") == args.work_front_id]
    print(yaml.safe_dump(records, sort_keys=False, allow_unicode=True).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
