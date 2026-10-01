from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.operator_console.session_projection import (
    ALLOWED_ACTOR_TYPES,
    SCHEMA_VERSION as SESSION_PROJECTION_SCHEMA,
)
from scripts.coordination.control_plane.worker_runtime.launcher import launch_process

SCHEMA_VERSION = "forprint_oc01_protected_terminal_gateway_v0_1"
COMMAND_REPRESENTATION = "ARGV_NO_SHELL"
CANCEL_STATE = "DEPENDENCY_PENDING_CF10"

TERMINAL_ACTOR_TYPES = frozenset(
    actor
    for actor in ALLOWED_ACTOR_TYPES
    if actor in {"operator_assistant", "human_terminal"}
)

READ_ONLY_CAPABILITIES: dict[str, tuple[str, ...]] = {
    "repo_status": ("status", "--short", "--untracked-files=all"),
    "repo_head": ("rev-parse", "HEAD"),
    "repo_diff_check": ("diff", "--check"),
}


class ProtectedTerminalError(RuntimeError):
    pass


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProtectedTerminalError(f"{label} must be a mapping")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProtectedTerminalError(f"{label} must be a non-empty string")
    return value.strip()


def _argv_sha256(argv: list[str]) -> str:
    return hashlib.sha256("\0".join(argv).encode("utf-8")).hexdigest()


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ProtectedTerminalError(f"{label} missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProtectedTerminalError(f"{label} must be a mapping")
    return value


def _validate_session_projection(
    session_projection: Mapping[str, Any],
) -> tuple[str, str]:
    if session_projection.get("schema_version") != SESSION_PROJECTION_SCHEMA:
        raise ProtectedTerminalError("session projection schema mismatch")

    authority = _mapping(
        session_projection.get("authority"),
        "session projection authority",
    )
    if not authority or any(value is not False for value in authority.values()):
        raise ProtectedTerminalError(
            "session projection unexpectedly grants authority"
        )

    actor = _mapping(session_projection.get("actor"), "session projection actor")
    actor_type = _required_string(actor.get("actor_type"), "actor_type")
    actor_id = _required_string(actor.get("actor_id"), "actor_id")
    if actor_type not in TERMINAL_ACTOR_TYPES:
        raise ProtectedTerminalError(
            "Protected Terminal requires operator_assistant or human_terminal"
        )
    if actor.get("authority_conferred") is not False:
        raise ProtectedTerminalError("actor context widened authority")
    return actor_type, actor_id


def _validate_git_scope(cwd: Path | str) -> Path:
    scope = Path(cwd).expanduser().resolve()
    if not scope.is_dir():
        raise ProtectedTerminalError("cwd must be an existing directory")
    result = subprocess.run(
        ["git", "-C", str(scope), "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ProtectedTerminalError("cwd must be inside a Git repository")
    top = Path(result.stdout.strip()).resolve()
    if top != scope:
        raise ProtectedTerminalError(
            "Protected Terminal v0.1 requires exact Git repository root scope"
        )
    return scope


def list_capabilities() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "default_enabled": False,
        "command_representation": COMMAND_REPRESENTATION,
        "arbitrary_command_text_allowed": False,
        "shell": False,
        "capabilities": [
            {
                "capability_id": capability_id,
                "class": "READ_ONLY",
                "execution_state": "AVAILABLE_WHEN_EXPLICITLY_ENABLED",
            }
            for capability_id in sorted(READ_ONLY_CAPABILITIES)
        ],
        "safe_write": {
            "class": "SAFE_WRITE",
            "execution_state": "BLOCKED",
            "blocker": "EXCLUSIVE_MODULE_LEASE_NOT_PROVEN",
        },
        "cancel": {
            "state": CANCEL_STATE,
            "implemented_by_oc01": False,
        },
    }


def build_terminal_plan(
    *,
    capability_id: str,
    cwd: Path | str,
    session_projection: Mapping[str, Any],
    enabled: bool = False,
    capability_class: str = "READ_ONLY",
    timeout_seconds: int = 30,
    evidence_dir: Path | str | None = None,
) -> dict[str, Any]:
    if enabled is not True:
        raise ProtectedTerminalError(
            "Protected Terminal is default-off; explicit enable is required"
        )

    actor_type, actor_id = _validate_session_projection(session_projection)

    if capability_class == "SAFE_WRITE":
        raise ProtectedTerminalError(
            "SAFE_WRITE blocked: EXCLUSIVE_MODULE_LEASE_NOT_PROVEN"
        )
    if capability_class != "READ_ONLY":
        raise ProtectedTerminalError("unsupported capability class")

    capability_id = _required_string(capability_id, "capability_id")
    args = READ_ONLY_CAPABILITIES.get(capability_id)
    if args is None:
        raise ProtectedTerminalError("unknown Protected Terminal capability")

    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
        or timeout_seconds > 300
    ):
        raise ProtectedTerminalError(
            "timeout_seconds must be an integer between 1 and 300"
        )

    scope = _validate_git_scope(cwd)

    git_executable = shutil.which("git")
    if not git_executable:
        raise ProtectedTerminalError("git executable is unavailable")
    argv = [
        str(Path(git_executable).resolve()),
        "--no-optional-locks",
        *args,
    ]

    evidence_root = (
        Path(evidence_dir).expanduser().resolve()
        if evidence_dir is not None
        else Path(tempfile.gettempdir()).resolve()
        / "forprint-oc01"
        / "protected_terminal"
    )
    try:
        evidence_root.relative_to(scope)
    except ValueError:
        pass
    else:
        raise ProtectedTerminalError(
            "evidence_dir must remain outside protected repository scope"
        )

    command_id_material = {
        "capability_id": capability_id,
        "cwd": str(scope),
        "actor_type": actor_type,
        "actor_id": actor_id,
        "argv_sha256": _argv_sha256(argv),
    }
    command_id = "oc01-terminal-" + hashlib.sha256(
        json.dumps(
            command_id_material,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:16]

    command_dir = evidence_root / command_id
    return {
        "schema_version": SCHEMA_VERSION,
        "command_id": command_id,
        "enabled": True,
        "capability": {
            "capability_id": capability_id,
            "class": "READ_ONLY",
            "exact_scope": str(scope),
        },
        "actor": {
            "actor_type": actor_type,
            "actor_id": actor_id,
            "source": "OC01_MINI_1_SESSION_PROJECTION",
            "authority_conferred": False,
        },
        "execution": {
            "command_representation": COMMAND_REPRESENTATION,
            "argv": argv,
            "argv_sha256": _argv_sha256(argv),
            "cwd": str(scope),
            "shell": False,
            "timeout_seconds": timeout_seconds,
            "stdout_path": str(command_dir / "stdout.log"),
            "stderr_path": str(command_dir / "stderr.log"),
        },
        "authority": {
            "gateway_grants_execution_authority": False,
            "gateway_grants_dispatch_authority": False,
            "gateway_grants_lease_authority": False,
            "gateway_grants_canonical_write_authority": False,
            "commit_allowed": False,
            "push_allowed": False,
            "merge_allowed": False,
            "release_allowed": False,
            "promotion_allowed": False,
        },
        "cancel": {
            "state": CANCEL_STATE,
            "available": False,
        },
    }


def execute_terminal_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    plan = _mapping(plan, "terminal plan")
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ProtectedTerminalError("terminal plan schema mismatch")
    if plan.get("enabled") is not True:
        raise ProtectedTerminalError("terminal plan is not enabled")

    actor = _mapping(plan.get("actor"), "actor")
    actor_type = _required_string(actor.get("actor_type"), "actor_type")
    _required_string(actor.get("actor_id"), "actor_id")
    if actor_type not in TERMINAL_ACTOR_TYPES:
        raise ProtectedTerminalError("terminal plan actor type is not allowed")
    if actor.get("source") != "OC01_MINI_1_SESSION_PROJECTION":
        raise ProtectedTerminalError("terminal plan actor source drift")
    if actor.get("authority_conferred") is not False:
        raise ProtectedTerminalError("terminal plan actor widened authority")

    capability = _mapping(plan.get("capability"), "capability")
    if capability.get("class") != "READ_ONLY":
        raise ProtectedTerminalError("only READ_ONLY execution is enabled")
    capability_id = _required_string(
        capability.get("capability_id"),
        "capability_id",
    )
    if capability_id not in READ_ONLY_CAPABILITIES:
        raise ProtectedTerminalError("unknown capability in terminal plan")

    authority = _mapping(plan.get("authority"), "authority")
    if not authority or any(value is not False for value in authority.values()):
        raise ProtectedTerminalError("terminal plan authority widened")

    execution = _mapping(plan.get("execution"), "execution")
    exact_scope = _validate_git_scope(
        _required_string(capability.get("exact_scope"), "exact_scope")
    )
    execution_cwd = _validate_git_scope(
        _required_string(execution.get("cwd"), "cwd")
    )
    if execution_cwd != exact_scope:
        raise ProtectedTerminalError("terminal execution cwd / exact scope drift")
    if execution.get("command_representation") != COMMAND_REPRESENTATION:
        raise ProtectedTerminalError("command representation drift")
    if execution.get("shell") is not False:
        raise ProtectedTerminalError("shell execution is forbidden")

    argv = execution.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(item, str) and item for item in argv)
    ):
        raise ProtectedTerminalError("terminal argv invalid")

    expected_args = READ_ONLY_CAPABILITIES[capability_id]
    git_executable = shutil.which("git")
    if not git_executable:
        raise ProtectedTerminalError("git executable is unavailable")
    expected_argv = [
        str(Path(git_executable).resolve()),
        "--no-optional-locks",
        *expected_args,
    ]
    if argv != expected_argv:
        raise ProtectedTerminalError(
            "terminal argv does not match registered capability"
        )
    if execution.get("argv_sha256") != _argv_sha256(argv):
        raise ProtectedTerminalError("terminal argv digest mismatch")

    stdout_path = Path(
        _required_string(execution.get("stdout_path"), "stdout_path")
    ).expanduser().resolve()
    stderr_path = Path(
        _required_string(execution.get("stderr_path"), "stderr_path")
    ).expanduser().resolve()
    for label, output_path in (
        ("stdout_path", stdout_path),
        ("stderr_path", stderr_path),
    ):
        try:
            output_path.relative_to(exact_scope)
        except ValueError:
            pass
        else:
            raise ProtectedTerminalError(
                f"{label} must remain outside protected repository scope"
            )

    result = launch_process(
        argv=list(argv),
        cwd=str(execution_cwd),
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout_seconds=execution.get("timeout_seconds"),
    )

    return {
        "schema_version": "forprint_oc01_protected_terminal_result_v0_1",
        "command_id": plan.get("command_id"),
        "capability_id": capability_id,
        "actor": plan.get("actor"),
        "cwd": execution.get("cwd"),
        "argv_sha256": execution.get("argv_sha256"),
        "stdout_path": result.get("stdout_path"),
        "stderr_path": result.get("stderr_path"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "return_code": result.get("return_code"),
        "timed_out": result.get("timed_out"),
        "outcome": result.get("outcome"),
        "shell": result.get("shell"),
        "cancel": {
            "state": CANCEL_STATE,
            "available": False,
            "cancelled": False,
        },
        "authority": {
            "gateway_granted_authority": False,
            "canonical_write_performed": False,
            "commit_performed": False,
            "push_performed": False,
            "merge_performed": False,
            "release_performed": False,
            "promotion_performed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-2 capability-shaped Protected Terminal gateway"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")

    for name in ("plan", "run"):
        p = sub.add_parser(name)
        p.add_argument("--capability", required=True)
        p.add_argument("--cwd", required=True)
        p.add_argument("--session-projection", required=True)
        p.add_argument("--timeout-seconds", type=int, default=30)
        p.add_argument("--evidence-dir")
        p.add_argument("--confirm-enable", action="store_true")

    args = parser.parse_args()

    if args.command == "capabilities":
        print(yaml.safe_dump(
            list_capabilities(),
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip())
        return 0

    plan = build_terminal_plan(
        capability_id=args.capability,
        cwd=Path(args.cwd),
        session_projection=_load_yaml(
            Path(args.session_projection),
            "session projection",
        ),
        enabled=args.confirm_enable,
        timeout_seconds=args.timeout_seconds,
        evidence_dir=Path(args.evidence_dir) if args.evidence_dir else None,
    )

    if args.command == "plan":
        print(yaml.safe_dump(
            plan,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip())
        return 0

    result = execute_terminal_plan(plan)
    print(yaml.safe_dump(
        result,
        sort_keys=False,
        allow_unicode=True,
        width=112,
    ).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
