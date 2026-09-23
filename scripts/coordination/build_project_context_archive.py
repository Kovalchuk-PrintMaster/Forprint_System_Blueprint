from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import yaml

INDEX_PATH = Path("coordination/bootstrap/index_v0_1.yaml")
SCHEMA = "forprint_project_context_archive_manifest_v0_1"


class ProjectContextError(ValueError):
    pass


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode:
        raise ProjectContextError(f"git {' '.join(args)} failed: {result.stdout.strip()}")
    return result.stdout.strip()


def _inside_root(root: Path, path: Path) -> bool:
    root = root.resolve()
    path = path.resolve()
    return path == root or root in path.parents


def _is_forbidden(path: Path, fragments: list[str]) -> bool:
    low = path.name.lower()
    return any(fragment.lower() in low for fragment in fragments)


def _tracked(root: Path, path: Path) -> bool:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            path.relative_to(root).as_posix(),
        ],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def load_index(root: Path) -> dict[str, Any]:
    path = root / INDEX_PATH
    if not path.is_file():
        raise ProjectContextError(f"bootstrap index missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ProjectContextError("bootstrap index must be a YAML mapping")
    if data.get("schema_version") != "forprint_project_context_bootstrap_index_v0_1":
        raise ProjectContextError("bootstrap index schema mismatch")
    return data


def _directory_files(
    directory: Path,
    *,
    recursive: bool,
    extensions: set[str],
) -> list[Path]:
    iterator = directory.rglob("*") if recursive else directory.iterdir()
    return sorted(path for path in iterator if path.is_file() and path.suffix.lower() in extensions)


def select_sources(
    *,
    root: Path,
    index: dict[str, Any],
    topics: list[str],
    module: str | None,
) -> tuple[list[Path], list[dict[str, Any]]]:
    root = root.resolve()
    topic_map = index.get("topics")
    if not isinstance(topic_map, dict):
        raise ProjectContextError("topics mapping missing")

    selected: dict[str, Path] = {}
    missing: list[dict[str, Any]] = []
    fragments = list(index.get("safety", {}).get("forbidden_name_fragments", []))

    def add(path: Path) -> None:
        resolved = path.resolve()
        if not _inside_root(root, resolved):
            raise ProjectContextError(f"source escapes repository root: {path}")
        if _is_forbidden(resolved, fragments):
            raise ProjectContextError(f"forbidden source selected: {path}")
        selected[resolved.relative_to(root).as_posix()] = resolved

    for topic in topics:
        spec = topic_map.get(topic)
        if not isinstance(spec, dict):
            raise ProjectContextError(f"unknown project-context topic: {topic}")
        sources = spec.get("sources")
        if not isinstance(sources, list):
            raise ProjectContextError(f"topic {topic} has no sources")
        for row in sources:
            if not isinstance(row, dict):
                raise ProjectContextError(f"invalid source row in topic {topic}")
            rel = row.get("path")
            mode = row.get("mode")
            required = row.get("required") is True
            if not isinstance(rel, str):
                raise ProjectContextError(f"source path missing in topic {topic}")
            path = root / rel
            if mode == "file":
                if path.is_file():
                    add(path)
                else:
                    missing.append({"topic": topic, "path": rel, "required": required})
            elif mode == "directory_files":
                if not path.is_dir():
                    missing.append({"topic": topic, "path": rel, "required": required})
                    continue
                extensions = {str(value).lower() for value in row.get("extensions", [])}
                files = _directory_files(
                    path,
                    recursive=row.get("recursive") is True,
                    extensions=extensions,
                )
                if required and not files:
                    missing.append(
                        {
                            "topic": topic,
                            "path": rel,
                            "required": True,
                            "reason": "empty_directory_selection",
                        }
                    )
                for item in files:
                    add(item)
            else:
                raise ProjectContextError(f"unsupported source mode {mode!r} in topic {topic}")

    if module:
        module_spec = index.get("module_detail", {})
        detail_root = root / str(module_spec.get("directory_root", ""))
        module_dir = detail_root / module
        if module_dir.is_dir():
            extensions = {str(value).lower() for value in module_spec.get("extensions", [])}
            for item in _directory_files(
                module_dir,
                recursive=module_spec.get("recursive") is True,
                extensions=extensions,
            ):
                add(item)

    return [selected[key] for key in sorted(selected)], missing


def source_rows(root: Path, sources: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in sources:
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": _sha(path),
                "bytes": path.stat().st_size,
                "git_tracked": _tracked(root, path),
            }
        )
    return rows


