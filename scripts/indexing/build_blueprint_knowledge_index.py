from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INDEX_ROOT = ROOT / "indexes"

SKIP_ROOTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv_blueprint",
    "indexes",
    "node_modules",
    "reports",
    "tmp",
}
SKIP_PARTS = {"__pycache__"}
SKIP_FILENAMES = {"tmp.py"}

TEXT_SUFFIXES = {
    ".bash",
    ".cfg",
    ".conf",
    ".css",
    ".csv",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".lock",
    ".markdown",
    ".md",
    ".mjs",
    ".mmd",
    ".ps1",
    ".py",
    ".scss",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsv",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".zsh",
}
MAX_TEXT_BYTES = 5_000_000

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ROOT_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"((?:adr|coordination|diagrams|docs|machine|module_guides|scripts|tests|tools)/"
    r"[A-Za-z0-9_./@+\-*?<>:{}]+)"
)
TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яІіЇїЄє0-9_]+")

PSEUDO_MODULE_ENDPOINTS = {"any_module", "external_1c"}

SEMANTIC_NONPATH_TOKENS = {
    "coordination/business",
    "coordination/framework",
    "coordination/governance",
    "coordination/navigation",
    "coordination/release",
    "coordination/self-check",
    "coordination/self-validation",
    "diagrams/photos/video",
    "docs/code",
    "docs/metadata",
    "docs/refactors/contracts/DB/security/external",
    "docs/standards/roadmaps",
    "machine/material/location/task",
    "machine/repository",
    "machine/scanner",
    "machine/standard",
    "machine/workstation",
    "scripts/CLIs",
    "scripts/actions",
    "scripts/actions/presets",
    "scripts/documents",
    "scripts/recovery",
    "scripts/tests",
    "scripts/tests/tools",
    "tests/checks/governance",
    "tests/evidence",
    "tests/rollback",
    "tests/tools",
    "tools/dependencies",
    "tools/files",
}

TARGET_MODULE_STANDARD_SOURCES = {
    "coordination/standards/governance/module_coordination_sync_protocol_v0_1.md",
    "coordination/standards/make_command_standard.md",
    "coordination/standards/module_outgoing_prompt_pull_protocol.md",
}

INDEXER_RULE_LITERAL_TOKENS = {
    "coordination/blueprint_awareness/",
    "coordination/completion_packets/",
    "coordination/repository_knowledge/direction/module_self_view/.gitkeep",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _yaml_text(data: dict) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def _json_text(data: dict | list) -> str:
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=False,
    ) + "\n"


def _iter_source_files() -> list[Path]:
    result: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if not rel.parts:
            continue
        if rel.parts[0] in SKIP_ROOTS:
            continue
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.name in SKIP_FILENAMES:
            continue
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(ROOT).as_posix())


def _is_text(path: Path) -> bool:
    if path.stat().st_size > MAX_TEXT_BYTES:
        return False
    if path.name in {"Dockerfile", "LICENSE", "Makefile", "README"}:
        return True
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if not path.suffix and path.stat().st_size <= 300_000:
        try:
            path.read_bytes()[:8192].decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False
    return False


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _category(rel: str) -> str:
    if rel == "coordination/releases/current.yaml":
        return "effective_release_authority"
    if rel.startswith("machine/"):
        return "machine_architecture_or_control"
    if rel.startswith("docs/architecture/"):
        return "architecture_documentation"
    if rel.startswith("docs/operations/"):
        return "operations_documentation"
    if rel.startswith("docs/"):
        return "documentation"
    if rel.startswith("coordination/standards/"):
        return "normative_standard_or_policy"
    if rel.startswith("coordination/internal_work/blueprint/legacy_alignment/"):
        return "historical_legacy_alignment"
    if rel.startswith("coordination/internal_work/"):
        return "internal_work_evidence"
    if rel.startswith("coordination/outgoing_prompts/"):
        return "prompt_lifecycle"
    if rel.startswith("coordination/roadmaps/"):
        return "roadmap"
    if rel.startswith("coordination/releases/"):
        return "release_history_or_evidence"
    if rel.startswith("coordination/"):
        return "coordination"
    if rel.startswith("adr/"):
        return "architecture_decision_history"
    if rel.startswith("scripts/"):
        return "tooling"
    if rel.startswith("tests/"):
        return "test"
    if rel.startswith("diagrams/"):
        return "diagram"
    if rel.startswith("module_guides/"):
        return "generated_module_guide"
    if rel.startswith("tools/"):
        return "support_tooling"
    return "other"


