from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

CANDIDATE_ROOT = Path(__file__).resolve().parents[3]
LIVE_ROOT = Path(os.environ.get("FORPRINT_LIVE_ROOT", CANDIDATE_ROOT)).resolve()
ROOT = CANDIDATE_ROOT
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
CONTRACT = (
    ROOT / "coordination/standards/automation/control_plane/"
    "central_listener_dispatcher_monitor_v0_1.yaml"
)

spec = importlib.util.spec_from_file_location(
    "_cf09_dispatch_intent_attempt_integration_candidate",
    SOURCE,
)
assert spec and spec.loader
dispatch_intent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch_intent
spec.loader.exec_module(dispatch_intent)


def _origin_manifest(digest: str = "a" * 64) -> dict:
    return {
        "handoff_manifest_sha256": digest,
        "launch_mode": "TASK_EXECUTION",
    }


def _result(
    *,
    attempt_id: str = "attempt-cf09-s2-001",
    status: str = "PASS",
    digest: str = "a" * 64,
) -> dict:
    return {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": digest,
        "attempt_id": attempt_id,
        "status": status,
        "changed_paths": ["a.txt"],
        "validation_evidence": [{"name": "pytest", "result": "PASS"}],
        "self_repair_attempts": [],
        "resume_coordinates": {
            "attempt_id": attempt_id,
            "step": "return-result",
        },
        "unresolved_findings": [],
    }


def _attempt_record(
    attempt_id: str = "attempt-cf09-s2-001",
    *,
    result_state: str = "SUCCEEDED",
    work_front_id: str = "wf-cf09-s2",
) -> dict:
    return {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": attempt_id,
        "work_front_id": work_front_id,
        "recorded_at": "2026-09-17T13:45:00Z",
        "actor_or_worker_ref": "cf09-dispatcher-test",
        "where": "blueprint",
        "why": "CF09 Dispatcher integration test",
        "source_fingerprint": "sha256:test-source",
        "profile_ref_or_revision": "bounded-local@r1",
        "pack_hash_or_context_hash": None,
        "launch_or_invocation_ref": "handoff-v2:test",
        "attempt_stage": "FINISHED",
        "result_state": result_state,
        "result_refs": [],
        "validator_outcome": "PASS",
        "validator_evidence_refs": ["pytest:cf09-s2"],
        "failure_or_retry_ref": None,
        "resume": {
            "latest_accepted_ref": None,
            "resume_coordinates": ["return-result"],
            "replay_forbidden_refs": [],
        },
    }



def _worker_delta_report(
    changed_paths: list[str] | None = None,
    *,
    attempt_id: str = "cf10-u180j-a004",
    workspace_repo: str = "/tmp/cf10/workspace/repo",
    authority_granted: bool = False,
) -> dict:
    paths = ["a.txt"] if changed_paths is None else list(changed_paths)
    return {
        "schema_version": "forprint_worker_workspace_delta_v0_1",
        "attempt_id": attempt_id,
        "workspace_repo": workspace_repo,
        "source_head": "b" * 40,
        "baseline_fingerprint_sha256": "c" * 64,
        "inherited_dirty_paths": ["inherited.txt"],
        "post_worker_dirty_paths": list(paths),
        "changed_paths": list(paths),
        "worker_delta_exact": True,
        "authority_granted": authority_granted,
        "candidate_promoted": False,
        "canonical_write_performed": False,
    }



def _dispatch_decision(
    workspace_repo: Path,
    *,
    attempt_id: str = "cf10-u180j-a004",
) -> dict:
    return {
        "schema_version": (
            "forprint_cf10_internal_explicit_dispatch_decision_v0_1"
        ),
        "decision_id": "d" * 64,
        "decision": "ALLOW_EXACT_FIRST_INTERNAL_WORKER_LAUNCH",
        "binding": {
            "attempt_id": attempt_id,
            "worker_id": "worker-01",
            "workspace_repo": str(workspace_repo),
        },
        "assistant_ack_validated": True,
        "explicit_dispatch_decision_recorded": True,
        "worker_process_launch_allowed": True,
        "canonical_attempt_ledger_append_allowed": True,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "foreign_repository_write_allowed": False,
        "automatic_accept_allowed": False,
        "grants_broad_dispatch_authority": False,
    }


