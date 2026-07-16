# Blueprint Resolve Next Prompt Result Table Architecture

## Status

Implemented architecture v0.1.

## Scope

The front changes only metadata presentation for:

```text
scripts/coordination/resolve_next_prompt.py
```

Prompt selection remains owned by the coordination command. Shared terminal
presentation is owned by:

```text
scripts/reporting/coordination_result_tables.py
```

## New shared renderer

```text
render_next_prompt_summary(
    module,
    sequence,
    prompt_id,
    title,
    priority,
    file,
    path,
    use_color,
)
```

The renderer uses `TableRow` and `render_boxed_table_lines`.

## Preserved CLI contracts

```text
--module
--root
--path-only
--read
```

No new CLI flag is added.

## Output ownership

Default mode:

```text
shared boxed metadata table on stdout;
exit code 0.
```

Path-only mode:

```text
one plain path line on stdout;
no table;
exit code 0.
```

Read mode:

```text
shared boxed metadata table;
blank line;
80-character separator;
prompt file content unchanged after the separator;
exit code 0.
```

Failure mode:

```text
FAILED: <message> on stdout;
stderr remains empty;
exit code 1.
```

## Read-only boundary

The command does not write:

```text
prompt indexes;
prompt files;
roadmaps;
queue state;
awareness ledgers;
module repositories.
```

## Color boundary

The command follows the `NO_COLOR` environment variable. Machine-like
`--path-only` output never receives color or box formatting.
