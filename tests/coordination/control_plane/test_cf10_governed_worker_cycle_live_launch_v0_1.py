from __future__ import annotations

import hashlib
import json

import pytest
import yaml

from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
from scripts.coordination.control_plane import cf10_training_dispatch
from scripts.coordination.control_plane import governed_worker_cycle as gwc
from scripts.coordination.control_plane.worker_runtime import (
    invocation_adapter,
    launcher,
)

ATTEMPT_ID = "cf10-u180j-test-a001"


def _governed_worker_context() -> dict:
    return {
        "schema_version": "forprint_governed_worker_context_projection_v0_1",
        "handoff_manifest_sha256": "2" * 64,
        "handoff_source_state_fingerprint": "1" * 64,
        "dependency_health_slice": {
            "dependency_health.yaml": {
                "sha256": "3" * 64,
                "bytes": 128,
            }
        },
        "lifecycle_roadmap_cursor": {
            "roadmap_sync": "IN_SYNC",
            "roadmap_status": "ACTIVE",
            "open_work": {"u180j": "ACTIVE"},
        },
        "resume_coordinates": {
            "work_id": "u180j",
            "work_state": "ACTIVE",
        },
        "expected_result_schema_revision": "0.1.0",
        "execution_bindings": {
            "work_front_or_project_onboard_not_applicable_reason": {
                "work_front_id": "wf-task",
            },
            "execution_profile_revision_for_task_execution": {
                "profile_id": "light-maintenance",
                "revision": "r1",
            },
            "governed_procedure_revision_or_not_required_reason": {
                "procedure_id": "governed_canonical_mutation",
                "revision": "0.1.0",
            },
        },
        "authority": {
            "context_grants_authority": False,
            "dispatch_authority_granted": False,
            "release_authority_granted": False,
            "cross_repository_write_authority_granted": False,
        },
    }


def _governed_worker_context_sha256(value: dict) -> str:
    canonical = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _ready(monkeypatch):
    monkeypatch.setattr(
        gwc,
        "live_facts",
        lambda *args, **kwargs: {"source": "test"},
    )
    monkeypatch.setattr(
        gwc,
        "derive_cycle_projection",
        lambda facts: {"state": "READY_FOR_WORKER_LAUNCH"},
    )
    monkeypatch.setattr(
        gwc,
        "_load_yaml",
        lambda path, label: {
            "git_head": "a" * 40,
            "fingerprint_sha256": "1" * 64,
        },
    )
    monkeypatch.setattr(
        gwc,
        "_assert_frozen_source_state_current",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        ledger,
        "load_contract",
        lambda root: {"fixture": "contract"},
    )


def _plan():
    return {
        "schema_version": "forprint_worker_runtime_launch_invocation_v0_1",
        "argv": ["copilot", "-p", "sensitive-prompt"],
        "workspace_repo": "/tmp/cf10-worker",
        "timeout_seconds": 30,
        "heartbeat_seconds": 15,
        "stall_threshold_seconds": 120.0,
        "paths": {
            "stdout": "/tmp/cf10-worker.stdout",
            "stderr": "/tmp/cf10-worker.stderr",
        },
    }


def _started(attempt_id=ATTEMPT_ID):
    return {
        "attempt_id": attempt_id,
        "attempt_stage": "STARTED",
        "result_state": "PENDING",
    }


def test_launch_uses_keyword_only_live_facts_contract(monkeypatch):
    captured = {}

    def keyword_only_live_facts(
        *,
        root,
        runtime_root,
        task_prompt_id,
        attempt_id,
        worker_id="worker-01",
    ):
        captured.update(
            {
                "root": root,
                "runtime_root": runtime_root,
                "task_prompt_id": task_prompt_id,
                "attempt_id": attempt_id,
                "worker_id": worker_id,
            }
        )
        raise RuntimeError("keyword-only live_facts contract reached")

    monkeypatch.setattr(gwc, "live_facts", keyword_only_live_facts)

    with pytest.raises(
        RuntimeError,
        match="keyword-only live_facts contract reached",
    ):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
        )

    assert captured == {
        "root": ".",
        "runtime_root": "/tmp/runtime",
        "task_prompt_id": "task",
        "attempt_id": ATTEMPT_ID,
        "worker_id": "worker-01",
    }


