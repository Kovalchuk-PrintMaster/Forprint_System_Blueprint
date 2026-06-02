# Prompt: Apply ForPrint Module Coordination Standard

## Target

Apply this standard to the current ForPrint module repository.

## Purpose

Every ForPrint module must maintain a structured coordination directory in its own repository.

The goal is to let ForPrint System Blueprint / future ForPrint Control Plane collect the current ecosystem state through Git instead of manually copying reports from each module chat.

This standard is mandatory for all active ForPrint modules.

---

## Required directory

Create and maintain:

```text
coordination/
```

Required structure:

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

If the directory already exists, update it.

Do not use `docs/architecture/` for live status. Architecture docs are stable documentation. Coordination files are live project-control artifacts.

---

## Required current status file

Create or update:

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

---

## Required current status markdown

Create or update:

```text
coordination/status/current_status.md
```

It must include:

```text
1. Module current status.
2. Current phase.
3. Last completed step.
4. Latest checks.
5. Current capabilities.
6. Current boundaries.
7. What the module must not own.
8. Open questions.
9. Recommended next step.
10. Whether the module should continue, pause, or wait.
```

---

## Required prompts archive

Create:

```text
coordination/prompts/received/
coordination/prompts/index.yaml
```

When this module receives a major prompt from Blueprint / owner / assistant, store it under:

```text
coordination/prompts/received/YYYY-MM-DD__PROMPT-ID__short-title.md
```

Recommended prompt ID:

```text
YYYY-MM-DD__module-id__action-slug
```

Update:

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

---

## Required reports archive

Create:

```text
coordination/reports/completion/
coordination/reports/commits/
coordination/reports/index.yaml
```

After a macro pack / phase / meaningful milestone, create a completion report:

```text
coordination/reports/completion/YYYY-MM-DD__REPORT-ID__responds-to-PROMPT-ID__short-title.md
```

A completion report must include:

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

Update:

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

For small commits inside a larger pack, optional commit reports may be stored under:

```text
coordination/reports/commits/
```

---

## Questions for Blueprint

Create or update:

```text
coordination/status/next_questions_for_blueprint.md
```

Use it only for unresolved architectural questions.

---

## Required workflow after each meaningful milestone

After completing a phase or macro pack:

```bash
make clean
make check
make check-report
```

Then update coordination files:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/reports/completion/<report>.md
```

Then commit and push:

```bash
git status --short
git add .
git commit -m "<meaningful milestone message>"
git push
```

If the status update is part of a larger completed milestone, include it in the milestone commit.

---

## Safety rule

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

---

## Check-report integration

If the module has a check-report runner, extend it to validate that these files exist:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
```

The check-report should also validate that `current_status.yaml` contains:

```text
module_id
module_status
priority
checks
boundary
recommended_next_step
updated_at
```

---

## Expected response from module assistant

After applying this standard, return:

```text
Module Coordination Standard Applied

1. Files added/changed.
2. current_status.yaml summary.
3. current_status.md summary.
4. prompts/index.yaml summary.
5. reports/index.yaml summary.
6. Check-report validation added or deferred.
7. make check result.
8. make check-report result.
9. Commit hash.
10. Push status.
11. Any open questions.
```

---

## Final instruction

Apply this standard to the current ForPrint module.

Keep coordination files short, accurate, safe and continuously updated.

The goal is to let ForPrint System Blueprint / future Control Plane collect ecosystem-wide state automatically through Git.
