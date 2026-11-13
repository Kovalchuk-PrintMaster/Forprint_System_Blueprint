# ForPrint Module Coordination Standard

## Status

Accepted

## Purpose

Every active ForPrint module must keep a structured coordination directory inside its own repository.

The goal is to let ForPrint System Blueprint / future Control Plane collect the real ecosystem state through Git instead of manually copying reports from module chats.

This standard covers:

```text
current status;
prompts received from Blueprint / owner / assistant;
completion reports;
commit/checkpoint reports;
open questions for Blueprint;
machine-readable indexes linking prompts, reports and commits.
```

## Required directory

Each active module repository must contain:

```text
coordination/
```

Recommended structure:

```text
coordination/
├── status/
│   ├── current_status.yaml
│   ├── current_status.md
│   └── next_questions_for_blueprint.md
│
├── prompts/
│   ├── received/
│   └── index.yaml
│
├── reports/
│   ├── completion/
│   ├── commits/
│   └── index.yaml
│
└── README.md
```

## Why this standard is needed

ForPrint has multiple active modules. The owner and Blueprint assistant must not manually collect scattered reports from separate chats.

Every module must publish its current state, received prompts and completion reports to Git.

Then the owner / Blueprint assistant can run `git pull` across repositories and see:

```text
which module is active;
which module is paused;
which module is blocked;
which prompt was issued;
which report answered the prompt;
which commit closed the work;
which module needs Blueprint decision;
which module should move next.
```

## Current status files

Required files:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
```

The main machine-readable file is:

```text
coordination/status/current_status.yaml
```

Required fields:

```yaml
module_id: ""
module_name: ""
module_status: ""
priority: ""
current_phase: ""
last_completed_step: ""
last_prompt_id: ""
last_report_id: ""
last_commit: ""
branch: "main"

checks:
  lint: ""
  tests: ""
  check_report: ""

boundary:
  no_foreign_ownership: true
  no_production_api: true
  no_live_write: true
  no_real_integrations: true

current_outputs: []

current_capabilities: []

active_work: []

paused_or_deferred: []

open_questions: []

recommended_next_step: []

risks: []

depends_on: []

blocks: []

updated_at: ""
```

Allowed `module_status` examples:

```text
active_development
bootstrap_development
boundary_correction_development
sandbox_development
reference_ready
storage_ready
sandbox_1c_import_export_ready
paused
hold
planned
deferred
```

Allowed `priority` examples:

```text
p0
p1
p2
hold
selective
deferred
```

## Prompt archive

Each module must store important prompts it receives from Blueprint / owner / assistant.

Directory:

```text
coordination/prompts/received/
```

Prompt file naming:

```text
YYYY-MM-DD__PROMPT-ID__short-title.md
```

Recommended prompt ID format:

```text
YYYY-MM-DD__module-id__action-slug
```

Example:

```text
2026-06-02__calculator_engine__calculation-output-package
```

Each prompt file should contain:

```text
prompt_id
target_module
source
date
purpose
allowed_scope
forbidden_scope
definition_of_done
expected_report_id
```

## Prompt index

Required file:

```text
coordination/prompts/index.yaml
```

Example:

```yaml
prompts:
  - prompt_id: "2026-06-02__calculator_engine__calculation-output-package"
    status: "received"
    source: "forprint_system_blueprint"
    received_at: "2026-06-02"
    file: "coordination/prompts/received/2026-06-02__calculator_engine__calculation-output-package.md"
    expected_report_id: "2026-06-02__calculator_engine__report__calculation-output-package"
    related_phase: "calculator_engine_vnext"
```

Allowed prompt statuses:

```text
draft
received
accepted
in_progress
completed
superseded
cancelled
blocked
```

## Completion reports

After each macro pack / phase / meaningful milestone, modules must create a completion report.

Directory:

```text
coordination/reports/completion/
```

File naming:

```text
YYYY-MM-DD__REPORT-ID__responds-to-PROMPT-ID__short-title.md
```

Recommended report ID format:

```text
YYYY-MM-DD__module-id__report__action-slug
```

A completion report should include:

```text
report_id
responds_to_prompt_id
module_id
completed_phase
files_added_changed
main_outputs
tests_added
check_results
boundary_confirmation
commit_hash
push_status
open_questions
recommended_next_step
```

## Commit/checkpoint reports

For smaller commits inside a larger macro pack, modules may maintain short commit reports.

Directory:

```text
coordination/reports/commits/
```

File naming:

```text
YYYY-MM-DD__COMMIT-SHA__short-title.md
```

Commit report should include:

```text
commit_hash
commit_message
related_prompt_id
related_report_id
what_changed
checks
remaining_work
```

Commit reports may be concise.

They are not a replacement for completion reports.

## Reports index

Required file:

```text
coordination/reports/index.yaml
```

Example:

```yaml
reports:
  - report_id: "2026-06-02__calculator_engine__report__calculation-output-package"
    responds_to_prompt_id: "2026-06-02__calculator_engine__calculation-output-package"
    status: "completed"
    report_file: "coordination/reports/completion/2026-06-02__calculator_engine__report__calculation-output-package.md"
    commit: "a1b2c3d"
    pushed: true
    checks:
      lint: "ok"
      tests: "ok"
      check_report: "ok"
```

Allowed report statuses:

```text
draft
completed
completed_with_warnings
failed
blocked
superseded
```

## Questions for Blueprint

Required file:

```text
coordination/status/next_questions_for_blueprint.md
```

Use it only for unresolved architectural questions.

Do not put routine implementation notes there.

Good examples:

```text
Should this module continue to v0.6 or pause?
Is production API approved or still deferred?
Should Gateway adapter planning begin now?
Which dependent module should be prioritized next?
```

## Required workflow after each meaningful milestone

After completing a phase or macro pack:

```bash
make clean
make check
make check-report
```

Then update:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/reports/completion/<report>.md
```

If the work was triggered by a Blueprint prompt, the report must reference the prompt ID.

Then commit and push:

```bash
git status --short
git add .
git commit -m "<meaningful milestone message>"
git push
```

## Safety rules

Coordination files must not contain:

```text
secrets
tokens
passwords
private client data
real accounting data
real 1C production data
personal data
large logs
binary files
temporary local paths with sensitive information
```

Only safe summaries are allowed.

## Check-report integration

If a module has a check-report runner, it should validate:

```text
coordination/status/current_status.yaml exists
coordination/status/current_status.md exists
coordination/status/next_questions_for_blueprint.md exists
coordination/prompts/index.yaml exists
coordination/reports/index.yaml exists
```

The check-report should also validate that:

```text
current_status.yaml contains module_id
current_status.yaml contains module_status
current_status.yaml contains priority
current_status.yaml contains checks
current_status.yaml contains boundary
current_status.yaml contains recommended_next_step
current_status.yaml contains updated_at
```

## Future aggregation

ForPrint Control Plane is planned but deferred.

Until Control Plane is active, ForPrint System Blueprint and the owner/assistant workflow will use these files manually.

Future flow:

```text
git pull module repositories
↓
read coordination/status/current_status.yaml
↓
read coordination/prompts/index.yaml
↓
read coordination/reports/index.yaml
↓
generate ecosystem status
↓
decide next priorities
```

## Final rule

Every active ForPrint module must keep its coordination files updated.

This is mandatory for synchronized ecosystem development.
