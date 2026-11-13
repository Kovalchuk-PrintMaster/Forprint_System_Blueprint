# Library Pilot Execution Plan v0.1

## Goal

Use `forprint_library` to prove the complete Module Knowledge Stabilization procedure before automating it or applying it to high-risk legacy modules.

The pilot is analysis and knowledge construction, not opportunistic refactoring.

## L0 — Preflight

Capture branch, HEAD/upstream, dirty state, module policy/governance, current coordination status and known Stage 1 Library evidence.

Output: `00_preflight/module_scope_and_authority.md`.

## L1 — Inventory and segmentation

Build repository inventory and functional analysis blocks.

Do not assume directory boundaries equal capability boundaries.

Outputs:
- block directories under `tmp/module_knowledge_analysis/forprint_library/`;
- `manifest.yaml` for each block;
- module-wide file classification.

## L2 — Sequential block analysis

Analyze one block at a time.

Each `analysis_report.md` contains:
- capabilities;
- implementation paths;
- entrypoints;
- state/data;
- dependencies;
- tests;
- documents;
- roadmap/Human Intent evidence;
- duplicate/migration/reuse candidates;
- uncertainty.

Do not synthesize before all selected block reports exist.

## L3 — Module synthesis

Create stable capability IDs and merge findings.

Output: draft Module Knowledge Base.

## L4 — Document authority reconciliation

Assign authority and assistant visibility to instruction-like/documentation surfaces.

Output: Document Authority Registry.

## L5 — Capability reconciliation

Find duplicates, partial alternatives, misplaced ownership and cross-module reuse/migration candidates.

Output: Capability Reconciliation Registry.

## L6 — Roadmap ↔ implementation linkage

For every major capability record:
- roadmap explicit/implied/absent/conflicting;
- implementation current/partial/none/legacy/unknown;
- evidence.

## L7 — Publish knowledge surfaces

Produce:
- Module Knowledge Index;
- Module Knowledge Base;
- registries;
- unresolved-decision list.

## L8 — Produce cleanup work package

Only now describe cleanup/migration/document/test work for a later bounded implementation task.

## L9 — Design maintenance automation

Use:
1. proven Library data model;
2. Blueprint's existing knowledge/index implementation as behavioral reference.

Automate mechanical maintenance; keep semantic authority decisions review-gated.

## Pilot success criteria

A new assistant can answer without scanning the entire repository:
- what Library can do;
- where important capabilities live;
- which tests prove them;
- which documents are current;
- which documents are historical/conflicting;
- which duplicate/reuse/migration candidates exist;
- which roadmap ideas are already implemented;
- what the exact next work item is.
