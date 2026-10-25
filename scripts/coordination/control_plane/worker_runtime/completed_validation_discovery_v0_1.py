#!/usr/bin/env python3
"""Discover same-attempt immutable validation evidence after a lost tool reply.

Purely read-only and non-authorizing. No subprocesses, replay, completion
synthesis, test execution, mutation, or acceptance. The caller supplies only
trusted runtime-bound identities, never a Worker-controlled filesystem path.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.control_plane.worker_runtime.completed_execution_readback_v0_1 import (
    EXEC_ID, ReadbackBlocked, verify_completed_execution,
)

MAX_EXECUTION_ENTRIES = 64
MAX_RESULT_BYTES = 2 * 1024 * 1024


class DiscoveryBlocked(ValueError):
    """The bound attempt or evidence enumeration is not safe."""


def _safe_dir(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink() and path.resolve() == path


def _metadata_kind(path: Path) -> str | None:
    """Only a classification hint; validation records are independently verified."""
    if not path.is_file() or path.is_symlink() or path.resolve() != path:
        raise DiscoveryBlocked("unsafe structured result file")
    if path.stat().st_size > MAX_RESULT_BYTES:
        raise DiscoveryBlocked("structured result exceeds bounded size")
    try:
        payload = yaml.safe_load(path.read_bytes())
    except (yaml.YAMLError, UnicodeError) as exc:
        raise DiscoveryBlocked("unreadable structured execution result") from exc
    if not isinstance(payload, dict):
        raise DiscoveryBlocked("structured execution result not a mapping")
    return payload.get("capability_id")


def discover_completed_validation_evidence(
    *, attempt_root: str, expected_task_id: str,
    expected_work_front_id: str, expected_decision_id: str,
    expected_workspace: str,
) -> dict[str, Any]:
    attempt = Path(attempt_root)
    workspace = Path(expected_workspace)
    if not _safe_dir(attempt) or not attempt.is_absolute():
        raise DiscoveryBlocked("attempt root missing/unsafe")
    if not _safe_dir(workspace) or workspace != attempt / "workspace" / "repo":
        raise DiscoveryBlocked("workspace not bound to attempt")
    evidence_root = attempt / "evidence" / "structured_command"
    if not _safe_dir(evidence_root):
        raise DiscoveryBlocked("structured evidence root missing/unsafe")
    entries = sorted(evidence_root.iterdir(), key=lambda p: p.name)
    if len(entries) > MAX_EXECUTION_ENTRIES:
        raise DiscoveryBlocked("structured execution enumeration budget exceeded")

    completed: list[dict[str, Any]] = []
    incomplete: list[str] = []
    rejected: list[str] = []
    other_completed = 0
    for directory in entries:
        if not _safe_dir(directory) or not EXEC_ID.fullmatch(directory.name):
            raise DiscoveryBlocked("unsafe/unexpected execution directory")
        result_path = directory / "execution_result_v0_1.yaml"
        if not result_path.exists() and not result_path.is_symlink():
            incomplete.append(directory.name)
            continue
        kind = _metadata_kind(result_path)
        if kind != "validation_suite":
            other_completed += 1
            continue
        try:
            checked = verify_completed_execution(
                attempt_root=str(attempt), execution_id=directory.name,
                expected_task_id=expected_task_id,
                expected_work_front_id=expected_work_front_id,
                expected_decision_id=expected_decision_id,
                expected_workspace=str(workspace),
            )
        except (ReadbackBlocked, OSError, yaml.YAMLError, ValueError, TypeError):
            rejected.append(directory.name)
            continue
        completed.append({
            "execution_id": checked["execution_id"],
            "request_id": checked["request_id"],
            "result_sha256": checked["result_sha256"],
            "evidence_digest": checked["evidence_digest"],
            "status": "PASS_NON_AUTHORIZING",
        })

    if len({x["request_id"] for x in completed}) != len(completed):
        raise DiscoveryBlocked("duplicate verified validation request identity")
    return {
        "schema_version": "forprint_cf10_validation_evidence_discovery_v0_1",
        "status": "PARTIAL_NON_AUTHORIZING" if (incomplete or rejected) else "PASS_NON_AUTHORIZING",
        "attempt_id": attempt.name,
        "verified_completed_validation": completed,
        "incomplete_execution_ids": incomplete,
        "rejected_validation_ids": rejected,
        "other_completed_count": other_completed,
        "historical_source_fingerprint_verified": False,
        "worker_result_validated": False,
        "acceptance_granted": False,
        "replay_skip_authorized": False,
        "canonical_write_performed": False,
    }
