# ForPrint Make Command Standard

## Status

Target standard / gradual adoption v0.2

## Purpose

This document defines common Makefile command names and Makefile structure for ForPrint modules.

The goal is to make module work predictable.

A developer or assistant should be able to run similar commands across modules without learning a completely different command surface every time.

## Core rule

Command names should be standardized.

Implementation may differ per module.

Example:

```text
make test
```

may run Django tests in one module, pytest in another module and shell checks in a utility module.

The external command name should remain consistent.

## Make-first workflow rule

Blueprint prompts and module assistants should prefer standardized Make targets over long raw command sequences.

Raw commands are implementation details.

Allowed in prompts:

```text
make module-start
make module-validate
make module-finish PACKET=coordination/completion_packets/examples/<packet>.yaml
```

Avoid in prompts:

```text
manual git pull;
manual sed path reads;
manual script calls;
manual completion report edits;
manual report cleanup.
```

Raw commands may still be used for debugging, inspection, or one-off repairs, but the normal module workflow should converge on Make targets.

## Makefile structure rule

Every active module should gradually organize its Makefile into visually separated thematic blocks.

The exact commands inside each block may differ by module, but the block structure should remain stable enough for quick navigation.

Recommended visual separator:

```make
# =============================================================================
# 00 Environment / constants START
# =============================================================================

# Purpose: define local runtime constants, Python binary, Blueprint path and colors.
# Result: shared variables are available to all targets.

# =============================================================================
# 00 Environment / constants FINISH
# =============================================================================
```

Every public target should have a short comment before it:

```make
# Purpose: run the main local validation flow before commit.
# Result: lint, tests and module validation pass or return non-zero.
.PHONY: check
check:
	$(MAKE) lint-fix
	$(MAKE) lint
	$(MAKE) test
```

## Makefile architecture / zoning rule

A module Makefile is not only a command list.

It is the operator control surface for the module and must be organized as a stable map.

Commands must be placed into the closest existing thematic zone.

New public commands should not be appended randomly at the bottom of the file.

Blueprint and coordination workflows are first-class operator workflows and should appear near the top of the Makefile after constants and help/navigation.

Module runtime, infrastructure, database, adapter, preview, diagnostic, test and validation commands must be grouped into their own zones.

If a command does not fit an existing zone, a new zone may be proposed, but the reason should be clear.

Empty or deferred zones are allowed in templates and young modules.

Young modules should not be forced to keep hundreds of unused deferred targets, but the Blueprint template must document the available zones and recommended target names.

A module may implement only the zones and commands it currently needs.

When a new command appears later, it should be inserted into the correct zone instead of creating a chaotic module-specific layout.

Public targets should have a short comment before them:

- Purpose: what the target is for.
- Result: what changes or validation result the operator should expect.

Composite targets should call other Make targets using `$(MAKE)` instead of duplicating long command bodies.

Standard ForPrint Makefiles must use the normal Makefile recipe format with TAB-prefixed recipe lines.

`.RECIPEPREFIX` must not be used in standard module Makefiles because it creates formatting differences between modules.


## Recommended Makefile blocks

Use numeric prefixes to keep block order stable.

Empty blocks are allowed during gradual adoption. If a block has no commands yet, keep a clear deferred note.

Recommended blocks:

```text
00 Environment / constants
01 Help / navigation

02 Operator entrypoints / Blueprint-first workflow
03 Blueprint repository synchronization
04 Blueprint instruction intake
05 Blueprint standards and policies
06 Blueprint outgoing prompts / prompt queue
07 Blueprint document awareness
08 Module coordination metadata
09 Module governance / policy checks

10 Module install / bootstrap
11 Module environment / local configuration
12 Runtime control / process lifecycle
13 Infrastructure / local services
14 Database / storage / migrations
15 Data import / export / fixtures
16 External adapters / sandbox integrations
17 Local previews / operator workflows
18 Observability / diagnostics / logs

19 Syntax / formatting / lint
20 Tests
21 Validation / check reports
22 Status reports / generated reports / cleanup
23 Completion packet / prompt finalization
24 Git / release / commit helpers

90 Module-specific helpers
```

## Recommended target placement

Typical targets should be placed into these zones.

### 02 Operator entrypoints / Blueprint-first workflow