def _lifecycle(rel: str) -> str:
    if rel.startswith("coordination/internal_work/"):
        return "internal_work_non_authoritative_evidence"
    if rel.startswith("coordination/self_coordination/"):
        return "historical_non_authoritative_projection"
    if rel.startswith("adr/"):
        return "decision_history"
    if "/completed/" in rel and rel.startswith("coordination/outgoing_prompts/"):
        return "completed_execution_contract"
    if "/approved/" in rel and rel.startswith("coordination/outgoing_prompts/"):
        return "released_execution_contract"
    if "/drafts/" in rel and rel.startswith("coordination/outgoing_prompts/"):
        return "draft"
    if rel.startswith("coordination/repository_knowledge/"):
        return "repository_knowledge_snapshot_or_protocol"
    if rel.startswith("docs/"):
        return "current_explanatory"
    if rel.startswith("machine/"):
        return "current_machine_surface"
    if rel.startswith("coordination/standards/"):
        return "current_normative"
    if rel == "coordination/releases/current.yaml":
        return "effective_current"
    return "current_or_supporting"


def _authority_class(rel: str) -> str:
    if rel == "coordination/releases/current.yaml":
        return "effective_release_authority"
    if rel == "machine/module_identity_registry.yaml":
        return "canonical_module_identity_authority"
    if rel.startswith("machine/"):
        return "machine_source"
    if rel.startswith("coordination/standards/"):
        return "normative_source"
    if rel.startswith("coordination/internal_work/"):
        return "history_or_evidence_only"
    if rel.startswith("coordination/repository_knowledge/"):
        return "snapshot_or_protocol_source"
    if rel.startswith("docs/"):
        return "explanatory_non_authoritative"
    if rel.startswith("indexes/"):
        return "derived_non_authoritative"
    return "contextual_or_supporting"


def _document_candidate(rel: str) -> bool:
    suffix = Path(rel).suffix.lower()
    if suffix not in {".json", ".md", ".markdown", ".yaml", ".yml"}:
        return False
    return rel.startswith(
        (
            "adr/",
            "coordination/",
            "docs/",
            "machine/",
        )
    )


def _extract_title(text: str, rel: str) -> str | None:
    if rel.endswith((".md", ".markdown")):
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return None


def _normalize_reference(raw: str) -> str:
    value = raw.strip().strip("`'\"")
    if " " in value and not value.startswith(("http://", "https://")):
        value = value.split()[0]
    value = value.split("#", 1)[0]
    return value.rstrip(".,;:)]}'\"")


def _is_external_reference(raw: str) -> bool:
    lowered = raw.lower()
    return lowered.startswith(
        (
            "http://",
            "https://",
            "mailto:",
            "ssh://",
            "git@",
        )
    )


def _retired_paths() -> set[str]:
    archive = (
        ROOT
        / "coordination"
        / "internal_work"
        / "blueprint"
        / "legacy_alignment"
        / "index.yaml"
    )
    if not archive.is_file():
        return set()
    data = _yaml(archive)
    return {
        item["original_path"]
        for item in data.get("artifacts", [])
        if isinstance(item.get("original_path"), str)
    }


def _lifecycle_replacement(value: str) -> str | None:
    candidates: list[str] = []
    if "/approved/" in value:
        candidates.append(value.replace("/approved/", "/completed/", 1))
    if "/drafts/" in value:
        candidates.append(value.replace("/drafts/", "/approved/", 1))
        candidates.append(value.replace("/drafts/", "/completed/", 1))

    for candidate in candidates:
        if (ROOT / candidate).exists():
            return candidate
    return None


