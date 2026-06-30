#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.build_document_manifest import (
    DEFAULT_SOURCE_REGISTRY,
    DocumentRecord,
    build_manifest,
)

DEFAULT_LEDGER = Path("coordination/blueprint_awareness/document_review_ledger.yaml")

PRIORITY_ORDER = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
    "reference": 4,
}

ATTENTION_STATUSES = {
    "unseen",
    "changed",
    "in_progress",
    "returned_for_fix",
}


@dataclass(frozen=True)
class LedgerEntry:
    path: str
    content_hash: str
    module_review_status: str
    notes: str | None


@dataclass(frozen=True)
class AwarenessRecord:
    document: DocumentRecord
    awareness_status: str
    ledger_hash: str | None
    notes: str | None
    recommended_action: str


@dataclass(frozen=True)
class SourceSummary:
    source_id: str
    total: int
    unseen: int
    changed: int
    acknowledged: int
    in_progress: int
    applied: int
    deferred: int
    highest_priority: str
    recommended_action: str


@dataclass(frozen=True)
class DashboardResult:
    module: str
    ledger_path: str
    ledger_loaded: bool
    document_count: int
    warning_count: int
    warnings: list[str]
    records: list[AwarenessRecord]
    summaries: list[SourceSummary]


class Palette:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled

    def paint(self, value: str, color: str) -> str:
        if not self.enabled:
            return value

        colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "green": "\033[32m",
            "light_green": "\033[92m",
            "yellow": "\033[33m",
            "red": "\033[31m",
            "cyan": "\033[36m",
            "gray": "\033[90m",
        }
        return f"{colors[color]}{value}{colors['reset']}"


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def load_ledger(path: Path) -> dict[str, LedgerEntry]:
    if not path.exists():
        return {}

    data = _load_yaml(path)
    reviewed_documents = data.get("reviewed_documents", [])
    if not isinstance(reviewed_documents, list):
        raise ValueError("ledger field `reviewed_documents` must be a list")

    entries: dict[str, LedgerEntry] = {}

    for index, item in enumerate(reviewed_documents):
        if not isinstance(item, dict):
            raise ValueError(f"ledger item {index} must be a mapping")

        document_path = item.get("path")
        content_hash = item.get("content_hash")
        status = item.get("module_review_status")
        notes = item.get("notes")

        if not isinstance(document_path, str) or not document_path.strip():
            raise ValueError(f"ledger item {index} has invalid `path`")
        if not isinstance(content_hash, str) or not content_hash.strip():
            raise ValueError(f"ledger item {index} has invalid `content_hash`")
        if not isinstance(status, str) or not status.strip():
            raise ValueError(
                f"ledger item {index} has invalid `module_review_status`"
            )
        if notes is not None and not isinstance(notes, str):
            raise ValueError(f"ledger item {index} has invalid `notes`")

        entries[document_path] = LedgerEntry(
            path=document_path,
            content_hash=content_hash,
            module_review_status=status,
            notes=notes,
        )

    return entries


def _is_applicable_to_module(
    document: DocumentRecord,
    *,
    module: str,
    include_reference: bool,
) -> bool:
    if document.applies_to == "all":
        return True

    if document.applies_to == "module_specific":
        return module in Path(document.path).parts

    if document.applies_to == "filtered":
        return module in Path(document.path).parts

    if document.applies_to == "reference":
        return include_reference

    return False


def _priority_rank(priority: str) -> int:
    return PRIORITY_ORDER.get(priority, 999)


def _awareness_status(document: DocumentRecord, ledger: dict[str, LedgerEntry]) -> tuple[str, str | None, str | None]:
    entry = ledger.get(document.path)

    if entry is None:
        return "unseen", None, None

    if entry.content_hash != document.content_hash:
        return "changed", entry.content_hash, entry.notes

    return entry.module_review_status, entry.content_hash, entry.notes


def _recommended_action(document: DocumentRecord, status: str) -> str:
    if status == "changed":
        return "review_changed_document_hash"
    if status == "unseen":
        return document.action
    if status == "in_progress":
        return "continue_alignment"
    if status == "returned_for_fix":
        return "requires_blueprint_clarification"
    return "no_immediate_action"


