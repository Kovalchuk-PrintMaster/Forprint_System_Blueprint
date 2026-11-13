"""Pure Stage 4A origin-bound S4 Handoff v2 result candidate composer.

This module NEVER reads files or executes commands, creates artifacts, repairs a
malformed full Handoff, or grants result acceptance or execution authority.

The caller must supply an independently verified, frozen, attempt-bound
``governed_worker_context`` and its original Handoff manifest. Verifying the
provenance of that upstream snapshot is a separate Stage 4B responsibility.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import PurePosixPath
import re
from typing import Any


class S4ResultComposerError(ValueError):
    """Fail closed when a completion draft or frozen-origin binding is invalid."""


RESULT_SCHEMA = "forprint_assistant_handoff_v2_result_v0_1"
CONTEXT_SCHEMA = "forprint_governed_worker_context_projection_v0_1"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
ATTEMPT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]+\Z")

WORKER_FIELDS = frozenset({
    "status", "changed_paths", "validation_evidence",
    "self_repair_attempts", "unresolved_findings",
})
WORKER_OPTIONAL_FIELDS = frozenset({"partial_resume"})
PARTIAL_FIELDS = frozenset({
    "latest_completed_node", "latest_accepted_ref", "replay_forbidden_refs",
})
PARTIAL_STATUSES = frozenset({
    "PARTIAL", "INTERRUPTED", "BLOCKED", "RETRYABLE_FAILURE",
})
TERMINAL_STATUSES = frozenset({"PASS", "FAIL"})

RESERVED_FIELDS = frozenset({
    "attempt_id", "handoff_manifest_sha256", "source_state_fingerprint",
    "lifecycle_roadmap_cursor", "resume_coordinates", "schema_version",
    "origin_manifest", "governed_worker_context", "execution_bindings",
})


def _reject(message: str) -> None:
    raise S4ResultComposerError(message)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        _reject(f"{label} must be a string-keyed mapping")
    return value


def _digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _reject(f"{label} must be an exact lowercase SHA-256 string")
    return value


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _reject(f"{label} must be a non-empty string")
    return value


def _list_of_nonempty_strings(value: Any, label: str) -> list[str]:
    if (not isinstance(value, list) or not value or
            any(not isinstance(x, str) or not x.strip() for x in value)):
        _reject(f"{label} must be a non-empty list of non-empty strings")
    return value


def _check_changed_paths(value: Any) -> None:
    if not isinstance(value, list):
        _reject("changed_paths must be a list")
    checked: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item or "\\" in item:
            _reject("changed_paths contains an invalid path")
        path = PurePosixPath(item)
        if path.is_absolute() or ".." in path.parts or item != path.as_posix():
            _reject("changed_paths must be normalized project-relative POSIX paths")
        checked.append(item)
    if len(checked) != len(set(checked)):
        _reject("changed_paths contains duplicates")


def _check_items(value: Any, label: str, *, nonempty: bool) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        _reject(f"{label} must be a {'non-empty ' if nonempty else ''}list")
    if any(not ((isinstance(x, str) and x.strip()) or isinstance(x, dict)) for x in value):
        _reject(f"{label} contains an invalid item")


def _check_repair_attempts(value: Any) -> None:
    if not isinstance(value, list):
        _reject("self_repair_attempts must be a list")
    required = {
        "attempt_no", "repair_code", "authority_scope", "before_sha256",
        "repaired_payload_sha256", "outcome",
    }
    for item in value:
        if not isinstance(item, dict) or not required.issubset(item):
            _reject("self_repair_attempts contains invalid mapping")
        n = item["attempt_no"]
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            _reject("self_repair_attempts attempt number invalid")
        if item["repair_code"] != "DEDUPLICATE_IDENTICAL_CHANGED_PATHS":
            _reject("self_repair_attempts repair code not permitted")
        if item["authority_scope"] != "RESULT_ENVELOPE_MECHANICAL_ONLY":
            _reject("self_repair_attempts authority widening forbidden")
        _digest(item["before_sha256"], "self_repair_attempts.before_sha256")
        _digest(item["repaired_payload_sha256"], "self_repair_attempts.repaired_payload_sha256")
        if item["outcome"] not in ("APPLIED", "NO_CHANGE", "FAILED"):
            _reject("self_repair_attempts outcome invalid")


def _validated_frozen_origin(
    origin_manifest: Any,
    governed_worker_context: Any,
    expected_attempt_id: Any,
) -> dict[str, Any]:
    origin = _mapping(origin_manifest, "origin_manifest")
    governed = _mapping(governed_worker_context, "governed_worker_context")
    if governed.get("schema_version") != CONTEXT_SCHEMA:
        _reject("governed origin context schema invalid")
    attempt = _nonempty(expected_attempt_id, "expected_attempt_id")
    if ATTEMPT_RE.fullmatch(attempt) is None:
        _reject("expected_attempt_id format invalid")
    bound = _mapping(governed.get("execution_bindings"), "execution_bindings")
    if bound.get("attempt_id") != attempt:
        _reject("frozen origin attempt binding mismatch")
    origin_hash = _digest(origin.get("handoff_manifest_sha256"), "origin manifest hash")
    if _digest(governed.get("handoff_manifest_sha256"), "context handoff hash") != origin_hash:
        _reject("origin Handoff manifest binding mismatch")
    source = _digest(
        governed.get("handoff_source_state_fingerprint"),
        "origin source-state fingerprint",
    )
    authority = _mapping(governed.get("authority"), "origin authority")
    for flag in (
        "context_grants_authority", "dispatch_authority_granted",
        "release_authority_granted", "cross_repository_write_authority_granted",
    ):
        if authority.get(flag) is not False:
            _reject("frozen origin authority cannot be widened: " + flag)
    cursor = _mapping(governed.get("lifecycle_roadmap_cursor"), "frozen roadmap cursor")
    _nonempty(cursor.get("roadmap_sync"), "cursor.roadmap_sync")
    _nonempty(cursor.get("roadmap_status"), "cursor.roadmap_status")
    _mapping(cursor.get("open_work"), "cursor.open_work")
    for field in ("lifecycle_status_sha256", "roadmap_status_sha256"):
        _digest(cursor.get(field), "cursor." + field)
    return {
        "attempt_id": attempt,
        "handoff_manifest_sha256": origin_hash,
        "source_state_fingerprint": source,
        "lifecycle_roadmap_cursor": deepcopy(cursor),
    }


def compose_s4_result_candidate(
    *,
    origin_manifest: dict[str, Any],
    governed_worker_context: dict[str, Any],
    expected_attempt_id: str,
    worker_completion: dict[str, Any],
) -> dict[str, Any]:
    """Compose an in-memory candidate; never repair or overwrite authoritative fields.

    Only explicitly typed Worker-owned fields are accepted from the completion
    draft. All immutable S4 coordinates come from the trusted frozen origin.
    The caller must independently validate the returned candidate using the
    existing Handoff v2 result-envelope and S4 resume validators.
    """
    resume = _validated_frozen_origin(
        origin_manifest, governed_worker_context, expected_attempt_id,
    )
    completion = _mapping(worker_completion, "worker_completion")
    missing = WORKER_FIELDS - completion.keys()
    unknown = completion.keys() - WORKER_FIELDS - WORKER_OPTIONAL_FIELDS
    if missing or unknown:
        _reject(
            "worker_completion strict field contract invalid: "
            f"missing={sorted(missing)}, unsupported={sorted(unknown)}"
        )
    status = completion["status"]
    if not isinstance(status, str) or status not in PARTIAL_STATUSES | TERMINAL_STATUSES:
        _reject("worker_completion status not supported")
    _check_changed_paths(completion["changed_paths"])
    _check_items(completion["validation_evidence"], "validation_evidence", nonempty=True)
    _check_items(completion["unresolved_findings"], "unresolved_findings", nonempty=False)
    _check_repair_attempts(completion["self_repair_attempts"])

    if status in PARTIAL_STATUSES:
        if "partial_resume" not in completion:
            _reject("partial/resumable completion must include partial_resume")
        partial = _mapping(completion["partial_resume"], "partial_resume")
        if partial.keys() != PARTIAL_FIELDS:
            _reject("partial_resume has missing or unexpected fields")
        _nonempty(partial["latest_completed_node"], "partial latest_completed_node")
        _nonempty(partial["latest_accepted_ref"], "partial latest_accepted_ref")
        _list_of_nonempty_strings(partial["replay_forbidden_refs"], "partial replay_forbidden_refs")
        resume.update(deepcopy(partial))
    elif "partial_resume" in completion:
        _reject("non-partial result must not supply partial_resume")

    return {
        "schema_version": RESULT_SCHEMA,
        "handoff_manifest_sha256": resume["handoff_manifest_sha256"],
        "attempt_id": resume["attempt_id"],
        "status": status,
        "changed_paths": deepcopy(completion["changed_paths"]),
        "validation_evidence": deepcopy(completion["validation_evidence"]),
        "self_repair_attempts": deepcopy(completion["self_repair_attempts"]),
        "resume_coordinates": resume,
        "unresolved_findings": deepcopy(completion["unresolved_findings"]),
    }
