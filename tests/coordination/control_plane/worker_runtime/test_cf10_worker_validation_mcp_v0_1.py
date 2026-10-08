from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import mcp.types as mcp_types

ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    ROOT
    / "scripts/coordination/control_plane/worker_runtime/"
    "worker_validation_mcp.py"
)


def _load_module():
    assert SOURCE.is_file(), (
        "RED: canonical Worker validation MCP server is not implemented"
    )
    spec = importlib.util.spec_from_file_location(
        "_cf10_worker_validation_mcp_test",
        SOURCE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _binding(tmp_path: Path) -> dict[str, str]:
    workspace = tmp_path / "attempt/workspace/repo"
    evidence = tmp_path / "attempt/evidence/structured_command"
    workspace.mkdir(parents=True)
    evidence.mkdir(parents=True)
    return {
        "attempt_id": "cf10-u180j-red-a999",
        "task_id": "cf10-fixture-task-v0-1",
        "work_front_id": "wf-cf10-fixture-v0-1",
        "decision_id": "d" * 64,
        "workspace_repo": str(workspace.resolve()),
        "evidence_root": str(evidence.resolve()),
    }


def _handler(server, method: str):
    entry = server.get_request_handler(method)
    assert entry is not None, f"missing MCP handler: {method}"
    return entry.handler


def _call_params(name: str, arguments: dict) -> mcp_types.CallToolRequestParams:
    return mcp_types.CallToolRequestParams.model_validate(
        {
            "_meta": {},
            "name": name,
            "arguments": arguments,
        }
    )


def test_validation_mcp_exposes_exactly_two_bounded_tools(tmp_path: Path) -> None:
    module = _load_module()
    server = module.build_server(**_binding(tmp_path))

    result = asyncio.run(_handler(server, "tools/list")(None, None))

    assert [tool.name for tool in result.tools] == [
        "run_validation_suite",
        "run_repo_diff_check",
    ]

    validation_tool = result.tools[0]
    assert validation_tool.input_schema == {
        "type": "object",
        "properties": {
            "suite_id": {"type": "string"},
            "require_tier": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "null"},
                ],
                "default": None,
            },
            "profile": {
                "type": "boolean",
                "default": False,
            },
        },
        "required": ["suite_id"],
        "additionalProperties": False,
    }

    diff_tool = result.tools[1]
    assert diff_tool.input_schema == {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    }


