# ForPrint Blueprint — Zero-Context Project Entry

<!-- startup-manifest-2026-09-15:start -->
## Mandatory startup manifest

Before broad planning or mutation, a fresh assistant must resolve these startup keys:

- `MUST_READ_BEFORE_FIRST_ACTION`: Constitution, `AGENTS.md`, this file, lifecycle/roadmap status, current Work Front, active reconciliation questions.
- `MUST_VERIFY`: HEAD/repository boundary, `ROADMAP_SYNC`, lifecycle cursor, source freshness, pending Z-package intake.
- `OPERATOR_INTERACTION_MODE`: male operator; friendly direct Ukrainian; human-readable roadmap explanations before internal IDs.
- `EXECUTION_ENTRYPOINT`: bounded Python action with unique semantic source identity; never depend on a fixed `tmp.py` as the durable action source.
- `EVENING_MODE`: architecture/decision conversation + Z-package; no assumed repo execution.
- `MORNING_Z_PACKAGE_INTAKE`: reconcile/classify/map first; never execute the archive as one job.
- `PROJECT_INDEX_ENTRYPOINT`: existing Blueprint index/knowledge/context pack surfaces.
- `OPEN_RECONCILIATION_QUESTIONS`: `coordination/bootstrap/ACTIVE_RECONCILIATION_QUESTIONS.yaml`.
- `DO_NOT_IMPROVISE`: canonical contradiction => explicit operator reconciliation, never silent overwrite.

The active reconciliation-question file is navigation only. Q1 remains the lifecycle authority for actual clarification threads; resolved reconciliation items leave the startup projection and remain historically discoverable elsewhere.
<!-- startup-manifest-2026-09-15:end -->


Status: current navigation entrypoint
Owner: `forprint_system_blueprint`

This file is the short entrypoint for a new Blueprint AI assistant. It does not replace
release authority, roadmap authority, Task Context, or module-local `AGENTS.md`.

## First action

From the Blueprint repository root, build the current project-entry context archive for the Blueprint assistant:

```bash
make assistant-context-pack MODULE=forprint_system_blueprint
```

The command prints the exact archive path under `tmp/project_context_archives/`.

Read that archive before broad planning or mutation when starting with little or no project
context.

## What the project-entry archive answers

It is the portfolio-level context:

- why ForPrint exists;
- current release and execution focus;
- Blueprint roadmap/current workfront;
- current module roadmap entrypoints;
- portfolio rebuild seeds for all known modules;
- current portfolio target/amendment projections;
- v0.4.1 lifecycle navigation;
- Module Memory / inventory / roadmap-reconciliation navigation.

It is intentionally bounded and does not dump the repository.

## Canonical project mission

Read the `Project mission` section in:

`coordination/roadmaps/details/forprint_system_blueprint/continuity/START_HERE.md`

That continuity file remains the current project mission/navigation authority. Do not create
a duplicate project-vision document unless later authority review proves one is needed.

## Mandatory authority chain

After opening the generated archive, follow this chain:

1. `coordination/releases/current.yaml`
2. `coordination/roadmaps/details/forprint_system_blueprint/continuity/START_HERE.md`
3. `coordination/roadmaps/details/forprint_system_blueprint/README.md`
4. `coordination/global_policy/current_execution_focus.md`
5. `coordination/roadmaps/details/forprint_system_blueprint/autonomous_multi_module_coordination_program_v0_1.md`
6. `coordination/roadmaps/details/forprint_system_blueprint/module_preparation_and_portfolio_readiness_program_v0_1.md`
7. current module roadmap/portfolio projection surfaces included in the archive
8. v0.4.1 lifecycle and self-knowledge authorities included in the archive
9. task-specific context, if a concrete task exists

Git/current release authority wins over stale snapshots and old chat context.

## Portfolio Context versus Task Context

Project-entry context answers:

> What is the whole project, what modules exist, where are they going, and where are we now?

Task Context answers:

> What exactly may this worker do for this specific prompt?

For a concrete authorized task, the canonical task-context primitive remains:

`scripts/coordination/build_context_bundle.py`

