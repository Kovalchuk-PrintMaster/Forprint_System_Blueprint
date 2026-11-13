#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

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
CURRENT_RELEASE = Path("coordination/releases/current.yaml")

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

TASK_CONTEXT_MODULE_MEMORY_PATHS = (
    Path("AGENTS.md"),
    Path("coordination") / "module_memory" / "module_memory.yaml",
    Path("coordination") / "module_memory" / "inventory_index.yaml",
    Path("coordination") / "module_memory" / "implementation_lineage.yaml",
    Path("coordination") / "module_memory" / "document_authority.yaml",
    Path("coordination") / "module_memory" / "roadmap_state.yaml",
    Path("coordination") / "module_memory" / "current_state.yaml",
    Path("coordination") / "module_memory" / "fresh_context_manifest.yaml",
)
TASK_CONTEXT_CONTROL_PROGRAM = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-09-06__blueprint__control_plane_module_memory_semantic_convergence_program_v0_1.yaml"
)
TASK_CONTEXT_ACTIVATION_ARCHITECTURE = Path(
    "coordination/internal_work/blueprint/governance/"
    "2026-09-06__blueprint__operator_clarified_ai_activation_and_portfolio_rollout_architecture_v0_1.yaml"
)
TASK_CONTEXT_RELEASE_POLICY = Path(
    "coordination/standards/governance/outgoing_prompt_release_policy_v0_1.yaml"
)


@dataclass(frozen=True)
class BundleResult:
    module: str
    scope: str
    generated_at: str
    document_count: int
    content: str

@dataclass(frozen=True)
class TaskContextResult:
    module: str
    prompt_id: str
    task_context_id: str
    generated_at: str
    manifest: dict[str, Any]
    bootstrap: str
    source_files: tuple[tuple[str, Path], ...]


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


def _current_release_summary(root: Path) -> dict[str, str]:
    path = root / CURRENT_RELEASE
    if not path.is_file():
        return {
            "source": CURRENT_RELEASE.as_posix(),
            "availability": "missing_in_isolated_root",
            "base_release": "unknown",
            "hardening_release": "unknown",
            "legacy_compatibility": "unknown",
        }

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Current release projection must be a YAML mapping")
    if data.get("schema_version") != "forprint_current_release_projection_v0_1":
        raise ValueError("Current release projection schema is invalid")

    metadata = data.get("metadata")
    release = data.get("release")
    legacy = data.get("legacy_compatibility")
    if not isinstance(metadata, dict):
        raise ValueError("Current release metadata must be a mapping")
    if not isinstance(release, dict):
        raise ValueError("Current release state must be a mapping")
    if not isinstance(legacy, dict):
        raise ValueError("Current release legacy state must be a mapping")
    if metadata.get("status") != "authoritative_current":
        raise ValueError("Current release projection is not authoritative_current")

    return {
        "source": CURRENT_RELEASE.as_posix(),
        "availability": "authoritative_current",
        "base_release": (
            f"{release.get('base_release')} "
            f"{release.get('base_release_state')}"
        ),
        "hardening_release": (
            f"{release.get('hardening_release')} "
            f"{release.get('hardening_state')}"
        ),
        "legacy_compatibility": (
            "advisory / nonblocking"
            if legacy.get("visibility") == "advisory_yellow"
            and legacy.get("default_current_gate_behavior")
            == "nonblocking_excluded_or_skipped"
            else "INVALID"
        ),
    }


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
    current_release = _current_release_summary(root)

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
        "## Current Release Authority",
        "",
        f"- Source: `{current_release['source']}`",
        f"- Availability: `{current_release['availability']}`",
        f"- Base release: `{current_release['base_release']}`",
        f"- Hardening release: `{current_release['hardening_release']}`",
        (
            "- Legacy compatibility: "
            f"`{current_release['legacy_compatibility']}`"
        ),
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



def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"{label} is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a YAML mapping: {path}")
    return data


def _git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            f"git {' '.join(args)} failed in {repo}: {result.stdout.strip()}"
        )
    return result.stdout.strip()


