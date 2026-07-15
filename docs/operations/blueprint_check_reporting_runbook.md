# Blueprint Check Reporting Runbook

## Routine pre-commit validation

```bash
make check
```

Expected outputs:

```text
compact boxed tables;
reports/blueprint_check_report.json;
reports/blueprint_check_report.md.
```

## Explicit compact report

```bash
make check-report
```

This is equivalent to the routine structured validation workflow.

## Full diagnostics

```bash
make check-report-full
```

Expected additional artifact:

```text
reports/diagnostics/blueprint_check_report_full.log
```

The terminal still stays compact.

## Intentional lint repair

```bash
make check-fix
```

This runs Ruff fixes first and then runs the non-mutating structured check.

## No-color mode

```bash
NO_COLOR=1 make check-report
```

All status meaning must remain readable.

## Failure handling

When the final status is `FAILED`:

```text
read the failed row;
read Blockers;
open the Markdown report;
open the full diagnostic log;
fix only the documented failing scope;
rerun make check-report.
```

## Warning handling

A `WARNING` result is non-blocking only when the relevant policy permits it.

The warning must remain visible and have a documented next action.

## Artifact ownership

Generated routine reports live under:

```text
reports/
reports/diagnostics/
```

They are diagnostic artifacts, not source-of-truth replacements for standards, prompts, roadmaps or completion packets.