with task-aware mode `--task-context`.

The project-entry archive never grants prompt release, claim, operator approval, worker
execution, module write authority, Blueprint `ACCEPT`, or next-prompt release.

## Optional focused package

The default package carries the broad portfolio view. A module can be supplied to include
that module's detailed roadmap directory when one exists:

```bash
make assistant-context-pack MODULE=logistics_service
```

Topics can also be narrowed explicitly:

```bash
make assistant-context-pack TOPICS=purpose,release,portfolio
```

The default topic set is defined in:

`coordination/bootstrap/index_v0_1.yaml`

## Freshness

Every archive contains a manifest with:

- Blueprint HEAD and branch;
- selected topic set;
- selected source paths and SHA-256 hashes;
- tracked/untracked state for each selected source;
- missing optional/required sources;
- source-state fingerprint.

Rebuild the archive when repository authority changes or when a fresh assistant starts a
new substantial Blueprint session.

<!-- control-foundation-state-aware-handoff-v0-1:start -->
## Current execution-state reconciliation for fresh assistants

For current Blueprint execution state, do not infer progress from historical roadmap
`state:` fields, chat history, shell output, or the legacy instruction-intake handoff.

Before broad planning or mutation:

1. Run `scripts/coordination/continuity_lifecycle.py --root . status`.
2. Run `scripts/coordination/roadmap_execution_reconciliation.py --root . status`.
3. Require `ROADMAP_SYNC=IN_SYNC`; treat lifecycle events as actual execution authority
   and the roadmap spec as desired-plan authority.
4. Read the current `CURRENT_WORKFRONT`, `NEXT_HORIZON`, `SOURCE_STATE`, and
   `UNRECONCILED_CURRENT_DELTA` handoff surfaces.
5. If a canonical mutation/event already happened but generated state is stale, rebuild
   affected derived artifacts and resume from the durable stage; never replay the mutation
   merely to make validators green.
6. Distinguish a real `CANONICAL_CONFLICT` from `PROJECTION_STALE`.
7. For deterministic continuity handoff use `make assistant-pack` /
   `make assistant-handoff-check`. The broader `make assistant-context-pack` remains the
   project-entry compatibility surface while Handoff Compiler v2 is still planned.
8. Neither pack grants execution, dispatch, release, foreign-write, or operator-approval
   authority.

A fresh assistant must resolve the currently bound roadmap step/work id and its Work Front
before implementation.
<!-- control-foundation-state-aware-handoff-v0-1:end -->

<!-- strategic-transition-vector-2026-09-16:start -->
## Temporary strategic transition MUST_READ
Fresh broad coordination must read:
- `coordination/global_policy/strategic_transition_vector_v0_1.md`
- `coordination/global_policy/governed_change_and_acceptance_policy_direction_v0_1.md`

They are context/policy direction, not execution authority. They do not authorize lifecycle transition, worker dispatch, release, push/merge or foreign writes.
<!-- strategic-transition-vector-2026-09-16:end -->

<!-- operator-readable-machine-id-reporting-2026-09-17 -->
## Operator-readable status rule

Fresh assistants and generated operator-facing status must never rely on opaque technical IDs alone.

For every significant roadmap/lifecycle/work identifier, report:
1. the human-readable stage/task name;
2. a short statement of what problem that stage solves;
3. current state;
4. next meaningful action;
5. the exact technical IDs/sequences for machine correlation.

Example:

`Dispatcher — integrate Work Fronts, Execution Profiles and Handoff v2 into governed execution control (CF-09, work u180i). State: ACTIVE.`

The IDs remain mandatory; this rule adds human meaning rather than replacing machine identity.

Before broad planning, also read:
- `coordination/global_policy/strategic_transition_vector_v0_1.md`;
- `coordination/global_policy/architecture_improvement_horizon_v0_1.md`.

A freshly generated bootstrap/handoff archive is a snapshot of live state at generation time. Previously generated ZIPs do not auto-update.

## Assistant Bootstrap v0.2 and Living Knowledge

For zero-context project entry, follow the canonical startup route:

