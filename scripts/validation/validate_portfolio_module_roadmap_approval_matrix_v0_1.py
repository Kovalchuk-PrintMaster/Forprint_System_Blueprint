#!/usr/bin/env python3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

def load(rel):
    with (ROOT / rel).open(encoding="utf-8") as f:
        return yaml.safe_load(f)

def fail(msg):
    raise SystemExit("PORTFOLIO_MODULE_ROADMAP_APPROVAL_MATRIX=FAIL: " + msg)

m = load("coordination/roadmaps/details/forprint_system_blueprint/portfolio_module_roadmap_approval_matrix_v0_1.yaml")
t = load("coordination/roadmaps/details/forprint_system_blueprint/portfolio_full_horizon_target_states_v0_1.yaml")
i = load("machine/module_identity_registry.yaml")
h = load("coordination/human_intent/modules/forprint_system_blueprint.yaml")
r = load("coordination/releases/current.yaml")

if m.get("status") != "ACTIVE_INTERNAL_PORTFOLIO_ANALYSIS":
    fail("status")
g = m.get("distribution_gate", {})
if g.get("state") != "CLOSED":
    fail("distribution gate")
for key in ("assistant_contact_allowed","assistant_task_distribution_allowed","prompt_activation_allowed","module_implementation_allowed"):
    if g.get(key) is not False:
        fail(key)

canonical = i.get("canonical_module_ids", [])
if set(m.get("modules", {})) != set(canonical) or len(canonical) != 23:
    fail("canonical coverage")

for mid in canonical:
    steps = m["modules"][mid]["steps"]
    target_steps = t["modules"][mid]["full_horizon_steps"]
    if len(steps) != len(target_steps):
        fail(mid + ": target length")
    if [x["sequence"] for x in steps] != list(range(1, len(steps) + 1)):
        fail(mid + ": steps")
    if any(x.get("execution_authority") is not False for x in steps):
        fail(mid + ": execution")
    if [x["title"] for x in steps] != target_steps:
        fail(mid + ": target mismatch")

sem = m["proposed_noncanonical_modules"]["forprint_semantic_retrieval_service"]
if "forprint_semantic_retrieval_service" in canonical:
    fail("semantic retrieval unexpectedly canonical")
if sem["identity_state"] != "PROPOSED_NONCANONICAL_REVIEW_ONLY" or len(sem["steps"]) != 10:
    fail("semantic retrieval review-only")

ids = {x["intent_id"] for x in h["intents"]}
if not {"HI-FP-SYSTEM-BLUEPRINT-027","HI-FP-SYSTEM-BLUEPRINT-028"} <= ids:
    fail("human intent")

if t["global_execution_gate"].get("assistant_distribution_allowed") is not False:
    fail("projection distribution gate")
if r.get("coordination_controls", {}).get("automatic_accept") is not False:
    fail("automatic_accept")
if r.get("coordination_controls", {}).get("automatic_release_next_prompt") is not False:
    fail("automatic_release_next_prompt")
if r.get("automation_validation_pilot", {}).get("sole_pilot_module") != "logistics_service":
    fail("H10 pilot")

print("PORTFOLIO_MODULE_ROADMAP_APPROVAL_MATRIX=PASS")
print("CANONICAL_MODULE_COUNT=23")
print("ROADMAP_HORIZON_MODEL=VARIABLE_FULL_HORIZON")
print("ASSISTANT_DISTRIBUTION_ALLOWED=false")
print("MODULE_IMPLEMENTATION_ALLOWED=false")