def test_launch_requires_ready_projection(monkeypatch):
    monkeypatch.setattr(gwc, "live_facts", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        gwc,
        "derive_cycle_projection",
        lambda facts: {"state": "READY_FOR_EXPLICIT_DISPATCH"},
    )
    with pytest.raises(RuntimeError, match="not launch-ready"):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
        )


def test_started_record_must_match_attempt():
    with pytest.raises(RuntimeError, match="identity mismatch"):
        gwc._b2_build_started_record(
            attempt_id=ATTEMPT_ID,
            record_data=_started("different"),
        )


def test_started_record_requires_started_semantics():
    with pytest.raises(RuntimeError, match="attempt_stage"):
        gwc._b2_build_started_record(
            attempt_id=ATTEMPT_ID,
            record_data={
                "attempt_id": ATTEMPT_ID,
                "attempt_stage": "FINISHED",
                "result_state": "SUCCEEDED",
                "event_type": "STARTED",
            },
        )


def test_started_record_requires_pending_result_state():
    with pytest.raises(RuntimeError, match="result_state"):
        gwc._b2_build_started_record(
            attempt_id=ATTEMPT_ID,
            record_data={
                "attempt_id": ATTEMPT_ID,
                "attempt_stage": "STARTED",
                "result_state": "SUCCEEDED",
            },
        )



def test_invocation_context_cannot_override_canonical_cycle_identity(monkeypatch):
    _ready(monkeypatch)

    with pytest.raises(
        RuntimeError,
        match="cannot override canonical cycle keys",
    ):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
            invocation_context={"attempt_id": "other-attempt"},
        )


def test_canonical_ledger_validation_errors_block_process_start(monkeypatch):
    _ready(monkeypatch)
    launched = []

    monkeypatch.setattr(
        invocation_adapter,
        "build_launch_invocation",
        lambda **kwargs: _plan(),
    )
    monkeypatch.setattr(
        invocation_adapter,
        "build_invocation_evidence",
        lambda **kwargs: {"argv_sha256": "abc"},
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: ["missing field: work_front_id"],
    )
    monkeypatch.setattr(
        launcher,
        "launch_process",
        lambda **kwargs: launched.append(kwargs),
    )

    with pytest.raises(
        RuntimeError,
        match="failed canonical ledger validation",
    ):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
        )

    assert launched == []



def test_live_b1_invocation_signature_is_satisfied(monkeypatch):
    _ready(monkeypatch)
    captured = {}

    def exact_builder(
        *,
        root,
        task_context,
        explicit_dispatch_decision,
        attempt_root,
    ):
        captured.update(
            {
                "root": root,
                "task_context": task_context,
                "explicit_dispatch_decision": explicit_dispatch_decision,
                "attempt_root": attempt_root,
            }
        )
        return _plan()

    monkeypatch.setattr(
        invocation_adapter,
        "build_launch_invocation",
        exact_builder,
    )
    monkeypatch.setattr(
        invocation_adapter,
        "build_invocation_evidence",
        lambda invocation: {"argv_sha256": "abc"},
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: [],
    )
    monkeypatch.setattr(
        cf10_training_dispatch,
        "assert_attempt_unused",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        ledger,
        "append_record",
        lambda **kwargs: None,
    )

    def fake_launch(**kwargs):
        kwargs["on_started"]()
        return {"returncode": 0}

    monkeypatch.setattr(launcher, "launch_process", fake_launch)

    task_context = {"task": "bounded"}
    decision = {"decision": "authorized"}
    attempt_root = "/tmp/cf10-attempt"

    result = gwc.launch_authorized_worker_cycle(
        root=".",
        runtime_root="/tmp/runtime",
        task_prompt_id="task",
        attempt_id=ATTEMPT_ID,
        started_record_data=_started(),
        invocation_context={
            "task_context": task_context,
            "explicit_dispatch_decision": decision,
            "attempt_root": attempt_root,
        },
    )

    assert captured["root"] == "."
    assert captured["task_context"] is task_context
    assert captured["explicit_dispatch_decision"] is decision
    assert captured["attempt_root"] == attempt_root
    assert result["state"] == "OBSERVE_WORKER"



