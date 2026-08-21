# ForPrint Module Development Roadmap Policy

## Status

Target standard / gradual adoption v0.1

## Purpose

This document defines how ForPrint modules should describe planned development steps, current work position, priorities and roadmap visibility.

The goal is to make assistant/module progress visible without depending only on conversation memory.

A module operator should be able to see:

- what the module has already completed;
- what step is currently active;
- what is planned next;
- what is blocked or deferred;
- which steps are critical/high/normal/low priority;
- which steps may depend on other modules.

## Scope

This policy applies to module-level roadmap and assistant work planning metadata.

It does not replace Blueprint outgoing prompts.

It complements:

```text
Prompt Queue = exact executable prompt front.
Module Roadmap = broader development plan and progress map.
Coordination Document Awareness = policy/standard/document changes the module must notice.
```
Core model

A module roadmap is a sequenced list of development steps.

Each step should have:

step_id
sequence
title
status
priority
owner_module
scope
prompt_id
depends_on
expected_outputs
evidence
notes

Not every field must be fully populated during early adoption.

Unknown dependencies may be explicitly marked as pending analysis.

Roadmap statuses

Recommended statuses:

planned
ready
active
completed
accepted
paused
blocked
deferred
cancelled
superseded

Meanings:

planned     known future step, not ready yet
ready       can be started when operator chooses it
active      currently being worked on
completed   completed by module but not necessarily accepted by Blueprint
accepted    accepted by Blueprint/reviewer
paused      intentionally paused
blocked     cannot continue until a blocker is resolved
deferred    intentionally delayed, not blocking current work
cancelled   removed from plan
superseded  replaced by another step
Priorities

Recommended priorities:

critical
high
normal
low
reference

Meanings:

critical  should be handled before dependent work continues
high      important near-term work
normal    regular planned work
low       cleanup or gradual alignment
reference informational or optional

Priority colors should follow:

coordination/standards/visual_interface/color_tokens_policy.md
Roadmap window

Dashboards should support a limited view around the current step.

Recommended default:

before_current: 5
after_current: 10

For large modules, the dashboard should not print the entire roadmap by default.

It should show:

recent completed steps
current active step
next ready/planned steps
blocked/deferred high-priority items
## Planning horizon rule

For every module under active development, the canonical roadmap should normally keep **at least 5 meaningful future actionable parent steps**, target **8**, and impose **no maximum**. Larger horizons such as 15, 25, or 50 steps are valid when concrete, dependency-aware and useful; do not pad the roadmap with speculative work.

The horizon is a planning map, not an immutable contract. Steps may be split, merged, reordered, blocked, deferred or superseded as evidence changes, but the roadmap must continue to show a credible path forward.

Count toward the actionable horizon:

```text
ready
active
planned
```

Do not use these statuses to artificially satisfy the minimum:

```text
deferred
reference-only work
cancelled
superseded
```

After each Blueprint acceptance or material scope change:

1. review the current step;
2. verify that 8–10 actionable steps remain visible ahead;
3. refresh dependencies and priorities;
4. add, remove or reorder future steps;
5. keep only the immediate executable work in Prompt Queue.

Young modules may temporarily have fewer than eight future steps only when the uncertainty is explicit and the roadmap contains a dedicated discovery step to rebuild the horizon.

Multiple module comparison

Roadmap dashboards should support displaying more than one module when practical.

Example use cases:

compare Gateway, Library and CRM current work fronts
see which module is blocked by another module
decide which module to move forward next

A comparison dashboard should keep output compact.

It may show only:

module
current_step
current_status
next_ready_step
critical_blockers
high_priority_waiting
Dependency fields

Dependencies are allowed from the start but may be incomplete.

Recommended dependency types:

module_step
prompt
document
contract
external_decision
manual_review

A step may declare:

depends_on:
  - type: module_step
    module: forprint_library
    step_id: library_reference_contract_foundation_v0_2
    status: pending

During early adoption, dependencies may use:

status: pending_analysis

This is better than pretending the dependency map is complete.

Prompt relationship

A roadmap step may be linked to a Blueprint prompt.

Recommended fields:

prompt_id
prompt_file
prompt_queue_sequence

A prompt may implement one roadmap step or part of a roadmap step.

A roadmap step may also exist before the exact prompt is written.

Evidence

A completed or accepted roadmap step should include evidence where available:

module_commit
blueprint_acceptance_commit
completion_report
check_report
test_summary

Evidence may be added gradually.

Dashboard behavior

A roadmap dashboard should show semantic status and priority text.

Color is optional and must follow shared visual tokens.

Default dashboard should highlight:

active step
ready next step
blocked critical/high steps
recently completed steps

It should not require reading the whole roadmap file manually.

Machine-readable template

The starter template is:

coordination/templates/module_development_roadmap_v0_1.template.yaml

Canonical Blueprint roadmap storage

Blueprint-owned module roadmaps must use one canonical entrypoint file per module:

coordination/roadmaps/<module_id>.yaml

Examples:

coordination/roadmaps/forprint_library.yaml
coordination/roadmaps/forprint_crm.yaml
coordination/roadmaps/forprint_integration_gateway.yaml

This canonical file is the file resolved by roadmap validators, dashboards and summaries.

If a module later needs additional roadmap detail files, they may be stored under:

coordination/roadmaps/details/<module_id>/

Detail files must not replace the canonical module roadmap entrypoint.

