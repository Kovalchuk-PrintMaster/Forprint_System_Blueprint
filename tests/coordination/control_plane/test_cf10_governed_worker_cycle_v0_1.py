from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import governed_worker_cycle as cycle


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
    )


def facts(**overrides):
    value = {
        "task_resolved": False,
        "workspace_prepared": False,
        "assistant_ack_validated": False,
        "explicit_dispatch_authorized": False,
        "worker_process_started": False,
        "worker_process_finished": False,
        "candidate_validation_passed": False,
        "handoff_validated": False,
        "attempt_terminal_pass": False,
        "attempt_terminal_failed": False,
        "operator_review_passed": False,
        "candidate_promoted": False,
        "canonical_validation_passed": False,
        "publication_approved": False,
        "commit_performed": False,
        "remote_containment_verified": False,
        "blocked": False,
    }
    value.update(overrides)
    return value


def test_empty_facts_start_at_resolve_task() -> None:
    result = cycle.derive_cycle_projection(facts())
    assert result["state"] == "RESOLVE_TASK"
    assert result["next_boundary"] == "RESOLVE_AUTHORITATIVE_TASK"
    assert result["derived_non_authoritative"] is True
    assert all(value is False for value in result["authority"].values())


def test_prepared_cycle_stops_at_assistant_ack() -> None:
    result = cycle.derive_cycle_projection(
        facts(task_resolved=True, workspace_prepared=True)
    )
    assert result["state"] == "AWAITING_ASSISTANT_ACK"
    assert result["next_boundary"] == "EXPLICIT_ASSISTANT_ACK"


def test_terminal_pass_stops_at_operator_review() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
        )
    )
    assert result["state"] == "AWAITING_OPERATOR_REVIEW"
    assert result["next_boundary"] == "OPERATOR_REVIEW"


def test_promoted_candidate_requires_canonical_validation() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
            operator_review_passed=True,
            candidate_promoted=True,
        )
    )
    assert result["state"] == "CANONICAL_VALIDATION"


def test_canonical_validation_stops_before_publication() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
            operator_review_passed=True,
            candidate_promoted=True,
            canonical_validation_passed=True,
        )
    )
    assert result["state"] == "AWAITING_PUBLICATION_APPROVAL"
    assert result["next_boundary"] == "PUBLICATION_APPROVAL"


def test_remote_containment_is_terminal_published_state() -> None:
    result = cycle.derive_cycle_projection(
        facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
            worker_process_started=True,
            worker_process_finished=True,
            candidate_validation_passed=True,
            handoff_validated=True,
            attempt_terminal_pass=True,
            operator_review_passed=True,
            candidate_promoted=True,
            canonical_validation_passed=True,
            publication_approved=True,
            commit_performed=True,
            remote_containment_verified=True,
        )
    )
    assert result["state"] == "PUBLISHED"


def test_impossible_state_fails_closed_to_unknown() -> None:
    result = cycle.derive_cycle_projection(
        facts(candidate_promoted=True)
    )
    assert result["state"] == "UNKNOWN"
    assert result["contradictions"]
    assert result["next_boundary"] == (
        "INSPECT_CONTRADICTORY_OR_INSUFFICIENT_EVIDENCE"
    )
def _prepared_refresh_attempt(
    *,
    root: Path,
    runtime_root: Path,
    attempt_id: str,
    binding: dict,
    source_head: str,
    source_fp: str,
) -> Path:
    attempt = (
        runtime_root
        / cycle.MODULE_ID
        / cycle.WORKER_ID
        / attempt_id
    )
    write_yaml(
        root / binding["work_front_ref"],
        {
            "work_front_id": binding["work_front_id"],
            "scope": ["target.py"],
        },
    )
    write_yaml(
        attempt / "manifest.yaml",
        {
            "attempt_id": attempt_id,
            "workspace_state": "PROVISIONED_NOT_DISPATCHED",
            "assistant_ack_validated": False,
            "explicit_dispatch_decision_recorded": False,
            "dispatch_authority_granted": False,
            "worker_launch_performed": False,
            "canonical_attempt_ledger_appended": False,
        },
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_prepared_execution_v0_1.yaml",
        {
            "state": "AWAITING_ASSISTANT_ACK",
            "assistant_ack_validated": False,
            "attempt_id": attempt_id,
            "worker_id": cycle.WORKER_ID,
            "cf10_training_binding": binding,
        },
    )
    write_yaml(
        attempt / "input/governed_worker_cycle_expected_ack_v0_1.yaml",
        {"ack": "canonical"},
    )
    write_yaml(
        attempt / "input/governed_worker_cycle_source_state_v0_1.yaml",
        {
            "git_head": source_head,
            "fingerprint_sha256": source_fp,
            "durable_dirty_paths": [],
        },
    )
    return attempt


