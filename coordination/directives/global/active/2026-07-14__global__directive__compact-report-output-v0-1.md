# Global Directive: Compact Report Output v0.1

## Directive ID

```text
2026-07-14__global__directive__compact-report-output-v0-1
```

## Scope

```text
all_active_modules
```

## Status

```text
active
```

## Priority

```text
p0
```

## Purpose

Reduce duplicated and low-value terminal, chat and completion-report output while preserving full diagnostic evidence in stable report files.

The governing standard is:

```text
coordination/standards/testing_and_check_report_standard.md
```

## Required behavior

Every active module must gradually provide:

```text
compact routine output by default;
extended diagnostic output on demand;
full JSON and Markdown report artifacts;
visible warning and failure counts;
stable paths to detailed evidence;
minimal GREEN assistant handoff;
focused YELLOW or RED diagnostic handoff.
```

## Required command direction

```text
make check
    compact pre-commit validation;

make check-report
    compact visual summary and report artifacts;

make check-report-full
    optional extended diagnostics.
```

Equivalent existing module-specific commands may remain temporarily when documented.

## Output rule

A routine check should be as small as practical for fast analysis. Near or below 100 lines is a useful guideline for a normal module, not a hard limit; architecture and evidence requirements control the necessary size.

Do not print complete successful test streams, repository trees, full payloads, generated files or repeated report copies unless Blueprint explicitly requests them.

## Tabular presentation rule

Routine reports should use one or more compact boxed tables and the active Blueprint visual-interface status/color conventions.

Separate unrelated concerns into separate tables when that improves readability. Use a current-row marker where a current prompt, roadmap step or selected item is meaningful.

The visual source of truth is discovered through:

```text
coordination/standards/visual_interface/index.yaml
```

Extended diagnostics may be as detailed as necessary and should be redirected to stable files when large.

## Artifact rule

Detailed evidence must be written under stable report paths such as:

```text
reports/<module>_check_report.json
reports/<module>_check_report.md
reports/diagnostics/<timestamp>/
```

## Rollout order

```text
1. Logistics Service — reference implementation.
2. Library — align through the next active prompt.
3. Telegram Bot — align through the next active prompt.
4. Other active modules — align when receiving their next relevant prompt.
```

Business development must not be paused solely to refactor historical report output.

## Expected acknowledgement

Each module should report:

```text
Compact Report Output Applied
```

with:

```text
default compact commands;
extended diagnostic command;
report artifact paths;
sample compact output;
checks performed;
remaining deviations;
commit hash;
push status.
```

## Safety

The directive does not permit hiding failures.

Warnings and failures must be visible in compact output, and detailed evidence must remain available in report artifacts.
