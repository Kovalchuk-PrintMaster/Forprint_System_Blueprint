from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination.control_plane.context import bootstrap_task_context as ctx

STANDARD = Path(
    "coordination/standards/automation/control_plane/bootstrap_task_context_mode_v0_1.yaml"
)


def main() -> int:
    required = [
        Path("scripts/coordination/control_plane/context/__init__.py"),
        Path("scripts/coordination/control_plane/context/bootstrap_task_context.py"),
        Path("scripts/coordination/control_plane/context/runtime.py"),
        Path("tests/coordination/control_plane/context/test_bootstrap_task_context_mode_v0_1.py"),
        STANDARD,
    ]
    if any(not path.is_file() for path in required):
        print("BOOTSTRAP_TASK_CONTEXT_MODE=FAIL missing")
        return 1

    data = yaml.safe_load(STANDARD.read_text(encoding="utf-8"))
    checks = [
        ctx.SCHEMA == "forprint_bootstrap_task_context_envelope_v0_1",
        data["execution_class"] == "MODULE_BOOTSTRAP",
        data["strict_mode"]["preserved"] is True,
        data["bootstrap_mode"]["dirty_worktree_is_debt_not_automatic_failure"] is True,
        data["bootstrap_mode"]["stale_generated_freshness_is_debt_not_automatic_failure"] is True,
        data["bootstrap_mode"]["roadmap_development_allowed"] is False,
        data["bootstrap_mode"]["strict_task_context_rebuild_after_stage_0"] is True,
        data["authority"]["release_authorization_remains_required"] is True,
        data["authority"]["authority_relaxation_allowed"] is False,
    ]
    if not all(checks):
        print("BOOTSTRAP_TASK_CONTEXT_MODE=FAIL invariant")
        return 1

    print("BOOTSTRAP_TASK_CONTEXT_MODE=PASS")
    print("STRICT_TASK_CONTEXT_MODE_PRESERVED=true")
    print("BOOTSTRAP_DEBT_ALLOWED=true")
    print("AUTHORITY_RELAXATION_ALLOWED=false")
    print("ROADMAP_DEVELOPMENT_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
