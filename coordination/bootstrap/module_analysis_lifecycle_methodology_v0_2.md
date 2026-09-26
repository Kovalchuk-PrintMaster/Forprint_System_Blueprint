---
document_id: forprint_module_analysis_lifecycle_methodology_v0_2
title: ForPrint Module Analysis Lifecycle Methodology
revision: v0.2
status: EVOLVING_IMPLEMENTATION_PILOT
maturity: WORKING_BASELINE_NOT_FINAL_CANON
authority: current_working_methodology_navigation_and_analysis_guidance
implementation_authority_created: false
roadmap_mutation_authority_created: false
execution_authority_created: false
owner: forprint_system_blueprint
introduced_after_pilots:
  - forprint_library
  - forprint_operations_control_registry
change_policy: IMPROVEMENT_PROPOSALS_EXPLICITLY_WELCOME
default_operator_decision_for_discovered_module_changes: action_now_none
---

# ForPrint Module Analysis Lifecycle Methodology v0.2

> **STATUS — EVOLVING IMPLEMENTATION PILOT / NOT FINAL CANON**
>
> This is the current working baseline for repeatable ForPrint module analysis.
> It is intentionally not immutable or final. New assistants should use it by default,
> but are explicitly encouraged to propose improvements that increase analytical quality,
> reduce unnecessary work, improve repeatability or shorten the path to trustworthy conclusions.
> Improvements must be visible and reviewable; they must not silently weaken evidence,
> authority boundaries, historical preservation or durable closeout.

## 1. Purpose

ForPrint modules evolve continuously. A module may be heavily refactored, change identity,
accumulate obsolete documents, carry several runtime generations, diverge from Blueprint,
or remain stable while the surrounding architecture changes.

Module analysis is therefore a **repeating lifecycle**, not a one-time migration.

The methodology exists so every assistant can:

1. reconstruct what the module actually is now;
2. distinguish implementation from historical intent;
3. identify trustworthy and non-trustworthy sources;
4. compare the module with current Blueprint/Human Intent/roadmap architecture;
5. detect duplication, stale generations, contradictions and unresolved ownership;
6. produce comparable reports across modules;
7. promote temporary analysis into durable repository-owned knowledge;
8. preserve provenance for later reasoning;
9. make each later audit cheaper;
10. improve the methodology itself.

## 2. Relationship to v0.1

Historical predecessor:

`coordination/bootstrap/module_snapshot_and_roadmap_rebuild_analysis_mode_v0_1.md`

Its core rules remain valid:

- audit is reconstruction before repair;
- divergence is evidence, not implementation authority;
- current implementation, historical documentation, roadmap representation,
  modern strategic direction and future roadmap input stay distinct;
- stale/superseded/conflicting material is preserved and classified;
- analytical findings do not create implementation authority;
- default discovered-work disposition is `action_now: none`.

v0.2 extends that protocol with:

- a repeating multi-layer lifecycle;
- a detailed Layer 0 proven on Library and Operations Control Registry;
- standardized durable snapshot closeout;
- temporary-evidence promotion;
- a legacy-heavy module profile;
- a methodology improvement loop;
- clean-tree-first working discipline;
- stronger parallel-assistant ownership rules.

Keep v0.1 as historical methodology provenance.

## 3. External engineering ideas used as reference

This remains ForPrint-specific; no external framework is copied wholesale.

### Architecture Reconstruction

SEI architecture reconstruction recovers an **as-built** architecture from legacy implementation
evidence, builds successive abstractions and compares the result with **as-designed** architecture.

ForPrint adopts this strongly in Layer 0:

`repository evidence -> semantic grouping -> reconstructed module model -> current architecture comparison`

### ATAM

ATAM evaluates architecture against quality goals and identifies risks, sensitivity points and
tradeoffs. ForPrint reserves these ideas mainly for deeper layers rather than making every L0
snapshot a formal ATAM.

### Evolutionary Architecture / fitness functions

Evolutionary Architecture uses tests, metrics and other fitness functions to protect important
architectural characteristics as systems evolve.

ForPrint uses this concept for later recurring conformance/drift checks.

### Decision-history / supersession

Historical architectural decisions should remain explainable.

ForPrint therefore prefers:

