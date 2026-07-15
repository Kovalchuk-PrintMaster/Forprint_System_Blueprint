# Module Prompt Execution and Reporting Protocol

Status: active standard
Created/updated: `2026-07-14`

## Purpose

This protocol defines the global prompt execution and reporting workflow for all ForPrint module assistants.

It connects the existing Blueprint prompt queue, module-side prompt reading, module-side completion reporting, completion packet automation and Blueprint-side review flow into one end-to-end protocol.

This is a global protocol. It is not specific to Library, Telegram Bot, Website, Calculator Engine, Operational Registry or any other single module.

## Scope

This protocol applies to every ForPrint module that receives work from ForPrint System Blueprint, including but not limited to:

- `forprint_library`
- `telegram_bot`
- `website`
- `calculator_engine`
- `forprint_operational_registry`
- `forprint_integration_gateway`
- `forprint_accounting_registry_service`
- `forprint_prepress_hub`
- future channel assistants and services

## Core rule

A module may read Blueprint prompts, standards, dashboards and context bundles.

A module must write only inside its own repository.

A module assistant must not directly create, update, copy or commit files inside the Blueprint repository unless the current working repository is explicitly `forprint_system_blueprint` and the active task is a Blueprint task.

Blueprint-side incoming reports, review records, acceptance metadata and prompt queue updates are created only from the Blueprint context.

## Repository ownership boundary

### Module repository

A module repository owns its own implementation and coordination records.