- make module-start
- make module-sync
- make module-validate
- make module-finish

### 03 Blueprint repository synchronization

- make blueprint-pull
- make blueprint-check
- make blueprint-sync
- make blueprint-sync-directives

### 04 Blueprint instruction intake

- make blueprint-instruction-list
- make blueprint-instruction-check
- make blueprint-instruction-sync
- make blueprint-instruction

### 05 Blueprint standards and policies

- make blueprint-standards-list
- make blueprint-standards-check
- make blueprint-standards-sync
- make blueprint-standards

### 06 Blueprint outgoing prompts / prompt queue

- make blueprint-prompts-list
- make blueprint-prompts-check
- make blueprint-prompts-sync
- make blueprint-prompts
- make prompt-read
- make prompt-queue-validate
- make prompt-dashboard
- make prompt-next
- make prompt-read-next

### 07 Blueprint document awareness

- make document-manifest
- make document-manifest-write
- make document-awareness
- make context-bundle
- make context-bundle-write
- make context-bundle-print
- make document-ledger-preview
- make document-ledger-update

### 08 Module coordination metadata

- make coordination-check
- make coordination-fix
- make status-report

### 09 Module governance / policy checks

- make module-policy-check
- make governance-check

### 10 Module install / bootstrap

- make install
- make bootstrap

### 11 Module environment / local configuration

- make env-check
- make config-check
- make secrets-check

### 12 Runtime control / process lifecycle

- make run
- make start
- make stop
- make restart
- make reload
- make status
- make logs

### 13 Infrastructure / local services

- make services-up
- make services-down
- make services-restart
- make services-status
- make workers-start
- make workers-stop
- make workers-restart

### 14 Database / storage / migrations

- make db-check
- make db-migrate
- make db-upgrade
- make db-downgrade
- make db-seed
- make db-reset

### 15 Data import / export / fixtures

- make fixtures-check
- make fixtures-load
- make import-preview
- make export-preview

### 16 External adapters / sandbox integrations

- make adapters-check
- make adapters-smoke
- make sandbox-check
- make sandbox-sync

### 17 Local previews / operator workflows

- make preview
- make smoke
- make operator-demo

### 18 Observability / diagnostics / logs

- make diagnostics
- make health
- make inspect

### 19 Syntax / formatting / lint

- make lint
- make lint-fix
- make format
- make format-check

### 20 Tests

- make test
- make test-unit
- make test-contract
- make test-integration

### 21 Validation / check reports

- make check
- make check-report

### 22 Status reports / generated reports / cleanup

- make status-report
- make report-clean

### 23 Completion packet / prompt finalization

- make completion-packet-validate
- make completion-packet-apply
- make completion-packet-check

### 24 Git / release / commit helpers

- make git-status
- make release-check

### 90 Module-specific helpers

Module-specific helper targets that do not belong to shared zones.

These targets should still follow the Purpose/Result comment rule.

## Optional console colors

Make may use ANSI colors for readable console output.

Recommended optional constants:

```make
COLOR_RESET ?= \033[0m
COLOR_BOLD ?= \033[1m
COLOR_GREEN ?= \033[32m
COLOR_YELLOW ?= \033[33m
COLOR_BLUE ?= \033[34m
COLOR_CYAN ?= \033[36m
COLOR_RED ?= \033[31m
```

Color must be cosmetic only.

A module should still be readable without color.

If a module supports `NO_COLOR=1`, color output should be disabled.

## Composite target rule

Composite targets should call other Make targets using `$(MAKE)`.

Preferred:

```make
blueprint-sync:
	$(MAKE) blueprint-pull
	$(MAKE) blueprint-check
	$(MAKE) blueprint-instruction
	$(MAKE) blueprint-standards
	$(MAKE) blueprint-prompts
```

Avoid duplicating long raw command bodies inside composite targets.

This keeps workflows easy to inspect and easy to override per module.

## Required / preferred targets

Every active module should gradually support:

