from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.coordination.control_plane.operator_console.console_api import (
    ConsoleApiError,
    ConsoleConfig,
    dispatch_action,
)
from scripts.coordination.control_plane.operator_console.session_projection import (
    build_session_projection,
)

SCHEMA_VERSION = "forprint_oc01_protected_terminal_real_proof_v0_1"
SESSION_FILENAME = "session_projection_v0_1.yaml"
PROOF_FILENAME = "protected_terminal_real_proof_v0_1.yaml"
CAPABILITIES = ("repo_head", "repo_status", "repo_diff_check")


class ProtectedTerminalProofError(RuntimeError):
    pass


def _run_git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode != 0:
        raise ProtectedTerminalProofError(
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


def _assert_outside(canonical: Path, path: Path, label: str) -> None:
    canonical = canonical.resolve()
    path = path.resolve()
    if path == canonical or canonical in path.parents:
        raise ProtectedTerminalProofError(
            f"{label} must remain outside canonical repository"
        )


def _write_immutable_yaml(path: Path, payload: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise ProtectedTerminalProofError(
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


def _repo_snapshot(repo: Path) -> dict[str, Any]:
    head = _run_git(repo, "rev-parse", "HEAD").strip()
    status_raw = _run_git(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    staged_raw = _run_git(repo, "diff", "--cached", "--name-only")
    unstaged_diff = _run_git(repo, "diff", "--binary")
    staged_diff = _run_git(repo, "diff", "--cached", "--binary")
    return {
        "head": head,
        "status_lines": status_raw.splitlines(),
        "staged_paths": [x for x in staged_raw.splitlines() if x],
        "unstaged_diff_sha256": _sha256_bytes(unstaged_diff.encode("utf-8")),
        "staged_diff_sha256": _sha256_bytes(staged_diff.encode("utf-8")),
    }


def _session_projection(
    *,
    canonical: Path,
    actor_id: str,
) -> dict[str, Any]:
    return build_session_projection(
        launch_request={
            "identity": {
                "module_id": "forprint_system_blueprint",
                "prompt_id": "oc01-mini7-protected-terminal-real-proof",
            }
        },
        worker_invocation={
            "attempt_id": "oc01-mini7-protected-terminal-real-proof",
            "worker_id": "oc01-mini7-proof",
            "workspace_repo": str(canonical),
            "heartbeat_seconds": 30,
        },
        actor_type="human_terminal",
        actor_id=actor_id,
        workspace_manifest=None,
    )


def _command_evidence(
    *,
    canonical: Path,
    response: Mapping[str, Any],
) -> dict[str, Any]:
    if response.get("ok") is not True:
        raise ProtectedTerminalProofError("Console API terminal response is not ok")
    result = response.get("result")
    if not isinstance(result, Mapping):
        raise ProtectedTerminalProofError("terminal result payload missing")

    stdout_path = Path(str(result.get("stdout_path", ""))).expanduser().resolve()
    stderr_path = Path(str(result.get("stderr_path", ""))).expanduser().resolve()
    for label, path in (("stdout", stdout_path), ("stderr", stderr_path)):
        _assert_outside(canonical, path, f"{label} evidence")
        if not path.is_file():
            raise ProtectedTerminalProofError(
                f"{label} evidence file missing: {path}"
            )

    if result.get("return_code") != 0:
        raise ProtectedTerminalProofError(
            f"terminal capability failed: {result.get('capability_id')}"
        )
    if result.get("timed_out") is not False:
        raise ProtectedTerminalProofError(
            f"terminal capability timed out: {result.get('capability_id')}"
        )
    if result.get("shell") is not False:
        raise ProtectedTerminalProofError("terminal proof unexpectedly used shell")

    authority = result.get("authority")
    if not isinstance(authority, Mapping) or any(
        value is not False for value in authority.values()
    ):
        raise ProtectedTerminalProofError(
            "terminal result unexpectedly widened authority"
        )

    actor = result.get("actor")
    if not isinstance(actor, Mapping):
        raise ProtectedTerminalProofError("terminal result actor missing")
    if actor.get("actor_type") != "human_terminal":
        raise ProtectedTerminalProofError("terminal proof actor type drift")
    if actor.get("authority_conferred") is not False:
        raise ProtectedTerminalProofError("terminal actor widened authority")

    if Path(str(result.get("cwd", ""))).resolve() != canonical:
        raise ProtectedTerminalProofError("terminal exact scope drift")

    return {
        "capability_id": result.get("capability_id"),
        "command_id": result.get("command_id"),
        "actor": dict(actor),
        "exact_scope": result.get("cwd"),
        "argv_sha256": result.get("argv_sha256"),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_sha256": _sha256_file(stdout_path),
        "stderr_sha256": _sha256_file(stderr_path),
        "stdout_text": stdout_path.read_text(encoding="utf-8"),
        "stderr_text": stderr_path.read_text(encoding="utf-8"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "return_code": result.get("return_code"),
        "timed_out": result.get("timed_out"),
        "outcome": result.get("outcome"),
        "shell": result.get("shell"),
        "authority": dict(authority),
    }


def run_real_protected_terminal_proof(
    *,
    canonical_repo: Path | str,
    runtime_root: Path | str,
    actor_id: str = "oc01-mini7-human-terminal-proof",
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    canonical = Path(canonical_repo).expanduser().resolve()
    runtime = Path(runtime_root).expanduser().resolve()

    if not canonical.is_dir():
        raise ProtectedTerminalProofError(
            "canonical_repo must be an existing directory"
        )
    _assert_outside(canonical, runtime, "runtime_root")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
        or timeout_seconds > 300
    ):
        raise ProtectedTerminalProofError(
            "timeout_seconds must be an integer between 1 and 300"
        )

    runtime.mkdir(parents=True, exist_ok=True)
    session_path = runtime / SESSION_FILENAME
    proof_path = runtime / PROOF_FILENAME
    if session_path.exists() or proof_path.exists():
        raise ProtectedTerminalProofError(
            "proof runtime already contains immutable session/proof evidence"
        )

    config = ConsoleConfig.build(
        canonical_root=canonical,
        runtime_root=runtime,
    )
    before = _repo_snapshot(canonical)

    session = _session_projection(
        canonical=canonical,
        actor_id=actor_id,
    )
    _write_immutable_yaml(session_path, session)

    commands: list[dict[str, Any]] = []
    try:
        for capability in CAPABILITIES:
            response = dispatch_action(
                config=config,
                action="terminal_run",
                payload={
                    "session_projection": str(session_path),
                    "capability_id": capability,
                    "enabled": True,
                    "confirm": True,
                    "timeout_seconds": timeout_seconds,
                    "evidence_dir": str(runtime / "terminal_evidence"),
                },
            )
            commands.append(
                _command_evidence(
                    canonical=canonical,
                    response=response,
                )
            )
    except (ConsoleApiError, ValueError) as exc:
        raise ProtectedTerminalProofError(str(exc)) from exc

    by_capability = {
        str(item["capability_id"]): item
        for item in commands
    }
    if set(by_capability) != set(CAPABILITIES):
        raise ProtectedTerminalProofError(
            "proof did not execute the exact registered capability set"
        )

    if by_capability["repo_head"]["stdout_text"].strip() != before["head"]:
        raise ProtectedTerminalProofError(
            "repo_head output differs from pre-proof canonical HEAD"
        )
    if (
        by_capability["repo_status"]["stdout_text"].splitlines()
        != before["status_lines"]
    ):
        raise ProtectedTerminalProofError(
            "repo_status output differs from pre-proof porcelain status"
        )
    if by_capability["repo_diff_check"]["stderr_text"]:
        raise ProtectedTerminalProofError(
            "repo_diff_check emitted stderr"
        )

    after = _repo_snapshot(canonical)
    if after != before:
        raise ProtectedTerminalProofError(
            "canonical repository evidence changed during terminal proof"
        )

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "state": "PASS",
        "proof_flow": "CONSOLE_API_DISPATCH_TO_EXISTING_PROTECTED_TERMINAL_GATEWAY",
        "manual_ssh_command_copying_required": False,
        "canonical_repo": str(canonical),
        "runtime_root": str(runtime),
        "session_projection_path": str(session_path),
        "capability_class": "READ_ONLY",
        "capabilities": list(CAPABILITIES),
        "before": before,
        "after": after,
        "commands": commands,
        "assertions": {
            "head_unchanged": True,
            "staging_unchanged": True,
            "status_unchanged": True,
            "unstaged_diff_bytes_unchanged": True,
            "staged_diff_bytes_unchanged": True,
            "repo_head_matches_before": True,
            "repo_status_matches_before": True,
            "repo_diff_check_passed": True,
            "all_commands_return_code_zero": True,
            "all_commands_not_timed_out": True,
            "all_commands_argv_no_shell": True,
            "stdout_stderr_outside_canonical": True,
        },
        "authority": {
            "state_authority": False,
            "dispatch_authority": False,
            "lease_authority": False,
            "canonical_write_authority": False,
            "commit_authority": False,
            "push_authority": False,
            "merge_authority": False,
            "release_authority": False,
            "promotion_authority": False,
        },
        "actions_performed": {
            "canonical_write": False,
            "staging": False,
            "commit": False,
            "push": False,
            "merge": False,
            "release": False,
            "promotion": False,
        },
        "evidence_path": str(proof_path),
        "hash_scope": "canonical_json_without_package_sha256",
    }
    payload["package_sha256"] = _canonical_sha256(payload)
    _write_immutable_yaml(proof_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-7 real Protected Terminal proof"
    )
    parser.add_argument("--canonical-repo", default=".")
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument(
        "--actor-id",
        default="oc01-mini7-human-terminal-proof",
    )
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()

    result = run_real_protected_terminal_proof(
        canonical_repo=args.canonical_repo,
        runtime_root=args.runtime_root,
        actor_id=args.actor_id,
        timeout_seconds=args.timeout_seconds,
    )

    print("OC01_MINI7_PROTECTED_TERMINAL_REAL_PROOF=PASS")
    print(f"PROOF_EVIDENCE={result['evidence_path']}")
    print(f"PROOF_SHA256={result['package_sha256']}")
    print(f"CANONICAL_HEAD={result['before']['head']}")
    print("CAPABILITY_COUNT=3")
    print("MANUAL_SSH_COMMAND_COPYING_REQUIRED=false")
    print("CANONICAL_STATE_UNCHANGED=true")
    print("STAGING_PERFORMED=false")
    print("COMMIT_PERFORMED=false")
    print("PUSH_PERFORMED=false")
    print("MERGE_PERFORMED=false")
    print("RELEASE_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
