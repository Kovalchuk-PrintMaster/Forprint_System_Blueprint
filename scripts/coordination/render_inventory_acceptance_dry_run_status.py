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
            pad(
                f"{BOLD}{value}{RESET}",
                widths[index],
            )
            for index, value in enumerate(headers)
        )
        + " │"
    )
    body = [
        "│ " + " │ ".join(pad(value, widths[index]) for index, value in enumerate(row)) + " │"
        for row in rows
    ]
    return "\n".join([top, header, middle, *body, bottom])


def colored_status(value: str) -> str:
    if value == "PASSED":
        return f"{GREEN}{value}{RESET}"

    if value == "SIMULATED":
        return f"{YELLOW}{value}{RESET}"

    return f"{RED}{value}{RESET}"


def render(report: dict[str, Any]) -> str:
    metadata = report.get("metadata")
    summary = report.get("summary")
    scenarios = report.get("scenarios")
    actions = report.get("simulated_actions")

    if not isinstance(metadata, dict):
        raise ValueError("metadata is missing")

    if not isinstance(summary, dict):
        raise ValueError("summary is missing")

    if not isinstance(scenarios, list):
        raise ValueError("scenarios are missing")

    if not isinstance(actions, list):
        raise ValueError("simulated actions are missing")

    result = str(metadata.get("result", "FAILED"))
    result_color = GREEN if result == "PASSED" else RED
    scenario_rows = [
        [
            str(item.get("scenario_id")),
            colored_status(str(item.get("status"))),
            str(item.get("decision")),
        ]
        for item in scenarios
        if isinstance(item, dict)
    ]
    action_rows = [
        [
            str(item.get("sequence")),
            str(item.get("action")),
            colored_status(str(item.get("status"))),
            str(item.get("effect_applied")),
        ]
        for item in actions
        if isinstance(item, dict)
    ]

    return "\n\n".join(
        [
            "\n".join(
                [
                    (f"{BOLD}{BLUE}Inventory Acceptance Dry Run{RESET}"),
                    (f"result={result_color}{result}{RESET}"),
                    (f"release decision={CYAN}{summary.get('release_decision')}{RESET}"),
                    (
                        "scenarios="
                        f"{summary.get('scenario_count')}  "
                        "passed="
                        f"{summary.get('passed_scenario_count')}  "
                        "failed="
                        f"{summary.get('failed_scenario_count')}"
                    ),
                    (
                        "candidate acceptance="
                        f"{summary.get('candidate_acceptance_performed')}  "
                        "git merge="
                        f"{summary.get('git_merge_performed')}  "
                        "effects applied="
                        f"{summary.get('dry_run_effects_applied')}"
                    ),
                    (f"external rollout={CYAN}{metadata.get('external_rollout_state')}{RESET}"),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}1. Dry-run scenarios{RESET}",
                    table(
                        ["Scenario", "Status", "Decision"],
                        scenario_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}2. Simulated actions{RESET}",
                    table(
                        [
                            "#",
                            "Action",
                            "Status",
                            "Effect applied",
                        ],
                        action_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}3. Interpretation{RESET}",
                    (
                        f"{DIM}• PASSED means acceptance prerequisites "
                        "can be simulated without mutating candidate "
                        "files or Git state.{RESET}"
                    ),
                    (
                        f"{DIM}• No candidate was accepted, no merge "
                        "was performed, and every action remains "
                        "SIMULATED with effect_applied=false.{RESET}"
                    ),
                    (
                        f"{DIM}• Packet integrity review is the next "
                        "mandatory gate; external rollout stays gated."
                        f"{RESET}"
                    ),
                ]
            ),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    print(render(load_yaml(Path(args.report))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
