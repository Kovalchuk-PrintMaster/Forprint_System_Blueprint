# Blueprint Diagrams

This directory contains current explanatory Mermaid views of the ForPrint architecture.

Diagrams never override canonical machine architecture.

## Current diagrams

### Generated

- `module_graph.mmd` — generated from `machine/data_flows.yaml`;
- `ownership_map.mmd` — generated from `machine/ownership.yaml`.

Generate with:

```bash
make diagrams
```

### Maintained explanatory views

- `data_flow.mmd` — compact high-level flow view;
- `system_detail_map.mmd` — human-facing layered/business interaction map.

Maintained diagrams must use canonical current module names and must not silently invent a
different authority model.

## Historical diagram

The former manual `project_landscape.mmd` described an early local-filesystem snapshot.
It is preserved under:

`coordination/internal_work/blueprint/legacy_alignment/diagrams/project_landscape.mmd`

Current repository/local module locations are tracked by:

`coordination/module_sources/module_git_sources.yaml`

## Validation

```bash
make diagrams-check
make check
```
