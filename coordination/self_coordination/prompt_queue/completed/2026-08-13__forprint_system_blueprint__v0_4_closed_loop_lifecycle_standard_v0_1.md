---
schema_version: blueprint_self_prompt_v0_1
prompt_id: blueprint_v0_4_closed_loop_lifecycle_standard_v0_1
target_module: forprint_system_blueprint
status: completed
roadmap_step_id: blueprint_v0_4_closed_loop_lifecycle_standard_v0_1
---

# Blueprint v0.4 — Closed-Loop Lifecycle Standard v0.1

Define the canonical roadmap → prompt → execution → completion outbox → discovery → intake → operator decision → roadmap/queue advance lifecycle.

Required: ownership/state machines, WIP=1, draft/prepared/released/pending-review/accepted/returned/held semantics, physical prompt-file lifecycle, `approved -> completed/` only after explicit ACCEPT, RETURN/HOLD not completed, queue-path consistency, soft capacity warnings vs hard integrity gates, rollback, and no automatic commit/push/ACCEPT.