def _task_queue_row(
    *,
    root: Path,
    module: str,
    prompt_id: str,
) -> tuple[Path, dict[str, Any]]:
    queue_path = root / "coordination/outgoing_prompts" / module / "index.yaml"
    queue = _load_yaml_mapping(queue_path, label="prompt queue")
    rows = queue.get("prompt_queue")
    if not isinstance(rows, list):
        raise ValueError("prompt queue must contain a prompt_queue list")
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("prompt_id") == prompt_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"prompt id {prompt_id!r} must resolve to exactly one queue row"
        )
    row = matches[0]
    if row.get("target_module") != module:
        raise ValueError("prompt target_module does not match requested module")
    execution = row.get("module_execution")
    if not isinstance(execution, dict):
        raise ValueError("prompt queue row has no module_execution mapping")
    if execution.get("status") != "ready_for_module_pull":
        raise ValueError(
            "task context compilation requires ready_for_module_pull prompt state"
        )
    return queue_path, row


def _machine_prompt_payload(approved_prompt: Path) -> dict[str, Any]:
    text = approved_prompt.read_text(encoding="utf-8")
    marker = "# ForPrint machine prompt"
    if marker not in text:
        raise ValueError("approved prompt has no ForPrint machine prompt section")
    tail = text.split(marker, 1)[1]
    if "```yaml" not in tail:
        raise ValueError("approved prompt has no machine YAML block")
    payload = tail.split("```yaml", 1)[1].split("```", 1)[0]
    data = yaml.safe_load(payload)
    if not isinstance(data, dict):
        raise ValueError("approved prompt machine YAML must be a mapping")
    return data


def _task_source_entry(
    *,
    origin: str,
    repository_root: Path,
    path: Path,
    role: str,
    authority_class: str,
    required: bool,
) -> tuple[dict[str, Any], tuple[str, Path]]:
    if not path.is_file():
        if required:
            raise ValueError(f"required task-context source is missing: {path}")
        raise FileNotFoundError(path)
    try:
        relative = path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"task-context source must stay inside {origin} repository: {path}"
        ) from exc
    archive_path = f"sources/{origin}/{relative}"
    entry = {
        "origin": origin,
        "role": role,
        "path": relative,
        "authority_class": authority_class,
        "sha256": _sha256_path(path),
        "size_bytes": path.stat().st_size,
        "required": required,
    }
    return entry, (archive_path, path)


def _validate_fresh_context_manifest(
    *,
    module_root: Path,
    module: str,
    prompt_id: str,
) -> tuple[Path, dict[str, Any]]:
    manifest_path = (
        module_root
        / "coordination"
        / "module_memory"
        / "fresh_context_manifest.yaml"
    )
    manifest = _load_yaml_mapping(
        manifest_path,
        label="module fresh-context manifest",
    )
    if manifest.get("module_id") != module:
        raise ValueError("fresh-context manifest module_id mismatch")
    prompt = manifest.get("prompt")
    if not isinstance(prompt, dict) or prompt.get("prompt_id") != prompt_id:
        raise ValueError("fresh-context manifest prompt_id mismatch")
    if manifest.get("worker_dispatch_state") != "PAUSED_BY_OPERATOR":
        raise ValueError(
            "task context v0.1 requires worker dispatch to remain PAUSED_BY_OPERATOR"
        )
    if manifest.get("unclassified_dirty_paths") != []:
        raise ValueError("fresh-context manifest contains unclassified dirty paths")

    repository = manifest.get("repository")
    if not isinstance(repository, dict):
        raise ValueError("fresh-context manifest repository mapping is missing")
    actual_head = _git_output(module_root, "rev-parse", "HEAD")
    if repository.get("head") != actual_head:
        raise ValueError("module HEAD differs from fresh-context manifest")

    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("fresh-context manifest sources must be a list")
    for item in sources:
        if not isinstance(item, dict):
            raise ValueError("fresh-context source row must be a mapping")
        relative = item.get("path")
        expected_sha = item.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected_sha, str):
            raise ValueError("fresh-context source requires path and sha256")
        source = module_root / relative
        if not source.is_file():
            raise ValueError(f"fresh-context source is missing: {relative}")
        if _sha256_path(source) != expected_sha:
            raise ValueError(f"fresh-context source hash drift: {relative}")

    return manifest_path, manifest