def build_dashboard(
    *,
    root: Path,
    module: str,
    registry_path: Path,
    ledger_path: Path,
    include_reference: bool = False,
) -> DashboardResult:
    manifest = build_manifest(root, registry_path)
    ledger = load_ledger(ledger_path)

    records: list[AwarenessRecord] = []

    for document in manifest.documents:
        if not _is_applicable_to_module(
            document,
            module=module,
            include_reference=include_reference,
        ):
            continue

        status, ledger_hash, notes = _awareness_status(document, ledger)

        records.append(
            AwarenessRecord(
                document=document,
                awareness_status=status,
                ledger_hash=ledger_hash,
                notes=notes,
                recommended_action=_recommended_action(document, status),
            )
        )

    records.sort(
        key=lambda item: (
            _priority_rank(item.document.priority),
            item.awareness_status not in ATTENTION_STATUSES,
            item.document.source_id,
            item.document.path,
        )
    )

    summaries = _build_summaries(records)

    return DashboardResult(
        module=module,
        ledger_path=_relative_to_root(root, ledger_path),
        ledger_loaded=ledger_path.exists(),
        document_count=len(records),
        warning_count=manifest.warning_count,
        warnings=manifest.warnings,
        records=records,
        summaries=summaries,
    )


def _build_summaries(records: list[AwarenessRecord]) -> list[SourceSummary]:
    grouped: dict[str, list[AwarenessRecord]] = {}

    for record in records:
        grouped.setdefault(record.document.source_id, []).append(record)

    summaries: list[SourceSummary] = []

    for source_id, source_records in grouped.items():
        priorities = {record.document.priority for record in source_records}
        highest_priority = sorted(priorities, key=_priority_rank)[0]

        attention_records = [
            record
            for record in source_records
            if record.awareness_status in ATTENTION_STATUSES
        ]
        recommended_action = (
            "review_attention_documents"
            if attention_records
            else "no_immediate_action"
        )

        summaries.append(
            SourceSummary(
                source_id=source_id,
                total=len(source_records),
                unseen=sum(
                    1 for record in source_records if record.awareness_status == "unseen"
                ),
                changed=sum(
                    1 for record in source_records if record.awareness_status == "changed"
                ),
                acknowledged=sum(
                    1
                    for record in source_records
                    if record.awareness_status == "acknowledged"
                ),
                in_progress=sum(
                    1
                    for record in source_records
                    if record.awareness_status == "in_progress"
                ),
                applied=sum(
                    1 for record in source_records if record.awareness_status == "applied"
                ),
                deferred=sum(
                    1 for record in source_records if record.awareness_status == "deferred"
                ),
                highest_priority=highest_priority,
                recommended_action=recommended_action,
            )
        )

    summaries.sort(key=lambda item: (_priority_rank(item.highest_priority), item.source_id))
    return summaries


def _render_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [len(header) for header in headers]

    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(_strip_ansi(cell)))

    def format_row(row: list[str]) -> str:
        cells: list[str] = []
        for index, cell in enumerate(row):
            visible_len = len(_strip_ansi(cell))
            padding = widths[index] - visible_len
            cells.append(f"{cell}{' ' * padding}")
        return "| " + " | ".join(cells) + " |"

    separator = "| " + " | ".join("-" * width for width in widths) + " |"

    return [format_row(headers), separator, *[format_row(row) for row in rows]]


def _strip_ansi(value: str) -> str:
    result = ""
    index = 0

    while index < len(value):
        if value[index] == "\033":
            while index < len(value) and value[index] != "m":
                index += 1
            index += 1
            continue
        result += value[index]
        index += 1

    return result


def _paint_priority(priority: str, palette: Palette) -> str:
    if priority == "critical":
        return palette.paint(priority, "red")
    if priority == "high":
        return palette.paint(priority, "yellow")
    if priority == "normal":
        return priority
    if priority == "reference":
        return palette.paint(priority, "cyan")
    return palette.paint(priority, "gray")


