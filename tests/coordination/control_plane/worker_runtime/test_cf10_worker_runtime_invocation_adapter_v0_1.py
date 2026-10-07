from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime import invocation_adapter as adapter


def _context() -> dict:
    return {
        "task_id": "cf10-fixture-task-v0-1",
        "module_id": "forprint_system_blueprint",
        "authority": {
            "context_grants_authority": False,
            "execution_authority_source": "WORK_FRONT",
            "dispatch_authority_conferred": False,
            "release_authority_conferred": False,
            "foreign_write_authority_conferred": False,
        },
        "task_envelope": {
            "schema_version": "forprint_worker_task_envelope_v0_1",
            "task_id": "cf10-fixture-task-v0-1",
            "module_id": "forprint_system_blueprint",
            "source": {
                "type": "MANUAL_INTERNAL",
                "artifact_ref": (
                    "coordination/internal_work/blueprint/worker_tasks/"
                    "cf10_fixture_task_v0_1.yaml"
                ),
            },
            "work": {
                "work_id": "u180j",
                "work_front_id": "wf-cf10-fixture-v0-1",
            },
            "objective": "Exercise the generic runtime invocation bridge.",
            "instructions": [
                "Modify only the canonical fixture target.",
                "Run focused validation.",
            ],
            "acceptance": ["Focused validation passes."],
            "stop_conditions": ["Authority widening is required."],
            "execution_profile": {
                "profile_id": "light-maintenance",
                "revision": "r1",
            },
            "procedure": {
                "procedure_id": "governed_canonical_mutation",
                "revision": "0.1.0",
            },
            "authority": {
                "execution_authority_source": "WORK_FRONT",
                "task_envelope_grants_authority": False,
                "widening_requested": False,
            },
        },
    }


def _decision(workspace: Path, *, provider: str = "github_copilot_cli") -> dict:
    return {
        "schema_version": "forprint_cf10_internal_explicit_dispatch_decision_v0_1",
        "decision_id": "d" * 64,
        "decision": "ALLOW_EXACT_CF10_TRAINING_WORKER_LAUNCH",
        "binding": {
            "work_id": "u180j",
            "worker_id": "worker-01",
            "attempt_id": "cf10-u180j-a999",
            "task_prompt_id": "cf10-fixture-task-v0-1",
            "training_task_id": "fixture",
            "training_order": 999,
            "source_state_fingerprint": "a" * 64,
            "work_front_id": "wf-cf10-fixture-v0-1",
            "work_front_ref": "coordination/work_fronts/cf10_fixture_v0_1.yaml",
            "profile_ref": "light-maintenance@r1",
            "procedure_id": "governed_canonical_mutation",
            "runtime_provider": provider,
            "runtime_model": "auto",
            "workspace_repo": str(workspace),
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


def _runtime_config() -> dict:
    return {
        "module_id": "forprint_system_blueprint",
        "provider_adapter": "CONSOLE_COMMAND",
        "working_directory": "ATTEMPT_WORKSPACE_REPO",
        "network_policy": "ALLOW",
        "timeout_seconds": 900,
        "command": {
            "provider_id": "github_copilot_cli",
            "runtime_id": "github_copilot_cli",
            "executable": "/usr/local/bin/copilot",
            "base_argv": ["/usr/local/bin/copilot"],
            "representation": "ARGV_NO_SHELL",
            "shell": False,
            "prompt_transport": "provider_adapter_owned",
        },
        "budget": {
            "currency": "USD",
            "max_cost": 0.0,
            "provider_specific": {"max_ai_credits": 30},
        },
        "tool_policy": {
            "automatic_accept_allowed": False,
            "canonical_repository_write_allowed": False,
            "command_execution_required": "validation_only",
            "exact_runtime_argv_deferred_to_launch_adapter": True,
            "foreign_repository_write_allowed": False,
            "git_commit_allowed": False,
            "git_push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "workspace_read_required": True,
            "workspace_write_required": "task_scope_bound",
        },
    }


def _runtime(provider: str = "github_copilot_cli") -> dict:
    return {
        "provider_id": provider,
        "runtime_id": provider,
        "model_id": "auto",
        "executable": "/usr/local/bin/copilot",
        "command_representation": "ARGV_NO_SHELL",
        "working_directory": "ATTEMPT_WORKSPACE_REPO",
        "timeout_seconds": 900,
        "network_policy": "ALLOW",
        "budget": {"provider_specific": {"max_ai_credits": 30}},
        "authority_granted": False,
    }


def _arrange(tmp_path: Path, monkeypatch):
    attempt = tmp_path / "attempt"
    workspace = attempt / "workspace" / "repo"
    workspace.mkdir(parents=True)
    mcp_script = (
        workspace
        / "scripts/coordination/control_plane/worker_runtime/"
        "worker_validation_mcp.py"
    )
    mcp_script.parent.mkdir(parents=True, exist_ok=True)
    mcp_script.write_text("# invocation fixture\n", encoding="utf-8")

    monkeypatch.setattr(
        adapter.registry,
        "load_module_runtime_config",
        lambda _root: _runtime_config(),
    )
    monkeypatch.setattr(
        adapter.registry,
        "resolve_default_runtime",
        lambda _root: _runtime(),
    )

    original_is_file = Path.is_file
    monkeypatch.setattr(
        adapter.Path,
        "is_file",
        lambda self: (
            True
            if str(self) == "/usr/local/bin/copilot"
            else original_is_file(self)
        ),
    )
    return attempt, workspace


def test_builds_provider_owned_argv_without_starting_process(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)

    result = adapter.build_launch_invocation(
        root=tmp_path,
        task_context=_context(),
        explicit_dispatch_decision=_decision(workspace),
        attempt_root=attempt,
    )

    assert result["provider_id"] == "github_copilot_cli"
    assert result["argv"][0] == "/usr/local/bin/copilot"
    assert result["argv"][-2:] == ["-C", str(workspace)]
    assert result["argv"][result["argv"].index("--model") + 1] == "auto"
    assert result["argv"][result["argv"].index("--max-ai-credits") + 1] == "30"
    assert result["effects"]["worker_process_started"] is False
    assert result["effects"]["filesystem_write_performed"] is False
    assert result["authority"]["adapter_grants_authority"] is False


def test_prompt_is_task_generic_and_uses_normalized_envelope() -> None:
    context = _context()
    decision = _decision(Path("/tmp/workspace"))

    prompt = adapter.render_worker_prompt(
        task_context=context,
        explicit_dispatch_decision=decision,
    )

    assert "cf10-fixture-task-v0-1" in prompt
    assert "Exercise the generic runtime invocation bridge." in prompt
    assert "cf10_fixture_task_v0_1.yaml" in prompt
    assert "cf10_fixture_v0_1.yaml" in prompt
    assert "Chat text is not execution authority." in prompt
    assert "Task50" not in prompt
    assert "a019" not in prompt


def test_binding_drift_fails_closed(tmp_path: Path, monkeypatch) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    decision = _decision(workspace)
    decision["binding"]["work_front_id"] = "wf-wrong"

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="binding drift",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=decision,
            attempt_root=attempt,
        )


def test_authority_widening_fails_closed(tmp_path: Path, monkeypatch) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    decision = _decision(workspace)
    decision["automatic_accept_allowed"] = True

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="widened forbidden authority",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=decision,
            attempt_root=attempt,
        )