```text
make install
make lint
make lint-fix
make test
make check
make check-report
make status-report
make report-clean

make blueprint-pull
make blueprint-check
make blueprint-sync-directives

make blueprint-instruction-list
make blueprint-instruction-check
make blueprint-instruction-sync
make blueprint-instruction

make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync
make blueprint-standards

make blueprint-prompts-list
make blueprint-prompts-check
make blueprint-prompts-sync
make blueprint-prompts
make prompt-read
make prompt-queue-validate
make prompt-dashboard
make prompt-next
make prompt-read-next

make document-manifest
make document-manifest-write
make document-awareness
make context-bundle
make context-bundle-write
make context-bundle-print
make document-ledger-preview
make document-ledger-update

make blueprint-sync

make coordination-check
make coordination-fix
make module-policy-check
make governance-check

make completion-packet-validate
make completion-packet-apply
make completion-packet-check

make module-start
make module-sync
make module-validate
make module-finish
```

## Shared variables

Modules may support these Make variables:

```text
PACKET=path/to/completion_packet.yaml
PROMPT=prompt_id_or_path
BLUEPRINT_ROOT=/path/to/forprint_system_blueprint
MODULE_ID=forprint_module
SCOPE=bootstrap
LIMIT=40
NO_COLOR=1
MODULE_DOCUMENT_AWARENESS_LEDGER=coordination/blueprint_awareness/make_command_standard.md
MODULE_DOCUMENT_AWARENESS_LEDGER=coordination/blueprint_awareness/document_review_ledger.yaml

STATUS=acknowledged
DOCUMENT=coordination/global_policy/forprint_project_doctrine.md
SOURCE=global_policy
PRIORITY=critical
NOTES=review note
MODULE_COMMIT=abc123
```

A module may define `BLUEPRINT_ROOT` internally.

Hard-coding the local Blueprint path is allowed during early adoption, but new modules should prefer a variable.

## install

Purpose:

```text
Install development dependencies.
```

Expected behavior:

```text
create/use venv if project standard defines it;
install package requirements;
prepare project for local checks.
```

## lint

Purpose:

```text
Run configured linter without modifying files.
```

Preferred behavior:

```text
python -m ruff check app scripts tests
```

Module-specific paths are allowed.

## lint-fix

Purpose:

```text
Run configured linter with safe automatic fixes.
```

Preferred behavior:

```text
python -m ruff check app scripts tests --fix
```

## test

Purpose:

```text
Run the module test suite.
```

Expected behavior:

```text
run all current tests required for module confidence;
return non-zero on failure.
```

## check

Purpose:

```text
Run the main local validation flow.
```

Preferred sequence:

```text
lint-fix;
lint;
test;
module-specific validations;
coordination checks if available.
```

`make check` should be the main command before commit.

## check-report

Purpose:

```text
Run module checks and generate human/machine reports.
```

Expected outputs:

```text
reports/<module>_check_report.json
reports/<module>_check_report.md
```

Console output should be easy to read.

`make check-report` should not leave tracked generated reports dirty unless those reports are intentional source-of-truth artifacts.

## status-report

Purpose:

```text
Generate or show the current module status report without running the full validation suite.
```

Expected behavior:

```text
read coordination/status/current_status.yaml;
read coordination/status/current_status.md where useful;
print a concise current module status summary;
optionally refresh reports/module_status.json or reports/module_status.md if the module supports it.
```

Difference from check-report:

```text
check-report = run checks and generate validation report;
status-report = show/export current coordination and development status.
```

The command should not fake successful checks.

If current status is stale or incomplete, it should report that clearly.

## report-clean

Purpose:

```text
Clean or restore generated reports so the working tree remains reviewable.
```

Expected behavior:

```text
remove ignored generated check reports;
restore tracked generated runtime reports only when they are not source-of-truth;
leave coordination reports and completion reports untouched.
```

Allowed examples:

```text
rm -f reports/<module>_check_report.json reports/<module>_check_report.md;
git restore -- reports/<tracked_generated_report>.json reports/<tracked_generated_report>.md.
```

The command must not delete source documentation or committed coordination reports.

## blueprint-pull

Purpose:

```text
Update the local ForPrint System Blueprint repository.
```

Expected behavior:

```text
git -C $(BLUEPRINT_ROOT) pull --ff-only
```

## blueprint-check

Purpose:

```text
Verify that required Blueprint paths exist and are readable.
```

Should check, where applicable:

