# Module Prompt Execution and Reporting Protocol

Status: active standard
Created/updated: `2026-07-07`

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