def source_fingerprint(
    *,
    head: str,
    branch: str,
    topics: list[str],
    module: str | None,
    rows: list[dict[str, Any]],
) -> str:
    payload = json.dumps(
        {
            "head": head,
            "branch": branch,
            "topics": topics,
            "module": module,
            "sources": [{"path": row["path"], "sha256": row["sha256"]} for row in rows],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest(
    *,
    root: Path,
    index: dict[str, Any],
    topics: list[str],
    module: str | None,
    sources: list[Path],
    missing: list[dict[str, Any]],
) -> dict[str, Any]:
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "branch", "--show-current")
    rows = source_rows(root, sources)
    required_missing = [row for row in missing if row.get("required") is True]
    fingerprint = source_fingerprint(
        head=head,
        branch=branch,
        topics=topics,
        module=module,
        rows=rows,
    )
    return {
        "schema_version": SCHEMA,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "blueprint_head": head,
        "blueprint_branch": branch,
        "module_detail": module,
        "topics": topics,
        "source_state_fingerprint": fingerprint,
        "selected_source_count": len(rows),
        "sources": rows,
        "missing_sources": missing,
        "required_missing_count": len(required_missing),
        "task_context": index["task_context"],
        "authority_note": (
            "This project-entry archive is navigation/context evidence. "
            "Current Git/release/task authority remains canonical."
        ),
    }


def _zip_write_bytes(
    archive: zipfile.ZipFile,
    name: str,
    data: bytes,
) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def build_archive(
    *,
    root: Path,
    output_dir: Path,
    manifest: dict[str, Any],
    sources: list[Path],
    reading_order: list[str],
) -> Path:
    if manifest["required_missing_count"]:
        raise ProjectContextError(
            "required project-context sources are missing: "
            + json.dumps(
                [row for row in manifest["missing_sources"] if row.get("required") is True],
                ensure_ascii=False,
            )
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    short_head = manifest["blueprint_head"][:12]
    short_fp = manifest["source_state_fingerprint"][:16]
    module_token = manifest["module_detail"] or "portfolio"
    archive_path = (
        output_dir / f"forprint_project_context__{module_token}__{short_head}__{short_fp}.zip"
    )

    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        _zip_write_bytes(
            archive,
            "PROJECT_CONTEXT_MANIFEST.json",
            (
                json.dumps(
                    manifest,
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            ).encode("utf-8"),
        )
        _zip_write_bytes(
            archive,
            "READING_ORDER.txt",
            ("\n".join(reading_order) + "\n").encode("utf-8"),
        )
        for path in sources:
            rel = path.relative_to(root).as_posix()
            _zip_write_bytes(
                archive,
                f"PROJECT_CONTEXT/{rel}",
                path.read_bytes(),
            )
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--module")
    parser.add_argument("--topics")
    parser.add_argument(
        "--output-dir",
        default="tmp/project_context_archives",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest-output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    index = load_index(root)
    topics = (
        [item.strip() for item in args.topics.split(",") if item.strip()]
        if args.topics
        else list(index["default_topics"])
    )
    sources, missing = select_sources(
        root=root,
        index=index,
        topics=topics,
        module=args.module,
    )
    manifest = build_manifest(
        root=root,
        index=index,
        topics=topics,
        module=args.module,
        sources=sources,
        missing=missing,
    )

    if args.manifest_output:
        output = Path(args.manifest_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"PROJECT_CONTEXT_SELECTED_SOURCE_COUNT={len(sources)}")
    print(f"PROJECT_CONTEXT_REQUIRED_MISSING_COUNT={manifest['required_missing_count']}")
    print("PROJECT_CONTEXT_SOURCE_STATE_FINGERPRINT=" + manifest["source_state_fingerprint"])

    if args.dry_run:
        print("PROJECT_CONTEXT_ARCHIVE_CREATED=false")
        return 0 if manifest["required_missing_count"] == 0 else 1

    archive_path = build_archive(
        root=root,
        output_dir=(root / args.output_dir)
        if not Path(args.output_dir).is_absolute()
        else Path(args.output_dir),
        manifest=manifest,
        sources=sources,
        reading_order=list(index["reading_order"]),
    )
    print(f"PROJECT_CONTEXT_ARCHIVE={archive_path.relative_to(root)}")
    print(f"PROJECT_CONTEXT_ARCHIVE_SHA256={_sha(archive_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
