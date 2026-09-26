# Control Plane facade for Worker Task Envelope compilation.

from __future__ import annotations

from typing import Any

from .envelope import build_task_envelope, validate_task_envelope


def compile_task_envelope(**kwargs: Any) -> dict[str, Any]:
    envelope = build_task_envelope(**kwargs)
    errors = validate_task_envelope(envelope)
    if errors:
        raise ValueError("; ".join(errors))
    return envelope