def test_missing_explicit_launch_authority_fails_closed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    decision = _decision(workspace)
    decision["worker_process_launch_allowed"] = False

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="does not authorize Worker process launch",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=decision,
            attempt_root=attempt,
        )


def test_provider_drift_fails_closed(tmp_path: Path, monkeypatch) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    monkeypatch.setattr(
        adapter.registry,
        "resolve_default_runtime",
        lambda _root: _runtime("other_provider"),
    )

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="dispatch/runtime provider drift",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=_decision(workspace),
            attempt_root=attempt,
        )


def test_unimplemented_future_provider_is_not_guessed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt = tmp_path / "attempt"
    workspace = attempt / "workspace" / "repo"
    workspace.mkdir(parents=True)

    config = _runtime_config()
    config["command"]["provider_id"] = "openai_codex_cli"
    config["command"]["runtime_id"] = "openai_codex_cli"
    monkeypatch.setattr(
        adapter.registry,
        "load_module_runtime_config",
        lambda _root: config,
    )
    monkeypatch.setattr(
        adapter.registry,
        "resolve_default_runtime",
        lambda _root: _runtime("openai_codex_cli"),
    )
    monkeypatch.setattr(adapter.Path, "is_file", lambda self: True)

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="provider adapter not implemented",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=_decision(
                workspace,
                provider="openai_codex_cli",
            ),
            attempt_root=attempt,
        )


def test_workspace_binding_is_exact(tmp_path: Path, monkeypatch) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    decision = _decision(workspace)
    decision["binding"]["workspace_repo"] = str(tmp_path / "wrong")

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="binding drift",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=decision,
            attempt_root=attempt,
        )