def _paint_status(status: str, priority: str, palette: Palette) -> str:
    if status == "applied":
        return palette.paint(status, "green")
    if status == "acknowledged":
        return palette.paint(status, "light_green")
    if status == "in_progress":
        return palette.paint(status, "yellow")
    if status == "changed" and priority == "critical":
        return palette.paint(status, "red")
    if status in {"changed", "unseen"}:
        return palette.paint(status, "yellow")
    if status in {"deferred", "not_applicable", "superseded"}:
        return palette.paint(status, "cyan")
    if status == "returned_for_fix":
        return palette.paint(status, "red")
    return palette.paint(status, "gray")


def render_dashboard(
    result: DashboardResult,
    *,
    no_color: bool,
    show_all: bool,
    limit: int,
) -> str:
    palette = Palette(enabled=not no_color)

    lines: list[str] = [
        palette.paint(f"Coordination Document Awareness — {result.module}", "bold"),
        "",
        f"Documents considered: {result.document_count}",
        f"Ledger: {result.ledger_path}",
        f"Ledger loaded: {'yes' if result.ledger_loaded else 'no'}",
        f"Warnings: {result.warning_count}",
        "",
    ]

    if result.warnings:
        lines.append("Warnings")
        lines.append("")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("Area Summary")
    lines.append("")

    summary_rows = [
        [
            summary.source_id,
            str(summary.total),
            str(summary.unseen),
            str(summary.changed),
            str(summary.in_progress),
            str(summary.acknowledged),
            str(summary.applied),
            str(summary.deferred),
            _paint_priority(summary.highest_priority, palette),
            summary.recommended_action,
        ]
        for summary in result.summaries
    ]

    lines.extend(
        _render_table(
            [
                "Source",
                "Total",
                "Unseen",
                "Changed",
                "In progress",
                "Ack",
                "Applied",
                "Deferred",
                "Priority",
                "Action",
            ],
            summary_rows,
        )
    )
    lines.append("")

    attention_records = [
        record
        for record in result.records
        if show_all or record.awareness_status in ATTENTION_STATUSES
    ]

    lines.append("Attention Required" if not show_all else "Documents")
    lines.append("")

    if not attention_records:
        lines.append("No attention-required documents.")
        lines.append("")
        return "\n".join(lines)

    displayed_records = attention_records[:limit]

    detail_rows = [
        [
            _paint_priority(record.document.priority, palette),
            _paint_status(
                record.awareness_status,
                record.document.priority,
                palette,
            ),
            record.document.source_id,
            record.document.path,
            record.recommended_action,
        ]
        for record in displayed_records
    ]

    lines.extend(
        _render_table(
            ["Priority", "Status", "Source", "Path", "Action"],
            detail_rows,
        )
    )

    hidden_count = len(attention_records) - len(displayed_records)
    if hidden_count > 0:
        lines.append("")
        lines.append(f"... {hidden_count} more documents hidden by --limit={limit}")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render ForPrint Blueprint coordination document awareness dashboard."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Blueprint repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module id used to filter module-specific coordination documents.",
    )
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_SOURCE_REGISTRY),
        help="Source registry path, relative to root unless absolute.",
    )
    parser.add_argument(
        "--ledger",
        default=str(DEFAULT_LEDGER),
        help="Module awareness ledger path, relative to root unless absolute.",
    )
    parser.add_argument(
        "--include-reference",
        action="store_true",
        help="Include reference-only documents in the dashboard.",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all applicable documents instead of only attention items.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Maximum number of detail rows to print.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output.",
    )

    args = parser.parse_args()
    root = Path(args.root).resolve()

    registry_path = Path(args.registry)
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    ledger_path = Path(args.ledger)
    if not ledger_path.is_absolute():
        ledger_path = root / ledger_path

    try:
        result = build_dashboard(
            root=root,
            module=args.module,
            registry_path=registry_path,
            ledger_path=ledger_path,
            include_reference=args.include_reference,
        )
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    no_color = args.no_color or os.environ.get("NO_COLOR") == "1"

    print(
        render_dashboard(
            result,
            no_color=no_color,
            show_all=args.show_all,
            limit=args.limit,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
