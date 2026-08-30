from __future__ import annotations

import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INDEX_ROOT = ROOT / "indexes"
IDENTITY = ROOT / "machine" / "module_identity_registry.yaml"
LEGACY_INDEX = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "legacy_alignment"
    / "index.yaml"
)
DERIVATION_MANIFEST = (
    ROOT
    / "coordination"
    / "templates"
    / "repository_knowledge_template"
    / "derivation_manifest.yaml"
)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _dump(data: dict) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )


def render_modules() -> str:
    source = _load(IDENTITY)
    data = {
        "schema_version": "forprint_blueprint_module_index_v0_1",
        "status": "derived_non_authoritative",
        "generated_from": "machine/module_identity_registry.yaml",
        "identity_authority_state": source["authority_state"],
        "canonical_module_ids": source["canonical_module_ids"],
        "aliases": source["aliases"],
    }
    return _dump(data)


def render_authorities() -> str:
    data = {
        "schema_version": "forprint_blueprint_authority_index_v0_2",
        "status": "derived_non_authoritative",
        "authority_precedence": [
            {
                "role": "effective_release_authority",
                "path": "coordination/releases/current.yaml",
                "state": "current",
            },
            {
                "role": "canonical_module_identity_authority",
                "path": "machine/module_identity_registry.yaml",
                "state": "current",
            },
            {
                "role": "canonical_machine_architecture",
                "path": "machine/",
                "state": "current_curated_surface",
            },
            {
                "role": "canonical_project_structure_standard",
                "path": "coordination/standards/project_structure_standard.md",
                "state": "current",
            },
            {
                "role": "document_taxonomy_policy",
                "path": (
                    "coordination/standards/governance/"
                    "blueprint_document_taxonomy.md"
                ),
                "state": "current",
            },
            {
                "role": "minimal_structure_adoption_profile",
                "path": "coordination/standards/repository_structure_baseline.md",
                "state": "reference_only",
            },
        ],
        "historical_non_authoritative": [
            "coordination/self_coordination/roadmap.yaml",
            "coordination/self_coordination/prompt_queue/index.yaml",
            "coordination/outgoing_prompts/forprint_operational_registry/index.yaml",
            "coordination/internal_work/blueprint/legacy_alignment/",
        ],
        "resolved_normalization": [
            {
                "id": "legacy_operations_registry_prompt_routing",
                "state": "resolved",
                "current_path": (
                    "coordination/outgoing_prompts/"
                    "forprint_operations_control_registry/index.yaml"
                ),
            },
            {
                "id": "accounting_registry_service_identity_split",
                "state": "resolved",
                "canonical_id": "forprint_accounting_registry_service",
            },
            {
                "id": "legacy_human_document_root",
                "state": "resolved_archived_and_consolidated",
                "current_docs_root": "docs/",
            },
            {
                "id": "legacy_prompt_dispatch_control",
                "state": "resolved_historical",
                "current_prompt_authority": "Prompt Queue v0.2 module indexes",
            },
            {
                "id": "repository_knowledge_duplicate_authority",
                "state": "resolved_source_to_derived",
            },
        ],
    }
    return _dump(data)


def render_documents() -> str:
    data = {
        "schema_version": "forprint_blueprint_document_index_v0_1",
        "status": "derived_non_authoritative",
        "current_human_architecture": [
            {
                "path": "docs/architecture/system_architecture.md",
                "role": "system_architecture_explanation",
            },
            {
                "path": "docs/architecture/module_boundaries.md",
                "role": "module_boundary_explanation",
            },
            {
                "path": "docs/architecture/integration_architecture.md",
                "role": "integration_architecture_explanation",
            },
        ],
        "documentation_roots": [
            {"path": "docs/architecture/", "role": "stable_architecture_docs"},
            {"path": "docs/operations/", "role": "runbooks_and_recovery"},
            {"path": "adr/", "role": "decision_history"},
        ],
        "normative_root": "coordination/standards/",
        "historical_root": (
            "coordination/internal_work/blueprint/legacy_alignment/"
        ),
        "retired_roots": ["human/"],
    }
    return _dump(data)


def render_legacy() -> str:
    source = _load(LEGACY_INDEX)
    data = {
        "schema_version": "forprint_blueprint_legacy_index_v0_1",
        "status": "derived_non_authoritative",
        "generated_from": LEGACY_INDEX.relative_to(ROOT).as_posix(),
        "archive": source,
    }
    return _dump(data)


