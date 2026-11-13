from pathlib import Path

import yaml

STANDARD = Path(
    "coordination/standards/automation/control_plane/module_bootstrap_prompt_requirements_v0_1.yaml"
)


def _data():
    return yaml.safe_load(STANDARD.read_text(encoding="utf-8"))


def test_stage_0_is_module_owned() -> None:
    data = _data()
    assert data["stage_0"]["required"] is True
    assert data["stage_0"]["owner"] == "MODULE_ASSISTANT"
    assert data["authority"]["blueprint_foreign_repo_commit_push"] is False


def test_destructive_git_operations_remain_forbidden() -> None:
    forbidden = set(_data()["stage_0"]["forbidden"])
    assert "force push" in forbidden
    assert "git reset --hard" in forbidden
    assert "git clean used to manufacture cleanliness" in forbidden


def test_bootstrap_requires_self_maintaining_module_memory_and_runtime() -> None:
    outcomes = set(_data()["bootstrap_outcomes"])
    assert "deterministic module inventory/index is present and maintainable" in outcomes
    assert (
        "HEAD-bound generated freshness does not create a tracked self-reference cycle" in outcomes
    )
    assert (
        "module-owned non-secret config/worker_runtime.yaml exists for normal development"
        in outcomes
    )


def test_finalization_preserves_human_acceptance() -> None:
    data = _data()
    assert data["authority"]["human_acceptance_required"] is True
    assert data["authority"]["automatic_accept"] is False
    assert data["authority"]["automatic_next_prompt_release"] is False
