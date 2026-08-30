from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_INDEX = (
    ROOT
    / "coordination"
    / "internal_work"
    / "blueprint"
    / "legacy_alignment"
    / "index.yaml"
)

RETIRED_MACHINE = {
    "calculator_alignment_review.yaml",
    "crm_alignment_review.yaml",
    "forprint_execution_queue.yaml",
    "integration_gateway_v0_2_review.yaml",
    "library_alignment_review.yaml",
    "module_alignment_execution_plan.yaml",
    "module_alignment_matrix.yaml",
    "module_alignment_report_schema.yaml",
    "module_statuses.yaml",
    "project_directories.yaml",
    "prompt_dispatch_index.yaml",
    "prompt_routes.yaml",
}

CURRENT_DOCS = {
    "docs/architecture/system_architecture.md",
    "docs/architecture/module_boundaries.md",
    "docs/architecture/integration_architecture.md",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate() -> list[str]:
    errors: list[str] = []

    if (ROOT / "human").exists():
        errors.append("LEGACY_HUMAN_ROOT_PRESENT")

    for rel in CURRENT_DOCS:
        if not (ROOT / rel).is_file():
            errors.append(f"CURRENT_DOC_MISSING:{rel}")

    for filename in sorted(RETIRED_MACHINE):
        if (ROOT / "machine" / filename).exists():
            errors.append(f"RETIRED_MACHINE_SURFACE_PRESENT:{filename}")

    if not (ROOT / "machine/module_status_report_schema.yaml").is_file():
        errors.append("CURRENT_MODULE_STATUS_REPORT_SCHEMA_MISSING")

    if not ARCHIVE_INDEX.is_file():
        errors.append("LEGACY_ARCHIVE_INDEX_MISSING")
    else:
        archive = yaml.safe_load(ARCHIVE_INDEX.read_text(encoding="utf-8"))
        records = archive.get("artifacts", [])
        original_paths = {item["original_path"] for item in records}

        human_records = {
            path for path in original_paths if path.startswith("human/")
        }
        if len(human_records) != 25:
            errors.append(
                f"LEGACY_HUMAN_ARCHIVE_COUNT:{len(human_records)}"
            )

        for item in records:
            archived = ROOT / item["archive_path"]
            if not archived.is_file():
                errors.append(
                    f"ARCHIVED_ARTIFACT_MISSING:{item['archive_path']}"
                )
                continue
            if _sha256(archived) != item["sha256"]:
                errors.append(
                    f"ARCHIVED_ARTIFACT_HASH_DRIFT:{item['archive_path']}"
                )

    root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "├── human/" in root_readme:
        errors.append("ROOT_README_ADVERTISES_HUMAN_ROOT")
    if "`accounting_registry_service`" in root_readme:
        errors.append("ROOT_README_USES_LEGACY_ACCOUNTING_ID")

    detail_map = (
        ROOT / "diagrams/system_detail_map.mmd"
    ).read_text(encoding="utf-8")
    if "OperationalRegistry[ForPrint Operational Registry<br/>" in detail_map:
        errors.append("SYSTEM_DETAIL_MAP_USES_OLD_OPERATIONS_NAME")
    if "Accounting[Accounting Registry Service<br/>" in detail_map:
        errors.append("SYSTEM_DETAIL_MAP_USES_OLD_ACCOUNTING_NAME")

    identity = yaml.safe_load(
        (ROOT / "machine/module_identity_registry.yaml").read_text(
            encoding="utf-8"
        )
    )
    if identity.get("authority_state") != "canonical":
        errors.append("MODULE_IDENTITY_AUTHORITY_NOT_CANONICAL")

    derivation_check = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/sync_repository_knowledge_distribution.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if derivation_check.returncode != 0:
        errors.append(
            "REPOSITORY_KNOWLEDGE_DISTRIBUTION_DRIFT:"
            + derivation_check.stdout.strip()
        )

    index_check = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/build_blueprint_index.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if index_check.returncode != 0:
        errors.append("BLUEPRINT_INDEX_DRIFT:" + index_check.stdout.strip())

    knowledge_check = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/validate_blueprint_knowledge_index.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if knowledge_check.returncode != 0:
        errors.append(
            "BLUEPRINT_KNOWLEDGE_INDEX_INVALID:"
            + knowledge_check.stdout.strip()
        )

    specialized_check = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/validate_blueprint_specialized_indexes.py",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if specialized_check.returncode != 0:
        errors.append(
            "BLUEPRINT_SPECIALIZED_INDEX_INVALID:"
            + specialized_check.stdout.strip()
        )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR={error}")
        print("BLUEPRINT_SEMANTIC_STRUCTURE=FAIL")
        return 1

    print("BLUEPRINT_SEMANTIC_STRUCTURE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
