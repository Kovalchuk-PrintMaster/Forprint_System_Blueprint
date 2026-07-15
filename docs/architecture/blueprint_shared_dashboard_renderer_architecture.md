# Blueprint Shared Dashboard Renderer Architecture

## Status

Implementation architecture v0.1

## Purpose

Centralize boxed-table rendering while preserving dashboard domain logic and CLI contracts.

## Scope

This checkpoint covers:

```text
Prompt Queue dashboard;
Module Roadmap dashboard;
multi-module Roadmap summary.
```

Deferred to the next checkpoint:

```text
completion intake result;
next-work suggestion;
document-awareness dashboard.
```

## Data flow

```text
dashboard domain data
→ dashboard-specific row/status selection
→ scripts.reporting.table_renderer.TableRow
→ render_boxed_table_lines()
→ existing dashboard composition
```

## Ownership

Dashboards own records, columns, markers, domain status mapping, warnings and explanatory text.

The shared renderer owns borders, visible-width calculation, ANSI stripping, row coloring, leading cell-color preservation, truncation, no-color rendering and shape validation.

## Compatibility

Prompt Queue and Module Roadmap keep narrow local `_boxed_table()` facades. These facades delegate to the shared renderer and contain no border or cell-formatting logic.

New code should use semantic `token`. Existing dashboards may temporarily use explicit `color` during gradual adoption.

## No-color contract

No-color mode removes row colors, cell colors and reset sequences while preserving all visible status text.

## Extension rule

No dashboard may add its own border builder, ANSI-width helper, truncation helper or boxed-row renderer.

## Verification

```text
shared renderer tests;
existing Prompt Queue tests;
existing Module Roadmap tests;
Ruff;
full pytest;
live color and no-color dashboard runs;
make check-report;
git diff --check.
```
