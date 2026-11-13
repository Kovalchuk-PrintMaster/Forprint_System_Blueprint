---
prompt_id: blueprint_self_coordination_consistency_ci_gate_v0_1
module_id: forprint_system_blueprint
status: completed
owner: blueprint_coordination_assistant
reviewer: project_owner
created_at: '2026-07-30'
---

# Self-Coordination Consistency CI Gate

## Objective

Integrate the accepted Blueprint self-coordination validator into the regular Blueprint check suite so roadmap, prompt queue, completion packets and managed-module planning cannot drift silently.

## Required outputs

- Read-only `make check` integration.
- Failure behavior for roadmap horizon and prompt-state drift.
- Completion-packet consistency checks.
- Regression tests and validation evidence.

## Completion gate

- The self-coordination validator runs through the standard Blueprint checks.
- Drift causes a clear non-zero validation result.
- Managed-module repositories and canonical module controls remain unchanged.
- Project owner remains the acceptance reviewer.
