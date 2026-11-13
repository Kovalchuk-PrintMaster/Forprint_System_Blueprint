from pathlib import Path

import yaml

REGISTRY = Path(
    "coordination/internal_work/blueprint/module_preparation/module_preparation_registry_v0_1.yaml"
)
QUEUE = Path(
    "coordination/internal_work/blueprint/module_preparation/module_preparation_queue_v0_1.yaml"
)
STANDARD = Path(
    "coordination/standards/automation/control_plane/module_preparation_registry_v0_1.yaml"
)


def main() -> int:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    queue = yaml.safe_load(QUEUE.read_text(encoding="utf-8"))
    standard = yaml.safe_load(STANDARD.read_text(encoding="utf-8"))

    if registry["module_count"] != 23:
        print("MODULE_PREPARATION_REGISTRY=FAIL module_count")
        return 1
    modules = {row["module_id"]: row for row in registry["modules"]}
    if modules["logistics_service"]["preparation_state"] != "BOOTSTRAP_READY":
        print("MODULE_PREPARATION_REGISTRY=FAIL logistics_state")
        return 1
    if modules["forprint_project_inspector"]["preparation_state"] != "DISCOVERED":
        print("MODULE_PREPARATION_REGISTRY=FAIL inspector_state")
        return 1
    if modules["forprint_project_inspector"]["pending_blueprint_obligation_count"] != 9:
        print("MODULE_PREPARATION_REGISTRY=FAIL inspector_obligations")
        return 1
    if modules["forprint_project_inspector"]["repository_provisioning_required"] is not True:
        print("MODULE_PREPARATION_REGISTRY=FAIL inspector_repository_provisioning")
        return 1
    if "REPOSITORY_PROVISIONING_REQUIRED" not in modules["forprint_project_inspector"]["blockers"]:
        print("MODULE_PREPARATION_REGISTRY=FAIL inspector_repository_blocker")
        return 1
    inspector_queue = next(
        row for row in queue["queue_rows"] if row["module_id"] == "forprint_project_inspector"
    )
    if inspector_queue["action"] != "AWAIT_EXPLICIT_REPOSITORY_PROVISIONING_AUTHORITY":
        print("MODULE_PREPARATION_REGISTRY=FAIL inspector_queue_action")
        return 1
    if modules["calculator_engine"]["historical_legacy_risk"] is not True:
        print("MODULE_PREPARATION_REGISTRY=FAIL calculator_risk")
        return 1
    if modules["telegram_bot"]["historical_legacy_risk"] is not True:
        print("MODULE_PREPARATION_REGISTRY=FAIL telegram_risk")
        return 1
    if registry["all_required_modules_verified_work_ready"] is not False:
        print("MODULE_PREPARATION_REGISTRY=FAIL portfolio_ready")
        return 1
    if registry["development_priority_selection_allowed"] is not False:
        print("MODULE_PREPARATION_REGISTRY=FAIL priority_gate")
        return 1
    if queue["development_priority_selection_performed"] is not False:
        print("MODULE_PREPARATION_REGISTRY=FAIL priority_performed")
        return 1
    if queue["worker_launch_allowed"] is not False:
        print("MODULE_PREPARATION_REGISTRY=FAIL worker_launch")
        return 1
    if standard["projection_rules"]["registry_is_execution_authority"] is not False:
        print("MODULE_PREPARATION_REGISTRY=FAIL authority")
        return 1

    print("MODULE_PREPARATION_REGISTRY=PASS")
    print("MODULE_COUNT=23")
    print("LOGISTICS_PREPARATION_STATE=BOOTSTRAP_READY")
    print("INSPECTOR_PREPARATION_STATE=DISCOVERED")
    print("INSPECTOR_REPOSITORY_PROVISIONING_REQUIRED=true")
    print("INSPECTOR_PENDING_BLUEPRINT_OBLIGATION_COUNT=9")
    print("DEVELOPMENT_PRIORITY_SELECTION_ALLOWED=false")
    print("WORKER_LAUNCH_ALLOWED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
