#!/usr/bin/env python3
"""Validate curated generator contracts against current generator inventory."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/automation/generator_derivation_contract_v0_1.yaml"
REGISTRY = ROOT / "coordination/registry/generator_derivation_registry_v0_1.yaml"
INVENTORY = ROOT / "indexes/generator_inventory.yaml"

CRITICAL = {
    "scripts/indexing/build_blueprint_index.py",
    "scripts/indexing/build_blueprint_knowledge_index.py",
    "scripts/indexing/build_blueprint_specialized_indexes.py",
    "scripts/coordination/build_project_context_archive.py",
    "scripts/coordination/build_context_bundle.py",
    "scripts/generate_mermaid.py",
    "scripts/generate_module_guides.py",
    "scripts/generate_module_policy_docs.py",
}

REQUIRED = {
    "id",
    "script",
    "owner",
    "derivation_class",
    "output_state",
    "authority",
    "source_scope",
    "check_mode",
    "apply_mode",
    "make_check_allowed",
    "freshness_contract",
    "review_status",
}


def fail(message: str) -> int:
    print(f"GENERATOR_CONTRACT_VALIDATION=FAIL {message}")
    return 1


def main() -> int:
    for path in (CONTRACT, REGISTRY, INVENTORY):
        if not path.is_file():
            return fail(f"missing={path.relative_to(ROOT)}")

    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    rows = registry.get("generators", [])

    by_script = {}
    ids = set()
    for row in rows:
        missing = sorted(REQUIRED - set(row))
        if missing:
            return fail(f"missing_fields script={row.get('script')} fields={','.join(missing)}")
        if row["id"] in ids:
            return fail(f"duplicate_id={row['id']}")
        ids.add(row["id"])
        if row["script"] in by_script:
            return fail(f"duplicate_script={row['script']}")
        by_script[row["script"]] = row

        if row["authority"] != "none":
            return fail(f"generated_output_claims_authority={row['script']}")
        if not (ROOT / row["script"]).is_file():
            return fail(f"registered_script_missing={row['script']}")

        if row["output_state"] == "tracked_derived" and row["check_mode"] == "missing":
            if row["make_check_allowed"] is not False:
                return fail(
                    "tracked_without_check_must_be_forbidden_from_make_check=" + row["script"]
                )
            if not row.get("remediation_required"):
                return fail("tracked_without_check_missing_remediation=" + row["script"])

    missing_critical = sorted(CRITICAL - set(by_script))
    if missing_critical:
        return fail("critical_unregistered=" + ",".join(missing_critical))

    inventory_rows = {row["script"]: row for row in inventory.get("generator_candidates", [])}
    not_discovered = sorted(set(by_script) - set(inventory_rows))
    if not_discovered:
        return fail("registered_not_discovered=" + ",".join(not_discovered))

    unregistered = sorted(set(inventory_rows) - set(by_script))
    expected = inventory.get("summary", {}).get("unregistered_candidate_count")
    if expected != len(unregistered):
        return fail("unregistered_summary_mismatch")

    critical_untracked = sorted(
        script for script in CRITICAL if not inventory_rows[script]["git_tracked"]
    )

    print("GENERATOR_CONTRACT_VALIDATION=PASS")
    print(f"REGISTERED_GENERATORS={len(by_script)}")
    print(f"DISCOVERED_GENERATOR_CANDIDATES={len(inventory_rows)}")
    print(f"UNREGISTERED_VISIBLE_GAPS={len(unregistered)}")
    print(f"CRITICAL_UNTRACKED_VISIBLE_STATE={len(critical_untracked)}")
    if unregistered:
        print("UNREGISTERED_SAMPLE=" + ",".join(unregistered[:20]))
    if critical_untracked:
        print("CRITICAL_UNTRACKED_SAMPLE=" + ",".join(critical_untracked[:20]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
