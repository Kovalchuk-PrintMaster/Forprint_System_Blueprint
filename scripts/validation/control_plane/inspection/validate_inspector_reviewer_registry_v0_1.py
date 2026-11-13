from pathlib import Path

from scripts.coordination.control_plane.inspection.reviewer_registry import (
    PROJECT_REVIEWER_ID,
    PROJECT_REVIEWER_ROLE,
    load_registry,
    resolve_completion_reviewer,
    validate_registry,
)

REGISTRY = Path(
    "coordination/standards/automation/control_plane/inspector_reviewer_registry_v0_1.yaml"
)


def main() -> int:
    data = load_registry(REGISTRY)
    validate_registry(data)
    resolved = resolve_completion_reviewer(registry=data)

    if resolved["reviewer_id"] != PROJECT_REVIEWER_ID:
        print("INSPECTOR_REVIEWER_REGISTRY=FAIL reviewer_id")
        return 1
    if resolved["reviewer_role"] != PROJECT_REVIEWER_ROLE:
        print("INSPECTOR_REVIEWER_REGISTRY=FAIL reviewer_role")
        return 1
    if resolved["read_only"] is not True:
        print("INSPECTOR_REVIEWER_REGISTRY=FAIL read_only")
        return 1
    if resolved["may_accept"] is not False:
        print("INSPECTOR_REVIEWER_REGISTRY=FAIL accept_authority")
        return 1

    print("INSPECTOR_REVIEWER_REGISTRY=PASS")
    print("PROJECT_CONFORMANCE_REVIEWER=forprint_project_inspector")
    print("PRODUCTION_RUNTIME_INSPECTOR_AS_CONFORMANCE_REVIEWER=false")
    print("INSPECTOR_READ_ONLY=true")
    print("HUMAN_ACCEPTANCE_AUTHORITY_PRESERVED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
