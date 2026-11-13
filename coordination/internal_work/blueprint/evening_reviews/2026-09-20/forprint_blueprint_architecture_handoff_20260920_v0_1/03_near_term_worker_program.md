# Near-Term Worker Program

This file defines the capabilities considered mature enough to enter Blueprint reconciliation and incremental implementation planning after repository audit.

## Workstream A — Existing architecture reconciliation

Priority: `FIRST`

Objectives:

- find all existing execution-profile, worker-runtime, graph/index, publication, Inspector, Library, Dispatcher, continuity, and legacy-wave mechanisms;
- produce `REUSE/EXTEND/ADAPT/REPLACE/NEW` decisions;
- identify conflicting policies, duplicated terminology, and partially implemented capabilities;
- do not create a second control plane before this audit.

Expected artifact: bounded reconciliation matrix + recommended first implementation step.

## Workstream B — Worker Execution Sandbox & Capability Control

Direction:

- extend existing execution profiles, not replace them;
- make permissions a ceiling;
- enforce filesystem/network/device/secrets/resource boundaries outside prompt memory;
- introduce scoped work-lease authority;
- design an action/capability broker for sensitive operations;
- support read/query access to strategic context while preventing foreign-module mutation;
- capture denied/allowed high-risk actions in audit events.

Initial target should be minimal and testable, not a full container platform rewrite.

## Workstream C — Reuse-First Capability Discovery / Novelty Gate

Direction:

- require bounded discovery before new architectural capability implementation;
- produce `Reuse Assessment` evidence;
- support dispositions `REUSE`, `EXTEND`, `ADAPT`, `REPLACE`, `NEW`;
- make `NEW` require explicit rationale;
- gate source-mutation implementation state where appropriate;
- avoid applying heavy architectural gate to trivial helper functions;
- later detect potential parallel frameworks and novelty-rate anomalies.

## Workstream D — Implementation Knowledge & Traceability Graph

Direction:

- typed nodes: capability, process, policy, standard, decision, contract, schema, script, symbol, validator, test, target, generated artifact, runtime service, module, interface;
- typed edges: implements, calls, imports, depends_on, reads, writes, produces, consumes, validates, tested_by, governed_by, constrained_by, generated_by, publishes, subscribes_to, supersedes, derived_from, owned_by;
- provenance/confidence on inferred edges;
- fast graph slices around a concept/process;
- impact/blast-radius analysis;
- coherent bundle compiler for focused audits;
- semantic-consistency review inputs;
- no replacement of current indexes.

## Workstream E — Publication Control Plane

Initial placement: `forprint_system_blueprint` hosted capability, extraction-ready.

Responsibilities:

- validate promotion manifests;
- confirm candidate SHA/fingerprint/current checks;
- evaluate publication risk/policy/required approvals;
- integrate with protected Git provider through adapter;
- trigger/observe merge queue or equivalent serialized promotion;
- publish immutable promotion events;
- never decide strategic work priority or execution completion itself.

Non-responsibilities:

- Planner decides desired work/state;
- Dispatcher provides execution lifecycle facts;
- Inspector provides diagnostics/evidence;
- Publication Controller owns canonical Git promotion decision/execution under policy.

## Workstream F — Promotion Milestones / Promotion Manifest

Define a promotion boundary separate from roadmap ordering.

A Promotion Manifest should minimally bind:

- promotion ID;
- module;
- accepted milestone/functionality;
- candidate branch and exact HEAD SHA;
- included work IDs;
- validation evidence;
- unresolved blockers;
- risk class;
- required approvals;
- target canonical branch;
- dispatcher/completion evidence references.

## Workstream G — Capability Lifecycle / Publication Review Model

Near-term work is architectural/contracts only until ownership audit is complete.

Desired model:

- versioned capability/revision metadata;
- lifecycle states;
- release manifests;
- consumer/subscriber awareness;
- publication events;
- explicit consumer review decisions;
- Inspector reconciliation of unreviewed/stale/deprecated usage;
- no forced universal upgrades.

`ForPrint Library` is a plausible host for catalog/discovery metadata, but this is **not canonical until current Library boundaries are audited**.

## Workstream H — Portfolio Planning / Dependency Intelligence / Convergence Engine

Initial placement: Blueprint hosted capability, extraction-ready.

Near-term foundation:

- canonical/normalized portfolio graph model;
- typed dependencies and ownership;
- current planning revision model;
- import of real current roadmaps, including messy/variable horizons;
- scenario/dry-run separation from apply;
- planning desired state vs execution actual state;
- event-watermark/freshness semantics;
- machine-readable reports;
- no autonomous strategic priority changes.

Current project phase: `Portfolio Knowledge Saturation` — expand knowledge before perfect global sequencing.

## Workstream I — Index/Graph/View integration

Formalize:

- canonical sources;
- derived search indexes;
- relationship graphs;
- generated human views;
- invalidation/rebuild rules;
- no fourth competing source of truth.

## Sequencing rule

Do not assign all workstreams simultaneously. Convert them into one bounded formal work item at a time, beginning with repository reconciliation.
