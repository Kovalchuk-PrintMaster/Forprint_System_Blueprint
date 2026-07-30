#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BLUE = "\033[34m"
RED = "\033[31m"
DIM = "\033[2m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
SUPPORTED_MODULE = "forprint_system_blueprint"


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")

    return data


def find_value(node: Any, key: str) -> Any:
    if isinstance(node, dict):
        if key in node:
            return node[key]

        for value in node.values():
            found = find_value(value, key)

            if found is not None:
                return found

    if isinstance(node, list):
        for value in node:
            found = find_value(value, key)

            if found is not None:
                return found

    return None


def visible_length(value: str) -> int:
    return len(ANSI_RE.sub("", value))


def pad(value: str, width: int) -> str:
    return value + (" " * max(0, width - visible_length(value)))


def table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [
        max(
            visible_length(headers[index]),
            *[visible_length(row[index]) for row in rows],
        )
        for index in range(len(headers))
    ]
    top = "┌" + "┬".join("─" * (width + 2) for width in widths) + "┐"
    middle = "├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
    bottom = "└" + "┴".join("─" * (width + 2) for width in widths) + "┘"
    header = (
        "│ "
        + " │ ".join(
            pad(f"{BOLD}{value}{RESET}", widths[index]) for index, value in enumerate(headers)
        )
        + " │"
    )
    body = [
        "│ " + " │ ".join(pad(value, widths[index]) for index, value in enumerate(row)) + " │"
        for row in rows
    ]
    return "\n".join([top, header, middle, *body, bottom])


def ratio_color(value: float) -> str:
    if value >= 0.8:
        return GREEN

    if value >= 0.5:
        return CYAN

    return YELLOW


def metric_row(
    label: str,
    completed: int,
    total: int,
) -> list[str]:
    ratio = completed / total if total else 0.0
    color = ratio_color(ratio)
    return [
        label,
        str(completed),
        str(total),
        f"{color}{ratio * 100:.2f}%{RESET}",
    ]


def render_inventory_status(
    wave: dict[str, Any],
    dashboard: dict[str, Any],
    maintenance: dict[str, Any],
    roadmap: dict[str, Any],
    module: str,
) -> str:
    tracked = int(find_value(wave, "tracked_files") or 0)
    reviewed = int(find_value(wave, "wave_1_plus_wave_2_reviewed") or 0)
    purpose = int(find_value(wave, "purpose_evidenced") or 0)
    dependencies = int(find_value(wave, "dependencies_mapped") or 0)
    verified = int(find_value(wave, "fully_verified") or 0)
    records_unknown = int(find_value(wave, "records_with_unknowns") or 0)
    changed_paths = int(find_value(dashboard, "changed_paths_since_rci_commit") or 0)
    scope_delta = int(find_value(dashboard, "artifact_map_scope_delta") or 0)
    rollout_state = str(find_value(maintenance, "state") or "unknown")
    roadmap_metadata = roadmap.get("metadata")

    if not isinstance(roadmap_metadata, dict):
        raise ValueError("Roadmap metadata is missing")

    current_step = str(roadmap_metadata.get("current_step_id", "unknown"))
    lower_bound = min(
        [
            reviewed / tracked if tracked else 0.0,
            purpose / tracked if tracked else 0.0,
            dependencies / tracked if tracked else 0.0,
            verified / tracked if tracked else 0.0,
        ]
    )

    rows = [
        metric_row("Reviewed", reviewed, tracked),
        metric_row("Purpose evidenced", purpose, tracked),
        metric_row("Dependencies mapped", dependencies, tracked),
        metric_row("Fully verified", verified, tracked),
    ]
    color = ratio_color(lower_bound)

    return "\n".join(
        [
            (f"{BOLD}{BLUE}Blueprint Inventory Status{RESET} {DIM}module={module}{RESET}"),
            (f"minimum completeness lower bound={color}{lower_bound * 100:.2f}%{RESET}"),
            table(
                ["Metric", "Done", "Tracked", "Coverage"],
                rows,
            ),
            (
                f"unknown records in Wave 2={YELLOW}{records_unknown}{RESET}  "
                f"changed since RCI={YELLOW}{changed_paths}{RESET}  "
                f"scope delta={YELLOW}{scope_delta}{RESET}"
            ),
            (f"external rollout={CYAN}{rollout_state}{RESET}  current={CYAN}{current_step}{RESET}"),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    args = parser.parse_args()

    if args.module != SUPPORTED_MODULE:
        print(f"{RED}Unsupported module: {args.module}{RESET}")
        return 2

    print(
        render_inventory_status(
            load_yaml(
                Path(
                    "coordination/internal_work/blueprint/"
                    "inventory_refresh/"
                    "2026-07-29__blueprint__"
                    "semantic_inventory_wave_2_v0_1.yaml"
                )
            ),
            load_yaml(
                Path(
                    "coordination/internal_work/blueprint/"
                    "inventory_refresh/"
                    "2026-07-29__blueprint__"
                    "inventory_coverage_drift_dashboard_v0_1.yaml"
                )
            ),
            load_yaml(Path("coordination/repository_knowledge/inventory_maintenance_v0_1.yaml")),
            load_yaml(Path("coordination/self_coordination/roadmap.yaml")),
            args.module,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
