# ForPrint Testing and Check Report Standard

## Status

Target standard / gradual adoption

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
