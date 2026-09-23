#!/usr/bin/env python3
"""Build deterministic non-authoritative inventory of current generator candidates."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "indexes/generator_inventory.yaml"
REGISTRY = ROOT / "coordination/registry/generator_derivation_registry_v0_1.yaml"

WRITE_RE = re.compile(
    r"(write_text|write_bytes|yaml\.(?:dump|safe_dump)|json\.dump|"
    r"open\([^)]*[\"'][wa][+b]?[\"']|ZipFile\([^)]*[\"']w[\"'])"
)
NAME_RE = re.compile(
    r"(?:^|/)(?:build|render|generate|refresh|compile|index|inventory|snapshot|"
    r"projection|dashboard|context|report|apply|update|record|prepare|manage|"
    r"accept|review)[A-Za-z0-9_.-]*\.py$",
    re.IGNORECASE,
)
RELEVANT_RE = re.compile(
    r"(index|knowledge|context|inventory|freshness|projection|dashboard|roadmap|"
    r"canonical_state|portfolio|derivation|authority|report|artifact)",
    re.IGNORECASE,
)
EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    "node_modules",
}


class Dumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def current_python_files() -> list[str]:
    result = []
    for root_name in ("scripts", "tools"):
        base = ROOT / root_name
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            rel = path.relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in rel.parts):
                continue
            if not path.is_file() or path.is_symlink():
                continue
            result.append(rel.as_posix())
    return sorted(set(result))


def tracked_files() -> set[str]:
    cp = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return set(cp.stdout.splitlines())


def dirty_status() -> dict[str, str]:
    cp = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", "scripts", "tools"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    result = {}
    for line in cp.stdout.splitlines():
        if not line or len(line) < 4:
            continue
        result[line[3:]] = line[:2]
    return result


def git_state(rel: str, tracked: set[str], dirty: dict[str, str]) -> str:
    if rel not in tracked:
        return "untracked"
    status = dirty.get(rel)
    if status is None:
        return "tracked_clean"
    return "tracked_modified"


def registry_by_script() -> dict[str, dict]:
    if not REGISTRY.is_file():
        return {}
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    return {str(row["script"]): row for row in data.get("generators", [])}


def discover() -> list[dict]:
    registry = registry_by_script()
    tracked = tracked_files()
    dirty = dirty_status()
    rows = []

    for rel in current_python_files():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        writes = bool(WRITE_RE.search(text))
        named = bool(NAME_RE.search(rel))
        relevant = bool(RELEVANT_RE.search(rel) or RELEVANT_RE.search(text[:20000]))
        if not (writes and (named or relevant)):
            continue

        contract = registry.get(rel)
        rows.append(
            {
                "script": rel,
                "sha256": sha256(path),
                "git_state": git_state(rel, tracked, dirty),
                "git_tracked": rel in tracked,
                "writes_files_detected": True,
                "generator_named": named,
                "native_check_literal": "--check" in text,
                "dry_run_literal": "--dry-run" in text,
                "apply_literal": "--apply" in text,
                "write_api_match_count": len(WRITE_RE.findall(text)),
                "registry_state": "registered" if contract else "unregistered",
                "registry_id": contract.get("id") if contract else None,
                "registered_output_state": contract.get("output_state") if contract else None,
                "registered_check_mode": contract.get("check_mode") if contract else None,
                "registered_make_check_allowed": (
                    contract.get("make_check_allowed") if contract else None
                ),
                "registered_review_status": contract.get("review_status") if contract else None,
            }
        )
    return sorted(rows, key=lambda row: row["script"])


def render() -> str:
    rows = discover()
    registered = [row for row in rows if row["registry_state"] == "registered"]
    unregistered = [row for row in rows if row["registry_state"] == "unregistered"]
    data = {
        "schema_version": "forprint_generator_inventory_v0_1",
        "status": "derived_non_authoritative",
        "authority": "none",
        "source_scope": "current_working_tree_python_scripts",
        "generated_from": [
            "current files under scripts/ and tools/",
            "git ls-files",
            "git status --porcelain=v1 --untracked-files=all",
            "coordination/registry/generator_derivation_registry_v0_1.yaml",
        ],
        "summary": {
            "generator_candidate_count": len(rows),
            "registered_candidate_count": len(registered),
            "unregistered_candidate_count": len(unregistered),
            "tracked_candidate_count": sum(1 for row in rows if row["git_tracked"]),
            "untracked_candidate_count": sum(1 for row in rows if not row["git_tracked"]),
            "modified_tracked_candidate_count": sum(
                1 for row in rows if row["git_state"] == "tracked_modified"
            ),
            "native_check_literal_count": sum(1 for row in rows if row["native_check_literal"]),
            "registered_tracked_derived_without_check_count": sum(
                1
                for row in registered
                if row["registered_output_state"] == "tracked_derived"
                and row["registered_check_mode"] == "missing"
            ),
        },
        "generator_candidates": rows,
    }
    return yaml.dump(
        data,
        Dumper=Dumper,
        allow_unicode=True,
        sort_keys=False,
        width=110,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()

    if args.check:
        if not OUTPUT.is_file():
            print(f"DRIFT missing={OUTPUT.relative_to(ROOT)}")
            return 1
        if OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"DRIFT stale={OUTPUT.relative_to(ROOT)}")
            return 1
        print("GENERATOR_INVENTORY_CHECK=PASS")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"GENERATOR_INVENTORY={OUTPUT.relative_to(ROOT)}")
    print("GENERATOR_INVENTORY_APPLY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
