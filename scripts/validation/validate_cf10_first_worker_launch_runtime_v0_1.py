from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = (
    ROOT
    / "scripts/coordination/control_plane/worker_runtime/launcher.py"
)
DISPATCH = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
CONTROL = (
    ROOT
    / "coordination/standards/automation/control_plane/"
    "central_listener_dispatcher_monitor_v0_1.yaml"
)
LEDGER = (
    ROOT
    / "coordination/standards/automation/"
    "execution_attempt_ledger_contract_v0_1.yaml"
)
HISTORICAL = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-09-06__blueprint__worker_runtime_and_invocation_contract_v0_1.yaml"
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    launcher = load_module(LAUNCHER, "_cf10_launcher_validator")
    dispatch = load_module(DISPATCH, "_cf10_dispatch_validator")

    for name in ("launch_process", "WorkerProcessLaunchError"):
        if not hasattr(launcher, name):
            raise RuntimeError(f"launcher symbol missing: {name}")

    for name in (
        "build_cf10_dispatcher_canonical_ack",
        "authorize_cf10_internal_zero_stage_explicit_dispatch",
    ):
        if not hasattr(dispatch, name):
            raise RuntimeError(f"dispatch symbol missing: {name}")

    control = yaml.safe_load(CONTROL.read_text(encoding="utf-8"))
    ledger = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    historical = yaml.safe_load(HISTORICAL.read_text(encoding="utf-8"))

    row = control["cf10_first_internal_actual_worker_launch_v0_1"]
    assert row["exact_scope"]["work_id"] == "u180j"
    assert row["exact_scope"]["worker_id"] == "worker-01"
    assert row["exact_scope"]["attempt_id"] == "cf10-u180j-a001"
    assert row["authority"]["external_dispatch"] is False
    assert row["authority"]["release"] is False
    assert row["authority"]["push"] is False
    assert row["authority"]["merge"] is False
    assert row["authority"]["foreign_repository_write"] is False

    extension = ledger["cf10_first_actual_launch_extension_v0_1"]
    assert extension["launch_fact"]["attempt_stage"] == "STARTED"
    assert extension["launch_fact"]["result_state"] == "PENDING"
    assert extension["retry"]["after_process_start_uses_new_attempt_id"] is True
    assert ledger["scope_exclusions"]["actual_worker_launch"] is False

    runtime_extension = historical[
        "cf10_first_actual_worker_launch_extension_v0_1"
    ]
    assert runtime_extension["provider_neutral_launcher"] is True
    assert runtime_extension["argv_no_shell"] is True
    assert runtime_extension["environment_values_serialized"] is False
    assert runtime_extension["commit_push_merge_release"] is False

    print("CF10_FIRST_WORKER_LAUNCH_RUNTIME_VALIDATION=PASS")
    print("PROVIDER_NEUTRAL_PROCESS_LAUNCHER=true")
    print("ARGV_NO_SHELL=true")
    print("LEDGER_START_FACT=STARTED/PENDING")
    print("EXACT_CF10_EXCEPTION_ONLY=true")
    print("BROAD_DISPATCH_AUTHORITY=false")
    print("WORKER_PROCESS_LAUNCHED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
