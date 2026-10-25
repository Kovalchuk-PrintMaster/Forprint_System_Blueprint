"""B4-P2C: explicit Copilot MCP tool deadline with reserved Worker finish budget."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.worker_runtime import invocation_adapter as adapter

ROOT = Path(__file__).resolve().parents[4]
POLICY = {"tool_timeout_ms": 960000, "minimum_worker_finish_reserve_seconds": 180}


def _helper_module():
    path = Path(__file__).with_name("test_cf10_worker_runtime_invocation_adapter_v0_1.py")
    spec = importlib.util.spec_from_file_location("cf10_existing_adapter_fixtures_p2c", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_canonical_budget_and_default_off_policy():
    c = yaml.safe_load((ROOT / "config/worker_runtime.yaml").read_text())
    assert c["schema_version"] == "forprint_module_worker_runtime_v0_1"
    assert c["timeout_seconds"] == 1200
    assert c["copilot_mcp"] == POLICY
    assert 900 * 1000 < POLICY["tool_timeout_ms"]
    assert POLICY["tool_timeout_ms"] + 180 * 1000 <= c["timeout_seconds"] * 1000
    assert c["tool_policy"]["automatic_accept_allowed"] is False
    readback = yaml.safe_load((ROOT / "coordination/registry/cf10_validation_evidence_readback_policy_v0_1.yaml").read_text())
    assert readback["default_enabled"] is False
    assert readback["opt_in_bindings"] == []


@pytest.mark.parametrize("payload", [
    None, "960000", True, -1, 0, 30000, 900000, 1200001, 1300000,
])
def test_invalid_timeout_fails_closed(payload):
    cfg = {"timeout_seconds": 1200, "copilot_mcp": {**POLICY, "tool_timeout_ms": payload}}
    with pytest.raises(adapter.WorkerRuntimeInvocationError):
        adapter._resolve_copilot_mcp_tool_timeout_ms(runtime_config=cfg, worker_timeout_seconds=1200)


@pytest.mark.parametrize("reserve", [None, True, 0, 60, -120, "180", 250])
def test_invalid_result_reserve_fails_closed(reserve):
    cfg = {"timeout_seconds": 1200, "copilot_mcp": {**POLICY, "minimum_worker_finish_reserve_seconds": reserve}}
    if reserve == 250:
        # 1200 - 960 = 240, so even a valid positive 250 does not fit.
        pass
    with pytest.raises(adapter.WorkerRuntimeInvocationError):
        adapter._resolve_copilot_mcp_tool_timeout_ms(runtime_config=cfg, worker_timeout_seconds=1200)


def test_canonical_missing_mcp_policy_fails_closed():
    with pytest.raises(adapter.WorkerRuntimeInvocationError, match="policy missing"):
        adapter._resolve_copilot_mcp_tool_timeout_ms(
            runtime_config={"schema_version": "forprint_module_worker_runtime_v0_1", "timeout_seconds": 1200},
            worker_timeout_seconds=1200,
        )


def test_runtime_drift_fails_closed():
    with pytest.raises(adapter.WorkerRuntimeInvocationError, match="config drift"):
        adapter._resolve_copilot_mcp_tool_timeout_ms(
            runtime_config={"timeout_seconds": 1200, "copilot_mcp": POLICY},
            worker_timeout_seconds=900,
        )


def test_provider_invocation_timeout_is_session_only(tmp_path, monkeypatch):
    fixtures = _helper_module()
    attempt, workspace = fixtures._arrange(tmp_path, monkeypatch)
    cfg = fixtures._runtime_config()
    cfg["schema_version"] = "forprint_module_worker_runtime_v0_1"
    cfg["timeout_seconds"] = 1200
    cfg["copilot_mcp"] = dict(POLICY)
    runtime = fixtures._runtime()
    runtime["timeout_seconds"] = 1200
    monkeypatch.setattr(adapter.registry, "load_module_runtime_config", lambda root: cfg)
    monkeypatch.setattr(adapter.registry, "resolve_default_runtime", lambda root: runtime)
    plan = adapter.build_launch_invocation(
        root=tmp_path, task_context=fixtures._context(),
        explicit_dispatch_decision=fixtures._decision(workspace), attempt_root=attempt,
    )
    argv = plan["argv"]
    mcp = json.loads(argv[argv.index("--additional-mcp-config") + 1])
    server = mcp["mcpServers"][adapter.WORKER_VALIDATION_MCP_SERVER]
    assert server["timeout"] == 960000
    assert server["tools"] == ["run_validation_suite", "run_repo_diff_check", "run_repo_head", "run_repo_status"]
    assert plan["timeout_seconds"] == 1200
    assert plan["provider_policy"]["mcp_server_tool_timeout_ms"] == 960000
    assert plan["authority"]["automatic_accept_allowed"] is False
    assert plan["effects"]["worker_process_started"] is False
    assert plan["effects"]["filesystem_write_performed"] is False


def test_budget_guard_blocks_old_900s_runtime(tmp_path, monkeypatch):
    fixtures = _helper_module()
    attempt, workspace = fixtures._arrange(tmp_path, monkeypatch)
    cfg = fixtures._runtime_config()
    cfg["schema_version"] = "forprint_module_worker_runtime_v0_1"
    cfg["copilot_mcp"] = dict(POLICY)
    # 900 s Worker would end before the 960 s MCP tool call.
    monkeypatch.setattr(adapter.registry, "load_module_runtime_config", lambda root: cfg)
    with pytest.raises(adapter.WorkerRuntimeInvocationError, match="reserve"):
        adapter.build_launch_invocation(
            root=tmp_path, task_context=fixtures._context(),
            explicit_dispatch_decision=fixtures._decision(workspace), attempt_root=attempt,
        )


# B4-P2E: GitHub Copilot CLI 1.0.88 refuses --max-ai-credits < 30.
# The guard belongs at invocation construction, before any provider process starts.
@pytest.mark.parametrize("credits", [None, True, False, -1, 0, 1, 5, 29, "30", 30.0])
def test_b4_p2e_copilot_credits_below_floor_rejected(tmp_path, monkeypatch, credits):
    fixtures = _helper_module()
    attempt, workspace = fixtures._arrange(tmp_path, monkeypatch)
    cfg = fixtures._runtime_config()
    cfg["schema_version"] = "forprint_module_worker_runtime_v0_1"
    cfg["timeout_seconds"] = 1200
    cfg["copilot_mcp"] = dict(POLICY)
    cfg["budget"]["provider_specific"]["max_ai_credits"] = credits
    runtime = fixtures._runtime()
    runtime["timeout_seconds"] = 1200
    monkeypatch.setattr(adapter.registry, "load_module_runtime_config", lambda root: cfg)
    monkeypatch.setattr(adapter.registry, "resolve_default_runtime", lambda root: runtime)
    with pytest.raises(adapter.WorkerRuntimeInvocationError, match="must be at least 30"):
        adapter.build_launch_invocation(
            root=tmp_path, task_context=fixtures._context(),
            explicit_dispatch_decision=fixtures._decision(workspace), attempt_root=attempt,
        )


@pytest.mark.parametrize("credits", [30, 31, 100])
def test_b4_p2e_copilot_credits_at_or_above_floor_accepted(tmp_path, monkeypatch, credits):
    fixtures = _helper_module()
    attempt, workspace = fixtures._arrange(tmp_path, monkeypatch)
    cfg = fixtures._runtime_config()
    cfg["schema_version"] = "forprint_module_worker_runtime_v0_1"
    cfg["timeout_seconds"] = 1200
    cfg["copilot_mcp"] = dict(POLICY)
    cfg["budget"]["provider_specific"]["max_ai_credits"] = credits
    runtime = fixtures._runtime()
    runtime["timeout_seconds"] = 1200
    monkeypatch.setattr(adapter.registry, "load_module_runtime_config", lambda root: cfg)
    monkeypatch.setattr(adapter.registry, "resolve_default_runtime", lambda root: runtime)
    invocation = adapter.build_launch_invocation(
        root=tmp_path, task_context=fixtures._context(),
        explicit_dispatch_decision=fixtures._decision(workspace), attempt_root=attempt,
    )
    args = invocation["argv"]
    assert args[args.index("--max-ai-credits") + 1] == str(credits)
    assert invocation["effects"]["worker_process_started"] is False


def test_b4_p2e_actual_runtime_budget_is_30_and_not_auto_authority():
    c = yaml.safe_load((ROOT / "config/worker_runtime.yaml").read_text())
    assert c["budget"]["provider_specific"]["max_ai_credits"] == 30
    assert adapter.COPILOT_CLI_MIN_AI_CREDITS == 30
    assert c["tool_policy"]["automatic_accept_allowed"] is False