def _latest_previous_completion(
    *,
    root: Path,
    rows: list[dict[str, Any]],
    sequence: int,
) -> Path | None:
    candidates = [
        row
        for row in rows
        if isinstance(row.get("sequence"), int)
        and row["sequence"] < sequence
        and isinstance(row.get("module_execution"), dict)
        and row["module_execution"].get("status") == "completed_by_module"
    ]
    candidates.sort(key=lambda row: row["sequence"], reverse=True)
    for row in candidates:
        report = row["module_execution"].get("completion_report")
        if isinstance(report, str) and report:
            path = root / report
            if path.is_file():
                return path
    return None


def build_task_context(
    *,
    root: Path,
    module: str,
    prompt_id: str,
    module_root: Path,
) -> TaskContextResult:
    root = root.resolve()
    module_root = module_root.resolve()
    if not (module_root / ".git").exists():
        raise ValueError("module_root must be a git working tree")

    queue_path, row = _task_queue_row(
        root=root,
        module=module,
        prompt_id=prompt_id,
    )
    queue_data = _load_yaml_mapping(queue_path, label="prompt queue")
    rows = [
        item
        for item in queue_data.get("prompt_queue", [])
        if isinstance(item, dict)
    ]

    approved_rel = row.get("file")
    if not isinstance(approved_rel, str):
        raise ValueError("prompt queue row has no approved prompt file")
    approved_prompt = root / "coordination/outgoing_prompts" / module / approved_rel
    if not approved_prompt.is_file():
        raise ValueError(f"approved prompt is missing: {approved_prompt}")

    contract_ref = row.get("prompt_contract")
    if not isinstance(contract_ref, dict):
        raise ValueError("prompt queue row has no prompt_contract mapping")
    contract_rel = contract_ref.get("path")
    if not isinstance(contract_rel, str):
        raise ValueError("prompt contract path is missing")
    contract_path = root / contract_rel
    if not contract_path.is_file():
        raise ValueError(f"prompt contract is missing: {contract_path}")
    expected_contract_sha = contract_ref.get("file_sha256")
    if (
        isinstance(expected_contract_sha, str)
        and _sha256_path(contract_path) != expected_contract_sha
    ):
        raise ValueError("prompt contract hash does not match queue authority")

    machine_prompt = _machine_prompt_payload(approved_prompt)
    acceptance = machine_prompt.get("acceptance_handoff")
    if not isinstance(acceptance, dict):
        raise ValueError("machine prompt has no acceptance_handoff mapping")
    oracle_rel = acceptance.get("acceptance_oracle_path")
    if not isinstance(oracle_rel, str):
        raise ValueError("acceptance oracle path is missing")
    oracle_path = root / oracle_rel
    if not oracle_path.is_file():
        raise ValueError(f"acceptance oracle is missing: {oracle_path}")

    contract = _load_yaml_mapping(contract_path, label="prompt contract")
    oracle = _load_yaml_mapping(oracle_path, label="acceptance oracle")
    contract_prompt_id = contract.get("prompt_id")
    if isinstance(contract_prompt_id, str) and contract_prompt_id != prompt_id:
        raise ValueError("prompt contract prompt_id mismatch")
    oracle_prompt_id = oracle.get("prompt_id")
    if isinstance(oracle_prompt_id, str) and oracle_prompt_id != prompt_id:
        raise ValueError("acceptance oracle prompt_id mismatch")

    fresh_manifest_path, fresh_manifest = _validate_fresh_context_manifest(
        module_root=module_root,
        module=module,
        prompt_id=prompt_id,
    )

    blueprint_head = _git_output(root, "rev-parse", "HEAD")
    module_head = _git_output(module_root, "rev-parse", "HEAD")
    blueprint_status = _git_output(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    module_status = _git_output(
        module_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )

    release_policy_path = root / TASK_CONTEXT_RELEASE_POLICY
    release_policy = _load_yaml_mapping(
        release_policy_path,
        label="outgoing prompt release policy",
    )
    release = release_policy.get("release")
    if not isinstance(release, dict) or not (
        release.get("global_enabled") is False
        and release.get("authorized_modules") == []
        and release.get("authorization_evidence") is None
    ):
        raise ValueError("release policy must remain fail-closed")

    sources: list[dict[str, Any]] = []
    source_files: list[tuple[str, Path]] = []

    def add_source(
        *,
        origin: str,
        repository_root: Path,
        path: Path,
        role: str,
        authority_class: str,
        required: bool = True,
    ) -> None:
        try:
            entry, archive_item = _task_source_entry(
                origin=origin,
                repository_root=repository_root,
                path=path,
                role=role,
                authority_class=authority_class,
                required=required,
            )
        except FileNotFoundError:
            return
        sources.append(entry)
        source_files.append(archive_item)

    add_source(
        origin="blueprint",
        repository_root=root,
        path=root / "AGENTS.md",
        role="blueprint_authority_frontdoor",
        authority_class="governance_navigation",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=root / CURRENT_RELEASE,
        role="current_release",
        authority_class="release_authority",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=release_policy_path,
        role="release_policy",
        authority_class="execution_boundary",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=queue_path,
        role="prompt_queue",
        authority_class="prompt_state_authority",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=approved_prompt,
        role="approved_prompt",
        authority_class="task_authority",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=contract_path,
        role="prompt_contract",
        authority_class="task_contract_authority",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=oracle_path,
        role="acceptance_oracle",
        authority_class="acceptance_evidence_authority",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=root / TASK_CONTEXT_CONTROL_PROGRAM,
        role="control_plane_program",
        authority_class="planning_direction",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=root / TASK_CONTEXT_ACTIVATION_ARCHITECTURE,
        role="activation_architecture",
        authority_class="planning_direction",
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=root / "coordination/roadmaps" / f"{module}.yaml",
        role="module_roadmap",
        authority_class="roadmap_navigation",
        required=False,
    )
    add_source(
        origin="blueprint",
        repository_root=root,
        path=root / "coordination/module_policy" / module / "module_policy.md",
        role="module_policy",
        authority_class="module_policy",
        required=False,
    )

    for relative in TASK_CONTEXT_MODULE_MEMORY_PATHS:
        add_source(
            origin="module",
            repository_root=module_root,
            path=module_root / relative,
            role=(
                "module_authority_frontdoor"
                if relative == Path("AGENTS.md")
                else f"module_self_knowledge:{Path(relative).stem}"
            ),
            authority_class=(
                "module_governance_navigation"
                if relative == Path("AGENTS.md")
                else "module_self_knowledge"
            ),
        )

    previous_completion = _latest_previous_completion(
        root=root,
        rows=rows,
        sequence=int(row.get("sequence", 0)),
    )
    if previous_completion is not None:
        add_source(
            origin="blueprint",
            repository_root=root,
            path=previous_completion,
            role="previous_completion",
            authority_class="historical_completion_evidence",
            required=False,
        )

    sources.sort(key=lambda item: (item["origin"], item["role"], item["path"]))
    source_files.sort(key=lambda item: item[0])

    identity_material = {
        "module_id": module,
        "prompt_id": prompt_id,
        "blueprint_head": blueprint_head,
        "module_head": module_head,
        "approved_prompt_sha256": _sha256_path(approved_prompt),
        "contract_sha256": _sha256_path(contract_path),
        "oracle_sha256": _sha256_path(oracle_path),
        "module_fresh_context_manifest_sha256": _sha256_path(fresh_manifest_path),
        "source_hashes": [
            f"{item['origin']}:{item['path']}:{item['sha256']}"
            for item in sources
        ],
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            identity_material,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    task_context_id = (
        f"{_safe_output_name(module)}__{_safe_output_name(prompt_id)}__"
        f"{fingerprint[:16]}"
    )
    generated_at = datetime.now(UTC).isoformat()

    manifest: dict[str, Any] = {
        "schema_version": "forprint_task_context_manifest_v0_1",
        "task_context_id": task_context_id,
        "generated_at": generated_at,
        "identity": {
            "module_id": module,
            "prompt_id": prompt_id,
            "prompt_sequence": row.get("sequence"),
            "context_fingerprint_sha256": fingerprint,
        },
        "authority_chain": {
            "prompt_queue": _relative_to_root(root, queue_path),
            "approved_prompt": _relative_to_root(root, approved_prompt),
            "prompt_contract": _relative_to_root(root, contract_path),
            "acceptance_oracle": _relative_to_root(root, oracle_path),
            "module_fresh_context_manifest": (
                fresh_manifest_path.relative_to(module_root).as_posix()
            ),
        },
        "repository_baseline": {
            "blueprint": {
                "head": blueprint_head,
                "dirty_entry_count": len(
                    [line for line in blueprint_status.splitlines() if line]
                ),
                "status_sha256": hashlib.sha256(
                    blueprint_status.encode("utf-8")
                ).hexdigest(),
            },
            "module": {
                "root": str(module_root),
                "head": module_head,
                "branch": _git_output(module_root, "branch", "--show-current"),
                "dirty_paths": [
                    line[3:]
                    for line in module_status.splitlines()
                    if len(line) >= 4
                ],
            },
        },
        "module_self_knowledge": {
            "fresh_context_state": "PASS",
            "worker_dispatch_state": fresh_manifest.get("worker_dispatch_state"),
            "unclassified_dirty_paths": fresh_manifest.get(
                "unclassified_dirty_paths"
            ),
            "required_surface_count": len(TASK_CONTEXT_MODULE_MEMORY_PATHS),
        },
        "task_prompt": {
            "path": _relative_to_root(root, approved_prompt),
            "sha256": _sha256_path(approved_prompt),
        },
        "prompt_contract": {
            "path": _relative_to_root(root, contract_path),
            "sha256": _sha256_path(contract_path),
        },
        "acceptance_oracle": {
            "path": _relative_to_root(root, oracle_path),
            "sha256": _sha256_path(oracle_path),
        },
        "roadmap_slice": {
            "module_roadmap_included": any(
                item["role"] == "module_roadmap" for item in sources
            ),
            "module_local_roadmap_state_included": True,
        },
        "dependency_readiness": {
            "status": "DEFERRED_TO_LAUNCH_REQUEST_GATE_V0_1",
            "launch_authorized_by_compiler": False,
        },
        "previous_completion": {
            "included": previous_completion is not None,
            "path": (
                _relative_to_root(root, previous_completion)
                if previous_completion is not None
                else None
            ),
        },
        "execution_boundaries": {
            "worker_dispatch_allowed": False,
            "prompt_claim_allowed": False,
            "blueprint_accept_allowed": False,
            "next_prompt_release_allowed": False,
            "telegram_required": False,
            "repository_write_performed": False,
            "secrets_allowed_in_bundle": False,
        },
        "budget_policy": {
            "mode": "NOT_AUTHORIZED_FOR_EXECUTION",
            "max_cost_usd": 0,
        },
        "freshness_evidence": {
            "module_fresh_context_manifest_sha256": _sha256_path(
                fresh_manifest_path
            ),
            "module_head_matches_manifest": True,
            "all_manifest_source_hashes_match": True,
            "release_policy_fail_closed": True,
        },
        "source_manifest": sources,
    }

    bootstrap_lines = [
        f"# ForPrint Task Context — {module}",
        "",
        f"- Task context id: `{task_context_id}`",
        f"- Module: `{module}`",
        f"- Prompt: `{prompt_id}`",
        f"- Generated at: `{generated_at}`",
        "",
        "## Execution state",
        "",
        "- This artifact is context compilation evidence only.",
        "- Worker dispatch is **not authorized** by this artifact.",
        "- Prompt claim is **not authorized** by this artifact.",
        "- Blueprint ACCEPT / next-prompt release are **not authorized**.",
        "",
        "## Read order",
        "",
        "1. Blueprint authority front door and current release/policy.",
        "2. Prompt queue, approved prompt, Prompt Contract and Acceptance Oracle.",
        "3. Module `AGENTS.md` and Module Memory surfaces.",
        "4. Module roadmap/current-state/fresh-context evidence.",
        "5. Previous completion evidence when present.",
        "",
        "## Freshness",
        "",
        f"- Module HEAD: `{module_head}`",
        "- Module fresh-context validation: `PASS`",
        "- Unclassified module dirty paths: `0`",
        "- Worker dispatch state: `PAUSED_BY_OPERATOR`",
        "",
        "## Next gate",
        "",
        "A separate Launch Request + Fresh Context Gate must validate dependencies,",
        "approval identity, budget and current repository state before dispatch.",
        "",
    ]

    return TaskContextResult(
        module=module,
        prompt_id=prompt_id,
        task_context_id=task_context_id,
        generated_at=generated_at,
        manifest=manifest,
        bootstrap="\n".join(bootstrap_lines),
        source_files=tuple(source_files),
    )


def write_task_context_archive(
    *,
    result: TaskContextResult,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{result.task_context_id}__{timestamp}.zip"
    output_path = output_dir / filename
    if output_path.exists():
        raise ValueError(f"task-context archive already exists: {output_path}")

    manifest_text = yaml.safe_dump(
        result.manifest,
        sort_keys=False,
        allow_unicode=True,
        width=112,
    )
    with zipfile.ZipFile(
        output_path,
        "x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        archive.writestr("TASK_CONTEXT_MANIFEST.yaml", manifest_text)
        archive.writestr("BOOTSTRAP_FOR_TASK.md", result.bootstrap)
        for archive_path, source in result.source_files:
            archive.write(source, archive_path)

    return output_path


def _render_task_context_summary(
    result: TaskContextResult,
    *,
    output_path: Path | None,
) -> str:
    lines = [
        "TASK_CONTEXT_COMPILER=PASS",
        f"TASK_CONTEXT_ID={result.task_context_id}",
        f"MODULE={result.module}",
        f"PROMPT_ID={result.prompt_id}",
        f"SOURCE_COUNT={len(result.manifest['source_manifest'])}",
        "WORKER_DISPATCH_ALLOWED=false",
        "PROMPT_CLAIM_ALLOWED=false",
    ]
    if output_path is not None:
        lines.extend(
            [
                f"TASK_CONTEXT_ARCHIVE={output_path}",
                f"TASK_CONTEXT_ARCHIVE_SHA256={_sha256_path(output_path)}",
            ]
        )
    return "\n".join(lines)


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
        "--task-context",
        action="store_true",
        help="Compile task-aware context using the existing context-bundle primitive.",
    )
    parser.add_argument(
        "--prompt-id",
        default=None,
        help="Prompt id for --task-context mode.",
    )
    parser.add_argument(
        "--module-root",
        default=None,
        help="Module repository root for --task-context mode.",
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

    if args.task_context:
        if not args.prompt_id:
            print("FAILED: --prompt-id is required with --task-context")
            return 1
        if not args.module_root:
            print("FAILED: --module-root is required with --task-context")
            return 1
        module_root = Path(args.module_root).resolve()
        try:
            task_context = build_task_context(
                root=root,
                module=args.module,
                prompt_id=args.prompt_id,
                module_root=module_root,
            )
        except Exception as exc:
            print(f"FAILED: {exc}")
            return 1

        if args.print:
            print(task_context.bootstrap)
            print("--- TASK_CONTEXT_MANIFEST ---")
            print(
                yaml.safe_dump(
                    task_context.manifest,
                    sort_keys=False,
                    allow_unicode=True,
                    width=112,
                ).rstrip()
            )
            return 0

        if args.no_write:
            print(_render_task_context_summary(task_context, output_path=None))
            return 0

        try:
            task_output = write_task_context_archive(
                result=task_context,
                output_dir=output_dir,
            )
        except Exception as exc:
            print(f"FAILED: {exc}")
            return 1
        print(_render_task_context_summary(task_context, output_path=task_output))
        return 0

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
