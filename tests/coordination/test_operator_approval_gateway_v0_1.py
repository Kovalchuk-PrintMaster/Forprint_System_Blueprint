from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from scripts.coordination import build_operator_approval_decision as gateway

REQUEST_ID = "request-1"
FINGERPRINT = "a" * 64


def _launch_request(path: Path, *, state: str) -> Path:
    data = {
        "schema_version": "forprint_launch_request_v0_1",
        "request_id": REQUEST_ID,
        "state": state,
        "identity": {
            "module_id": "logistics_service",
            "prompt_id": "prompt-v0-1",
            "task_context_id": "ctx-v0-1",
            "context_fingerprint_sha256": "b" * 64,
            "request_fingerprint_sha256": FINGERPRINT,
        },
        "task_context": {
            "archive_path": str(path.parent / "context.zip"),
            "archive_sha256": "c" * 64,
        },
        "repository_revalidation": {
            "blueprint_head": "blueprint-head",
            "module_head": "module-head",
            "fresh_context_state": "PASS",
            "unclassified_dirty_paths": [],
        },
        "dependency_readiness": {
            "path": str(path.parent / "dependency.yaml"),
            "sha256": "d" * 64,
            "status": "READY" if state == "AWAITING_OPERATOR_APPROVAL" else "NOT_PROVIDED",
        },
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def _current(state: str) -> dict:
    return yaml.safe_load(
        yaml.safe_dump(
            {
                "schema_version": "forprint_launch_request_v0_1",
                "request_id": REQUEST_ID,
                "state": state,
                "identity": {
                    "module_id": "logistics_service",
                    "prompt_id": "prompt-v0-1",
                    "task_context_id": "ctx-v0-1",
                    "context_fingerprint_sha256": "b" * 64,
                    "request_fingerprint_sha256": FINGERPRINT,
                },
                "task_context": {
                    "archive_path": "context.zip",
                    "archive_sha256": "c" * 64,
                },
                "repository_revalidation": {
                    "blueprint_head": "blueprint-head",
                    "module_head": "module-head",
                    "fresh_context_state": "PASS",
                    "unclassified_dirty_paths": [],
                },
                "dependency_readiness": {
                    "path": "dependency.yaml",
                    "sha256": "d" * 64,
                    "status": "READY" if state == "AWAITING_OPERATOR_APPROVAL" else "NOT_PROVIDED",
                },
            },
            sort_keys=False,
        )
    )


def test_blocked_request_cannot_be_approved(tmp_path: Path, monkeypatch) -> None:
    launch = _launch_request(tmp_path / "launch.yaml", state="BLOCKED")
    monkeypatch.setattr(
        gateway,
        "_revalidate_launch_request",
        lambda **_: _current("BLOCKED"),
    )

    evaluation = gateway.evaluate_gateway(
        root=tmp_path,
        module_root=tmp_path,
        launch_request_path=launch,
    )

    assert evaluation.status == gateway.EVAL_OK
    assert "APPROVE" not in evaluation.allowed_decisions
    assert set(evaluation.allowed_decisions) == {"HOLD", "REJECT"}


def test_approve_builds_expiring_human_authority_artifact(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launch = _launch_request(
        tmp_path / "launch.yaml",
        state="AWAITING_OPERATOR_APPROVAL",
    )
    current = _current("AWAITING_OPERATOR_APPROVAL")
    current["task_context"]["archive_path"] = str(tmp_path / "context.zip")
    current["dependency_readiness"]["path"] = str(tmp_path / "dependency.yaml")
    monkeypatch.setattr(
        gateway,
        "_revalidate_launch_request",
        lambda **_: current,
    )
    now = datetime(2026, 9, 6, 18, 0, tzinfo=UTC)

    decision = gateway.build_operator_decision(
        root=tmp_path,
        module_root=tmp_path,
        launch_request_path=launch,
        decision="APPROVE",
        decided_by="operator",
        reason="pilot approved",
        expires_in_minutes=20,
        now=now,
    )

    assert decision["decision"] == "APPROVE"
    assert decision["decided_by"] == "operator"
    assert decision["expires_at"] == (now + timedelta(minutes=20)).isoformat()
    assert decision["authority"]["human_operator_decision"] is True
    assert decision["authority"]["eligible_as_future_worker_dispatch_authority"] is True
    assert decision["authority"]["direct_worker_dispatch_allowed_by_gateway"] is False
    assert decision["authority"]["blueprint_accept"] is False
    assert decision["governance_alignment"]["q4_artifact_type"] == "operator_decision"
    assert decision["governance_alignment"]["q5_event_family"] == "operator_decision"
    assert decision["governance_alignment"]["q6_attention_reason"] == "operator_acceptance_required"


def test_hold_on_blocked_request_is_non_execution_decision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launch = _launch_request(tmp_path / "launch.yaml", state="BLOCKED")
    monkeypatch.setattr(
        gateway,
        "_revalidate_launch_request",
        lambda **_: _current("BLOCKED"),
    )

    decision = gateway.build_operator_decision(
        root=tmp_path,
        module_root=tmp_path,
        launch_request_path=launch,
        decision="HOLD",
        decided_by="operator",
        reason="dependency evidence missing",
    )

    assert decision["decision"] == "HOLD"
    assert decision["expires_at"] is None
    assert decision["authority"]["eligible_as_future_worker_dispatch_authority"] is False
    assert decision["governance_alignment"]["q6_attention_reason"] == "dependency_blocked"


def test_expired_approval_is_invalid_for_dispatch(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launch = _launch_request(
        tmp_path / "launch.yaml",
        state="AWAITING_OPERATOR_APPROVAL",
    )
    current = _current("AWAITING_OPERATOR_APPROVAL")
    current["task_context"]["archive_path"] = str(tmp_path / "context.zip")
    current["dependency_readiness"]["path"] = str(tmp_path / "dependency.yaml")
    monkeypatch.setattr(
        gateway,
        "_revalidate_launch_request",
        lambda **_: current,
    )
    decided = datetime(2026, 9, 6, 18, 0, tzinfo=UTC)
    decision = gateway.build_operator_decision(
        root=tmp_path,
        module_root=tmp_path,
        launch_request_path=launch,
        decision="APPROVE",
        decided_by="operator",
        reason="pilot approved",
        expires_in_minutes=5,
        now=decided,
    )
    decision_path = tmp_path / "decision.yaml"
    decision_path.write_text(
        yaml.safe_dump(decision, sort_keys=False),
        encoding="utf-8",
    )

    validation = gateway.validate_approval_for_dispatch(
        root=tmp_path,
        module_root=tmp_path,
        launch_request_path=launch,
        decision_path=decision_path,
        now=decided + timedelta(minutes=6),
    )

    assert validation.valid is False
    assert gateway.APPROVAL_EXPIRED in validation.reason_codes


def test_request_fingerprint_drift_invalidates_gateway(
    tmp_path: Path,
    monkeypatch,
) -> None:
    launch = _launch_request(
        tmp_path / "launch.yaml",
        state="AWAITING_OPERATOR_APPROVAL",
    )
    current = _current("AWAITING_OPERATOR_APPROVAL")
    current["identity"]["request_fingerprint_sha256"] = "e" * 64
    monkeypatch.setattr(
        gateway,
        "_revalidate_launch_request",
        lambda **_: current,
    )

    evaluation = gateway.evaluate_gateway(
        root=tmp_path,
        module_root=tmp_path,
        launch_request_path=launch,
    )

    assert evaluation.status == gateway.EVAL_INVALID
    assert gateway.REQUEST_FINGERPRINT_DRIFT in evaluation.reason_codes
    assert evaluation.allowed_decisions == ()
