#!/usr/bin/env python3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "coordination/roadmaps/details/forprint_system_blueprint/portfolio_full_horizon_target_states_v0_1.yaml"

def clip(value, n):
    value = " ".join(str(value).split())
    return value if len(value) <= n else value[:n-1] + "…"

data = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
mods = data["modules"]
rank = {"P0":0,"P1":1,"P2":2,"P3":3,"SUPPORT":4}

print("FORPRINT PORTFOLIO READINESS DASHBOARD v0.1")
print("AUTHORITY=planning_projection_not_release_authority")
print("ORDINARY_MODULE_IMPLEMENTATION_ALLOWED=false")
print()
print(f"{'PRIO':<8} {'MODULE':<39} {'RAW/INVENTORY':<38} {'EFFECTIVE':<10} {'VALUE':<18} DEPENDS")
print("-"*145)
for mid, item in sorted(mods.items(), key=lambda kv:(rank.get(kv[1]["strategic_priority"],9), kv[0])):
    deps = ",".join(item.get("dependencies_or_inputs", [])) or "-"
    print(f"{item['strategic_priority']:<8} {clip(mid,39):<39} {clip(item['inventory_state'],38):<38} {'HOLD':<10} {clip(item['module_value_test'],18):<18} {clip(deps,60)}")
print()
print("GATE=full roadmaps + mature targets + self-inventory + dependency/readiness baseline")
print("NOTE=raw readiness does not override strategic priority or dependency timing")