def test_started_is_validated_then_appended_only_on_process_start(monkeypatch):
    _ready(monkeypatch)
    events = []

    monkeypatch.setattr(
        invocation_adapter,
        "build_launch_invocation",
        lambda **kwargs: _plan(),
    )
    monkeypatch.setattr(
        invocation_adapter,
        "build_invocation_evidence",
        lambda **kwargs: {
            "argv_sha256": "abc",
            "prompt_sha256": "def",
        },
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: events.append("validate") or [],
    )
    monkeypatch.setattr(
        cf10_training_dispatch,
        "assert_attempt_unused",
        lambda **kwargs: events.append("guard"),
    )
    monkeypatch.setattr(
        ledger,
        "append_record",
        lambda **kwargs: events.append("append"),
    )

    def fake_launch(**kwargs):
        events.append("launcher_enter")
        kwargs["on_started"]()
        events.append("process")
        return {
            "returncode": 0,
            "argv": ["must-not-be-durable"],
            "prompt_text": "must-not-be-durable",
        }

    monkeypatch.setattr(launcher, "launch_process", fake_launch)

    result = gwc.launch_authorized_worker_cycle(
        root=".",
        runtime_root="/tmp/runtime",
        task_prompt_id="task",
        attempt_id=ATTEMPT_ID,
        started_record_data=_started(),
    )

    assert events == [
        "validate",
        "launcher_enter",
        "guard",
        "append",
        "process",
    ]
    assert result["state"] == "OBSERVE_WORKER"
    assert result["started_record_appended"] is True
    assert result["candidate_promotion_allowed"] is False
    assert result["automatic_accept_allowed"] is False
    assert result["commit_allowed"] is False
    assert "argv" not in result["process_result"]
    assert "prompt_text" not in result["process_result"]


def test_no_started_append_when_spawn_fails_before_callback(monkeypatch):
    _ready(monkeypatch)
    appended = []

    monkeypatch.setattr(
        invocation_adapter,
        "build_launch_invocation",
        lambda **kwargs: _plan(),
    )
    monkeypatch.setattr(
        invocation_adapter,
        "build_invocation_evidence",
        lambda **kwargs: {"argv_sha256": "abc"},
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: [],
    )
    monkeypatch.setattr(
        ledger,
        "append_record",
        lambda **kwargs: appended.append(kwargs),
    )
    monkeypatch.setattr(
        launcher,
        "launch_process",
        lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("spawn failed")
        ),
    )

    with pytest.raises(RuntimeError, match="spawn failed"):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
        )

    assert appended == []


def test_duplicate_on_started_is_rejected(monkeypatch):
    _ready(monkeypatch)

    monkeypatch.setattr(
        invocation_adapter,
        "build_launch_invocation",
        lambda **kwargs: _plan(),
    )
    monkeypatch.setattr(
        invocation_adapter,
        "build_invocation_evidence",
        lambda **kwargs: {"argv_sha256": "abc"},
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: [],
    )
    monkeypatch.setattr(
        cf10_training_dispatch,
        "assert_attempt_unused",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        ledger,
        "append_record",
        lambda **kwargs: None,
    )

    def fake_launch(**kwargs):
        kwargs["on_started"]()
        with pytest.raises(RuntimeError, match="more than once"):
            kwargs["on_started"]()
        return {"returncode": 0}

    monkeypatch.setattr(launcher, "launch_process", fake_launch)

    result = gwc.launch_authorized_worker_cycle(
        root=".",
        runtime_root="/tmp/runtime",
        task_prompt_id="task",
        attempt_id=ATTEMPT_ID,
        started_record_data=_started(),
    )
    assert result["started_record_appended"] is True


def test_canonical_b1_plan_maps_to_launcher_kwargs():
    plan = _plan()

    launch = gwc._b2_find_launch_mapping(plan)

    assert launch == {
        "argv": plan["argv"],
        "cwd": plan["workspace_repo"],
        "stdout_path": plan["paths"]["stdout"],
        "stderr_path": plan["paths"]["stderr"],
        "timeout_seconds": 30,
        "heartbeat_seconds": 15,
        "stall_threshold_seconds": 120.0,
    }


