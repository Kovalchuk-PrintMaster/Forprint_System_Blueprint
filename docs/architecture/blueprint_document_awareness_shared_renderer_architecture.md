# Blueprint Document Awareness Shared Renderer Architecture

## Status

Implementation architecture v0.1.

## Purpose

This front centralizes operator-facing document-awareness tables while
preserving document discovery, ledger interpretation, bundle construction,
manifest artifacts and read/write boundaries.

## Scope

```text
render_document_awareness_dashboard.py terminal tables;
build_context_bundle.py terminal summary;
build_document_manifest.py terminal summary.
```

## Deliberately unchanged

```text
context bundle Markdown content;
manifest JSON schema;
manifest Markdown tables;
document scan and hashing;
ledger interpretation;
--print bundle output;
--no-write behavior;
write locations and filenames.
```

## Data flow

```text
document/ledger domain models
    ↓
existing awareness, bundle and manifest logic
    ↓
scripts.reporting.document_awareness_tables
    ↓
scripts.reporting.table_renderer
    ↓
compact terminal output
```

## Ownership

Coordination scripts own:

```text
file discovery;
applicability filtering;
priority and awareness status;
recommended actions;
Markdown artifact construction;
write decisions.
```

The reporting package owns:

```text
terminal headers;
fixed compact widths;
closed borders;
ANSI-safe truncation;
NO_COLOR behavior;
warning presentation.
```

## Compatibility labels

The context summary retains:

```text
Module:
Scope:
Documents included:
Write mode:
Bundle:
```

The manifest summary retains:

```text
Schema:
Source registry:
Documents:
Warnings:
```

## Read-only contract

`document-manifest` continues to call `--no-write`.

`context-bundle` continues to call `--no-write`.

`document-awareness` performs no write operation.

The presentation module receives only resolved strings and counts and never
opens or writes coordination documents.
