# Prompt: Library Make-First Semantic Reference Readiness v0.1

## Target module

`forprint_library`

## Working directory

`/srv/software_development/forprint-project/forprint_library`

## Blueprint directory

`/srv/software_development/forprint-project/forprint_system_blueprint`

## Purpose

Align ForPrint Library with the Blueprint Make Command Standard v0.2 and prepare a small semantic/reference readiness layer for downstream modules.

The goal is not to build the full production catalog.

The goal is to make Library easier to start, verify, and use as the canonical semantic/catalog authority for early Calculator, Operational Registry, Telegram Bot, and later CRM workflows.

## Strategic role reminder

ForPrint Library owns canonical semantic/catalog authority for:

```text
product/service naming
material naming
operation naming
aliases
technical card references
template references
contract definitions
semantic IDs
catalog meaning
```

Library must remain the semantic/catalog authority.

Library must not become:

```text
operational order registry
client database
payment/accounting truth
warehouse stock truth
CRM workflow engine
Telegram runtime adapter
Calculator pricing engine
production runtime controller
```

## Blueprint baseline

Use the current ForPrint System Blueprint.

Relevant Blueprint files:

```text
coordination/module_policy/forprint_library/module_policy.md
coordination/standards/make_command_standard.md
coordination/templates/module_makefile_standard.template.mk
coordination/outgoing_prompts/forprint_library/index.yaml
```

## Make-first workflow requirement

This prompt must follow the Blueprint Make Command Standard v0.2.

Do not rely on long raw command sequences as the normal workflow.

Before implementing the main semantic readiness scope, add or align the module Makefile with the standard high-level workflow targets if they are missing:

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

```bash
make module-start
```

Required validation command:

```bash
make module-validate
```

If completion packet automation is not yet implemented in Library, do not fake it. Either add a minimal safe implementation or clearly defer it and report the gap.

## Required starting verification

Run the standardized start workflow:

```bash
make module-start
```

Expected behavior:

* Blueprint repository is pulled.
* Blueprint paths are checked.
* Blueprint directives sync is executed or clearly deferred.
* Blueprint instruction intake is listed, checked and synchronized.
* Blueprint standards are listed, checked and synchronized.
* Blueprint outgoing prompts are listed, checked and synchronized.
* Module coordination metadata is checked.
* Current module status is shown.
* The active prompt is readable through `make prompt-read`.

If any required target is missing, implement or safely defer it according to the Blueprint Make Command Standard v0.2 before continuing.

## Main scope

After make-first alignment, implement a small semantic/reference readiness checkpoint.

This checkpoint should make Library more useful to other modules without expanding into a full catalog system.

Required direction:

```text
minimal semantic reference inventory;
stable sample canonical IDs;
alias/readiness examples;
downstream handoff notes for Calculator and Operational Registry;
clear boundaries for what Library owns and does not own;
check-report visibility for semantic readiness.
```

Suggested files may include existing or new Library-local equivalents of:

```text
docs/semantic_reference_readiness.md
docs/downstream_reference_contract_notes.md
examples/semantic_reference_preview.yaml
```

Use the module's existing structure where possible. Do not create duplicate concepts if better files already exist.

## Semantic readiness expectations

The checkpoint should show, at minimum:

```text
how a downstream module can refer to a canonical product/service/material/operation id;
how aliases are represented or planned;
how ambiguous naming should be reported;
how Library avoids owning pricing, stock, order state or accounting truth;
how local fixtures remain non-production and versioned.
```

## Required boundaries

Do not implement:

```text
production catalog database;
live API;
CRM integration;
Telegram integration;
Operational Registry write;
Calculator pricing logic;
warehouse stock logic;
accounting or payment logic;
1C sync/write;
automatic posting;
production runtime service.
```

Allowed:

```text
local docs;
local YAML/JSON examples;
local preview script if useful;
tests for semantic/reference examples;
check-report row showing readiness;
Makefile standard alignment.
```

## Required check-report visibility

If Library has a check-report runner, add or align rows for:

```text
Make-first workflow alignment
Semantic reference readiness
Blueprint prompt visibility
Blueprint standards visibility
```

If check-report is simpler at this stage, ensure the report clearly states whether each item is implemented, deferred, or warning-level.

## Required final validation

Use the standardized validation workflow:

```bash
make module-validate
```

If completion packet automation is available or added, also run:

```bash
make module-finish PACKET=coordination/completion_packets/examples/library_semantic_reference_readiness_v0_1.yaml
```

Expected behavior:

* check-report passes;
* check passes;
* governance-check passes;
* report-clean leaves the working tree reviewable;
* status-report shows the updated phase or readiness state;
* no generated runtime reports remain dirty unless intentionally tracked as source-of-truth.

## Final response required

Return:

```text
changed files
created or updated Makefile targets
semantic/reference readiness files
validation results
whether completion packet automation exists or is deferred
git status
commit recommendation
```

Do not commit until checks are green and the operator approves.