def test_canonical_b1_plan_requires_launcher_paths(monkeypatch):
    _ready(monkeypatch)
    bad = _plan()
    del bad["paths"]["stdout"]

    monkeypatch.setattr(
        invocation_adapter,
        "build_launch_invocation",
        lambda **kwargs: bad,
    )
    monkeypatch.setattr(
        invocation_adapter,
        "build_invocation_evidence",
        lambda **kwargs: {"argv_sha256": "abc"},
    )
    monkeypatch.setattr(
        ledger,
        "validate_record_data",
        lambda record, contract: [],
    )

    with pytest.raises(
        RuntimeError,
        match="missing launcher fields",
    ):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
        )
def test_project_native_launch_cycle_requires_explicit_confirmation(
    tmp_path,
) -> None:
    with pytest.raises(
        gwc.GovernedWorkerCycleError,
        match="explicit --confirm-launch is required",
    ):
        gwc.launch_cycle(
            root=tmp_path,
            runtime_root=tmp_path / "runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            confirm=False,
        )


def test_project_native_launch_cycle_persists_process_evidence(
    tmp_path,
    monkeypatch,
) -> None:
    root = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    root.mkdir()
    attempt = (
        runtime
        / gwc.MODULE_ID
        / gwc.WORKER_ID
        / ATTEMPT_ID
    )
    input_dir = attempt / "input"
    input_dir.mkdir(parents=True)
    workspace = attempt / "workspace/repo"
    workspace.mkdir(parents=True)

    source_fp = "1" * 64
    binding = {
        "task_prompt_id": "task",
        "work_front_id": "wf-task",
        "work_front_ref": "coordination/work_fronts/wf_task.yaml",
        "profile_ref": "light-maintenance@r1",
        "procedure_id": "governed_canonical_mutation",
    }
    decision = {
        "binding": {
            "attempt_id": ATTEMPT_ID,
            "worker_id": gwc.WORKER_ID,
            "task_prompt_id": "task",
            "work_front_id": "wf-task",
            "profile_ref": "light-maintenance@r1",
            "procedure_id": "governed_canonical_mutation",
            "runtime_provider": "github_copilot_cli",
            "workspace_repo": str(workspace),
            "governed_worker_context_sha256": (
                _governed_worker_context_sha256(
                    _governed_worker_context()
                )
            ),
        }
    }

    for name, value in {
        "governed_worker_cycle_source_state_v0_1.yaml": {
            "git_head": "a" * 40,
            "fingerprint_sha256": source_fp,
        },
        "governed_worker_cycle_prepared_execution_v0_1.yaml": {
            "handoff_manifest_sha256": "2" * 64,
            "governed_worker_context": _governed_worker_context(),
            "governed_worker_context_sha256": (
                _governed_worker_context_sha256(
                    _governed_worker_context()
                )
            ),
        },
        "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml": decision,
    }.items():
        (input_dir / name).write_text(
            yaml.safe_dump(value, sort_keys=False),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        gwc,
        "_assert_frozen_source_state_current",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    task_context = {
        "source_state": {"fingerprint_sha256": source_fp},
        "task_envelope": {"task_id": "task"},
    }
    monkeypatch.setattr(
        gwc,
        "build_internal_task_context",
        lambda *_args, **_kwargs: task_context,
    )

    captured = {}
    stdout_path = attempt / "logs/provider.stdout.log"
    stdout_path.parent.mkdir(parents=True)
    stdout_path.write_text(
        "framed-result-transport-stub\n",
        encoding="utf-8",
    )

    def fake_launch(**kwargs):
        captured.update(kwargs)
        return {
            "invocation_evidence": {"argv_sha256": "3" * 64},
            "process_result": {
                "process_started": True,
                "return_code": 0,
                "timed_out": False,
                "stdout_path": str(stdout_path),
            },
        }

    monkeypatch.setattr(
        gwc,
        "launch_authorized_worker_cycle",
        fake_launch,
    )

    def fake_materialize(**kwargs):
        assert kwargs["stdout_path"] == str(stdout_path)
        assert kwargs["expected_attempt_id"] == ATTEMPT_ID
        result_path = attempt / "result/worker_result.yaml"
        result_path.parent.mkdir(parents=True)
        result_path.write_text(
            "schema_version: forprint_assistant_handoff_v2_result_v0_1\n"
            f"attempt_id: {ATTEMPT_ID}\n",
            encoding="utf-8",
        )
        return {
            "result_path": str(result_path),
            "validation_passed": True,
        }

    monkeypatch.setattr(
        gwc.worker_result_return,
        "materialize_worker_result",
        fake_materialize,
    )
    monkeypatch.setattr(
        gwc,
        "status",
        lambda **_kwargs: {
            "state": "VALIDATE_CANDIDATE",
            "next_boundary": "CANDIDATE_VALIDATION",
            "attempt_id": ATTEMPT_ID,
            "task_prompt_id": "task",
        },
    )

    result = gwc.launch_cycle(
        root=root,
        runtime_root=runtime,
        task_prompt_id="task",
        attempt_id=ATTEMPT_ID,
        confirm=True,
    )

    started = captured["started_record_data"]
    assert started["attempt_id"] == ATTEMPT_ID
    assert started["work_front_id"] == "wf-task"
    assert started["attempt_stage"] == "STARTED"
    assert started["result_state"] == "PENDING"
    assert started["source_fingerprint"] == source_fp
    assert started["profile_ref_or_revision"] == "light-maintenance@r1"
    assert captured["invocation_context"]["task_context"] is task_context
    assert captured["invocation_context"]["governed_worker_context"] == (
        _governed_worker_context()
    )
    assert (
        captured["invocation_context"]["explicit_dispatch_decision"]
        == decision
    )
    assert captured["invocation_context"]["attempt_root"] == attempt

    evidence_path = (
        attempt
        / "evidence/"
        "governed_worker_cycle_worker_process_result_v0_1.yaml"
    )
    assert evidence_path.is_file()
    evidence = yaml.safe_load(
        evidence_path.read_text(encoding="utf-8")
    )
    assert evidence["process"]["process_started"] is True
    assert evidence["process"]["return_code"] == 0
    assert evidence["candidate_promotion_allowed"] is False
    assert result["state"] == "VALIDATE_CANDIDATE"
    assert result["worker_process_launched"] is True
    assert result["process_return_code"] == 0
# CF10_GOVERNED_WORKER_CONTEXT_DELIVERY_RED_V0_1


def test_project_native_launch_rejects_governed_context_digest_drift(
    tmp_path,
    monkeypatch,
) -> None:
    root = tmp_path / "repo-drift"
    runtime = tmp_path / "runtime-drift"
    root.mkdir()
    attempt = (
        runtime
        / gwc.MODULE_ID
        / gwc.WORKER_ID
        / ATTEMPT_ID
    )
    attempt.mkdir(parents=True)

    source_fp = "1" * 64
    binding = {
        "task_prompt_id": "task",
        "work_front_id": "wf-task",
        "work_front_ref": "coordination/work_fronts/wf_task.yaml",
        "profile_ref": "light-maintenance@r1",
        "procedure_id": "governed_canonical_mutation",
    }
    context = _governed_worker_context()
    context_sha = _governed_worker_context_sha256(context)
    prepared = {
        "handoff_manifest_sha256": "2" * 64,
        "governed_worker_context": context,
        "governed_worker_context_sha256": context_sha,
    }
    decision = {
        "binding": {
            "attempt_id": ATTEMPT_ID,
            "worker_id": gwc.WORKER_ID,
            "task_prompt_id": "task",
            "work_front_id": "wf-task",
            "profile_ref": "light-maintenance@r1",
            "procedure_id": "governed_canonical_mutation",
            "runtime_provider": "github_copilot_cli",
            "workspace_repo": str(attempt / "workspace/repo"),
            "governed_worker_context_sha256": "9" * 64,
        }
    }

    monkeypatch.setattr(
        gwc.training,
        "resolve_training_task",
        lambda **_kwargs: binding,
    )
    monkeypatch.setattr(
        gwc,
        "build_internal_task_context",
        lambda *_args, **_kwargs: {
            "source_state": {"fingerprint_sha256": source_fp},
            "task_envelope": {"task_id": "task"},
        },
    )

    with pytest.raises(
        gwc.GovernedWorkerCycleError,
        match="governed Worker context",
    ):
        gwc._project_native_started_record(
            canonical=root,
            attempt=attempt,
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            worker_id=gwc.WORKER_ID,
            source_state={"fingerprint_sha256": source_fp},
            prepared_execution=prepared,
            explicit_dispatch_decision=decision,
        )
