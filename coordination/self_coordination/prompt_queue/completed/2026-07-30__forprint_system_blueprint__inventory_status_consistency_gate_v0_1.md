---
prompt_id: blueprint_inventory_status_consistency_gate_v0_1
module_id: forprint_system_blueprint
status: completed
owner: blueprint_coordination_assistant
reviewer: project_owner
created_at: '2026-07-30'
---

# Inventory Status Consistency Gate

## Objective

Validate that the short inventory-status table stays consistent with Wave 2, coverage/drift and roadmap sources.

## Required outputs

- Cross-artifact metric consistency checks.
- Freshness and drift failure behavior.
- Standard check-suite integration.
- Regression tests.

## Completion gate

- Displayed metrics match canonical source artifacts.
- Stale or contradictory metrics produce a non-zero result.
- External rollout remains gated.
