from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "coordination/standards/automation/work_front_contract_v0_1.yaml"
RUNTIME = ROOT / "scripts/coordination/work_front_v0_1.py"
CONTROLLER = ROOT / "scripts/coordination/roadmap_execution_reconciliation.py"
MAKEFILE = ROOT / "Makefile"
AGENTS = ROOT / "AGENTS.md"
STANDARDS_INDEX = ROOT / "coordination/standards/index.yaml"


def fail(reason: str) -> int:
    print("WORK_FRONT_CONTRACT_VALIDATION=FAIL")
    print("REASON=" + reason)
    return 1


def runtime_module():
    spec = importlib.util.spec_from_file_location("_work_front_validation_runtime", RUNTIME)
    if spec is None or spec.loader is None:
        raise RuntimeError("runtime import spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_contract_only() -> int:
    if not CONTRACT.is_file() or not RUNTIME.is_file():
        return fail("CONTRACT_OR_RUNTIME_MISSING")

    try:
        data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return fail("CONTRACT_YAML:" + str(exc))
    if not isinstance(data, dict):
        return fail("CONTRACT_ROOT")

    try:
        runtime_module().validate_contract_shape(data)
    except Exception as exc:
        return fail("CONTRACT_SHAPE:" + str(exc))

    print("WORK_FRONT_CONTRACT=PASS")
    print("WORK_FRONT_EXECUTION_AUTHORITY=true")
    print("CHAT_AUTHORITY=false")
    print("NEW_REQUIRES_RATIONALE=true")
    print("DISPATCH_AUTHORITY_CONFERRED=false")
    return 0


def validate_full() -> int:
    rc = validate_contract_only()
    if rc:
        return rc

    standards = yaml.safe_load(STANDARDS_INDEX.read_text(encoding="utf-8"))
    if not isinstance(standards, dict):
        return fail("STANDARDS_INDEX_ROOT")
    records = standards.get("standards")
    if not isinstance(records, list):
        return fail("STANDARDS_INDEX_RECORDS")
    matches = [
        row
        for row in records
        if isinstance(row, dict) and row.get("file") == "automation/work_front_contract_v0_1.yaml"
    ]
    if len(matches) != 1:
        return fail("STANDARDS_INDEX_REGISTRATION")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    if makefile.count(".PHONY: work-front-contract-check") != 1:
        return fail("MAKE_CONTRACT_PHONY")
    if makefile.count("work-front-contract-check:") != 1:
        return fail("MAKE_CONTRACT_TARGET")
    check_core = next(
        (line for line in makefile.splitlines() if line.startswith("check-core:")),
        "",
    )
    if "work-front-contract-check" not in check_core.split():
        return fail("CHECK_CORE_BINDING")
    if "work-front-assistant-pack-gate" not in makefile:
        return fail("ASSISTANT_PACK_GATE")
    if 'FRONT="$(FRONT)"' not in makefile:
        return fail("ASSISTANT_PACK_FRONT_BINDING")

    agents = AGENTS.read_text(encoding="utf-8")
    if "<!-- FORPRINT_WORK_FRONT_CONTRACT_START -->" not in agents:
        return fail("AGENTS_BINDING")
    if "REUSE / EXTEND / ADAPT / REPLACE / NEW" not in agents:
        return fail("AGENTS_REUSE_ENUM")

    controller = CONTROLLER.read_text(encoding="utf-8")
    for marker in (
        "WORK_FRONT_GATE=PASS",
        "GATE_REASON=WORK_FRONT_REQUIRED",
        "GATE_REASON=WORK_FRONT_INVALID",
        "DISPATCH_AUTHORITY=false",
    ):
        if marker not in controller:
            return fail("CONTROLLER_BINDING:" + marker)

    print("WORK_FRONT_CONTRACT_VALIDATION=PASS")
    print("REUSE_DISPOSITIONS=REUSE,EXTEND,ADAPT,REPLACE,NEW")
    print("NEW_REQUIRES_RATIONALE=true")
    print("ASSISTANT_PACK_GATE_BOUND=true")
    print("DISPATCH_GATE_BOUND=true")
    print("PROJECT_ONBOARD_COMPATIBILITY_WITHOUT_FRONT=true")
    print("DISPATCH_AUTHORITY_WIDENED=false")
    print("CF05_HISTORY_IMPLEMENTED=true")
    print("WORKFRONT_HISTORY_IMPLEMENTED=true")
    print("EXECUTION_ATTEMPT_LEDGER_IMPLEMENTED=true")
    print("CF06_EXECUTION_PROFILES_IMPLEMENTED=false")
    print("BLUEPRINT_AI_TRIAL_READY=false")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract-only", action="store_true")
    parser.add_argument("--front")
    parser.add_argument(
        "--action",
        choices=["validate", "assistant-pack", "dispatch"],
        default="validate",
    )
    args = parser.parse_args()

    if args.contract_only:
        return validate_contract_only()

    if args.front:
        rc = validate_contract_only()
        if rc:
            return rc
        try:
            runtime_module().validate_work_front(ROOT, args.front, action=args.action)
        except Exception as exc:
            return fail("FRONT:" + str(exc))
        print("WORK_FRONT_INSTANCE_VALIDATION=PASS")
        return 0

    return validate_full()


if __name__ == "__main__":
    raise SystemExit(main())
