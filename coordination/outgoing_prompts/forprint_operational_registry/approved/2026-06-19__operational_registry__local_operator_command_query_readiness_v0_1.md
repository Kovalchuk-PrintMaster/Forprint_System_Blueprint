# Prompt: Operational Registry Local Operator Command/Query Readiness v0.1

## Target module

`forprint_operational_registry`

## Working directory

`/srv/software_development/forprint-project/forprint_operational_registry`

## Blueprint directory

`/srv/software_development/forprint-project/forprint_system_blueprint`

## Purpose

Continue ForPrint Operational Registry after the completed Local Launch Readiness + Completion Report Automation checkpoint.

This prompt must harden the module for local/offline operator command/query readiness.

The goal is not to add production runtime. The goal is to make the existing local operational registry foundation easier to use, verify, and hand off for internal offline operation.

## Current known baseline

The previous checkpoint completed:

`local_launch_readiness_completion_automation_v0_1`

Known completed commit:

`a119f50 Add local launch readiness completion automation`

Blueprint now includes the global completion packet template standard:

`e12167b Add completion packet template standard`

Operational Registry already has:

* Blueprint instruction intake visibility
* Blueprint standards visibility
* idempotent Blueprint snapshot sync
* local launch readiness docs
* completion packet validation/apply automation
* completion report generation through completion packets
* check-report rows for completion packet automation and Blueprint sync idempotency

## Hard rule

Use the local completion packet automation for the final completion report.

Do not manually update all coordination files one by one unless the completion packet automation itself requires a targeted repair.

## Make-first workflow requirement

This prompt must follow the Blueprint Make Command Standard v0.2.

Do not rely on long raw command sequences as the normal workflow.

Before implementing the main scope, add or align the module Makefile with the standard high-level workflow targets if they are missing:

```text
blueprint-prompts-list
blueprint-prompts-check
blueprint-prompts-sync
blueprint-prompts
prompt-read
blueprint-sync
module-start
module-sync
module-validate
module-finish
report-clean
completion-packet-check
```

The exact implementation may remain module-specific, but the external command names must be standardized.

Required start command:

make module-start

Required finalization command:

make module-finish PACKET=coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml

Required validation command:

make module-validate

## Required starting verification

Run the standardized start workflow:

```bash
make module-start
```

Expected behavior:

Blueprint repository is pulled.
Blueprint paths are checked.
Blueprint directives sync is executed or clearly deferred.
Blueprint instruction intake is listed, checked and synchronized.
Blueprint standards are listed, checked and synchronized.
Blueprint outgoing prompts are listed, checked and synchronized.
Module coordination metadata is checked.
Current module status is shown.
The active prompt is readable through make prompt-read.

If any required target is missing, implement or safely defer it according to the Blueprint Make Command Standard v0.2 before continuing.

## Required Blueprint standard review

Read the new Blueprint completion packet template standard:

```bash
sed -n '1,240p' /srv/software_development/forprint-project/forprint_system_blueprint/tools/completion_packet_template/README.md

sed -n '1,320p' /srv/software_development/forprint-project/forprint_system_blueprint/coordination/standards/module_prompt_completion_protocol.md
```

The final completion for this prompt must follow this standard.

## Hard boundaries

Do not add:

* production API
* FastAPI app
* live CRM integration
* live Telegram integration
* live Website integration
* real 1C sync/write
* production write
* automatic posting
* Accounting payment truth
* CRM dashboard
* Telegram runtime UI
* Calculator final price ownership
* Library catalog ownership
* Warehouse stock truth
* Prepress lifecycle ownership

Operational Registry remains the operational truth layer and internal data custodian.

Allowed in this prompt:

* local/offline operator runbooks
* local command/query readiness documentation
* local smoke checks
* local CLI/preview documentation
* check-report improvements
* completion packet example for this prompt
* safe examples only
* tests for local/offline validation

## Main goal

