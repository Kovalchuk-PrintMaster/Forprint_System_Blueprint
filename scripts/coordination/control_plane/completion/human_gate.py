from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.coordination.control_plane.completion.inspector import (
    RESULT_STATES,
    validate_inspector_result,
)
from scripts.coordination.control_plane.completion.intake import load_yaml_mapping

PROJECTION_SCHEMA = "forprint_human_acceptance_gate_projection_v0_1"


def project_human_acceptance_gate(
    *, inspector_request_path: Path, inspector_result_path: Path
) -> dict[str, Any]:
    validation = validate_inspector_result(
        request_path=inspector_request_path,
        result_path=inspector_result_path,
    )
    if not validation.valid:
        raise ValueError("invalid Inspector result: " + ",".join(validation.errors))

    request = load_yaml_mapping(inspector_request_path, label="Inspector request")
    result = load_yaml_mapping(inspector_result_path, label="Inspector result")
    state = result.get("state")
    if state not in RESULT_STATES:
        raise ValueError("unsupported Inspector result state")

    projection = {
        "CONFORMANT": "AWAITING_HUMAN_ACCEPTANCE",
        "NON_CONFORMANT": "RETURN_RECOMMENDED",
        "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE",
    }[state]
    return {
        "schema_version": PROJECTION_SCHEMA,
        "identity": {
            "module_id": request["identity"]["module_id"],
            "prompt_id": request["identity"]["prompt_id"],
            "request_id": request["request_id"],
        },
        "state": projection,
        "inspector_state": state,
        "findings": result.get("findings", []),
        "human_decision": {
            "required": True,
            "decision": "NOT_DECIDED",
            "allowed_decisions": ["ACCEPT", "RETURN", "HOLD"],
        },
        "semantic_boundaries": {
            "projection_is_human_decision": False,
            "inspector_conformant_is_blueprint_accept": False,
            "automatic_accept": False,
            "automatic_return": False,
            "automatic_hold": False,
            "automatic_next_prompt_release": False,
        },
    }
