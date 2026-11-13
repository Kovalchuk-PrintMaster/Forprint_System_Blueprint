from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _load(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []

    identity = _load("machine/module_identity_registry.yaml")
    canonical = set(identity.get("canonical_module_ids", []))
    forbidden = set(identity.get("forbidden_current_ids", []))

    if identity.get("authority_state") != "canonical":
        errors.append("IDENTITY_NOT_CANONICAL")

    registry_ids = {
        "machine/modules.yaml": {
            item["id"] for item in _load("machine/modules.yaml").get("modules", [])
        },
        "coordination/module_sources/module_git_sources.yaml": {
            item["module_id"]
            for item in _load(
                "coordination/module_sources/module_git_sources.yaml"
            )["module_git_sources"].get("modules", [])
        },
        "coordination/registry/coordination_source_registry_v0_1.yaml": {
            item["module_id"]
            for item in _load(
                "coordination/registry/coordination_source_registry_v0_1.yaml"
            ).get("modules", [])
        },
        "coordination/module_policy/module_policy_index.yaml": {
            item["module_id"]
            for item in _load(
                "coordination/module_policy/module_policy_index.yaml"
            )["module_policy_index"].get("modules", [])
        },
    }

    for source, ids in registry_ids.items():
        unknown = sorted(ids - canonical)
        forbidden_here = sorted(ids & forbidden)
        if unknown:
            errors.append(f"UNKNOWN_IDS:{source}:{','.join(unknown)}")
        if forbidden_here:
            errors.append(
                f"FORBIDDEN_CURRENT_IDS:{source}:{','.join(forbidden_here)}"
            )

    machine_ids = registry_ids["machine/modules.yaml"]
    if "forprint_accounting_registry_service" not in machine_ids:
        errors.append("ACCOUNTING_CANONICAL_ID_MISSING")
    if "accounting_registry_service" in machine_ids:
        errors.append("ACCOUNTING_LEGACY_ID_STILL_CURRENT")

    legacy_queue = _load(
        "coordination/outgoing_prompts/forprint_operational_registry/index.yaml"
    )
    if legacy_queue.get("lifecycle") != "historical_non_authoritative":
        errors.append("LEGACY_OPERATIONS_QUEUE_NOT_HISTORICAL")
    if legacy_queue.get("authority") != "none":
        errors.append("LEGACY_OPERATIONS_QUEUE_HAS_AUTHORITY")
    if legacy_queue.get("active_prompts") != []:
        errors.append("LEGACY_OPERATIONS_QUEUE_STILL_ACTIVE")

    current_queue = _load(
        "coordination/outgoing_prompts/"
        "forprint_operations_control_registry/index.yaml"
    )
    if current_queue.get("schema_version") != "prompt_queue_v0_2":
        errors.append("CURRENT_OPERATIONS_QUEUE_SCHEMA")
    if current_queue.get("module") != "forprint_operations_control_registry":
        errors.append("CURRENT_OPERATIONS_QUEUE_MODULE")
    if not isinstance(current_queue.get("prompt_queue"), list):
        errors.append("CURRENT_OPERATIONS_QUEUE_RECORDS")

    source_registry = _load(
        "coordination/registry/coordination_source_registry_v0_1.yaml"
    )
    operations = next(
        (
            item
            for item in source_registry.get("modules", [])
            if item.get("module_id") == "forprint_operations_control_registry"
        ),
        None,
    )
    if operations is None:
        errors.append("OPERATIONS_SOURCE_REGISTRY_ENTRY_MISSING")
    else:
        path = operations["sources"]["prompt_queue"]["path"]
        expected = (
            "coordination/outgoing_prompts/"
            "forprint_operations_control_registry/index.yaml"
        )
        if path != expected:
            errors.append("OPERATIONS_SOURCE_REGISTRY_QUEUE_PATH")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR={error}")
        print("MODULE_IDENTITY_ROUTING_VALIDATION=FAIL")
        return 1

    print("MODULE_IDENTITY_ROUTING_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
