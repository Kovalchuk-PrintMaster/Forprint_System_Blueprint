# Blueprint Module Roadmap Renderer Cleanup Architecture

## Scope

`module_roadmap.py` keeps roadmap validation, current-step derivation, window
selection and semantic row composition. Shared reporting owns borders, widths,
truncation and ANSI-safe presentation.

## Removed wrappers

```text
_row
_boxed_table
_token_color
```

`_row` had no callers. `_boxed_table` delegated to
`render_boxed_table_lines`. `_token_color` duplicated the shared semantic
palette.

## Direct shared dependencies

```text
scripts.reporting.table_renderer.TableRow
scripts.reporting.table_renderer.render_boxed_table_lines
scripts.reporting.statuses.colorize
```

## Preserved contracts

```text
roadmap YAML schema and validation;
current-step and window semantics;
dashboard and summary content;
CLI flags;
NO_COLOR behavior;
Makefile targets;
read-only behavior.
```

Planned and unknown values remain uncolored to preserve existing output.
