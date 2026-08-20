from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from scripts.reporting.coordination_result_tables import render_module_governance_summary

ROOT = Path(__file__).resolve().parents[1]
MODULE_SOURCES = ROOT / "coordination" / "module_sources" / "module_git_sources.yaml"

REPORT_JSON = ROOT / "reports" / "module_governance_audit.json"
REPORT_MD = ROOT / "reports" / "module_governance_audit.md"

def _resolve_report_paths(report_dir: Path | None) -> tuple[Path, Path]:
    """Resolve audit report paths."""

    if report_dir is None:
        return REPORT_JSON, REPORT_MD

    return (
        report_dir / "module_governance_audit.json",
        report_dir / "module_governance_audit.md",
    )

REQUIRED_FILES = [
    "Makefile",
    "forprint_module_manifest.yaml",
    "coordination/status/current_status.yaml",
    "coordination/prompts/index.yaml",
    "coordination/reports/index.yaml",
    "coordination/status/next_questions_for_blueprint.md",
]

REQUIRED_TARGETS = [
    "check",
    "check-report",
    "status-report",
    "coordination-sync-check",
    "blueprint-check",
    "blueprint-sync-directives",
    "coordination-check",
    "coordination-fix",
    "module-policy-check",
    "governance-check",
]

DEFERRED_STATUSES = {
    "planned",
    "deferred",
    "disabled",
    "not_started",
    "future",
    "placeholder",
}


@dataclass
class ModuleAuditResult:
    module_id: str
    module_name: str
    local_path: str
    declared_status: str
    audit_status: str
    missing_files: list[str]
    missing_targets: list[str]
    notes: list[str]