def test_validation_mcp_binds_hidden_execution_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_module()
    binding = _binding(tmp_path)
    captured = {}

    stdout = Path(binding["evidence_root"]) / "fixture/stdout.log"
    stderr = Path(binding["evidence_root"]) / "fixture/stderr.log"
    stdout.parent.mkdir(parents=True)
    stdout.write_text("VALIDATION_FIXTURE_PASS\n" + ("x" * 5000), encoding="utf-8")
    stderr.write_text("fixture warning\n", encoding="utf-8")

    def fake_build_execution_plan(*, root, request):
        captured["root"] = str(Path(root).resolve())
        captured["request"] = request
        return {
            "schema_version": "forprint_structured_execution_plan_v0_1",
            "request": request,
            "execution_id": "structured-exec-redfixture",
        }

    def fake_execute_execution_plan(*, root, plan):
        captured["execute_root"] = str(Path(root).resolve())
        captured["plan"] = plan
        return {
            "execution_id": "structured-exec-redfixture",
            "outcome": "completed",
            "elapsed_seconds": 12.5,
            "return_code": 0,
            "timed_out": False,
            "stdout_evidence": {
                "path": str(stdout),
                "sha256": "1" * 64,
                "size_bytes": stdout.stat().st_size,
            },
            "stderr_evidence": {
                "path": str(stderr),
                "sha256": "2" * 64,
                "size_bytes": stderr.stat().st_size,
            },
            "evidence_digest": "3" * 64,
            "authority": {
                "executor_grants_authority": False,
                "canonical_write_allowed": False,
                "safe_write_allowed": False,
                "commit_allowed": False,
                "push_allowed": False,
                "merge_allowed": False,
                "release_allowed": False,
                "promotion_allowed": False,
                "arbitrary_shell_allowed": False,
            },
        }

    monkeypatch.setattr(
        module.structured_executor,
        "build_execution_plan",
        fake_build_execution_plan,
    )
    monkeypatch.setattr(
        module.structured_executor,
        "execute_execution_plan",
        fake_execute_execution_plan,
    )

    server = module.build_server(**binding)
    result = asyncio.run(
        _handler(server, "tools/call")(
            None,
            _call_params(
                "run_validation_suite",
                {
                    "suite_id": "cf10-worker-pipeline",
                    "require_tier": "LOCAL_FOCUSED",
                    "profile": True,
                },
            ),
        )
    )

    request = captured["request"]
    workspace = str(Path(binding["workspace_repo"]).resolve())
    evidence_root = str(Path(binding["evidence_root"]).resolve())

    assert captured["root"] == workspace
    assert captured["execute_root"] == workspace
    assert request["capability_id"] == "validation_suite"
    assert request["capability_version"] == "0.2.0"
    assert request["parameters"] == {
        "suite_id": "cf10-worker-pipeline",
        "require_tier": "LOCAL_FOCUSED",
        "profile": True,
    }
    assert request["exact_cwd"] == workspace
    assert request["execution_scope"] == {
        "kind": "GIT_REPOSITORY_ROOT",
        "root": workspace,
    }
    assert request["timeout_seconds"] == 900
    assert request["evidence_destination"] == evidence_root
    assert request["consumer_id"] == "cf10_worker_validation_mcp"
    assert request["execution_identity"] == {
        "attempt_id": binding["attempt_id"],
        "task_id": binding["task_id"],
        "work_front_id": binding["work_front_id"],
        "explicit_dispatch_decision_id": binding["decision_id"],
    }
    assert binding["attempt_id"] in request["request_id"]

    envelope = request["authorization_envelope"]
    for field in (
        "consumer_id",
        "request_id",
        "capability_id",
        "capability_version",
        "execution_identity",
        "execution_scope",
        "exact_cwd",
        "parameters",
        "timeout_seconds",
        "evidence_destination",
    ):
        assert envelope[field] == request[field]

    authority = envelope["authority"]
    assert authority["consumer_policy_validated"] is True
    for key in (
        "executor_grants_authority",
        "canonical_write_allowed",
        "safe_write_allowed",
        "commit_allowed",
        "push_allowed",
        "merge_allowed",
        "release_allowed",
        "promotion_allowed",
        "arbitrary_shell_allowed",
    ):
        assert authority[key] is False

    assert result.is_error is False
    payload = result.structured_content
    assert payload is not None
    assert payload["execution_id"] == "structured-exec-redfixture"
    assert payload["outcome"] == "completed"
    assert payload["elapsed_seconds"] == 12.5
    assert payload["return_code"] == 0
    assert payload["timed_out"] is False
    assert payload["evidence_digest"] == "3" * 64
    assert payload["stdout_evidence"]["path"] == str(stdout)
    assert payload["stderr_evidence"]["path"] == str(stderr)
    assert "VALIDATION_FIXTURE_PASS" in payload["diagnostics"]["stdout_excerpt"]
    assert len(payload["diagnostics"]["stdout_excerpt"]) <= 4096
    assert len(payload["diagnostics"]["stderr_excerpt"]) <= 4096
    assert "argv" not in payload
    assert "shell_text" not in payload