`preserve old record -> classify -> create newer current decision -> record supersession`

rather than rewriting history to make old evidence appear current.

### Software quality models

ISO/IEC 25010-style quality dimensions may later structure deeper quality layers.
Layer 0 does not try to score every quality attribute.

## 4. Fundamental invariants

### 4.1 Evidence before repair

`DISCOVERED_DIVERGENCE != AUTHORIZATION_TO_FIX`

### 4.2 Repository reality is evidence, not automatic authority

Current code may itself be transitional or architecturally stale.

### 4.3 Document existence is not authority

Names such as `canonical`, `accepted`, `final`, `current`, `architecture` or `contract`
do not establish present authority by themselves.

### 4.4 Green tests are not architectural acceptance

A green validator may validate stale assumptions.

`TEST_PASS != ARCHITECTURAL_CORRECTNESS`

`VERIFIED != ACCEPTED`

### 4.5 Preserve historical evidence during analysis

Deletion/retirement is a separate task.

### 4.6 `tmp/` is not durable knowledge

Important analysis must be promoted before closeout.

### 4.7 Standardize outputs, not every internal packet

Modules can need different packetization. Durable outputs and closeout semantics should remain comparable.

### 4.8 Avoid roadmap duplication

Enrich an existing step when it already owns the direction.

### 4.9 Local truth, central projection

Detailed evidence lives in the module repository. Blueprint keeps portfolio interpretation,
registration and central ownership/roadmap consequences.

## 5. Repeating analysis lifecycle

Only L0 is fully specified in v0.2. L1-L4 are intentionally provisional.

```text
L0  Baseline Reconstruction & Knowledge Stabilization
    ↓
L1  Authority & Architecture Conformance
    ↓
L2  Domain / Contract / Data Deep Reconciliation
    ↓
L3  Operational Fitness / Security / Recovery Evaluation
    ↓
L4  Periodic Drift Reassessment
    ↺ escalate to any deeper layer when drift requires it
```

A module need not run every layer every time.

## 6. Layer 0 — Baseline Reconstruction & Knowledge Stabilization

Status: `DEFINED_AND_PILOTED`

Pilots:

- `forprint_library`
- `forprint_operations_control_registry`

Use L0 when:

- the module has never had a durable audit;
- a major refactor occurred;
- repository/package identity changed;
- documentation has been unreconciled for a long time;
- legacy/history is dense;
- portfolio planning needs trustworthy current-state evidence;
- a neighboring module needs reliable dependency/ownership information.

### 6.1 Objective

Answer:

> What is this module now, how did it get here, how does it relate to the current ecosystem,
> and what durable evidence must remain after temporary analysis disappears?

L0 is primarily knowledge reconstruction/stabilization, not code-quality repair.

### 6.2 L0-A — Entry and clean-state preflight

Before mutation:

1. resolve repository identity;
2. record branch, HEAD, upstream;
3. record Git status;
4. classify pre-existing dirty paths;
5. identify parallel work ownership;
6. define the analysis write set;
7. protect foreign-owned parallel files;
8. record Blueprint branch/HEAD and relevant authority;
9. locate latest durable snapshot;
10. record why the audit was triggered.

Preferred state: `CLEAN_TREE_FIRST`.

If no parallel work exists, start from a clean repository.

During temporary parallel work:

- foreign dirty paths may exist;
- own write set must be attributable;
- target collision is a stop condition;
- commit/push only own bounded work;
- do not accumulate owned dirt across unrelated tasks.

Never manufacture cleanliness with broad reset/clean or automatic stash/pop of foreign work.

### 6.3 L0-B — Coarse inventory

Map before deep reading:

- source packages;
- config;
- schemas;
- storage/repositories;
- services/use cases;
- contracts/DTOs/events;
- integrations/adapters;
- tests;
- validators;
- Makefile/operator surface;
- coordination;
- reports;
- docs;
- historical/legacy paths;
- generated outputs;
- temp artifacts;
- dependency/reference surfaces.

Where useful inspect current worktree plus historical/deleted tracked sources.

Do not assume:

`deleted tracked == semantically retired`

`untracked replacement == accepted current truth`

### 6.4 L0-C — Large thematic segmentation

