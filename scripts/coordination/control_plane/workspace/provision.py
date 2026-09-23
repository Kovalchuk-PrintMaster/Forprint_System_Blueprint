"""Isolated worker workspace provisioning for ForPrint Control Plane.

The canonical repository is never the worker workspace. A workspace is built as:
1. independent local clone,
2. detached checkout of the canonical pinned HEAD,
3. overlay of only continuity durable_dirty_paths.

The overlay copies the final working-tree state, not the canonical Git index/staging state.
This module grants no execution or dispatch authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.coordination.continuity import build_source_state

from .runtime import WorkspaceLayout, build_workspace_layout, workspace_manifest


class WorkspaceProvisionError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkspacePlan:
    layout: WorkspaceLayout
    canonical_repo: Path
    source_head: str
    source_branch: str | None
    durable_dirty_paths: tuple[str, ...]
    source_state_fingerprint: str | None
    base_mode: str = "DETACHED_LOCAL_CLONE"
    overlay_mode: str = "CONTINUITY_DURABLE_DIRTY_PATHS"


def _run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )


def _require(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 300,
) -> str:
    cp = _run(argv, cwd=cwd, timeout=timeout)
    if cp.returncode:
        raise WorkspaceProvisionError(
            "command failed rc="
            + str(cp.returncode)
            + ": "
            + " ".join(argv)
            + "\n"
            + cp.stdout
        )
    return cp.stdout.strip()


def _safe_relative_path(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceProvisionError("durable dirty path must be a non-empty string")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise WorkspaceProvisionError(
            f"durable dirty path escapes repository: {value!r}"
        )
    normalized = Path(*[part for part in rel.parts if part not in ("", ".")])
    if not normalized.parts:
        raise WorkspaceProvisionError("durable dirty path cannot resolve to repository root")
    return normalized


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _source_state(
    canonical_repo: Path,
    supplied: dict[str, Any] | None,
) -> dict[str, Any]:
    state = supplied if supplied is not None else build_source_state(canonical_repo)
    if not isinstance(state, dict):
        raise WorkspaceProvisionError("source state must be a mapping")
    head = state.get("git_head")
    paths = state.get("durable_dirty_paths")
    if not isinstance(head, str) or len(head.strip()) < 7:
        raise WorkspaceProvisionError("source state git_head missing")
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise WorkspaceProvisionError("source state durable_dirty_paths must be a string list")
    return state


def plan_workspace(
    *,
    canonical_repo: Path | str,
    runtime_root: Path | str,
    module_id: str,
    worker_id: str,
    attempt_id: str,
    source_state: dict[str, Any] | None = None,
) -> WorkspacePlan:
    canonical = Path(canonical_repo).expanduser().resolve()
    if not (canonical / ".git").exists():
        raise WorkspaceProvisionError(f"canonical repository is not a Git checkout: {canonical}")

    layout = build_workspace_layout(
        runtime_root=runtime_root,
        canonical_repo=canonical,
        module_id=module_id,
        worker_id=worker_id,
        attempt_id=attempt_id,
    )
    if _inside(layout.attempt_root, canonical) or _inside(canonical, layout.attempt_root):
        raise WorkspaceProvisionError("workspace and canonical repository must be isolated")

    state = _source_state(canonical, source_state)
    safe_paths = tuple(
        sorted({_safe_relative_path(item).as_posix() for item in state["durable_dirty_paths"]})
    )
    return WorkspacePlan(
        layout=layout,
        canonical_repo=canonical,
        source_head=str(state["git_head"]).strip(),
        source_branch=(
            str(state.get("git_branch")).strip()
            if state.get("git_branch") is not None
            else None
        ),
        durable_dirty_paths=safe_paths,
        source_state_fingerprint=(
            str(state.get("fingerprint_sha256")).strip()
            if state.get("fingerprint_sha256")
            else None
        ),
    )


def _remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _overlay_one(canonical: Path, workspace: Path, relative: str) -> None:
    rel = _safe_relative_path(relative)
    source = canonical / rel
    target = workspace / rel
    target.parent.mkdir(parents=True, exist_ok=True)

    if source.is_symlink():
        _remove_existing(target)
        os.symlink(os.readlink(source), target)
        return

    if source.is_file():
        _remove_existing(target)
        shutil.copy2(source, target, follow_symlinks=False)
        return

    if source.exists():
        raise WorkspaceProvisionError(
            f"durable dirty path must resolve to file/symlink/missing, not directory: {relative}"
        )

    _remove_existing(target)


def provision_workspace(
    plan: WorkspacePlan,
) -> dict[str, Any]:
    layout = plan.layout
    if layout.attempt_root.exists():
        raise WorkspaceProvisionError(
            f"attempt workspace already exists: {layout.attempt_root}"
        )

    layout.attempt_root.parent.mkdir(parents=True, exist_ok=True)
    clone = _run(
        [
            "git",
            "clone",
            "--no-checkout",
            "--no-hardlinks",
            str(plan.canonical_repo),
            str(layout.workspace_repo),
        ],
        timeout=900,
    )
    if clone.returncode:
        if layout.attempt_root.exists():
            shutil.rmtree(layout.attempt_root, ignore_errors=True)
        raise WorkspaceProvisionError("local clone failed:\n" + clone.stdout)

    try:
        _require(
            ["git", "checkout", "--detach", plan.source_head],
            cwd=layout.workspace_repo,
            timeout=300,
        )
        for relative in plan.durable_dirty_paths:
            _overlay_one(
                plan.canonical_repo,
                layout.workspace_repo,
                relative,
            )

        manifest = workspace_manifest(
            layout=layout,
            canonical_repo=plan.canonical_repo,
            source_head=plan.source_head,
            module_id=layout.attempt_root.parents[1].name,
            worker_id=layout.attempt_root.parent.name,
            attempt_id=layout.attempt_root.name,
        )
        manifest.update(
            {
                "base_mode": plan.base_mode,
                "overlay_mode": plan.overlay_mode,
                "source_branch": plan.source_branch,
                "source_state_fingerprint": plan.source_state_fingerprint,
                "durable_dirty_paths": list(plan.durable_dirty_paths),
                "provisioning_performed": True,
                "worker_launch_performed": False,
            }
        )
        layout.manifest.write_text(
            __import__("yaml").safe_dump(
                manifest,
                sort_keys=False,
                allow_unicode=True,
                width=110,
            ),
            encoding="utf-8",
        )
        return manifest
    except Exception:
        shutil.rmtree(layout.attempt_root, ignore_errors=True)
        raise


def _path_snapshot(root: Path, relative: str) -> dict[str, str | None]:
    path = root / _safe_relative_path(relative)
    if path.is_symlink():
        target = os.readlink(path)
        return {
            "kind": "symlink",
            "sha256": hashlib.sha256(target.encode("utf-8")).hexdigest(),
            "symlink_target": target,
            "mode": f"{path.lstat().st_mode & 0o7777:04o}",
        }
    if path.is_file():
        return {
            "kind": "file",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "symlink_target": None,
            "mode": f"{path.stat().st_mode & 0o7777:04o}",
        }
    if path.exists():
        return {
            "kind": "directory",
            "sha256": None,
            "symlink_target": None,
            "mode": f"{path.stat().st_mode & 0o7777:04o}",
        }
    return {
        "kind": "missing",
        "sha256": None,
        "symlink_target": None,
        "mode": None,
    }


def _working_delta(root: Path, durable_paths: tuple[str, ...]) -> list[str]:
    if not durable_paths:
        return []

    tracked = _require(
        [
            "git",
            "diff",
            "--name-status",
            "--find-renames",
            "--find-copies-harder",
            "HEAD",
            "--",
            *durable_paths,
        ],
        cwd=root,
    ).splitlines()
    untracked_raw = _require(
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            *durable_paths,
        ],
        cwd=root,
    )
    untracked = [f"??\t{row}" for row in untracked_raw.splitlines() if row.strip()]
    return sorted(tracked + untracked)


def verify_workspace_equivalence(
    plan: WorkspacePlan,
) -> dict[str, Any]:
    workspace = plan.layout.workspace_repo
    if not workspace.is_dir():
        raise WorkspaceProvisionError("workspace repository is missing")

    workspace_head = _require(["git", "rev-parse", "HEAD"], cwd=workspace)
    if workspace_head != plan.source_head:
        raise WorkspaceProvisionError(
            f"workspace HEAD mismatch: expected={plan.source_head} actual={workspace_head}"
        )

    mismatches: list[str] = []
    for relative in plan.durable_dirty_paths:
        canonical_snapshot = _path_snapshot(plan.canonical_repo, relative)
        workspace_snapshot = _path_snapshot(workspace, relative)
        if canonical_snapshot != workspace_snapshot:
            mismatches.append(relative)

    canonical_delta = _working_delta(plan.canonical_repo, plan.durable_dirty_paths)
    workspace_delta = _working_delta(workspace, plan.durable_dirty_paths)
    if canonical_delta != workspace_delta:
        raise WorkspaceProvisionError(
            "workspace working delta differs from canonical durable source state:\n"
            + "canonical="
            + repr(canonical_delta)
            + "\nworkspace="
            + repr(workspace_delta)
        )
    if mismatches:
        raise WorkspaceProvisionError(
            "workspace durable content mismatch: " + ",".join(mismatches)
        )

    branch = _require(
        ["git", "branch", "--show-current"],
        cwd=workspace,
    )
    return {
        "equivalent": True,
        "git_head": workspace_head,
        "workspace_branch": branch or None,
        "branch_identity_compared": False,
        "durable_dirty_paths": list(plan.durable_dirty_paths),
        "durable_dirty_path_count": len(plan.durable_dirty_paths),
        "working_delta": workspace_delta,
        "content_equivalence": True,
        "worker_dispatch_performed": False,
    }

WORKER_BASELINE_SCHEMA = "forprint_worker_workspace_baseline_v0_1"
WORKER_DELTA_SCHEMA = "forprint_worker_workspace_delta_v0_1"


def _dirty_paths_against_head(root: Path) -> list[str]:
    """Return final dirty paths relative to HEAD, including rename endpoints."""
    tracked_cp = _run(
        [
            "git",
            "diff",
            "--name-status",
            "--find-renames",
            "--find-copies-harder",
            "-z",
            "HEAD",
        ],
        cwd=root,
    )
    if tracked_cp.returncode:
        raise WorkspaceProvisionError(
            "cannot inspect workspace tracked delta:\n" + tracked_cp.stdout
        )

    tokens = [item for item in tracked_cp.stdout.split("\0") if item]
    paths: set[str] = set()
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if status.startswith(("R", "C")):
            if index + 1 >= len(tokens):
                raise WorkspaceProvisionError(
                    "malformed rename/copy record in workspace delta"
                )
            paths.add(_safe_relative_path(tokens[index]).as_posix())
            paths.add(_safe_relative_path(tokens[index + 1]).as_posix())
            index += 2
        else:
            if index >= len(tokens):
                raise WorkspaceProvisionError(
                    "malformed tracked record in workspace delta"
                )
            paths.add(_safe_relative_path(tokens[index]).as_posix())
            index += 1

    untracked_cp = _run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=root,
    )
    if untracked_cp.returncode:
        raise WorkspaceProvisionError(
            "cannot inspect workspace untracked paths:\n" + untracked_cp.stdout
        )
    for item in untracked_cp.stdout.split("\0"):
        if item:
            paths.add(_safe_relative_path(item).as_posix())
    return sorted(paths)


def _baseline_fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def capture_worker_baseline(
    plan: WorkspacePlan,
    *,
    equivalence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Capture exact pre-worker workspace content as runtime evidence only."""
    workspace = plan.layout.workspace_repo
    if not workspace.is_dir():
        raise WorkspaceProvisionError("workspace repository is missing")

    checked = equivalence if equivalence is not None else verify_workspace_equivalence(plan)
    if checked.get("equivalent") is not True:
        raise WorkspaceProvisionError(
            "worker baseline requires equivalent pre-dispatch workspace"
        )

    workspace_head = _require(["git", "rev-parse", "HEAD"], cwd=workspace)
    if workspace_head != plan.source_head:
        raise WorkspaceProvisionError(
            "worker baseline HEAD differs from workspace source_head"
        )

    baseline_dirty_paths = _dirty_paths_against_head(workspace)
    snapshot_paths = sorted(
        set(plan.durable_dirty_paths) | set(baseline_dirty_paths)
    )
    snapshots = {
        relative: _path_snapshot(workspace, relative)
        for relative in snapshot_paths
    }
    core: dict[str, Any] = {
        "schema_version": WORKER_BASELINE_SCHEMA,
        "source_head": plan.source_head,
        "workspace_repo": str(workspace),
        "durable_dirty_paths": list(plan.durable_dirty_paths),
        "baseline_dirty_paths": baseline_dirty_paths,
        "baseline_path_snapshots": snapshots,
        "worker_process_started": False,
        "authority_granted": False,
    }
    core["baseline_fingerprint_sha256"] = _baseline_fingerprint(core)

    evidence_dir = plan.layout.evidence
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "worker_baseline_v0_1.yaml"
    if evidence_path.exists():
        raise WorkspaceProvisionError(
            "worker baseline evidence already exists; recapture is forbidden"
        )
    evidence_path.write_text(
        __import__("yaml").safe_dump(
            core,
            sort_keys=False,
            allow_unicode=True,
            width=110,
        ),
        encoding="utf-8",
    )
    result = dict(core)
    result["evidence_path"] = str(evidence_path)
    return result


