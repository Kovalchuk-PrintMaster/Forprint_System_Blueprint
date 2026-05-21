# python scripts/generate_mermaid.py
"""
Generate Mermaid diagrams from machine-readable Blueprint YAML.

На старті генерує:
- diagrams/module_graph.mmd з machine/data_flows.yaml;
- diagrams/ownership_map.mmd з machine/ownership.yaml.
"""

from __future__ import annotations

# Дозволяє запускати скрипт і як модуль, і напряму: python scripts/name.py
if __package__ is None or __package__ == "":
    import sys as _sys
    from pathlib import Path as _Path

    _sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

import re
import sys
from pathlib import Path
from typing import Any

from scripts.blueprint_utils import load_yaml, project_root, write_text


def _label(value: str) -> str:
    """Convert an id-like value into a readable Mermaid label."""

    return value.replace("_", " ").title()


def _safe_node_id(value: str) -> str:
    """Make Mermaid-safe node id."""

    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def render_module_graph(data_flows: list[dict[str, Any]]) -> str:
    """Render module graph from data flows."""

    lines = ["graph TD"]
    for flow in data_flows:
        source = flow["source"]
        target = flow["target"]
        contract = flow["contract"]
        source_id = _safe_node_id(source)
        target_id = _safe_node_id(target)
        lines.append(
            f'    {source_id}["{_label(source)}"] -->|{contract}| {target_id}["{_label(target)}"]'
        )
    lines.append("")
    return "\n".join(lines)


def render_ownership_map(ownership: dict[str, Any]) -> str:
    """Render ownership map from ownership.yaml."""

    lines = ["graph TD"]
    for object_id, record in sorted(ownership.items()):
        owner = record["owner"]
        owner_id = _safe_node_id(owner)
        object_node_id = _safe_node_id(f"object_{object_id}")
        lines.append(f'    {owner_id}["{_label(owner)}"] --> {object_node_id}["{object_id}"]')
    lines.append("")
    return "\n".join(lines)


def generate(root: Path | None = None) -> list[Path]:
    """Generate Mermaid files and return written paths."""

    root = root or project_root()
    machine = root / "machine"
    diagrams = root / "diagrams"

    flows_yaml = load_yaml(machine / "data_flows.yaml")
    ownership_yaml = load_yaml(machine / "ownership.yaml")

    module_graph = render_module_graph(flows_yaml.get("data_flows", []))
    ownership_map = render_ownership_map(ownership_yaml.get("ownership", {}))

    module_graph_path = diagrams / "module_graph.mmd"
    ownership_map_path = diagrams / "ownership_map.mmd"

    write_text(module_graph_path, module_graph)
    write_text(ownership_map_path, ownership_map)

    return [module_graph_path, ownership_map_path]


def main() -> int:
    """CLI entry point."""

    paths = generate()
    for path in paths:
        print(f"✅ Generated {path.relative_to(project_root())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