Allowed:

coordination/roadmaps/forprint_library.yaml
coordination/roadmaps/details/forprint_library/reference_contract_phase.yaml

Avoid:

coordination/roadmap/module_development_roadmap.yaml
coordination/roadmaps/forprint_library/main.yaml

Gradual adoption rule

Young modules may start with a short roadmap.

Mature modules may expand roadmap steps and dependencies.

Missing dependency analysis should be explicit, not hidden.

Allowed:

dependency_status: pending_analysis

Avoid:

empty dependencies that imply there are no dependencies
Relationship to Prompt Queue

Prompt Queue controls the immediate next executable prompt.

Roadmap controls wider module development visibility.

A module should not use roadmap status as a replacement for prompt queue execution status.

When both exist:

Prompt Queue answers: what prompt should I execute next?
Roadmap answers: where am I in the broader plan?

## Hierarchical task detail (`substeps[]`) — v0.4.1 hardening

Roadmap steps remain the atomic Blueprint prompt/review/ACCEPT unit. A roadmap
step may optionally contain `substeps[]` when the parent title alone is not
sufficient to preserve implementation depth and history.

Rules:

- Existing roadmaps without `substeps[]` remain valid.
- Every substep has a stable `substep_id`, `title`, `status`, and optional
  `blocking` boolean (`true` by default).
- `substep_id` values are unique inside the roadmap document.
- Substep statuses use the roadmap's canonical status vocabulary.
- A parent claiming completion (`completed` or `accepted`) is invalid while a
  blocking substep remains unfinished.
- `cancelled` and `superseded` may close a parent with unfinished blocking
  substeps because those states do not claim implementation completion.
- Non-blocking substeps may remain unfinished after parent ACCEPT.
- Substeps describe internal scope/history of one atomic roadmap task.
- Normal new coordination should prefer one executable prompt bound to one
  parent `step_id`; acceptance criteria/evidence may bind to `substep_id`.
- Historical multi-step prompt bindings remain readable for compatibility.
- `roadmap-dashboard` remains compact/default.
- `make roadmap-detail MODULE=<module>` expands substeps.

This hardening does not rewrite existing roadmap data and does not advance any
roadmap or prompt queue.

## Acceptance oracle — v0.4.1 hardening

New roadmap work may opt into an explicit acceptance oracle:

```yaml
acceptance:
  oracle_required: true
  oracle_path: coordination/acceptance_oracles/<module>/<oracle>.yaml
  oracle_sha256: <lowercase_sha256>
```

Absence of `acceptance` remains valid for historical/legacy steps and does not
retroactively reinterpret sealed v0.4 decisions.

The canonical schema is `blueprint_acceptance_oracle_v0_1`. An oracle does not
create another requirements system. Every criterion MUST reference one or more
existing `IMP-*`, `VER-*`, or `CE-*` obligation IDs from one exact immutable
`module_prompt_contract_v0_4` instance bound by repository path and SHA-256.

Each criterion records stable `criterion_id`, parent `step_id`, optional
`substep_id`, `requirement_refs`, summary, `blocking`, verification kind,
exact verification locator, expected observation, and required evidence refs.

For `ACCEPT` on an oracle-required step, the review request must carry an
`acceptance_oracle_evaluation` bound to the same oracle path and SHA-256.
Every criterion has exactly one result: `PASS`, `FAIL`, or `NOT_EVALUATED`.

A blocking criterion authorizes ACCEPT only when it is `PASS` and every
declared required evidence reference is present. Otherwise ACCEPT is blocked
unless the same explicit operator request carries a criterion-specific waiver
with `explicit_operator_authorization: true` and a non-empty reason. Waivers
are copied into immutable Blueprint review evidence.

RETURN and HOLD do not require a passing oracle because they do not claim
acceptance. Oracle PASS never creates ACCEPT automatically. The gate is
evaluated before any roadmap, queue, prompt-file, or review-evidence mutation.


For oracle-gated ACCEPT, the evaluation MUST bind the exact review candidate
through `event_sha256`, `packet_sha256`, and
`discovery_fingerprint_sha256`. Blueprint stores those hashes with a canonical
SHA-256 fingerprint of the exact operator-supplied oracle evaluation in the
immutable decision evidence. Reapplying the same `decision_id` is idempotent
only when the candidate hashes and oracle-evaluation fingerprint are identical;
changed observed evidence, criterion results, evidence refs, waiver contents,
or candidate hashes fail safely as a conflicting decision identity.

The bound Prompt Contract MUST pass the canonical
`validate_prompt_contract_v0_4.validate_contract()` validator before any oracle
criterion may reference its obligation IDs. The oracle does not maintain a
parallel reduced Prompt Contract validator.


Acceptance evidence is grounded in the exact module-owned completion packet.
`evidence_required` and evaluation `evidence_refs` are stable `evidence_id`
values from that packet's `evidence_manifest`, not free-form labels. Before
ACCEPT, Blueprint verifies the candidate `packet_path` and `packet_sha256`,
reuses `validate_completion_packet_v0_4.validate_packet()`, rejects evidence
refs absent from the manifest, and requires each criterion `requirement_ref`
to be represented by at least one cited evidence ID that the validated packet
itself binds to that obligation. A waiver may bypass an unsatisfied blocking
criterion, but it cannot make an unknown/fabricated evidence reference valid.
