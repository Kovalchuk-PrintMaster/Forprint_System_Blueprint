#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.reporting.table_renderer import TableRow, render_boxed_table_lines

PROMPT_QUEUE_SCHEMA_VERSION = "prompt_queue_v0_2"
OUTGOING_PROMPTS_DIR = Path("coordination/outgoing_prompts")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BLUEPRINT_MODULE = "forprint_system_blueprint"
BLUEPRINT_STATUS_SCRIPT = (
    PROJECT_ROOT
    / "scripts/coordination/"
    "render_blueprint_self_coordination_status.py"
)

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


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    return text if text else "-"


def _short_commit(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    return text[:12] if text else "-"


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

    next_prompt = resolve_next_prompt(data)

    lines.append("Active Prompt Queue")
    lines.extend(_render_active_prompt_table(data, next_prompt, use_color=use_color))

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

    lines.append("")
    lines.append("Draft / Planned Prompts")
    lines.extend(_render_draft_prompt_table(index_path, use_color=use_color))
    lines.append("")
    lines.append(
        "Draft rule: draft prompts are planning-only artifacts. "
        "They may be read for awareness, but must not be executed until "
        "Blueprint promotes them into the active prompt queue."
    )

    return _finalize_output(lines, use_color=use_color)


def _render_active_prompt_table(
    data: dict[str, Any],
    next_prompt: dict[str, Any] | None,
    *,
    use_color: bool,
) -> list[str]:
    rows: list[TableRow] = []

    for record in _sorted_prompt_queue(data):
        module_execution = record.get("module_execution")
        blueprint_review = record.get("blueprint_review")

        module_execution = module_execution if isinstance(module_execution, dict) else {}
        blueprint_review = blueprint_review if isinstance(blueprint_review, dict) else {}

        module_status = _cell(module_execution.get("status"))
        blueprint_status = _cell(blueprint_review.get("status"))
        is_next = _same_prompt(record, next_prompt)

        rows.append(
            TableRow(
                values=(
                    "→" if is_next else "",
                    _cell(record.get("sequence")),
                    _cell(record.get("prompt_id")),
                    _cell(record.get("priority")),
                    module_status,
                    _short_commit(module_execution.get("completion_commit")),
                    blueprint_status,
                    _short_commit(blueprint_review.get("acceptance_commit")),
                    _cell(record.get("file")),
                ),
                color=_record_row_color(
                    module_status,
                    blueprint_status,
                    is_next=is_next,
                ),
            )
        )

    if not rows:
        rows.append(
            TableRow(
                values=(
                    "",
                    "-",
                    "No active prompt queue records",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                ),
                color=COLOR_GRAY,
            )
        )

    return _boxed_table(
        headers=(
            "",
            "Seq",
            "Prompt ID",
            "Priority",
            "Module Status",
            "Module Commit",
            "Blueprint Status",
            "Blueprint Commit",
            "File",
        ),
        widths=(2, 4, 52, 10, 23, 14, 23, 14, 78),
        rows=rows,
        use_color=use_color,
    )


def _render_draft_prompt_table(index_path: Path, *, use_color: bool) -> list[str]:
    draft_paths = _sorted_draft_prompts(index_path)
    rows: list[TableRow] = []

    for draft_path in draft_paths:
        rows.append(
            TableRow(
                values=(
                    "",
                    _draft_id(draft_path),
                    _draft_title(draft_path),
                    str(draft_path.relative_to(index_path.parent)),
                ),
                color=COLOR_GRAY,
            )
        )

    if not rows:
        rows.append(
            TableRow(
                values=("", "-", "No draft prompts found", "-"),
                color=COLOR_GRAY,
            )
        )

    return _boxed_table(
        headers=("", "Draft ID", "Title", "File"),
        widths=(2, 64, 56, 78),
        rows=rows,
        use_color=use_color,
    )


def _same_prompt(
    record: dict[str, Any],
    next_prompt: dict[str, Any] | None,
) -> bool:
    if next_prompt is None:
        return False

    return (
        record.get("sequence") == next_prompt.get("sequence")
        and record.get("prompt_id") == next_prompt.get("prompt_id")
    )


def _record_row_color(
    module_status: str,
    blueprint_status: str,
    *,
    is_next: bool,
) -> str | None:
    blocked_statuses = {"blocked", "returned_for_fix", "failed"}
    if module_status in blocked_statuses or blueprint_status in blocked_statuses:
        return COLOR_RED

    if is_next or module_status == "ready_for_module_pull":
        return COLOR_ORANGE

    if module_status == "in_progress":
        return COLOR_YELLOW

    if blueprint_status == "accepted_by_blueprint":
        return COLOR_BRIGHT_GREEN

    if module_status == "completed_by_module":
        return COLOR_LIGHT_GREEN

    if module_status == "planned" or blueprint_status == "not_started":
        return COLOR_GRAY

    if module_status in {"not_required", "superseded"}:
        return COLOR_CYAN

    return None


def _sorted_draft_prompts(index_path: Path) -> list[Path]:
    drafts_dir = index_path.parent / "drafts"
    if not drafts_dir.exists():
        return []

    return sorted(
        path
        for path in drafts_dir.glob("*.md")
        if path.is_file() and not path.name.startswith(".")
    )


def _draft_id(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}__", "", stem)
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    return stem


def _draft_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title.lower().startswith("prompt:"):
                    title = title[7:].strip()
                return title or path.stem
    except OSError:
        return path.stem

    return path.stem


def _boxed_table(
    *,
    headers: tuple[str, ...],
    widths: tuple[int, ...],
    rows: list[TableRow],
    use_color: bool,
) -> list[str]:
    return render_boxed_table_lines(
        headers=headers,
        widths=widths,
        rows=rows,
        use_color=use_color,
    )


def _finalize_output(lines: list[str], *, use_color: bool) -> str:
    rendered = "\n".join(lines)
    if not use_color:
        return rendered
    return rendered + COLOR_RESET


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

    if args.module == BLUEPRINT_MODULE:
        command = [
            sys.executable,
            str(BLUEPRINT_STATUS_SCRIPT),
            "--module",
            args.module,
            "--view",
            "prompts",
        ]
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
        ).returncode

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
