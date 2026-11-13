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
RED = "\033[31m"
BLUE = "\033[34m"
DIM = "\033[2m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping: {path}")
    return data


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


def color(value: str) -> str:
    if value == "FRESH":
        return f"{GREEN}{value}{RESET}"
    if value == "BOUNDED_REFRESH_REQUIRED":
        return f"{YELLOW}{value}{RESET}"
    return f"{RED}{value}{RESET}"


def render(report: dict[str, Any]) -> str:
    metadata = report.get("metadata")
    summary = report.get("summary")
    snapshots = report.get("snapshots")
    classes = report.get("change_class_counts")

    if not isinstance(metadata, dict):
        raise ValueError("metadata is missing")
    if not isinstance(summary, dict):
        raise ValueError("summary is missing")
    if not isinstance(snapshots, list):
        raise ValueError("snapshots are missing")
    if not isinstance(classes, dict):
        classes = {}

    rows = []
    for item in snapshots:
        if not isinstance(item, dict):
            continue
        baseline = str(item.get("baseline_commit") or "—")
        rows.append(
            [
                str(item.get("comparison_id", "")),
                color(str(item.get("freshness", "FAILED"))),
                baseline[:8],
                str(item.get("changed_path_count", 0)),
                str(item.get("knowledge_relevant_changed_path_count", 0)),
            ]
        )

    class_rows = [[str(name), str(count)] for name, count in sorted(classes.items())]

    decision = str(summary.get("release_decision", "UNKNOWN"))
    decision_color = (
        GREEN
        if decision == "PROCEED_AS_FRESH"
        else YELLOW
        if decision == "PROCEED_WITH_BOUNDED_REFRESH"
        else RED
    )

    sections = [
        "\n".join(
            [
                f"{BOLD}{BLUE}Repository Knowledge Freshness{RESET}",
                f"release decision={decision_color}{decision}{RESET}",
                (
                    f"snapshots={summary.get('snapshot_count')}  "
                    f"fresh={summary.get('fresh_snapshot_count')}  "
                    f"bounded={summary.get('bounded_refresh_snapshot_count')}  "
                    f"failed={summary.get('failed_snapshot_count')}"
                ),
                (
                    f"changed paths={summary.get('changed_path_union_count')}  "
                    "knowledge relevant="
                    f"{summary.get('knowledge_relevant_changed_path_union_count')}"
                ),
                (f"external rollout={CYAN}{metadata.get('external_rollout_state')}{RESET}"),
            ]
        ),
        "\n".join(
            [
                f"{BOLD}1. Snapshot freshness{RESET}",
                table(
                    ["Snapshot", "Freshness", "Baseline", "Changed", "Relevant"],
                    rows,
                ),
            ]
        ),
    ]

    if class_rows:
        sections.append(
            "\n".join(
                [
                    f"{BOLD}2. Changed-path classes{RESET}",
                    table(["Class", "Count"], class_rows),
                ]
            )
        )

    sections.append(
        "\n".join(
            [
                f"{BOLD}3. Interpretation{RESET}",
                (f"{DIM}• FRESH: no committed paths changed after the snapshot baseline.{RESET}"),
                (
                    f"{DIM}• BOUNDED_REFRESH_REQUIRED: integrity "
                    f"is valid, but RCI enrichment must include "
                    f"the listed committed changes.{RESET}"
                ),
                (f"{DIM}• FAILED: integrity or policy blocks RCI enrichment.{RESET}"),
            ]
        )
    )
    return "\n\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    print(render(load_yaml(Path(args.report))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
