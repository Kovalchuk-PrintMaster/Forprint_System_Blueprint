from __future__ import annotations

import pytest

from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
from scripts.coordination.control_plane import cf10_training_dispatch
from scripts.coordination.control_plane import governed_worker_cycle as gwc
from scripts.coordination.control_plane.worker_runtime import (
    invocation_adapter,
    launcher,
)

ATTEMPT_ID = "cf10-u180j-test-a001"


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
        ledger,
        "load_contract",
        lambda root: {"fixture": "contract"},
    )


def _plan():
    return {
        "provider": "github_copilot_cli",
        "launch": {
            "argv": ["copilot", "-p", "sensitive-prompt"],
            "cwd": "/tmp/cf10-worker",
            "stdout_path": "/tmp/cf10-worker.stdout",
            "stderr_path": "/tmp/cf10-worker.stderr",
            "timeout_seconds": 30,
        },
    }


def _started(attempt_id=ATTEMPT_ID):
    return {
        "attempt_id": attempt_id,
        "attempt_stage": "STARTED",
        "result_state": "PENDING",
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


def test_invocation_plan_requires_exactly_one_launcher_mapping(monkeypatch):
    _ready(monkeypatch)
    bad = {
        "a": _plan()["launch"],
        "b": _plan()["launch"],
    }

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
        match="exactly one launcher mapping",
    ):
        gwc.launch_authorized_worker_cycle(
            root=".",
            runtime_root="/tmp/runtime",
            task_prompt_id="task",
            attempt_id=ATTEMPT_ID,
            started_record_data=_started(),
        )