def test_refresh_cycle_archives_stale_pre_ack_and_reprepares(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a099"
    task_prompt_id = "task-refresh"
    old_head = "a" * 40
    new_head = "b" * 40
    old_fp = "1" * 64
    new_fp = "2" * 64
    binding = {
        "task_prompt_id": task_prompt_id,
        "task_ref": (
            "coordination/internal_work/blueprint/worker_tasks/task.yaml"
        ),
        "work_front_id": "wf-refresh",
        "work_front_ref": "coordination/work_fronts/wf_refresh.yaml",
    }
    attempt = _prepared_refresh_attempt(
        root=root,
        runtime_root=runtime,
        attempt_id=attempt_id,
        binding=binding,
        source_head=old_head,
        source_fp=old_fp,
    )

    monkeypatch.setattr(
        cycle.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        cycle.training,
        "assert_attempt_unused",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        cycle.training,
        "build_training_canonical_ack",
        lambda **_kwargs: {"ack": "canonical"},
    )
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": new_head,
            "fingerprint_sha256": new_fp,
            "durable_dirty_paths": [],
        },
    )
    monkeypatch.setattr(
        cycle,
        "_git_is_ancestor",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        cycle,
        "_git_output",
        lambda *_args, **_kwargs: "",
    )

    def fake_prepare_cycle(**_kwargs):
        refreshed_attempt = (
            runtime
            / cycle.MODULE_ID
            / cycle.WORKER_ID
            / attempt_id
        )
        refreshed_attempt.mkdir(parents=True)
        return {
            "source_head": new_head,
            "source_state_fingerprint": new_fp,
        }

    monkeypatch.setattr(cycle, "prepare_cycle", fake_prepare_cycle)

    result = cycle.refresh_cycle(
        root=root,
        runtime_root=runtime,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
    )

    archive = Path(result["superseded_runtime_archive"])
    assert archive == attempt.parent / (
        attempt_id
        + "__predispatch_superseded__"
        + old_head[:7]
        + "_"
        + old_fp[:12]
        + "_to_"
        + new_head[:7]
        + "_"
        + new_fp[:12]
    )
    assert archive.is_dir()
    assert (
        archive
        / "evidence/"
        "governed_worker_cycle_predispatch_supersession_v0_1.yaml"
    ).is_file()
    assert result["refresh_performed"] is True
    assert result["state"] == "AWAITING_ASSISTANT_ACK"
    assert result["source_head"] == new_head
    assert result["worker_launch_performed"] is False


def test_refresh_cycle_refuses_relevant_committed_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a100"
    task_prompt_id = "task-refresh"
    binding = {
        "task_prompt_id": task_prompt_id,
        "task_ref": (
            "coordination/internal_work/blueprint/worker_tasks/task.yaml"
        ),
        "work_front_id": "wf-refresh",
        "work_front_ref": "coordination/work_fronts/wf_refresh.yaml",
    }
    attempt = _prepared_refresh_attempt(
        root=root,
        runtime_root=runtime,
        attempt_id=attempt_id,
        binding=binding,
        source_head="a" * 40,
        source_fp="1" * 64,
    )

    monkeypatch.setattr(
        cycle.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        cycle.training,
        "assert_attempt_unused",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        cycle.training,
        "build_training_canonical_ack",
        lambda **_kwargs: {"ack": "canonical"},
    )
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": "b" * 40,
            "fingerprint_sha256": "2" * 64,
            "durable_dirty_paths": [],
        },
    )
    monkeypatch.setattr(
        cycle,
        "_git_is_ancestor",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        cycle,
        "_git_output",
        lambda *_args, **_kwargs: "target.py",
    )

    with pytest.raises(
        cycle.GovernedWorkerCycleError,
        match="execution-relevant source changed",
    ):
        cycle.refresh_cycle(
            root=root,
            runtime_root=runtime,
            task_prompt_id=task_prompt_id,
            attempt_id=attempt_id,
        )

    assert attempt.is_dir()
    assert not list(
        attempt.parent.glob(
            attempt_id + "__predispatch_superseded__*"
        )
    )


