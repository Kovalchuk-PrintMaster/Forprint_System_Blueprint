from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
spec = importlib.util.spec_from_file_location("_cf10_launch_gate_test", SOURCE)
assert spec is not None and spec.loader is not None
dispatch = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch
spec.loader.exec_module(dispatch)


def prepared() -> dict:
    return {
        "schema_version": "forprint_cf09_dispatcher_pre_execution_envelope_v0_1",
        "mode": "TASK_EXECUTION",
        "state": "AWAITING_ASSISTANT_ACK",
        "module": "forprint_system_blueprint",
        "work_front_id": (
            "coordination/work_fronts/"
            "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
        ),
        "work_front_gate": {
            "validated": True,
            "work_front_id": (
                "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
            ),
            "work_front_path": (
                "coordination/work_fronts/"
                "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
            ),
        },
        "execution_profile_ref": "light-maintenance",
        "task_prompt_id": (
            "cf10-zero-stage-dispatch-boundary-regression-v0-1"
        ),
        "task_module_root": ".",
        "procedure_id": "governed_canonical_mutation",
        "procedure_not_required_reason": None,
        "handoff_manifest_sha256": "a" * 64,
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
        },
        "assistant_ack_validated": False,
        "next_required_human_boundary": "ASSISTANT_ACK_REQUIRED",
    }


def test_dispatcher_canonical_ack_uses_exact_envelope() -> None:
    ack = dispatch.build_cf10_dispatcher_canonical_ack(
        root=ROOT,
        prepared_execution=prepared(),
        source_state_fingerprint="b" * 64,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a001",
    )
    exact = dispatch._cf09_ack_contract(ROOT)["exact_fields"]
    assert list(ack) == exact
    assert ack["handoff_manifest_sha256"] == "a" * 64
    assert ack["launch_mode"] == "TASK_EXECUTION"
    assert ack["context_fingerprint"] == "b" * 64


