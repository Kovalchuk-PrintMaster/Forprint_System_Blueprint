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