1. `coordination/instruction_intake/assistant_reading_order.md`
2. `coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml`
3. `coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml`
4. `coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`
5. `coordination/repository_knowledge/roadmap_enrichment/README.md`
6. `coordination/repository_knowledge/roadmap_enrichment/source_map.yaml`

These surfaces provide navigation and reusable knowledge only. They do not grant execution, dispatch, release, or CF10 activation authority.

<!-- cf10-temporary-parallel-assistant-coordination-2026-09-21:start -->
## Temporary parallel assistant coordination — 2026-09-21

Two independent AI workstreams may temporarily operate in this repository:

1. **CF-10 / Internal Worker Engineering**
   - bounded internal Blueprint AI worker engineering;
   - runtime, Dispatcher, Handoff v2, validation, recovery, worker tooling,
     Worker Training Queue and related self-hardening;
   - does **not** own global portfolio planning or roadmap enrichment.

2. **Roadmap Enrichment / Portfolio Knowledge**
   - deep module audits and current-state reconstruction;
   - mature target states and capability catalogs;
   - Human Intent / conversation evidence;
   - roadmap enrichment, cross-module dependencies and strategic objectives;
   - portfolio knowledge saturation and preparation for future automatic planning.

Temporary collision-avoidance convention:

- both workstreams may operate in parallel in the same repository;
- each assistant stays inside its current task and workstream;
- another workstream's changes are not rewritten, normalized, refactored or
  "improved" as incidental changes;
- before a task mutates a shared surface, or a file that clearly belongs to
  the other active workstream, prepare a short **cross-workstream notice** for
  the operator;
- the notice contains: `surface/path`, `reason`, `expected mutation`, and
  `collision risk`;
- the operator transfers that notice to the other assistant;
- absence of a response from the other assistant does **not** create write
  authority;
- canonical authority, lifecycle, Git reconciliation and existing governance
  remain unchanged;
- this is a temporary coordination convention, **not** a new execution-
  authority, locking, dispatch or handoff framework.

Canonical CF-10 Worker Training Queue:

`coordination/internal_work/blueprint/worker_training/cf10_worker_training_queue_v0_1.yaml`

The queue is planning/training metadata only. It does not grant dispatch,
release, foreign-write, commit, push, merge or automatic-accept authority.
<!-- cf10-temporary-parallel-assistant-coordination-2026-09-21:end -->

<!-- fp-assistant-context-system-specs-v0-1:start -->
## Assistant context operating map

Read `coordination/bootstrap/assistant_context_system_specs_v0_1.yaml` before broad planning or source reconciliation.

From the Blueprint repository root:

- `make assistant-context-pack` builds a context package focused on
  `forprint_system_blueprint`;
- `make assistant-context-pack MODULE=<canonical_module>` explicitly selects another
  module;
- `make assistant-context-pack TOPICS=<...>` may select additional/narrow topics.

The package is navigation/evidence only. It does not grant roadmap mutation, lifecycle,
dispatch, release, commit, push, merge or foreign-write authority.

The preferred duplicate-aware dialogue navigator is currently Master Memory v3.7, but
embedded histories are processed source-by-source and are never bulk-promoted into
current truth.
<!-- fp-assistant-context-system-specs-v0-1:end -->

<!-- module-analysis-lifecycle-methodology-v0-2:start -->
## Module analysis lifecycle methodology

For module audits, knowledge saturation, current-state reconstruction or recurring
architecture review, first resolve the current methodology through:

`coordination/bootstrap/module_analysis_methodology_current.yaml`

Current working revision:

`coordination/bootstrap/module_analysis_lifecycle_methodology_v0_2.md`

Status: **EVOLVING IMPLEMENTATION PILOT / NOT FINAL CANON**.

The methodology is a working baseline, not a rigid copy-by-template procedure.
Assistants should follow its durable evidence/authority/closeout invariants while
recording improvement proposals that can improve quality or speed.

Layer 0 is defined and piloted. Deeper layers are intentionally provisional.

Temporary analysis under `tmp/` is not durable closeout.
<!-- module-analysis-lifecycle-methodology-v0-2:end -->
