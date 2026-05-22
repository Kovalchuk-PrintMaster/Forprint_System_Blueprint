from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_mobile_app_future_readiness_is_declared() -> None:
    root = Path(__file__).resolve().parents[1]
    data = _load_yaml(root / "machine/future_channel_readiness.yaml")

    items = data["future_channel_readiness"]
    mobile_items = [item for item in items if item["future_module_id"] == "mobile_app"]

    assert mobile_items, "mobile_app must be declared in future_channel_readiness.yaml"

    mobile = mobile_items[0]
    assert mobile["status"] == "deferred_planned"
    assert mobile["start_condition"] == "calculator_engine_fully_operational"
    assert mobile["current_development_role"] == "none"


def test_mobile_app_readiness_mentions_key_modules() -> None:
    root = Path(__file__).resolve().parents[1]
    data = _load_yaml(root / "machine/future_channel_readiness.yaml")

    mobile = data["future_channel_readiness"][0]
    required_modules = {
        "forprint_crm",
        "forprint_integration_gateway",
        "forprint_operational_registry",
        "calculator_engine",
        "telegram_bot",
        "website",
    }

    assert required_modules.issubset(set(mobile["must_be_considered_by"]))
    