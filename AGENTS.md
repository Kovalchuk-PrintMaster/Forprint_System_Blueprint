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
