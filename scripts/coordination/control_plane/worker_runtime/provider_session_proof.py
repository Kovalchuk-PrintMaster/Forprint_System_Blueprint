#!/usr/bin/env python3
"""Project-native real GitHub Copilot -> ForPrintValidation MCP proof.

This capability proves the provider-visible MCP execution path without creating
or launching a governed Worker attempt. It is read-only with respect to the
canonical repository and writes immutable proof evidence only under an explicit
runtime root outside the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.coordination.control_plane.worker_runtime import (
    invocation_adapter as adapter,
)
from scripts.coordination.control_plane.worker_runtime import registry
from scripts.coordination.control_plane.worker_runtime.launcher import (
    WorkerProcessLaunchError,
    launch_process,
)


TASK_ID = "cf10-validation-check-pipeline-profile-and-optimization-v0-1"
WORK_FRONT_ID = "wf-cf10-project-native-provider-session-proof-v0-1"
PROOF_ID = "cf10-provider-session-proof"
PROOF_SCHEMA = "forprint_cf10_worker_provider_session_proof_v0_1"
PROOF_FILENAME = "provider_session_proof_v0_1.yaml"
STRUCTURED_DIRNAME = "structured_execution"
PERSISTENT_MCP_PATHS = (Path(".mcp.json"), Path(".github/mcp.json"))


class WorkerProviderSessionProofError(RuntimeError):
    """Raised when the bounded provider-session proof cannot be established."""


def _run_git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        shell=False,
    )
    if cp.returncode != 0:
        raise WorkerProviderSessionProofError(
            "git evidence command failed rc="
            + str(cp.returncode)
            + ": "
            + " ".join(args)
            + "\n"
            + cp.stdout
        )
    return cp.stdout


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(raw)


def _is_inside(parent: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False


def _require_outside(
    canonical: Path,
    candidate: Path,
    label: str,
) -> Path:
    resolved = candidate.expanduser().resolve()
    if resolved == canonical or _is_inside(canonical, resolved):
        raise WorkerProviderSessionProofError(
            f"{label} must remain outside canonical repository"
        )
    return resolved


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkerProviderSessionProofError(
            f"{label} must be a non-empty string"
        )
    return value.strip()


def capture_repository_snapshot(repo: Path | str) -> dict[str, Any]:
    """Capture immutable-comparison evidence without requiring a clean worktree."""

    canonical = Path(repo).expanduser().resolve()
    if not canonical.is_dir():
        raise WorkerProviderSessionProofError(
            "canonical repository must be an existing directory"
        )
    head = _run_git(canonical, "rev-parse", "HEAD").strip()
    status = _run_git(
        canonical,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    unstaged = _run_git(canonical, "diff", "--binary")
    staged = _run_git(canonical, "diff", "--cached", "--binary")
    return {
        "head": head,
        "status": status,
        "unstaged_diff_sha256": _sha256_bytes(unstaged.encode("utf-8")),
        "staged_diff_sha256": _sha256_bytes(staged.encode("utf-8")),
    }


def _persistent_mcp_snapshot(
    canonical: Path,
) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for relative in PERSISTENT_MCP_PATHS:
        path = canonical / relative
        if path.exists():
            if not path.is_file() or path.is_symlink():
                raise WorkerProviderSessionProofError(
                    f"unsafe persistent MCP path: {path}"
                )
            snapshot[str(relative)] = {
                "exists": True,
                "sha256": _sha256_file(path),
            }
        else:
            snapshot[str(relative)] = {
                "exists": False,
                "sha256": None,
            }
    return snapshot


def _preflight_mcp_python(
    python_executable: str,
    cwd: Path,
) -> dict[str, str]:
    path = Path(python_executable)
    if not path.is_absolute() or not path.is_file():
        raise WorkerProviderSessionProofError(
            "exact MCP Python executable is unavailable or not absolute"
        )
    cp = subprocess.run(
        [
            python_executable,
            "-c",
            (
                "import sys, mcp; "
                "print('PYTHON_EXECUTABLE=' + sys.executable); "
                "print('MCP_IMPORT=PASS')"
            ),
        ],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
    )
    if cp.returncode != 0:
        raise WorkerProviderSessionProofError(
            "exact MCP interpreter preflight failed:\n"
            + cp.stdout
            + cp.stderr
        )
    if "MCP_IMPORT=PASS" not in cp.stdout.splitlines():
        raise WorkerProviderSessionProofError(
            "exact MCP interpreter preflight did not confirm mcp import"
        )
    return {
        "python_executable": python_executable,
        "mcp_import": "PASS",
    }


def _provider_prompt(
    *,
    model_visible_tool_id: str,
    suite_id: str,
    require_tier: str,
) -> str:
    arguments = json.dumps(
        {
            "suite_id": suite_id,
            "require_tier": require_tier,
            "profile": False,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        "This is a machine-verification task, not a question. "
        f"You MUST invoke the only available tool, {model_visible_tool_id}, "
        "exactly once before producing any final response. "
        f"Call it with this exact JSON object: {arguments}. "
        "Do not claim success without the tool result. "
        "After the tool returns, output exactly two values copied from the "
        "actual tool result: EXECUTION_ID=<execution_id> and "
        "EVIDENCE_DIGEST=<evidence_digest>. "
        "If the tool cannot be invoked, output TOOL_CALL_FAILED instead. "
        "Do not read, edit, create, or otherwise mutate repository files. "
        "Do not use shell, web, subagents, git mutation, commit, push, merge, "
        "release, or any other tool."
    )


def build_provider_session_plan(
    *,
    canonical_repo: Path | str,
    runtime_root: Path | str,
    suite_id: str = "cf10-worker-pipeline",
    require_tier: str = "LOCAL_FOCUSED",
    profile: bool = False,
) -> dict[str, Any]:
    """Build the exact provider proof invocation without starting a process."""

    canonical = Path(canonical_repo).expanduser().resolve()
    if not canonical.is_dir():
        raise WorkerProviderSessionProofError(
            "canonical repository must be an existing directory"
        )
    runtime = _require_outside(
        canonical,
        Path(runtime_root),
        "runtime_root",
    )
    if profile is not False:
        raise WorkerProviderSessionProofError(
            "provider baseline proof requires profile=false"
        )

    suite = _require_string(suite_id, "suite_id")
    tier = _require_string(require_tier, "require_tier")

    runtime_config = registry.load_module_runtime_config(canonical)
    resolved_runtime = registry.resolve_default_runtime(canonical)

    if runtime_config.get("provider_adapter") != "CONSOLE_COMMAND":
        raise WorkerProviderSessionProofError(
            "provider adapter must remain CONSOLE_COMMAND"
        )
    command = runtime_config.get("command")
    if not isinstance(command, Mapping):
        raise WorkerProviderSessionProofError(
            "runtime command mapping missing"
        )
    if command.get("representation") != "ARGV_NO_SHELL":
        raise WorkerProviderSessionProofError(
            "runtime command representation must remain ARGV_NO_SHELL"
        )
    if command.get("shell") is not False:
        raise WorkerProviderSessionProofError(
            "provider proof forbids shell execution"
        )

    provider_id = _require_string(
        resolved_runtime.get("provider_id"),
        "provider_id",
    )
    if provider_id != adapter.SUPPORTED_PROVIDER:
        raise WorkerProviderSessionProofError(
            f"provider-session proof unsupported for provider: {provider_id}"
        )
    if resolved_runtime.get("command_representation") != "ARGV_NO_SHELL":
        raise WorkerProviderSessionProofError(
            "resolved runtime command representation drift"
        )

    executable = _require_string(
        resolved_runtime.get("executable"),
        "provider executable",
    )
    executable_path = Path(executable)
    if not executable_path.is_file():
        raise WorkerProviderSessionProofError(
            "configured provider executable is unavailable"
        )
    base_argv = command.get("base_argv")
    if (
        not isinstance(base_argv, list)
        or not base_argv
        or not all(isinstance(item, str) and item for item in base_argv)
        or base_argv[0] != executable
    ):
        raise WorkerProviderSessionProofError(
            "runtime base_argv/provider executable drift"
        )

    model_id = _require_string(
        resolved_runtime.get("model_id"),
        "provider model_id",
    )
    timeout_seconds = resolved_runtime.get("timeout_seconds")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise WorkerProviderSessionProofError(
            "provider timeout_seconds invalid"
        )

    budget = runtime_config.get("budget")
    if not isinstance(budget, Mapping):
        raise WorkerProviderSessionProofError("runtime budget missing")
    provider_budget = budget.get("provider_specific")
    if not isinstance(provider_budget, Mapping):
        raise WorkerProviderSessionProofError(
            "runtime provider-specific budget missing"
        )
    max_ai_credits = provider_budget.get("max_ai_credits")
    if (
        not isinstance(max_ai_credits, int)
        or isinstance(max_ai_credits, bool)
        or max_ai_credits <= 0
    ):
        raise WorkerProviderSessionProofError(
            "max_ai_credits must be positive"
        )

    model_visible_tool_id = (
        adapter.GITHUB_COPILOT_MCP_MODEL_TOOL_ID
    )
    permission_pattern = (
        adapter.GITHUB_COPILOT_MCP_PERMISSION_PATTERN
    )
    if model_visible_tool_id not in adapter.GITHUB_COPILOT_AVAILABLE_TOOLS:
        raise WorkerProviderSessionProofError(
            "model-visible MCP tool id is not canonical"
        )
    if permission_pattern in adapter.GITHUB_COPILOT_AVAILABLE_TOOLS:
        raise WorkerProviderSessionProofError(
            "permission selector leaked into available-tools universe"
        )

    python_executable = sys.executable
    python_path = Path(python_executable)
    if not python_path.is_absolute():
        raise WorkerProviderSessionProofError(
            "current MCP Python executable must be absolute"
        )

    mcp_script = (
        canonical / adapter.WORKER_VALIDATION_MCP_SCRIPT
    ).resolve()
    structured_root = runtime / STRUCTURED_DIRNAME

    mcp_config = {
        "mcpServers": {
            adapter.WORKER_VALIDATION_MCP_SERVER: {
                "type": "local",
                "command": python_executable,
                "args": [
                    str(mcp_script),
                    "--attempt-id",
                    PROOF_ID,
                    "--task-id",
                    TASK_ID,
                    "--work-front-id",
                    WORK_FRONT_ID,
                    "--decision-id",
                    PROOF_ID,
                    "--workspace-repo",
                    str(canonical),
                    "--evidence-root",
                    str(structured_root),
                ],
                "tools": [adapter.WORKER_VALIDATION_MCP_TOOL],
                "cwd": str(canonical),
            }
        }
    }
    mcp_config_json = json.dumps(
        mcp_config,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    prompt = _provider_prompt(
        model_visible_tool_id=model_visible_tool_id,
        suite_id=suite,
        require_tier=tier,
    )
    argv = [
        *[str(item) for item in base_argv],
        "-p",
        prompt,
        "--silent",
        "--model",
        model_id,
        "--additional-mcp-config",
        mcp_config_json,
        "--available-tools",
        model_visible_tool_id,
        "--allow-tool",
        permission_pattern,
        "--disable-builtin-mcps",
        "--no-ask-user",
        "--max-ai-credits",
        str(max_ai_credits),
        "--no-auto-update",
        "-C",
        str(canonical),
    ]
    if "--allow-all-tools" in argv:
        raise WorkerProviderSessionProofError(
            "provider proof must not use --allow-all-tools"
        )

    return {
        "schema_version": (
            "forprint_cf10_worker_provider_session_proof_plan_v0_1"
        ),
        "provider_id": provider_id,
        "command_representation": "ARGV_NO_SHELL",
        "provider_executable": executable,
        "provider_model": model_id,
        "timeout_seconds": timeout_seconds,
        "max_ai_credits": max_ai_credits,
        "canonical_repo": str(canonical),
        "runtime_root": str(runtime),
        "structured_evidence_root": str(structured_root),
        "provider_stdout_path": str(runtime / "provider_stdout.log"),
        "provider_stderr_path": str(runtime / "provider_stderr.log"),
        "proof_evidence_path": str(runtime / PROOF_FILENAME),
        "model_visible_tool_id": model_visible_tool_id,
        "permission_pattern": permission_pattern,
        "available_tools": [model_visible_tool_id],
        "allow_tools": [permission_pattern],
        "allow_all_tools": False,
        "no_ask_user": True,
        "persistent_mcp_config_written": False,
        "mcp_python_executable": python_executable,
        "mcp_python_path_resolved": False,
        "mcp_config": mcp_config,
        "suite_id": suite,
        "require_tier": tier,
        "profile": False,
        "argv": argv,
        "shell": False,
        "authority": {
            "proof_grants_execution_authority": False,
            "proof_grants_dispatch_authority": False,
            "proof_grants_canonical_write_authority": False,
            "proof_grants_commit_authority": False,
            "proof_grants_push_authority": False,
            "proof_grants_merge_authority": False,
            "proof_grants_release_authority": False,
            "proof_grants_promotion_authority": False,
        },
    }


def _validate_file_evidence(
    *,
    execution_dir: Path,
    evidence: Any,
    label: str,
) -> tuple[Path, str]:
    if not isinstance(evidence, Mapping):
        raise WorkerProviderSessionProofError(
            f"{label} evidence mapping missing"
        )
    raw_path = evidence.get("path")
    expected_sha = evidence.get("sha256")
    expected_size = evidence.get("size_bytes")
    if not isinstance(raw_path, str) or not raw_path:
        raise WorkerProviderSessionProofError(
            f"{label} evidence path missing"
        )
    if (
        not isinstance(expected_sha, str)
        or len(expected_sha) != 64
    ):
        raise WorkerProviderSessionProofError(
            f"{label} evidence sha256 invalid"
        )
    if (
        not isinstance(expected_size, int)
        or isinstance(expected_size, bool)
        or expected_size < 0
    ):
        raise WorkerProviderSessionProofError(
            f"{label} evidence size invalid"
        )

    path = Path(raw_path).expanduser().resolve()
    if not _is_inside(execution_dir, path):
        raise WorkerProviderSessionProofError(
            f"{label} evidence escaped execution directory"
        )
    if not path.is_file() or path.is_symlink():
        raise WorkerProviderSessionProofError(
            f"{label} evidence file missing or unsafe"
        )

    raw = path.read_bytes()
    observed_sha = _sha256_bytes(raw)
    if observed_sha != expected_sha:
        raise WorkerProviderSessionProofError(
            f"{label} evidence sha256 drift"
        )
    if len(raw) != expected_size:
        raise WorkerProviderSessionProofError(
            f"{label} evidence size drift"
        )
    return path, observed_sha


def validate_structured_execution_evidence(
    *,
    result_path: Path | str,
    expected_suite_id: str,
    expected_tier: str,
) -> dict[str, Any]:
    """Validate one immutable structured result and its hash-bound streams."""

    path = Path(result_path).expanduser().resolve()
    if not path.is_file() or path.is_symlink():
        raise WorkerProviderSessionProofError(
            "structured execution result missing or unsafe"
        )
    execution_dir = path.parent
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WorkerProviderSessionProofError(
            "structured execution result must be a mapping"
        )

    if value.get("capability_id") != "validation_suite":
        raise WorkerProviderSessionProofError(
            "structured execution capability_id drift"
        )
    if value.get("capability_version") != "0.2.0":
        raise WorkerProviderSessionProofError(
            "structured execution capability_version drift"
        )
    execution_id = _require_string(
        value.get("execution_id"),
        "execution_id",
    )
    if execution_id != execution_dir.name:
        raise WorkerProviderSessionProofError(
            "structured execution id/path drift"
        )
    if value.get("return_code") != 0:
        raise WorkerProviderSessionProofError(
            "structured execution return_code must be zero"
        )
    if value.get("timed_out") is not False:
        raise WorkerProviderSessionProofError(
            "structured execution timed_out drift"
        )
    if value.get("shell") is not False:
        raise WorkerProviderSessionProofError(
            "structured execution unexpectedly used shell"
        )
    if value.get("outcome") not in {
        "completed",
        "completed_with_stall_evidence",
    }:
        raise WorkerProviderSessionProofError(
            "structured execution outcome invalid"
        )
    elapsed = value.get("elapsed_seconds")
    if (
        not isinstance(elapsed, (int, float))
        or isinstance(elapsed, bool)
        or elapsed < 0
    ):
        raise WorkerProviderSessionProofError(
            "structured execution elapsed_seconds invalid"
        )

    authority = value.get("authority")
    if not isinstance(authority, Mapping) or not authority:
        raise WorkerProviderSessionProofError(
            "structured execution authority missing"
        )
    if any(item is not False for item in authority.values()):
        raise WorkerProviderSessionProofError(
            "structured execution authority widened"
        )

    stdout_path, stdout_sha = _validate_file_evidence(
        execution_dir=execution_dir,
        evidence=value.get("stdout_evidence"),
        label="stdout",
    )
    _stderr_path, stderr_sha = _validate_file_evidence(
        execution_dir=execution_dir,
        evidence=value.get("stderr_evidence"),
        label="stderr",
    )

    suite = _require_string(expected_suite_id, "expected_suite_id")
    tier = _require_string(expected_tier, "expected_tier")
    stdout_lines = stdout_path.read_text(
        encoding="utf-8",
        errors="strict",
    ).splitlines()
    required_lines = (
        f"VALIDATION_SUITE_ID={suite}",
        f"VALIDATION_SUITE_VERIFICATION_TIER={tier}",
        f"VALIDATION_SUITE=PASS suite={suite}",
    )
    for line in required_lines:
        if line not in stdout_lines:
            raise WorkerProviderSessionProofError(
                "hash-bound stdout validation contract missing exact line: "
                + line
            )

    evidence_digest = value.get("evidence_digest")
    if (
        not isinstance(evidence_digest, str)
        or len(evidence_digest) != 64
        or any(ch not in "0123456789abcdef" for ch in evidence_digest)
    ):
        raise WorkerProviderSessionProofError(
            "structured execution evidence_digest invalid"
        )
    digest_material = dict(value)
    digest_material.pop("evidence_digest", None)
    observed_digest = _canonical_sha256(digest_material)
    if observed_digest != evidence_digest:
        raise WorkerProviderSessionProofError(
            "structured execution evidence_digest drift"
        )

    return {
        "capability_id": "validation_suite",
        "capability_version": "0.2.0",
        "execution_id": execution_id,
        "elapsed_seconds": float(elapsed),
        "return_code": 0,
        "outcome": value.get("outcome"),
        "timed_out": False,
        "shell": False,
        "evidence_digest": evidence_digest,
        "result_path": str(path),
        "result_sha256": _sha256_file(path),
        "stdout_sha256": stdout_sha,
        "stderr_sha256": stderr_sha,
        "suite_id": suite,
        "require_tier": tier,
        "suite_pass": True,
        "authority_widened": False,
    }


def _write_immutable_yaml(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    if path.exists() or path.is_symlink():
        raise WorkerProviderSessionProofError(
            f"refusing to overwrite immutable proof evidence: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            dict(payload),
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ),
        encoding="utf-8",
    )


def run_provider_session_proof(
    *,
    canonical_repo: Path | str,
    runtime_root: Path | str,
    suite_id: str = "cf10-worker-pipeline",
    require_tier: str = "LOCAL_FOCUSED",
    profile: bool = False,
) -> dict[str, Any]:
    """Run one real provider session and prove one exact validation MCP call."""

    canonical = Path(canonical_repo).expanduser().resolve()
    runtime = _require_outside(
        canonical,
        Path(runtime_root),
        "runtime_root",
    )
    if runtime.exists() and any(runtime.iterdir()):
        raise WorkerProviderSessionProofError(
            "runtime_root already contains immutable proof evidence"
        )
    runtime.mkdir(parents=True, exist_ok=True)

    plan = build_provider_session_plan(
        canonical_repo=canonical,
        runtime_root=runtime,
        suite_id=suite_id,
        require_tier=require_tier,
        profile=profile,
    )

    mcp_script = (
        canonical / adapter.WORKER_VALIDATION_MCP_SCRIPT
    ).resolve()
    if not mcp_script.is_file() or mcp_script.is_symlink():
        raise WorkerProviderSessionProofError(
            "canonical Worker validation MCP server is missing or unsafe"
        )

    preflight = _preflight_mcp_python(
        plan["mcp_python_executable"],
        canonical,
    )

    before_repo = capture_repository_snapshot(canonical)
    before_persistent = _persistent_mcp_snapshot(canonical)

    structured_root = Path(plan["structured_evidence_root"])
    structured_root.mkdir(parents=True, exist_ok=False)

    try:
        provider_result = launch_process(
            argv=list(plan["argv"]),
            cwd=str(canonical),
            stdout_path=plan["provider_stdout_path"],
            stderr_path=plan["provider_stderr_path"],
            timeout_seconds=int(plan["timeout_seconds"]),
        )
    except WorkerProcessLaunchError as exc:
        raise WorkerProviderSessionProofError(str(exc)) from exc

    after_repo = capture_repository_snapshot(canonical)
    after_persistent = _persistent_mcp_snapshot(canonical)

    if before_repo != after_repo:
        raise WorkerProviderSessionProofError(
            "canonical repository state changed during provider proof"
        )
    if before_persistent != after_persistent:
        raise WorkerProviderSessionProofError(
            "persistent MCP configuration changed during provider proof"
        )
    if provider_result.get("return_code") != 0:
        raise WorkerProviderSessionProofError(
            "provider session returned non-zero"
        )
    if provider_result.get("timed_out") is not False:
        raise WorkerProviderSessionProofError(
            "provider session timed out"
        )
    if provider_result.get("shell") is not False:
        raise WorkerProviderSessionProofError(
            "provider session unexpectedly used shell"
        )

    result_paths = sorted(
        structured_root.glob(
            "structured-exec-*/execution_result_v0_1.yaml"
        )
    )
    if len(result_paths) != 1:
        raise WorkerProviderSessionProofError(
            "provider proof requires exactly one structured validation "
            f"execution; observed={len(result_paths)}"
        )

    structured = validate_structured_execution_evidence(
        result_path=result_paths[0],
        expected_suite_id=plan["suite_id"],
        expected_tier=plan["require_tier"],
    )

    provider_stdout_path = Path(plan["provider_stdout_path"]).resolve()
    provider_stderr_path = Path(plan["provider_stderr_path"]).resolve()
    if (
        not provider_stdout_path.is_file()
        or not provider_stderr_path.is_file()
    ):
        raise WorkerProviderSessionProofError(
            "provider stdout/stderr evidence missing"
        )
    provider_stdout = provider_stdout_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    payload: dict[str, Any] = {
        "schema_version": PROOF_SCHEMA,
        "state": "PASS",
        "proof_id": PROOF_ID,
        "provider_id": plan["provider_id"],
        "canonical_repo": str(canonical),
        "runtime_root": str(runtime),
        "provider": {
            "command_representation": "ARGV_NO_SHELL",
            "model_visible_tool_id": plan["model_visible_tool_id"],
            "permission_pattern": plan["permission_pattern"],
            "available_tools": list(plan["available_tools"]),
            "allow_tools": list(plan["allow_tools"]),
            "allow_all_tools": False,
            "no_ask_user": True,
            "shell": False,
            "argv": list(plan["argv"]),
            "stdout_path": str(provider_stdout_path),
            "stderr_path": str(provider_stderr_path),
            "stdout_sha256": _sha256_file(provider_stdout_path),
            "stderr_sha256": _sha256_file(provider_stderr_path),
            "return_code": provider_result.get("return_code"),
            "timed_out": provider_result.get("timed_out"),
            "outcome": provider_result.get("outcome"),
        },
        "mcp": {
            "server": adapter.WORKER_VALIDATION_MCP_SERVER,
            "tool": adapter.WORKER_VALIDATION_MCP_TOOL,
            "python_executable": plan["mcp_python_executable"],
            "python_path_resolved": False,
            "mcp_import_preflight": preflight["mcp_import"],
            "session_only_additional_mcp_config": True,
            "persistent_mcp_config_written": False,
        },
        "structured_execution": structured,
        "provider_stdout_bound_execution": (
            structured["execution_id"] in provider_stdout
        ),
        "provider_stdout_bound_digest": (
            structured["evidence_digest"] in provider_stdout
        ),
        "real_mcp_tool_invocation_proven": True,
        "repository_state_unchanged": True,
        "persistent_mcp_config_written": False,
        "authority_widened": False,
        "worker_attempt_created": False,
        "dispatch_created": False,
        "promotion_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "merge_performed": False,
        "release_performed": False,
        "before_repository": before_repo,
        "after_repository": after_repo,
        "evidence_path": str(runtime / PROOF_FILENAME),
        "hash_scope": "canonical_json_without_package_sha256",
    }
    payload["package_sha256"] = _canonical_sha256(payload)
    _write_immutable_yaml(Path(payload["evidence_path"]), payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Project-native real GitHub Copilot -> ForPrintValidation "
            "provider-session proof"
        )
    )
    parser.add_argument("--canonical-repo", default=".")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--suite", default="cf10-worker-pipeline")
    parser.add_argument("--require-tier", default="LOCAL_FOCUSED")
    args = parser.parse_args()

    try:
        result = run_provider_session_proof(
            canonical_repo=args.canonical_repo,
            runtime_root=args.runtime_root,
            suite_id=args.suite,
            require_tier=args.require_tier,
            profile=False,
        )
    except (
        OSError,
        ValueError,
        subprocess.SubprocessError,
        WorkerProviderSessionProofError,
    ) as exc:
        print(
            "CF10_WORKER_PROVIDER_SESSION_PROOF=FAIL "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    structured = result["structured_execution"]
    print("CF10_WORKER_PROVIDER_SESSION_PROOF=PASS")
    print("REAL_MCP_TOOL_INVOCATION_PROVEN=true")
    print(f"PROVIDER_ID={result['provider_id']}")
    print(
        "MODEL_TOOL_ID="
        + result["provider"]["model_visible_tool_id"]
    )
    print(
        "PERMISSION_PATTERN="
        + result["provider"]["permission_pattern"]
    )
    print(f"CAPABILITY_ID={structured['capability_id']}")
    print(f"CAPABILITY_VERSION={structured['capability_version']}")
    print(f"SUITE_ID={structured['suite_id']}")
    print(f"REQUIRE_TIER={structured['require_tier']}")
    print("PROFILE=false")
    print(f"EXECUTION_ID={structured['execution_id']}")
    print(f"ELAPSED_SECONDS={structured['elapsed_seconds']:.3f}")
    print("RETURN_CODE=0")
    print("TIMED_OUT=false")
    print(f"EVIDENCE_DIGEST={structured['evidence_digest']}")
    print(f"PROOF_EVIDENCE={result['evidence_path']}")
    print("SHELL=false")
    print("REPOSITORY_STATE_UNCHANGED=true")
    print("PERSISTENT_MCP_CONFIG_WRITTEN=false")
    print("AUTHORITY_WIDENED=false")
    print("WORKER_ATTEMPT_CREATED=false")
    print("A033_CREATED=false")
    print("A033_LAUNCHED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
