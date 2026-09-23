# Reusable isolated worker workspace layout v0.1.
# No directories, worktrees or worker processes are created by this module.

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class WorkspaceLayout:
    runtime_root: Path
    attempt_root: Path
    manifest: Path
    input_dir: Path
    workspace_repo: Path
    scratch: Path
    logs: Path
    candidate: Path
    evidence: Path
    result: Path
    recovery: Path
    quarantine: Path


def _safe_token(label: str, value: str) -> str:
    if not isinstance(value, str) or not _SAFE_TOKEN.fullmatch(value):
        raise ValueError(f"{label} must match {_SAFE_TOKEN.pattern}: {value!r}")
    return value


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def build_workspace_layout(
    *,
    runtime_root: Path | str,
    canonical_repo: Path | str,
    module_id: str,
    worker_id: str,
    attempt_id: str,
) -> WorkspaceLayout:
    module_id = _safe_token("module_id", module_id)
    worker_id = _safe_token("worker_id", worker_id)
    attempt_id = _safe_token("attempt_id", attempt_id)
    runtime = Path(runtime_root).expanduser().resolve()
    canonical = Path(canonical_repo).expanduser().resolve()
    attempt = runtime / module_id / worker_id / attempt_id
    workspace_repo = attempt / "workspace" / "repo"

    if _inside(attempt, canonical) or _inside(canonical, attempt):
        raise ValueError("worker attempt workspace must be isolated from canonical repository")
    if workspace_repo == canonical:
        raise ValueError("canonical repository cannot be the worker workspace repository")

    return WorkspaceLayout(
        runtime_root=runtime,
        attempt_root=attempt,
        manifest=attempt / "manifest.yaml",
        input_dir=attempt / "input",
        workspace_repo=workspace_repo,
        scratch=attempt / "scratch",
        logs=attempt / "logs",
        candidate=attempt / "artifacts" / "candidate",
        evidence=attempt / "evidence",
        result=attempt / "result",
        recovery=attempt / "recovery",
        quarantine=attempt / "quarantine",
    )


def workspace_manifest(
    *,
    layout: WorkspaceLayout,
    canonical_repo: Path | str,
    source_head: str,
    module_id: str,
    worker_id: str,
    attempt_id: str,
) -> dict[str, object]:
    if not isinstance(source_head, str) or not source_head.strip():
        raise ValueError("source_head is required")
    canonical = Path(canonical_repo).expanduser().resolve()
    return {
        "schema_version": "forprint_worker_workspace_manifest_v0_1",
        "module_id": module_id,
        "worker_id": worker_id,
        "attempt_id": attempt_id,
        "canonical_repo": str(canonical),
        "source_head": source_head.strip(),
        "runtime_root": str(layout.runtime_root),
        "attempt_root": str(layout.attempt_root),
        "workspace_repo": str(layout.workspace_repo),
        "candidate_dir": str(layout.candidate),
        "canonical_write_allowed": False,
        "provisioning_performed": False,
        "worker_launch_performed": False,
    }
