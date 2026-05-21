from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load_machine_file(name: str) -> dict:
    return yaml.safe_load((ROOT / "machine" / name).read_text(encoding="utf-8"))


def test_integration_gateway_module_is_declared() -> None:
    modules = _load_machine_file("modules.yaml")["modules"]
    gateway = next(module for module in modules if module["id"] == "forprint_integration_gateway")

    assert gateway["type"] == "integration_gateway_and_message_router"
    assert "client" in gateway["must_not_own"]
    assert "order" in gateway["must_not_own"]
    assert "integration_request" in gateway["owns"]


def test_gateway_has_core_routing_contracts() -> None:
    contracts = _load_machine_file("contracts.yaml")["contracts"]
    contract_ids = {contract["id"] for contract in contracts}

    assert "website_to_integration_gateway_request.v1" in contract_ids
    assert "integration_gateway_to_calculator_request.v1" in contract_ids
    assert "integration_gateway_to_warehouse_reservation.v1" in contract_ids
    assert "integration_gateway_to_accounting_invoice_request.v1" in contract_ids


def test_gateway_flows_do_not_remove_logical_blueprint_flows() -> None:
    flows = _load_machine_file("data_flows.yaml")["data_flows"]
    flow_ids = {flow["id"] for flow in flows}

    assert "website_requests_to_integration_gateway" in flow_ids
    assert "calculator_result_to_integration_gateway" in flow_ids
    assert "calculator_quote_to_crm" in flow_ids
