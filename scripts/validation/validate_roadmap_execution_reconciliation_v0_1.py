#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT / "coordination/standards/automation/roadmap_execution_reconciliation_contract_v0_1.yaml"
)
PROGRAM = (
    ROOT
    / "coordination/roadmaps/details/forprint_system_blueprint/control_foundation_near_horizon_program_v0_1.yaml"
)
LEGACY = (
    ROOT / "coordination/roadmaps/details/forprint_system_blueprint/continuity/"
    "2026-09-10__continuity_assistant_handoff_micro_roadmap_v0_1.yaml"
)
MAKEFILE = ROOT / "Makefile"
AGENTS = ROOT / "AGENTS.md"


def fail(reason: str) -> int:
    print("ROADMAP_EXECUTION_RECONCILIATION_VALIDATION=FAIL")
    print("ERROR=" + reason)
    return 1


def main() -> int:
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("schema_version") != "forprint_roadmap_execution_reconciliation_contract_v0_1":
        return fail("CONTRACT_SCHEMA")
    if contract.get("authority") != "none":
        return fail("CONTRACT_AUTHORITY")
    if (
        contract.get("dependency_reference_forms", {}).get("external_lifecycle", {}).get("syntax")
        != "work_id:LIFECYCLE_STATE"
    ):
        return fail("EXTERNAL_DEPENDENCY_SYNTAX")
    history = contract.get("historical_migration_policy", {})
    if history.get("current_or_future_roadmap_override_allowed") is not False:
        return fail("HISTORICAL_OVERRIDE_BOUNDARY")
    manual = contract.get("manual_mode", {})
    if manual.get("wip_limit") != 1:
        return fail("WIP_LIMIT")
    if manual.get("auto_next_step_activation_allowed") is not False:
        return fail("AUTO_ACTIVATION")
    if manual.get("automatic_worker_dispatch_allowed") is not False:
        return fail("WORKER_DISPATCH")
    if contract.get("public_make_check_non_mutating") is not True:
        return fail("MAKE_CHECK_MUTATION")

    program = yaml.safe_load(PROGRAM.read_text(encoding="utf-8"))
    steps = {row["id"]: row for row in program["steps"]}
    legacy = yaml.safe_load(LEGACY.read_text(encoding="utf-8"))
    if any("state" in row for row in legacy.get("steps", [])):
        return fail("LEGACY_EXECUTION_STATE_DOUBLE_WRITE")
    historical = legacy.get("historical_completion_evidence", {})
    if historical.get("schema_version") != "forprint_legacy_roadmap_completion_evidence_v0_1":
        return fail("LEGACY_HISTORICAL_EVIDENCE_SCHEMA")
    if historical.get("authority") != "HISTORICAL_ACCEPTANCE_EVIDENCE_NOT_EXECUTION_STATE":
        return fail("LEGACY_HISTORICAL_EVIDENCE_AUTHORITY")
    if historical.get("step_state_fields_retired") is not True:
        return fail("LEGACY_STATE_RETIREMENT_MARKER")
    if historical.get("completed_step_ids") != [row.get("id") for row in legacy.get("steps", [])]:
        return fail("LEGACY_HISTORICAL_EVIDENCE_STEP_SET")
    if any("state" in row for row in program["steps"]):
        return fail("CONTROL_FOUNDATION_EXECUTION_STATE_DOUBLE_WRITE")
    if steps["CF-01"].get("work_id") != "u180a":
        return fail("CF01_BINDING")
    if steps["CF-02"].get("work_id") != "u180b":
        return fail("CF02_BINDING")
    rr = program.get("roadmap_execution_reconciliation", {})
    if rr.get("cf02_closure_acceptance") != "EVENT_SOURCED_DERIVED_CURSOR_PROVEN":
        return fail("PROGRAM_CF02_CLOSURE_ACCEPTANCE")
    if "status" in rr or "current_work_id" in rr:
        return fail("PROGRAM_STALE_EXECUTION_CURSOR_METADATA")
    if rr.get("actual_execution_authority") != "continuity_event_store":
        return fail("PROGRAM_EXECUTION_AUTHORITY")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    for token in (
        ".PHONY: roadmap-sync",
        ".PHONY: roadmap-sync-check",
        ".PHONY: roadmap-status",
    ):
        if token not in makefile:
            return fail("MAKE_TARGET:" + token)
    if makefile.count("roadmap-status:") != 1:
        return fail("ROADMAP_STATUS_TARGET_NOT_UNIQUE")
    if "scripts/coordination/roadmap_execution_reconciliation.py --root . status" not in makefile:
        return fail("ROADMAP_STATUS_RECONCILIATION_RECIPE")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")), ""
    )
    if "roadmap-sync-check" not in check_core.split():
        return fail("CHECK_CORE_BINDING")
    if "roadmap-sync" in check_core.split():
        return fail("MUTATING_SYNC_IN_CHECK_CORE")
    if "assistant-pack:\n\t$(MAKE) roadmap-sync-check" not in makefile:
        return fail("ASSISTANT_PACK_GATE")
    if "assistant-handoff-check:\n\t$(MAKE) roadmap-sync-check" not in makefile:
        return fail("ASSISTANT_HANDOFF_GATE")

    agents = AGENTS.read_text(encoding="utf-8")
    if "<!-- FORPRINT_ROADMAP_EXECUTION_RECONCILIATION_START -->" not in agents:
        return fail("AGENTS_BINDING")

    cp = subprocess.run(
        [
            sys.executable,
            "scripts/coordination/roadmap_execution_reconciliation.py",
            "--root",
            ".",
            "check",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if cp.returncode:
        return fail("RUNTIME_CHECK\n" + cp.stdout)
    if "ROADMAP_SYNC=IN_SYNC" not in cp.stdout:
        return fail("SYNC_MARKER")
    if "MUTATION_PERFORMED=false" not in cp.stdout:
        return fail("NON_MUTATING_MARKER")

    status = subprocess.run(
        [
            sys.executable,
            "scripts/coordination/roadmap_execution_reconciliation.py",
            "--root",
            ".",
            "status",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if status.returncode:
        return fail("STATUS_COMMAND\n" + status.stdout)
    control_status_lines = [
        line
        for line in status.stdout.splitlines()
        if line.startswith("ROADMAP_STATUS=control_foundation_near_horizon:")
    ]
    if len(control_status_lines) != 1:
        return fail("CONTROL_FOUNDATION_STATUS_SHAPE")
    control_status = control_status_lines[0]
    for field in ("previous=", "current=", "next=", "ready="):
        if field not in control_status:
            return fail("CONTROL_FOUNDATION_STATUS_FIELD_" + field[:-1].upper())

    print("ROADMAP_EXECUTION_RECONCILIATION_VALIDATION=PASS")
    print("DERIVED_CURSOR_PHASE_INDEPENDENT_VALIDATION=true")
    print("PROGRAM_EXECUTION_CURSOR_METADATA=DERIVED_NOT_STORED")
    print("CF02_CLOSURE_ACCEPTANCE=EVENT_SOURCED_DERIVED_CURSOR_PROVEN")
    print("ROADMAP_SYNC=IN_SYNC")
    print("ACTUAL_EXECUTION_AUTHORITY=continuity_event_store")
    print("GENERATED_STATUS_AUTHORITY=none")
    print("EXTERNAL_LIFECYCLE_DEPENDENCIES=SUPPORTED")
    print("HISTORICAL_MIGRATION_COMPATIBILITY=BOUNDED")
    print("WIP_LIMIT=1")
    print("AUTO_NEXT_ACTIVATION=false")
    print("WORKER_DISPATCH_AUTHORITY=false")
    print("PUBLIC_MAKE_CHECK_NON_MUTATING=true")
    print("CONTROL_FOUNDATION_DOUBLE_WRITE_REMOVED=true")
    print("LEGACY_TERMINAL_STATE_RETIREMENT=COMPLETE")
    print("LEGACY_HISTORICAL_COMPLETION_EVIDENCE=EXPLICIT")
    print("LIFECYCLE_RECONCILIATION_CHOKE_POINTS=HARD_GATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
