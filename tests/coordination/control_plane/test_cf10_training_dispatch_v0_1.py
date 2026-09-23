from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import cf10_training_dispatch as training

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "cf10-verification-tier-self-hardening-v0-1"


def _prepared(binding: dict) -> dict:
    return {
        "schema_version": "forprint_cf09_dispatcher_pre_execution_envelope_v0_1",
        "mode": "TASK_EXECUTION",
        "state": "AWAITING_ASSISTANT_ACK",
        "assistant_ack_validated": False,
        "module": "forprint_system_blueprint",
        "work_front_id": binding["work_front_ref"],
        "execution_profile_ref": binding["execution_profile"],
        "task_prompt_id": binding["task_prompt_id"],
        "task_module_root": ".",
        "procedure_id": binding["procedure_id"],
        "procedure_not_required_reason": None,
        "handoff_manifest_sha256": "1" * 64,
        "work_front_gate": {
            "validated": True,
            "work_front_id": binding["work_front_id"],
            "work_front_path": binding["work_front_ref"],
        },
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "worker_dispatch_performed": False,
            "external_dispatch_allowed": False,
            "release_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
        },
        "next_required_human_boundary": "ASSISTANT_ACK_REQUIRED",
        "cf10_training_binding": binding,
        "worker_id": "worker-01",
        "attempt_id": "cf10-u180j-a004",
        "workspace_required_before_dispatch": True,
        "worker_process_launch_allowed": False,
        "canonical_attempt_ledger_append_allowed": False,
    }


def test_resolve_materialized_task3_from_canonical_queue() -> None:
    binding = training.resolve_training_task(root=ROOT, task_prompt_id=TASK_ID)

    assert binding["work_id"] == "u180j"
    assert binding["training_task_id"] == "verification_tier_self_hardening"
    assert binding["training_order"] == 30
    assert binding["work_front_id"] == (
        "wf-cf10-verification-tier-self-hardening-v0-1"
    )
    assert binding["execution_profile"] == "light-maintenance"
    assert binding["profile_ref"] == "light-maintenance@r1"
    assert binding["procedure_id"] == "governed_canonical_mutation"
    assert binding["candidate_only"] is True