def test_runtime_tool_policy_cannot_enable_publication(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    config = _runtime_config()
    config["tool_policy"]["git_push_allowed"] = True
    monkeypatch.setattr(
        adapter.registry,
        "load_module_runtime_config",
        lambda _root: config,
    )

    with pytest.raises(
        adapter.WorkerRuntimeInvocationError,
        match="tool policy widened authority",
    ):
        adapter.build_launch_invocation(
            root=tmp_path,
            task_context=_context(),
            explicit_dispatch_decision=_decision(workspace),
            attempt_root=attempt,
        )

def test_durable_invocation_evidence_omits_prompt_and_full_argv(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    invocation = adapter.build_launch_invocation(
        root=tmp_path,
        task_context=_context(),
        explicit_dispatch_decision=_decision(workspace),
        attempt_root=attempt,
    )

    evidence = adapter.build_invocation_evidence(invocation)

    # Durable evidence may contain paths.prompt, but never the runtime prompt
    # text or full argv as top-level serialized command material.
    assert "prompt" not in evidence
    assert "argv" not in evidence
    assert evidence["prompt_sha256"] == invocation["prompt_sha256"]
    assert evidence["argv_sha256"] == invocation["argv_sha256"]
    assert evidence["paths"]["prompt"].endswith("worker_prompt.txt")
    assert evidence["provider_policy"]["available_tools"] == [
        "view",
        "edit",
        "apply_patch",
        "ForPrintValidation-run_validation_suite",
    ]
    assert evidence["provider_policy"]["mcp_permission_patterns"] == [
        "ForPrintValidation(run_validation_suite)"
    ]
    assert evidence["provider_policy"]["permission_mode"] == (
        "ALLOW_ALL_WITHIN_AVAILABLE_TOOL_UNIVERSE"
    )
    assert evidence["provider_policy"]["bash_available"] is False
    assert evidence["provider_policy"]["web_available"] is False
    assert evidence["provider_policy"]["builtin_mcps_disabled"] is True
    assert evidence["serialization_boundary"] == {
        "prompt_text_serialized": False,
        "full_argv_serialized": False,
        "secret_values_serialized": False,
    }


def test_sanitized_evidence_contains_paths_but_not_runtime_command_material(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)
    invocation = adapter.build_launch_invocation(
        root=tmp_path,
        task_context=_context(),
        explicit_dispatch_decision=_decision(workspace),
        attempt_root=attempt,
    )

    evidence = adapter.build_invocation_evidence(invocation)
    rendered = yaml.safe_dump(
        evidence,
        sort_keys=False,
        allow_unicode=True,
    )

    assert invocation["prompt"] not in rendered
    assert json.dumps(invocation["argv"], ensure_ascii=False) not in rendered
    assert "NORMALIZED TASK ENVELOPE" not in rendered
    assert "--available-tools" not in rendered
    assert "worker_prompt.txt" in rendered

# CF10_WORKER_VALIDATION_MCP_BRIDGE_RED_V0_1


def test_worker_bridge_injects_session_only_validation_mcp_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)

    result = adapter.build_launch_invocation(
        root=tmp_path,
        task_context=_context(),
        explicit_dispatch_decision=_decision(workspace),
        attempt_root=attempt,
    )

    argv = result["argv"]
    assert "--additional-mcp-config" in argv, (
        "RED: invocation adapter does not inject the session-only MCP bridge"
    )

    raw = argv[argv.index("--additional-mcp-config") + 1]
    config = json.loads(raw)
    assert set(config) == {"mcpServers"}
    assert set(config["mcpServers"]) == {"ForPrintValidation"}

    server = config["mcpServers"]["ForPrintValidation"]
    assert server["type"] == "local"
    assert server["cwd"] == str(workspace)
    assert server["tools"] == ["run_validation_suite"]
    assert server["command"] == sys.executable
    assert Path(server["command"]).is_absolute()

    args = server["args"]
    expected_bindings = {
        "--attempt-id": "cf10-u180j-a999",
        "--task-id": "cf10-fixture-task-v0-1",
        "--work-front-id": "wf-cf10-fixture-v0-1",
        "--decision-id": "d" * 64,
        "--workspace-repo": str(workspace),
        "--evidence-root": str(
            (attempt / "evidence" / "structured_command").resolve()
        ),
    }
    for flag, expected in expected_bindings.items():
        assert flag in args
        assert args[args.index(flag) + 1] == expected

    assert ".mcp.json" not in " ".join(args)
    assert ".github/mcp.json" not in " ".join(args)


# CF10_A032_PROVIDER_EXPOSURE_REPAIR_RED_V0_1
def test_worker_bridge_exposes_exact_bounded_tool_universe(
    tmp_path: Path,
    monkeypatch,
) -> None:
    attempt, workspace = _arrange(tmp_path, monkeypatch)

    result = adapter.build_launch_invocation(
        root=tmp_path,
        task_context=_context(),
        explicit_dispatch_decision=_decision(workspace),
        attempt_root=attempt,
    )

    expected = [
        "view",
        "edit",
        "apply_patch",
        "ForPrintValidation-run_validation_suite",
    ]
    provider_policy = result["provider_policy"]
    assert provider_policy["available_tools"] == expected, (
        "RED: Copilot --available-tools must expose the provider/model-visible "
        "sanitized MCP tool id"
    )
    assert provider_policy["mcp_permission_patterns"] == [
        "ForPrintValidation(run_validation_suite)"
    ], (
        "RED: MCP permission-filter identity must remain separately represented "
        "from model-visible available-tool identity"
    )
    assert "ForPrintValidation(run_validation_suite)" not in provider_policy[
        "available_tools"
    ]

    argv = result["argv"]
    available_start = argv.index("--available-tools") + 1
    available_end = argv.index("--allow-all-tools")
    assert argv[available_start:available_end] == expected
    assert "ForPrintValidation(run_validation_suite)" not in argv[
        available_start:available_end
    ]

    assert provider_policy["bash_available"] is False
    assert provider_policy["web_available"] is False
    assert provider_policy["builtin_mcps_disabled"] is True
    assert provider_policy["persistent_mcp_config_written"] is False
    assert "shell" not in provider_policy["available_tools"]
# CF10_GOVERNED_WORKER_CONTEXT_DELIVERY_RED_V0_1


def test_prompt_renders_hash_bound_non_authoritative_governed_context() -> None:
    governed = {
        "schema_version": "forprint_governed_worker_context_projection_v0_1",
        "handoff_manifest_sha256": "1" * 64,
        "handoff_source_state_fingerprint": "2" * 64,
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
                "work_front_id": "wf-cf10-fixture-v0-1",
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
    canonical = (
        json.dumps(
            governed,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()

    decision = _decision(Path("/tmp/workspace"))
    decision["binding"]["governed_worker_context_sha256"] = digest

    prompt = adapter.render_worker_prompt(
        task_context=_context(),
        explicit_dispatch_decision=decision,
        governed_worker_context=governed,
    )

    assert "GOVERNED EXECUTION CONTEXT — NON-AUTHORITATIVE" in prompt
    assert "IN_SYNC" in prompt
    assert "u180j" in prompt
    assert "dependency_health.yaml" in prompt
    assert "0.1.0" in prompt
    assert "Work Front remains execution authority." in prompt
    assert "verification context only" in prompt


def test_hash_bound_governed_context_is_explicit_freshness_proof() -> None:
    governed = {
        "schema_version": "forprint_governed_worker_context_projection_v0_1",
        "handoff_manifest_sha256": "1" * 64,
        "handoff_source_state_fingerprint": "2" * 64,
        "dependency_health_slice": {
            "dependency_health.yaml": {
                "sha256": "3" * 64,
                "bytes": 128,
            }
        },
        "lifecycle_roadmap_cursor": {
            "roadmap_sync": "IN_SYNC",
            "roadmap_status": "ACTIVE",
            "open_work": {
                "u180j": {
                    "state": "ACTIVE",
                    "event_id": "evt-fixture",
                    "sequence": 67,
                }
            },
        },
        "resume_coordinates": {
            "work_id": "u180j",
            "git_head": "a" * 40,
            "work_state": {
                "state": "ACTIVE",
            },
        },
        "expected_result_schema_revision": "0.1.0",
        "execution_bindings": {
            "work_front_or_project_onboard_not_applicable_reason": {
                "work_front_id": "wf-cf10-fixture-v0-1",
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

    prompt = adapter.render_worker_prompt(
        task_context=_context(),
        explicit_dispatch_decision=_decision(Path("/tmp/workspace")),
        governed_worker_context=governed,
    )

    assert (
        "The hash-bound governed context is the attempt-scoped freshness "
        "verification snapshot." in prompt
    )
    assert (
        "Treat roadmap_sync=IN_SYNC plus the bound ACTIVE work item as "
        "sufficient freshness proof for this attempt unless the projection "
        "is internally inconsistent." in prompt
    )
    assert (
        "Do not regenerate lifecycle/roadmap freshness through shell commands."
        in prompt
    )
    assert "verification context only" in prompt
    assert "Work Front remains execution authority." in prompt


# CF10_TASK70_A031_PREREQUISITE_REPAIR_RED_V0_1
