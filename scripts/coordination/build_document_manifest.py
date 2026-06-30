#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

SOURCE_REGISTRY_SCHEMA_VERSION = "coordination_document_source_registry_v0_1"
DOCUMENT_MANIFEST_SCHEMA_VERSION = "coordination_document_manifest_v0_1"

DEFAULT_SOURCE_REGISTRY = Path("coordination/document_awareness/source_registry.yaml")
DEFAULT_OUTPUT_DIR = Path("reports/coordination_awareness")


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    path: Path
    priority: str
    applies_to: str
    action: str
    include_patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...]


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    source_id: str
    path: str
    source_relative_path: str
    title: str
    priority: str
    applies_to: str
    action: str
    content_hash: str
    size_bytes: int
    file_extension: str


@dataclass(frozen=True)
class ManifestResult:
    schema_version: str
    generated_at: str
    source_registry: str
    document_count: int
    warning_count: int
    warnings: list[str]
    documents: list[DocumentRecord]


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _as_string_list(value: Any, *, field_name: str, source_id: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"source `{source_id}` field `{field_name}` must be a list")

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"source `{source_id}` field `{field_name}` has invalid list item"
            )
        result.append(item)

    return tuple(result)


def load_source_registry(root: Path, registry_path: Path) -> list[SourceDefinition]:
    data = _load_yaml(registry_path)

    schema_version = data.get("schema_version")
    if schema_version != SOURCE_REGISTRY_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported source registry schema_version `{schema_version}`"
        )

    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source registry field `sources` must be a list")

    definitions: list[SourceDefinition] = []

    for index, item in enumerate(sources):
        if not isinstance(item, dict):
            raise ValueError(f"source registry item {index} must be a mapping")

        source_id = item.get("source_id")
        path = item.get("path")
        priority = item.get("priority")
        applies_to = item.get("applies_to")
        action = item.get("action")

        for field_name, value in (
            ("source_id", source_id),
            ("path", path),
            ("priority", priority),
            ("applies_to", applies_to),
            ("action", action),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"source registry item {index} has invalid `{field_name}`"
                )

        include_patterns = _as_string_list(
            item.get("include_patterns"),
            field_name="include_patterns",
            source_id=source_id,
        )
        exclude_patterns = _as_string_list(
            item.get("exclude_patterns"),
            field_name="exclude_patterns",
            source_id=source_id,
        )

        definitions.append(
            SourceDefinition(
                source_id=source_id,
                path=(root / path).resolve(),
                priority=priority,
                applies_to=applies_to,
                action=action,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )
        )

    return definitions


def _matches_pattern(path: Path, pattern: str) -> bool:
    normalized = path.as_posix()
    return fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(normalized, pattern)


def _should_include_file(
    *,
    relative_to_source: Path,
    include_patterns: tuple[str, ...],
    exclude_patterns: tuple[str, ...],
) -> bool:
    if any(_matches_pattern(relative_to_source, pattern) for pattern in exclude_patterns):
        return False

    return any(_matches_pattern(relative_to_source, pattern) for pattern in include_patterns)


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _slug(value: str) -> str:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered)
    return normalized.strip("_") or "document"


def _document_id(source_id: str, relative_to_source: Path) -> str:
    parts = list(relative_to_source.with_suffix("").parts)
    slugged = [_slug(part) for part in parts]
    return ".".join([source_id, *slugged])


def _title_from_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.stem.replace("_", " ").replace("-", " ").title()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.removeprefix("# ").strip()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("title:"):
            return stripped.split(":", 1)[1].strip().strip('"').strip("'")

    return path.stem.replace("_", " ").replace("-", " ").title()


