from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination import build_worker_invocation as adapter


def _launch_request(path: Path, *, state: str = "AWAITING_OPERATOR_APPROVAL") -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "forprint_launch_request_v0_1",
                "request_id": "request-1",
                "state": state,
                "identity": {
                    "module_id": "logistics_service",
                    "prompt_id": "prompt-1",
                    "task_context_id": "ctx-1",
                    "context_fingerprint_sha256": "a" * 64,
                    "request_fingerprint_sha256": "b" * 64,
                },
                "task_context": {
                    "archive_path": str(path.parent / "context.zip"),
                    "archive_sha256": "c" * 64,
                },
                "repository_revalidation": {
                    "blueprint_head": "blueprint-head",
                    "module_head": "module-head",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _runtime(
    path: Path,
    *,
    working_directory: str = ".",
    required_environment: list[str] | None = None,
) -> Path:
    required_environment = required_environment or []
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "forprint_worker_runtime_v0_1",
                "module_id": "logistics_service",
                "provider_adapter": "CONSOLE_COMMAND",
                "model": "test-model",
                "working_directory": working_directory,
                "timeout_seconds": 900,
                "network_policy": {
                    "mode": "DENY",
                    "allowlist": [],
                },
                "budget": {
                    "max_input_tokens": 1000,
                    "max_output_tokens": 500,
                    "max_total_tokens": 1500,
                    "max_cost": 1.0,
                    "currency": "USD",
                },
                "environment_allowlist": required_environment,
                "required_environment": required_environment,
                "command": {
                    "executable": "worker-cli",
                    "args": [
                        "--model",
                        "{model}",
                        "--context",
                        "{task_context_archive}",
                        "--completion-output",
                        "{completion_output}",
                    ],
                },
                "completion": {
                    "schema_version": "forprint_worker_completion_capture_v0_1",
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_missing_approval_blocks_without_process_start(tmp_path: Path) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    launch = _launch_request(tmp_path / "launch.yaml")
    runtime = _runtime(tmp_path / "runtime.yaml")

    plan = adapter.build_worker_invocation(
        root=tmp_path,
        module_root=module_root,
        launch_request_path=launch,
        runtime_path=runtime,
    )

    assert plan.state == adapter.STATE_BLOCKED
    assert adapter.BLOCKER_APPROVAL_MISSING in plan.blocker_codes
    assert plan.document["execution_boundaries"]["worker_process_started"] is False
    assert plan.document["console_command"]["subprocess_started"] is False


def test_valid_approval_and_runtime_produce_dry_run_ready(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    launch = _launch_request(tmp_path / "launch.yaml")
    runtime = _runtime(tmp_path / "runtime.yaml")
    decision = tmp_path / "decision.yaml"
    decision.write_text(
        yaml.safe_dump(
            {
                "schema_version": "forprint_operator_approval_decision_v0_1",
                "decision_id": "decision-1",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        adapter,
        "_approval_validation",
        lambda **_: (True, [], "decision-1"),
    )

    plan = adapter.build_worker_invocation(
        root=tmp_path,
        module_root=module_root,
        launch_request_path=launch,
        runtime_path=runtime,
        decision_path=decision,
    )

    assert plan.state == adapter.STATE_DRY_RUN_READY
    assert plan.blocker_codes == ()
    assert plan.document["eligibility"]["future_dispatch_eligible"] is True
    assert plan.document["console_command"]["argv"][0] == "worker-cli"
    assert plan.document["console_command"]["shell"] is False
    assert plan.document["execution_boundaries"]["worker_process_start_allowed"] is False


def test_blocked_launch_request_cannot_become_ready_even_with_valid_approval(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    launch = _launch_request(tmp_path / "launch.yaml", state="BLOCKED")
    runtime = _runtime(tmp_path / "runtime.yaml")
    decision = tmp_path / "decision.yaml"
    decision.write_text("decision: fixture\n", encoding="utf-8")
    monkeypatch.setattr(
        adapter,
        "_approval_validation",
        lambda **_: (True, [], "decision-1"),
    )

    plan = adapter.build_worker_invocation(
        root=tmp_path,
        module_root=module_root,
        launch_request_path=launch,
        runtime_path=runtime,
        decision_path=decision,
    )

    assert plan.state == adapter.STATE_BLOCKED
    assert adapter.BLOCKER_LAUNCH_STATE in plan.blocker_codes


def test_runtime_working_directory_cannot_escape_module_root(tmp_path: Path) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    runtime = _runtime(
        tmp_path / "runtime.yaml",
        working_directory="../outside",
    )

    validation = adapter.validate_runtime_config(
        runtime_path=runtime,
        module_root=module_root,
    )

    assert validation.valid is False
    assert any("within module root" in item for item in validation.errors)


def test_environment_values_are_never_serialized(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    launch = _launch_request(tmp_path / "launch.yaml")
    runtime = _runtime(
        tmp_path / "runtime.yaml",
        required_environment=["FORPRINT_TEST_SECRET"],
    )
    decision = tmp_path / "decision.yaml"
    decision.write_text("decision: fixture\n", encoding="utf-8")
    monkeypatch.setenv("FORPRINT_TEST_SECRET", "super-secret-value")
    monkeypatch.setattr(
        adapter,
        "_approval_validation",
        lambda **_: (True, [], "decision-1"),
    )

    plan = adapter.build_worker_invocation(
        root=tmp_path,
        module_root=module_root,
        launch_request_path=launch,
        runtime_path=runtime,
        decision_path=decision,
    )
    rendered = yaml.safe_dump(plan.document, sort_keys=False)

    assert plan.state == adapter.STATE_DRY_RUN_READY
    assert "super-secret-value" not in rendered
    assert (
        plan.document["runtime"]["environment_presence"]["FORPRINT_TEST_SECRET"]
        == "present"
    )
    assert plan.document["console_command"]["secret_values_serialized"] is False


def test_missing_required_environment_blocks(tmp_path: Path, monkeypatch) -> None:
    module_root = tmp_path / "module"
    module_root.mkdir()
    launch = _launch_request(tmp_path / "launch.yaml")
    runtime = _runtime(
        tmp_path / "runtime.yaml",
        required_environment=["FORPRINT_MISSING_SECRET"],
    )
    decision = tmp_path / "decision.yaml"
    decision.write_text("decision: fixture\n", encoding="utf-8")
    monkeypatch.delenv("FORPRINT_MISSING_SECRET", raising=False)
    monkeypatch.setattr(
        adapter,
        "_approval_validation",
        lambda **_: (True, [], "decision-1"),
    )

    plan = adapter.build_worker_invocation(
        root=tmp_path,
        module_root=module_root,
        launch_request_path=launch,
        runtime_path=runtime,
        decision_path=decision,
    )

    assert plan.state == adapter.STATE_BLOCKED
    assert adapter.BLOCKER_ENVIRONMENT_MISSING in plan.blocker_codes