def test_refresh_cycle_refuses_after_ack_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a101"
    task_prompt_id = "task-refresh"
    binding = {
        "task_prompt_id": task_prompt_id,
        "task_ref": (
            "coordination/internal_work/blueprint/worker_tasks/task.yaml"
        ),
        "work_front_id": "wf-refresh",
        "work_front_ref": "coordination/work_fronts/wf_refresh.yaml",
    }
    attempt = _prepared_refresh_attempt(
        root=root,
        runtime_root=runtime,
        attempt_id=attempt_id,
        binding=binding,
        source_head="a" * 40,
        source_fp="1" * 64,
    )
    write_yaml(
        attempt / "input/governed_worker_cycle_ready_execution_v0_1.yaml",
        {"state": "READY_FOR_EXPLICIT_DISPATCH"},
    )

    monkeypatch.setattr(
        cycle.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        cycle.training,
        "assert_attempt_unused",
        lambda **_kwargs: None,
    )

    with pytest.raises(
        cycle.GovernedWorkerCycleError,
        match="ACK/dispatch artifact",
    ):
        cycle.refresh_cycle(
            root=root,
            runtime_root=runtime,
            task_prompt_id=task_prompt_id,
            attempt_id=attempt_id,
        )
def test_refresh_cycle_restores_old_runtime_and_preserves_evidence_on_prepare_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a102"
    task_prompt_id = "task-refresh"
    old_head = "a" * 40
    new_head = "b" * 40
    old_fp = "1" * 64
    new_fp = "2" * 64
    binding = {
        "task_prompt_id": task_prompt_id,
        "task_ref": (
            "coordination/internal_work/blueprint/worker_tasks/task.yaml"
        ),
        "work_front_id": "wf-refresh",
        "work_front_ref": "coordination/work_fronts/wf_refresh.yaml",
    }
    attempt = _prepared_refresh_attempt(
        root=root,
        runtime_root=runtime,
        attempt_id=attempt_id,
        binding=binding,
        source_head=old_head,
        source_fp=old_fp,
    )

    monkeypatch.setattr(
        cycle.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        cycle.training,
        "assert_attempt_unused",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        cycle.training,
        "build_training_canonical_ack",
        lambda **_kwargs: {"ack": "canonical"},
    )
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": new_head,
            "fingerprint_sha256": new_fp,
            "durable_dirty_paths": [],
        },
    )
    monkeypatch.setattr(
        cycle,
        "_git_is_ancestor",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        cycle,
        "_git_output",
        lambda *_args, **_kwargs: "",
    )

    def fail_prepare_cycle(**_kwargs):
        raise RuntimeError("synthetic prepare failure")

    monkeypatch.setattr(cycle, "prepare_cycle", fail_prepare_cycle)

    with pytest.raises(RuntimeError, match="synthetic prepare failure"):
        cycle.refresh_cycle(
            root=root,
            runtime_root=runtime,
            task_prompt_id=task_prompt_id,
            attempt_id=attempt_id,
        )

    assert attempt.is_dir()
    assert not list(
        attempt.parent.glob(
            attempt_id + "__predispatch_superseded__*"
        )
    )
    evidence = (
        attempt
        / "evidence/"
        "governed_worker_cycle_predispatch_supersession_v0_1.yaml"
    )
    assert evidence.is_file()
    value = yaml.safe_load(evidence.read_text(encoding="utf-8"))
    assert value["old_source_head"] == old_head
    assert value["new_source_head"] == new_head
    assert value["assistant_ack_validated"] is False
    assert value["worker_launch_performed"] is False
