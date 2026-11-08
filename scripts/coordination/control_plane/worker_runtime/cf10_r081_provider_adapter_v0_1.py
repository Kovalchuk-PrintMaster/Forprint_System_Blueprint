"""R081: provider adapter router for legacy Copilot invocation parity.

A PURE vendor command/policy renderer, not an execution/auth/approval adapter.
No dynamic imports, fallback, provider writes, network, processes, ledger or claims.
Future providers must be added by reviewed source with their own tests; declaring
READY in the catalog alone will never make a provider executable.
"""
from __future__ import annotations

from collections.abc import Mapping
import argparse
import json
from typing import Any

COPILOT_ID = "github_copilot_cli"


class AdapterRouteBlocked(ValueError):
    pass


def deny(code: str) -> None:
    raise AdapterRouteBlocked("CF10_R081_" + code)


def _string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        deny("INVALID_" + name)
    return value


def _values(value: Any, name: str) -> list[str]:
    if not isinstance(value, (tuple, list)) or not value:
        deny("INVALID_" + name)
    return [_string(item, name) for item in value]


class CopilotCliAdapter:
    """R079 ABI subset. Never grants execution or normalizes untrusted output."""

    def inspect_readiness(self, binding: Mapping) -> Mapping:
        if not isinstance(binding, Mapping) or binding.get("provider_id") != COPILOT_ID:
            deny("PROVIDER_BINDING_MISMATCH")
        return {
            "provider_id": COPILOT_ID,
            "adapter_available": True,
            "provider_session_authenticated": False,
            "worker_execution_authorized": False,
        }

    def build_invocation(self, binding: Mapping, frozen_task: Mapping) -> Mapping:
        if not isinstance(binding, Mapping) or not isinstance(frozen_task, Mapping):
            deny("BINDING_OR_TASK_NOT_MAPPING")
        if binding.get("provider_id") != COPILOT_ID:
            deny("PROVIDER_BINDING_MISMATCH")
        model = _string(binding.get("model_id"), "MODEL")
        workspace = _string(binding.get("workspace"), "WORKSPACE")
        base_argv = _values(frozen_task.get("base_argv"), "BASE_ARGV")
        prompt = _string(frozen_task.get("prompt"), "PROMPT")
        mcp_config = _string(frozen_task.get("mcp_config_json"), "MCP_CONFIG")
        tools = _values(frozen_task.get("available_tools"), "AVAILABLE_TOOLS")
        patterns = _values(frozen_task.get("permission_patterns"), "PERMISSION_PATTERNS")
        server = _string(frozen_task.get("mcp_server_name"), "MCP_SERVER")
        readback_tool = frozen_task.get("readback_tool")
        readback_permission = frozen_task.get("readback_permission")
        if (readback_tool is None) != (readback_permission is None):
            deny("READBACK_TOOL_PERMISSION_ASYMMETRY")
        if readback_tool is not None:
            tools.append(_string(readback_tool, "READBACK_TOOL"))
            patterns.append(_string(readback_permission, "READBACK_PERMISSION"))
        credits = frozen_task.get("max_ai_credits")
        if type(credits) is not int or credits < 30:
            deny("COPILOT_CREDIT_ARGUMENT")
        timeout = frozen_task.get("mcp_timeout_ms")
        if timeout is not None and (type(timeout) is not int or timeout <= 0):
            deny("MCP_TIMEOUT")
        # R115 explicitly migrates the old Copilot-only argv by inserting
        # --sandbox; all other argument bytes and permission rules are retained.
        # The launcher still requires independent host/session proof.
        argv = [
            *base_argv,
            "-p", prompt,
            "--silent", "--model", model,
            "--additional-mcp-config", mcp_config,
            "--available-tools", *tools,
            "--allow-all-tools",
            "--disable-builtin-mcps",
            "--max-ai-credits", str(credits),
            "--no-auto-update", "--sandbox", "-C", workspace,
        ]
        policy = {
            "available_tools": tools,
            "mcp_permission_patterns": patterns,
            "permission_mode": "ALLOW_ALL_WITHIN_AVAILABLE_TOOL_UNIVERSE",
            "bash_available": False,
            "web_available": False,
            "builtin_mcps_disabled": True,
            "additional_mcp_config_source": "SESSION_ONLY_ARGV",
            "mcp_server_names": [server],
            "mcp_transport": "STDIO_LOCAL",
            "mcp_server_tool_timeout_ms": timeout,
            "persistent_mcp_config_written": False,
            "sandbox_cli_requested": True,
            "sandbox_effective_policy_attested": False,
        }
        return {
            "provider_id": COPILOT_ID,
            "argv": argv,
            "provider_policy": policy,
            "adapter_grants_authority": False,
            "claim_consumed": False,
            "process_started": False,
            "result_accepted": False,
        }

    def normalize_result_candidate(self, provider_stream: bytes, binding: Mapping) -> Mapping:
        # Existing canonical worker_result_return owns framed result verification.
        # R081 MUST NOT introduce an easier provider-native acceptance route.
        deny("RESULT_NORMALIZATION_REMAINS_CANONICAL_FAIL_CLOSED")


_SOURCE_BOUND_ADAPTERS = {COPILOT_ID: CopilotCliAdapter()}


def route_invocation(*, provider_id: str, binding: Mapping, frozen_task: Mapping) -> dict:
    """Trusted caller supplies already validated binding; no provider fallback."""
    if not isinstance(provider_id, str) or not isinstance(binding, Mapping):
        deny("PROVIDER_SELECTION_INVALID")
    if binding.get("provider_id") != provider_id:
        deny("SELECTED_BINDING_PROVIDER_DRIFT")
    adapter = _SOURCE_BOUND_ADAPTERS.get(provider_id)
    if adapter is None:
        deny("ADAPTER_NOT_WIRED_NO_FALLBACK")
    result = dict(adapter.build_invocation(binding, frozen_task))
    if result.get("provider_id") != provider_id:
        deny("ADAPTER_RESULT_PROVIDER_DRIFT")
    if any(result.get(x) is not False for x in ("adapter_grants_authority", "claim_consumed", "process_started", "result_accepted")):
        deny("ADAPTER_AUTHORITY_WIDENING")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("inspect",), required=True)
    ap.parse_args(argv)
    print(json.dumps({
        "schema_version": "cf10_r081_source_bound_provider_adapter_review_v0_1",
        "status": "COPILOT_ADAPTER_SEAM_SOURCE_BOUND_PARITY_CANDIDATE",
        "wired_provider_ids": [COPILOT_ID],
        "registered_provider_is_not_dispatch_authority": True,
        "second_provider_execution_enabled": False,
        "copilot_auth_tested": False,
        "worker_launched": False,
        "claim_consumed": False,
        "ledger_written": False,
        "result_accepted": False,
        "automatic_fallback": False,
    },sort_keys=True,indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