Do not micro-analyze hundreds of files one by one in chat.

Default packet model:

#### A — Identity / History / Documentation / Roadmap Lineage

Repository/package identity, rename history, status, architecture docs, roadmap,
completion history, historical/superseded material, provenance.

#### B — Domain / Runtime / Capabilities / Persistence

Models, services, repositories, lifecycle, runtime entrypoints, persistence, projections,
business capability foundations.

#### C — Ownership / Contracts / Integrations / Cross-Module Boundaries

DTOs, references, commands/events, contracts, foreign dependencies, integration edges,
source-of-truth boundaries.

#### D — Governance / Validation / Operator / Security / Recovery

Tests, validators, Makefile, reports, completion/governance workflows, runtime safety,
auth/security exposure, idempotency/retry/recovery, operational readiness.

A-D is a default, not a rigid file taxonomy. Prefer a few large packets over many micro-gates.

### 6.5 L0-D — Packet semantic review

Each packet should produce:

- human-readable `.md`;
- machine-readable `.yaml` when practical.

Preferred classifications:

- `CURRENT_CANONICAL`
- `CURRENT_USEFUL`
- `HISTORICAL_CONTEXT`
- `SUPERSEDED`
- `CONTRADICTS_CURRENT_ARCHITECTURE`
- `DUPLICATE`
- `UNCERTAIN_NEEDS_RECONCILIATION`
- `CANDIDATE_RETIREMENT`

Review what exists, what is current/historical/duplicated/conflicting/missing,
what requires cross-project reconciliation, and what is only supporting evidence.

No implementation during packet review.

### 6.6 L0-E — Comprehensive module audit

After all packets, synthesize one audit covering at minimum:

- current identity;
- repository maturity;
- implemented core;
- next-generation/partial foundations;
- duplicate model generations;
- ownership;
- contracts/integrations;
- roadmap realization;
- stale documentation;
- validator semantic drift;
- operator surface;
- security exposure;
- recovery/resilience maturity;
- contradiction register;
- unresolved/deferred decisions.

### 6.7 L0-F — Cross-project Blueprint reconciliation

Compare the comprehensive audit with:

- `machine/modules.yaml`;
- `machine/ownership.yaml`;
- `machine/contracts.yaml`;
- `machine/data_flows.yaml`;
- `machine/data_objects.yaml`;
- Human Intent;
- module/portfolio roadmaps;
- Contract Registry direction;
- relevant neighboring snapshots.

Preferred dispositions:

- `ALREADY_REPRESENTED`
- `REFINE_EXISTING`
- `MACHINE_DELTA_CANDIDATE`
- `PROJECT_LEVEL`
- `HISTORICAL_OR_SUPPORTING_ONLY`
- `CONTRADICTION_REQUIRES_RECONCILIATION`
- `UNRESOLVED`

A mismatch can mean module stale, Blueprint stale, both transitional, ownership unresolved,
or project-level schema missing.

### 6.8 L0-G — Bounded canonical enrichment

Only after adjudication:

- enrich existing roadmap steps where possible;
- avoid parallel H-step proliferation;
- preview before apply;
- hash-precondition targets;
- fail closed on collision;
- keep machine changes separate from prose changes;
- do not guess machine schema where target semantics are unresolved;
- preserve approval/execution authority unless separately authorized.

### 6.9 L0-H — Durable module snapshot promotion

L0 is not complete while important evidence lives only in `tmp/`.

Recommended module-local structure:

```text
coordination/
├── reports/
│   └── analysis/
│       ├── YYYY-MM-DD__<module_id>__module_snapshot_v0_1.md
│       ├── YYYY-MM-DD__<module_id>__roadmap_rebuild_input_v0_1.yaml
│       └── index.yaml
└── repository_knowledge/
    └── module_snapshots/
        └── <module_id>/
            ├── index.yaml
            └── YYYY-MM-DD/
                ├── README.md
                ├── snapshot_manifest.yaml
                ├── related_module_snapshots.yaml
                └── analysis_evidence/
                    ├── inventory/
                    ├── thematic_reviews/
                    ├── comprehensive_audit/
                    ├── cross_project_reconciliation/
                    ├── semantic_adjudication/
                    ├── canonical_enrichment/
                    ├── deferred_candidates/
                    └── provenance/
```