Create a clear local/offline operator command/query readiness layer.

It should answer:

“How can an operator or developer use the current Operational Registry foundation locally, without production API or live integrations, to inspect operational order/workflow/readiness state?”

## Required outputs

Add or update documentation under:

```text
docs/local_launch_readiness/
```

Required new docs:

```text
docs/local_launch_readiness/operator_command_query_readiness.md
docs/local_launch_readiness/local_operator_smoke_runbook.md
```

Update if needed:

```text
docs/local_launch_readiness/README.md
docs/local_launch_readiness/local_readiness_checklist.md
```

## operator_command_query_readiness.md requirements

Document the local/offline operator path:

```text
local fixture/context
→ command/query facade or preview entrypoint
→ order/workflow projection
→ blockers/readiness
→ terminal previews/reports
→ module status export
→ completion packet/report update
```

Must list existing local preview/check commands already available in the module.

Must clearly distinguish:

* command/write-like local operations
* query/read-only local operations
* previews
* reports/status exports
* coordination/completion operations

No production API should be introduced.

## local_operator_smoke_runbook.md requirements

Provide a step-by-step smoke runbook that can be executed locally.

It should include:

```bash
make blueprint-instruction-check
make blueprint-standards-check
make check-report
make check
make governance-check
```

It should also include available local preview targets such as order/workflow/payment/material/alert/report previews if they exist in the current Makefile.

The runbook must end with generated report cleanup commands so the working tree can remain clean.

## Optional script

If useful, add a small local-only smoke script:

```text
scripts/run_local_operator_readiness_smoke.py
```

This script must only call local/offline checks or inspect local fixture/config files.

It must not:

* start a web server
* call network services
* connect to 1C
* write production data
* require CRM/Telegram/Website/Library/Warehouse services

If added, expose it through a Makefile target:

```text
local-operator-readiness-smoke
```

## Check-report integration

Add check-report rows equivalent to:

```text
Local operator command/query readiness docs
Local operator smoke runbook
Local operator readiness smoke
```

The smoke row is required only if the script/Makefile target is added.

## Tests

Add or extend tests so that:

* local operator command/query readiness docs exist
* smoke runbook exists and contains required validation commands
* no production API/live integration scope is added
* if a smoke script is added, it runs successfully and is offline-only
* completion packet automation still validates and applies idempotently

## Completion packet requirement

Create a completion packet for this prompt:

```text
coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml
```

The packet must generate this completion report:

```text
coordination/reports/completion/2026-06-19__forprint_operational_registry__report__local-operator-command-query-readiness-v0-1.md
```

Use phase:

```text
local_operator_command_query_readiness_v0_1
```

Use prompt id:

```text
operational_registry_local_operator_command_query_readiness_v0_1
```

The packet must include:

* instruction_sources_reviewed
* standards_reviewed
* standards_alignment_notes
* boundary_confirmation
* checks
* current_outputs
* next_recommended_steps
* next_questions_for_blueprint

The final coordination update must be produced by:

```bash
make completion-packet-validate PACKET=coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml
make completion-packet-apply PACKET=coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml
make completion-packet-apply PACKET=coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml
```

The second apply must report no semantic changes.

## Required final validation

Use the standardized finish workflow:

```bash
make module-finish PACKET=coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml
```

Then run:

```bash
make module-validate
git status --short
```

Expected behavior:

completion packet validates;
completion packet applies;
completion packet apply is idempotent;
check-report passes;
check passes;
governance-check passes;
report-clean leaves the working tree reviewable;
status-report shows the updated phase;
no generated runtime reports remain dirty unless intentionally tracked as source-of-truth.

## Final response required

Return:

* changed files
* new/updated Makefile targets
* validation results
* completion packet path
* generated completion report path
* current status phase
* whether completion packet apply is idempotent
* whether Blueprint snapshot sync remains idempotent
* git status
* commit recommendation

Do not commit until checks are green and the user approves.