def _load_worker_baseline(plan: WorkspacePlan) -> dict[str, Any]:
    evidence_path = plan.layout.evidence / "worker_baseline_v0_1.yaml"
    if not evidence_path.is_file():
        raise WorkspaceProvisionError("worker baseline evidence is missing")
    value = __import__("yaml").safe_load(
        evidence_path.read_text(encoding="utf-8")
    )
    if not isinstance(value, dict):
        raise WorkspaceProvisionError(
            "worker baseline evidence must be a mapping"
        )
    return value


def derive_worker_delta(
    plan: WorkspacePlan,
    *,
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive worker mutations relative to the captured pre-worker baseline."""
    workspace = plan.layout.workspace_repo
    value = dict(
        baseline if baseline is not None else _load_worker_baseline(plan)
    )
    if value.get("schema_version") != WORKER_BASELINE_SCHEMA:
        raise WorkspaceProvisionError("worker baseline schema mismatch")
    if value.get("source_head") != plan.source_head:
        raise WorkspaceProvisionError("worker baseline source_head mismatch")
    if value.get("workspace_repo") != str(workspace):
        raise WorkspaceProvisionError(
            "worker baseline workspace binding mismatch"
        )

    expected_fingerprint = value.get("baseline_fingerprint_sha256")
    fingerprint_input = dict(value)
    fingerprint_input.pop("baseline_fingerprint_sha256", None)
    fingerprint_input.pop("evidence_path", None)
    if expected_fingerprint != _baseline_fingerprint(fingerprint_input):
        raise WorkspaceProvisionError("worker baseline fingerprint mismatch")

    workspace_head = _require(["git", "rev-parse", "HEAD"], cwd=workspace)
    if workspace_head != plan.source_head:
        raise WorkspaceProvisionError(
            "workspace HEAD changed after worker baseline"
        )

    snapshots = value.get("baseline_path_snapshots")
    if not isinstance(snapshots, dict):
        raise WorkspaceProvisionError(
            "worker baseline path snapshots missing"
        )

    post_dirty_paths = _dirty_paths_against_head(workspace)
    universe = sorted(set(snapshots) | set(post_dirty_paths))
    changed_paths: list[str] = []
    for relative in universe:
        if relative in snapshots:
            before = snapshots[relative]
            if not isinstance(before, dict):
                raise WorkspaceProvisionError(
                    f"invalid baseline snapshot for {relative}"
                )
            if _path_snapshot(workspace, relative) != before:
                changed_paths.append(relative)
        elif relative in post_dirty_paths:
            # Pre-worker path був clean/absent, post-worker став dirty.
            changed_paths.append(relative)

    return {
        "schema_version": WORKER_DELTA_SCHEMA,
        "source_head": plan.source_head,
        "baseline_fingerprint_sha256": expected_fingerprint,
        "inherited_dirty_paths": list(
            value.get("baseline_dirty_paths") or []
        ),
        "post_worker_dirty_paths": post_dirty_paths,
        "changed_paths": sorted(changed_paths),
        "worker_delta_exact": True,
        "authority_granted": False,
        "candidate_promoted": False,
        "canonical_write_performed": False,
    }


def seal_pre_dispatch_workspace(
    plan: WorkspacePlan,
    *,
    frozen_source_state: dict[str, Any],
) -> dict[str, Any]:
    """Seal a provisioned workspace only if canonical durable source stayed frozen.

    This writes runtime evidence only. It does not grant dispatch authority.
    """
    if not isinstance(frozen_source_state, dict):
        raise WorkspaceProvisionError("frozen_source_state must be a mapping")

    frozen_head = frozen_source_state.get("git_head")
    frozen_fingerprint = frozen_source_state.get("fingerprint_sha256")
    frozen_paths = frozen_source_state.get("durable_dirty_paths")
    if frozen_head != plan.source_head:
        raise WorkspaceProvisionError("frozen source HEAD does not match workspace plan")
    if not isinstance(frozen_fingerprint, str) or len(frozen_fingerprint) != 64:
        raise WorkspaceProvisionError("frozen source fingerprint missing")
    if not isinstance(frozen_paths, list):
        raise WorkspaceProvisionError("frozen durable_dirty_paths missing")
    if sorted(frozen_paths) != list(plan.durable_dirty_paths):
        raise WorkspaceProvisionError("frozen durable dirty paths do not match workspace plan")

    equivalence = verify_workspace_equivalence(plan)

    current = build_source_state(plan.canonical_repo)
    for key in ("git_head", "fingerprint_sha256"):
        if current.get(key) != frozen_source_state.get(key):
            _mark_workspace_blocked(
                plan,
                reason="CANONICAL_SOURCE_DRIFT",
                frozen_source_state=frozen_source_state,
                current_source_state=current,
            )
            raise WorkspaceProvisionError(
                f"canonical source changed after freeze: {key}"
            )
    if current.get("durable_dirty_paths") != frozen_source_state.get(
        "durable_dirty_paths"
    ):
        _mark_workspace_blocked(
            plan,
            reason="CANONICAL_DURABLE_PATH_SET_DRIFT",
            frozen_source_state=frozen_source_state,
            current_source_state=current,
        )
        raise WorkspaceProvisionError(
            "canonical durable dirty path set changed after freeze"
        )

    worker_baseline = capture_worker_baseline(
        plan,
        equivalence=equivalence,
    )

    manifest_path = plan.layout.manifest
    manifest = __import__("yaml").safe_load(
        manifest_path.read_text(encoding="utf-8")
    )
    if not isinstance(manifest, dict):
        raise WorkspaceProvisionError("workspace manifest is not a mapping")

    manifest.update(
        {
            "workspace_state": "PROVISIONED_NOT_DISPATCHED",
            "source_state_frozen": True,
            "source_state_fingerprint": frozen_fingerprint,
            "source_state_revalidated": True,
            "workspace_equivalence_validated": True,
            "worker_baseline_captured": True,
            "worker_baseline_fingerprint_sha256": worker_baseline[
                "baseline_fingerprint_sha256"
            ],
            "worker_baseline_evidence": worker_baseline["evidence_path"],
            "assistant_ack_validated": False,
            "explicit_dispatch_decision_recorded": False,
            "dispatch_authority_granted": False,
            "worker_launch_performed": False,
            "canonical_attempt_ledger_appended": False,
        }
    )
    manifest_path.write_text(
        __import__("yaml").safe_dump(
            manifest,
            sort_keys=False,
            allow_unicode=True,
            width=110,
        ),
        encoding="utf-8",
    )

    evidence_dir = plan.layout.evidence
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence = {
        "schema_version": "forprint_worker_workspace_pre_dispatch_evidence_v0_1",
        "workspace_state": "PROVISIONED_NOT_DISPATCHED",
        "source_head": plan.source_head,
        "source_state_fingerprint": frozen_fingerprint,
        "durable_dirty_path_count": len(plan.durable_dirty_paths),
        "equivalence": equivalence,
        "worker_baseline_captured": True,
        "worker_baseline_fingerprint_sha256": worker_baseline[
            "baseline_fingerprint_sha256"
        ],
        "worker_baseline_evidence": worker_baseline["evidence_path"],
        "assistant_ack_validated": False,
        "explicit_dispatch_decision_recorded": False,
        "dispatch_authority_granted": False,
        "worker_launch_performed": False,
        "canonical_attempt_ledger_appended": False,
    }
    evidence_path = evidence_dir / "pre_dispatch_workspace.yaml"
    evidence_path.write_text(
        __import__("yaml").safe_dump(
            evidence,
            sort_keys=False,
            allow_unicode=True,
            width=110,
        ),
        encoding="utf-8",
    )
    return {
        "manifest": manifest,
        "evidence": evidence,
        "evidence_path": str(evidence_path),
        "worker_baseline": worker_baseline,
    }


def _mark_workspace_blocked(
    plan: WorkspacePlan,
    *,
    reason: str,
    frozen_source_state: dict[str, Any],
    current_source_state: dict[str, Any],
) -> None:
    manifest_path = plan.layout.manifest
    try:
        manifest = __import__("yaml").safe_load(
            manifest_path.read_text(encoding="utf-8")
        )
    except Exception:
        manifest = {}
    if not isinstance(manifest, dict):
        manifest = {}
    manifest.update(
        {
            "workspace_state": "BLOCKED_PRE_DISPATCH",
            "block_reason": reason,
            "source_state_frozen_fingerprint": frozen_source_state.get(
                "fingerprint_sha256"
            ),
            "source_state_current_fingerprint": current_source_state.get(
                "fingerprint_sha256"
            ),
            "dispatch_authority_granted": False,
            "worker_launch_performed": False,
            "canonical_attempt_ledger_appended": False,
        }
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        __import__("yaml").safe_dump(
            manifest,
            sort_keys=False,
            allow_unicode=True,
            width=110,
        ),
        encoding="utf-8",
    )
