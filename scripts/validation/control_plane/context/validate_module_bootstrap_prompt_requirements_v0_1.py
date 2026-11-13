from pathlib import Path

import yaml

STANDARD = Path(
    "coordination/standards/automation/control_plane/module_bootstrap_prompt_requirements_v0_1.yaml"
)


def main() -> int:
    data = yaml.safe_load(STANDARD.read_text(encoding="utf-8"))
    checks = [
        data["execution_class"] == "MODULE_BOOTSTRAP",
        data["stage_0"]["required"] is True,
        data["stage_0"]["owner"] == "MODULE_ASSISTANT",
        data["authority"]["module_local_commit_allowed"] is True,
        data["authority"]["module_local_push_allowed"] is True,
        data["authority"]["blueprint_foreign_repo_commit_push"] is False,
        data["authority"]["human_acceptance_required"] is True,
        data["authority"]["automatic_accept"] is False,
        data["authority"]["automatic_next_prompt_release"] is False,
        "module-owned non-secret config/worker_runtime.yaml exists for normal development"
        in data["bootstrap_outcomes"],
        "HEAD-bound generated freshness does not create a tracked self-reference cycle"
        in data["bootstrap_outcomes"],
    ]
    if not all(checks):
        print("MODULE_BOOTSTRAP_PROMPT_REQUIREMENTS=FAIL")
        return 1
    print("MODULE_BOOTSTRAP_PROMPT_REQUIREMENTS=PASS")
    print("STAGE_0_REQUIRED=true")
    print("MODULE_LOCAL_COMMIT_PUSH_ALLOWED=true")
    print("BLUEPRINT_FOREIGN_REPO_COMMIT_PUSH=false")
    print("HUMAN_ACCEPTANCE_REQUIRED=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