def _is_module_coordination_reference(value: str) -> bool:
    if value.startswith(
        (
            "coordination/status/",
            "coordination/prompts/",
        )
    ):
        return True
    return value in {
        "coordination/status",
        "coordination/prompts/received/",
        "coordination/blueprint_source.yaml",
        "coordination/blueprint_awareness/document_review_ledger.yaml",
        "coordination/standards/blueprint_standards_snapshot.yaml",
    }


def _is_planned_runtime_surface(value: str) -> bool:
    return value.startswith(
        (
            "coordination/completion_outbox/records",
            "coordination/completion_packets/records",
            "coordination/prompt_execution_events/records",
            "coordination/execution_preflight/records",
        )
    )


def _is_example_like_reference(source_rel: str, value: str) -> bool:
    lowered = value.lower()
    if any(token in lowered for token in ("demo", "example")):
        return True
    if value in {
        "scripts/name.py",
        "docs/code.",
        "tests/rollback.",
        "coordination/reports/completion/example.md",
    }:
        return True
    if source_rel.startswith(
        (
            "coordination/templates/",
            "tools/module_standards_template/",
            "tools/module_coordination_template/",
            "tools/module_prompt_pull_template/",
            "tools/completion_packet_template/",
        )
    ):
        return True
    return False


def _is_policy_example_source(source_rel: str) -> bool:
    return source_rel in {
        "coordination/standards/governance/folder_architecture_policy.md",
        "coordination/standards/governance/module_development_roadmap_policy.md",
        "coordination/standards/project_structure_standard.md",
        "coordination/standards/testing_and_check_report_standard.md",
        "coordination/standards/automation/work_package_and_evidence_report_standard_v0_1.md",
    }


def _is_target_module_relative_reference(source_rel: str, value: str) -> bool:
    if not source_rel.startswith(
        (
            "coordination/outgoing_prompts/",
            "coordination/prompt_contracts/",
        )
    ):
        return False

    if value.startswith(
        (
            "docs/",
            "scripts/",
            "tests/",
            "tools/",
            "machine/",
            "coordination/",
        )
    ):
        return True

    return _is_module_coordination_reference(value)


def _structured_pointer(value: str) -> tuple[str, str] | None:
    if ":" not in value or "::" in value:
        return None
    base, pointer = value.split(":", 1)
    if not base or not pointer:
        return None
    if (ROOT / base).is_file():
        return base, pointer
    return None


def _pytest_nodeid(value: str) -> tuple[str, str] | None:
    if "::" not in value:
        return None
    base, nodeid = value.split("::", 1)
    if base.endswith(".py") and nodeid and (ROOT / base).is_file():
        return base, nodeid
    return None


def _is_historical_alias_prompt_source(source_rel: str) -> bool:
    return source_rel.startswith(
        "coordination/outgoing_prompts/forprint_operational_registry/"
    )


def _is_incoming_request_evidence_source(source_rel: str) -> bool:
    return source_rel.startswith("coordination/incoming_requests/")


def _is_module_snapshot_source(source_rel: str) -> bool:
    return source_rel.startswith("coordination/module_docs_snapshots/")


def _is_blueprint_detail_roadmap_source(source_rel: str) -> bool:
    return source_rel.startswith(
        "coordination/roadmaps/details/forprint_system_blueprint/"
    )


def _is_target_module_completion_evidence(
    source_rel: str,
    value: str,
) -> bool:
    if not value.startswith("coordination/reports/completion/"):
        return False
    return source_rel.startswith(
        (
            "coordination/outgoing_prompts/",
            "coordination/roadmaps/",
            "coordination/review_packets/",
        )
    )


def _is_declared_registry_reference(source_rel: str) -> bool:
    return (
        source_rel
        == "coordination/registry/coordination_source_registry_v0_1.yaml"
    )


def _is_target_module_standard_reference(
    source_rel: str,
    value: str,
) -> bool:
    if source_rel not in TARGET_MODULE_STANDARD_SOURCES:
        return False
    return value.startswith(
        (
            "scripts/",
            "coordination/blueprint_awareness/",
            "coordination/instruction_intake/",
        )
    )