def test_refresh_cycle_same_head_dirty_drift_uses_unique_archive_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a103"
    task_prompt_id = "task-refresh"
    same_head = "a" * 40
    old_fp = "1" * 64
    new_fp = "2" * 64
    binding = {
        "task_prompt_id": task_prompt_id,
        "task_ref": (
            "coordination/internal_work/blueprint/worker_tasks/task.yaml"
        ),
        "work_front_id": "wf-refresh",
        "work_front_ref": "coordination/work_fronts/wf_refresh.yaml",
    }
    attempt = _prepared_refresh_attempt(
        root=root,
        runtime_root=runtime,
        attempt_id=attempt_id,
        binding=binding,
        source_head=same_head,
        source_fp=old_fp,
    )

    monkeypatch.setattr(
        cycle.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        cycle.training,
        "assert_attempt_unused",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        cycle.training,
        "build_training_canonical_ack",
        lambda **_kwargs: {"ack": "canonical"},
    )
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": same_head,
            "fingerprint_sha256": new_fp,
            "durable_dirty_paths": ["unrelated/new-file.yaml"],
        },
    )

    def fake_prepare_cycle(**_kwargs):
        refreshed_attempt = (
            runtime
            / cycle.MODULE_ID
            / cycle.WORKER_ID
            / attempt_id
        )
        refreshed_attempt.mkdir(parents=True)
        return {
            "source_head": same_head,
            "source_state_fingerprint": new_fp,
        }

    monkeypatch.setattr(cycle, "prepare_cycle", fake_prepare_cycle)

    result = cycle.refresh_cycle(
        root=root,
        runtime_root=runtime,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
    )

    archive = Path(result["superseded_runtime_archive"])
    assert archive.name == (
        attempt_id
        + "__predispatch_superseded__"
        + same_head[:7]
        + "_"
        + old_fp[:12]
        + "_to_"
        + same_head[:7]
        + "_"
        + new_fp[:12]
    )
    assert archive.is_dir()
    evidence = yaml.safe_load(
        (
            archive
            / "evidence/"
            "governed_worker_cycle_predispatch_supersession_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )
    assert evidence["refresh_ordinal"] == 1

def test_refresh_cycle_archive_collision_gets_monotonic_suffix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a104"
    task_prompt_id = "task-refresh"
    old_head = "a" * 40
    new_head = "b" * 40
    old_fp = "1" * 64
    new_fp = "2" * 64
    binding = {
        "task_prompt_id": task_prompt_id,
        "task_ref": (
            "coordination/internal_work/blueprint/worker_tasks/task.yaml"
        ),
        "work_front_id": "wf-refresh",
        "work_front_ref": "coordination/work_fronts/wf_refresh.yaml",
    }
    attempt = _prepared_refresh_attempt(
        root=root,
        runtime_root=runtime,
        attempt_id=attempt_id,
        binding=binding,
        source_head=old_head,
        source_fp=old_fp,
    )
    archive_base = attempt.parent / (
        attempt_id
        + "__predispatch_superseded__"
        + old_head[:7]
        + "_"
        + old_fp[:12]
        + "_to_"
        + new_head[:7]
        + "_"
        + new_fp[:12]
    )
    archive_base.mkdir(parents=True)

    monkeypatch.setattr(
        cycle.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        cycle.training,
        "assert_attempt_unused",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        cycle.training,
        "build_training_canonical_ack",
        lambda **_kwargs: {"ack": "canonical"},
    )
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": new_head,
            "fingerprint_sha256": new_fp,
            "durable_dirty_paths": [],
        },
    )
    monkeypatch.setattr(
        cycle,
        "_git_is_ancestor",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        cycle,
        "_git_output",
        lambda *_args, **_kwargs: "",
    )

    def fake_prepare_cycle(**_kwargs):
        refreshed_attempt = (
            runtime
            / cycle.MODULE_ID
            / cycle.WORKER_ID
            / attempt_id
        )
        refreshed_attempt.mkdir(parents=True)
        return {
            "source_head": new_head,
            "source_state_fingerprint": new_fp,
        }

    monkeypatch.setattr(cycle, "prepare_cycle", fake_prepare_cycle)

    result = cycle.refresh_cycle(
        root=root,
        runtime_root=runtime,
        task_prompt_id=task_prompt_id,
        attempt_id=attempt_id,
    )

    archive = Path(result["superseded_runtime_archive"])
    assert archive == Path(str(archive_base) + "__r02")
    evidence = yaml.safe_load(
        (
            archive
            / "evidence/"
            "governed_worker_cycle_predispatch_supersession_v0_1.yaml"
        ).read_text(encoding="utf-8")
    )
    assert evidence["refresh_ordinal"] == 2
def test_source_freshness_assertion_rejects_stale_fingerprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen = {
        "git_head": "a" * 40,
        "fingerprint_sha256": "1" * 64,
    }
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": "a" * 40,
            "fingerprint_sha256": "2" * 64,
        },
    )

    with pytest.raises(
        cycle.GovernedWorkerCycleError,
        match="frozen source state is stale",
    ):
        cycle._assert_frozen_source_state_current(
            tmp_path,
            frozen,
            boundary="test boundary",
        )


