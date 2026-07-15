#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.coordination.build_document_manifest import DEFAULT_SOURCE_REGISTRY
from scripts.coordination.render_document_awareness_dashboard import (
    DEFAULT_LEDGER,
    AwarenessRecord,
    build_dashboard,
)
from scripts.reporting.document_awareness_tables import (
    render_context_bundle_summary,
)

DEFAULT_OUTPUT_DIR = Path("reports/coordination_context_bundles")

VALID_SCOPES = {
    "bootstrap",
    "required",
    "changed",
    "critical",
    "high",
    "module",
    "full",
}

BOOTSTRAP_SOURCES = {
    "global_policy",
    "standards",
    "instruction_intake",
    "module_policy",
    "outgoing_prompts",
}

ATTENTION_STATUSES = {
    "unseen",
    "changed",
    "in_progress",
    "returned_for_fix",
}


@dataclass(frozen=True)
class BundleResult:
    module: str
    scope: str
    generated_at: str
    document_count: int
    content: str


def _priority_rank(priority: str) -> int:
    order = {
        "critical": 0,
        "high": 1,
        "normal": 2,
        "low": 3,
        "reference": 4,
    }
    return order.get(priority, 999)


def _should_include_record(record: AwarenessRecord, *, scope: str, module: str) -> bool:
    priority = record.document.priority
    source_id = record.document.source_id
    path_parts = Path(record.document.path).parts

    if scope == "full":
        return True

    if scope == "bootstrap":
        return source_id in BOOTSTRAP_SOURCES and priority in {"critical", "high"}

    if scope == "required":
        return priority in {"critical", "high"}

    if scope == "changed":
        return record.awareness_status in ATTENTION_STATUSES

    if scope == "critical":
        return priority == "critical"

    if scope == "high":
        return priority in {"critical", "high"}

    if scope == "module":
        return source_id in {"module_policy", "outgoing_prompts"} or module in path_parts

    raise ValueError(f"unsupported bundle scope `{scope}`")


def select_bundle_records(
    records: list[AwarenessRecord],
    *,
    scope: str,
    module: str,
) -> list[AwarenessRecord]:
    if scope not in VALID_SCOPES:
        raise ValueError(f"unsupported bundle scope `{scope}`")

    selected = [
        record
        for record in records
        if _should_include_record(record, scope=scope, module=module)
    ]

    selected.sort(
        key=lambda record: (
            _priority_rank(record.document.priority),
            record.document.source_id,
            record.document.path,
        )
    )

    return selected


def _safe_output_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)
    return normalized.strip("_") or "bundle"


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_document_content(root: Path, document_path: str) -> str:
    path = root / document_path
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "[Binary or non-UTF-8 file omitted from text bundle.]"


def _render_record_metadata(record: AwarenessRecord) -> list[str]:
    return [
        f"- Document id: `{record.document.document_id}`",
        f"- Source: `{record.document.source_id}`",
        f"- Priority: `{record.document.priority}`",
        f"- Awareness status: `{record.awareness_status}`",
        f"- Applies to: `{record.document.applies_to}`",
        f"- Action: `{record.recommended_action}`",
        f"- Hash: `{record.document.content_hash}`",
        f"- Size: `{record.document.size_bytes}` bytes",
    ]

def _render_selected_records_snapshot(records: list[AwarenessRecord]) -> str:
    if not records:
        return "No documents selected for this bundle scope."

    source_counts: dict[str, int] = {}
    for record in records:
        source_counts[record.document.source_id] = (
            source_counts.get(record.document.source_id, 0) + 1
        )

    lines: list[str] = [
        "Selected source summary:",
        "",
        "| Source | Documents |",
        "|---|---:|",
    ]

    for source_id, count in sorted(source_counts.items()):
        lines.append(f"| `{source_id}` | {count} |")

    lines.extend(
        [
            "",
            "Selected documents:",
            "",
            "| Priority | Status | Source | Path |",
            "|---|---|---|---|",
        ]
    )

    for record in records:
        lines.append(
            "| "
            f"{record.document.priority} | "
            f"{record.awareness_status} | "
            f"`{record.document.source_id}` | "
            f"`{record.document.path}` |"
        )

    return "\n".join(lines)