class _Ledger:
    def __init__(self):
        self.rows = []

    def load_contract(self, root):
        return {"schema_version": "test"}

    def validate_record_data(self, record, contract):
        required = {
            "attempt_id",
            "work_front_id",
            "recorded_at",
            "attempt_stage",
            "result_state",
        }
        return [] if required <= set(record) else ["missing"]

    def append_record(self, root, record, *, store_override=None):
        assert store_override is not None
        if any(row["attempt_id"] == record["attempt_id"] for row in self.rows):
            raise FileExistsError(record["attempt_id"])
        retry_of = record.get("retry_of_attempt_id")
        if retry_of and not any(row["attempt_id"] == retry_of for row in self.rows):
            raise ValueError("retry_of_attempt_id not found")
        self.rows.append(dict(record))
        output = Path(store_override) / f"{record['attempt_id']}__test.yaml"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(yaml.safe_dump(record), encoding="utf-8")
        return output


def _runtime(validated: dict):
    def validate_result_for_return(
        root,
        manifest,
        result,
        *,
        max_self_repair_attempts=2,
    ):
        assert max_self_repair_attempts == 2
        return dict(validated)

    return SimpleNamespace(
        validate_result_for_return=validate_result_for_return,
    )


def test_valid_pass_is_recorded_once_and_no_retry(tmp_path: Path) -> None:
    result = _result()
    ledger = _Ledger()
    report = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=_attempt_record(),
        attempt_number=1,
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(report),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "ATTEMPT_RECORDED"
    assert final["canonical_attempt_record_written"] is True
    assert final["telemetry_projection_written"] is True
    assert final["retry_decision"]["decision"] == "NO_RETRY_RESULT_PASS"
    assert final["worker_dispatch_performed"] is False
    assert len(ledger.rows) == 1

    telemetry = json.loads(Path(final["telemetry_projection_path"]).read_text(encoding="utf-8"))
    assert telemetry["source_of_truth"] is False
    assert telemetry["attempt_id"] == result["attempt_id"]
    assert telemetry["handoff_manifest_sha256"] == result["handoff_manifest_sha256"]


def test_invalid_result_never_reaches_canonical_ledger(tmp_path: Path) -> None:
    ledger = _Ledger()
    validation = {
        "valid": False,
        "result": _result(),
        "errors": [
            {
                "code": "STALE_GENERATED_CONTEXT",
                "field": "source_state_fingerprint",
                "message": "stale",
            }
        ],
        "repair_attempt_count": 0,
    }

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=_result(),
        attempt_record=_attempt_record(),
        attempt_number=1,
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "RESULT_REJECTED"
    assert final["canonical_attempt_record_written"] is False
    assert final["telemetry_projection_written"] is False
    assert ledger.rows == []


def test_retry_requires_new_attempt_id_and_explicit_dispatch(tmp_path: Path) -> None:
    retry_result = _result(status="RETRYABLE_FAILURE")
    validation = {
        "valid": True,
        "result": retry_result,
        "errors": [],
        "repair_attempt_count": 1,
        "freshness_resume": {"valid": True, "errors": []},
    }
    ledger = _Ledger()

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=retry_result,
        attempt_record=_attempt_record(result_state="FAILED"),
        attempt_number=1,
        requested_max_attempts=2,
        next_attempt_id="attempt-cf09-s2-002",
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
    )

    retry = final["retry_decision"]
    assert retry["retry_allowed"] is True
    assert retry["decision"] == "RETRY_ELIGIBLE_REQUIRES_EXPLICIT_DISPATCH"
    assert retry["retry_of_attempt_id"] == "attempt-cf09-s2-001"
    assert retry["next_attempt_id"] == "attempt-cf09-s2-002"
    assert final["worker_dispatch_performed"] is False
    assert final["next_required_boundary"] == "EXPLICIT_DISPATCH_DECISION"


