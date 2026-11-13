from __future__ import annotations

from pathlib import Path

import yaml

STANDARD = Path("coordination/standards/automation/control_plane/module_readiness_levels_v0_1.yaml")


def main() -> int:
    required = [
        Path("scripts/coordination/control_plane/readiness/__init__.py"),
        Path("scripts/coordination/control_plane/readiness/module_readiness.py"),
        Path("scripts/coordination/control_plane/readiness/runtime.py"),
        Path("tests/coordination/control_plane/readiness/test_module_readiness_levels_v0_1.py"),
        STANDARD,
    ]
    if any(not path.is_file() for path in required):
        print("MODULE_READINESS_LEVELS=FAIL missing")
        return 1

    data = yaml.safe_load(STANDARD.read_text(encoding="utf-8"))
    checks = [
        data["bootstrap_readiness"]["state"] == "BOOTSTRAP_READY",
        data["bootstrap_readiness"]["grants_roadmap_development"] is False,
        data["development_readiness"]["state"] == "DEVELOPMENT_READY",
        data["development_readiness"]["bootstrap_acceptance_required"] is True,
        data["development_readiness"]["strict_task_context_required"] is True,
        data["development_readiness"]["inspector_binding_required"] is True,
        data["development_readiness"]["dependency_readiness_required"] is True,
        data["authority"]["bootstrap_ready_is_execution_authority"] is False,
        data["authority"]["automatic_accept"] is False,
    ]
    if not all(checks):
        print("MODULE_READINESS_LEVELS=FAIL invariant")
        return 1

    print("MODULE_READINESS_LEVELS=PASS")
    print("BOOTSTRAP_AND_DEVELOPMENT_READINESS_SEPARATE=true")
    print("BOOTSTRAP_READY_GRANTS_ROADMAP_DEVELOPMENT=false")
    print("AUTOMATIC_ACCEPT=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
