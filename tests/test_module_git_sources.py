from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_module_git_sources_file_exists() -> None:
    assert (ROOT / "coordination" / "module_sources" / "module_git_sources.yaml").exists()


def test_module_git_sources_readme_exists() -> None:
    assert (ROOT / "coordination" / "module_sources" / "README.md").exists()


def test_module_git_sources_has_required_top_level_keys() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    registry = data["module_git_sources"]

    assert registry["version"] == "0.1"
    assert registry["default_branch"] == "main"
    assert registry["default_coordination_root"] == "coordination"
    assert registry["default_status_file"] == "coordination/status/current_status.yaml"
    assert isinstance(registry["modules"], list)
    assert registry["modules"]


def test_module_git_sources_include_core_modules() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    modules = {item["module_id"]: item for item in data["module_git_sources"]["modules"]}

    required_modules = {
        "forprint_system_blueprint",
        "calculator_engine",
        "forprint_accounting_registry_service",
        "forprint_operational_registry",
        "forprint_library",
        "forprint_integration_gateway",
        "logistics_service",
        "telegram_bot",
        "forprint_prepress_hub",
        "forprint_crm",
        "mobile_app",
    }

    assert required_modules.issubset(set(modules))


def test_confirmed_modules_have_repo_url_and_local_path() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    for module in data["module_git_sources"]["modules"]:
        if module["repo_status"] == "confirmed":
            assert module["repo_url"]
            assert module["local_path"]


def test_every_module_declares_coordination_paths() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    for module in data["module_git_sources"]["modules"]:
        assert module["coordination_root"] == "coordination"
        assert module["status_file"] == "coordination/status/current_status.yaml"
        assert module["prompt_index"] == "coordination/prompts/index.yaml"
        assert module["report_index"] == "coordination/reports/index.yaml"


def test_mobile_app_is_deferred_not_created() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    modules = {item["module_id"]: item for item in data["module_git_sources"]["modules"]}

    mobile_app = modules["mobile_app"]

    assert mobile_app["priority"] == "deferred"
    assert mobile_app["repo_status"] == "planned_not_created"
    assert mobile_app["development_status"] == "planned_deferred_until_calculator_ready"


def test_accounting_registry_is_waiting_for_sanitized_samples() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    modules = {item["module_id"]: item for item in data["module_git_sources"]["modules"]}

    accounting = modules["forprint_accounting_registry_service"]

    assert accounting["development_status"] == "sandbox_1c_import_export_ready"
    assert accounting["waiting_for"] == "real_sanitized_one_c_export_samples"


def test_logistics_service_is_canonical_confirmed_module_source() -> None:
    data = _load_yaml(ROOT / "coordination" / "module_sources" / "module_git_sources.yaml")

    modules = {item["module_id"]: item for item in data["module_git_sources"]["modules"]}

    logistics = modules["logistics_service"]

    assert logistics["module_name"] == "ForPrint Logistics Service"
    assert logistics["priority"] == "p1"
    assert logistics["development_status"] == "active_development"
    assert logistics["local_path"] == (
        "/srv/software_development/forprint-project/forprint_logistics_service"
    )
    assert logistics["repo_url"] == (
        "git@github.com:Kovalchuk-PrintMaster/Forprint_Logistics_Service.git"
    )
    assert logistics["branch"] == ("feature/logistics-tracking-events-contract-v01")
    assert logistics["repo_status"] == "confirmed"


def test_logistics_service_resolves_through_module_source_registry() -> None:
    from scripts.collect_module_coordination import (
        find_module,
        load_module_sources,
    )

    resolved = find_module(
        "logistics_service",
        load_module_sources(),
    )

    assert resolved["module_id"] == "logistics_service"
    assert resolved["local_path"] == (
        "/srv/software_development/forprint-project/forprint_logistics_service"
    )
    assert resolved["repo_status"] == "confirmed"