def _is_target_module_template_validator_reference(
    source_rel: str,
    value: str,
) -> bool:
    return (
        source_rel == "scripts/validate_module_standards_template.py"
        and value.startswith("scripts/")
    )


def _is_module_completion_packet_reference(
    source_rel: str,
    value: str,
) -> bool:
    return (
        source_rel == "scripts/coordination/completion_intake_check.py"
        and value.startswith("coordination/completion_packets/")
    )


def _is_recovery_absence_reference(source_rel: str, value: str) -> bool:
    return (
        source_rel
        == "docs/operations/blueprint_repository_knowledge_snapshot_recovery.md"
        and value
        == "coordination/repository_knowledge/direction/module_self_view/.gitkeep"
    )


def _is_indexer_rule_literal_reference(source_rel: str, value: str) -> bool:
    return (
        source_rel == "scripts/indexing/build_blueprint_knowledge_index.py"
        and value in INDEXER_RULE_LITERAL_TOKENS
    )


def _discoverability_class(rel: str) -> str | None:
    if rel.startswith("coordination/standards/"):
        return "standards_governance_index"
    if rel.startswith("coordination/roadmaps/details/forprint_system_blueprint/"):
        return "blueprint_roadmap_detail_tree"
    if rel.startswith("coordination/module_policy/"):
        return "module_policy_tree"
    if rel.startswith("coordination/templates/"):
        return "coordination_template_root"
    if rel.startswith("coordination/incoming_requests/"):
        return "incoming_request_routing_index"
    if rel.startswith("docs/"):
        return "document_catalog"
    return None


def _resolve_reference(
    source_rel: str,
    raw: str,
    retired: set[str],
) -> tuple[str, str | None, str | None]:
    value = _normalize_reference(raw)
    if not value or _is_external_reference(value):
        return "external_or_empty", None, None

    if any(token in value for token in ("<", ">", "{", "}")):
        return "template_or_placeholder", None, None

    pointer = _structured_pointer(value)
    if pointer is not None:
        base, fragment = pointer
        return "resolved_structured_pointer", base, fragment

    nodeid = _pytest_nodeid(value)
    if nodeid is not None:
        base, fragment = nodeid
        return "resolved_pytest_nodeid", base, fragment

    if "*" in value or "?" in value:
        try:
            base = ROOT
            matches = sorted(
                item.relative_to(ROOT).as_posix()
                for item in base.glob(value)
                if item.exists()
            )
        except (NotImplementedError, ValueError):
            matches = []
        return (
            "resolved_pattern" if matches else "unresolved_pattern",
            None,
            ",".join(matches[:20]) if matches else None,
        )

    root_candidate = ROOT / value
    if root_candidate.exists():
        target = root_candidate.relative_to(ROOT).as_posix()
        kind = "resolved_file" if root_candidate.is_file() else "resolved_directory"
        return kind, target, None

    source_path = ROOT / source_rel
    relative_candidate = source_path.parent / value
    try:
        relative_candidate = relative_candidate.resolve()
        relative_candidate.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        relative_candidate = None

    if relative_candidate is not None and relative_candidate.exists():
        target = relative_candidate.relative_to(ROOT.resolve()).as_posix()
        kind = (
            "resolved_relative_file"
            if relative_candidate.is_file()
            else "resolved_relative_directory"
        )
        return kind, target, None

    if value in retired or value.startswith("human/"):
        return "retired_path_mention", None, None

    if _is_historical_alias_prompt_source(source_rel):
        return "historical_alias_prompt_reference", None, None

    if source_rel.startswith("coordination/self_coordination/"):
        return "historical_projection_reference", None, None

    if _is_incoming_request_evidence_source(source_rel):
        return "incoming_request_module_evidence_reference", None, None

    if _is_module_snapshot_source(source_rel):
        return "module_document_snapshot_reference", None, None

    if _is_blueprint_detail_roadmap_source(source_rel):
        return "blueprint_roadmap_planning_reference", None, None

    if source_rel.startswith("coordination/directives/modules/"):
        return "target_module_directive_reference", None, None

    if _is_target_module_completion_evidence(source_rel, value):
        return "target_module_completion_evidence_reference", None, None

    if _is_declared_registry_reference(source_rel):
        return "declared_registry_availability_reference", None, None

    if _is_target_module_standard_reference(source_rel, value):
        return "target_module_standard_reference", None, None

    if _is_target_module_template_validator_reference(source_rel, value):
        return "target_module_template_reference", None, None

    if _is_module_completion_packet_reference(source_rel, value):
        return "module_completion_packet_reference", None, None

    if _is_recovery_absence_reference(source_rel, value):
        return "recovery_absence_reference", None, None

    if _is_indexer_rule_literal_reference(source_rel, value):
        return "indexer_rule_literal_reference", None, None

    if value in SEMANTIC_NONPATH_TOKENS:
        return "conceptual_nonpath_reference", None, None

    if source_rel.startswith("coordination/internal_work/"):
        return "historical_or_internal_evidence_reference", None, None

    if source_rel.startswith("adr/"):
        return "historical_decision_reference", None, None

    if source_rel.startswith("coordination/repository_knowledge/"):
        return "repository_knowledge_snapshot_reference", None, None

    if source_rel.startswith("tests/"):
        return "test_fixture_or_assertion_reference", None, None

    if _is_example_like_reference(source_rel, value):
        return "template_or_example_reference", None, None

    if _is_planned_runtime_surface(value):
        return "planned_or_module_runtime_surface_reference", None, None

    if source_rel.startswith("coordination/module_sources/") and (
        _is_module_coordination_reference(value)
        or value == "coordination/reports/index.yaml"
    ):
        return "external_module_coordination_reference", None, None

    if _is_target_module_relative_reference(source_rel, value):
        return "target_module_relative_reference", None, None

    if _is_module_coordination_reference(value):
        return "module_coordination_contract_reference", None, None

    replacement = _lifecycle_replacement(value)
    if replacement is not None:
        return "lifecycle_moved_reference", replacement, replacement

    if _is_policy_example_source(source_rel):
        return "policy_example_reference", None, None

    return "unresolved_candidate", None, None

