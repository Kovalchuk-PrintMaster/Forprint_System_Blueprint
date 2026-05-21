# python scripts/validate_blueprint.py
"""
Validate ForPrint System Blueprint YAML files.

Перевіряє базову цілісність архітектурного опису:
- унікальність module_id / object_id / contract_id / flow_id;
- існування owner-модулів для data objects;
- існування source/target modules у data flows;
- існування contracts, які використовуються у data flows;
- існування data_objects у contracts / data_flows / impact_rules;
- відповідність ownership.yaml до data_objects.yaml.
"""

from __future__ import annotations

# Дозволяє запускати скрипт і як модуль, і напряму: python scripts/name.py
if __package__ is None or __package__ == "":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import sys
from pathlib import Path
from typing import Any

from scripts.blueprint_utils import ValidationResult, load_yaml, project_root, unique_ids

EXTERNAL_MODULE_IDS = {"any_module", "any_impacted_module", "external_1c", "human_or_module"}


def _items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"Expected list under key '{key}'")
    return value


def validate_project(root: Path | None = None) -> ValidationResult:
    """Validate the blueprint project and return errors/warnings without exiting."""

    root = root or project_root()
    machine = root / "machine"
    errors: list[str] = []
    warnings: list[str] = []

    modules_yaml = load_yaml(machine / "modules.yaml")
    data_objects_yaml = load_yaml(machine / "data_objects.yaml")
    contracts_yaml = load_yaml(machine / "contracts.yaml")
    data_flows_yaml = load_yaml(machine / "data_flows.yaml")
    ownership_yaml = load_yaml(machine / "ownership.yaml")
    impact_rules_yaml = load_yaml(machine / "impact_rules.yaml")

    modules = _items(modules_yaml, "modules")
    data_objects = _items(data_objects_yaml, "data_objects")
    contracts = _items(contracts_yaml, "contracts")
    data_flows = _items(data_flows_yaml, "data_flows")
    impact_rules = _items(impact_rules_yaml, "impact_rules")

    module_ids, module_errors = unique_ids(modules, "modules")
    object_ids, object_errors = unique_ids(data_objects, "data_objects")
    contract_ids, contract_errors = unique_ids(contracts, "contracts")
    flow_ids, flow_errors = unique_ids(data_flows, "data_flows")
    rule_ids, rule_errors = unique_ids(impact_rules, "impact_rules")

    errors.extend(module_errors + object_errors + contract_errors + flow_errors + rule_errors)

    known_modules = module_ids | EXTERNAL_MODULE_IDS

    for obj in data_objects:
        obj_id = obj.get("id", "<missing>")
        owner = obj.get("owner")
        if owner not in known_modules:
            errors.append(f"data_object '{obj_id}' has unknown owner module: {owner}")
        fields = obj.get("canonical_fields", [])
        if not isinstance(fields, list) or not fields:
            warnings.append(f"data_object '{obj_id}' has no canonical_fields")

    for contract in contracts:
        contract_id = contract.get("id", "<missing>")
        provider = contract.get("provider")
        consumer = contract.get("consumer")
        if provider not in known_modules:
            errors.append(f"contract '{contract_id}' has unknown provider: {provider}")
        if consumer not in known_modules:
            errors.append(f"contract '{contract_id}' has unknown consumer: {consumer}")
        for object_id in contract.get("data_objects", []):
            if object_id not in object_ids:
                errors.append(f"contract '{contract_id}' references unknown data_object: {object_id}")

    for flow in data_flows:
        flow_id = flow.get("id", "<missing>")
        source = flow.get("source")
        target = flow.get("target")
        contract_id = flow.get("contract")
        if source not in known_modules:
            errors.append(f"data_flow '{flow_id}' has unknown source: {source}")
        if target not in known_modules:
            errors.append(f"data_flow '{flow_id}' has unknown target: {target}")
        if contract_id not in contract_ids:
            errors.append(f"data_flow '{flow_id}' references unknown contract: {contract_id}")
        for object_id in flow.get("data_objects", []):
            if object_id not in object_ids:
                errors.append(f"data_flow '{flow_id}' references unknown data_object: {object_id}")

    ownership = ownership_yaml.get("ownership", {})
    if not isinstance(ownership, dict):
        errors.append("ownership.yaml key 'ownership' must be a mapping")
        ownership = {}

    for object_id, record in ownership.items():
        if object_id not in object_ids:
            errors.append(f"ownership references unknown data_object: {object_id}")
            continue
        owner = record.get("owner")
        if owner not in known_modules:
            errors.append(f"ownership for '{object_id}' has unknown owner: {owner}")
        for consumer in record.get("consumers", []):
            if consumer not in known_modules:
                errors.append(f"ownership for '{object_id}' has unknown consumer: {consumer}")

    for object_id in object_ids:
        if object_id not in ownership:
            warnings.append(f"data_object '{object_id}' is not listed in ownership.yaml")

    for rule in impact_rules:
        rule_id = rule.get("id", "<missing>")
        for object_id in rule.get("when_changed", []):
            if object_id not in object_ids and object_id != "contract_definition":
                errors.append(f"impact_rule '{rule_id}' references unknown changed object: {object_id}")
        for module_id in rule.get("notify_modules", []):
            if module_id not in known_modules:
                errors.append(f"impact_rule '{rule_id}' references unknown module: {module_id}")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def main() -> int:
    """CLI entry point."""

    result = validate_project()

    if result.warnings:
        print("⚠️ Blueprint validation warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.errors:
        print("❌ Blueprint validation failed:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    print("✅ Blueprint validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
