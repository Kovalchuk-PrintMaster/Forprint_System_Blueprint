# ForPrint Testing and Check Report Standard

## Status

Active standard / prompt-or-directive rollout

## Purpose

This document defines the expected testing and visual check-report direction for ForPrint modules.

The goal is to make every module easy to verify before commit and easy to inspect visually.

## Main testing principle

Tests should cover the current working scope of the module, not only one isolated function.

As a module grows, tests should cover:

```text
domain models;
service/use-case logic;
contracts or fixtures;
repository/storage behavior if present;
boundary rules;
coordination metadata;
project health commands.
```

## Preferred test groups

Recommended structure:

```text
tests/unit/
tests/contract/
tests/integration/
```

## Unit tests

Purpose:

```text
Check small local logic.
```

Examples:

```text
model validation;
pure service functions;
catalog loaders;
alias resolution;
status transitions.
```

## Contract tests

Purpose:

```text
Check stable data shapes and boundary contracts.
```

Examples:

```text
fixture validation;
placeholder contract schema;
output package structure;
module manifest expectations;
cross-module reference conventions.
```

## Integration tests

Purpose:

```text
Check module components working together.
```

Examples:

```text
repository + service;
storage + projection;
check-report runner;
coordination sync script;
local API smoke tests if applicable.
```

## Documentation tests

Documentation tests should verify important architecture files exist and contain key concepts.

Do not make documentation tests overly brittle.

For prose checks, prefer case-insensitive matching unless the value is a machine enum.

## Required check command

Every active module should eventually support:

```text
make check
```

`make check` should be the main pre-commit validation command.

Preferred sequence:

```text
lint-fix;
lint;
test;
module-specific validation;
coordination-check if available.
```

## Visual check-report command

Every active module should eventually support:

```text
make check-report
```

This command should:

```text
run important checks;
show a visual console table;
write JSON report;
write Markdown report;
return non-zero if a required check fails.
```

## Status meanings

Standard statuses:

```text
OK
WARN
DEFERRED
FAILED
SKIPPED
```

## Color convention

Console visual output may use ANSI colors:

```text
OK = green
WARN = yellow
DEFERRED = yellow
FAILED = red
SKIPPED = neutral
```

Colors are for humans only.

JSON and Markdown reports must remain plain and machine-readable.

## Recommended visual table

Example:

```text
ForPrint <Module> — check report

┌──────────────────────────────┬─────────────────────────────┬────────┬───────┐
│ Check                        │ Expected result             │ Status │ Time  │
├──────────────────────────────┼─────────────────────────────┼────────┼───────┤
│ Ruff lint                    │ No lint errors              │ OK     │ 0.04s │
│ Pytest                       │ All tests pass              │ OK     │ 0.31s │
│ Coordination metadata        │ Metadata is valid           │ OK     │ 0.02s │
│ Blueprint directives index   │ Present or deferred warning │ WARN   │ 0.01s │
└──────────────────────────────┴─────────────────────────────┴────────┴───────┘
```

## Recommended report files

Reports should be stored under:

```text
reports/
```

Recommended names:

```text
reports/<module>_check_report.json
reports/<module>_check_report.md
```

## Recommended check-report categories

Where applicable, include:

```text
Ruff lint;
Pytest;
module-specific validation;
schema validation;
contract fixture validation;
module manifest boundary;
required architecture docs;
coordination files;
Blueprint source config;
Makefile standard targets.
```

## JSON report

The JSON report should include:

```text
module_id;
generated_at;
overall_status;
checks[];
```

Each check should include:

```text
name;
expected;
status;
duration_seconds;
details;
```

## Markdown report

The Markdown report should include:

```text
title;
generated timestamp;
summary table;
failed/warning details;
report file paths.
```

## Failure behavior

If a required check fails:

```text
console table shows FAILED;
JSON overall_status is FAILED;
Markdown report records the failure;
command exits with non-zero status.
```

If a check is intentionally deferred:

```text
console table shows DEFERRED or WARN;
JSON records DEFERRED;
Markdown explains why.
```

## Boundary checks

Modules should test that they do not take ownership of forbidden domains.

Example:

```text
Calculator must not own canonical client registry.
Library must not own operational orders.
Accounting Registry must not own CRM workflow.
Operational Registry must not own Library catalog semantics.
```

## Coordination metadata checks

Modules should gradually adopt Blueprint central metadata validator:

```text
coordination-check;
coordination-fix.
```

## Review rule

A module is easier to promote when:

```text
make check passes;
make check-report passes;
reports are generated;
coordination metadata is valid;
boundary tests exist;
the working tree is clean after commit/push.
```

## Compact and extended output modes

Routine verification must use two output levels.

### Compact mode

Compact mode is the default for:

```text
make check;
make check-report;
routine assistant handoff;
routine Blueprint review.
```

