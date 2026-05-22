from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_system_layers_reference_known_modules() -> None:
    root = Path(__file__).resolve().parents[1]

    modules_data = _load_yaml(root / "machine/modules.yaml")
    layers_data = _load_yaml(root / "machine/system_layers.yaml")

    known_modules = {item["id"] for item in modules_data["modules"]}

    for layer in layers_data["system_layers"]:
        assert layer["modules"], f"{layer['id']} must contain at least one module"
        for module_id in layer["modules"]:
            assert module_id in known_modules, f"Unknown module in system layer: {module_id}"


def test_system_layers_have_required_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    layers_data = _load_yaml(root / "machine/system_layers.yaml")

    required_fields = {"id", "title", "purpose", "modules", "must_not_do"}

    for layer in layers_data["system_layers"]:
        missing = required_fields - set(layer)
        assert not missing, f"{layer.get('id')} missing fields: {sorted(missing)}"
        assert isinstance(layer["must_not_do"], list)
        assert layer["must_not_do"], f"{layer['id']} must define must_not_do"


def test_system_control_flows_have_required_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    flows_data = _load_yaml(root / "machine/system_control_flows.yaml")

    required_fields = {"id", "title", "flow_type", "status", "description"}

    assert flows_data["control_flows"], "system_control_flows.yaml must not be empty"

    for flow in flows_data["control_flows"]:
        missing = required_fields - set(flow)
        assert not missing, f"{flow.get('id')} missing fields: {sorted(missing)}"
        assert "source" in flow or "source_type" in flow
        assert "target" in flow or "target_type" in flow