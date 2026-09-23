from pathlib import Path

TRACEABILITY = Path(
    "coordination/standards/governance/module_concept_and_roadmap_traceability_standard_v0_1.md"
)
ROADMAP_POLICY = Path("coordination/standards/governance/module_development_roadmap_policy.md")
INVENTORY_MASTER = Path(
    "coordination/internal_work/blueprint/module_inventory/"
    "2026-09-04__module_inventory_program_master_v0_1.md"
)


def main() -> int:
    for path in (TRACEABILITY, ROADMAP_POLICY, INVENTORY_MASTER):
        if not path.is_file():
            print(f"MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL missing:{path}")
            return 1

    trace = TRACEABILITY.read_text(encoding="utf-8")
    policy = ROADMAP_POLICY.read_text(encoding="utf-8")
    master = INVENTORY_MASTER.read_text(encoding="utf-8")

    if "Implementation ↔ Inventory ↔ Roadmap reconciliation" not in trace:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL traceability")
        return 1
    if "Blueprint-derived module obligations" not in trace:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL obligations")
        return 1
    if "UNKNOWN_LEGACY" not in trace:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL unknown_legacy")
        return 1
    if "Post-inventory roadmap reconciliation gate" not in policy:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL roadmap_policy")
        return 1
    if "capability exists but roadmap omits it" not in policy:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL capability_case")
        return 1
    if "Blueprint assigns a new responsibility" not in policy:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL blueprint_case")
        return 1
    if "Roadmap reconciliation is a mandatory P6/P7 boundary" not in master:
        print("MODULE_ROADMAP_RECONCILIATION_STANDARD=FAIL inventory_master")
        return 1

    print("MODULE_ROADMAP_RECONCILIATION_STANDARD=PASS")
    print("IMPLEMENTATION_INVENTORY_ROADMAP_INVARIANT=true")
    print("BLUEPRINT_OBLIGATION_PROJECTION_REQUIRED=true")
    print("UNKNOWN_LEGACY_INVENTION_FORBIDDEN=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
