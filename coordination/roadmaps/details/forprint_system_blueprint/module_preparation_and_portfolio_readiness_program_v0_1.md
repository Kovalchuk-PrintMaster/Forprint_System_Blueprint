# Module Preparation and Portfolio Readiness Program v0.1

Status: ACTIVE_CURRENT
Owner: forprint_system_blueprint
Adopted: 2026-09-07

## Objective

Prepare every ForPrint module to the same minimum self-knowledge and execution standard before broad roadmap development begins.

## Operating decision

Blueprint does not clean, commit, push, reset, stash, rebase, or otherwise manufacture cleanliness in a foreign module repository.

Every explicit `MODULE_BOOTSTRAP` prompt begins with mandatory **Stage 0 — Module Local Hygiene**. The module assistant owns reconciliation of its own repository and may commit and push intentional preparation changes within that module branch. Force push, destructive cleanup, cross-repository writes, and hidden authority expansion remain prohibited.

## Preparation state machine

`DISCOVERED -> INVENTORIED -> BOOTSTRAP_READY -> BOOTSTRAPPED -> VERIFIED_WORK_READY`

A module enters normal roadmap development only after `VERIFIED_WORK_READY`.

## Standard bootstrap outcome

A prepared module must have:

- root `AGENTS.md`;
- deterministic inventory/index;
- implementation lineage;
- documentation authority model;
- roadmap state;
- self-maintenance/rebuild commands;
- fresh-context validation;
- module validation;
- module-owned runtime policy/profile;
- completion evidence suitable for independent Inspector review.

## Control Plane work before portfolio rollout

1. ✅ Bootstrap context mode implemented; strict Task Context Compiler remains required after Stage 0.
2. ✅ Bootstrap readiness is separated from strict development readiness.
3. ✅ Blueprint-owned bootstrap worker runtime profile implemented.
4. ✅ `forprint_project_inspector` registered/bound as the read-only project conformance reviewer.
5. ✅ Logistics bootstrap Prompt 1 v0.2 prepared as an unreleased release candidate with Stage 0 semantics.
6. Add a module preparation registry/queue.

## Project-entry context foundation

Parallel portfolio onboarding foundation:

- ✅ AUT-02 zero-context Blueprint entrypoint implemented;
- ✅ AUT-03 machine-readable bootstrap topic/source index implemented;
- ✅ AUT-04 deterministic bounded project-context archive builder implemented;
- default project-entry context includes current module roadmap entrypoints and all
  portfolio rebuild seeds, so a fresh Blueprint assistant can see the whole portfolio
  before task-specific execution;
- strict task context remains separate and mandatory for authorized execution.

## Portfolio rollout

After Control Plane bootstrap plumbing is complete:

1. close the Logistics bootstrap cycle;
2. select the next discovered module;
3. perform bounded forensic inventory;
4. prepare/reconcile its self-knowledge baseline;
5. run its bootstrap assistant;
6. independently inspect completion;
7. move it to `VERIFIED_WORK_READY`;
8. repeat until all modules are prepared.

Only after the preparation pass is complete do we build the cross-module dependency/readiness graph and choose roadmap execution priority.

## Self-knowledge / roadmap reconciliation foundation

Parallel preparation foundation completed on 2026-09-08:

- implementation ↔ inventory/lineage/document-authority ↔ roadmap reconciliation is now an
  explicit module-preparation invariant;
- Blueprint-derived module responsibilities must be evidenced in implementation or projected
  into module roadmap obligations/gaps;
- the reusable read-only analyzer is
  `scripts/coordination/build_module_roadmap_reconciliation.py`;
- Logistics has the first evidence-bound reconciliation report and remains
  `REVIEW_READY_PENDING_CANONICAL_ROADMAP_APPLY`;
- no Logistics roadmap status, prompt release, worker state or human acceptance is changed by
  the report itself.

The next Control Plane implementation remains
`module_preparation_registry_and_queue_v0_1`, which should carry pending Blueprint-derived
obligations and roadmap-reconciliation state for every module.

## Module Preparation Registry / Queue — implemented 2026-09-08

The portfolio preparation state machine now has a durable non-executing projection:

- registry: `coordination/internal_work/blueprint/module_preparation/module_preparation_registry_v0_1.yaml`;
- preparation queue: `coordination/internal_work/blueprint/module_preparation/module_preparation_queue_v0_1.yaml`;
- Blueprint-derived module obligations:
  `coordination/internal_work/blueprint/module_preparation/blueprint_module_obligations_v0_1.yaml`.

Current projection rules:

- registry/queue do not launch workers or claim prompts;
- queue order is not development priority;
- development priority selection remains forbidden until all preparation-required modules reach
  `VERIFIED_WORK_READY`;
- Logistics is `BOOTSTRAP_READY` but its replacement Prompt v0.2 still requires explicit release
  authorization;
- `forprint_project_inspector` is `DISCOVERED` and carries Blueprint-derived conformance-review
  obligations into its future forensic/bootstrap cycle;
- Calculator and Telegram Bot retain explicit historical/legacy-risk flags.

The next portfolio action is operator selection of the next module for forensic preparation,
while the Logistics bootstrap release decision remains a separate explicit authority gate.

## Inspector repository provisioning gate — 2026-09-08

`forprint_project_inspector` cannot enter forensic inventory/bootstrap yet.

`coordination/module_sources/module_git_sources.yaml` records the planned local path, `repo_url: null`,
`repo_status: planned_directory_created` and `development_status: planned_bootstrap_pending`.
The local directory exists but is not a Git repository.

Blueprint does not invent a remote, run `git init`, clone, or create a remote without explicit
provisioning authority. Durable blocker:
`coordination/internal_work/blueprint/module_preparation/forprint_project_inspector_repository_provisioning_gap_v0_1.yaml`.

Inspector remains `DISCOVERED` with nine Blueprint-derived obligations preserved. Other modules
with existing repositories may continue forensic preparation in parallel.

