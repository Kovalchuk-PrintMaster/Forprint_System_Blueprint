from __future__ import annotations

from typing import Any

from scripts.coordination.control_plane.events import (
    Q5_ALLOWED_FAMILIES,
    validate_q5_event_envelope,
)

COMPLETION_FAMILY = "completion_publication"


def validate_completion_publication_event(
    event: dict[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    valid, base_errors = validate_q5_event_envelope(event)
    errors = list(base_errors)
    event_type = event.get("event_type")
    if not isinstance(event_type, str) or "." not in event_type:
        errors.append("completion_event_type_invalid")
    elif event_type.split(".", 1)[0] != COMPLETION_FAMILY:
        errors.append("completion_event_family_mismatch")
    payload = event.get("payload")
    if not isinstance(payload, dict):
        errors.append("completion_payload_not_mapping")
    else:
        for key in ("normalized_completion_id", "normalized_completion_sha256"):
            if not isinstance(payload.get(key), str) or not payload[key]:
                errors.append(f"completion_payload_missing_{key}")
    if COMPLETION_FAMILY not in Q5_ALLOWED_FAMILIES:
        errors.append("q5_completion_family_not_registered")
    return valid and not errors, tuple(sorted(set(errors)))