def _reference_candidates(text: str) -> set[str]:
    candidates: set[str] = set()
    for match in MARKDOWN_LINK_RE.finditer(text):
        candidates.add(match.group(1))
    for match in ROOT_PATH_RE.finditer(text):
        candidates.add(match.group(1))
    return candidates


def _declared_derivation_pairs() -> set[tuple[str, str]]:
    manifest = (
        ROOT
        / "coordination"
        / "templates"
        / "repository_knowledge_template"
        / "derivation_manifest.yaml"
    )
    if not manifest.is_file():
        return set()
    data = _yaml(manifest)
    return {
        (item["source"], item["derived"])
        for item in data.get("derivations", [])
    }


def _duplicate_classification(
    paths: list[str],
    size_bytes: int,
    declared_pairs: set[tuple[str, str]],
) -> str:
    if size_bytes == 0:
        return "structural_or_empty_duplicate"

    if all(Path(path).name == "__init__.py" for path in paths):
        return "python_package_marker_duplicate"

    if len(paths) == 2:
        left, right = paths
        if (left, right) in declared_pairs or (right, left) in declared_pairs:
            return "declared_source_derived_pair"

        snapshot_paths = [
            path
            for path in paths
            if path.startswith("coordination/prompt_contracts/")
            and path.endswith("/source_prompt_snapshot.md")
        ]
        prompt_paths = [
            path
            for path in paths
            if path.startswith("coordination/outgoing_prompts/")
            and path.endswith(".md")
        ]
        if len(snapshot_paths) == 1 and len(prompt_paths) == 1:
            return "immutable_prompt_source_snapshot"

    if all(
        path.startswith(
            "coordination/internal_work/blueprint/legacy_alignment/"
        )
        for path in paths
    ):
        return "historical_duplicate"

    if all(Path(path).name == ".gitkeep" for path in paths):
        return "structural_placeholder"

    return "review_exact_duplicate"

