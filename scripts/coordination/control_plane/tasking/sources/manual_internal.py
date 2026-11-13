# Manual Blueprint-internal source for CF-10 zero-stage tasks.

from __future__ import annotations


def manual_internal_source(
    *,
    artifact_ref: str,
    created_by: str = "operator_assistant",
) -> dict[str, object]:
    if not isinstance(artifact_ref, str) or not artifact_ref.strip():
        raise ValueError("artifact_ref is required")
    if artifact_ref.strip().lower().startswith(("chat:", "raw_chat:")):
        raise ValueError("manual internal task must reference a durable artifact, not raw chat")
    if not isinstance(created_by, str) or not created_by.strip():
        raise ValueError("created_by is required")
    return {
        "type": "MANUAL_INTERNAL",
        "generation_mode": "MANUAL",
        "artifact_ref": artifact_ref.strip(),
        "created_by": created_by.strip(),
        "raw_chat_is_authority": False,
    }