```text
coordination/global_policy/
coordination/standards/
coordination/module_policy/<module_id>/module_policy.md
coordination/directives/global/index.yaml
coordination/directives/modules/<module_id>/index.yaml
coordination/outgoing_prompts/<module_id>/index.yaml
```

Missing module-specific directive index may be a warning during early adoption, not always a hard failure.

## blueprint-sync-directives

Purpose:

```text
Import active Blueprint directives into the local module coordination inbox.
```

Important distinction:

```text
blueprint-pull = update Blueprint repository
blueprint-check = verify Blueprint paths
blueprint-sync-directives = import active directives
```

The canonical directive source is:

```text
module_directives.active
```

from:

```text
coordination/directives/modules/<module_id>/index.yaml
```

Imported directive files should be copied to:

```text
coordination/prompts/received/
```

and registered in:

```text
coordination/prompts/index.yaml
```

The command must avoid duplicate imports.

## Blueprint instruction intake targets

### blueprint-instruction-list

Purpose:

```text
List Blueprint instruction intake sources relevant to the module.
```

### blueprint-instruction-check

Purpose:

```text
Verify that required Blueprint instruction intake sources are readable.
```

### blueprint-instruction-sync

Purpose:

```text
Synchronize the module-local Blueprint instruction intake snapshot.
```

Expected local output may include:

```text
coordination/instruction_intake/blueprint_instruction_packet.yaml
```

The command must be idempotent and avoid timestamp-only churn.

### blueprint-instruction

Purpose:

```text
Run the complete instruction intake workflow.
```

Recommended sequence:

```text
blueprint-instruction-list;
blueprint-instruction-check;
blueprint-instruction-sync.
```

## Blueprint standards targets

### blueprint-standards-list

Purpose:

```text
List Blueprint standards relevant to the module.
```

### blueprint-standards-check

Purpose:

```text
Verify that required Blueprint standards are readable.
```

### blueprint-standards-sync

Purpose:

```text
Synchronize the module-local Blueprint standards snapshot.
```

Expected local output may include:

```text
coordination/standards/blueprint_standards_snapshot.yaml
```

The command must be idempotent and avoid timestamp-only churn.

### blueprint-standards

Purpose:

```text
Run the complete standards workflow.
```

Recommended sequence:

```text
blueprint-standards-list;
blueprint-standards-check;
blueprint-standards-sync.
```

## Blueprint outgoing prompt targets

Blueprint-to-module prompts are stored in Blueprint under:

```text
coordination/outgoing_prompts/<module_id>/
```

### blueprint-prompts-list

Purpose:

```text
List active Blueprint outgoing prompts for this module.
```

Expected behavior:

```text
read coordination/outgoing_prompts/<module_id>/index.yaml;
print active prompt ids, statuses, phases and files.
```

### blueprint-prompts-check

Purpose:

```text
Verify that active Blueprint outgoing prompts for this module are readable and valid.
```

Expected behavior:

```text
verify outgoing prompt index exists;
verify active prompt files exist;
verify target_module matches module id;
verify required prompt sections exist.
```

### blueprint-prompts-sync

Purpose:

```text
Synchronize active Blueprint outgoing prompts into the module-local coordination area.
```

Recommended local destination:

```text
coordination/prompts/received/
```

Recommended local index update:

```text
coordination/prompts/index.yaml
```

The command must avoid duplicate imports.

### blueprint-prompts

Purpose:

```text
Run the complete Blueprint outgoing prompt workflow.
```

Recommended sequence:

```text
blueprint-prompts-list;
blueprint-prompts-check;
blueprint-prompts-sync.
```

### prompt-read

Purpose:

```text
Show the current active prompt that the module assistant should execute.
```

Expected behavior:

```text
read the local synced prompt when available;
otherwise read the active prompt directly from Blueprint;
print the prompt to console.
```

If there are multiple active prompts, the command should clearly report them and require `PROMPT=...` or use a documented priority rule.

## Coordination document awareness targets

### document-manifest

Purpose:

```text
Build and validate the Blueprint coordination document manifest without writing generated reports by default.
```

Expected behavior:

```text
Reads the Blueprint coordination document source registry.
Scans configured coordination document sources.
Computes content hashes.
Prints a concise summary.
Does not write generated report files unless an explicit write target is used.
```

Recommended command behavior:

```make
document-manifest:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/build_document_manifest.py --root "$(BLUEPRINT_ROOT)" --no-write
```