def _machine_module_dependencies() -> tuple[list[dict], list[str]]:
    identity = _yaml(ROOT / "machine/module_identity_registry.yaml")
    canonical = set(identity.get("canonical_module_ids", []))
    allowed = canonical | PSEUDO_MODULE_ENDPOINTS

    evidence_by_edge: dict[tuple[str, str], list[dict]] = {}
    unknown: set[str] = set()

    flows = _yaml(ROOT / "machine/data_flows.yaml").get("data_flows", [])
    for item in flows:
        source = item.get("source")
        target = item.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        evidence_by_edge.setdefault((source, target), []).append(
            {
                "kind": "data_flow",
                "id": item.get("id"),
                "status": item.get("status"),
                "contract": item.get("contract"),
                "data_objects": item.get("data_objects", []),
            }
        )
        unknown.update({source, target} - allowed)

    contracts = _yaml(ROOT / "machine/contracts.yaml").get("contracts", [])
    for item in contracts:
        source = item.get("provider")
        target = item.get("consumer")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        evidence_by_edge.setdefault((source, target), []).append(
            {
                "kind": "contract",
                "id": item.get("id"),
                "status": item.get("status"),
                "data_objects": item.get("data_objects", []),
            }
        )
        unknown.update({source, target} - allowed)

    ownership = _yaml(ROOT / "machine/ownership.yaml").get("ownership", {})
    for object_id, item in ownership.items():
        if not isinstance(item, dict):
            continue
        owner = item.get("owner")
        consumers = item.get("consumers", [])
        if not isinstance(owner, str) or not isinstance(consumers, list):
            continue
        for consumer in consumers:
            if not isinstance(consumer, str):
                continue
            evidence_by_edge.setdefault((owner, consumer), []).append(
                {
                    "kind": "ownership_consumption",
                    "data_object": object_id,
                }
            )
            unknown.update({owner, consumer} - allowed)

    edges = [
        {
            "source": source,
            "target": target,
            "evidence": evidence,
        }
        for (source, target), evidence in sorted(evidence_by_edge.items())
    ]
    return edges, sorted(unknown)