def build_context_bundle(
    *,
    root: Path,
    module: str,
    scope: str,
    registry_path: Path,
    ledger_path: Path,
    include_reference: bool = False,
    limit: int | None = None,
) -> BundleResult:
    dashboard = build_dashboard(
        root=root,
        module=module,
        registry_path=registry_path,
        ledger_path=ledger_path,
        include_reference=include_reference,
    )

    selected_records = select_bundle_records(
        dashboard.records,
        scope=scope,
        module=module,
    )

    if limit is not None:
        selected_records = selected_records[:limit]

    generated_at = datetime.now(UTC).isoformat()

    lines: list[str] = [
        f"# Coordination Context Bundle — {module}",
        "",
        f"- Module: `{module}`",
        f"- Scope: `{scope}`",
        f"- Generated at: `{generated_at}`",
        f"- Source registry: `{_relative_to_root(root, registry_path)}`",
        f"- Ledger: `{_relative_to_root(root, ledger_path)}`",
        f"- Ledger loaded: `{'yes' if ledger_path.exists() else 'no'}`",
        f"- Documents included: `{len(selected_records)}`",
        "",
        "## Selected Document Snapshot",
        "",
        _render_selected_records_snapshot(selected_records),
        "",
        "## Included Documents",
        "",
        ]

    if not selected_records:
        lines.append("No documents matched this bundle scope.")
        lines.append("")
    else:
        for index, record in enumerate(selected_records, start=1):
            lines.extend(
                [
                    f"### {index}. {record.document.path}",
                    "",
                    *_render_record_metadata(record),
                    "",
                    f"--- BEGIN FILE: {record.document.path} ---",
                    "",
                    _read_document_content(root, record.document.path).rstrip(),
                    "",
                    f"--- END FILE: {record.document.path} ---",
                    "",
                ]
            )

    lines.extend(
        [
            "## Operator Note",
            "",
            "This bundle is a delivery artifact for assistant context.",
            "The Blueprint repository remains the source of truth for document content.",
            "The module ledger remains the source of truth for module review status.",
            "",
        ]
    )

    return BundleResult(
        module=module,
        scope=scope,
        generated_at=generated_at,
        document_count=len(selected_records),
        content="\n".join(lines),
    )


def write_context_bundle(
    *,
    root: Path,
    bundle: BundleResult,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = (
        f"{_safe_output_name(bundle.module)}__"
        f"{_safe_output_name(bundle.scope)}__"
        f"{timestamp}.md"
    )

    output_path = output_dir / filename
    output_path.write_text(bundle.content, encoding="utf-8")

    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a Markdown coordination context bundle for a module."
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
        "--scope",
        default="bootstrap",
        choices=sorted(VALID_SCOPES),
        help="Bundle scope.",
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
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for generated context bundles.",
    )
    parser.add_argument(
        "--include-reference",
        action="store_true",
        help="Include reference-only documents.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of documents to include.",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print bundle to stdout instead of writing a file.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Build bundle and print summary without writing a file.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output for the terminal summary.",
    )

    args = parser.parse_args()
    no_color = args.no_color or os.environ.get("NO_COLOR") == "1"
    root = Path(args.root).resolve()

    registry_path = Path(args.registry)
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    ledger_path = Path(args.ledger)
    if not ledger_path.is_absolute():
        ledger_path = root / ledger_path

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    try:
        bundle = build_context_bundle(
            root=root,
            module=args.module,
            scope=args.scope,
            registry_path=registry_path,
            ledger_path=ledger_path,
            include_reference=args.include_reference,
            limit=args.limit,
        )
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    if args.print:
        print(bundle.content)
        return 0

    if args.no_write:
        print(
            render_context_bundle_summary(
                module=bundle.module,
                scope=bundle.scope,
                document_count=bundle.document_count,
                write_mode="disabled",
                output_path=None,
                use_color=not no_color,
            )
        )
        return 0

    output_path = write_context_bundle(
        root=root,
        bundle=bundle,
        output_dir=output_dir,
    )

    print(
        render_context_bundle_summary(
            module=bundle.module,
            scope=bundle.scope,
            document_count=bundle.document_count,
            write_mode="enabled",
            output_path=_relative_to_root(root, output_path),
            use_color=not no_color,
        )
    )
    return 0


if __name__ == "__main__":
    no_color = os.environ.get("NO_COLOR") == "1"
    sys.exit(main())
