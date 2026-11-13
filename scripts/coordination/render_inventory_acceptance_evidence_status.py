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


def render(
    index: dict[str, Any],
    report: dict[str, Any],
) -> str:
    metadata = report.get("metadata")
    summary = report.get("summary")
    entries = index.get("evidence_entries")
    deferrals = index.get("explicit_deferrals")

    if not isinstance(metadata, dict):
        raise ValueError("validation metadata is missing")

    if not isinstance(summary, dict):
        raise ValueError("validation summary is missing")

    if not isinstance(entries, list):
        raise ValueError("evidence entries are missing")

    if not isinstance(deferrals, list):
        raise ValueError("explicit deferrals are missing")

    result = str(metadata.get("result", "FAILED"))
    result_color = GREEN if result == "PASSED" else RED
    entry_rows = [
        [
            str(item.get("evidence_id")),
            str(item.get("integrity_mode")),
            str(item.get("authority")),
            str(item.get("artifact_type")),
        ]
        for item in entries
        if isinstance(item, dict)
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
                    (f"{BOLD}{BLUE}Inventory Acceptance Evidence Index{RESET}"),
                    (f"result={result_color}{result}{RESET}"),
                    (f"release decision={CYAN}{summary.get('release_decision')}{RESET}"),
                    (
                        "entries="
                        f"{summary.get('evidence_entry_count')}  "
                        "passed="
                        f"{summary.get('passed_entry_count')}  "
                        "sha256="
                        f"{summary.get('stable_hash_entry_count')}  "
                        "runtime="
                        f"{summary.get('runtime_result_entry_count')}"
                    ),
                    (
                        "candidate acceptance performed="
                        f"{summary.get('candidate_acceptance_performed')}"
                    ),
                    (f"external rollout={CYAN}{metadata.get('external_rollout_state')}{RESET}"),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}1. Indexed evidence{RESET}",
                    table(
                        [
                            "Evidence",
                            "Integrity",
                            "Authority",
                            "Type",
                        ],
                        entry_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}2. Explicit deferrals{RESET}",
                    table(
                        [
                            "Deferral",
                            "Count",
                            "Visible",
                        ],
                        deferral_rows,
                    ),
                ]
            ),
            "\n".join(
                [
                    f"{BOLD}3. Interpretation{RESET}",
                    (
                        f"{DIM}• Stable artifacts use SHA-256; "
                        "runtime reports use result-path validation "
                        "so normal regeneration does not stale the index."
                        f"{RESET}"
                    ),
                    (
                        f"{DIM}• RCI v0.4 and REDM v0.4 remain "
                        "candidate evidence and are not accepted by "
                        "this step.{RESET}"
                    ),
                    (
                        f"{DIM}• The dry run may proceed while 646 "
                        "unreviewed files and 25 unknown records "
                        "remain explicitly visible.{RESET}"
                    ),
                ]
            ),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    print(
        render(
            load_yaml(Path(args.index)),
            load_yaml(Path(args.report)),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
