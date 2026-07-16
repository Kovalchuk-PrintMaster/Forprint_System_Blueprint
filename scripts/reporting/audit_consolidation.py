#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from scripts.reporting.table_renderer import TableRow, render_boxed_table

DEFAULT_TARGETS = (
    "scripts/reporting/table_renderer.py",
    "scripts/reporting/statuses.py",
    "scripts/reporting/models.py",
    "scripts/reporting/artifact_writer.py",
    "scripts/reporting/console_summary.py",
    "scripts/reporting/coordination_result_tables.py",
    "scripts/reporting/document_awareness_tables.py",
    "scripts/run_blueprint_checks.py",
    "scripts/coordination/render_document_awareness_dashboard.py",
    "scripts/coordination/render_module_roadmap_dashboard.py",
    "scripts/coordination/module_roadmap.py",
    "scripts/coordination/module_completion_intake.py",
    "scripts/coordination/resolve_next_module_work.py",
    "scripts/coordination/render_prompt_dashboard.py",
    "scripts/coordination/resolve_next_prompt.py",
    "scripts/audit_module_governance.py",
)

SHARED_CORE = {
    "scripts/reporting/table_renderer.py",
    "scripts/reporting/statuses.py",
    "scripts/reporting/models.py",
    "scripts/reporting/artifact_writer.py",
    "scripts/reporting/console_summary.py",
    "scripts/reporting/coordination_result_tables.py",
    "scripts/reporting/document_awareness_tables.py",
}

CONSOLIDATED_CONSUMERS = {
    "scripts/run_blueprint_checks.py",
    "scripts/coordination/render_document_awareness_dashboard.py",
    "scripts/coordination/render_module_roadmap_dashboard.py",
    "scripts/coordination/module_roadmap.py",
    "scripts/coordination/module_completion_intake.py",
    "scripts/coordination/resolve_next_module_work.py",
    "scripts/coordination/render_prompt_dashboard.py",
    "scripts/coordination/resolve_next_prompt.py",
    "scripts/audit_module_governance.py",
}

PARTIAL_MIGRATIONS: set[str] = set()

EXPECTED_PARTIAL_HELPERS: dict[str, set[str]] = {}


@dataclass(frozen=True)
class AuditRecord:
    file: str
    exists: bool
    classification: str
    status: str
    shared_reporting_imports: tuple[str, ...]
    local_helper_names: tuple[str, ...]
    cli_flags: tuple[str, ...]
    writes_artifacts: bool
    evidence: str
    next_action: str


def _imports(tree: ast.AST) -> tuple[str, ...]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module)
    return tuple(sorted(values))


def _function_names(tree: ast.AST) -> tuple[str, ...]:
    return tuple(
        sorted(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        )
    )


def _cli_flags(tree: ast.AST) -> tuple[str, ...]:
    values: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument":
            continue
        for argument in node.args:
            if (
                isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
                and argument.value.startswith("-")
            ):
                values.add(argument.value)
    return tuple(sorted(values))


def _writes_artifacts(source: str) -> bool:
    return any(
        marker in source
        for marker in (
            ".write_text(",
            ".write_bytes(",
            "json.dump(",
            "yaml.safe_dump(",
            ".mkdir(",
        )
    )


def classify_source(relative: str, source: str) -> AuditRecord:
    """Classify one reporting-related source file using verified contracts."""

    tree = ast.parse(source, filename=relative)
    imports = _imports(tree)
    shared_imports = tuple(
        value
        for value in imports
        if value.startswith("scripts.reporting")
    )
    functions = set(_function_names(tree))
    flags = _cli_flags(tree)
    writes = _writes_artifacts(source)

    if relative in SHARED_CORE:
        return AuditRecord(
            file=relative,
            exists=True,
            classification="shared_reporting_core",
            status="OK",
            shared_reporting_imports=shared_imports,
            local_helper_names=(),
            cli_flags=flags,
            writes_artifacts=writes,
            evidence="Canonical shared reporting implementation.",
            next_action="Preserve as shared source of truth.",
        )

    if relative in PARTIAL_MIGRATIONS:
        expected = EXPECTED_PARTIAL_HELPERS.get(relative, set())
        present = tuple(sorted(expected & functions))
        missing = tuple(sorted(expected - functions))

        if present:
            status = "ACTION"
            evidence = "Residual wrappers: " + ", ".join(present)
            next_action = (
                "Remove residual wrappers while preserving roadmap schema, "
                "validation and dashboard output."
            )
        else:
            status = "OK"
            evidence = "No verified residual wrappers remain."
            next_action = "Reclassify as consolidated consumer."

        if missing and present:
            evidence += "; absent: " + ", ".join(missing)

        return AuditRecord(
            file=relative,
            exists=True,
            classification="partial_migration",
            status=status,
            shared_reporting_imports=shared_imports,
            local_helper_names=present,
            cli_flags=flags,
            writes_artifacts=writes,
            evidence=evidence,
            next_action=next_action,
        )

    if relative in CONSOLIDATED_CONSUMERS:
        return AuditRecord(
            file=relative,
            exists=True,
            classification="consolidated_consumer",
            status="OK",
            shared_reporting_imports=shared_imports,
            local_helper_names=(),
            cli_flags=flags,
            writes_artifacts=writes,
            evidence="Verified consumer or CLI wrapper using shared reporting.",
            next_action="Preserve public CLI and artifact contracts.",
        )

    return AuditRecord(
        file=relative,
        exists=True,
        classification="manual_review",
        status="REVIEW",
        shared_reporting_imports=shared_imports,
        local_helper_names=(),
        cli_flags=flags,
        writes_artifacts=writes,
        evidence="Not covered by the verified reporting baseline.",
        next_action="Review before adding to the migration roadmap.",
    )