def test_validation_mcp_rejects_worker_supplied_hidden_fields(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_module()
    called = []

    monkeypatch.setattr(
        module.structured_executor,
        "build_execution_plan",
        lambda **kwargs: called.append(kwargs),
    )

    server = module.build_server(**_binding(tmp_path))
    result = asyncio.run(
        _handler(server, "tools/call")(
            None,
            _call_params(
                "run_validation_suite",
                {
                    "suite_id": "cf10-worker-pipeline",
                    "cwd": "/tmp/evil",
                },
            ),
        )
    )

    assert result.is_error is True
    assert called == []
    assert result.structured_content is None


# CF10_WORKER_VALIDATION_SURFACE_COMPLETION_RED_V0_1


def test_repo_diff_check_tool_reuses_exact_registered_capability(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_module()
    binding = _binding(tmp_path)
    captured = {}

    stdout = Path(binding["evidence_root"]) / "diff/stdout.log"
    stderr = Path(binding["evidence_root"]) / "diff/stderr.log"
    stdout.parent.mkdir(parents=True)
    stdout.write_text("", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")

    def fake_build_execution_plan(*, root, request):
        captured["root"] = str(Path(root).resolve())
        captured["request"] = request
        return {
            "schema_version": "forprint_structured_execution_plan_v0_1",
            "request": request,
            "execution_id": "structured-exec-diff-check",
        }

    def fake_execute_execution_plan(*, root, plan):
        captured["execute_root"] = str(Path(root).resolve())
        captured["plan"] = plan
        return {
            "execution_id": "structured-exec-diff-check",
            "outcome": "completed",
            "elapsed_seconds": 0.1,
            "return_code": 0,
            "timed_out": False,
            "stdout_evidence": {
                "path": str(stdout),
                "sha256": "1" * 64,
                "size_bytes": 0,
            },
            "stderr_evidence": {
                "path": str(stderr),
                "sha256": "2" * 64,
                "size_bytes": 0,
            },
            "evidence_digest": "3" * 64,
            "authority": {
                "executor_grants_authority": False,
                "canonical_write_allowed": False,
                "safe_write_allowed": False,
                "commit_allowed": False,
                "push_allowed": False,
                "merge_allowed": False,
                "release_allowed": False,
                "promotion_allowed": False,
                "arbitrary_shell_allowed": False,
            },
        }

    monkeypatch.setattr(
        module.structured_executor,
        "build_execution_plan",
        fake_build_execution_plan,
    )
    monkeypatch.setattr(
        module.structured_executor,
        "execute_execution_plan",
        fake_execute_execution_plan,
    )

    server = module.build_server(**binding)

    result = asyncio.run(
        _handler(server, "tools/call")(
            None,
            _call_params(
                "run_repo_diff_check",
                {},
            ),
        )
    )

    assert result.is_error is False

    request = captured["request"]
    workspace = str(Path(binding["workspace_repo"]).resolve())
    evidence_root = str(Path(binding["evidence_root"]).resolve())

    assert captured["root"] == workspace
    assert captured["execute_root"] == workspace

    assert request["capability_id"] == "repo_diff_check"
    assert request["capability_version"] == "0.1.0"
    assert request["parameters"] == {}

    assert request["exact_cwd"] == workspace
    assert request["execution_scope"] == {
        "kind": "GIT_REPOSITORY_ROOT",
        "root": workspace,
    }

    assert request["evidence_destination"] == evidence_root
    assert request["consumer_id"] == "cf10_worker_validation_mcp"

    envelope = request["authorization_envelope"]
    assert envelope["capability_id"] == "repo_diff_check"
    assert envelope["capability_version"] == "0.1.0"
    assert envelope["parameters"] == {}
    assert envelope["exact_cwd"] == workspace

    assert envelope["authority"]["arbitrary_shell_allowed"] is False
    assert envelope["authority"]["canonical_write_allowed"] is False
    assert envelope["authority"]["promotion_allowed"] is False


def test_repo_diff_check_rejects_worker_supplied_parameters(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_module()
    called = []

    monkeypatch.setattr(
        module.structured_executor,
        "build_execution_plan",
        lambda **kwargs: called.append(kwargs),
    )

    server = module.build_server(**_binding(tmp_path))

    result = asyncio.run(
        _handler(server, "tools/call")(
            None,
            _call_params(
                "run_repo_diff_check",
                {
                    "cwd": "/tmp/evil",
                },
            ),
        )
    )

    assert result.is_error is True
    assert result.structured_content is None
    assert called == []


# CF10_TASK70_A031_PREREQUISITE_REPAIR_RED_V0_1