### document-manifest-write

Purpose:

```text
Build the Blueprint coordination document manifest and write generated manifest reports.
```

Expected behavior:

```text
Writes generated document manifest outputs under reports/coordination_awareness.
This target is explicit because generated reports should not be created accidentally during routine checks.
```

Recommended command behavior:

```make
document-manifest-write:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/build_document_manifest.py --root "$(BLUEPRINT_ROOT)"
```

### document-awareness

Purpose:

```text
Render the module-specific coordination document awareness dashboard.
```

Expected behavior:

```text
Compares the current Blueprint document manifest with the module awareness ledger when available.
Shows new, changed, in-progress, acknowledged, applied and deferred documents.
Filters module-specific sources by MODULE_ID.
Limits detail output by LIMIT.
Uses the module-local MODULE_DOCUMENT_AWARENESS_LEDGER for review state.
```

Recommended command behavior:

```make
document-awareness:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/render_document_awareness_dashboard.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --limit "$(LIMIT)"
```

If ` by LIMIT.
```

Recommended command behavior:

```make
document-awareness:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/render_document_awareness_dashboard.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --limitNO_COLOR=1` is provided, color output should be disabled.

### context-bundle

Purpose:

```text
Build a module coordination context bundle without writing generated files by default.
```

Expected behavior:

```text
Builds a Markdown context bundle in memory.
Prints only a summary.
Does not write generated bundle files unless an explicit write target is used.
Uses SCOPE to choose bootstrap, required, changed, critical, high, module or full context.
```

Recommended command behavior:

```make
context-bundle:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/build_context_bundle.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)"
        --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write
```

### context-bundle-write

Purpose:

```text
Build and write a module coordination context bundle.
```

Expected behavior:

```text
Writes a Markdown bundle under reports/coordination_context_bundles.
This target is explicit because bundles can be large generated artifacts.
```

Recommended command behavior:

```make
context-bundle-write:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/build_context_bundle.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)"
        --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)"
```

### context-bundle-print

Purpose:

```text
Print a module coordination context bundle to stdout.
```

Expected behavior:

```text
Prints the selected bundle content to the terminal.
Useful when the operator needs to copy the bundle into an assistant chat.
```

Recommended command behavior:

```make
context-bundle-print:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/build_context_bundle.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)"
        --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)" --print
```

### document-ledger-preview

Purpose:

```text
Preview an update to the module-local coordination document awareness ledger.
```

Expected behavior:

```text
Selects applicable Blueprint coordination documents by DOCUMENT, SOURCE, PRIORITY or all-applicable mode.
Reads current document_id and content_hash from the Blueprint document manifest.
Prints selected documents.
Does not write the module-local ledger.
```

Recommended command behavior:

```make
document-ledger-preview:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/update_document_awareness_ledger.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --status "$(STATUS)" --document "$(DOCUMENT)" --no-write
```

### document-ledger-update

Purpose:

```text
Update the module-local coordination document awareness ledger with current Blueprint document hashes.
```

Expected behavior:

```text
Writes selected Blueprint coordination documents into the module-local ledger.
Stores document_id, path, content_hash, module_review_status, reviewed_at, module_commit and notes.
Requires an explicit selector such as DOCUMENT, SOURCE or PRIORITY.
```

Recommended command behavior:

```make
document-ledger-update:
        $(BLUEPRINT_PYTHON) $(BLUEPRINT_ROOT)/scripts/coordination/update_document_awareness_ledger.py --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --status "$(STATUS)" --document "$(DOCUMENT)"
```

## blueprint-sync

Purpose:

```text
Run all Blueprint synchronization steps needed before module work starts.
```

Preferred sequence:

```text
blueprint-pull;
blueprint-check;
blueprint-sync-directives;
blueprint-instruction;
blueprint-standards;
blueprint-prompts.
```

If a sync step is not implemented yet, it may print a clear deferred message if the deferral is documented.

## coordination-check

Purpose:

```text
Validate module coordination metadata.
```

Preferred behavior:

```text
$(BLUEPRINT_ROOT)/.venv_blueprint/bin/python \
  $(BLUEPRINT_ROOT)/scripts/check_coordination_metadata.py \
  --module-root .
```

