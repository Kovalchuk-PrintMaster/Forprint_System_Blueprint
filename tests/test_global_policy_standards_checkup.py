from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_global_policy_files_exist() -> None:
    required_files = [
        ROOT / "coordination" / "global_policy" / "README.md",
        ROOT / "coordination" / "global_policy" / "forprint_project_doctrine.md",
        ROOT / "coordination" / "global_policy" / "ecosystem_module_map.md",
        ROOT / "coordination" / "global_policy" / "current_execution_focus.md",
    ]

    for path in required_files:
        assert path.exists()


def test_standards_files_exist() -> None:
    required_files = [
        ROOT / "coordination" / "standards" / "README.md",
        ROOT / "coordination" / "standards" / "repository_structure_baseline.md",
        ROOT / "coordination" / "standards" / "make_command_standard.md",
        ROOT / "coordination" / "standards" / "configuration_policy.md",
    ]

    for path in required_files:
        assert path.exists()


def test_checkup_policy_files_exist() -> None:
    required_files = [
        ROOT / "coordination" / "checkup" / "README.md",
        ROOT / "coordination" / "checkup" / "ecosystem_checkup_policy.yaml",
        ROOT / "coordination" / "checkup" / "module_activity_thresholds.yaml",
    ]

    for path in required_files:
        assert path.exists()


def test_global_policy_mentions_core_module_roles() -> None:
    content = (
        ROOT / "coordination" / "global_policy" / "forprint_project_doctrine.md"
    ).read_text(encoding="utf-8")

    assert "Operations Control Registry" in content
    assert "Library" in content
    assert "Calculator Engine" in content
    assert "Accounting Registry" in content
    assert "Control Plane is planned but deferred" in content


def test_configuration_policy_rejects_hardcoded_paths() -> None:
    content = (
        ROOT / "coordination" / "standards" / "configuration_policy.md"
    ).read_text(encoding="utf-8")

    assert "Avoid hardcoded paths" in content
    assert "Prefer configuration files" in content
    assert "Secrets must not be committed to Git" in content


def test_make_command_standard_mentions_coordination_sync_check() -> None:
    content = (
        ROOT / "coordination" / "standards" / "make_command_standard.md"
    ).read_text(encoding="utf-8")

    assert "make coordination-sync-check" in content
    assert "make coordination-check" in content
    assert "make status-report" in content


def test_ecosystem_checkup_policy_is_planned_skeleton() -> None:
    data = _load_yaml(
        ROOT / "coordination" / "checkup" / "ecosystem_checkup_policy.yaml"
    )

    policy = data["ecosystem_checkup_policy"]

    assert policy["version"] == "0.1"
    assert policy["status"] == "planned_skeleton"
    assert policy["future_command_name"] == "ecosystem-check"
    assert "stale_high_priority_module" in policy["planned_checks"]


def test_activity_thresholds_define_p0_warning_and_critical() -> None:
    data = _load_yaml(
        ROOT / "coordination" / "checkup" / "module_activity_thresholds.yaml"
    )

    thresholds = data["module_activity_thresholds"]["thresholds"]

    assert thresholds["p0"]["warning_after_days_without_report"] == 3
    assert thresholds["p0"]["critical_after_days_without_report"] == 7
