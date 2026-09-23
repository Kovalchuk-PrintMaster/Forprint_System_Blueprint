from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination.control_plane.dispatch_intent import build_dispatch_intent
from scripts.coordination.control_plane.events import Q5_REQUIRED_FIELDS, validate_q5_event_envelope
from scripts.coordination.control_plane.runtime import run_control_plane_step


def _write(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _launch(path: Path, state: str = "AWAITING_OPERATOR_APPROVAL") -> Path:
    return _write(
        path,
        {
            "schema_version": "forprint_launch_request_v0_1",
            "request_id": "req-1",
            "state": state,
            "identity": {"module_id": "logistics_service", "prompt_id": "prompt-1"},
            "repository_revalidation": {"module_head": "head-1"},
            "eligibility": {
                "blockers": []
                if state != "BLOCKED"
                else [{"code": "DEPENDENCY_READINESS_NOT_PROVIDED"}]
            },
        },
    )


def _approval(path: Path) -> Path:
    return _write(
        path,
        {
            "schema_version": "forprint_operator_approval_decision_v0_1",
            "decision_id": "decision-1",
            "request_id": "req-1",
            "decision": "APPROVE",
        },
    )


def _inv(path: Path, ready: bool = True) -> Path:
    return _write(
        path,
        {
            "schema_version": "forprint_worker_invocation_v0_1",
            "invocation_id": "inv-1",
            "state": "DRY_RUN_READY" if ready else "BLOCKED",
            "identity": {"module_id": "logistics_service", "prompt_id": "prompt-1"},
            "authority_binding": {
                "approval_valid_for_dispatch": ready,
                "approval_decision_id": "decision-1" if ready else None,
                "module_head": "head-1",
            },
            "eligibility": {"dry_run_ready": ready, "future_dispatch_eligible": ready},
            "console_command": {"subprocess_started": False},
        },
    )


def test_ready_artifacts_only_create_ready_for_explicit_dispatch(tmp_path: Path) -> None:
    r = build_dispatch_intent(
        launch_request_path=_launch(tmp_path / "launch.yaml"),
        worker_invocation_path=_inv(tmp_path / "inv.yaml"),
        approval_decision_path=_approval(tmp_path / "approval.yaml"),
    )
    assert r.state == "READY_FOR_EXPLICIT_DISPATCH"
    assert r.document["execution_boundaries"]["worker_process_started"] is False


def test_blocked_launch_cannot_be_force_approved(tmp_path: Path) -> None:
    r = build_dispatch_intent(
        launch_request_path=_launch(tmp_path / "launch.yaml", "BLOCKED"),
        worker_invocation_path=_inv(tmp_path / "inv.yaml"),
        approval_decision_path=_approval(tmp_path / "approval.yaml"),
    )
    assert r.state == "BLOCKED"
    assert "LAUNCH_REQUEST_NOT_AWAITING_OPERATOR_APPROVAL" in r.blocker_codes


def test_wip_one_blocks_second_execution(tmp_path: Path) -> None:
    active = _write(
        tmp_path / "active.yaml", {"module_id": "logistics_service", "state": "RUNNING"}
    )
    r = build_dispatch_intent(
        launch_request_path=_launch(tmp_path / "launch.yaml"),
        worker_invocation_path=_inv(tmp_path / "inv.yaml"),
        approval_decision_path=_approval(tmp_path / "approval.yaml"),
        active_execution_paths=[active],
    )
    assert "MODULE_WIP_CONFLICT" in r.blocker_codes


def test_q5_family_set_is_not_silently_expanded() -> None:
    event = {k: None for k in Q5_REQUIRED_FIELDS}
    event.update(
        {
            "event_id": "e1",
            "event_type": "claim_status.observed",
            "occurred_at": "2026-09-06T00:00:00+00:00",
            "producer": "test",
            "target": "blueprint",
            "correlation_id": "c1",
            "severity": "notice",
            "blocking": False,
            "schema_version": "payload_v0_1",
            "payload": {},
            "evidence_refs": [],
            "idempotency_key": "i1",
        }
    )
    assert validate_q5_event_envelope(event)[0] is True
    event["event_type"] = "dispatch_intent_state.ready"
    valid, errors = validate_q5_event_envelope(event)
    assert valid is False and "event_family_not_in_q5_v0_1" in errors


def test_one_shot_runtime_is_idempotent_and_never_executes(tmp_path: Path) -> None:
    launch = _launch(tmp_path / "launch.yaml", "BLOCKED")
    inv = _inv(tmp_path / "inv.yaml", False)
    first = run_control_plane_step(
        launch_request_path=launch,
        worker_invocation_path=inv,
        runtime_dir=tmp_path / "runtime",
        write=True,
    )
    second = run_control_plane_step(
        launch_request_path=launch,
        worker_invocation_path=inv,
        runtime_dir=tmp_path / "runtime",
        write=True,
    )
    assert first["dispatch_intent_state"] == "BLOCKED"
    assert first["execution_boundaries"]["worker_process_started"] is False
    assert first["execution_boundaries"]["daemon_started"] is False
    assert second["write_results"]["dispatch_intent"] == "DUPLICATE_EQUIVALENT"
