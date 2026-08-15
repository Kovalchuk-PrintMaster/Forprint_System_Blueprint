---
schema_version: blueprint_self_prompt_v0_1
prompt_id: blueprint_v0_4_completion_discovery_and_intake_v0_1
target_module: forprint_system_blueprint
status: draft
roadmap_step_id: blueprint_v0_4_completion_discovery_and_intake_v0_1
---

# Blueprint v0.4 — Implement idempotent completion discovery and v0.4 intake

Implement read-only discovery of module-owned completion outbox records and the v0.4 completion intake path.

Preserve module ownership and immutability: Blueprint may discover, validate, classify, and review completion records but must not rewrite module-owned completion evidence. Keep candidate protocol revisions gated by their declared activation state, preserve explicit operator ACCEPT/RETURN/HOLD, and perform no module repository writes, rollout, production writes, automatic commit, or automatic push.
