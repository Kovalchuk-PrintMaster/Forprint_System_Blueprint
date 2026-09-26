<!-- FORPRINT_BLUEPRINT_ASSISTANT_PROTOCOL_START -->
# ForPrint System Blueprint — AI Assistant Entry

If you are a new AI assistant with no repository context, do not read the tree
randomly and do not mutate the project first.

1. Read `coordination/releases/current.yaml` — release authority.
2. Read `machine/module_identity_registry.yaml` — canonical module identities.
3. Read `indexes/knowledge_summary.yaml`.
4. Use `indexes/document_catalog.yaml`, `indexes/references.json`,
   `indexes/dependencies.json`, `indexes/prompts.yaml`, `indexes/roadmaps.yaml`,
   `indexes/governance.yaml`, `indexes/contracts.yaml`,
   `indexes/source_coverage.yaml`, and `indexes/incoming_requests.yaml`.
5. Read `coordination/roadmaps/details/forprint_system_blueprint/`.

Choose onboarding mode:
- `BOOTSTRAP_WITHOUT_TASK` when no concrete task is assigned;
- `BOOTSTRAP_FOR_TASK` when a roadmap step/task exists.

Prefer one generated bootstrap/task context bundle over repeated manual transfer
of individual files.

Before implementation resolve: active roadmap step, process-contract revision,
applicable governance/standards, dependencies, validators and acceptance evidence.

Before handoff: refresh/check derived indexes, update required documentation,
verify the pinned process revision is still supported, run deterministic checks,
and produce completion/conformance evidence.

Derived indexes are navigation/evidence, not authority. `make check` validates;
it must not silently auto-fix project state.
<!-- FORPRINT_BLUEPRINT_ASSISTANT_PROTOCOL_END -->


<!-- human-intent-ledger-v0-1:start -->
## Human intent preservation
For substantial architecture / evening-review work, read `coordination/human_intent/README.md`.
Completion of the review requires a Human Intent Delta, append-only module intent updates, regenerated expanded human portfolio, and an explicit GAP list. Do not replace missing exact human details with invented equivalents.
<!-- human-intent-ledger-v0-1:end -->

- Portfolio review rendering/content standard: `coordination/standards/governance/portfolio_rendering_and_content_specification_v0_1.md`
- Latest integrated evening-review architecture index: `coordination/internal_work/blueprint/evening_reviews/2026-08-31/README.md`

<!-- FORPRINT_CF05_HISTORY_LEDGER_START -->
## Workfront and execution-attempt durable history

Read:
`coordination/standards/automation/workfront_history_contract_v0_1.yaml`
and
`coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml`.

Operational rule:
- Work Front remains the bounded execution-contract authority;
- the Continuity Event Store remains actual roadmap lifecycle execution authority;
- Workfront History and Execution Attempt Ledger are separate append-only fact histories;
- a retry creates a new attempt and never overwrites the prior attempt;
- failed and partial attempts remain durable;
- partial/interrupted attempts preserve resume coordinates from the latest accepted mutation/event and must not replay already accepted work;
- raw chat may be provenance evidence only and is never execution authority;
- history records do not grant worker-dispatch, release or foreign-repository-write authority;
- CF-06 Execution Profiles are not implemented by CF-05.
<!-- FORPRINT_CF05_HISTORY_LEDGER_END -->

<!-- FORPRINT_ASSISTANT_HANDOFF_COMPILER_START -->
## Deterministic assistant handoff pack

The continuity handoff operator surface is:

`make assistant-pack`

It builds a deterministic runtime ZIP under `tmp/assistant_handoff/` from immutable
continuity events plus the current working-tree source state. The pack includes
`00_READ_FIRST.md`, mission/bootstrap inputs, latest checkpoint, current in-memory
continuity projections, blockers/unknowns, next horizon, roadmap/dependency slices,
knowledge-health evidence, compiler source and a hash-bound manifest.

Binding boundaries:
- the pack is non-authoritative and cannot grant release, queue, worker-dispatch,
  foreign-module mutation or operator-approval authority;
- chat transcripts are excluded;
- current unreconciled durable delta is preserved visibly rather than silently
  folded into the latest checkpoint;
- archive bytes are deterministic for the same compiler and repository state;
- `make assistant-handoff-check` validates buildability without writing an archive;
- the legacy `make assistant-context-pack` Project Context surface remains separate
  compatibility tooling until its later determinism/provenance/safety hardening and
  zero-context startup migration are explicitly accepted.
<!-- FORPRINT_ASSISTANT_HANDOFF_COMPILER_END -->
