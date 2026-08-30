# Blueprint Derived Indexes

`indexes/` is the generated navigation and discovery layer for
`forprint_system_blueprint`.

It is **derived and non-authoritative**.

Indexes answer:

- what source files currently exist;
- which documents are current, normative, explanatory or historical;
- which repository paths reference which other paths;
- which file-level and module-level dependencies are declared;
- which references are Blueprint-local, module-relative, historical, planned or examples;
- which prompt queues and roadmaps are current versus historical;
- which governance and contract surfaces are effective;
- which module registries have coverage for each canonical module ID.

Indexes never override `coordination/releases/current.yaml`, `machine/*.yaml`, active
standards, released prompts or other canonical source artifacts.

## Core navigation

- `index.yaml`
- `modules.yaml`
- `authorities.yaml`
- `documents.yaml`
- `legacy.yaml`
- `derivations.yaml`

## Full Knowledge Index

- `files.json` — deterministic source-file inventory;
- `document_catalog.yaml` — document catalog and lifecycle classification;
- `references.json` — path-reference index plus backlinks and scope classifications;
- `dependencies.json` — resolved file edges plus machine module dependency edges;
- `review_candidates.yaml` — actionable unresolved references plus classified review signals;
- `knowledge_summary.yaml` — compact counts and quality posture.

## Specialized query indexes

- `prompts.yaml` — queue authority, identity, lifecycle and completion-report scope;
- `roadmaps.yaml` — roadmap availability, current steps and status counts;
- `governance.yaml` — effective release/governance projection and standards inventory;
- `contracts.yaml` — machine contracts and prompt-contract packages;
- `source_coverage.yaml` — canonical module coverage across specialized registries and module-policy documents;
- `incoming_requests.yaml` — canonical incoming-request routes plus historical alias routes.

## Reference semantics

A path-looking string is not automatically a Blueprint-local dependency.

The index separates, among others:

- Blueprint-local resolved files/directories;
- target-module-relative references;
- common module-coordination contract paths;
- planned module-owned runtime surfaces;
- historical/internal-work evidence;
- Repository Knowledge snapshot references;
- test fixtures and policy/template examples;
- lifecycle-moved prompt origins;
- retired historical paths;
- structured YAML pointers and pytest node IDs;
- target-module completion evidence;
- declared unavailable registry paths;
- roadmap planning references;
- conceptual slash-separated non-path text.

Only the remaining `unresolved_candidate` class enters the default actionable reference
review queue.

Documents with no literal backlink are also separated into two groups: genuine
`no_inbound_current_documents` and structurally discoverable documents already covered by
standards, roadmap-detail, template, module-policy, incoming-request or document-catalog
navigation.

## Duplicate semantics

Exact hash equality is classified before review.

Intentional classes include:

- declared source→derived distributions;
- immutable prompt source snapshots;
- Python package markers;
- structural/empty placeholders;
- historical duplicates.

Only `review_exact_duplicate` is considered a harmful duplicate candidate by default.

## Determinism boundary

The full file index intentionally excludes:

- `indexes/` itself, to avoid self-hash cycles;
- `reports/`, because check reports are volatile generated artifacts;
- `tmp/`, `tmp.py`, virtual environments and caches.

## Commands

```bash
.venv_blueprint/bin/python scripts/indexing/build_blueprint_index.py --check
.venv_blueprint/bin/python scripts/indexing/build_blueprint_knowledge_index.py --check
.venv_blueprint/bin/python scripts/indexing/validate_blueprint_knowledge_index.py
.venv_blueprint/bin/python scripts/indexing/build_blueprint_specialized_indexes.py --check
.venv_blueprint/bin/python scripts/indexing/validate_blueprint_specialized_indexes.py
```

The semantic-structure gate validates both the full Knowledge Index and the specialized
query layer, so `make check` covers the complete derived index system.