### 6.10 Required snapshot manifest semantics

At minimum:

```yaml
module_id:
snapshot_date:
analysis_methodology_revision:
analysis_layers_completed:
repository:
  branch:
  head:
  upstream:
  upstream_head:
  remote_synced:
worktree_observation:
  clean_at_snapshot_commit:
  preexisting_parallel_context:
durable_evidence:
  root:
  file_count:
  aggregate_hash_or_manifest:
authority:
  snapshot_is_historical_evidence: true
  overrides_module_policy: false
  overrides_blueprint_policy: false
  implementation_authority_created: false
roadmap:
  reconciliation_status:
machine:
  reconciliation_status:
deferred:
  machine_candidates:
  unresolved_questions:
temporary_evidence:
  all_required_tmp_promoted:
  tmp_safe_to_remove:
```

### 6.11 `tmp_safe_to_remove`

Set true only after:

1. required evidence is in durable module paths;
2. manifest has hashes/counts;
3. snapshot files are tracked;
4. module snapshot commit exists;
5. module snapshot commit is pushed/remote-contained;
6. Blueprint registration points to the exact durable snapshot;
7. no required conclusion exists only in chat or `tmp/`.

### 6.12 L0-I — Blueprint registration

Recommended:

```text
coordination/repository_knowledge/
└── module_knowledge_stabilization/
    └── snapshots/
        └── YYYY-MM-DD__<module_id>__snapshot_registration_v0_1.yaml
```

Registration stores module ID/date, repo branch/HEAD/upstream, remote containment,
durable evidence count, module-local paths, manifest hash, completed layers,
roadmap/machine reconciliation status, authority limits and future use.

It is historical evidence/portfolio input, not a second runtime truth source.

### 6.13 L0-J — Preferred closeout order

1. build module-local snapshot;
2. validate durable counts/hashes;
3. commit module snapshot files only;
4. push module snapshot;
5. verify remote containment;
6. add Blueprint registration;
7. include already-reviewed roadmap enrichment if applicable;
8. commit only Blueprint closeout files;
9. push Blueprint closeout;
10. set/confirm `tmp_safe_to_remove: true`;
11. temp evidence may later be cleaned.

## 7. L1 — Authority & Architecture Conformance

Status: `PROVISIONAL_SKELETON`

Future purpose:

- detailed source-of-truth boundaries;
- as-built vs current as-designed comparison;
- module identity/role/dependency correctness;
- shadow registries/duplicated ownership;
- stale validators/docs enforcing obsolete architecture;
- machine graph vs implementation.

Potential outputs: authority map, conformance matrix, shadow-owner register,
machine-delta candidates, contract-role discrepancies.

Do not treat this skeleton as final.

## 8. L2 — Domain / Contract / Data Deep Reconciliation

Status: `PROVISIONAL_SKELETON`

Future purpose:

- aggregates/model generations;
- lifecycle/state decomposition;
- API/contract semantics;
- schema evolution;
- commands/events/queries;
- data retention/migration;
- provider/caller vs publisher/receiver;
- persistence model vs domain model.

## 9. L3 — Operational Fitness / Security / Recovery

Status: `PROVISIONAL_SKELETON`

Possible dimensions:

- test relevance;
- architecture fitness functions;
- operator workflows;
- observability;
- idempotency;
- failure handling;
- retries/dead-letter;
- backup/restore;
- restart recovery;
- security/auth/authz;
- privacy/adversarial input;
- production-entry gates;
- performance/reliability;
- release rollback.

Future revisions may use ISO/IEC 25010 or ATAM-style scenarios as organizing aids.

## 10. L4 — Periodic Drift Reassessment

Status: `PROVISIONAL_SKELETON`

Possible triggers:

- major refactor;
- release;
- contract/ownership change;
- new external integration;
- long period since snapshot;
- suspicious runtime/documentation drift;
- portfolio architecture revision.

Expected behavior:

1. compare current fingerprint with latest durable snapshot;
2. identify material changed areas;
3. rerun only affected analysis where safe;
4. escalate to deeper layer when needed;
5. publish a new dated snapshot instead of rewriting history.

