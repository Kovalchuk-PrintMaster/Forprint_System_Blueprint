# Blueprint Coordination Result Tables Architecture

## Status

Implementation architecture v0.1.

## Purpose

Completion intake and next-work resolution already own stable domain models and
JSON contracts. This front changes only their operator-facing presentation.

## Data flow

```text
domain validation and resolution
    ↓
existing IntakePlan / NextWorkSuggestion
    ↓
existing JSON-compatible mapping
    ↓
scripts.reporting.coordination_result_tables
    ↓
scripts.reporting.table_renderer
    ↓
compact terminal tables
```

## Stable contracts

The following remain unchanged:

```text
completion packet validation;
preview versus write behavior;
atomic writes and rollback;
prompt queue and roadmap mutations;
NextWorkSuggestion resolution rules;
--json payload fields;
exit codes;
Makefile targets.
```

The following are additive:

```text
compact boxed human output;
--no-color;
NO_COLOR environment support;
shared semantic row styling.
```

## Presentation ownership

`scripts/reporting/coordination_result_tables.py` owns summary and detail tables.
The coordination scripts continue to own all business decisions and validation.

## Compatibility

Legacy field labels remain visible in table output. JSON remains the canonical
machine-readable contract.

## Safety boundary

The presentation layer receives resolved mappings and strings. It must not read
or write queue, roadmap, packet, review or module files.

## Deferred work

Markdown artifact emission is deferred. Preview commands must stay read-only,
and new generated files require a separate artifact-retention decision.