def test_retry_same_attempt_id_is_rejected(tmp_path: Path) -> None:
    retry_result = _result(status="RETRYABLE_FAILURE")
    validation = {
        "valid": True,
        "result": retry_result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }

    try:
        dispatch_intent.finalize_cf09_task_execution(
            root=LIVE_ROOT,
            origin_manifest=_origin_manifest(),
            result=retry_result,
            attempt_record=_attempt_record(result_state="FAILED"),
            attempt_number=1,
            next_attempt_id="attempt-cf09-s2-001",
            ledger_store_override=tmp_path / "ledger",
            telemetry_root_override=tmp_path / "telemetry",
            runtime_loader=lambda: _runtime(validation),
            ledger_loader=lambda: _Ledger(),
        )
    except ValueError as exc:
        assert "new attempt_id" in str(exc)
    else:
        raise AssertionError("retry reused current attempt_id")


def test_retry_hard_ceiling_escalates_without_launch(tmp_path: Path) -> None:
    retry_result = _result(status="RETRYABLE_FAILURE")
    validation = {
        "valid": True,
        "result": retry_result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=retry_result,
        attempt_record=_attempt_record(result_state="FAILED"),
        attempt_number=3,
        requested_max_attempts=99,
        next_attempt_id="attempt-cf09-s2-004",
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: _Ledger(),
    )

    assert final["retry_budget"]["hard_ceiling"] == 3
    assert final["retry_budget"]["effective_max_attempts"] == 3
    assert final["retry_decision"]["decision"] == "ESCALATE_RETRY_CEILING_REACHED"
    assert final["retry_decision"]["retry_allowed"] is False
    assert final["worker_dispatch_performed"] is False


def test_attempt_id_binding_fails_closed(tmp_path: Path) -> None:
    result = _result()
    validation = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }

    try:
        dispatch_intent.finalize_cf09_task_execution(
            root=LIVE_ROOT,
            origin_manifest=_origin_manifest(),
            result=result,
            attempt_record=_attempt_record("attempt-other-001"),
            attempt_number=1,
            ledger_store_override=tmp_path / "ledger",
            telemetry_root_override=tmp_path / "telemetry",
            runtime_loader=lambda: _runtime(validation),
            ledger_loader=lambda: _Ledger(),
        )
    except ValueError as exc:
        assert "attempt_id" in str(exc)
    else:
        raise AssertionError("mismatched attempt_id accepted")


def test_contract_declares_reuse_and_no_worker_launch() -> None:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    row = data["cf09_attempt_result_integration"]

    assert row["reuse_before_create"]["execution_attempt_ledger"] is True
    assert row["canonical_attempt_history"]["parallel_ledger_created"] is False
    assert row["telemetry"]["source_of_truth"] is False
    assert row["retry"]["retry_creates_new_attempt_id"] is True
    assert row["retry"]["retry_launch_performed_by_this_slice"] is False
    assert row["resume"]["full_conversation_replay"] is False
    assert row["authority"]["worker_launch"] is False
    assert row["authority"]["cf10_started"] is False


class _TransitionLedger(_Ledger):
    # Minimal mock of the extended canonical same-attempt append semantics.

    def append_record(self, root, record, *, store_override=None):
        assert store_override is not None

        existing = [
            row
            for row in self.rows
            if row["attempt_id"] == record["attempt_id"]
        ]
        if existing:
            latest = existing[-1]
            if latest["result_state"] != "PENDING":
                raise FileExistsError(record["attempt_id"])
            if record["result_state"] == "PENDING":
                raise ValueError("same-attempt append must terminalize PENDING")

        retry_of = record.get("retry_of_attempt_id")
        if retry_of and not any(
            row["attempt_id"] == retry_of
            for row in self.rows
        ):
            raise ValueError("retry_of_attempt_id not found")

        self.rows.append(dict(record))
        output = (
            Path(store_override)
            / f"{record['attempt_id']}__transition-{len(self.rows)}.yaml"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            yaml.safe_dump(record),
            encoding="utf-8",
        )
        return output


