---
schema_version: blueprint_self_prompt_v0_1
prompt_id: blueprint_v0_4_next_prompt_selection_and_activation_v0_1
target_module: forprint_system_blueprint
status: approved
roadmap_step_id: blueprint_v0_4_next_prompt_selection_and_activation_v0_1
---
# Implement deterministic next-prompt selection and activation

## Objective

Implement deterministic next-prompt selection and bounded activation after a validated Blueprint review/roadmap/queue transaction.

## Scope

1. Read validated current Blueprint roadmap, prompt queue, dependency readiness, and accepted review state.
2. Select the next eligible prompt deterministically from the v0.4 workstream.
3. Activate at most one prompt and keep roadmap, queue, physical lifecycle, and handoff aligned.
4. Preserve dependency ordering and prompt-buffer health.
5. Emit immutable Blueprint-owned evidence for selection/activation.
6. Provide complete rollback across every Blueprint-owned path mutated by activation.

## Hard boundaries

- Do not implement Tracking Events v0.4 reference execution.
- Do not perform the dark-zone audit.
- Do not perform global v0.4 promotion.
- Do not write module repositories.
- Do not create automatic ACCEPT or RETURN decisions.
- Do not commit or push automatically.
- Do not perform rollout, production, or live-system writes.
