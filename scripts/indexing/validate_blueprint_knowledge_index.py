from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def validate() -> list[str]:
    errors: list[str] = []

    check = subprocess.run(
        [
            str(ROOT / ".venv_blueprint/bin/python"),
            "scripts/indexing/build_blueprint_knowledge_index.py",
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if check.returncode != 0:
        errors.append("KNOWLEDGE_INDEX_DRIFT:" + check.stdout.strip())

    summary_path = ROOT / "indexes/knowledge_summary.yaml"
    dependencies_path = ROOT / "indexes/dependencies.json"
    files_path = ROOT / "indexes/files.json"
    review_path = ROOT / "indexes/review_candidates.yaml"

    if not summary_path.is_file():
        errors.append("KNOWLEDGE_SUMMARY_MISSING")
    if not dependencies_path.is_file():
        errors.append("DEPENDENCY_INDEX_MISSING")
    if not files_path.is_file():
        errors.append("FILE_INDEX_MISSING")
    if not review_path.is_file():
        errors.append("REVIEW_CANDIDATES_MISSING")

    if dependencies_path.is_file():
        dependencies = json.loads(
            dependencies_path.read_text(encoding="utf-8")
        )
        unknown = dependencies.get("unknown_module_endpoints", [])
        if unknown:
            errors.append(
                "UNKNOWN_MACHINE_MODULE_ENDPOINTS:" + ",".join(unknown)
            )

    if summary_path.is_file():
        summary = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        counts = summary.get("counts", {})
        if counts.get("source_files", 0) <= 0:
            errors.append("SOURCE_FILE_INDEX_EMPTY")
        if counts.get("module_dependency_edges", 0) <= 0:
            errors.append("MODULE_DEPENDENCY_INDEX_EMPTY")

    if files_path.is_file():
        files = json.loads(files_path.read_text(encoding="utf-8"))
        paths = [item["path"] for item in files.get("files", [])]
        if len(paths) != len(set(paths)):
            errors.append("DUPLICATE_FILE_PATHS_IN_INDEX")
        if "tmp.py" in paths:
            errors.append("TRANSIENT_OPERATOR_SCRIPT_INDEXED")
        if any(path.startswith("indexes/") for path in paths):
            errors.append("DERIVED_INDEX_SELF_REFERENCE")

    if review_path.is_file():
        review = yaml.safe_load(review_path.read_text(encoding="utf-8"))
        harmful = review.get("harmful_duplicate_candidates", [])
        if harmful:
            errors.append(
                "HARMFUL_EXACT_DUPLICATE_CANDIDATES:"
                + str(len(harmful))
            )

        unresolved = review.get(
            "unresolved_current_reference_candidates",
            [],
        )
        if unresolved:
            errors.append(
                "ACTIONABLE_UNRESOLVED_REFERENCE_CANDIDATES:"
                + str(len(unresolved))
            )

        no_inbound = review.get("no_inbound_current_documents", [])
        if no_inbound:
            errors.append(
                "GENUINE_NO_INBOUND_CURRENT_DOCUMENTS:"
                + str(len(no_inbound))
            )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR={error}")
        print("BLUEPRINT_KNOWLEDGE_INDEX_VALIDATION=FAIL")
        return 1

    print("BLUEPRINT_KNOWLEDGE_INDEX_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
