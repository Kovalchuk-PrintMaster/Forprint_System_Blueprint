# Blueprint Document Awareness Shared Renderer Runbook

## Awareness dashboard

```bash
make document-awareness MODULE=forprint_library LIMIT=20
NO_COLOR=1 make document-awareness MODULE=forprint_library LIMIT=20
```

Verify:

```text
Area Summary table;
Attention Required table or empty-state message;
warning evidence;
visible priority and status without ANSI.
```

## Context bundle read-only summary

```bash
make context-bundle MODULE=forprint_library SCOPE=bootstrap LIMIT=10
NO_COLOR=1 make context-bundle MODULE=forprint_library SCOPE=bootstrap LIMIT=10
```

The summary must state `Write mode: disabled`.

## Context bundle Markdown preview

```bash
make context-bundle-print MODULE=forprint_library SCOPE=bootstrap LIMIT=10
```

This output is bundle Markdown and is intentionally not converted to terminal
boxed tables.

## Manifest read-only summary

```bash
make document-manifest
NO_COLOR=1 make document-manifest
```

## Focused tests

```bash
python -m pytest -q \
  tests/reporting/test_document_awareness_shared_renderer.py \
  tests/coordination/test_document_awareness_dashboard.py \
  tests/coordination/test_context_bundle.py \
  tests/coordination/test_document_awareness_manifest.py
```

## Full verification

```bash
python -m ruff check scripts tests tools
python -m pytest -q
make check-report
git diff --check
```