def _relative_to_root(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_documents(root: Path, sources: list[SourceDefinition]) -> tuple[list[DocumentRecord], list[str]]:
    documents: list[DocumentRecord] = []
    warnings: list[str] = []

    for source in sources:
        if not source.path.exists():
            warnings.append(f"source path does not exist: {_relative_to_root(root, source.path)}")
            continue

        if not source.path.is_dir():
            warnings.append(f"source path is not a directory: {_relative_to_root(root, source.path)}")
            continue

        for path in sorted(source.path.rglob("*")):
            if not path.is_file():
                continue

            relative_to_source = path.relative_to(source.path)

            if not _should_include_file(
                relative_to_source=relative_to_source,
                include_patterns=source.include_patterns,
                exclude_patterns=source.exclude_patterns,
            ):
                continue

            documents.append(
                DocumentRecord(
                    document_id=_document_id(source.source_id, relative_to_source),
                    source_id=source.source_id,
                    path=_relative_to_root(root, path),
                    source_relative_path=relative_to_source.as_posix(),
                    title=_title_from_text(path),
                    priority=source.priority,
                    applies_to=source.applies_to,
                    action=source.action,
                    content_hash=_content_hash(path),
                    size_bytes=path.stat().st_size,
                    file_extension=path.suffix,
                )
            )

    documents.sort(key=lambda item: (item.priority, item.path))
    return documents, warnings


def build_manifest(root: Path, registry_path: Path) -> ManifestResult:
    sources = load_source_registry(root, registry_path)
    documents, warnings = scan_documents(root, sources)

    return ManifestResult(
        schema_version=DOCUMENT_MANIFEST_SCHEMA_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        source_registry=_relative_to_root(root, registry_path),
        document_count=len(documents),
        warning_count=len(warnings),
        warnings=warnings,
        documents=documents,
    )


def manifest_to_dict(manifest: ManifestResult) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "generated_at": manifest.generated_at,
        "source_registry": manifest.source_registry,
        "document_count": manifest.document_count,
        "warning_count": manifest.warning_count,
        "warnings": manifest.warnings,
        "documents": [asdict(document) for document in manifest.documents],
    }


def render_markdown(manifest: ManifestResult) -> str:
    lines: list[str] = [
        "# Coordination Document Manifest",
        "",
        f"- Schema version: `{manifest.schema_version}`",
        f"- Generated at: `{manifest.generated_at}`",
        f"- Source registry: `{manifest.source_registry}`",
        f"- Document count: `{manifest.document_count}`",
        f"- Warning count: `{manifest.warning_count}`",
        "",
    ]

    if manifest.warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in manifest.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    summary: dict[str, int] = {}
    for document in manifest.documents:
        summary[document.source_id] = summary.get(document.source_id, 0) + 1

    lines.append("## Source Summary")
    lines.append("")
    lines.append("| Source | Documents |")
    lines.append("|---|---:|")
    for source_id, count in sorted(summary.items()):
        lines.append(f"| `{source_id}` | {count} |")
    lines.append("")

    lines.append("## Documents")
    lines.append("")
    lines.append("| Priority | Source | Path | Hash |")
    lines.append("|---|---|---|---|")

    for document in manifest.documents:
        lines.append(
            "| "
            f"{document.priority} | "
            f"`{document.source_id}` | "
            f"`{document.path}` | "
            f"`{document.content_hash}` |"
        )

    lines.append("")
    return "\n".join(lines)


def write_manifest_reports(manifest: ManifestResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "document_manifest.json"
    markdown_path = output_dir / "document_manifest.md"

    json_path.write_text(
        json.dumps(manifest_to_dict(manifest), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(manifest), encoding="utf-8")

    return json_path, markdown_path


def print_summary(manifest: ManifestResult) -> None:
    print("ForPrint Coordination Document Manifest")
    print(f"Schema: {manifest.schema_version}")
    print(f"Source registry: {manifest.source_registry}")
    print(f"Documents: {manifest.document_count}")
    print(f"Warnings: {manifest.warning_count}")

    if manifest.warnings:
        print("")
        print("Warnings:")
        for warning in manifest.warnings:
            print(f"- {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build ForPrint Blueprint coordination document manifest."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Blueprint repository root. Defaults to current directory.",
    )
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_SOURCE_REGISTRY),
        help="Path to source registry, relative to root unless absolute.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory for generated manifest reports.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Build and print summary without writing generated reports.",
    )

    args = parser.parse_args()
    root = Path(args.root).resolve()

    registry_path = Path(args.registry)
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    try:
        manifest = build_manifest(root, registry_path)
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print_summary(manifest)

    if args.no_write:
        print("Write mode: disabled")
        return 0

    json_path, markdown_path = write_manifest_reports(manifest, output_dir)
    print("")
    print(f"JSON report: {_relative_to_root(root, json_path)}")
    print(f"Markdown report: {_relative_to_root(root, markdown_path)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
