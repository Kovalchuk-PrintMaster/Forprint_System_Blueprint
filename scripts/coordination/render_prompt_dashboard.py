#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PROMPT_QUEUE_SCHEMA_VERSION = "prompt_queue_v0_2"
OUTGOING_PROMPTS_DIR = Path("coordination/outgoing_prompts")

COLOR_RESET = "\033[0m"
COLOR_BRIGHT_GREEN = "\033[92m"
COLOR_LIGHT_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_ORANGE = "\033[38;5;208m"
COLOR_RED = "\033[31m"
COLOR_GRAY = "\033[90m"
COLOR_CYAN = "\033[36m"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _status_color(status: str) -> str:
    if status == "accepted_by_blueprint":
        return COLOR_BRIGHT_GREEN
    if status == "completed_by_module":
        return COLOR_LIGHT_GREEN
    if status == "in_progress":
        return COLOR_YELLOW
    if status == "ready_for_module_pull":
        return COLOR_ORANGE
    if status in {"blocked", "returned_for_fix"}:
        return COLOR_RED
    if status == "planned":
        return COLOR_GRAY
    if status in {"not_required", "superseded"}:
        return COLOR_CYAN
    return ""


def _colorize(value: str, *, enabled: bool) -> str:
    if not enabled:
        return value
    color = _status_color(value)
    if not color:
        return value
    return f"{color}{value}{COLOR_RESET}"


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    return text if text else "-"


def _short_commit(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    return text[:12] if text else "-"


def _format_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]

    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(_strip_ansi(value)))

    def format_row(row: list[str]) -> str:
        return " | ".join(
            value + (" " * (widths[index] - len(_strip_ansi(value))))
            for index, value in enumerate(row)
        )

    separator = "-+-".join("-" * width for width in widths)

    output = [format_row(headers), separator]
    output.extend(format_row(row) for row in rows)
    return "\n".join(output)


def _strip_ansi(value: str) -> str:
    result = ""
    index = 0
    while index < len(value):
        if value[index] == "\033":
            end = value.find("m", index)
            if end == -1:
                break
            index = end + 1
            continue
        result += value[index]
        index += 1
    return result


def _sorted_prompt_queue(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = data.get("prompt_queue")
    if not isinstance(records, list):
        return []

    mappings = [record for record in records if isinstance(record, dict)]
    return sorted(mappings, key=lambda item: item.get("sequence", 999_999))


def resolve_next_prompt(data: dict[str, Any]) -> dict[str, Any] | None:
    for record in _sorted_prompt_queue(data):
        module_execution = record.get("module_execution")
        if not isinstance(module_execution, dict):
            continue
        if module_execution.get("status") == "ready_for_module_pull":
            return record
    return None


def render_dashboard(index_path: Path, *, use_color: bool = True) -> str:
    data = _load_yaml(index_path)
    module = data.get("module", index_path.parent.name)
    schema_version = data.get("schema_version")

    lines: list[str] = []
    lines.append(f"Prompt Queue Dashboard — {module}")
    lines.append(f"Index: {index_path}")
    lines.append(f"Schema: {schema_version or 'legacy'}")
    lines.append("")

    if schema_version != PROMPT_QUEUE_SCHEMA_VERSION:
        lines.append("Legacy outgoing prompt index detected.")
        lines.append("Prompt Queue v0.2 dashboard is not available for this module yet.")
        return "\n".join(lines)

    rows: list[list[str]] = []

    for record in _sorted_prompt_queue(data):
        module_execution = record.get("module_execution")
        blueprint_review = record.get("blueprint_review")

        module_execution = module_execution if isinstance(module_execution, dict) else {}
        blueprint_review = blueprint_review if isinstance(blueprint_review, dict) else {}

        module_status = _cell(module_execution.get("status"))
        blueprint_status = _cell(blueprint_review.get("status"))

        rows.append(
            [
                _cell(record.get("sequence")),
                _cell(record.get("prompt_id")),
                _cell(record.get("priority")),
                _colorize(module_status, enabled=use_color),
                _short_commit(module_execution.get("completion_commit")),
                _colorize(blueprint_status, enabled=use_color),
                _short_commit(blueprint_review.get("acceptance_commit")),
                _cell(record.get("file")),
            ]
        )

    headers = [
        "Seq",
        "Prompt ID",
        "Priority",
        "Module Status",
        "Module Commit",
        "Blueprint Status",
        "Blueprint Commit",
        "File",
    ]

    lines.append(_format_table(headers, rows))

    next_prompt = resolve_next_prompt(data)
    lines.append("")
    if next_prompt is None:
        lines.append("Next prompt: -")
    else:
        lines.append(
            "Next prompt: "
            f"{next_prompt.get('sequence')} "
            f"{next_prompt.get('prompt_id')} "
            f"({next_prompt.get('file')})"
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render ForPrint Prompt Queue v0.2 dashboard."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Blueprint repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module id, for example: forprint_library.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    index_path = root / OUTGOING_PROMPTS_DIR / args.module / "index.yaml"

    if not index_path.exists():
        print(f"FAILED: prompt index does not exist: {index_path}")
        return 1

    try:
        print(render_dashboard(index_path, use_color=not args.no_color))
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
