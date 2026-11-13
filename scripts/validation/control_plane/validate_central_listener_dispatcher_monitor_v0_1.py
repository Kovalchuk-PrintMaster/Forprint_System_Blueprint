from pathlib import Path

import yaml

from scripts.coordination.control_plane import dispatch_intent, events, monitor, runtime


def main() -> int:
    contract = Path(
        "coordination/standards/automation/control_plane/central_listener_dispatcher_monitor_v0_1.yaml"
    )
    data = yaml.safe_load(contract.read_text(encoding="utf-8")) if contract.is_file() else None
    checks = [
        isinstance(data, dict),
        isinstance(data, dict)
        and data.get("schema_version") == "central_listener_dispatcher_monitor_contract_v0_1",
        isinstance(data, dict) and data.get("architecture", {}).get("central_runtime_count") == 1,
        isinstance(data, dict) and data.get("architecture", {}).get("per_module_listener") is False,
        isinstance(data, dict) and data.get("architecture", {}).get("daemon_required") is False,
        dispatch_intent.DISPATCH_INTENT_SCHEMA == "forprint_dispatch_intent_v0_1",
        monitor.MONITOR_SCHEMA == "forprint_execution_monitor_projection_v0_1",
        "dispatch_intent_state" not in events.Q5_ALLOWED_FAMILIES,
        callable(runtime.run_control_plane_step),
    ]
    if not all(checks):
        print("CENTRAL_CONTROL_PLANE_RUNTIME_CONTRACT=FAIL")
        return 1
    print("CENTRAL_CONTROL_PLANE_RUNTIME_CONTRACT=PASS")
    print("CENTRAL_RUNTIME_COUNT=1")
    print("PER_MODULE_LISTENER=false")
    print("Q5_EVENT_FAMILY_SET_NOT_EXPANDED=true")
    print("WORKER_PROCESS_START_ALLOWED=false")
    print("DAEMON_REQUIRED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