## 11. Legacy-heavy module profile

Known future candidates:

- `calculator_engine`
- `telegram_bot`

Analyze these later, after more methodology pilots.

### 11.1 Default assumptions

Do not assume newest-looking document is correct.
Do not assume oldest code is obsolete.
Do not assume passing tests represent current architecture.
Do not assume an historical `accepted` document still has current authority.

### 11.2 Required extra registers

#### Document-generation register

For major document families record path, date/commit when recoverable, era/generation,
current references, authority classification, superseded-by, contradiction, duplication,
and retention reason.

#### Code-generation register

For overlapping implementations record package/path, runtime reachability, callers/imports,
Make/operator path, tests, config selector, storage/schema relationship, generation,
actual-use evidence, and retirement/migration candidacy.

#### Validator-semantic register

For each important validator record the invariant, whether it is still current,
whether green can validate obsolete architecture, and current target rule when known.

### 11.3 Extra classifications

- `ACTIVE_CURRENT_GENERATION`
- `ACTIVE_COMPATIBILITY_GENERATION`
- `HISTORICAL_RUNTIME_GENERATION`
- `UNREFERENCED_CANDIDATE`
- `DUPLICATE_IMPLEMENTATION`
- `SUPERSEDED_BUT_REQUIRED_FOR_MIGRATION`
- `CONTRADICTS_CURRENT_ARCHITECTURE`
- `UNKNOWN_RUNTIME_REACHABILITY`
- `CANDIDATE_RETIREMENT`

No physical cleanup during discovery.

### 11.4 Legacy triangulation rule

Use together:

```text
current runtime
+ focused tests
+ current docs
+ historical docs
+ current Blueprint/Human Intent
+ Make/operator entrypoints
```

No single category is sufficient alone.

## 12. Methodology improvement loop

Every audit may emit `methodology_improvement_candidates`.

Suggested fields:

```yaml
candidate_id:
layer:
problem_observed:
current_method_cost_or_gap:
proposed_change:
expected_quality_effect:
expected_speed_effect:
evidence_preservation_effect:
risk:
requires_operator_approval:
pilot_module:
disposition:
```

Possible dispositions:

- `TRY_IN_CURRENT_READ_ONLY_ANALYSIS`
- `PILOT_ON_NEXT_MODULE`
- `ACCEPT_FOR_NEXT_REVISION`
- `REJECT`
- `DEFER`
- `NEEDS_MORE_EVIDENCE`

An assistant may adapt read-only packet size/boundaries, extraction technique, report layout,
reading order and temporary scripts when coverage/authority/closeout are preserved.

Operator review is required before changing authority semantics, Git policy, retention,
required durable outputs, cleanup rules or automatic canonical mutation.

## 13. Clean-tree-first working discipline

### 13.1 New default

`CLEAN_TREE_FIRST`

Broad dirty Blueprint state is no longer the preferred normal working style.

### 13.2 Preserve the reason the old rule existed

The old compatibility rule correctly taught that:

- task compatibility is not identical to global cleanliness;
- unrelated work must not be destroyed;
- execution ownership must remain attributable;
- true parallelism should use isolated workspaces.

Keep that history.

Do not interpret it as permission to accumulate unrelated uncommitted work indefinitely.

### 13.3 Default behavior

Without parallel work:

`start clean -> bounded work -> validate -> commit -> push -> clean owned scope`

With parallel assistants:

- explicit write sets;
- foreign dirty paths are read-only context;
- target collision stops mutation;
- stage/commit only own files;
- never `git add .` / `git add -A`;
- own work is committed/pushed promptly;
- prefer isolated worktrees for true concurrency.

### 13.4 Grandfather active CF-10

Do not retroactively damage current CF-10 work.

- no reset/stash/clean of CF-10;
- no rewrite of its execution baseline;
- no staging CF-10-owned paths in analysis commits;
- apply clean-tree-first forward as workstreams reach safe commit boundaries.

Dirty state may still be analytical evidence.

## 14. Parallel assistant discipline

1. define owned targets before mutation;
2. capture target precondition hashes;
3. fail on exact target collision;
4. do not reinterpret foreign files;
5. do not stage foreign files;
6. do not clean foreign temp evidence;
7. commit only owned files;
8. push own commit;
9. publish new HEAD before a dependent mutation.

