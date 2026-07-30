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


def render(report: dict[str, Any]) -> str:
    metadata = report.get("metadata")
    summary = report.get("summary")
    integrity = report.get("candidate_integrity")
    deferrals = report.get("explicit_deferrals")

    if not isinstance(metadata, dict):
        raise ValueError("metadata is missing")

    if not isinstance(summary, dict):
        raise ValueError("summary is missing")

    if not isinstance(integrity, dict):
        raise ValueError("candidate integrity is missing")

    if not isinstance(deferrals, list):
        raise ValueError("explicit deferrals are missing")

    closure_state = str(summary.get("closure_state", "FAILED"))
    state_color = GREEN if closure_state == "GREEN_WITH_EXPLICIT_DEFERRALS" else RED
    tracked = int(summary.get("tracked_files", 0))

    coverage_rows = [
        [
            "Repository reviewed",
            str(summary.get("reviewed_files")),
            str(tracked),
            (f"{summary.get('reviewed_files') / tracked * 100:.2f}%" if tracked else "0.00%"),
        ],
        [
            "Purpose evidenced",
            str(summary.get("purpose_evidenced")),
            str(tracked),
            (f"{summary.get('purpose_evidenced') / tracked * 100:.2f}%" if tracked else "0.00%"),
        ],
        [
            "Dependencies mapped",
            str(summary.get("dependencies_mapped")),
            str(tracked),
            (f"{summary.get('dependencies_mapped') / tracked * 100:.2f}%" if tracked else "0.00%"),
        ],
        [
            "Fully verified",
            str(summary.get("fully_verified")),
            str(tracked),
            (f"{summary.get('fully_verified') / tracked * 100:.2f}%" if tracked else "0.00%"),
        ],
    ]
    candidate_rows = [
        [
            "RCI v0.4",
            str(integrity.get("rci_validation")),
            str(integrity.get("rci_sha256", ""))[:12],
        ],
        [
            "REDM v0.4",
            str(integrity.get("redm_validation")),
            str(integrity.get("redm_sha256", ""))[:12],
        ],
    ]
    deferral_rows = [
        [
            str(item.get("deferral_id")),
            str(item.get("count")),
            ("yes" if item.get("must_remain_visible") else "no"),
        ]
        for item in deferrals
        if isinstance(item, dict)
    ]

    return "\n\n".join(
        [
            "\n".join(
                [
                    (f"{BOLD}{BLUE}Semantic Coverage Closure{RESET}"),
                    (f"closure state={state_color}{closure_state}{RESET}"),
                    (f"release decision={YELLOW}{summary.get('release_decision')}{RESET}"),
                    (
                        "repository lower bound="
                        f"{summary.get('repository_semantic_lower_bound') * 100:.2f}%  "
                        "reviewed quality="
                        f"{summary.get('reviewed_quality_lower_bound') * 100:.2f}%"
                    ),
                    (f"external rollout={CYAN}{metadata.get('external_rollout_state')}{RESET}"),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}1. Coverage lower bounds{RESET}",
                    table(
                        ["Metric", "Done", "Tracked", "Coverage"],
                        coverage_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}2. Candidate integrity{RESET}",
                    table(
                        ["Candidate", "Validation", "SHA-256"],
                        candidate_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}3. Explicit deferrals{RESET}",
                    table(
                        ["Deferral", "Count", "Visible"],
                        deferral_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}4. Interpretation{RESET}",
                    (
                        f"{DIM}• Closure is GREEN for the "
                        "verified lower-bound scope, not for "
                        "100% repository semantics.{RESET}"
                    ),
                    (
                        f"{DIM}• 646 unreviewed files and 25 "
                        "Wave 2 unknown records stay explicit "
                        "through reconciliation.{RESET}"
                    ),
                    (
                        f"{DIM}• Reconciliation may proceed; "
                        "acceptance and external rollout remain "
                        "separately gated.{RESET}"
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