def test_attempt_history_reuse_is_rejected(tmp_path: Path) -> None:
    store = tmp_path / "ledger"
    store.mkdir()
    (store / "old.yaml").write_text(
        yaml.safe_dump(
            {
                "attempt_id": "cf10-u180j-a004",
                "recorded_at": "2026-09-23T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        training.CF10TrainingDispatchError,
        match="already exists in immutable ledger history",
    ):
        training.assert_attempt_unused(
            root=ROOT,
            attempt_id="cf10-u180j-a004",
            store_override=store,
        )


def test_prepare_delegates_to_generic_task_execution_and_stops_at_ack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed = {}

    def fake_prepare(**kwargs):
        observed.update(kwargs)
        binding = training.resolve_training_task(
            root=ROOT,
            task_prompt_id=TASK_ID,
        )
        return _prepared(binding)

    monkeypatch.setattr(
        training.dispatch,
        "prepare_cf09_task_execution",
        fake_prepare,
    )
    store = tmp_path / "empty-ledger"
    store.mkdir()

    prepared = training.prepare_training_pre_dispatch(
        root=ROOT,
        task_prompt_id=TASK_ID,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a004",
        ledger_store_override=store,
    )

    assert observed["work_front"] == (
        "coordination/work_fronts/"
        "cf10_verification_tier_self_hardening_v0_1.yaml"
    )
    assert observed["execution_profile"] == "light-maintenance"
    assert observed["procedure_id"] == "governed_canonical_mutation"
    assert prepared["state"] == "AWAITING_ASSISTANT_ACK"
    assert prepared["assistant_ack_validated"] is False
    assert prepared["worker_process_launch_allowed"] is False
    assert prepared["canonical_attempt_ledger_append_allowed"] is False


def test_canonical_ack_is_exactly_bound_to_task3(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = training.resolve_training_task(root=ROOT, task_prompt_id=TASK_ID)
    prepared = _prepared(binding)
    monkeypatch.setattr(training, "_sha256_file", lambda _path: "a" * 64)

    ack = training.build_training_canonical_ack(
        root=ROOT,
        prepared_execution=prepared,
        source_state_fingerprint="b" * 64,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a004",
    )

    assert ack["launch_mode"] == "TASK_EXECUTION"
    assert ack["work_front_ack"]["work_front_id"] == binding["work_front_id"]
    assert ack["profile_ack"]["profile_ref"] == "light-maintenance@r1"
    assert ack["freshness_ack"]["attempt_id"] == "cf10-u180j-a004"
    assert ack["authority_ack"]["authority_widening"] is False


def test_ack_validation_delegates_to_existing_generic_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = training.resolve_training_task(root=ROOT, task_prompt_id=TASK_ID)
    prepared = _prepared(binding)
    expected = {"opaque": "ack"}
    observed = {}

    def fake_validate(**kwargs):
        observed.update(kwargs)
        ready = dict(kwargs["prepared_execution"])
        ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
        ready["assistant_ack_validated"] = True
        return ready

    monkeypatch.setattr(
        training.dispatch,
        "validate_cf09_assistant_ack",
        fake_validate,
    )

    ready = training.validate_training_assistant_ack(
        root=ROOT,
        prepared_execution=prepared,
        assistant_ack=expected,
        expected_ack=expected,
    )

    assert observed["expected_ack_source"] == "DISPATCHER_CANONICAL_BINDING"
    assert ready["state"] == "READY_FOR_EXPLICIT_DISPATCH"
    assert ready["assistant_ack_validated"] is True


def test_explicit_dispatch_requires_validated_ack(tmp_path: Path) -> None:
    binding = training.resolve_training_task(root=ROOT, task_prompt_id=TASK_ID)
    prepared = _prepared(binding)
    store = tmp_path / "empty-ledger"
    store.mkdir()
    workspace = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / "cf10-u180j-a004"
        / "workspace"
        / "repo"
    )
    workspace.mkdir(parents=True)

    with pytest.raises(
        training.CF10TrainingDispatchError,
        match="READY_FOR_EXPLICIT_DISPATCH",
    ):
        training.authorize_training_explicit_dispatch(
            root=ROOT,
            ready_execution=prepared,
            worker_id="worker-01",
            attempt_id="cf10-u180j-a004",
            source_state_fingerprint="c" * 64,
            workspace_repo=workspace,
            runtime_provider="github_copilot_cli",
            runtime_model="auto",
            ledger_store_override=store,
        )


def test_explicit_dispatch_binds_exact_task_attempt_workspace_and_runtime(
    tmp_path: Path,
) -> None:
    binding = training.resolve_training_task(root=ROOT, task_prompt_id=TASK_ID)
    ready = _prepared(binding)
    ready["state"] = "READY_FOR_EXPLICIT_DISPATCH"
    ready["assistant_ack_validated"] = True

    store = tmp_path / "empty-ledger"
    store.mkdir()
    workspace = (
        tmp_path
        / "forprint_system_blueprint"
        / "worker-01"
        / "cf10-u180j-a004"
        / "workspace"
        / "repo"
    )
    workspace.mkdir(parents=True)

    decision = training.authorize_training_explicit_dispatch(
        root=ROOT,
        ready_execution=ready,
        worker_id="worker-01",
        attempt_id="cf10-u180j-a004",
        source_state_fingerprint="d" * 64,
        workspace_repo=workspace,
        runtime_provider="github_copilot_cli",
        runtime_model="auto",
        ledger_store_override=store,
    )

    assert decision["decision"] == "ALLOW_EXACT_CF10_TRAINING_WORKER_LAUNCH"
    assert decision["binding"]["task_prompt_id"] == TASK_ID
    assert decision["binding"]["training_task_id"] == (
        "verification_tier_self_hardening"
    )
    assert decision["binding"]["training_order"] == 30
    assert decision["binding"]["attempt_id"] == "cf10-u180j-a004"
    assert decision["binding"]["workspace_repo"] == str(workspace.resolve())
    assert decision["binding"]["runtime_provider"] == "github_copilot_cli"
    assert decision["binding"]["runtime_model"] == "auto"
    assert decision["worker_process_launch_allowed"] is True
    assert decision["canonical_attempt_ledger_append_allowed"] is True
    assert decision["external_dispatch_allowed"] is False
    assert decision["foreign_repository_write_allowed"] is False
    assert decision["push_allowed"] is False
    assert decision["merge_allowed"] is False
    assert decision["release_allowed"] is False
    assert decision["automatic_accept_allowed"] is False
    assert decision["grants_broad_dispatch_authority"] is False
