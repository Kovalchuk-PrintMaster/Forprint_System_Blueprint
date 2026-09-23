from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/coordination/workfront_history_v0_1.py"
spec = importlib.util.spec_from_file_location("_wfh_test_runtime", SOURCE)
assert spec is not None and spec.loader is not None
wfh = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wfh
spec.loader.exec_module(wfh)


def record(record_id: str = "wfh-test-001") -> dict:
    return {
        "schema_version": "forprint_workfront_history_record_v0_1",
        "history_record_id": record_id,
        "work_front_id": "wf-test-001",
        "recorded_at": "2026-09-14T13:00:00Z",
        "actor": "test",
        "reason": "bounded implementation history",
        "source_fingerprint": "sha256:test-source",
        "work_front_snapshot_or_hash": "sha256:test-front",
        "provenance_refs": ["roadmap:CF-05"],
    }


def test_contract_preserves_authority_separation() -> None:
    contract = wfh.load_contract(ROOT)
    model = contract["authority_model"]
    assert model["work_front_contract_is_execution_authority"] is True
    assert model["lifecycle_event_store_is_roadmap_execution_authority"] is True
    assert model["history_is_fact_authority_only"] is True
    assert model["grants_worker_dispatch_authority"] is False


def test_valid_record_passes() -> None:
    assert wfh.validate_record_data(record(), wfh.load_contract(ROOT)) == []


def test_authority_fields_are_forbidden() -> None:
    value = record()
    value["dispatch_authority"] = True
    errors = wfh.validate_record_data(value, wfh.load_contract(ROOT))
    assert "forbidden authority field: dispatch_authority" in errors


def test_append_is_content_hash_bound_and_duplicate_id_is_rejected(
    tmp_path: Path,
) -> None:
    value = record()
    path = wfh.append_record(ROOT, value, store_override=tmp_path)
    assert path.is_file()
    assert wfh.record_digest(value)[:12] in path.name
    with pytest.raises(FileExistsError):
        wfh.append_record(ROOT, value, store_override=tmp_path)


def test_distinct_history_records_are_preserved(tmp_path: Path) -> None:
    first = record("wfh-test-001")
    second = record("wfh-test-002")
    second["parent_history_record_id"] = "wfh-test-001"
    wfh.append_record(ROOT, first, store_override=tmp_path)
    wfh.append_record(ROOT, second, store_override=tmp_path)
    records = wfh.iter_records(tmp_path)
    assert {row["history_record_id"] for row in records} == {
        "wfh-test-001",
        "wfh-test-002",
    }
