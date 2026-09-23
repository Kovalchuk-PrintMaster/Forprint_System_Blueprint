from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
S4_RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_freshness_resume_v0_1.py"
S2_RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py"


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


s4 = load(S4_RUNTIME, "assistant_handoff_v2_s4_test")
s2 = load(S2_RUNTIME, "assistant_handoff_v2_s2_s4_test")


def origin() -> dict[str, Any]:
    return {
        "schema_version": "forprint_assistant_handoff_v2_runtime_manifest_v0_1",
        "launch_mode": "PROJECT_ONBOARD",
        "source_state_fingerprint": "a" * 64,
        "lifecycle_roadmap_cursor": {
            "current": "CF-08",
            "event_sequence": 57,
            "roadmap_sync": "IN_SYNC",
        },
        "handoff_manifest_sha256": "b" * 64,
    }


def result(
    *,
    status: str = "PASS",
    attempt_id: str = "attempt-s4-test-001",
) -> dict[str, Any]:
    manifest = origin()
    return {
        "attempt_id": attempt_id,
        "status": status,
        "handoff_manifest_sha256": manifest["handoff_manifest_sha256"],
        "resume_coordinates": {
            "attempt_id": attempt_id,
            "handoff_manifest_sha256": manifest["handoff_manifest_sha256"],
            "source_state_fingerprint": manifest["source_state_fingerprint"],
            "lifecycle_roadmap_cursor": manifest["lifecycle_roadmap_cursor"],
        },
    }


def codes(report: dict[str, Any]) -> set[str]:
    return {item["code"] for item in report["errors"]}


def test_fresh_state_and_base_resume_pass() -> None:
    report = s4.validate_freshness_and_resume(
        origin(),
        origin(),
        result(),
        root=ROOT,
    )
    assert report["valid"] is True


def test_stale_source_fingerprint_fails_closed() -> None:
    live = origin()
    live["source_state_fingerprint"] = "c" * 64
    report = s4.validate_freshness_and_resume(
        origin(),
        live,
        result(),
        root=ROOT,
    )
    assert codes(report) == {"STALE_SOURCE_STATE_FINGERPRINT"}


def test_stale_cursor_fails_closed() -> None:
    live = origin()
    live["lifecycle_roadmap_cursor"] = {
        **live["lifecycle_roadmap_cursor"],
        "event_sequence": 58,
    }
    report = s4.validate_freshness_and_resume(
        origin(),
        live,
        result(),
        root=ROOT,
    )
    assert "STALE_LIFECYCLE_ROADMAP_CURSOR" in codes(report)


def test_resume_attempt_binding_mismatch_fails() -> None:
    value = result()
    value["resume_coordinates"]["attempt_id"] = "attempt-other-002"
    report = s4.validate_freshness_and_resume(
        origin(),
        origin(),
        value,
        root=ROOT,
    )
    assert "RESUME_ATTEMPT_BINDING_MISMATCH" in codes(report)


def test_resume_manifest_binding_mismatch_fails() -> None:
    value = result()
    value["resume_coordinates"]["handoff_manifest_sha256"] = "d" * 64
    report = s4.validate_freshness_and_resume(
        origin(),
        origin(),
        value,
        root=ROOT,
    )
    assert "RESUME_MANIFEST_BINDING_MISMATCH" in codes(report)


def test_retry_cannot_reuse_attempt_id() -> None:
    value = result()
    value["resume_coordinates"]["retry_of_attempt_id"] = value["attempt_id"]
    report = s4.validate_freshness_and_resume(
        origin(),
        origin(),
        value,
        root=ROOT,
    )
    assert "RESUME_ATTEMPT_BINDING_MISMATCH" in codes(report)


def test_partial_requires_durable_resume_anchors() -> None:
    value = result(status="INTERRUPTED")
    report = s4.validate_freshness_and_resume(
        origin(),
        origin(),
        value,
        root=ROOT,
    )
    assert "RESUME_COORDINATES_INCOMPLETE" in codes(report)

    value["resume_coordinates"].update(
        {
            "latest_completed_node": "validate_conformance",
            "latest_accepted_ref": "evt-u180h-activate",
            "replay_forbidden_refs": ["accepted-mutation-001"],
        }
    )
    report = s4.validate_freshness_and_resume(
        origin(),
        origin(),
        value,
        root=ROOT,
    )
    assert report["valid"] is True


def test_s2_scope_marks_s4_implemented() -> None:
    compiled = s2.compile_runtime_manifest(
        ROOT,
        launch_mode="PROJECT_ONBOARD",
    )
    scope = compiled["s2_scope"]
    assert scope["freshness_fail_closed_hardening_deferred_to_s4"] is False
    assert scope["freshness_fail_closed_hardening_implemented_s4"] is True
    assert scope["durable_resume_hardening_deferred_to_s4"] is False
    assert scope["durable_resume_hardening_implemented_s4"] is True
    assert scope["dispatcher_integration_deferred_to_cf09"] is True
