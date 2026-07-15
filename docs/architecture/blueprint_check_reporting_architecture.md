# Blueprint Check Reporting Architecture

## Status

Implemented architecture v0.1

## Purpose

This document describes the ForPrint System Blueprint validation/reporting pipeline and its ownership boundaries.

## Data flow

```text
CheckDefinition catalog
    ↓
isolated subprocess execution
    ↓
structured CheckResult
    ↓
status normalization
    ↓
group aggregation
    ↓
compact boxed tables
    ↓
JSON / Markdown artifacts
    ↓
optional full diagnostic log
```

## Components

```text
scripts/run_blueprint_checks.py
    orchestration and authoritative check catalog;

scripts/reporting/models.py
    immutable result and summary models;

scripts/reporting/statuses.py
    status detection, aggregation and semantic visual tokens;

scripts/reporting/table_renderer.py
    reusable closed-border table rendering;

scripts/reporting/console_summary.py
    concern-group and final-summary tables;

scripts/reporting/artifact_writer.py
    JSON, Markdown and full diagnostic artifacts.
```

## Ownership boundaries

Check commands own their validation logic.

The runner owns execution order and process isolation.

Reporting components own normalization and presentation.

Individual checks must not print directly into the routine report. Their stdout and stderr are captured as evidence.

## Routine mode

Routine mode is the default.

It prints coherent compact tables:

```text
Core quality;
Coordination and governance;
Documentation and generated artifacts;
Final result.
```

It always writes:

```text
reports/blueprint_check_report.json
reports/blueprint_check_report.md
```

## Full diagnostic mode

Full mode writes complete captured command output to:

```text
reports/diagnostics/blueprint_check_report_full.log
```

Warnings and failures automatically enable the full log even when the routine command was used.

## Status model

```text
OK
    return code is zero and no warning evidence exists;

WARNING
    return code is zero but warning evidence exists;

FAILED
    return code is non-zero.
```

The final overall status is the worst status present.

## Mutation boundary

`make check` and `make check-report` are read-oriented validation commands and do not run Ruff with `--fix`.

Use:

```text
make check-fix
```

when intentional formatting/lint correction is desired before validation.

## Extending the catalog

Add a new `CheckDefinition` in `build_checks()`.

Every check requires:

```text
stable check_id;
short title;
operator-readable expected result;
tuple command;
coherent group.
```

Do not add rendering logic to the check definition.

## Compatibility direction

Prompt and roadmap dashboards already follow similar table conventions.

Future refactoring may move those dashboards to the shared renderer after compatibility tests are in place. This is not required for the v0.1 reporting checkpoint.

## Backward compatibility

The compact-report refactor preserves the public facade of:

```text
scripts.run_blueprint_checks
```

Existing tests and local tools may continue importing:

```text
STATUS_OK
STATUS_WARNING
STATUS_FAILED
CheckDefinition
CheckResult
detect_status
has_warning_signal
format_duration
color_status
summarize_results
render_text_table
render_markdown_report
write_reports
tail_text
```

Internally, new orchestration uses `ReportSummary` and the
`scripts.reporting` package.

Compatibility aliases may be removed only through an explicit migration
checkpoint with repository-wide caller evidence.

## Stable check-catalog labels

Some Blueprint governance tests and downstream documentation treat selected
check titles as stable public contract labels.

The reporting catalog therefore preserves:

```text
Module governance audit
Completion packet template validation
```

A compact table may truncate these labels visually, but the complete catalog
value remains available in source, JSON and Markdown artifacts.
