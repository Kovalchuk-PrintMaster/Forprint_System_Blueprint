---
schema_version: outgoing_prompt_artifact_v0_1
prompt_id: replace_with_canonical_prompt_id_v0_1
target_module: replace_with_canonical_module_id
roadmap_step_id: example_roadmap_step_v0_1
title: Replace with a precise prompt title
phase: replace_with_canonical_phase_v0_1
priority: normal
created_at: "YYYY-MM-DD"
source_change: replace_with_blueprint_change_or_evidence
lifecycle_state: draft
lineage:
  supersedes: null
---
# Prompt: Replace with a precise prompt title

## Purpose

State one measurable purpose. This draft is non-executable until Blueprint
prepares and explicitly releases it.

## Context

Describe the architectural and operational context needed by the module.

## Required actions

1. Define the first required action.
2. Define the validation or evidence requirement.
3. Preserve explicit module boundaries.

## Blueprint references

- Add exact Blueprint paths and contracts.
- Do not use placeholders that cannot be resolved before preparation.

## Safety boundaries

- No writes outside the target module repository during module execution.
- No protected-branch merge unless separately authorized.
- No production or external side effect unless explicitly authorized.

## Expected completion evidence

List the exact report, tests, checks, commits and completion packet fields the
module must return.

For Logistics-pilot managed prompts, the machine payload SHOULD include an
`acceptance_handoff` mapping that declares the Prompt Contract path, Acceptance
Oracle path, stable acceptance criteria, and completion-packet evidence IDs.
Provider-specific research prompts MUST fail closed when current official
provider evidence is unavailable instead of inventing capabilities.
