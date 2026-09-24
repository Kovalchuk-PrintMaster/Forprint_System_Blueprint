# Module Analysis Playbook v0.1

This procedure is intentionally explicit. A new assistant follows it in order.

## Phase 0 — Load authority and scope

1. Read the program README and Stage 2 Charter.
2. Read target-module Blueprint policy/coordination surfaces.
3. Read latest current-state evidence.
4. Read known Stage 1 historical-enrichment records.
5. Record exact branch, HEAD/upstream and dirty state.
6. Do not mutate the repository.

Output: `00_preflight/module_scope_and_authority.md`.

## Phase 1 — Build temporary analysis workspace

Recommended:

```text
tmp/module_knowledge_analysis/<module>/
├── 00_preflight/
├── 01_domain/
├── 02_storage_and_state/
├── 03_integrations/
├── 04_runtime_and_services/
├── 05_tests_and_validation/
├── 06_documentation/
├── 07_coordination_and_governance/
├── 08_legacy_unknown/
└── synthesis/
```

Adapt block names to the module, but keep analysis capability-oriented.

## Phase 2 — Segment repository

1. Inventory tracked and relevant untracked files.
2. Group by functional surface, not merely directory.
3. Associate tests with capabilities they verify.
4. Separate generated/cache/build/tmp material.
5. Put ambiguous areas into `08_legacy_unknown` instead of guessing.

Output per block: `manifest.yaml`.

## Phase 3 — Analyze one block at a time

For each block:

1. read source files;
2. identify capabilities;
3. identify entrypoints/public services/operator commands;
4. identify state/data stores;
5. identify dependencies/integrations;
6. identify tests/checks;
7. identify related documents;
8. identify roadmap/Human Intent references where known;
9. identify possible duplicates;
10. identify possible wrong-module ownership;
11. record uncertainty.

Output per block: `analysis_report.md`.

Do not edit canonical source during block analysis.

## Phase 4 — Synthesize capability inventory

After all block reports exist:

1. merge equivalent capability names;
2. retain materially distinct implementations;
3. assign stable capability IDs;
4. assign implementation states;
5. attach verification evidence.

Output: draft Module Knowledge Base.

## Phase 5 — Reconcile documents

For each instruction/architecture document:

1. identify architecture generation;
2. compare with current Blueprint governance;
3. compare with current implementation;
4. compare with newer documents;
5. assign Document Authority status;
6. assign assistant visibility;
7. record conflicts.

Do not delete conflicting documents during discovery.

## Phase 6 — Detect duplicates and misplaced capabilities

1. search within module for equivalent implementations;
2. consult other known module knowledge/index surfaces;
3. assign duplicate groups;
4. identify current architectural owner candidate;
5. record reuse/adapt/migration candidates;
6. do not migrate yet.

## Phase 7 — Reconcile roadmap and implementation

For every important capability record separately:

- roadmap maturity;
- implementation state;
- whether roadmap mention is explicit/implied/absent/conflicting;
- whether capability already exists;
- supporting Human Intent/evidence.

## Phase 8 — Build final knowledge surfaces

Produce:

- Module Knowledge Index;
- Module Knowledge Base;
- Document Authority Registry;
- Capability Reconciliation Registry;
- Cross-module reuse/migration candidates;
- unresolved decisions.

## Phase 9 — Produce cleanup work package

Only after knowledge surfaces exist, create bounded work items for legacy cleanup, duplicate consolidation, migration, documentation updates, missing tests and governance gaps.

Analysis is not authorization to mutate.

## Phase 10 — Automate maintenance

Only after the Library pilot is complete:

1. use Blueprint's existing knowledge/index implementation as reference behavior;
2. automate mechanically derivable fields;
3. add stale-index detection;
4. validate that significant capability changes update knowledge surfaces;
5. keep semantic authority decisions review-gated.

## Completion gate

A module is `KNOWLEDGE_STABILIZED` only when:

- all meaningful functional blocks were analyzed;
- major capabilities have stable IDs;
- implementation evidence is attached;
- instruction-like documents have authority statuses;
- duplicates/misplacements are recorded;
- roadmap ↔ implementation linkage exists;
- unresolved conflicts are explicit;
- no new implementation was invented merely to complete the analysis.
