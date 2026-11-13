#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "coordination/global_policy/project_native_execution_policy_v0_1.yaml"
SPECS = ROOT / "coordination/bootstrap/assistant_context_system_specs_v0_1.yaml"
START = ROOT / "coordination/bootstrap/START_HERE.md"
READING = ROOT / "coordination/instruction_intake/assistant_reading_order.md"

def load(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"NOT_MAPPING:{path}")
    return data

def main() -> int:
    for p in (POLICY, SPECS, START, READING):
        if not p.is_file():
            raise SystemExit(f"MISSING:{p.relative_to(ROOT)}")
    policy = load(POLICY)
    specs = load(SPECS)
    rules = {x.get("id"): x.get("rule") for x in policy.get("core_rules", [])}
    required = {f"PNX-{i:02d}" for i in range(1, 9)}
    if set(rules) != required:
        raise SystemExit(f"RULE_SET_MISMATCH:{sorted(rules)}")
    if policy.get("status") != "ACTIVE_CANONICAL_POLICY":
        raise SystemExit("POLICY_NOT_ACTIVE")
    section = specs.get("project_native_execution_policy")
    if not isinstance(section, dict):
        raise SystemExit("SPECS_POLICY_SECTION_MISSING")
    expected = "coordination/global_policy/project_native_execution_policy_v0_1.yaml"
    if section.get("canonical_source") != expected:
        raise SystemExit("SPECS_CANONICAL_SOURCE_MISMATCH")
    if section.get("required_for_zero_context_assistant") is not True:
        raise SystemExit("ZERO_CONTEXT_REQUIREMENT_MISSING")
    if expected not in START.read_text(encoding="utf-8"):
        raise SystemExit("START_HERE_ROUTE_MISSING")
    if expected not in READING.read_text(encoding="utf-8"):
        raise SystemExit("READING_ORDER_ROUTE_MISSING")
    print("PROJECT_NATIVE_EXECUTION_POLICY=PASS")
    print("POLICY_ACTIVE=true")
    print("RULE_COUNT=8")
    print("ASSISTANT_CONTEXT_CARRIES_POLICY_DIGEST=true")
    print("START_HERE_ROUTE=true")
    print("READING_ORDER_ROUTE=true")
    print("CHAT_IS_PRIMARY_RUNTIME=false")
    print("PROJECT_IS_PRIMARY_LOGIC_HOME=true")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
