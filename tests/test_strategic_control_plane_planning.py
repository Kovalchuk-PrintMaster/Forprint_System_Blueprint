from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_strategic_control_plane_policy_exists() -> None:
    assert (
        ROOT
        / "coordination"
        / "global_policy"
        / "forprint_strategic_control_plane_policy.md"
    ).exists()


def test_strategic_control_plane_is_registered_in_module_sources() -> None:
    data = _load_yaml(
        ROOT
        / "coordination"
        / "module_sources"
        / "module_git_sources.yaml"
    )

    modules = {
        item["module_id"]: item
        for item in data["module_git_sources"]["modules"]
    }

    module = modules["forprint_strategic_control_plane"]

    assert module["priority"] == "deferred"
    assert module["repo_status"] == "planned_directory_created"
    assert (
        module["development_status"]
        == "planned_high_priority_deferred_until_core_modules_alive"
    )
    assert (
        module["local_path"]
        == "/srv/software_development/forprint-project/forprint_strategic_control_plane"
    )


def test_strategic_control_plane_policy_defers_active_implementation() -> None:
    content = (
        ROOT
        / "coordination"
        / "global_policy"
        / "forprint_strategic_control_plane_policy.md"
    ).read_text(encoding="utf-8")

    assert "Planned / high priority / deferred" in content
    assert "Do not implement now" in content
    assert "Current governance remains" in content
