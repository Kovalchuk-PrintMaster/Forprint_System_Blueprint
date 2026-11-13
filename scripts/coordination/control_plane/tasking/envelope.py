# Worker Task Envelope v0.1.
# Instruction/context only; Work Front remains execution authority.

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "forprint_worker_task_envelope_v0_1"
ALLOWED_SOURCE_TYPES = {"MANUAL_INTERNAL", "EXTERNAL_PROMPT_QUEUE"}
SOURCE_GENERATION_MODES = {
    "MANUAL_INTERNAL": "MANUAL",
    "EXTERNAL_PROMPT_QUEUE": "EXTERNAL_QUEUE",
}
FORBIDDEN_AUTHORITY_KEYS = {
    "dispatch_authority",
    "release_authority",
    "push_authority",
    "merge_authority",
    "foreign_write_authority",
    "automatic_accept",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_string_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(_nonempty_string(item) for item in value)
    )


def _find_forbidden_keys(node: Any, trail: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key) in FORBIDDEN_AUTHORITY_KEYS:
                errors.append(f"forbidden authority field: {trail}.{key}")
            errors.extend(_find_forbidden_keys(value, f"{trail}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            errors.extend(_find_forbidden_keys(value, f"{trail}[{index}]"))
    return errors


def validate_task_envelope(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["task envelope must be a mapping"]

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version mismatch")

    for field in ("task_id", "module_id", "objective"):
        if not _nonempty_string(data.get(field)):
            errors.append(f"{field} must be a non-empty string")

    for field in ("instructions", "acceptance", "stop_conditions"):
        if not _nonempty_string_list(data.get(field)):
            errors.append(f"{field} must be a non-empty list of strings")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be a mapping")
    else:
        source_type = source.get("type")
        if source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"unsupported source type: {source_type!r}")
        elif source.get("generation_mode") != SOURCE_GENERATION_MODES[source_type]:
            errors.append("source generation_mode mismatch")

        if source.get("raw_chat_is_authority") is not False:
            errors.append("source must declare raw_chat_is_authority=false")

        module_id = data.get("module_id")
        if source_type == "MANUAL_INTERNAL" and module_id != "forprint_system_blueprint":
            errors.append(
                "MANUAL_INTERNAL is restricted to forprint_system_blueprint in v0.1"
            )

        if source_type == "MANUAL_INTERNAL":
            if not _nonempty_string(source.get("artifact_ref")):
                errors.append("MANUAL_INTERNAL requires artifact_ref")
        elif source_type == "EXTERNAL_PROMPT_QUEUE":
            for field in ("queue_ref", "prompt_id", "approved_prompt_ref"):
                if not _nonempty_string(source.get(field)):
                    errors.append(f"EXTERNAL_PROMPT_QUEUE requires {field}")
            if source.get("prompt_queue_grants_worker_authority") is not False:
                errors.append("external prompt queue must not grant worker authority")

    work = data.get("work")
    if not isinstance(work, dict):
        errors.append("work must be a mapping")
    else:
        for field in ("work_id", "work_front_id"):
            if not _nonempty_string(work.get(field)):
                errors.append(f"work.{field} must be a non-empty string")

    profile = data.get("execution_profile")
    if not isinstance(profile, dict):
        errors.append("execution_profile must be a mapping")
    else:
        if not _nonempty_string(profile.get("profile_id")):
            errors.append("execution_profile.profile_id is required")
        if not _nonempty_string(profile.get("revision")):
            errors.append("execution_profile.revision is required")

    procedure = data.get("procedure")
    if not isinstance(procedure, dict):
        errors.append("procedure must be a mapping")
    else:
        if not _nonempty_string(procedure.get("procedure_id")):
            errors.append("procedure.procedure_id is required")
        if not _nonempty_string(procedure.get("revision")):
            errors.append("procedure.revision is required")

    expected_authority = {
        "execution_authority_source": "WORK_FRONT",
        "task_envelope_grants_authority": False,
        "widening_requested": False,
    }
    if data.get("authority") != expected_authority:
        errors.append("authority must preserve Work Front authority without widening")

    errors.extend(_find_forbidden_keys(data))
    return errors


def build_task_envelope(
    *,
    task_id: str,
    module_id: str,
    source: dict[str, Any],
    work_id: str,
    work_front_id: str,
    objective: str,
    instructions: list[str],
    acceptance: list[str],
    stop_conditions: list[str],
    execution_profile_id: str,
    execution_profile_revision: str,
    procedure_id: str,
    procedure_revision: str,
) -> dict[str, Any]:
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "module_id": module_id,
        "source": dict(source),
        "work": {"work_id": work_id, "work_front_id": work_front_id},
        "objective": objective,
        "instructions": list(instructions),
        "acceptance": list(acceptance),
        "stop_conditions": list(stop_conditions),
        "execution_profile": {
            "profile_id": execution_profile_id,
            "revision": execution_profile_revision,
        },
        "procedure": {
            "procedure_id": procedure_id,
            "revision": procedure_revision,
        },
        "authority": {
            "execution_authority_source": "WORK_FRONT",
            "task_envelope_grants_authority": False,
            "widening_requested": False,
        },
    }
    errors = validate_task_envelope(envelope)
    if errors:
        raise ValueError("; ".join(errors))
    return envelope
