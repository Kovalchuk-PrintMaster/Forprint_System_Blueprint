# Strict provider-stdout return boundary for governed CF-10 Workers.
#
# This module is transport/validation plumbing only. It grants no execution,
# acceptance, promotion, Git, release, or retry authority.

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.assistant_handoff_v2_result_v0_1 import (
    validate_result_envelope,
)


FRAME_BEGIN = "FORPRINT_HANDOFF_V2_RESULT_BEGIN"
FRAME_END = "FORPRINT_HANDOFF_V2_RESULT_END"
RESULT_FILENAME = "worker_result.yaml"


class WorkerResultReturnError(RuntimeError):
    pass


def extract_framed_result(stdout_text: str) -> dict[str, Any]:
    if not isinstance(stdout_text, str):
        raise WorkerResultReturnError("provider stdout must be text")

    begin_count = stdout_text.count(FRAME_BEGIN)
    end_count = stdout_text.count(FRAME_END)

    if begin_count == 0 and end_count == 0:
        raise WorkerResultReturnError("missing result frame")
    if begin_count == 0 and end_count:
        raise WorkerResultReturnError("unexpected result frame end")
    if begin_count and end_count == 0:
        raise WorkerResultReturnError("unterminated result frame")
    if begin_count != 1 or end_count != 1:
        raise WorkerResultReturnError(
            "exactly one result frame is required"
        )

    begin_at = stdout_text.find(FRAME_BEGIN)
    end_at = stdout_text.find(FRAME_END)
    if end_at < begin_at:
        raise WorkerResultReturnError("unexpected result frame ordering")

    before = stdout_text[:begin_at]
    payload_start = begin_at + len(FRAME_BEGIN)
    payload_text = stdout_text[payload_start:end_at]
    after = stdout_text[end_at + len(FRAME_END):]

    if before.strip() or after.strip():
        raise WorkerResultReturnError(
            "non-whitespace content outside result frame is forbidden"
        )

    try:
        payload = yaml.safe_load(payload_text)
    except yaml.YAMLError as exc:
        raise WorkerResultReturnError(
            f"result frame YAML invalid: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise WorkerResultReturnError(
            "result frame payload must be a mapping"
        )

    return payload


def materialize_worker_result(
    *,
    root: Path | str,
    attempt_root: Path | str,
    stdout_path: Path | str,
    origin_manifest: dict[str, Any],
    expected_attempt_id: str,
) -> dict[str, Any]:
    canonical = Path(root).resolve()
    attempt = Path(attempt_root).expanduser().resolve()
    stdout = Path(stdout_path).expanduser().resolve()

    if not attempt.is_dir():
        raise WorkerResultReturnError("bound attempt runtime is missing")
    if not stdout.is_file() or stdout.is_symlink():
        raise WorkerResultReturnError(
            "bound provider stdout is missing or unsafe"
        )

    try:
        stdout.relative_to(attempt)
    except ValueError as exc:
        raise WorkerResultReturnError(
            "provider stdout escapes bound attempt runtime"
        ) from exc

    result_dir = attempt / "result"
    if result_dir.is_symlink():
        raise WorkerResultReturnError(
            "result directory cannot be a symlink"
        )
    if result_dir.exists() and not result_dir.is_dir():
        raise WorkerResultReturnError(
            "result path exists but is not a directory"
        )

    result_path = result_dir / RESULT_FILENAME
    if result_path.exists() or result_path.is_symlink():
        raise WorkerResultReturnError(
            "worker result already exists; overwrite is forbidden"
        )

    payload = extract_framed_result(
        stdout.read_text(encoding="utf-8")
    )
    if payload.get("attempt_id") != expected_attempt_id:
        raise WorkerResultReturnError(
            "result attempt binding mismatch"
        )

    errors = validate_result_envelope(
        payload,
        origin_manifest,
        root=canonical,
    )
    if errors:
        raise WorkerResultReturnError(
            "Handoff v2 result validation failed: "
            + yaml.safe_dump(
                {"errors": errors},
                sort_keys=False,
                allow_unicode=True,
            ).strip()
        )

    result_dir.mkdir(parents=True, exist_ok=True)
    if result_dir.is_symlink():
        raise WorkerResultReturnError(
            "result directory cannot be a symlink"
        )

    try:
        with result_path.open("x", encoding="utf-8") as handle:
            yaml.safe_dump(
                payload,
                handle,
                sort_keys=False,
                allow_unicode=True,
                width=112,
            )
    except FileExistsError as exc:
        raise WorkerResultReturnError(
            "worker result already exists; overwrite is forbidden"
        ) from exc

    return {
        "schema_version": (
            "forprint_worker_result_return_materialization_v0_1"
        ),
        "attempt_id": expected_attempt_id,
        "result_path": str(result_path),
        "validation_passed": True,
        "result": payload,
        "authority_granted": False,
        "candidate_promoted": False,
        "canonical_write_performed": False,
    }
