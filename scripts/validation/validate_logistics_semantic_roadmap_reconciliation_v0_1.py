from pathlib import Path

import yaml

ROADMAP = Path("coordination/roadmaps/logistics_service.yaml")
REPORT = Path(
    "coordination/internal_work/blueprint/module_inventory/logistics_service/"
    "2026-09-08__logistics_service__semantic_roadmap_reconciliation_apply_v0_1.yaml"
)


def main() -> int:
    roadmap = yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))
    report = yaml.safe_load(REPORT.read_text(encoding="utf-8"))

    if roadmap["metadata"]["current_step_id"] != (
        "logistics_service_authority_lineage_and_module_bootstrap_v0_1"
    ):
        print("LOGISTICS_SEMANTIC_RECONCILIATION=FAIL current_step")
        return 1
    if len(roadmap["roadmap"]) != 33:
        print("LOGISTICS_SEMANTIC_RECONCILIATION=FAIL step_count")
        return 1
    if report["canonical_apply"]["numbered_steps_added"] != 0:
        print("LOGISTICS_SEMANTIC_RECONCILIATION=FAIL bounded_apply")
        return 1
    if len(report["required_roadmap_candidates"]) != 3:
        print("LOGISTICS_SEMANTIC_RECONCILIATION=FAIL required_candidates")
        return 1
    if len(report["review_candidates"]) != 2:
        print("LOGISTICS_SEMANTIC_RECONCILIATION=FAIL review_candidates")
        return 1
    if report["authority_boundaries"]["logistics_repository_write_performed"] is not False:
        print("LOGISTICS_SEMANTIC_RECONCILIATION=FAIL repository_boundary")
        return 1

    print("LOGISTICS_SEMANTIC_RECONCILIATION=PASS")
    print("CANONICAL_CURRENT_STEP=logistics_service_authority_lineage_and_module_bootstrap_v0_1")
    print("CANONICAL_STEP_COUNT=33")
    print("REQUIRED_ROADMAP_CANDIDATE_COUNT=3")
    print("REVIEW_CANDIDATE_COUNT=2")
    print("LOGISTICS_REPOSITORY_WRITE_PERFORMED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