def test_valid_pass_terminalizes_existing_started_attempt_without_new_attempt_id(
    tmp_path: Path,
) -> None:
    result = _result()
    ledger = _TransitionLedger()

    started = _attempt_record()
    started["recorded_at"] = "2026-09-17T13:44:00Z"
    started["attempt_stage"] = "STARTED"
    started["result_state"] = "PENDING"
    started["validator_outcome"] = "NOT_RUN"
    started["validator_evidence_refs"] = []
    started["resume"]["resume_coordinates"] = []
    ledger.rows.append(dict(started))

    report = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }

    terminal = _attempt_record()
    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=terminal,
        attempt_number=1,
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(report),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "ATTEMPT_RECORDED"
    assert final["canonical_attempt_record_written"] is True
    assert len(ledger.rows) == 2
    assert {
        row["attempt_id"]
        for row in ledger.rows
    } == {"attempt-cf09-s2-001"}
    assert [
        row["result_state"]
        for row in ledger.rows
    ] == ["PENDING", "SUCCEEDED"]
    assert ledger.rows[0]["attempt_stage"] == "STARTED"
    assert ledger.rows[1]["attempt_stage"] == "FINISHED"
    assert final["retry_decision"]["decision"] == "NO_RETRY_RESULT_PASS"
    assert final["worker_dispatch_performed"] is False


def test_cf10_result_requires_worker_delta_report_before_ledger(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    result = _result(attempt_id=attempt_id)
    validation = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }
    ledger = _Ledger()

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=_attempt_record(
            attempt_id,
            work_front_id="wf-cf10-worker-delta-verification",
        ),
        attempt_number=1,
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "RESULT_REJECTED"
    assert final["canonical_attempt_record_written"] is False
    assert final["telemetry_projection_written"] is False
    assert final["worker_delta_verification"]["required"] is True
    assert final["worker_delta_verification"]["provided"] is False
    assert final["worker_delta_verification"]["errors"] == [
        "WORKER_DELTA_REPORT_REQUIRED"
    ]
    assert ledger.rows == []


def test_cf10_result_rejects_worker_delta_changed_path_mismatch(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    result = _result(attempt_id=attempt_id)
    validation = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }
    ledger = _Ledger()

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=_attempt_record(
            attempt_id,
            work_front_id="wf-cf10-worker-delta-verification",
        ),
        attempt_number=1,
        worker_delta_report=_worker_delta_report(["different.txt"]),
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "RESULT_REJECTED"
    verification = final["worker_delta_verification"]
    assert verification["required"] is True
    assert verification["provided"] is True
    assert verification["valid"] is False
    assert verification["match"] is False
    assert "WORKER_DELTA_CHANGED_PATHS_MISMATCH" in verification["errors"]
    assert ledger.rows == []


def test_cf10_result_accepts_exact_worker_delta_before_ledger(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    result = _result(attempt_id=attempt_id)
    validation = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }
    ledger = _Ledger()

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=_attempt_record(
            attempt_id,
            work_front_id="wf-cf10-worker-delta-verification",
        ),
        attempt_number=1,
        worker_delta_report=_worker_delta_report(["a.txt"]),
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "ATTEMPT_RECORDED"
    verification = final["worker_delta_verification"]
    assert verification["required"] is True
    assert verification["provided"] is True
    assert verification["valid"] is True
    assert verification["match"] is True
    assert verification["reported_changed_paths"] == ["a.txt"]
    assert verification["derived_changed_paths"] == ["a.txt"]
    assert len(ledger.rows) == 1

    telemetry = json.loads(
        Path(final["telemetry_projection_path"]).read_text(encoding="utf-8")
    )
    assert telemetry["worker_delta_verification"]["valid"] is True
    assert telemetry["worker_delta_verification"]["source_of_truth"] is False


def test_cf10_result_rejects_worker_delta_authority_widening(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    result = _result(attempt_id=attempt_id)
    validation = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }
    ledger = _Ledger()

    final = dispatch_intent.finalize_cf09_task_execution(
        root=LIVE_ROOT,
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=_attempt_record(
            attempt_id,
            work_front_id="wf-cf10-worker-delta-verification",
        ),
        attempt_number=1,
        worker_delta_report=_worker_delta_report(
            ["a.txt"],
            authority_granted=True,
        ),
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
    )

    assert final["state"] == "RESULT_REJECTED"
    assert "WORKER_DELTA_AUTHORITY_WIDENED" in (
        final["worker_delta_verification"]["errors"]
    )
    assert ledger.rows == []


