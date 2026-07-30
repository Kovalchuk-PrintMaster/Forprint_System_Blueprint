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
MAGENTA = "\033[35m"
BLUE = "\033[34m"
DIM = "\033[2m"
RED = "\033[31m"
SUPPORTED_MODULE = "forprint_system_blueprint"
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


def color_status(status: str) -> str:
    normalized = status.lower()

    if normalized in {"completed", "accepted"}:
        color = GREEN
    elif normalized in {"active", "approved", "ready"}:
        color = CYAN
    elif normalized in {"planned", "draft"}:
        color = YELLOW
    elif normalized in {"deferred", "superseded"}:
        color = DIM
    else:
        color = RED

    return f"{color}{status}{RESET}"


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


def render_roadmap(data: dict[str, Any], module: str) -> str:
    metadata = data.get("metadata")
    steps = data.get("steps")

    if not isinstance(metadata, dict) or not isinstance(steps, list):
        raise ValueError("Invalid roadmap structure")

    current = metadata.get("current_step_id")
    rows: list[list[str]] = []

    for item in sorted(
        [step for step in steps if isinstance(step, dict)],
        key=lambda step: (
            step.get("sequence", 10000),
            str(step.get("step_id", "")),
        ),
    ):
        step_id = str(item.get("step_id", ""))
        status = str(item.get("status", "unknown"))
        rows.append(
            [
                "▶" if step_id == current else "",
                str(item.get("sequence", "")),
                color_status(status),
                step_id,
                str(item.get("title", "")),
            ]
        )

    return "\n".join(
        [
            f"{BOLD}{BLUE}Blueprint Roadmap{RESET} {DIM}module={module}{RESET}",
            (
                f"current={CYAN}{current}{RESET}  "
                f"ahead={metadata.get('actionable_steps_after_current')}"
            ),
            table(["", "#", "Status", "Step ID", "Title"], rows),
        ]
    )


def render_prompts(data: dict[str, Any], module: str) -> str:
    metadata = data.get("metadata")
    prompts = data.get("prompts")

    if not isinstance(metadata, dict) or not isinstance(prompts, list):
        raise ValueError("Invalid prompt queue structure")

    active = metadata.get("active_prompt_id")
    order = {"approved": 0, "draft": 1, "completed": 2}
    records = [item for item in prompts if isinstance(item, dict)]
    records.sort(
        key=lambda item: (
            order.get(str(item.get("status")), 99),
            str(item.get("prompt_id", "")),
        )
    )
    rows: list[list[str]] = []

    for item in records:
        prompt_id = str(item.get("prompt_id", ""))
        status = str(item.get("status", "unknown"))
        rows.append(
            [
                "▶" if prompt_id == active else "",
                color_status(status),
                prompt_id,
                str(item.get("roadmap_step_id", "")),
                str(item.get("completion_packet", "—")),
            ]
        )

    return "\n".join(
        [
            f"{BOLD}{MAGENTA}Blueprint Prompt Queue{RESET} {DIM}module={module}{RESET}",
            (
                f"active={CYAN}{active}{RESET}  "
                f"approved={metadata.get('approved_prompt_count')}  "
                f"draft={metadata.get('draft_prompt_count')}  "
                f"completed={metadata.get('completed_prompt_count')}"
            ),
            table(
                ["", "Status", "Prompt ID", "Roadmap Step", "Completion Packet"],
                rows,
            ),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    parser.add_argument("--view", choices=("roadmap", "prompts"), required=True)
    args = parser.parse_args()

    if args.module != SUPPORTED_MODULE:
        print(f"{RED}Unsupported module: {args.module}{RESET}")
        return 2

    if args.view == "roadmap":
        data = load_yaml(Path("coordination/self_coordination/roadmap.yaml"))
        print(render_roadmap(data, args.module))
    else:
        data = load_yaml(Path("coordination/self_coordination/prompt_queue/index.yaml"))
        print(render_prompts(data, args.module))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
