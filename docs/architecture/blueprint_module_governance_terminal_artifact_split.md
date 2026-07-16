# Blueprint Module Governance Terminal/Artifact Split Architecture

## Status

Implementation architecture v0.1.

## Scope

The governance audit keeps one audit model and two independent presentation
surfaces:

```text
terminal summary -> shared compact boxed renderer
JSON artifact    -> existing detailed machine contract
Markdown artifact -> existing detailed human-readable contract
```

## Source of truth

Audit logic and detailed artifact generation remain in:

```text
scripts/audit_module_governance.py
```

Compact terminal rendering is owned by:

```text
scripts/reporting/coordination_result_tables.py
```

## Shared renderer

```text
render_module_governance_summary(
    modules_checked,
    summary,
    report_writing,
    report_json,
    report_markdown,
    use_color,
)
```

The renderer receives already-computed values. It does not load module
registries, inspect module repositories, decide statuses or write artifacts.

## Protected contracts

The following definitions remain source-identical during installation:

```text
ModuleAuditResult
_audit_module()
_summary()
_write_json()
_write_markdown()
_resolve_report_paths()
build_cli()
```

## CLI contract

```text
--no-write
--report-dir
```

No new CLI option is introduced.

## Artifact contract

JSON keeps:

```text
generated_at
source_file
required_files
required_targets
summary
modules
```

Summary key order remains:

```text
OK
NEEDS_ALIGNMENT
WARN
DEFERRED
```

Markdown keeps the existing heading sequence and report filenames.

## Timestamp-aware verification

Generated artifacts contain current UTC timestamps. Raw SHA-256 therefore
changes on every execution. Contract verification normalizes only the
generated timestamp and compares the remaining bytes and parsed structure.

## Read-only mode

`--no-write` must not create, replace or modify either default report file.