def test_cf10_workspace_finalizer_auto_derives_delta_from_bound_workspace(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    result = _result(attempt_id=attempt_id)
    validation = {
        "valid": True,
        "result": result,
        "errors": [],
        "repair_attempt_count": 0,
        "freshness_resume": {"valid": True, "errors": []},
    }
    ledger = _Ledger()

    workspace_repo = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / attempt_id
        / "workspace"
        / "repo"
    )
    workspace_repo.mkdir(parents=True)
    manifest_path = (
        workspace_repo.parent.parent / "manifest.yaml"
    )
    manifest_path.write_text("test: true\n", encoding="utf-8")

    seen: list[Path] = []

    def load_delta(path: Path) -> dict:
        seen.append(Path(path))
        return _worker_delta_report(
            ["a.txt"],
            attempt_id=attempt_id,
            workspace_repo=str(workspace_repo),
        )

    final = dispatch_intent.finalize_cf10_workspace_task_execution(
        root=LIVE_ROOT,
        explicit_dispatch_decision=_dispatch_decision(
            workspace_repo,
            attempt_id=attempt_id,
        ),
        origin_manifest=_origin_manifest(),
        result=result,
        attempt_record=_attempt_record(
            attempt_id,
            work_front_id="wf-cf10-worker-delta-verification",
        ),
        attempt_number=1,
        ledger_store_override=tmp_path / "ledger",
        telemetry_root_override=tmp_path / "telemetry",
        runtime_loader=lambda: _runtime(validation),
        ledger_loader=lambda: ledger,
        worker_delta_loader=load_delta,
    )

    assert seen == [manifest_path]
    assert final["state"] == "ATTEMPT_RECORDED"
    assert final["worker_delta_verification"]["valid"] is True
    assert final["worker_delta_verification"]["match"] is True
    assert len(ledger.rows) == 1


def test_cf10_workspace_finalizer_rejects_dispatch_attempt_mismatch(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    workspace_repo = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / "cf10-u180j-a999"
        / "workspace"
        / "repo"
    )
    workspace_repo.mkdir(parents=True)

    with pytest.raises(
        ValueError,
        match="decision attempt_id does not match result",
    ):
        dispatch_intent.finalize_cf10_workspace_task_execution(
            root=LIVE_ROOT,
            explicit_dispatch_decision=_dispatch_decision(
                workspace_repo,
                attempt_id="cf10-u180j-a999",
            ),
            origin_manifest=_origin_manifest(),
            result=_result(attempt_id=attempt_id),
            attempt_record=_attempt_record(
                attempt_id,
                work_front_id="wf-cf10-worker-delta-verification",
            ),
            attempt_number=1,
            ledger_store_override=tmp_path / "ledger",
            telemetry_root_override=tmp_path / "telemetry",
            runtime_loader=lambda: _runtime({}),
            ledger_loader=lambda: _Ledger(),
            worker_delta_loader=lambda path: {},
        )


def test_cf10_workspace_finalizer_rejects_delta_workspace_mismatch(
    tmp_path: Path,
) -> None:
    attempt_id = "cf10-u180j-a004"
    workspace_repo = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / attempt_id
        / "workspace"
        / "repo"
    )
    workspace_repo.mkdir(parents=True)
    other_workspace = (
        tmp_path / "other" / "workspace" / "repo"
    )
    other_workspace.mkdir(parents=True)

    with pytest.raises(
        ValueError,
        match="derived worker delta workspace binding mismatch",
    ):
        dispatch_intent.finalize_cf10_workspace_task_execution(
            root=LIVE_ROOT,
            explicit_dispatch_decision=_dispatch_decision(
                workspace_repo,
                attempt_id=attempt_id,
            ),
            origin_manifest=_origin_manifest(),
            result=_result(attempt_id=attempt_id),
            attempt_record=_attempt_record(
                attempt_id,
                work_front_id="wf-cf10-worker-delta-verification",
            ),
            attempt_number=1,
            ledger_store_override=tmp_path / "ledger",
            telemetry_root_override=tmp_path / "telemetry",
            runtime_loader=lambda: _runtime({}),
            ledger_loader=lambda: _Ledger(),
            worker_delta_loader=lambda path: _worker_delta_report(
                ["a.txt"],
                attempt_id=attempt_id,
                workspace_repo=str(other_workspace),
            ),
        )