A routine command should be as small as practical for fast analysis. For a normal module, output near or below 100 terminal lines is a useful guideline, not a hard limit. The required size depends on the current architecture, the number of independent concerns and the evidence needed to avoid missing failures.

Compact output must show:

```text
module;
command or check scope;
overall signal;
error count;
warning count;
test summary;
blockers;
next action;
paths to detailed reports.
```

Compact mode must not print:

```text
every successful test;
complete repository trees;
complete JSON or YAML payloads;
complete generated files;
repeated copies of the same result;
long stack traces for already understood failures.
```

### Extended mode

Extended output is used only when:

```text
the compact result contains a warning or failure;
Blueprint explicitly requests diagnostic evidence;
a migration, data-loss, security or boundary risk exists;
an integration contract fails;
the compact result cannot explain the problem.
```

Recommended optional command:

```text
make check-report-full
```

A module may use another clearly documented verbose command during gradual adoption.

## Compact tabular presentation

Routine human-facing reports should prefer one or more compact boxed tables.

Each table should represent one coherent concern, for example:

```text
core code quality and tests;
business or provider contract checks;
safety and ownership boundaries;
integration checks;
coordination and prompt state.
```

Use as many tables and rows as required for quick, reliable analysis. Do not force unrelated information into one oversized table, and do not remove necessary checks merely to satisfy a line-count target.

Tables should:

```text
use closed borders where supported;
use the active Blueprint visual-interface status and color conventions;
show a current-row marker such as `>` where a current prompt, roadmap step or selected item is meaningful;
show warnings and failures explicitly;
show counts and stable artifact paths;
remain readable without ANSI color.
```

The applicable visual rules are discovered through:

```text
coordination/standards/visual_interface/index.yaml
```

Modules should read the index and then apply the active or relevant table, status and color documents referenced there.

Extended diagnostic output is not line-limited. When it is large, redirect it to a file under `reports/diagnostics/` and keep only the compact result and artifact path in routine terminal or assistant output.

## Overall human signal

Existing per-check statuses remain:

```text
OK
WARN
DEFERRED
FAILED
SKIPPED
```

The compact report may additionally expose one overall human signal:

```text
GREEN = no blocking failures and no unresolved warnings;
YELLOW = warning, deferred item or non-blocking inconsistency;
RED = blocking failure.
```

Machine-readable JSON must keep explicit status values and must not depend on terminal color.

## File-first diagnostics

Detailed evidence belongs in files, not in routine chat or terminal output.

Preferred locations:

```text
reports/<module>_check_report.json
reports/<module>_check_report.md
reports/diagnostics/<timestamp>/
```

The terminal and assistant handoff should provide only a concise summary and stable paths to those artifacts.

## Compact handoff format

A routine assistant handoff should use:

```text
RESULT:
WHAT_CHANGED:
CHECKS:
ERRORS:
WARNINGS:
BLOCKERS:
DECISIONS_REQUIRED:
REPORT_PATHS:
COMMIT:
```

When the result is GREEN, the handoff should remain minimal.

When the result is YELLOW or RED, include only the evidence needed to identify the problem and provide paths to the full artifacts.

## Completion report size and duplication

A completion report describes decisions, implementation and verification. It must not reproduce raw logs.

Recommended completion report sections:

```text
task;
result;
implemented;
architectural decisions;
tests and checks;
remaining risks or blockers;
changed files;
recommended next step;
paths to detailed evidence.
```

A routine completion report should normally remain below 150 lines.

Large logs, payloads, generated reports and full diffs must remain separate artifacts.

## Make command direction

The common direction is:

```text
make check
    compact pre-commit validation;

make check-report
    compact visual summary plus JSON and Markdown artifacts;

make check-report-full
    optional extended console diagnostics.
```

Existing module-specific commands may remain during gradual migration.

## Rollout rule

This standard becomes mandatory for a module through an explicit Blueprint prompt or active global directive.

Migration should be applied in small safe steps and must not pause valid business development solely to refactor old report output.

Logistics Service should be used as the first reference implementation. Library and Telegram Bot should align through their next active prompts.

## Blueprint shared reporting architecture

The Blueprint reference implementation is documented at:

```text
docs/architecture/blueprint_check_reporting_architecture.md
docs/operations/blueprint_check_reporting_runbook.md
docs/operations/blueprint_check_reporting_recovery.md
```

The reusable implementation lives under:

```text
scripts/reporting/
```

The default Blueprint `make check` and `make check-report` commands are structured, compact and non-mutating.

Intentional lint repair uses:

```text
make check-fix
```

Full command evidence uses:

```text
make check-report-full
reports/diagnostics/blueprint_check_report_full.log
```

New module implementations may adapt this architecture while preserving structured results, semantic statuses, compact tables, machine-readable artifacts and file-first diagnostics.