## coordination-fix

Purpose:

```text
Safely fix simple coordination metadata issues.
```

Preferred behavior:

```text
$(BLUEPRINT_ROOT)/.venv_blueprint/bin/python \
  $(BLUEPRINT_ROOT)/scripts/fix_coordination_metadata.py \
  --module-root .
```

When finalizing commit/push metadata, a module may use:

```text
$(BLUEPRINT_ROOT)/.venv_blueprint/bin/python \
  $(BLUEPRINT_ROOT)/scripts/fix_coordination_metadata.py \
  --module-root . \
  --update-git-commit \
  --mark-pushed-if-upstream-clean
```

## module-policy-check

Purpose:

```text
Verify that Blueprint module policy for this module is readable.
```

Expected check:

```text
coordination/module_policy/<module_id>/module_policy.md
```

## governance-check

Purpose:

```text
Run the module governance check sequence.
```

Recommended sequence:

```text
blueprint-pull;
blueprint-check;
blueprint-sync-directives;
blueprint-instruction-check;
blueprint-standards-check;
blueprint-prompts-check;
module-policy-check;
coordination-check;
status-report.
```

The command should return non-zero if a required governance check fails.

## Completion packet targets

### completion-packet-validate

Purpose:

```text
Validate a completion packet.
```

Expected usage:

```text
make completion-packet-validate PACKET=coordination/completion_packets/examples/<packet>.yaml
```

### completion-packet-apply

Purpose:

```text
Apply a completion packet to module coordination records.
```

Expected usage:

```text
make completion-packet-apply PACKET=coordination/completion_packets/examples/<packet>.yaml
```

Expected behavior:

```text
generate/update completion report;
update reports index;
update current status;
update next questions for Blueprint when present;
avoid duplicate entries.
```

### completion-packet-check

Purpose:

```text
Validate and apply a completion packet in an idempotency-safe way.
```

Recommended sequence:

```text
completion-packet-validate;
completion-packet-apply;
completion-packet-apply again to verify idempotency.
```

The second apply should produce no semantic changes.

## High-level module workflow targets

### module-start

Purpose:

```text
Prepare the module for prompt execution.
```

Recommended sequence:

```text
blueprint-sync;
coordination-check;
status-report;
prompt-read.
```

A module assistant should normally run this before starting work.

### module-sync

Purpose:

```text
Run the standard synchronization workflow without reading or executing the prompt.
```

Recommended sequence:

```text
blueprint-sync;
coordination-check;
status-report.
```

### module-validate

Purpose:

```text
Run the standard validation sequence before completion or commit.
```

Recommended sequence:

```text
check-report;
check;
governance-check;
report-clean;
status-report.
```

### module-finish

Purpose:

```text
Finalize a completed prompt using completion packet automation.
```

Expected usage:

```text
make module-finish PACKET=coordination/completion_packets/examples/<packet>.yaml
```

Recommended sequence:

```text
completion-packet-check;
module-validate.
```

The command should fail clearly if `PACKET` is missing.

## Help target

Recommended:

```text
make help
```

It should list available targets and short descriptions when practical.

## Deferred targets

If a target cannot be implemented yet, it should not fake success.

Allowed behavior:

```text
print a clear deferred message;
exit 0 only if deferral is expected and documented;
exit non-zero if the missing target blocks the requested action.
```

## Standardization rule

All modules should gradually converge on these command names and block structure.

Do not invent module-specific alternatives when a standard command already exists.

Allowed:

```text
make check-report
```

Avoid:

```text
make run-special-super-checks
```

unless it is an additional helper behind the standard command.

## Review rule

During module review, Blueprint may check whether the module exposes standard Makefile targets.

Missing targets should be reported with one of these statuses:

```text
implemented;
deferred;
not_applicable;
missing_needs_fix.
```

## Prompt authoring rule

Blueprint outgoing prompts should prefer this pattern:

```text
Start:
make module-start

Work:
implement requested scope

Finish:
make module-finish PACKET=coordination/completion_packets/examples/<packet>.yaml

Validate:
make module-validate
```

Prompt authors may include raw commands only when:

```text
the command is diagnostic;
the command is a temporary migration step;
the command is needed because the target is not implemented yet;
the prompt explicitly asks the module to implement that target.
```