A module may update:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/reports/index.yaml
coordination/reports/completion/*.md
coordination/prompts/index.yaml
module source code
module tests
module docs
module local tooling

A module may not update:

/srv/software_development/forprint-project/forprint_system_blueprint/...

from a module-side task.

Blueprint repository

Blueprint owns:

coordination/outgoing_prompts/<module_id>/
coordination/outgoing_prompts/<module_id>/index.yaml
coordination/standards/
coordination/templates/
coordination/incoming_reports/
Blueprint review metadata
Blueprint acceptance metadata
Blueprint prompt queue state

Blueprint may import, copy or register a module completion report into a Blueprint-side intake location, but this is a Blueprint-side action.

End-to-end workflow

The normal prompt execution loop is:

Blueprint creates or updates an outgoing prompt for a module.
Blueprint registers the prompt in coordination/outgoing_prompts/<module_id>/index.yaml.
The module pulls or reads Blueprint state using approved Make targets.
The module resolves the next active prompt from the prompt queue.
The module executes the prompt only in its own repository.
The module creates or updates its module-side completion artifacts.
The module updates its own coordination records.
The module runs validation, tests and governance checks.
The module commits and pushes its own repository.
Blueprint reads the module-side report.
Blueprint may create a Blueprint-side incoming report record.
Blueprint reviews the result.
Blueprint updates prompt queue execution and review metadata.
Blueprint commits and pushes its own repository.
Prompt reading

Modules should use queue-based prompt navigation.

Preferred targets:

make blueprint-pull
make prompt-dashboard
make prompt-next
make prompt-read-next

A module must read only its own prompt queue:

coordination/outgoing_prompts/<module_id>/index.yaml

A module must not self-assign work from another module queue.

A module must not execute draft prompts.

Draft prompts may be read for awareness only. They become executable only after Blueprint promotes them into the active prompt queue.

Module-side execution

After reading a prompt, the module assistant should:

check the working tree;
confirm the prompt target module matches the current module;
review applicable standards;
implement only the prompt scope;
keep unrelated changes out of the checkpoint;
avoid live external integrations unless explicitly approved;
avoid production writes unless explicitly approved;
update tests and documentation as required;
prepare module-side completion reporting.
Completion reporting automation

Manual editing of several coordination files is not the preferred workflow.

When completion packet automation is available, a module assistant should use it instead of manually synchronizing duplicated metadata across multiple files.

Preferred workflow:

completion packet
completion-packet-validate
completion-packet-apply
completion-packet-check
git diff review
module validation
commit/push

The completion packet workflow should update or generate:

coordination/reports/completion/<report>.md
coordination/reports/index.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md

The assistant should review the generated diff before committing.

Completion automation boundary

Module-side completion automation may write only inside the module repository.

Completion scripts must not write into the Blueprint repository.

Completion scripts that accept paths must validate that generated or modified paths stay under the module root.

Completion scripts may include Blueprint prompt paths as read-only metadata, but must not modify those Blueprint files.

A module-side completion script must not perform Blueprint-side intake, Blueprint review, prompt queue acceptance or Blueprint metadata commits.

Deferred automation

A module may temporarily expose deferred-safe completion targets when full completion packet automation is not yet configured.

Deferred-safe behavior is allowed only if it is explicit and does not fake successful automation.

Acceptable deferred-safe behavior:

print that completion packet automation is not configured;
make no file changes;
return success only for compatibility if the module checkpoint does not require packet application;
document the deferral in the completion report or status.

Deferred-safe targets should later be replaced with real packet validation and application.

Manual fallback

Manual completion reporting is allowed only as a fallback when completion automation is not yet available or when Blueprint explicitly requests a manual transition checkpoint.

When manual fallback is used, the assistant must still keep module-side ownership boundaries:

write module report in module repo;
update module status in module repo;
update module reports index in module repo;
do not write into Blueprint repo.

Manual fallback should not become the normal workflow for active modules.

Blueprint-side incoming reports

Blueprint may keep a received copy or metadata record for module reports.

Recommended Blueprint-side path:

coordination/incoming_reports/<module_id>/index.yaml
coordination/incoming_reports/<module_id>/completion/<report>.md

Recommended incoming report statuses:

received_pending_blueprint_review
accepted_by_blueprint
returned_for_fix
superseded

This is Blueprint-owned metadata.

A module assistant must not create or update these files from a module-side task.

Blueprint review

Blueprint review should update the prompt queue record separately for:

module_execution.status
module_execution.completion_commit
module_execution.completion_report
blueprint_review.status
blueprint_review.acceptance_commit
blueprint_review.review_notes

Module completion is not the same as Blueprint acceptance.

A prompt can be completed by the module while still pending Blueprint review.

Make target expectations

Active modules should gradually support:

make module-start
make module-sync
make module-validate
make module-finish

make prompt-dashboard
make prompt-next
make prompt-read-next

make completion-packet-validate
make completion-packet-apply
make completion-packet-check

make coordination-check
make governance-check
make check
make check-report

module-finish should run validation and completion reporting checks, but must not perform Blueprint-side review or Blueprint-side intake.

Forbidden patterns

Module assistants must not:

copy files into forprint_system_blueprint from module context;
edit Blueprint prompt queues from module context;
mark their own Blueprint review as accepted;
commit Blueprint metadata from a module repository;
treat draft prompts as executable work;
treat module completion as Blueprint acceptance;
manually maintain duplicated completion metadata when automation exists;
write generated reports outside the module root.
Allowed patterns

Module assistants may:

read Blueprint outgoing prompts;
read Blueprint standards;
read Blueprint dashboards;
read context bundles;
write module-local reports;
write module-local current status;
write module-local next questions for Blueprint;
commit and push module-local changes;
ask Blueprint to review completion output.

Blueprint assistants may:

read module reports;
copy or register module reports into Blueprint incoming_reports;
update Blueprint prompt queues;
record Blueprint review status;
issue the next prompt;
commit and push Blueprint-side metadata.
Relationship to other standards

This protocol connects and clarifies:

coordination/standards/module_outgoing_prompt_pull_protocol.md
coordination/standards/module_prompt_completion_protocol.md
coordination/standards/module_coordination_records_protocol.md
coordination/standards/governance/prompt_queue_navigation_policy.md
coordination/standards/make_command_standard.md
coordination/templates/module_makefile_standard.template.mk

If these documents conflict, this protocol controls the cross-repository write boundary and the end-to-end execution/reporting loop.

<!-- blueprint-completion-finalization-v0-1:start -->

## Blueprint completion intake and finalization

Module-side completion and Blueprint-side acceptance are separate operations.

The module finishes its own work first:

```text
module implementation
-> module checks
-> completion packet
-> module completion report
-> module commit and push
```

Blueprint then performs an independent finalization flow:

```text
completion intake preview
-> evidence validation
-> Blueprint decision
-> review packet
-> prompt queue update
-> roadmap evidence update
-> documented next-work suggestion
```

### Blueprint intake commands

Preferred Blueprint commands:

```text
make completion-intake-preview MODULE=<module> MODULE_ROOT=<path> PACKET=<module-relative-packet>
make completion-accept MODULE=<module> MODULE_ROOT=<path> PACKET=<module-relative-packet>
make completion-return MODULE=<module> MODULE_ROOT=<path> PACKET=<module-relative-packet> REVIEW_NOTES="..."
make completion-finalize-check MODULE=<module>
```

`completion-intake-preview` must not write files.

`completion-accept` and `completion-return` require an explicit operator decision and write only inside the Blueprint repository.

### Completion evidence validation

Blueprint intake must verify, where available:

```text
module id;
prompt id;
completion report path;
implementation commit;
completion commit;
remote containment of completion commit;
push status;
required successful checks;
boundary confirmations;
prompt queue record;
roadmap step.
```

The intake tool may normalize both boundary flag styles during transition:

```text
no_<unsafe_behavior>: true
<unsafe_behavior>_added: false
```

Unsafe or ambiguous boundary values must block acceptance.

### Review packet

Every written Blueprint decision creates or updates a deterministic review packet under:

```text
coordination/review_packets/<module_id>/processed/
```

The review packet is the stable Blueprint evidence record.

The existing `blueprint_review.acceptance_commit` field may remain `null`. A Git commit cannot safely contain its own final hash. Git history identifies the commit that introduced the review packet and queue/roadmap update.

### Idempotency

Repeating the same intake command with the same:

```text
packet;
completion commit;
decision;
review date;
review notes
```

must produce no additional diff.

The tool must not duplicate prompt queue records, roadmap evidence or review packets.

## Next-work recommendation hierarchy

Blueprint automation must not invent the content of a new prompt.

The documented source hierarchy is:

```text
1. current approved prompt that is ready or in progress;
2. draft prompt matching the next roadmap step;
3. next non-completed roadmap step;
4. explicit NEXT_WORK_UNDEFINED warning.
```

Preferred command:

```text
make next-work-suggestion MODULE=<module_id>
```

### Active approved prompt

When an approved prompt has execution status `ready_for_module_pull` or `in_progress`, the result is:

```text
ACTIVE_PROMPT_EXISTS
```

The module should continue or pull that prompt. Draft and roadmap recommendations remain secondary.

### Matching draft candidate

When no approved prompt is active and exactly one draft matches the next roadmap step, the result is:

```text
DRAFT_CANDIDATE_FOUND
```

The system proposes the draft for human review. It does not promote or activate the draft automatically.

Multiple matching drafts produce:

```text
MULTIPLE_DRAFT_CANDIDATES
```

Drafts that do not match the next roadmap step produce:

```text
DRAFT_ROADMAP_CONFLICT
```

### Roadmap fallback

When no active approved prompt and no matching draft exist, but the roadmap contains a next step, the result is:

```text
ROADMAP_PROMPT_NEEDED
```

The suggestion must show only documented roadmap fields such as:

```text
sequence;
step_id;
title;
status;
priority;
summary;
expected_outputs;
dependencies.
```

This is a prompt-authoring hint, not generated business scope.

### Undefined next work

When neither draft nor roadmap defines the next work, the result is:

```text
NEXT_WORK_UNDEFINED
```

Blueprint must update the roadmap before issuing another prompt.

### Promotion boundary

Draft promotion and approved prompt activation are explicit future write operations.

A draft must never become executable merely because it exists in `drafts/`.

Before promotion, Blueprint must verify:

```text
target module;
prompt id uniqueness;
roadmap step match;
sequence;
dependencies;
scope;
outgoing prompt validation.
```

<!-- blueprint-completion-finalization-v0-1:end -->

## Compact tabular final handoff

Routine module completion handoffs should use one or more compact boxed tables when terminal table rendering is available.

Recommended concern groups include:

```text
implementation result;
tests and validation;
boundaries and safety;
coordination lifecycle;
warnings, blockers and decisions;
artifact and commit paths.
```

The number of tables and rows is determined by readability and risk, not by a rigid universal line limit.

For a normal module, output near or below 100 lines is a useful guideline. Larger architectures may require more rows. When a failure needs deep investigation, extended diagnostics may be unlimited and should be stored in a file with a stable path.

Modules must use the applicable visual-interface standards referenced by:

```text
coordination/standards/visual_interface/index.yaml
```

Color is supplementary. Status text, counts and markers must remain understandable in plain text.

## Documentation and recovery gate

Meaningful coordination and automation changes must follow:

```text
coordination/standards/governance/documentation_and_recovery_gate.md
```

Important workflow decisions must not remain only in chat history.

The repository must preserve enough architecture, operations, recovery, test and completion evidence for another assistant to resume safely after context loss or assistant replacement.
