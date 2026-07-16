#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.reporting.coordination_result_tables import render_next_prompt_summary

PROMPT_QUEUE_SCHEMA_VERSION = "prompt_queue_v0_2"
OUTGOING_PROMPTS_DIR = Path("coordination/outgoing_prompts")


@dataclass(frozen=True)
class NextPromptSummary:
    module: str
    sequence: int
    prompt_id: str
    title: str
    priority: str
    file: str
    path: Path


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _sorted_prompt_queue(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = data.get("prompt_queue")
    if not isinstance(records, list):
        return []

    mappings = [record for record in records if isinstance(record, dict)]
    return sorted(mappings, key=lambda item: item.get("sequence", 999_999))


def _resolve_next_prompt(data: dict[str, Any]) -> dict[str, Any] | None:
    for record in _sorted_prompt_queue(data):
        module_execution = record.get("module_execution")
        if not isinstance(module_execution, dict):
            continue
        if module_execution.get("status") == "ready_for_module_pull":
            return record
    return None


def resolve_next_prompt_summary(root: Path, module: str) -> NextPromptSummary:
    index_path = root / OUTGOING_PROMPTS_DIR / module / "index.yaml"

    if not index_path.exists():
        raise FileNotFoundError(f"prompt index does not exist: {index_path}")

    data = _load_yaml(index_path)
    schema_version = data.get("schema_version")

    if schema_version != PROMPT_QUEUE_SCHEMA_VERSION:
        raise ValueError(
            f"module `{module}` is not migrated to {PROMPT_QUEUE_SCHEMA_VERSION}"
        )

    next_prompt = _resolve_next_prompt(data)

    if next_prompt is None:
        raise LookupError(f"module `{module}` has no ready prompt")

    file_value = next_prompt.get("file")
    if not isinstance(file_value, str) or not file_value.strip():
        raise ValueError(f"next prompt for module `{module}` has invalid file")

    prompt_path = root / OUTGOING_PROMPTS_DIR / module / file_value

    if not prompt_path.exists():
        raise FileNotFoundError(f"next prompt file does not exist: {prompt_path}")

    return NextPromptSummary(
        module=module,
        sequence=int(next_prompt.get("sequence")),
        prompt_id=str(next_prompt.get("prompt_id")),
        title=str(next_prompt.get("title")),
        priority=str(next_prompt.get("priority")),
        file=file_value,
        path=prompt_path,
    )


def render_summary(
    summary: NextPromptSummary,
    root: Path,
    *,
    use_color: bool = True,
) -> str:
    relative_path = summary.path.relative_to(root)
    return render_next_prompt_summary(
        module=summary.module,
        sequence=summary.sequence,
        prompt_id=summary.prompt_id,
        title=summary.title,
        priority=summary.priority,
        file=summary.file,
        path=str(relative_path),
        use_color=use_color,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve the next ready ForPrint Prompt Queue v0.2 prompt."
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
        "--path-only",
        action="store_true",
        help="Print only the resolved prompt path.",
    )
    parser.add_argument(
        "--read",
        action="store_true",
        help="Print the resolved prompt metadata and prompt file content.",
    )

    args = parser.parse_args()
    root = Path(args.root).resolve()

    try:
        summary = resolve_next_prompt_summary(root, args.module)
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    if args.path_only:
        try:
            print(summary.path.relative_to(root))
        except ValueError:
            print(summary.path)
        return 0

    print(
        render_summary(
            summary,
            root,
            use_color="NO_COLOR" not in os.environ,
        )
    )

    if args.read:
        print("")
        print("=" * 80)
        print(summary.path.read_text(encoding="utf-8"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