def audit_repository(
    root: Path,
    targets: tuple[str, ...] = DEFAULT_TARGETS,
) -> tuple[AuditRecord, ...]:
    records: list[AuditRecord] = []

    for relative in targets:
        path = root / relative
        if not path.is_file():
            records.append(
                AuditRecord(
                    file=relative,
                    exists=False,
                    classification="missing",
                    status="FAILED",
                    shared_reporting_imports=(),
                    local_helper_names=(),
                    cli_flags=(),
                    writes_artifacts=False,
                    evidence="Expected reporting file is missing.",
                    next_action="Restore or update the audit baseline.",
                )
            )
            continue

        records.append(
            classify_source(relative, path.read_text(encoding="utf-8"))
        )

    return tuple(records)


def _git_value(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return "-"
    return result.stdout.strip() or "-"


def _summary(records: tuple[AuditRecord, ...]) -> dict[str, int]:
    return {
        "total": len(records),
        "ok": sum(record.status == "OK" for record in records),
        "action": sum(record.status == "ACTION" for record in records),
        "review": sum(record.status == "REVIEW" for record in records),
        "failed": sum(record.status == "FAILED" for record in records),
    }


def render_compact(
    records: tuple[AuditRecord, ...],
    *,
    use_color: bool,
) -> str:
    summary = _summary(records)
    rows = tuple(
        TableRow(
            values=(
                record.status,
                record.classification,
                record.file,
                record.evidence,
                record.next_action,
            ),
            token={
                "OK": "success",
                "ACTION": "active",
                "REVIEW": "warning",
                "FAILED": "failed",
            }.get(record.status, "info"),
        )
        for record in records
    )

    table = render_boxed_table(
        headers=("Status", "Class", "File", "Evidence", "Next action"),
        widths=(8, 22, 52, 44, 48),
        rows=rows,
        use_color=use_color,
    )

    summary_table = render_boxed_table(
        headers=("Total", "OK", "Action", "Review", "Failed"),
        widths=(7, 7, 8, 8, 8),
        rows=(
            TableRow(
                values=(
                    str(summary["total"]),
                    str(summary["ok"]),
                    str(summary["action"]),
                    str(summary["review"]),
                    str(summary["failed"]),
                ),
                token="failed" if summary["failed"] else "success",
            ),
        ),
        use_color=use_color,
    )

    return "\n\n".join(
        (
            "ForPrint Reporting Consolidation Audit",
            table,
            "Summary",
            summary_table,
            (
                "Decision: next implementation front is "
                "blueprint_reporting_consolidation_closeout_v0_1."
            ),
        )
    )


def build_payload(
    root: Path,
    records: tuple[AuditRecord, ...],
) -> dict[str, object]:
    return {
        "schema_version": "blueprint_reporting_consolidation_audit_v0_1",
        "mode": "read_only",
        "branch": _git_value(root, "branch", "--show-current"),
        "commit": _git_value(root, "rev-parse", "--short", "HEAD"),
        "summary": _summary(records),
        "records": [asdict(record) for record in records],
        "planning_horizon": [
            "blueprint_reporting_consolidation_closeout_v0_1",
            "blueprint_document_ledger_result_table_v0_1",
            "blueprint_module_roadmap_validation_result_table_v0_1",
            "blueprint_prompt_queue_validation_result_table_v0_1",
            "blueprint_metadata_validation_result_tables_v0_1",
            "blueprint_standards_validation_result_tables_v0_1",
            "blueprint_generator_terminal_artifact_split_v0_1",
            "blueprint_reporting_consolidation_reaudit_v0_2",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit the verified Blueprint reporting consolidation baseline."
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    records = audit_repository(root)
    payload = build_payload(root, records)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        use_color = not args.no_color and "NO_COLOR" not in os.environ
        print(render_compact(records, use_color=use_color))

    return 1 if payload["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