def _load_yaml(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _deep_collect_modules(value: Any) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []

    if isinstance(value, dict):
        looks_like_module = (
            "module_id" in value
            or "id" in value
            or "module" in value
        ) and (
            "local_path" in value
            or "path" in value
            or "repository" in value
            or "repo" in value
        )

        if looks_like_module:
            collected.append(value)

        for child in value.values():
            collected.extend(_deep_collect_modules(child))

    elif isinstance(value, list):
        for item in value:
            collected.extend(_deep_collect_modules(item))

    return collected


def _normalize_module(raw: dict[str, Any]) -> dict[str, str]:
    module_id = str(
        raw.get("module_id")
        or raw.get("id")
        or raw.get("module")
        or raw.get("name")
        or "unknown"
    )

    module_name = str(raw.get("module_name") or raw.get("name") or module_id)

    local_path = str(
        raw.get("local_path")
        or raw.get("path")
        or raw.get("working_dir")
        or raw.get("local_repo_path")
        or ""
    )

    declared_status = str(
        raw.get("status")
        or raw.get("module_status")
        or raw.get("lifecycle_status")
        or "active"
    )

    return {
        "module_id": module_id,
        "module_name": module_name,
        "local_path": local_path,
        "declared_status": declared_status,
    }


def _load_modules() -> list[dict[str, str]]:
    data = _load_yaml(MODULE_SOURCES)
    raw_modules = _deep_collect_modules(data)

    normalized: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw in raw_modules:
        module = _normalize_module(raw)
        module_id = module["module_id"]

        if module_id in seen or module_id == "unknown":
            continue

        seen.add(module_id)
        normalized.append(module)

    normalized.sort(key=lambda item: item["module_id"])
    return normalized


def _make_targets(makefile: Path) -> set[str]:
    if not makefile.exists():
        return set()

    target_pattern = re.compile(r"^([A-Za-z0-9_.-]+)\s*:")
    targets: set[str] = set()

    for line in makefile.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = target_pattern.match(line)
        if match:
            targets.add(match.group(1))

    return targets


def _audit_module(module: dict[str, str]) -> ModuleAuditResult:
    module_id = module["module_id"]
    local_path_text = module["local_path"]
    declared_status = module["declared_status"]
    notes: list[str] = []

    if declared_status.lower() in DEFERRED_STATUSES:
        return ModuleAuditResult(
            module_id=module_id,
            module_name=module["module_name"],
            local_path=local_path_text,
            declared_status=declared_status,
            audit_status="DEFERRED",
            missing_files=[],
            missing_targets=[],
            notes=["Module is declared as planned/deferred."],
        )

    if not local_path_text:
        return ModuleAuditResult(
            module_id=module_id,
            module_name=module["module_name"],
            local_path="",
            declared_status=declared_status,
            audit_status="WARN",
            missing_files=REQUIRED_FILES,
            missing_targets=REQUIRED_TARGETS,
            notes=["No local_path declared in module sources registry."],
        )

    module_path = Path(local_path_text)

    if not module_path.exists():
        return ModuleAuditResult(
            module_id=module_id,
            module_name=module["module_name"],
            local_path=local_path_text,
            declared_status=declared_status,
            audit_status="WARN",
            missing_files=REQUIRED_FILES,
            missing_targets=REQUIRED_TARGETS,
            notes=["Declared local_path does not exist."],
        )

    missing_files = [
        file_name for file_name in REQUIRED_FILES if not (module_path / file_name).exists()
    ]

    targets = _make_targets(module_path / "Makefile")
    missing_targets = [target for target in REQUIRED_TARGETS if target not in targets]

    if not missing_files and not missing_targets:
        audit_status = "OK"
    else:
        audit_status = "NEEDS_ALIGNMENT"

    return ModuleAuditResult(
        module_id=module_id,
        module_name=module["module_name"],
        local_path=local_path_text,
        declared_status=declared_status,
        audit_status=audit_status,
        missing_files=missing_files,
        missing_targets=missing_targets,
        notes=notes,
    )


def _summary(results: list[ModuleAuditResult]) -> dict[str, int]:
    summary = {
        "OK": 0,
        "NEEDS_ALIGNMENT": 0,
        "WARN": 0,
        "DEFERRED": 0,
    }

    for result in results:
        summary[result.audit_status] = summary.get(result.audit_status, 0) + 1

    return summary


def _write_json(results: list[ModuleAuditResult], report_json: Path) -> None:
    report_json.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_file": str(MODULE_SOURCES.relative_to(ROOT)),
        "required_files": REQUIRED_FILES,
        "required_targets": REQUIRED_TARGETS,
        "summary": _summary(results),
        "modules": [asdict(result) for result in results],
    }

    report_json.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_markdown(results: list[ModuleAuditResult], report_md: Path) -> None:
    report_md.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# ForPrint Module Governance Audit",
        "",
        f"Generated at: `{datetime.now(UTC).isoformat()}`",
        "",
        "## Summary",
        "",
    ]

    for status, count in _summary(results).items():
        lines.append(f"- `{status}`: {count}")

    lines.extend(
        [
            "",
            "## Required files",
            "",
            *[f"- `{item}`" for item in REQUIRED_FILES],
            "",
            "## Required Makefile targets",
            "",
            *[f"- `make {item}`" for item in REQUIRED_TARGETS],
            "",
            "## Module results",
            "",
            "| Module | Status | Missing files | Missing targets | Notes |",
            "|---|---:|---:|---:|---|",
        ]
    )

    for result in results:
        missing_files = "<br>".join(f"`{item}`" for item in result.missing_files) or "-"
        missing_targets = "<br>".join(f"`{item}`" for item in result.missing_targets) or "-"
        notes = "<br>".join(result.notes) or "-"
        lines.append(
            f"| `{result.module_id}` | `{result.audit_status}` | "
            f"{missing_files} | {missing_targets} | {notes} |"
        )

    lines.append("")
    report_md.write_text("\n".join(lines), encoding="utf-8")

def build_cli() -> argparse.ArgumentParser:
    """Build command-line parser for the governance audit."""

    parser = argparse.ArgumentParser(description="Audit ForPrint module governance.")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Run audit without writing reports/module_governance_audit.* files.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Directory for generated audit reports. Defaults to reports/.",
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_cli().parse_args(argv)

    modules = _load_modules()
    results = [_audit_module(module) for module in modules]
    report_json, report_md = _resolve_report_paths(args.report_dir)

    if not args.no_write:
        _write_json(results, report_json)
        _write_markdown(results, report_md)

    print(
        render_module_governance_summary(
            modules_checked=len(results),
            summary=_summary(results),
            report_writing=not args.no_write,
            report_json=str(report_json) if not args.no_write else None,
            report_markdown=str(report_md) if not args.no_write else None,
            use_color="NO_COLOR" not in os.environ,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
