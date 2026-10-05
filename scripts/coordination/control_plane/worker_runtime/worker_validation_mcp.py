#!/usr/bin/env python3
"""Bounded CF10 Worker validation MCP bridge.

The MCP surface exposes exactly one read-only validation tool. Worker-supplied
input is limited to a registered validation suite id and optional verification
tier. Execution identity, workspace, evidence destination, timeout, capability
identity and authorization are bound at server startup by the invocation
adapter and cannot be overridden by the Worker.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import anyio
import mcp.types as types
from mcp import Client, StdioServerParameters
from mcp.server import Server, ServerRequestContext
from mcp.server.stdio import stdio_server

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.coordination.control_plane.worker_runtime import (  # noqa: E402
    structured_command_executor as structured_executor,
)

SERVER_NAME = "ForPrintValidation"
SERVER_VERSION = "0.1.0"
TOOL_NAME = "run_validation_suite"
CAPABILITY_ID = "validation_suite"
CAPABILITY_VERSION = "0.1.0"
CONSUMER_ID = "cf10_worker_validation_mcp"
TIMEOUT_SECONDS = 900
MAX_DIAGNOSTIC_BYTES = 4096

TOOL_INPUT_SCHEMA: dict[str, Any] = {
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
    },
    "required": ["suite_id"],
    "additionalProperties": False,
}


class WorkerValidationMCPError(RuntimeError):
    """Raised when the bounded MCP bridge cannot prove its binding."""


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkerValidationMCPError(f"{label} must be a non-empty string")
    return value.strip()


def _normalized_absolute_path(value: Any, label: str) -> Path:
    raw = _string(value, label)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise WorkerValidationMCPError(f"{label} must be absolute")
    resolved = path.resolve()
    if str(resolved) != raw:
        raise WorkerValidationMCPError(f"{label} must be normalized")
    return resolved


def _is_inside(parent: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_startup_binding(
    *,
    attempt_id: str,
    task_id: str,
    work_front_id: str,
    decision_id: str,
    workspace_repo: str,
    evidence_root: str,
) -> dict[str, Any]:
    workspace = _normalized_absolute_path(workspace_repo, "workspace_repo")
    evidence = _normalized_absolute_path(evidence_root, "evidence_root")

    if not workspace.is_dir():
        raise WorkerValidationMCPError("workspace_repo must be an existing directory")
    if evidence == workspace or _is_inside(workspace, evidence):
        raise WorkerValidationMCPError(
            "evidence_root must remain outside the Worker workspace"
        )

    return {
        "attempt_id": _string(attempt_id, "attempt_id"),
        "task_id": _string(task_id, "task_id"),
        "work_front_id": _string(work_front_id, "work_front_id"),
        "decision_id": _string(decision_id, "decision_id"),
        "workspace": workspace,
        "evidence_root": evidence,
    }


def _authorization_envelope(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": (
            "forprint_structured_execution_authorization_envelope_v0_1"
        ),
        "decision": "ALLOW_EXACT_STRUCTURED_EXECUTION",
        "consumer_id": request["consumer_id"],
        "request_id": request["request_id"],
        "capability_id": request["capability_id"],
        "capability_version": request["capability_version"],
        "execution_identity": dict(request["execution_identity"]),
        "execution_scope": dict(request["execution_scope"]),
        "exact_cwd": request["exact_cwd"],
        "parameters": dict(request["parameters"]),
        "timeout_seconds": request["timeout_seconds"],
        "evidence_destination": request["evidence_destination"],
        "authority": {
            "consumer_policy_validated": True,
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


def _bounded_excerpt(
    evidence: Any,
    *,
    evidence_root: Path,
) -> str:
    if not isinstance(evidence, Mapping):
        return ""
    raw_path = evidence.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        return ""

    path = Path(raw_path).expanduser().resolve()
    if not _is_inside(evidence_root, path):
        raise WorkerValidationMCPError(
            "executor evidence path escaped the bound evidence root"
        )
    if not path.is_file() or path.is_symlink():
        raise WorkerValidationMCPError(
            "executor evidence path is missing or unsafe"
        )

    with path.open("rb") as handle:
        raw = handle.read(MAX_DIAGNOSTIC_BYTES)
    return raw.decode("utf-8", errors="replace")


def _success_payload(
    result: Mapping[str, Any],
    *,
    evidence_root: Path,
) -> dict[str, Any]:
    required = (
        "execution_id",
        "outcome",
        "return_code",
        "timed_out",
        "stdout_evidence",
        "stderr_evidence",
        "evidence_digest",
    )
    missing = [key for key in required if key not in result]
    if missing:
        raise WorkerValidationMCPError(
            "structured executor result missing fields: " + ",".join(missing)
        )

    authority = result.get("authority")
    if not isinstance(authority, Mapping):
        raise WorkerValidationMCPError(
            "structured executor authority result missing"
        )
    forbidden_true = (
        "executor_grants_authority",
        "canonical_write_allowed",
        "safe_write_allowed",
        "commit_allowed",
        "push_allowed",
        "merge_allowed",
        "release_allowed",
        "promotion_allowed",
        "arbitrary_shell_allowed",
    )
    widened = [key for key in forbidden_true if authority.get(key) is not False]
    if widened:
        raise WorkerValidationMCPError(
            "structured executor result widened authority: " + ",".join(widened)
        )

    return {
        "execution_id": result["execution_id"],
        "outcome": result["outcome"],
        "return_code": result["return_code"],
        "timed_out": result["timed_out"],
        "stdout_evidence": dict(result["stdout_evidence"]),
        "stderr_evidence": dict(result["stderr_evidence"]),
        "evidence_digest": result["evidence_digest"],
        "diagnostics": {
            "stdout_excerpt": _bounded_excerpt(
                result["stdout_evidence"],
                evidence_root=evidence_root,
            ),
            "stderr_excerpt": _bounded_excerpt(
                result["stderr_evidence"],
                evidence_root=evidence_root,
            ),
            "maximum_bytes_per_stream": MAX_DIAGNOSTIC_BYTES,
        },
        "authority": {key: False for key in forbidden_true},
    }


def _error_result(message: str) -> types.CallToolResult:
    bounded = message[:1000]
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text="ForPrint validation bridge rejected the request: " + bounded,
            )
        ],
        is_error=True,
    )


def build_server(
    *,
    attempt_id: str,
    task_id: str,
    work_front_id: str,
    decision_id: str,
    workspace_repo: str,
    evidence_root: str,
) -> Server:
    """Build one attempt-bound low-level MCP server."""

    binding = _validate_startup_binding(
        attempt_id=attempt_id,
        task_id=task_id,
        work_front_id=work_front_id,
        decision_id=decision_id,
        workspace_repo=workspace_repo,
        evidence_root=evidence_root,
    )
    request_counter = itertools.count(1)

    async def handle_list_tools(
        _ctx: ServerRequestContext,
        _params: types.PaginatedRequestParams | None,
    ) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=TOOL_NAME,
                    description=(
                        "Run one registered ForPrint validation suite through "
                        "the bounded structured command executor."
                    ),
                    input_schema=TOOL_INPUT_SCHEMA,
                )
            ]
        )

    async def handle_call_tool(
        _ctx: ServerRequestContext,
        params: types.CallToolRequestParams,
    ) -> types.CallToolResult:
        try:
            if params.name != TOOL_NAME:
                raise WorkerValidationMCPError(
                    f"unknown tool: {params.name}"
                )

            arguments = params.arguments or {}
            if not isinstance(arguments, dict):
                raise WorkerValidationMCPError(
                    "tool arguments must be an object"
                )

            unknown = sorted(
                set(arguments) - {"suite_id", "require_tier"}
            )
            if unknown:
                raise WorkerValidationMCPError(
                    "unsupported Worker parameters: " + ",".join(unknown)
                )

            suite_id = _string(arguments.get("suite_id"), "suite_id")
            require_tier = arguments.get("require_tier")
            if require_tier is not None:
                require_tier = _string(require_tier, "require_tier")

            parameters: dict[str, Any] = {"suite_id": suite_id}
            if require_tier is not None:
                parameters["require_tier"] = require_tier

            workspace: Path = binding["workspace"]
            evidence: Path = binding["evidence_root"]
            request_id = (
                f"{binding['attempt_id']}:validation:"
                f"{next(request_counter):04d}"
            )
            execution_identity = {
                "attempt_id": binding["attempt_id"],
                "task_id": binding["task_id"],
                "work_front_id": binding["work_front_id"],
                "explicit_dispatch_decision_id": binding["decision_id"],
            }
            request: dict[str, Any] = {
                "capability_id": CAPABILITY_ID,
                "capability_version": CAPABILITY_VERSION,
                "execution_scope": {
                    "kind": "GIT_REPOSITORY_ROOT",
                    "root": str(workspace),
                },
                "exact_cwd": str(workspace),
                "parameters": parameters,
                "timeout_seconds": TIMEOUT_SECONDS,
                "evidence_destination": str(evidence),
                "execution_identity": execution_identity,
                "consumer_id": CONSUMER_ID,
                "request_id": request_id,
            }
            request["authorization_envelope"] = _authorization_envelope(
                request
            )

            plan = structured_executor.build_execution_plan(
                root=workspace,
                request=request,
            )
            result = structured_executor.execute_execution_plan(
                root=workspace,
                plan=plan,
            )
            payload = _success_payload(
                result,
                evidence_root=evidence,
            )
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "execution_id": payload["execution_id"],
                                "outcome": payload["outcome"],
                                "return_code": payload["return_code"],
                                "timed_out": payload["timed_out"],
                                "evidence_digest": payload["evidence_digest"],
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    )
                ],
                structured_content=payload,
                is_error=False,
            )
        except (
            OSError,
            ValueError,
            WorkerValidationMCPError,
            structured_executor.StructuredCommandExecutorError,
        ) as exc:
            return _error_result(f"{type(exc).__name__}: {exc}")

    return Server(
        SERVER_NAME,
        version=SERVER_VERSION,
        on_list_tools=handle_list_tools,
        on_call_tool=handle_call_tool,
    )


async def _run_stdio(server: Server) -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


async def _run_proof(
    *,
    root: Path,
    evidence_root: Path,
    suite_id: str,
    require_tier: str,
) -> dict[str, Any]:
    if not root.is_dir() or not (root / ".git").exists():
        raise WorkerValidationMCPError(
            "proof root must be an exact Git repository root"
        )
    if evidence_root == root or _is_inside(root, evidence_root):
        raise WorkerValidationMCPError(
            "proof evidence root must remain outside the repository"
        )
    if evidence_root.exists() and any(evidence_root.iterdir()):
        raise WorkerValidationMCPError(
            "proof evidence root must be absent or empty"
        )
    evidence_root.mkdir(parents=True, exist_ok=True)

    script = Path(__file__).resolve()
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            str(script),
            "--attempt-id",
            "cf10-worker-invocation-bridge-proof",
            "--task-id",
            "cf10-validation-check-pipeline-profile-and-optimization-v0-1",
            "--work-front-id",
            "wf-cf10-worker-invocation-bridge-v0-1",
            "--decision-id",
            "cf10-worker-invocation-bridge-proof",
            "--workspace-repo",
            str(root),
            "--evidence-root",
            str(evidence_root),
        ],
        cwd=str(root),
    )

    async with Client(
        params,
        read_timeout_seconds=1200,
    ) as client:
        listed = await client.list_tools()
        if [tool.name for tool in listed.tools] != [TOOL_NAME]:
            raise WorkerValidationMCPError(
                "proof MCP tool universe drift"
            )
        tool = listed.tools[0]
        if tool.input_schema != TOOL_INPUT_SCHEMA:
            raise WorkerValidationMCPError(
                "proof MCP tool schema drift"
            )

        arguments: dict[str, Any] = {"suite_id": suite_id}
        if require_tier:
            arguments["require_tier"] = require_tier
        result = await client.call_tool(TOOL_NAME, arguments)

    if result.is_error is True:
        raise WorkerValidationMCPError(
            "proof validation tool returned is_error=true"
        )
    payload = result.structured_content
    if not isinstance(payload, dict):
        raise WorkerValidationMCPError(
            "proof validation tool returned no structured content"
        )
    if payload.get("return_code") != 0:
        raise WorkerValidationMCPError(
            f"proof validation failed return_code={payload.get('return_code')}"
        )
    if payload.get("timed_out") is not False:
        raise WorkerValidationMCPError(
            "proof validation timed out"
        )
    if payload.get("outcome") not in {
        "completed",
        "completed_with_stall_evidence",
    }:
        raise WorkerValidationMCPError(
            f"proof validation outcome invalid: {payload.get('outcome')!r}"
        )
    authority = payload.get("authority")
    if not isinstance(authority, dict) or any(authority.values()):
        raise WorkerValidationMCPError(
            "proof validation result widened authority"
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ForPrint bounded Worker validation MCP server"
    )
    parser.add_argument("--proof", action="store_true")
    parser.add_argument("--root", default=str(PROJECT_ROOT))
    parser.add_argument("--suite", default="cf10-worker-pipeline")
    parser.add_argument("--require-tier", default="LOCAL_FOCUSED")
    parser.add_argument("--attempt-id")
    parser.add_argument("--task-id")
    parser.add_argument("--work-front-id")
    parser.add_argument("--decision-id")
    parser.add_argument("--workspace-repo")
    parser.add_argument("--evidence-root")
    args = parser.parse_args()

    try:
        if args.proof:
            if args.evidence_root is None:
                raise WorkerValidationMCPError(
                    "--proof requires --evidence-root"
                )
            root = _normalized_absolute_path(
                str(Path(args.root).expanduser().resolve()),
                "proof root",
            )
            evidence_root = _normalized_absolute_path(
                str(Path(args.evidence_root).expanduser().resolve()),
                "proof evidence root",
            )
            suite_id = _string(args.suite, "proof suite")
            require_tier = _string(
                args.require_tier,
                "proof require_tier",
            )
            async def proof_runner() -> dict[str, Any]:
                return await _run_proof(
                    root=root,
                    evidence_root=evidence_root,
                    suite_id=suite_id,
                    require_tier=require_tier,
                )

            payload = anyio.run(proof_runner)
            print("CF10_WORKER_INVOCATION_BRIDGE_PROOF=PASS")
            print(f"SERVER_NAME={SERVER_NAME}")
            print(f"TOOL_NAME={TOOL_NAME}")
            print(f"SUITE_ID={suite_id}")
            print(f"RETURN_CODE={payload['return_code']}")
            print(f"TIMED_OUT={str(payload['timed_out']).lower()}")
            print(f"OUTCOME={payload['outcome']}")
            print(f"EXECUTION_ID={payload['execution_id']}")
            print(f"EVIDENCE_DIGEST={payload['evidence_digest']}")
            print("SHELL=false")
            print("AUTHORITY_WIDENED=false")
            print("A029_CREATED=false")
            return 0

        missing = [
            name
            for name, value in {
                "--attempt-id": args.attempt_id,
                "--task-id": args.task_id,
                "--work-front-id": args.work_front_id,
                "--decision-id": args.decision_id,
                "--workspace-repo": args.workspace_repo,
                "--evidence-root": args.evidence_root,
            }.items()
            if value is None
        ]
        if missing:
            raise WorkerValidationMCPError(
                "serve mode missing required arguments: "
                + ",".join(missing)
            )
        server = build_server(
            attempt_id=args.attempt_id,
            task_id=args.task_id,
            work_front_id=args.work_front_id,
            decision_id=args.decision_id,
            workspace_repo=args.workspace_repo,
            evidence_root=args.evidence_root,
        )
    except WorkerValidationMCPError as exc:
        print(
            f"WORKER_VALIDATION_MCP=FAIL {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    anyio.run(_run_stdio, server)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
