from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination.control_plane.completion import (
    human_gate,
    inspector,
    intake,
    q5_completion,
)
from scripts.coordination.control_plane.events import Q5_ALLOWED_FAMILIES

STANDARD = Path(
    "coordination/standards/automation/control_plane/"
    "completion_intake_inspector_conformance_v0_1.yaml"
)


def main() -> int:
    required = [
        Path("scripts/coordination/control_plane/completion/__init__.py"),
        Path("scripts/coordination/control_plane/completion/intake.py"),
        Path("scripts/coordination/control_plane/completion/inspector.py"),
        Path("scripts/coordination/control_plane/completion/human_gate.py"),
        Path("scripts/coordination/control_plane/completion/q5_completion.py"),
        Path("scripts/coordination/control_plane/completion/runtime.py"),
        Path(
            "tests/coordination/control_plane/completion/"
            "test_completion_intake_inspector_conformance_v0_1.py"
        ),
        STANDARD,
    ]
    if any(not path.is_file() for path in required):
        print("COMPLETION_INSPECTOR_INTEGRATION_CONTRACT=FAIL missing")
        return 1
    standard = yaml.safe_load(STANDARD.read_text(encoding="utf-8"))
    checks = [
        standard["schema_version"] == "completion_intake_inspector_conformance_contract_v0_1",
        standard["architecture"]["inspector_read_only"] is True,
        standard["architecture"]["human_acceptance_authority"] is True,
        standard["architecture"]["automatic_accept"] is False,
        standard["structure"]["new_internals_nested"] is True,
        standard["q5"]["family"] == "completion_publication",
        standard["q5"]["family_set_expanded"] is False,
        "completion_publication" in Q5_ALLOWED_FAMILIES,
        intake.NORMALIZED_SCHEMA == "forprint_normalized_completion_intake_v0_1",
        inspector.REQUEST_SCHEMA == "forprint_inspector_conformance_request_v0_1",
        inspector.RESULT_SCHEMA == "forprint_inspector_conformance_result_v0_1",
        human_gate.PROJECTION_SCHEMA == "forprint_human_acceptance_gate_projection_v0_1",
        q5_completion.COMPLETION_FAMILY == "completion_publication",
    ]
    if not all(checks):
        print("COMPLETION_INSPECTOR_INTEGRATION_CONTRACT=FAIL invariant")
        return 1
    print("COMPLETION_INSPECTOR_INTEGRATION_CONTRACT=PASS")
    print("INSPECTOR_READ_ONLY=true")
    print("INSPECTOR_REPOSITORY_BINDING=UNBOUND_EXTERNAL_REVIEWER")
    print("HUMAN_ACCEPTANCE_AUTHORITY=true")
    print("Q5_COMPLETION_PUBLICATION_REUSED=true")
    print("AUTOMATIC_ACCEPT=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
