#!/usr/bin/env python3
"""Validate exact CF-10 exception before real workspace provisioning."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DISPATCH = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
CONTROL = ROOT / (
    "coordination/standards/automation/control_plane/"
    "central_listener_dispatcher_monitor_v0_1.yaml"
)
ROADMAP = ROOT / (
    "coordination/roadmaps/details/forprint_system_blueprint/"
    "control_foundation_near_horizon_program_v0_1.yaml"
)

spec = importlib.util.spec_from_file_location("_cf10_dispatch_live", DISPATCH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def main() -> int:
    try:
        control = yaml.safe_load(CONTROL.read_text(encoding="utf-8"))
        row = control.get("cf10_internal_zero_stage_exception")
        if not isinstance(row, dict):
            raise RuntimeError("CF-10 exception contract section missing")

        broad = row.get("broad_trial_gate")
        if not isinstance(broad, dict):
            raise RuntimeError("broad_trial_gate missing")
        if broad.get("required_value_for_this_exception") is not False:
            raise RuntimeError("CF-10 exception must coexist with broad readiness=false")
        if broad.get("mutation_allowed_by_cf10_exception") is not False:
            raise RuntimeError("CF-10 exception cannot mutate broad readiness")

        roadmap = yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))
        gate = roadmap.get("blueprint_ai_trial_readiness_gate")
        if not isinstance(gate, dict):
            raise RuntimeError("Blueprint broad trial readiness gate missing")
        if gate.get("signal_value_now") is not False:
            raise RuntimeError("BLUEPRINT_AI_TRIAL_READY unexpectedly true")

        exact = mod.CF10_INTERNAL_ZERO_STAGE_BINDING_V0_1
        result = mod.validate_cf10_internal_zero_stage_exception(
            work_id=exact["work_id"],
            module=exact["module"],
            work_front=exact["work_front"],
            task_prompt_id=exact["task_prompt_id"],
            task_module_root=exact["task_module_root"],
            execution_profile=exact["execution_profile"],
            procedure_id=exact["procedure_id"],
            worker_id=exact["worker_id"],
            attempt_id=exact["attempt_id"],
            blueprint_ai_trial_ready=False,
        )
        if result.get("eligible") is not True:
            raise RuntimeError("exact CF-10 binding is not eligible")
        if result.get("worker_process_launch_allowed") is not False:
            raise RuntimeError("Slice 4 exception unexpectedly allows worker launch")
        if result.get("canonical_attempt_ledger_append_allowed") is not False:
            raise RuntimeError("Slice 4 exception unexpectedly allows attempt append")

        authority = result.get("authority")
        if not isinstance(authority, dict) or any(
            value is not False for value in authority.values()
        ):
            raise RuntimeError("CF-10 exception authority widened")

        print("CF10_INTERNAL_DISPATCH_EXCEPTION_VALIDATION=PASS")
        print("EXCEPTION_SCOPE=CF10_U180J_EXACT_BINDING_ONLY")
        print("GLOBAL_BLUEPRINT_AI_TRIAL_READY=false")
        print("GLOBAL_BLUEPRINT_AI_TRIAL_READY_MUTATED=false")
        print("ASSISTANT_ACK_REQUIRED=true")
        print("ASSISTANT_ACK_VALIDATED=false")
        print("EXPLICIT_DISPATCH_DECISION_REQUIRED=true")
        print("WORKER_PROCESS_LAUNCH_ALLOWED=false")
        print("CANONICAL_ATTEMPT_LEDGER_APPEND_ALLOWED=false")
        print("EXTERNAL_DISPATCH_ALLOWED=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        return 0
    except Exception as exc:
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("CF10_INTERNAL_DISPATCH_EXCEPTION_VALIDATION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
