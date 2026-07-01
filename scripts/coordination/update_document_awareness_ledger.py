#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.coordination.build_document_manifest import (
    DEFAULT_SOURCE_REGISTRY,
    DocumentRecord,
    build_manifest,
)

LEDGER_SCHEMA_VERSION = "module_document_awareness_ledger_v0_1"
DEFAULT_LEDGER = Path("coordination/blueprint_awareness/document_review_ledger.yaml")

ALLOWED_STATUSES = {
    "acknowledged",
    "applied",
    "deferred",
    "in_progress",
    "returned_for_fix",
}


@dataclass(frozen=True)
class LedgerUpdateResult:
    module: str
    ledger_path: Path
    selected_count: int
    write_enabled: bool
    selected_documents: list[DocumentRecord]


def _resolve_root_relative(root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def _resolve_cwd_relative(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    return (Path.cwd() / path).resolve()


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")

    return data


def _load_ledger(path: Path, *, module: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": LEDGER_SCHEMA_VERSION,
            "module": module,
            "reviewed_documents": [],
        }

    data = _load_yaml_mapping(path)

    schema_version = data.get("schema_version")
    if schema_version != LEDGER_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported ledger schema_version `{schema_version}` in {path}"
        )

    ledger_module = data.get("module")
    if ledger_module != module:
        raise ValueError(
            f"ledger module `{ledger_module}` does not match requested module `{module}`"
        )

    reviewed_documents = data.get("reviewed_documents")
    if not isinstance(reviewed_documents, list):
        raise ValueError("ledger field `reviewed_documents` must be a list")

    return data


def _ledger_items_by_path(ledger_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items_by_path: dict[str, dict[str, Any]] = {}

    reviewed_documents = ledger_data.get("reviewed_documents", [])
    if not isinstance(reviewed_documents, list):
        raise ValueError("ledger field `reviewed_documents` must be a list")

    for index, item in enumerate(reviewed_documents):
        if not isinstance(item, dict):
            raise ValueError(f"ledger item {index} must be a mapping")

        document_path = item.get("path")
        if not isinstance(document_path, str) or not document_path.strip():
            raise ValueError(f"ledger item {index} has invalid `path`")

        if document_path in items_by_path:
            raise ValueError(f"duplicate ledger path: {document_path}")

        items_by_path[document_path] = dict(item)

    return items_by_path


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


def _matches_document_selector(document: DocumentRecord, selector: str) -> bool:
    return selector in {
        document.document_id,
        document.path,
        document.source_relative_path,
        Path(document.path).name,
    }


def _select_documents(
    documents: list[DocumentRecord],
    *,
    module: str,
    include_reference: bool,
    document_selectors: list[str],
    source_selectors: list[str],
    priority_selectors: list[str],
    all_applicable: bool,
) -> list[DocumentRecord]:
    applicable = [
        document
        for document in documents
        if _is_applicable_to_module(
            document,
            module=module,
            include_reference=include_reference,
        )
    ]

    if not any(
        (
            all_applicable,
            document_selectors,
            source_selectors,
            priority_selectors,
        )
    ):
        raise ValueError(
            "provide at least one selector: --document, --source, --priority "
            "or --all-applicable"
        )

    selected: list[DocumentRecord] = []

    if all_applicable:
        selected.extend(applicable)

    missing_document_selectors: list[str] = []
    for selector in document_selectors:
        matches = [
            document
            for document in applicable
            if _matches_document_selector(document, selector)
        ]

        if not matches:
            missing_document_selectors.append(selector)
            continue

        selected.extend(matches)

    if missing_document_selectors:
        missing = ", ".join(sorted(missing_document_selectors))
        raise ValueError(f"document selector did not match any document: {missing}")

    if source_selectors:
        selected.extend(
            document
            for document in applicable
            if document.source_id in set(source_selectors)
        )

    if priority_selectors:
        selected.extend(
            document
            for document in applicable
            if document.priority in set(priority_selectors)
        )

    unique_by_path = {document.path: document for document in selected}

    return sorted(
        unique_by_path.values(),
        key=lambda document: (document.priority, document.source_id, document.path),
    )


def update_ledger(
    *,
    root: Path,
    registry_path: Path,
    ledger_path: Path,
    module: str,
    status: str,
    document_selectors: list[str],
    source_selectors: list[str],
    priority_selectors: list[str],
    all_applicable: bool,
    include_reference: bool,
    reviewed_at: str | None,
    module_commit: str | None,
    notes: str | None,
    write: bool,
) -> LedgerUpdateResult:
    if status not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise ValueError(f"unsupported status `{status}`; allowed: {allowed}")

    manifest = build_manifest(root, registry_path)
    selected_documents = _select_documents(
        manifest.documents,
        module=module,
        include_reference=include_reference,
        document_selectors=document_selectors,
        source_selectors=source_selectors,
        priority_selectors=priority_selectors,
        all_applicable=all_applicable,
    )

    ledger_data = _load_ledger(ledger_path, module=module)
    items_by_path = _ledger_items_by_path(ledger_data)

    timestamp = reviewed_at or datetime.now(UTC).isoformat(timespec="seconds")

    for document in selected_documents:
        item = dict(items_by_path.get(document.path, {}))
        item["document_id"] = document.document_id
        item["path"] = document.path
        item["content_hash"] = document.content_hash
        item["module_review_status"] = status
        item["reviewed_at"] = timestamp
        item["module_commit"] = module_commit
        item["notes"] = notes

        items_by_path[document.path] = item

    updated_ledger = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "module": module,
        "reviewed_documents": [
            items_by_path[path] for path in sorted(items_by_path)
        ],
    }

    if write:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            yaml.safe_dump(
                updated_ledger,
                allow_unicode=True,
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    return LedgerUpdateResult(
        module=module,
        ledger_path=ledger_path,
        selected_count=len(selected_documents),
        write_enabled=write,
        selected_documents=selected_documents,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update a module-local coordination document awareness ledger."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Blueprint repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_SOURCE_REGISTRY,
        help="Source registry path, relative to root unless absolute.",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help="Module-local ledger path. Relative paths are resolved from cwd.",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Module id used to filter module-specific coordination documents.",
    )
    parser.add_argument(
        "--status",
        choices=sorted(ALLOWED_STATUSES),
        default="acknowledged",
        help="Status to write for selected documents.",
    )
    parser.add_argument(
        "--document",
        action="append",
        default=[],
        help="Document selector: document_id, path, source-relative path or filename.",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Select applicable documents by source_id.",
    )
    parser.add_argument(
        "--priority",
        action="append",
        default=[],
        help="Select applicable documents by priority.",
    )
    parser.add_argument(
        "--all-applicable",
        action="store_true",
        help="Select all documents applicable to the module.",
    )
    parser.add_argument(
        "--include-reference",
        action="store_true",
        help="Include reference-only documents in the selection.",
    )
    parser.add_argument(
        "--reviewed-at",
        help="Explicit review timestamp. Defaults to current UTC time.",
    )
    parser.add_argument(
        "--module-commit",
        help="Module commit associated with this review/update.",
    )
    parser.add_argument(
        "--notes",
        help="Notes to store on selected ledger entries.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Preview the update without writing the ledger file.",
    )
    return parser


def print_result(result: LedgerUpdateResult) -> None:
    print("ForPrint Document Awareness Ledger Update")
    print(f"Module: {result.module}")
    print(f"Ledger: {result.ledger_path}")
    print(f"Selected documents: {result.selected_count}")
    print(f"Write mode: {'enabled' if result.write_enabled else 'disabled'}")

    for document in result.selected_documents:
        print(f"- {document.document_id} :: {document.path}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    root = args.root.resolve()
    registry_path = _resolve_root_relative(root, args.registry)
    ledger_path = _resolve_cwd_relative(args.ledger)

    try:
        result = update_ledger(
            root=root,
            registry_path=registry_path,
            ledger_path=ledger_path,
            module=args.module,
            status=args.status,
            document_selectors=args.document,
            source_selectors=args.source,
            priority_selectors=args.priority,
            all_applicable=args.all_applicable,
            include_reference=args.include_reference,
            reviewed_at=args.reviewed_at,
            module_commit=args.module_commit,
            notes=args.notes,
            write=not args.no_write,
        )
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 1

    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
