# Prompt Queue Navigation Policy

## Purpose

This standard defines how ForPrint Blueprint should manage outgoing prompts, prompt queues, module execution state, and Blueprint review state.

The goal is to make prompt navigation explicit, auditable, and easy to inspect without relying on hardcoded active prompt paths in module Makefiles.

This policy replaces the habit of treating a single static prompt as the current work front.

## Problem

A prompt file may exist in Blueprint but still be invisible to a module if it is not indexed correctly.

A module may also keep reading an older prompt if its Makefile contains a hardcoded `ACTIVE_BLUEPRINT_PROMPT`.

This creates several problems:

```text
prompt exists != prompt is visible
prompt is indexed != prompt is next
module completed prompt != Blueprint accepted prompt
```

ForPrint must separate these states.

## Core Rule

Blueprint outgoing prompts should be managed as a queue.

Each module should have a prompt queue index that can show:

planned prompts
ready prompts
prompts in progress
prompts completed by module
prompts accepted by Blueprint
prompts returned for fixes
superseded prompts
blocked prompts

The queue must distinguish between module execution and Blueprint review.

## Prompt Queue v0.2

The preferred schema version is:

schema_version: prompt_queue_v0_2
module: forprint_library

prompt_queue:
  - prompt_id: library_reference_contract_foundation_v0_2
    sequence: 2
    title: Library Reference Contract Foundation v0.2
    file: approved/2026-06-29__library__reference_contract_foundation_v0_2.md
    target_module: forprint_library
    phase: reference_contract_foundation_v0_2
    priority: high

    module_execution:
      status: ready_for_module_pull
      completion_commit: null
      completion_report: null
      completed_at: null

    blueprint_review:
      status: not_started
      acceptance_commit: null
      accepted_at: null
      review_notes: null
## Required Separation

Prompt queue records must separate:

module_execution.status
blueprint_review.status

This avoids treating module completion as Blueprint acceptance.

A prompt can be:

completed by module

without being:

accepted by Blueprint
## Module Execution Statuses

Allowed module execution statuses:

planned
ready_for_module_pull
in_progress
completed_by_module
returned_for_fix
paused
blocked
superseded
## Blueprint Review Statuses

Allowed Blueprint review statuses:

not_started
pending_review
accepted_by_blueprint
returned_for_fix
not_required
superseded
## Priority

Allowed priority values:

critical
high
normal
low
reference

Priority controls operator attention, not automatic execution.

High-priority prompts should be considered before lower-priority prompts, but sequence order remains the main navigation rule inside one module queue.

## Sequence

Each prompt should have a numeric sequence.

The sequence is module-local.

Example:

forprint_library:
  1 make-first semantic readiness
  2 reference contract foundation
  3 reference resolution preview

If an older sequence remains unfinished while a later prompt is already in progress, dashboards should mark the older unfinished prompt as a warning.

## Prompt File

The file field is relative to the module outgoing prompt directory.

Example:

file: approved/2026-06-29__library__reference_contract_foundation_v0_2.md

For module forprint_library, this resolves to:

coordination/outgoing_prompts/forprint_library/approved/2026-06-29__library__reference_contract_foundation_v0_2.md
## Dashboard Behavior

A prompt dashboard should show at minimum:

sequence
prompt_id
title
priority
module_execution.status
module_execution.completion_commit
blueprint_review.status
blueprint_review.acceptance_commit
file

Terminal dashboards may use color.

Recommended colors:

bright green = accepted_by_blueprint
light green  = completed_by_module
yellow       = in_progress
orange       = ready_for_module_pull
red          = blocked / returned_for_fix / skipped older work
gray         = planned
cyan         = reference / not_required / superseded

Markdown and JSON reports must not rely only on color. They must include explicit status text.

## Next Prompt Resolution

The next prompt for a module should be resolved from the queue, not from a hardcoded Makefile variable.

The resolver should select the first prompt by sequence where:

module_execution.status == ready_for_module_pull

If no ready prompt exists, it may report:

no ready prompt

If there are blocked or returned prompts before the next ready prompt, the resolver should report them as warnings.

## Manual Prompt Delivery During Transition

During early migration, prompts may still be delivered manually to module assistants.

This is acceptable while Prompt Queue v0.2 tooling is being built.

However, new automation should target Prompt Queue v0.2 directly.

Do not extend legacy hardcoded active prompt behavior unless required for emergency compatibility.

## Legacy Active Prompts

The older active_prompts structure is considered legacy.

It may remain temporarily for old modules, but new development should not depend on it.

New tooling should prefer:

prompt_queue

instead of:

active_prompts
## Module Makefile Rule

Module Makefiles should eventually support:

make prompt-dashboard
make prompt-next
make prompt-read-next

These targets should use Blueprint prompt queue tooling.

Until migrated, module assistants may receive explicit prompt paths from the operator.

## Source of Truth

The source of truth is the structured prompt queue index.

Generated outputs are not source of truth.

Source of truth:

coordination/outgoing_prompts/<module>/index.yaml
completion reports
Blueprint acceptance records
git commits

Generated outputs:

terminal tables
markdown dashboards
json dashboards
## No Manual Dashboard Editing

Prompt dashboard files should be generated.

Operators and assistants should not manually maintain status tables.

Manual edits should be limited to meaningful state changes in YAML records, such as:

new prompt added
prompt marked ready
module completion commit recorded
Blueprint review status recorded
prompt superseded
## Migration Rule

Do not migrate all modules at once.

Preferred migration order:

1. Blueprint policy and template
2. new validator
3. new dashboard renderer
4. Library pilot
5. Make target standard update
6. gradual module adoption
## Summary

Prompt navigation should be:

queue-based
status-aware
module-aware
Blueprint-review-aware
auditable
dashboard-friendly
not hardcoded to one prompt path

## Draft / planned prompt visibility

Draft prompt files may live under:

```text
coordination/outgoing_prompts/<module>/drafts/
```

Draft prompts are planning artifacts.

They may be shown in the prompt dashboard so Blueprint and module assistants can see future planned work.

Draft prompts may be read for awareness, but they must not be executed until Blueprint promotes them into the active prompt queue.

A draft prompt must not be returned by:

make prompt-next
make prompt-read-next

Promotion from draft to active work requires an explicit Blueprint action:

move or copy the prompt into approved/;
register it in index.yaml prompt_queue;
assign sequence, priority and execution status;
run prompt queue validation.

The dashboard should visually separate active queue prompts from draft/planned prompts.

Recommended dashboard behavior:

active prompt queue first;
current ready prompt marked with an arrow;
status color applied to the whole active row;
draft/planned prompts shown in a separate muted section;
draft prompts never treated as executable work.
