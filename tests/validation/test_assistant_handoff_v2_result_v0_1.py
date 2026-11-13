from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
RESULT_RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_result_v0_1.py"
S2_RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py"


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


result_runtime = load(
    RESULT_RUNTIME,
    "assistant_handoff_v2_result_runtime_test",
)
s2_runtime = load(
    S2_RUNTIME,
    "assistant_handoff_v2_runtime_s3_test",
)


def manifest(digest: str = "a" * 64) -> dict[str, Any]:
    return {
        "handoff_manifest_sha256": digest,
        "expected_result_schema_revision": "0.1.0",
    }


def result(digest: str = "a" * 64) -> dict[str, Any]:
    return {
        "schema_version": result_runtime.RESULT_SCHEMA_VERSION,
        "handoff_manifest_sha256": digest,
        "attempt_id": "attempt-s3-test-001",
        "status": "PASS",
        "changed_paths": ["a.txt"],
        "validation_evidence": [{"name": "pytest", "result": "PASS"}],
        "self_repair_attempts": [],
        "resume_coordinates": {"step": "return-result"},
        "unresolved_findings": [{"note": "preserve-me"}],
    }


def error_codes(value: dict[str, Any]) -> set[str]:
    return {
        item["code"]
        for item in result_runtime.validate_result_envelope(
            value,
            manifest(),
            root=ROOT,
        )
    }


def test_exact_valid_result_passes() -> None:
    assert error_codes(result()) == set()


def test_missing_and_unexpected_fields_fail_closed() -> None:
    value = result()
    value.pop("status")
    value["outcome"] = "PASS"
    codes = error_codes(value)
    assert "MISSING_FIELDS" in codes
    assert "UNEXPECTED_FIELDS" in codes


def test_manifest_binding_mismatch_is_not_repairable() -> None:
    value = result("b" * 64)
    report = result_runtime.validate_with_bounded_self_repair(
        value,
        manifest(),
        root=ROOT,
        max_self_repair_attempts=3,
    )
    assert report["valid"] is False
    assert report["repair_attempt_count"] == 0
    assert {item["code"] for item in report["errors"]} == {"RESULT_MANIFEST_BINDING_MISMATCH"}
    assert report["result"]["handoff_manifest_sha256"] == "b" * 64


def test_attempt_id_is_not_rewritten() -> None:
    value = result()
    value["attempt_id"] = "bad attempt id"
    report = result_runtime.validate_with_bounded_self_repair(
        value,
        manifest(),
        root=ROOT,
        max_self_repair_attempts=3,
    )
    assert report["valid"] is False
    assert report["repair_attempt_count"] == 0
    assert report["result"]["attempt_id"] == "bad attempt id"
    assert {item["code"] for item in report["errors"]} == {"ATTEMPT_ID_INVALID"}


def test_duplicate_changed_path_has_one_safe_repair() -> None:
    value = result()
    value["changed_paths"] = ["a.txt", "a.txt", "b.txt"]
    report = result_runtime.validate_with_bounded_self_repair(
        value,
        manifest(),
        root=ROOT,
        max_self_repair_attempts=1,
    )
    assert report["valid"] is True
    assert report["repair_attempt_count"] == 1
    assert report["result"]["changed_paths"] == ["a.txt", "b.txt"]
    attempts = report["result"]["self_repair_attempts"]
    assert len(attempts) == 1
    assert attempts[0]["repair_code"] == "DEDUPLICATE_IDENTICAL_CHANGED_PATHS"
    assert attempts[0]["authority_scope"] == "RESULT_ENVELOPE_MECHANICAL_ONLY"


def test_zero_repair_budget_leaves_duplicate_invalid() -> None:
    value = result()
    value["changed_paths"] = ["a.txt", "a.txt"]
    report = result_runtime.validate_with_bounded_self_repair(
        value,
        manifest(),
        root=ROOT,
        max_self_repair_attempts=0,
    )
    assert report["valid"] is False
    assert report["repair_attempt_count"] == 0
    assert "CHANGED_PATH_DUPLICATE" in {item["code"] for item in report["errors"]}


def test_repair_preserves_unresolved_findings() -> None:
    value = result()
    before = list(value["unresolved_findings"])
    value["changed_paths"] = ["a.txt", "a.txt"]
    report = result_runtime.validate_with_bounded_self_repair(
        value,
        manifest(),
        root=ROOT,
        max_self_repair_attempts=1,
    )
    assert report["valid"] is True
    assert report["result"]["unresolved_findings"] == before


def test_repair_budget_hard_ceiling() -> None:
    with pytest.raises(
        result_runtime.ResultValidationError,
        match="must be 0..3",
    ):
        result_runtime.validate_with_bounded_self_repair(
            result(),
            manifest(),
            root=ROOT,
            max_self_repair_attempts=4,
        )


def test_s2_runtime_delegates_result_validation() -> None:
    origin = s2_runtime.compile_runtime_manifest(
        ROOT,
        launch_mode="PROJECT_ONBOARD",
    )
    value = result(origin["handoff_manifest_sha256"])
    value["resume_coordinates"] = {
        "attempt_id": value["attempt_id"],
        "handoff_manifest_sha256": origin["handoff_manifest_sha256"],
        "source_state_fingerprint": origin["source_state_fingerprint"],
        "lifecycle_roadmap_cursor": origin["lifecycle_roadmap_cursor"],
    }
    report = s2_runtime.validate_result_for_return(
        ROOT,
        origin,
        value,
        max_self_repair_attempts=2,
    )
    assert report["valid"] is True
    compiled = s2_runtime.compile_runtime_manifest(
        ROOT,
        launch_mode="PROJECT_ONBOARD",
    )
    assert compiled["s2_scope"]["exact_result_validation_implemented_s3"] is True
    assert compiled["s2_scope"]["bounded_self_repair_execution_implemented_s3"] is True
    assert compiled["s2_scope"]["dispatcher_integration_deferred_to_cf09"] is True
