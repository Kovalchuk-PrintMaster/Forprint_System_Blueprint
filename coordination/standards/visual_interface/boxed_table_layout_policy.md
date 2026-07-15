# ForPrint Boxed Table Layout Policy

## Status

Active standard / gradual alignment v0.1

## Purpose

This policy defines a shared terminal-table layout for ForPrint dashboards, routine check reports and coordination summaries.

The goal is fast operator analysis without relying on one assistant's private formatting habits.

## Core rules

Routine human-facing reports should use one or more coherent boxed tables when the terminal supports Unicode box-drawing characters.

A table must:

```text
have closed outer borders;
have explicit column headers;
keep status meaning readable without color;
truncate oversized cells with an ellipsis;
avoid placing unrelated concerns in one oversized table;
show warnings and failures explicitly;
show stable paths to detailed evidence outside or below the table.
```

## Multiple-table rule

Use separate tables for independent concerns.

Examples:

```text
core quality and tests;
coordination and prompt state;
business or provider contracts;
integration boundaries;
documentation and generated artifacts;
final summary.
```

The number of tables and rows is controlled by readability and risk, not by a universal fixed line count.

For a normal module, a routine report near or below 100 terminal lines is a useful guideline. This is not a hard limit.

## Current-row marker

Use `>` or `→` in a narrow first column when a current or selected item is meaningful.

Applicable examples:

```text
current prompt;
current roadmap step;
current check group under investigation;
selected provider or scenario.
```

Do not mark every row.

## Status and color

Colors must follow semantic tokens from:

```text
coordination/standards/visual_interface/color_tokens_policy.md
```

Color is cosmetic.

Every colored status must also contain readable text such as:

```text
OK
WARNING
FAILED
active
accepted
planned
blocked
```

`NO_COLOR=1` or an equivalent no-color option must preserve all meaning.

## Width and truncation

Column widths should be intentionally bounded.

Long identifiers and paths may be shortened with `…` in the console table. The complete value must remain available in JSON, Markdown or source files.

Do not wrap one logical row into a large multi-line block in a routine table.

## Detailed diagnostics

Routine tables summarize.

Complete logs, stack traces, payloads and repeated successful output belong in:

```text
reports/diagnostics/
```

When a warning or failure exists, the routine report must show:

```text
status;
affected check;
blocker or decision;
path to detailed evidence.
```

## Reuse rule

New reporting tools should use shared table-rendering primitives when available.

Do not create a new incompatible border, marker or color system for each module.

## Shared implementation

The Blueprint reference renderer is:

```text
scripts/reporting/table_renderer.py
```

Prompt Queue and Module Roadmap dashboards use this implementation. Narrow
compatibility facades may remain, but border construction, ANSI visible-width
handling, truncation and row rendering must stay centralized.

Semantic tokens are preferred. Temporary explicit ANSI row colors are allowed
only for gradual compatibility migration.