def collect() -> dict[str, str]:
    files = _iter_source_files()
    text_by_path: dict[str, str] = {}
    records: list[dict] = []
    hash_groups: dict[str, list[str]] = {}

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        size = path.stat().st_size
        digest = _sha256(path)
        is_text = _is_text(path)

        text = _read_text(path) if is_text else ""
        if is_text:
            text_by_path[rel] = text

        record = {
            "path": rel,
            "category": _category(rel),
            "lifecycle": _lifecycle(rel),
            "authority_class": _authority_class(rel),
            "size_bytes": size,
            "sha256": digest,
            "text": is_text,
            "line_count": (
                text.count("\n") + (1 if text else 0)
                if is_text
                else None
            ),
        }
        records.append(record)
        hash_groups.setdefault(digest, []).append(rel)

    retired = _retired_paths()
    references: list[dict] = []
    file_edges: set[tuple[str, str]] = set()
    inbound: dict[str, set[str]] = {}
    unresolved: list[dict] = []
    retired_mentions: list[dict] = []

    for source_rel, source_text in sorted(text_by_path.items()):
        for raw in sorted(_reference_candidates(source_text)):
            classification, target, detail = _resolve_reference(
                source_rel,
                raw,
                retired,
            )
            record = {
                "source": source_rel,
                "raw": raw,
                "classification": classification,
                "target": target,
            }
            if detail is not None:
                record["detail"] = detail
            references.append(record)

            if classification in {
                "resolved_file",
                "resolved_relative_file",
            } and target is not None:
                file_edges.add((source_rel, target))
                inbound.setdefault(target, set()).add(source_rel)
            elif classification == "unresolved_candidate":
                unresolved.append(record)
            elif classification == "retired_path_mention":
                retired_mentions.append(record)

    module_edges, unknown_module_endpoints = _machine_module_dependencies()

    declared_pairs = _declared_derivation_pairs()
    duplicate_groups: list[dict] = []
    record_by_path = {item["path"]: item for item in records}

    for digest, paths in sorted(hash_groups.items()):
        if len(paths) <= 1:
            continue
        paths = sorted(paths)
        size_bytes = record_by_path[paths[0]]["size_bytes"]
        duplicate_groups.append(
            {
                "sha256": digest,
                "size_bytes": size_bytes,
                "paths": paths,
                "classification": _duplicate_classification(
                    paths,
                    size_bytes,
                    declared_pairs,
                ),
            }
        )

    duplicate_groups.sort(
        key=lambda item: (
            item["classification"],
            -len(item["paths"]),
            item["paths"][0],
        )
    )

    documents: list[dict] = []
    for record in records:
        rel = record["path"]
        if not _document_candidate(rel):
            continue
        text = text_by_path.get(rel, "")
        documents.append(
            {
                "path": rel,
                "category": record["category"],
                "lifecycle": record["lifecycle"],
                "authority_class": record["authority_class"],
                "title": _extract_title(text, rel),
                "sha256": record["sha256"],
                "inbound_reference_count": len(inbound.get(rel, set())),
            }
        )

    no_inbound: list[dict] = []
    structurally_discoverable_no_inbound: list[dict] = []
    for item in documents:
        if item["inbound_reference_count"] != 0:
            continue
        if item["lifecycle"] in {
            "historical_non_authoritative",
            "historical_non_authoritative_projection",
            "internal_work_non_authoritative_evidence",
            "decision_history",
        }:
            continue

        discoverability = _discoverability_class(item["path"])
        record = {
            "path": item["path"],
            "category": item["category"],
            "lifecycle": item["lifecycle"],
        }
        if discoverability is None:
            no_inbound.append(record)
        else:
            record["discoverability"] = discoverability
            structurally_discoverable_no_inbound.append(record)

    reference_counts: dict[str, int] = {}
    for item in references:
        key = item["classification"]
        reference_counts[key] = reference_counts.get(key, 0) + 1

    duplicate_counts: dict[str, int] = {}
    for item in duplicate_groups:
        key = item["classification"]
        duplicate_counts[key] = duplicate_counts.get(key, 0) + 1

    harmful_duplicate_candidates = [
        item
        for item in duplicate_groups
        if item["classification"] == "review_exact_duplicate"
    ]

    nonblocking_reference_counts = {
        key: value
        for key, value in sorted(reference_counts.items())
        if key
        in {
            "historical_or_internal_evidence_reference",
            "historical_decision_reference",
            "repository_knowledge_snapshot_reference",
            "test_fixture_or_assertion_reference",
            "template_or_example_reference",
            "planned_or_module_runtime_surface_reference",
            "external_module_coordination_reference",
            "target_module_relative_reference",
            "module_coordination_contract_reference",
            "lifecycle_moved_reference",
            "policy_example_reference",
            "retired_path_mention",
            "resolved_structured_pointer",
            "resolved_pytest_nodeid",
            "historical_alias_prompt_reference",
            "historical_projection_reference",
            "incoming_request_module_evidence_reference",
            "module_document_snapshot_reference",
            "blueprint_roadmap_planning_reference",
            "target_module_directive_reference",
            "target_module_completion_evidence_reference",
            "declared_registry_availability_reference",
            "target_module_standard_reference",
            "target_module_template_reference",
            "module_completion_packet_reference",
            "recovery_absence_reference",
            "indexer_rule_literal_reference",
            "conceptual_nonpath_reference",
        }
    }

    files_payload = {
        "schema_version": "forprint_blueprint_file_index_v0_1",
        "status": "derived_non_authoritative",
        "source_scope": {
            "excluded_roots": sorted(SKIP_ROOTS),
            "excluded_files": sorted(SKIP_FILENAMES),
            "reason": (
                "Exclude derived indexes, volatile reports/tmp and runtime/cache "
                "surfaces to keep the source index deterministic."
            ),
        },
        "files": records,
    }

    documents_payload = {
        "schema_version": "forprint_blueprint_document_catalog_v0_1",
        "status": "derived_non_authoritative",
        "documents": documents,
    }

    references_payload = {
        "schema_version": "forprint_blueprint_reference_index_v0_1",
        "status": "derived_non_authoritative",
        "classification_counts": dict(sorted(reference_counts.items())),
        "references": references,
        "backlinks": [
            {
                "target": target,
                "sources": sorted(sources),
                "source_count": len(sources),
            }
            for target, sources in sorted(inbound.items())
        ],
    }

    dependencies_payload = {
        "schema_version": "forprint_blueprint_dependency_index_v0_1",
        "status": "derived_non_authoritative",
        "file_dependencies": [
            {"source": source, "target": target}
            for source, target in sorted(file_edges)
        ],
        "module_dependencies": module_edges,
        "unknown_module_endpoints": unknown_module_endpoints,
    }

    review_payload = {
        "schema_version": "forprint_blueprint_index_review_candidates_v0_3",
        "status": "derived_non_authoritative",
        "semantics": (
            "Only unresolved_current_reference_candidates, genuine no-inbound "
            "documents and review_exact_duplicate groups require semantic attention by "
            "default. Historical, module-relative, structured-pointer, fixture, template, "
            "planned-surface, lifecycle-moved and structurally discoverable references "
            "are classified as nonblocking context."
        ),
        "unresolved_current_reference_candidates": unresolved,
        "retired_path_mentions": retired_mentions,
        "nonblocking_reference_classifications": nonblocking_reference_counts,
        "exact_duplicate_groups": duplicate_groups,
        "harmful_duplicate_candidates": harmful_duplicate_candidates,
        "no_inbound_current_documents": no_inbound,
        "structurally_discoverable_no_inbound_documents": (
            structurally_discoverable_no_inbound
        ),
    }

    summary_payload = {
        "schema_version": "forprint_blueprint_knowledge_index_summary_v0_3",
        "status": "derived_non_authoritative",
        "counts": {
            "source_files": len(records),
            "text_files": len(text_by_path),
            "documents": len(documents),
            "references": len(references),
            "resolved_file_dependencies": len(file_edges),
            "module_dependency_edges": len(module_edges),
            "unresolved_reference_candidates": len(unresolved),
            "retired_path_mentions": len(retired_mentions),
            "classified_nonblocking_reference_count": sum(
                nonblocking_reference_counts.values()
            ),
            "exact_duplicate_groups": len(duplicate_groups),
            "harmful_duplicate_candidates": len(harmful_duplicate_candidates),
            "no_inbound_current_documents": len(no_inbound),
            "structurally_discoverable_no_inbound_documents": len(
                structurally_discoverable_no_inbound
            ),
        },
        "reference_classifications": dict(sorted(reference_counts.items())),
        "duplicate_classifications": dict(sorted(duplicate_counts.items())),
        "quality": {
            "unknown_module_endpoint_count": len(unknown_module_endpoints),
            "unknown_module_endpoints": unknown_module_endpoints,
            "note": (
                "Scope-aware reference classes keep module-repository, historical, "
                "fixture, template and lifecycle-moved references out of the actionable "
                "queue. Indexer implementation-rule literals are also classified as nonblocking. "
                "Structurally indexed standards, roadmap details, templates, module-policy "
                "documents, incoming-request routes and authored docs are "
                "separated from genuine no-inbound/orphan candidates. Unknown current "
                "machine module endpoints remain a hard consistency failure."
            ),
        },
    }

    return {
        "files.json": _json_text(files_payload),
        "document_catalog.yaml": _yaml_text(documents_payload),
        "references.json": _json_text(references_payload),
        "dependencies.json": _json_text(dependencies_payload),
        "review_candidates.yaml": _yaml_text(review_payload),
        "knowledge_summary.yaml": _yaml_text(summary_payload),
    }


def build(check: bool) -> int:
    expected = collect()
    drift: list[str] = []

    for name, content in expected.items():
        path = INDEX_ROOT / name
        if check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else ""
            if actual != content:
                drift.append(f"indexes/{name}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if drift:
        print("BLUEPRINT_KNOWLEDGE_INDEX_DRIFT=" + ",".join(drift))
        return 1

    if check:
        print("BLUEPRINT_KNOWLEDGE_INDEX_CHECK=PASS")
    else:
        print("BLUEPRINT_KNOWLEDGE_INDEX_BUILD=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return build(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
