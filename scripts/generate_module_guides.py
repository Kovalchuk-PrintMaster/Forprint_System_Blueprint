# python scripts/generate_module_guides.py
"""
Generate module guides / prompt files from Blueprint YAML.

Ці файли можна вставляти в окремі чати дочірніх модулів, щоб не пояснювати
кожного разу всю систему вручну.
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

from scripts.blueprint_utils import load_yaml, project_root, write_text


def _bullet_list(values: list[str]) -> str:
    if not values:
        return "- Немає явно зафіксованих пунктів."
    return "\n".join(f"- `{value}`" for value in values)


def _find_related_flows(module_id: str, flows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    incoming = [flow for flow in flows if flow.get("target") == module_id]
    outgoing = [flow for flow in flows if flow.get("source") == module_id]
    return incoming, outgoing


def _find_related_contracts(
    module_id: str, contracts: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    consumes = [contract for contract in contracts if contract.get("consumer") == module_id]
    provides = [contract for contract in contracts if contract.get("provider") == module_id]
    return consumes, provides


def _render_flow(flow: dict[str, Any]) -> str:
    objects = ", ".join(f"`{obj}`" for obj in flow.get("data_objects", []))
    return (
        f"- `{flow['id']}`: `{flow['source']}` → `{flow['target']}` "
        f"via `{flow['contract']}`; objects: {objects}; "
        f"status: `{flow.get('status', 'unknown')}`; criticality: `{flow.get('criticality', 'unknown')}`"
    )


def _render_contract(contract: dict[str, Any]) -> str:
    objects = ", ".join(f"`{obj}`" for obj in contract.get("data_objects", []))
    return (
        f"- `{contract['id']}`: provider `{contract['provider']}`, "
        f"consumer `{contract['consumer']}`, status `{contract.get('status', 'unknown')}`; "
        f"objects: {objects}"
    )


def render_module_guide(
    module: dict[str, Any], flows: list[dict[str, Any]], contracts: list[dict[str, Any]]
) -> str:
    """Render one Markdown module guide."""

    module_id = module["id"]
    incoming_flows, outgoing_flows = _find_related_flows(module_id, flows)
    consumed_contracts, provided_contracts = _find_related_contracts(module_id, contracts)

    incoming_text = "\n".join(_render_flow(flow) for flow in incoming_flows) or "- Немає."
    outgoing_text = "\n".join(_render_flow(flow) for flow in outgoing_flows) or "- Немає."
    consumed_contracts_text = "\n".join(_render_contract(c) for c in consumed_contracts) or "- Немає."
    provided_contracts_text = "\n".join(_render_contract(c) for c in provided_contracts) or "- Немає."

    return f"""# {module['title']}

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`{module_id}`

## Type

`{module.get('type', 'unknown')}`

## Status

`{module.get('status', 'unknown')}`

## Role

{module.get('role', '').strip()}

## Owns

{_bullet_list(module.get('owns', []))}

## Consumes

{_bullet_list(module.get('consumes', []))}

## Provides

{_bullet_list(module.get('provides', []))}

## Must not own

{_bullet_list(module.get('must_not_own', []))}

## Incoming data flows

{incoming_text}

## Outgoing data flows

{outgoing_text}

## Consumed contracts

{consumed_contracts_text}

## Provided contracts

{provided_contracts_text}

## Prompt for module chat

Ти працюєш над модулем `{module_id}` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/{module_id}/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
"""


def generate(root: Path | None = None) -> list[Path]:
    """Generate all module guides."""

    root = root or project_root()
    machine = root / "machine"
    module_guides = root / "module_guides"

    modules = load_yaml(machine / "modules.yaml").get("modules", [])
    flows = load_yaml(machine / "data_flows.yaml").get("data_flows", [])
    contracts = load_yaml(machine / "contracts.yaml").get("contracts", [])

    written: list[Path] = []
    for module in modules:
        content = render_module_guide(module, flows, contracts)
        path = module_guides / f"{module['id']}.md"
        write_text(path, content)
        written.append(path)

    return written


def main() -> int:
    """CLI entry point."""

    paths = generate()
    for path in paths:
        print(f"✅ Generated {path.relative_to(project_root())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