def test_exact_first_worker_dispatch_requires_ack(tmp_path: Path) -> None:
    ready = prepared()
    ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
    ready["assistant_ack_validated"] = True
    ready["next_required_human_boundary"] = "EXPLICIT_DISPATCH_DECISION"

    workspace = (
        tmp_path
        / "forprint_system_blueprint/worker-01/"
        "cf10-u180j-a001/workspace/repo"
    )
    workspace.mkdir(parents=True)

    decision = dispatch.authorize_cf10_internal_zero_stage_explicit_dispatch(
        root=ROOT,
        ready_execution=ready,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a001",
        source_state_fingerprint="b" * 64,
        workspace_repo=workspace,
        runtime_provider="github_copilot_cli",
        runtime_model="auto",
    )
    assert decision["explicit_dispatch_decision_recorded"] is True
    assert decision["worker_process_launch_allowed"] is True
    assert decision["canonical_attempt_ledger_append_allowed"] is True
    assert decision["external_dispatch_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["push_allowed"] is False
    assert decision["merge_allowed"] is False
    assert decision["foreign_repository_write_allowed"] is False


def test_wrong_attempt_never_inherits_exception(tmp_path: Path) -> None:
    ready = prepared()
    ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
    ready["assistant_ack_validated"] = True

    workspace = (
        tmp_path
        / "forprint_system_blueprint/worker-01/"
        "cf10-u180j-a003/workspace/repo"
    )
    workspace.mkdir(parents=True)

    with pytest.raises(ValueError, match="exact first attempt"):
        dispatch.authorize_cf10_internal_zero_stage_explicit_dispatch(
            root=ROOT,
            ready_execution=ready,
            worker_id="worker-01",
            attempt_id="cf10-u180j-a003",
            source_state_fingerprint="b" * 64,
            workspace_repo=workspace,
            runtime_provider="github_copilot_cli",
            runtime_model="auto",
        )


def test_unacked_execution_cannot_dispatch(tmp_path: Path) -> None:
    workspace = (
        tmp_path
        / "forprint_system_blueprint/worker-01/"
        "cf10-u180j-a001/workspace/repo"
    )
    workspace.mkdir(parents=True)

    with pytest.raises(ValueError, match="READY_FOR_EXPLICIT_DISPATCH"):
        dispatch.authorize_cf10_internal_zero_stage_explicit_dispatch(
            root=ROOT,
            ready_execution=prepared(),
            worker_id="worker-01",
            attempt_id="cf10-u180j-a001",
            source_state_fingerprint="b" * 64,
            workspace_repo=workspace,
            runtime_provider="github_copilot_cli",
            runtime_model="auto",
        )


def test_cf10_bounded_retry_a002_ack_and_explicit_dispatch(tmp_path) -> None:
    from pathlib import Path

    from scripts.coordination.control_plane import dispatch_intent as dispatch

    root = Path(__file__).resolve().parents[3]
    attempt_id = "cf10-u180j-a002"
    source_state_fingerprint = "ab" * 32

    prepared = dispatch.prepare_cf10_internal_zero_stage_pre_dispatch(
        root=root,
        worker_id="worker-01",
        attempt_id=attempt_id,
        blueprint_ai_trial_ready=False,
    )
    assert prepared["state"] == "AWAITING_ASSISTANT_ACK"

    expected_ack = dispatch.build_cf10_dispatcher_canonical_ack(
        root=root,
        prepared_execution=prepared,
        source_state_fingerprint=source_state_fingerprint,
        worker_id="worker-01",
        attempt_id=attempt_id,
    )

    ready = dispatch.validate_cf09_assistant_ack(
        root=root,
        prepared_execution=prepared,
        assistant_ack=dict(expected_ack),
        expected_ack=expected_ack,
        expected_ack_source="DISPATCHER_CANONICAL_BINDING",
    )
    assert ready["state"] == "READY_FOR_EXPLICIT_DISPATCH"
    assert ready["assistant_ack_validated"] is True

    workspace = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / attempt_id
        / "workspace"
        / "repo"
    )
    workspace.mkdir(parents=True)

    decision = dispatch.authorize_cf10_internal_zero_stage_explicit_dispatch(
        root=root,
        ready_execution=ready,
        worker_id="worker-01",
        attempt_id=attempt_id,
        source_state_fingerprint=source_state_fingerprint,
        workspace_repo=workspace,
        runtime_provider="github_copilot_cli",
        runtime_model="auto",
    )

    assert decision["worker_process_launch_allowed"] is True
    assert decision["canonical_attempt_ledger_append_allowed"] is True
    assert decision["external_dispatch_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["push_allowed"] is False
    assert decision["merge_allowed"] is False
    assert decision["foreign_repository_write_allowed"] is False
    assert decision["automatic_accept_allowed"] is False

    # The successful authorizer return itself proves that both the supplied
    # a002 attempt_id and the exact a002 workspace suffix passed the gate.
    # Do not require extra top-level echo fields that are not part of the
    # explicit-dispatch decision contract.


def test_cf10_canonical_ack_rejects_a003() -> None:
    from pathlib import Path

    import pytest

    from scripts.coordination.control_plane import dispatch_intent as dispatch

    root = Path(__file__).resolve().parents[3]
    prepared = dispatch.prepare_cf10_internal_zero_stage_pre_dispatch(
        root=root,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a002",
        blueprint_ai_trial_ready=False,
    )

    with pytest.raises(ValueError, match="canonical ACK"):
        dispatch.build_cf10_dispatcher_canonical_ack(
            root=root,
            prepared_execution=prepared,
            source_state_fingerprint="ab" * 32,
            worker_id="worker-01",
            attempt_id="cf10-u180j-a003",
        )

# cf10-a003-operator-status-binding-tests-v0-3:start
def test_cf10_operator_status_a003_ack_and_dispatch(tmp_path: Path) -> None:
    attempt_id = "cf10-u180j-a003"
    fingerprint = "cd" * 32
    prepared_a003 = dispatch.prepare_cf10_operator_status_a003_pre_dispatch(
        root=ROOT, worker_id="worker-01", attempt_id=attempt_id,
        blueprint_ai_trial_ready=False,
    )
    assert prepared_a003["state"] == "AWAITING_ASSISTANT_ACK"
    assert prepared_a003["task_prompt_id"] == (
        "cf10-operator-status-surface-self-hardening-v0-1"
    )
    assert prepared_a003["work_front_gate"]["work_front_id"] == (
        "wf-cf10-operator-status-surface-self-hardening-v0-1"
    )
    assert prepared_a003["worker_process_launch_allowed"] is False

    ack = dispatch.build_cf10_operator_status_a003_canonical_ack(
        root=ROOT, prepared_execution=prepared_a003,
        source_state_fingerprint=fingerprint,
        worker_id="worker-01", attempt_id=attempt_id,
    )
    assert list(ack) == dispatch._cf09_ack_contract(ROOT)["exact_fields"]
    assert ack["freshness_ack"]["attempt_id"] == attempt_id

    ready = dispatch.validate_cf09_assistant_ack(
        root=ROOT, prepared_execution=prepared_a003,
        assistant_ack=dict(ack), expected_ack=ack,
        expected_ack_source="DISPATCHER_CANONICAL_BINDING",
    )
    workspace = (
        tmp_path / "forprint_system_blueprint/worker-01" /
        attempt_id / "workspace/repo"
    )
    workspace.mkdir(parents=True)
    decision = dispatch.authorize_cf10_operator_status_a003_explicit_dispatch(
        root=ROOT, ready_execution=ready, worker_id="worker-01",
        attempt_id=attempt_id, source_state_fingerprint=fingerprint,
        workspace_repo=workspace, runtime_provider="github_copilot_cli",
        runtime_model="auto",
    )
    assert decision["binding"]["attempt_id"] == attempt_id
    assert decision["binding"]["work_id"] == "u180j"
    assert decision["worker_process_launch_allowed"] is True
    assert decision["external_dispatch_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["push_allowed"] is False
    assert decision["merge_allowed"] is False
    assert decision["foreign_repository_write_allowed"] is False
    assert decision["automatic_accept_allowed"] is False


def test_cf10_operator_status_a003_rejects_task1_prepared() -> None:
    old = dispatch.prepare_cf10_internal_zero_stage_pre_dispatch(
        root=ROOT, worker_id="worker-01", attempt_id="cf10-u180j-a002",
        blueprint_ai_trial_ready=False,
    )
    with pytest.raises(ValueError, match="outside CF10 a003 binding"):
        dispatch.build_cf10_operator_status_a003_canonical_ack(
            root=ROOT, prepared_execution=old,
            source_state_fingerprint="ef" * 32,
            worker_id="worker-01", attempt_id="cf10-u180j-a003",
        )
# cf10-a003-operator-status-binding-tests-v0-3:end
