from pathlib import Path

import yaml

from scripts.generate_module_policy_docs import render_policy

ROOT = Path(__file__).resolve().parents[1]
POLICY_INDEX = ROOT / "coordination" / "module_policy" / "module_policy_index.yaml"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_module_policy_index_exists() -> None:
    assert POLICY_INDEX.exists()


def test_module_policy_index_has_required_local_modules() -> None:
    data = _load_yaml(POLICY_INDEX)

    modules = {
        item["module_id"]: item
        for item in data["module_policy_index"]["modules"]
    }

    required_modules = {
        "forprint_system_blueprint",
        "calculator_engine",
        "forprint_accounting_registry_service",
        "forprint_crm",
        "forprint_integration_gateway",
        "forprint_library",
        "forprint_operations_control_registry",
        "forprint_prepress_hub",
        "forprint_strategic_control_plane",
        "telegram_bot",
    }

    assert required_modules.issubset(set(modules))


def test_each_module_policy_entry_has_required_fields() -> None:
    data = _load_yaml(POLICY_INDEX)

    required_fields = {
        "module_id",
        "module_name",
        "priority",
        "development_status",
        "strategic_role",
        "main_goals",
        "owns",
        "must_not_own",
        "next_focus",
    }

    for module in data["module_policy_index"]["modules"]:
        assert required_fields.issubset(set(module))
        assert isinstance(module["main_goals"], list)
        assert isinstance(module["owns"], list)
        assert isinstance(module["must_not_own"], list)
        assert isinstance(module["next_focus"], list)


def test_generated_module_policy_docs_are_up_to_date() -> None:
    data = _load_yaml(POLICY_INDEX)

    for module in data["module_policy_index"]["modules"]:
        path = (
            ROOT
            / "coordination"
            / "module_policy"
            / module["module_id"]
            / "module_policy.md"
        )

        assert path.exists()
        assert path.read_text(encoding="utf-8") == render_policy(module)


def test_calculator_policy_keeps_p0_and_output_package() -> None:
    data = _load_yaml(POLICY_INDEX)

    modules = {
        item["module_id"]: item
        for item in data["module_policy_index"]["modules"]
    }

    calculator = modules["calculator_engine"]
    rendered = render_policy(calculator).casefold()

    assert calculator["priority"] == "p0"
    assert "calculationoutputpackage".casefold() in rendered
    assert "quote" in rendered
    assert "order" in rendered


def test_strategic_control_plane_is_deferred() -> None:
    data = _load_yaml(POLICY_INDEX)

    modules = {
        item["module_id"]: item
        for item in data["module_policy_index"]["modules"]
    }

    control_plane = modules["forprint_strategic_control_plane"]

    assert control_plane["priority"] == "deferred"
    assert (
        control_plane["development_status"]
        == "planned_high_priority_deferred_until_core_modules_alive"
    )
