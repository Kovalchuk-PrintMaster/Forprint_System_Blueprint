## Файл: `scripts/validate_module_manifest.py`

# python scripts/validate_module_manifest.py module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml

"""
Validate one ForPrint module manifest against the System Blueprint.

Скрипт виконує легку перевірку forprint_module_manifest.yaml:
- module_id має існувати у machine/modules.yaml;
- усі responsibilities мають посилатися на відомі data_objects;
- модуль не має заявляти ownership на об’єкти з blueprint must_not_own;
- усі contracts мають існувати у machine/contracts.yaml;
- consumed/provided contracts мають відповідати ролі consumer/provider, де це можливо.
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

from scripts.blueprint_utils import ValidationResult, load_yaml, project_root

RESPONSIBILITY_KEYS = ("owns", "consumes", "provides", "must_not_own")
CONTRACT_KEYS = ("consumes", "provides")


def _list(value: Any, field_name: str, errors: list[str]) -> list[str]:
    """Return value as list[str] or append validation error."""

    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{field_name} must be a list")
        return []
    invalid_items = [item for item in value if not isinstance(item, str)]
    if invalid_items:
        errors.append(f"{field_name} must contain only strings")
        return []
    return value


def _by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build id -> item mapping."""

    return {item["id"]: item for item in items if "id" in item}


def _items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"Expected list under key '{key}'")
    return value


def validate_manifest(manifest_path: Path, root: Path | None = None) -> ValidationResult:
    """Validate module manifest and return structured result."""

    root = root or project_root()
    machine = root / "machine"
    errors: list[str] = []
    warnings: list[str] = []

    manifest = load_yaml(manifest_path)
    modules = _by_id(_items(load_yaml(machine / "modules.yaml"), "modules"))
    data_objects = _by_id(_items(load_yaml(machine / "data_objects.yaml"), "data_objects"))
    contracts = _by_id(_items(load_yaml(machine / "contracts.yaml"), "contracts"))

    module_id = manifest.get("module_id")
    if not isinstance(module_id, str) or not module_id:
        errors.append("module_id is required and must be a non-empty string")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    blueprint_module = modules.get(module_id)
    if blueprint_module is None:
        errors.append(f"module_id '{module_id}' is not declared in machine/modules.yaml")
        return ValidationResult(ok=False, errors=errors, warnings=warnings)

    for required_field in (
        "title",
        "status",
        "implementation_root",
        "responsibilities",
        "contracts",
        "reports",
    ):
        if required_field not in manifest:
            errors.append(f"missing required field: {required_field}")

    responsibilities = manifest.get("responsibilities", {})
    if not isinstance(responsibilities, dict):
        errors.append("responsibilities must be a mapping")
        responsibilities = {}

    blueprint_must_not_own = set(blueprint_module.get("must_not_own", []))
    claimed_owns = set(_list(responsibilities.get("owns"), "responsibilities.owns", errors))

    forbidden_ownership = sorted(claimed_owns & blueprint_must_not_own)
    for object_id in forbidden_ownership:
        errors.append(f"module '{module_id}' claims forbidden ownership of '{object_id}'")

    for key in RESPONSIBILITY_KEYS:
        for object_id in _list(responsibilities.get(key), f"responsibilities.{key}", errors):
            if object_id not in data_objects:
                errors.append(f"responsibilities.{key} references unknown data_object: {object_id}")

    blueprint_allowed = {
        "owns": set(blueprint_module.get("owns", [])),
        "consumes": set(blueprint_module.get("consumes", [])),
        "provides": set(blueprint_module.get("provides", [])),
    }

    for key in ("owns", "consumes", "provides"):
        declared = set(_list(responsibilities.get(key), f"responsibilities.{key}", errors))
        extra = sorted(declared - blueprint_allowed[key])
        for object_id in extra:
            warnings.append(
                f"module '{module_id}' declares responsibilities.{key} "
                f"'{object_id}' not present in Blueprint module definition"
            )

    contract_section = manifest.get("contracts", {})
    if not isinstance(contract_section, dict):
        errors.append("contracts must be a mapping")
        contract_section = {}

    for key in CONTRACT_KEYS:
        for contract_id in _list(contract_section.get(key), f"contracts.{key}", errors):
            contract = contracts.get(contract_id)
            if contract is None:
                errors.append(f"contracts.{key} references unknown contract: {contract_id}")
                continue
            if key == "provides" and contract.get("provider") not in {module_id, "any_module"}:
                warnings.append(
                    f"module '{module_id}' provides '{contract_id}', "
                    f"but Blueprint provider is '{contract.get('provider')}'"
                )
            if key == "consumes" and contract.get("consumer") not in {module_id, "any_module"}:
                warnings.append(
                    f"module '{module_id}' consumes '{contract_id}', "
                    f"but Blueprint consumer is '{contract.get('consumer')}'"
                )

    reports = manifest.get("reports", {})
    if isinstance(reports, dict):
        status_report = reports.get("status_report")
        if not isinstance(status_report, str) or not status_report:
            warnings.append("reports.status_report is missing or empty")
    else:
        errors.append("reports must be a mapping")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def main() -> int:
    """CLI entry point."""

    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/validate_module_manifest.py "
            "<path-to-forprint_module_manifest.yaml>"
        )
        return 2

    result = validate_manifest(Path(sys.argv[1]))

    if result.warnings:
        print("⚠️ Module manifest validation warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.errors:
        print("❌ Module manifest validation failed:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    print("✅ Module manifest validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())