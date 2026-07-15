# Blueprint Compact Check Reporting v0.1 — Completion Record

## Result

Implementation checkpoint prepared on branch:

```text
feature/blueprint-compact-check-report-v01
```

## Implemented

```text
shared structured reporting models;
semantic status normalization;
reusable closed-border table renderer;
compact concern-group reporting;
JSON and Markdown artifacts;
automatic or explicit full diagnostic log;
non-mutating default check workflow;
documented check-fix workflow;
reporting architecture document;
operator runbook;
recovery guide;
boxed-table visual standard;
documentation and recovery gate;
automated reporting tests.
```

## Main commands

```bash
make check
make check-report
make check-report-full
make check-fix
```

## Main artifacts

```text
reports/blueprint_check_report.json
reports/blueprint_check_report.md
reports/diagnostics/blueprint_check_report_full.log
```

## Architectural decision

Routine terminal output is compact and tabular.

Complete command output is captured and stored as file-first diagnostic evidence.

`make check` does not silently modify source files. Intentional Ruff repair is exposed through `make check-fix`.

## Recovery evidence

```text
docs/architecture/blueprint_check_reporting_architecture.md
docs/operations/blueprint_check_reporting_runbook.md
docs/operations/blueprint_check_reporting_recovery.md
```

## Verification required before acceptance

```text
reporting unit tests;
existing Blueprint tests;
standards index validation;
full make check;
check-report-full artifact creation;
git diff --check;
idempotent second routine run except generated timestamp artifacts.
```

## Compatibility correction

The initial v0.1 installation exposed a regression because existing tests
imported legacy public names from `scripts.run_blueprint_checks`.

The correction preserves the old facade while retaining the new internal
reporting architecture.

Verification includes:

```text
legacy CheckResult positional and duration_sec constructor;
legacy status constants;
legacy summarize_results mapping;
legacy render_text_table helper;
legacy Markdown/report writers;
full existing Blueprint test suite.
```

## Legacy table-label compatibility

The public `render_text_table()` facade keeps its original Ukrainian column
labels:

```text
Перевірка
Очікуваний результат
Статус
Час
```

The new compact grouped report may use its newer English operator labels
internally, but legacy callers remain stable.

## Check-catalog compatibility correction

The full Blueprint suite revealed two repository-level static contracts for
check titles.

The catalog now preserves:

```text
Module governance audit
Completion packet template validation
```

The correction also normalizes the runner's standard-library import order for
Ruff compatibility and adds a regression test for both labels.