def test_ack_refuses_stale_source_before_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a105"
    attempt = (
        runtime
        / cycle.MODULE_ID
        / cycle.WORKER_ID
        / attempt_id
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_prepared_execution_v0_1.yaml",
        {"attempt_id": attempt_id},
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_expected_ack_v0_1.yaml",
        {"ack": "canonical"},
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_source_state_v0_1.yaml",
        {
            "git_head": "a" * 40,
            "fingerprint_sha256": "1" * 64,
        },
    )

    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": "b" * 40,
            "fingerprint_sha256": "2" * 64,
        },
    )

    def should_not_validate(**_kwargs):
        raise AssertionError("ACK validator must not run for stale source")

    monkeypatch.setattr(
        cycle.training,
        "validate_training_assistant_ack",
        should_not_validate,
    )

    with pytest.raises(
        cycle.GovernedWorkerCycleError,
        match="assistant ACK: frozen source state is stale",
    ):
        cycle.confirm_assistant_ack(
            root=root,
            runtime_root=runtime,
            attempt_id=attempt_id,
            confirm=True,
        )

    assert not (
        attempt
        / "input/governed_worker_cycle_ready_execution_v0_1.yaml"
    ).exists()


def test_authorize_dispatch_refuses_stale_source_before_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a106"
    attempt = (
        runtime
        / cycle.MODULE_ID
        / cycle.WORKER_ID
        / attempt_id
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_ready_execution_v0_1.yaml",
        {"state": "READY_FOR_EXPLICIT_DISPATCH"},
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_source_state_v0_1.yaml",
        {
            "git_head": "a" * 40,
            "fingerprint_sha256": "1" * 64,
        },
    )
    write_yaml(
        attempt / "manifest.yaml",
        {
            "workspace_repo": str(
                attempt / "workspace/repo"
            ),
        },
    )

    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": "b" * 40,
            "fingerprint_sha256": "2" * 64,
        },
    )

    def should_not_authorize(**_kwargs):
        raise AssertionError(
            "dispatch authorization must not run for stale source"
        )

    monkeypatch.setattr(
        cycle.training,
        "authorize_training_explicit_dispatch",
        should_not_authorize,
    )

    with pytest.raises(
        cycle.GovernedWorkerCycleError,
        match=(
            "explicit dispatch authorization: "
            "frozen source state is stale"
        ),
    ):
        cycle.authorize_dispatch(
            root=root,
            runtime_root=runtime,
            attempt_id=attempt_id,
            confirm=True,
        )

    assert not (
        attempt
        / "input/"
        "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml"
    ).exists()


def test_launch_refuses_stale_source_before_invocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt_id = "cf10-u180j-a107"
    task_prompt_id = "task-refresh"
    attempt = (
        runtime
        / cycle.MODULE_ID
        / cycle.WORKER_ID
        / attempt_id
    )
    write_yaml(
        attempt
        / "input/governed_worker_cycle_source_state_v0_1.yaml",
        {
            "git_head": "a" * 40,
            "fingerprint_sha256": "1" * 64,
        },
    )

    monkeypatch.setattr(
        cycle,
        "live_facts",
        lambda **_kwargs: facts(
            task_resolved=True,
            workspace_prepared=True,
            assistant_ack_validated=True,
            explicit_dispatch_authorized=True,
        ),
    )
    monkeypatch.setattr(
        cycle,
        "derive_cycle_projection",
        lambda _facts: {
            "state": "READY_FOR_WORKER_LAUNCH",
            "next_boundary": "WORKER_PROCESS_LAUNCH",
        },
    )
    monkeypatch.setattr(
        cycle,
        "build_source_state",
        lambda _root: {
            "git_head": "b" * 40,
            "fingerprint_sha256": "2" * 64,
        },
    )

    with pytest.raises(
        cycle.GovernedWorkerCycleError,
        match="Worker process launch: frozen source state is stale",
    ):
        cycle.launch_authorized_worker_cycle(
            root=root,
            runtime_root=runtime,
            task_prompt_id=task_prompt_id,
            attempt_id=attempt_id,
            started_record_data={},
        )
