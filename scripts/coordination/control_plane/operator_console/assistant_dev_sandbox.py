from __future__ import annotations

import argparse
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.operator_console.session_projection import (
    SCHEMA_VERSION as SESSION_PROJECTION_SCHEMA,
)
from scripts.coordination.control_plane.workspace.provision import (
    WorkspaceProvisionError,
    capture_worker_baseline,
    load_workspace_plan_from_manifest,
    plan_workspace,
    provision_workspace,
)

SCHEMA_VERSION = "forprint_oc01_assistant_dev_sandbox_v0_1"
LOCAL_COMMIT_STATE = "DEPENDENCY_PENDING_CF10"
CHECKPOINT_STATE = "PROJECTION_AVAILABLE_NO_PAUSE_RESUME_AUTHORITY"
RESULT_SEAL_STATE = "SUPPORTED"
PROMOTION_STATE = "NEXT_SLICE_OC01_MINI_5"


class AssistantDevSandboxError(RuntimeError):
    pass


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AssistantDevSandboxError(f"{label} must be a mapping")
    return value


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AssistantDevSandboxError(f"{label} must be a non-empty string")
    return value.strip()


def _load_yaml(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise AssistantDevSandboxError(f"{label} missing: {path}")
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssistantDevSandboxError(f"{label} must be a mapping")
    return value


def _git(repo: Path, *args: str) -> str:
    cp = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode != 0:
        raise AssistantDevSandboxError(
            "git command failed rc="
            + str(cp.returncode)
            + ": git -C "
            + str(repo)
            + " "
            + " ".join(args)
            + "\n"
            + cp.stdout
        )
    return cp.stdout.strip()


def _validate_session_projection(
    projection: Mapping[str, Any],
) -> dict[str, str]:
    if projection.get("schema_version") != SESSION_PROJECTION_SCHEMA:
        raise AssistantDevSandboxError("session projection schema mismatch")

    authority = _mapping(projection.get("authority"), "session authority")
    if not authority or any(value is not False for value in authority.values()):
        raise AssistantDevSandboxError(
            "session projection unexpectedly grants authority"
        )

    actor = _mapping(projection.get("actor"), "session actor")
    if actor.get("actor_type") != "operator_assistant":
        raise AssistantDevSandboxError(
            "Assistant Dev Sandbox requires operator_assistant actor"
        )
    if actor.get("authority_conferred") is not False:
        raise AssistantDevSandboxError("actor context widened authority")

    return {
        "actor_type": "operator_assistant",
        "actor_id": _required_string(actor.get("actor_id"), "actor_id"),
    }


def _paths(repo: Path, *git_args: str) -> list[str]:
    raw = _git(repo, *git_args)
    return sorted({row.strip() for row in raw.splitlines() if row.strip()})


def _environment_delta(
    *,
    workspace: Path,
    base_head: str,
    inherited_paths: tuple[str, ...],
) -> dict[str, Any]:
    current_head = _git(workspace, "rev-parse", "HEAD")

    ancestor_cp = subprocess.run(
        ["git", "-C", str(workspace), "merge-base", "--is-ancestor", base_head, current_head],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    base_is_ancestor = ancestor_cp.returncode == 0

    committed_paths = (
        _paths(workspace, "diff", "--name-only", f"{base_head}..{current_head}")
        if current_head != base_head
        else []
    )
    working_paths = _paths(workspace, "diff", "--name-only", "HEAD")
    untracked_paths = _paths(
        workspace,
        "ls-files",
        "--others",
        "--exclude-standard",
    )
    all_paths = sorted(set(committed_paths) | set(working_paths) | set(untracked_paths))
    inherited = sorted(set(inherited_paths))

    local_commit_count: int | None
    if current_head == base_head:
        local_commit_count = 0
    elif base_is_ancestor:
        local_commit_count = int(
            _git(workspace, "rev-list", "--count", f"{base_head}..{current_head}")
        )
    else:
        local_commit_count = None

    return {
        "projection_authority": False,
        "base_head": base_head,
        "current_workspace_head": current_head,
        "base_is_ancestor_of_current_head": base_is_ancestor,
        "local_commit_count_observed": local_commit_count,
        "local_commit_support": LOCAL_COMMIT_STATE,
        "committed_paths_since_base": committed_paths,
        "working_paths_against_current_head": working_paths,
        "untracked_paths": untracked_paths,
        "all_changed_paths": all_paths,
        "inherited_durable_dirty_paths": inherited,
        "paths_outside_inherited_baseline": sorted(set(all_paths) - set(inherited)),
        "inherited_paths_currently_dirty": sorted(set(all_paths) & set(inherited)),
    }


def sandbox_status(
    *,
    manifest_path: Path | str,
    session_projection: Mapping[str, Any],
) -> dict[str, Any]:
    actor = _validate_session_projection(session_projection)

    try:
        plan = load_workspace_plan_from_manifest(manifest_path)
    except WorkspaceProvisionError as exc:
        raise AssistantDevSandboxError(str(exc)) from exc

    manifest = _load_yaml(Path(manifest_path).expanduser().resolve(), "workspace manifest")
    if manifest.get("canonical_write_allowed") is not False:
        raise AssistantDevSandboxError(
            "workspace canonical_write_allowed must remain false"
        )

    workspace = plan.layout.workspace_repo.resolve()
    canonical = plan.canonical_repo.resolve()
    if workspace == canonical:
        raise AssistantDevSandboxError("sandbox workspace cannot equal canonical repository")

    current_canonical_head = _git(canonical, "rev-parse", "HEAD")
    delta = _environment_delta(
        workspace=workspace,
        base_head=plan.source_head,
        inherited_paths=plan.durable_dirty_paths,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "state": "OPEN",
        "actor": {
            **actor,
            "authority_conferred": False,
        },
        "sandbox": {
            "module_id": manifest.get("module_id"),
            "worker_id": manifest.get("worker_id"),
            "attempt_id": manifest.get("attempt_id"),
            "manifest": str(Path(manifest_path).expanduser().resolve()),
            "workspace_repo": str(workspace),
            "canonical_repo": str(canonical),
            "isolated": workspace != canonical,
            "canonical_write_allowed": False,
        },
        "base": {
            "base_head": plan.source_head,
            "source_state_fingerprint": plan.source_state_fingerprint,
            "source_branch": plan.source_branch,
            "current_canonical_head": current_canonical_head,
            "canonical_head_drifted_since_base": current_canonical_head != plan.source_head,
            "durable_dirty_paths": list(plan.durable_dirty_paths),
        },
        "environment_delta": delta,
        "lifecycle": {
            "create": "SUPPORTED",
            "open": "SUPPORTED",
            "status": "SUPPORTED",
            "local_commits": LOCAL_COMMIT_STATE,
            "checkpoint_projection": CHECKPOINT_STATE,
            "canonical_pause_resume": "DEPENDENCY_PENDING_CF10",
            "result_seal": RESULT_SEAL_STATE,
            "canonical_promotion": PROMOTION_STATE,
        },
        "authority": {
            "state_authority": False,
            "lease_authority": False,
            "canonical_write_authority": False,
            "promotion_authority": False,
            "remote_push_authority": False,
            "merge_authority": False,
            "release_authority": False,
        },
    }


def create_sandbox(
    *,
    canonical_repo: Path | str,
    runtime_root: Path | str,
    module_id: str,
    worker_id: str,
    attempt_id: str,
    expected_base_head: str,
    session_projection: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_session_projection(session_projection)
    expected_base_head = _required_string(expected_base_head, "expected_base_head")

    try:
        plan = plan_workspace(
            canonical_repo=canonical_repo,
            runtime_root=runtime_root,
            module_id=module_id,
            worker_id=worker_id,
            attempt_id=attempt_id,
        )
    except (WorkspaceProvisionError, ValueError) as exc:
        raise AssistantDevSandboxError(str(exc)) from exc

    if plan.source_head != expected_base_head:
        raise AssistantDevSandboxError(
            "BASE_HEAD mismatch: expected="
            + expected_base_head
            + " observed="
            + plan.source_head
        )

    try:
        provision_workspace(plan)
        worker_baseline = capture_worker_baseline(plan)
    except WorkspaceProvisionError as exc:
        raise AssistantDevSandboxError(str(exc)) from exc

    status = sandbox_status(
        manifest_path=plan.layout.manifest,
        session_projection=session_projection,
    )
    status["state"] = "CREATED"
    status["worker_baseline"] = {
        "captured": True,
        "schema_version": worker_baseline.get("schema_version"),
        "baseline_fingerprint_sha256": worker_baseline.get(
            "baseline_fingerprint_sha256"
        ),
        "evidence_path": worker_baseline.get("evidence_path"),
    }
    return status


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OC-01 MINI-3 Assistant Dev Sandbox operator workflow"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--canonical-repo", required=True)
    create.add_argument("--runtime-root", required=True)
    create.add_argument("--module-id", required=True)
    create.add_argument("--worker-id", required=True)
    create.add_argument("--attempt-id", required=True)
    create.add_argument("--base-head", required=True)
    create.add_argument("--session-projection", required=True)

    for name in ("open", "status"):
        p = sub.add_parser(name)
        p.add_argument("--manifest", required=True)
        p.add_argument("--session-projection", required=True)

    args = parser.parse_args()
    session = _load_yaml(Path(args.session_projection), "session projection")

    if args.command == "create":
        result = create_sandbox(
            canonical_repo=Path(args.canonical_repo),
            runtime_root=Path(args.runtime_root),
            module_id=args.module_id,
            worker_id=args.worker_id,
            attempt_id=args.attempt_id,
            expected_base_head=args.base_head,
            session_projection=session,
        )
    else:
        result = sandbox_status(
            manifest_path=Path(args.manifest),
            session_projection=session,
        )
        if args.command == "open":
            result["state"] = "OPENED"

    print(
        yaml.safe_dump(
            result,
            sort_keys=False,
            allow_unicode=True,
            width=112,
        ).rstrip()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
