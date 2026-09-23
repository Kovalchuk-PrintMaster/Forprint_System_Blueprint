#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FAIL_CLASSES = (
    "STALE_SOURCE_STATE_FINGERPRINT",
    "STALE_LIFECYCLE_ROADMAP_CURSOR",
    "STALE_GENERATED_CONTEXT",
    "RESUME_ATTEMPT_BINDING_MISMATCH",
    "RESUME_MANIFEST_BINDING_MISMATCH",
    "RESUME_COORDINATES_INCOMPLETE",
)
PARTIAL_STATUSES = {
    "PARTIAL",
    "INTERRUPTED",
    "BLOCKED",
    "RETRYABLE_FAILURE",
}
BASE_RESUME_FIELDS = (
    "attempt_id",
    "handoff_manifest_sha256",
    "source_state_fingerprint",
    "lifecycle_roadmap_cursor",
)
PARTIAL_RESUME_FIELDS = (
    "latest_completed_node",
    "latest_accepted_ref",
    "replay_forbidden_refs",
)


class FreshnessResumeError(RuntimeError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _error(code: str, field: str, message: str) -> dict[str, str]:
    return {"code": code, "field": field, "message": message}


def _mapping(value: Any) -> bool:
    return isinstance(value, dict)


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in value
    )


def validate_freshness(
    origin_manifest: dict[str, Any],
    live_manifest: dict[str, Any],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    origin_fp = origin_manifest.get("source_state_fingerprint")
    live_fp = live_manifest.get("source_state_fingerprint")
    if not _non_empty(origin_fp) or not _non_empty(live_fp):
        errors.append(
            _error(
                "STALE_GENERATED_CONTEXT",
                "source_state_fingerprint",
                "origin and live source-state fingerprints are required",
            )
        )
    elif origin_fp != live_fp:
        errors.append(
            _error(
                "STALE_SOURCE_STATE_FINGERPRINT",
                "source_state_fingerprint",
                "origin handoff source-state fingerprint no longer matches live state",
            )
        )

    origin_cursor = origin_manifest.get("lifecycle_roadmap_cursor")
    live_cursor = live_manifest.get("lifecycle_roadmap_cursor")
    if not _mapping(origin_cursor) or not _mapping(live_cursor):
        errors.append(
            _error(
                "STALE_GENERATED_CONTEXT",
                "lifecycle_roadmap_cursor",
                "origin and live lifecycle/roadmap cursors are required",
            )
        )
    elif _canonical(origin_cursor) != _canonical(live_cursor):
        errors.append(
            _error(
                "STALE_LIFECYCLE_ROADMAP_CURSOR",
                "lifecycle_roadmap_cursor",
                "origin lifecycle/roadmap cursor no longer matches live reconciled state",
            )
        )

    origin_mode = origin_manifest.get("launch_mode")
    live_mode = live_manifest.get("launch_mode")
    if origin_mode != live_mode:
        errors.append(
            _error(
                "STALE_GENERATED_CONTEXT",
                "launch_mode",
                "origin and live launch modes differ",
            )
        )

    origin_schema = origin_manifest.get("schema_version")
    live_schema = live_manifest.get("schema_version")
    if origin_schema != live_schema:
        errors.append(
            _error(
                "STALE_GENERATED_CONTEXT",
                "schema_version",
                "origin and live runtime manifest schema revisions differ",
            )
        )

    return errors


def validate_resume(
    result: dict[str, Any],
    origin_manifest: dict[str, Any],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    resume = result.get("resume_coordinates")

    if not isinstance(resume, dict):
        return [
            _error(
                "RESUME_COORDINATES_INCOMPLETE",
                "resume_coordinates",
                "S4 requires structured resume_coordinates mapping",
            )
        ]

    missing = [field for field in BASE_RESUME_FIELDS if field not in resume]
    if missing:
        errors.append(
            _error(
                "RESUME_COORDINATES_INCOMPLETE",
                "resume_coordinates",
                "missing base fields: " + ",".join(missing),
            )
        )
        return errors

    attempt_id = result.get("attempt_id")
    if resume.get("attempt_id") != attempt_id:
        errors.append(
            _error(
                "RESUME_ATTEMPT_BINDING_MISMATCH",
                "resume_coordinates.attempt_id",
                "resume attempt binding must equal result attempt_id",
            )
        )

    manifest_hash = result.get("handoff_manifest_sha256")
    if resume.get("handoff_manifest_sha256") != manifest_hash:
        errors.append(
            _error(
                "RESUME_MANIFEST_BINDING_MISMATCH",
                "resume_coordinates.handoff_manifest_sha256",
                "resume manifest binding must equal result handoff manifest hash",
            )
        )

    if resume.get("source_state_fingerprint") != origin_manifest.get("source_state_fingerprint"):
        errors.append(
            _error(
                "STALE_SOURCE_STATE_FINGERPRINT",
                "resume_coordinates.source_state_fingerprint",
                "resume source-state binding must equal origin handoff fingerprint",
            )
        )

    if _canonical(resume.get("lifecycle_roadmap_cursor")) != _canonical(
        origin_manifest.get("lifecycle_roadmap_cursor")
    ):
        errors.append(
            _error(
                "STALE_LIFECYCLE_ROADMAP_CURSOR",
                "resume_coordinates.lifecycle_roadmap_cursor",
                "resume cursor binding must equal origin handoff cursor",
            )
        )

    retry_of = resume.get("retry_of_attempt_id")
    if retry_of is not None:
        if not _non_empty(retry_of):
            errors.append(
                _error(
                    "RESUME_COORDINATES_INCOMPLETE",
                    "resume_coordinates.retry_of_attempt_id",
                    "retry_of_attempt_id must be a non-empty string when present",
                )
            )
        elif retry_of == attempt_id:
            errors.append(
                _error(
                    "RESUME_ATTEMPT_BINDING_MISMATCH",
                    "resume_coordinates.retry_of_attempt_id",
                    "retry must create a new attempt_id",
                )
            )

    status = str(result.get("status", "")).upper()
    if status in PARTIAL_STATUSES:
        missing_partial = [field for field in PARTIAL_RESUME_FIELDS if field not in resume]
        if missing_partial:
            errors.append(
                _error(
                    "RESUME_COORDINATES_INCOMPLETE",
                    "resume_coordinates",
                    "partial/resumable status missing: " + ",".join(missing_partial),
                )
            )
        else:
            if not _non_empty(resume.get("latest_completed_node")):
                errors.append(
                    _error(
                        "RESUME_COORDINATES_INCOMPLETE",
                        "resume_coordinates.latest_completed_node",
                        "partial/resumable status requires latest_completed_node",
                    )
                )
            if not _non_empty(resume.get("latest_accepted_ref")):
                errors.append(
                    _error(
                        "RESUME_COORDINATES_INCOMPLETE",
                        "resume_coordinates.latest_accepted_ref",
                        "partial/resumable status requires latest_accepted_ref",
                    )
                )
            if not _string_list(resume.get("replay_forbidden_refs")):
                errors.append(
                    _error(
                        "RESUME_COORDINATES_INCOMPLETE",
                        "resume_coordinates.replay_forbidden_refs",
                        "partial/resumable status requires non-empty replay_forbidden_refs string list",
                    )
                )

    return errors


def validate_freshness_and_resume(
    origin_manifest: dict[str, Any],
    live_manifest: dict[str, Any],
    result: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    del root
    freshness_errors = validate_freshness(
        origin_manifest,
        live_manifest,
    )
    resume_errors = validate_resume(
        result,
        origin_manifest,
    )
    errors = [*freshness_errors, *resume_errors]
    return {
        "valid": not errors,
        "errors": errors,
        "freshness_valid": not freshness_errors,
        "resume_valid": not resume_errors,
        "fail_closed_classes": list(FAIL_CLASSES),
        "central_resume_routing_performed": False,
        "worker_dispatch_performed": False,
        "lifecycle_mutation_performed": False,
    }