def render_derivations() -> str:
    source = _load(DERIVATION_MANIFEST)
    data = {
        "schema_version": "forprint_blueprint_derivation_index_v0_1",
        "status": "derived_non_authoritative",
        "generated_from": DERIVATION_MANIFEST.relative_to(ROOT).as_posix(),
        "derivations": source["derivations"],
    }
    return _dump(data)


def render_root_index() -> str:
    data = {
        "schema_version": "forprint_blueprint_index_registry_v0_2",
        "status": "derived_non_authoritative",
        "authority": "none",
        "indexes": [
            {
                "id": "modules",
                "path": "indexes/modules.yaml",
                "generated_from": "machine/module_identity_registry.yaml",
            },
            {
                "id": "authorities",
                "path": "indexes/authorities.yaml",
                "generated_from": "explicit_normalization_classification",
            },
            {
                "id": "documents",
                "path": "indexes/documents.yaml",
                "generated_from": "document_taxonomy_and_current_docs",
            },
            {
                "id": "legacy",
                "path": "indexes/legacy.yaml",
                "generated_from": LEGACY_INDEX.relative_to(ROOT).as_posix(),
            },
            {
                "id": "derivations",
                "path": "indexes/derivations.yaml",
                "generated_from": DERIVATION_MANIFEST.relative_to(ROOT).as_posix(),
            },
            {
                "id": "files",
                "path": "indexes/files.json",
                "generated_from": "scripts/indexing/build_blueprint_knowledge_index.py",
            },
            {
                "id": "document_catalog",
                "path": "indexes/document_catalog.yaml",
                "generated_from": "scripts/indexing/build_blueprint_knowledge_index.py",
            },
            {
                "id": "references",
                "path": "indexes/references.json",
                "generated_from": "scripts/indexing/build_blueprint_knowledge_index.py",
            },
            {
                "id": "dependencies",
                "path": "indexes/dependencies.json",
                "generated_from": "scripts/indexing/build_blueprint_knowledge_index.py",
            },
            {
                "id": "review_candidates",
                "path": "indexes/review_candidates.yaml",
                "generated_from": "scripts/indexing/build_blueprint_knowledge_index.py",
            },
            {
                "id": "knowledge_summary",
                "path": "indexes/knowledge_summary.yaml",
                "generated_from": "scripts/indexing/build_blueprint_knowledge_index.py",
            },
            {
                "id": "prompts",
                "path": "indexes/prompts.yaml",
                "generated_from": "scripts/indexing/build_blueprint_specialized_indexes.py",
            },
            {
                "id": "roadmaps",
                "path": "indexes/roadmaps.yaml",
                "generated_from": "scripts/indexing/build_blueprint_specialized_indexes.py",
            },
            {
                "id": "governance",
                "path": "indexes/governance.yaml",
                "generated_from": "scripts/indexing/build_blueprint_specialized_indexes.py",
            },
            {
                "id": "contracts",
                "path": "indexes/contracts.yaml",
                "generated_from": "scripts/indexing/build_blueprint_specialized_indexes.py",
            },
            {
                "id": "source_coverage",
                "path": "indexes/source_coverage.yaml",
                "generated_from": "scripts/indexing/build_blueprint_specialized_indexes.py",
            },
            {
                "id": "incoming_requests",
                "path": "indexes/incoming_requests.yaml",
                "generated_from": "scripts/indexing/build_blueprint_specialized_indexes.py",
            },
        ],
        "planned_indexes": [
            "artifacts",
        ],
    }
    return _dump(data)


def expected_files() -> dict[Path, str]:
    return {
        INDEX_ROOT / "modules.yaml": render_modules(),
        INDEX_ROOT / "authorities.yaml": render_authorities(),
        INDEX_ROOT / "documents.yaml": render_documents(),
        INDEX_ROOT / "legacy.yaml": render_legacy(),
        INDEX_ROOT / "derivations.yaml": render_derivations(),
        INDEX_ROOT / "index.yaml": render_root_index(),
    }


def build(check: bool) -> int:
    failures = []
    for path, content in expected_files().items():
        if check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else ""
            if actual != content:
                failures.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if failures:
        print("INDEX_DRIFT=" + ",".join(failures))
        return 1

    if check:
        print("BLUEPRINT_INDEX_DRIFT_CHECK=PASS")
    else:
        print("BLUEPRINT_INDEX_BUILD=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return build(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
