# Blueprint Document Awareness Shared Renderer Recovery Guide

## Establish state

```bash
git status -sb
git log --oneline -6
git branch -vv
```

Expected branch:

```text
feature/blueprint-document-awareness-renderer-v01
```

## Source of truth

```text
scripts/reporting/document_awareness_tables.py
scripts/reporting/table_renderer.py
scripts/coordination/render_document_awareness_dashboard.py
scripts/coordination/build_context_bundle.py
scripts/coordination/build_document_manifest.py
docs/architecture/blueprint_document_awareness_shared_renderer_architecture.md
```

## Recovery verification

```bash
python -m pytest -q \
  tests/reporting/test_document_awareness_shared_renderer.py \
  tests/coordination/test_document_awareness_dashboard.py \
  tests/coordination/test_context_bundle.py \
  tests/coordination/test_document_awareness_manifest.py

make document-awareness MODULE=forprint_library LIMIT=20
make context-bundle MODULE=forprint_library SCOPE=bootstrap LIMIT=10
make document-manifest

NO_COLOR=1 make document-awareness MODULE=forprint_library LIMIT=20
NO_COLOR=1 make context-bundle MODULE=forprint_library SCOPE=bootstrap LIMIT=10
NO_COLOR=1 make document-manifest
```

## Boundary rule

Do not move discovery, hashing, ledger, filtering, bundle Markdown or manifest
artifact logic into the reporting package.

Do not replace generated Markdown tables with terminal box-drawing characters.

Do not reintroduce `_render_table`, `_strip_ansi`, local border builders or
local visible-width helpers.

## Backup

Installer backups are stored under:

```text
.tmp_blueprint_backups/document_awareness_renderer_<timestamp>/
```