Long-term: isolated Git worktrees / attributable execution workspaces.

## 15. Standard report family

Recommended durable roles:

- `module_snapshot`
- `roadmap_rebuild_input`
- `snapshot_manifest`
- `related_module_snapshots`
- `thematic_review_*`
- `comprehensive_audit`
- `cross_project_reconciliation`
- `semantic_adjudication`
- `canonical_enrichment_receipt`
- `deferred_candidates`

## 16. Snapshot immutability

Later audits create later dated snapshots.

Do not rewrite old snapshots to make history look clean.

A later snapshot may explicitly confirm, supersede, reclassify, resolve, invalidate or retire
an earlier conclusion.

## 17. Fresh-assistant startup behavior

When starting module analysis:

1. read current bootstrap/authority;
2. read the current module-analysis methodology pointer;
3. determine requested layer;
4. locate latest durable module snapshot;
5. inspect Git cleanliness/ownership;
6. identify parallel work;
7. distinguish read-only analysis from mutation;
8. build only needed temp evidence;
9. preserve standard output semantics;
10. record methodology improvements instead of silently inventing a new process.

## 18. Current pilot status

### Library

Reference pilot for durable module-local snapshot, evidence promotion,
Blueprint snapshot registration and remote-contained historical baseline.

### Operations Control Registry

Reference pilot for large thematic packets, comprehensive audit,
cross-project reconciliation, roadmap enrichment and machine-delta deferral.

Operations is not fully closed until its durable snapshot and Blueprint registration are pushed.

## 19. Definition of L0 complete

```yaml
all_large_packets_reviewed: true
comprehensive_audit_complete: true
cross_project_reconciliation_complete: true
roadmap_reconciliation_complete_or_explicitly_no_change: true
machine_deltas_applied_or_explicitly_deferred: true
durable_module_snapshot_written: true
durable_evidence_tracked: true
module_snapshot_commit_pushed: true
blueprint_snapshot_registration_written: true
blueprint_closeout_commit_pushed: true
tmp_safe_to_remove: true
methodology_improvement_candidates_recorded: true
```

## 20. Revision policy

This methodology is expected to change.

Create a new revision when evidence justifies meaningful change.

Potential milestones:

- v0.3 after more L0 pilots;
- dedicated L1 protocol after authority/conformance work matures;
- standardized drift profile after recurring audits;
- dedicated legacy-heavy revision after Calculator Engine and Telegram Bot analysis.

Preserve previous revisions and explain compatibility implications.

## 21. Closing principle

The methodology must not become bureaucracy that costs more than the knowledge it preserves.

Preferred direction:

```text
fewer large evidence passes
+ stronger semantic synthesis
+ durable standardized closeout
+ explicit authority
+ clean attributable Git history
+ recurring lightweight drift checks
+ continuous methodology improvement
```

A successful process lets a new assistant understand the previous evidence, repeat the method,
challenge it where justified, and leave the project easier to understand than she found it.

## Appendix A — External reference points used while shaping v0.2

These sources are reference material, not ForPrint authority:

- Carnegie Mellon SEI — *Architecture Reconstruction Guidelines*:
  https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines/
- Carnegie Mellon SEI — *Architecture Reconstruction Guidelines, Third Edition*:
  https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/
- Carnegie Mellon SEI — *Architecture Tradeoff Analysis Method (ATAM)*:
  https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-atam/
- Thoughtworks — *Building Evolutionary Architectures, 2nd Edition*:
  https://www.thoughtworks.com/insights/books/building-evolutionaryarchitectures-second-edition
- Martin Fowler — *Architecture Decision Record*:
  https://martinfowler.com/bliki/ArchitectureDecisionRecord.html
- ISO/IEC 25010:2023 — product quality model:
  https://www.iso.org/standard/78176.html

The methodology borrows ideas selectively:

- reconstruct as-built architecture before redesign;
- reason explicitly about architectural risks/tradeoffs;
- use fitness functions for recurring conformance;
- preserve decision history through supersession rather than rewriting;
- use quality models as later-layer checklists rather than forcing them into Layer 0.

