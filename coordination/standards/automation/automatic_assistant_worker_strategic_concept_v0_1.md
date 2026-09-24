# ForPrint Automatic Assistant / Governed Worker

## Strategic Concept & Architecture Intent v0.1

**Date:** 2026-09-24
**Status:** `CURRENT_STRATEGIC_REFERENCE`
**Authority class:** `NON_EXECUTION_AUTHORITY / REFERENCE_ONLY`
**Scope:** ForPrint-wide automatic-assistant / governed-worker architecture
**Current implementation pilot:** `CF-10 / u180j / Blueprint-internal zero-stage worker`
**Primary purpose:** preserve the long-term architectural intent used to guide roadmap design, local implementation choices, portability decisions, and future autonomy expansion.

> **This document is deliberately evolvable.** It is not a frozen final design and it does not grant execution authority. It may be refined, extended, reorganized, or superseded when a safer, simpler, faster, more observable, more portable, or more maintainable design is proven. Improvements are welcome when they preserve or explicitly reconcile the core safety and governance goals.

> **Conflict rule:** current canonical authority wins. If this concept conflicts with the Project Constitution, Module Policy, Execution Profile, active Work Front, accepted contract, or current lifecycle/roadmap authority, the canonical authority governs execution until an explicit reconciliation updates the appropriate artifact.

---

## Strategic document role

This document answers **“what are we trying to build and why?”**.

It intentionally does **not** replace:

- a roadmap — which answers **what should be implemented next and in what order**;
- a Work Front — which defines the exact bounded executable authority for one task;
- an Execution Profile — which defines reusable execution constraints;
- a contract or standard — which defines enforceable machine/human requirements;
- lifecycle / continuity state — which records what is actually active, blocked, completed or accepted;
- generated indexes / projections — which are derived navigation and status surfaces.

The intended hierarchy is:

`Strategic Concept -> Roadmap / Program -> Work Front -> Execution -> Evidence -> Validation -> Acceptance / Publication`

The concept may inspire future roadmap items, but **must not activate them by itself**.

---

## Evolution policy

The concept should evolve under the following rules:

1. **Prefer improvement over dogma.** A previous design choice may be changed when the new approach measurably improves safety, speed, clarity, observability, portability, maintainability or operator effort.
2. **Do not silently erase rationale.** Material conceptual changes should record what changed and why.
3. **Do not use the concept to bypass authority.** Strategic intent never substitutes for a missing Work Front, policy, approval, dependency or acceptance gate.
4. **Keep implementation reality visible.** A desired capability should be distinguishable from a capability that is actually implemented and validated.
5. **Avoid duplicate architecture.** Before introducing a new mechanism, inspect existing capabilities and extend/reuse them where reasonable.
6. **Preserve forensic history.** The concept can change; immutable execution-attempt history must not.
7. **Version significant conceptual shifts.** Minor clarification may update the current version through normal Git history; a materially different architecture should become a new version and explicitly supersede the previous concept.
8. **Keep one discoverable current reference.** The automation/document index should identify which version is the current strategic reference.

---

## Relationship to the current CF-10 roadmap

The present CF-10 training queue is **consistent with this concept** and should remain the implementation sequence for the Blueprint-internal pilot.

| CF-10 order | Training task | Strategic concept area | Alignment |
|---:|---|---|---|
| 10 | `dispatcher_zero_stage_regression_mutation_proof` | bounded mutation, isolated execution, worker delta | aligned / proven |
| 20 | `operator_status_surface_self_hardening` | operator visibility, derived status, no new authority | aligned / proven |
| 30 | `verification_tier_self_hardening` | execution profiles, verification intent, independent validation | aligned / proven |
| 40 | `worker_watchdog_observability_self_hardening` | observability, heartbeat, stall/timeout distinction | aligned / current |
| 50 | `local_dispatcher_telegram_operator_surface` | operator interaction / transport without authority widening | aligned / planned |
| 60 | `human_dashboard_self_hardening` | machine-readable facts projected to human-readable status | aligned / planned |
| 70 | `validation_check_pipeline_profile_and_optimization` | efficiency, measurable cost, same-or-stronger validation | aligned / planned |
| 80 | `planning_projection_cursor_sync_audit` | roadmap/lifecycle reconciliation, freshness | aligned / planned |
| 90 | `automatic_task_materialization` | plan -> bounded Work Front / task candidate, no automatic dispatch | aligned / planned |
| 100 | `project_execution_planning_system_control_task` | Blueprint-local planning/control core and final CF-10 stability evidence | aligned / final CF-10 control task |

### Important interpretation

CF-10 is **not the whole automatic-assistant program**. It is the internal proving/training phase.

The broader strategic concept additionally requires post-CF-10 work for:

- portable module task-intake / pull adapters;
- module bootstrap/adoption interfaces;
- portable task-context compilation;
- module Knowledge Index / Knowledge Base consumption;
- provider/runtime adapter conformance beyond one provider;
- result/completion exchange back to Blueprint;
- portable adoption/conformance tests;
- external-module pilot;
- progressive-autonomy evidence and metrics;
- budget/cost/runaway controls;
- broad multi-module rollout only after pilot evidence.

These should become separate bounded roadmap/work-front items when their prerequisites are met. They should **not be injected into CF-10 task #4–#10 merely to make CF-10 look more complete**.

---

## Current strategic reconciliation conclusion — 2026-09-24

The architecture direction in this document and the current CF-10 queue are compatible.

The most important already-demonstrated direction is:

`Intent / Plan -> bounded authority -> fresh context -> sealed workspace -> exact ACK -> explicit dispatch -> isolated worker -> delta -> independent validation -> separate promotion/publication`

The most important remaining internal-pilot capabilities are the current queue tasks #4–#10.

The most important capabilities **outside** the CF-10 closure boundary are portability and external-module adoption. They remain strategic follow-on work and should be activated only through later roadmap/lifecycle decisions.

No current CF-10 task should gain cross-module write authority merely because the long-term concept includes multi-module adoption.

---

# 0. How to use this document

This document is intentionally broader than CF-10.
CF-10 is the current **Blueprint-internal zero-stage worker pilot**. The target architecture is a **portable ForPrint worker pattern** that can later be adopted by other modules without turning Blueprint into a process that directly edits every module repository.
For every requirement below, the implementation assistant should mark one of:

- `IMPLEMENTED_AND_VALIDATED`
- `IMPLEMENTED_NOT_YET_VALIDATED`
- `PARTIAL`
- `PLANNED`
- `DEFERRED_BY_DESIGN`
- `NOT_APPLICABLE`
- `MISSING`
- `CONFLICT_REQUIRES_RECONCILIATION`

The brief separates three evidence classes:

1. **CURRENT VERIFIED SURFACE** — present in current/recent Blueprint runtime/contracts/tests.
2. **ACCEPTED OWNER / ARCHITECTURAL INTENT** — recovered from recent dialogue enrichment and earlier accepted design discussion.
3. **TARGET PORTABLE STATE** — required for safe rollout to other modules; it may not yet exist.

Historical material is provenance, not current authority. If a current policy/contract conflicts with an old conversation or old design note, current canonical authority wins until an explicit reconciliation changes it.

---

# 1. Executive target

The ForPrint automatic assistant should not be one monolithic "AI daemon".
It should be a **governed execution stack** where:

- Blueprint or another authorized planning/control surface defines a bounded task;
- the target module **pulls/intakes** the task through its local coordination flow;
- a fresh worker receives a bounded, deterministic context package;
- authority is resolved before execution;
- execution happens in an isolated workspace;
- the model/provider is replaceable and selected per attempt;
- the worker cannot silently widen its own authority;
- all attempts are durable and append-only;
- results are returned through a typed/validated result path;
- acceptance, publication, release and next-step activation remain separate governed decisions;
- the same worker architecture can be adapted to Library, Logistics, Calculator, Telegram Bot and other modules with module-specific policy/configuration instead of copying Blueprint-specific logic.

A short target formula:
`Intent/Plan -> Work Front -> Context -> Approval/Gates -> Dispatch -> Isolated Worker -> Result -> Validation -> Completion -> Publication/Next Decision`
Not:
`Prompt -> AI -> directly edit whatever is available -> commit/push -> call it done`

---

# 2. Non-negotiable invariants

## 2.1 Context is not authority

Assistant packs, context packs, projections, indexes, raw chat and historical dialogue accelerate reconstruction and navigation.
They do **not** grant:

- execution authority;
- dispatch authority;
- roadmap mutation authority;
- release authority;
- commit/push/merge authority;
- foreign-repository write authority.

The worker must resolve authority from canonical governance surfaces.

## 2.2 Authority hierarchy

Current Blueprint authority precedence:
`Project Constitution -> Module Policy -> Execution Profile -> Work Front`
A lower layer may **narrow** authority.
A lower layer must never silently **widen** authority.
The AI actor must not be able to modify a guardrail, validate the same guardrail change itself, and thereby increase its own authority.

## 2.3 Work is bounded before execution

A task must have a bounded Work Front / equivalent execution contract carrying at minimum:

- objective;
- scope;
- exclusions;
- provenance;
- dependencies;
- outputs;
- acceptance criteria;
- stop conditions;
- authority;
- capability reuse evidence.

Raw user intent or chat is not a substitute.

## 2.4 Reuse before NEW

Before implementing new functionality, the worker must search existing:

- capabilities;
- scripts;
- libraries;
- services/APIs;
- module Knowledge Index / Knowledge Base where available;
- adjacent modules where reuse is plausible.

Disposition should be explicit:
`REUSE / EXTEND / ADAPT / REPLACE / NEW`
`NEW` requires evidence that reuse search was actually performed.
This rule becomes even more important after Module Knowledge Stabilization is deployed.

## 2.5 Provider/model neutrality

Worker identity and worker authority must not be tied to one model provider.
Provider/model is a runtime binding, not project authority.
The runtime must not:

- guess a provider;
- invent a model;
- hard-code provider credentials;
- store tokens/API keys/secrets in Git;
- widen authority because a stronger model/provider is selected.

Provider selection should be replaceable and preferably per attempt.

## 2.6 Isolated execution

A worker executes inside a sealed isolated workspace.
It must not use the canonical repository checkout as its working directory for untrusted mutation.
Before launch, the workspace must be:

- provisioned;
- bound to the intended source revision;
- fingerprinted/sealed;
- equivalent to the approved source state;
- not stale.

## 2.7 Explicit dispatch

A valid Assistant ACK is a gate, not dispatch authority.
The expected sequence is conceptually:
`validated task/context -> ACK -> ACK validation -> explicit dispatch decision -> process launch`
No worker launch before the explicit dispatch decision.

## 2.8 Durable attempt history

Execution Attempt history is append-only evidence.
If an attempt starts:

- the attempt becomes durable;
- stdout/stderr/exit/timing/timeout evidence is retained;
- failure is not erased;
- a retry uses a **new attempt_id**;
- a failed attempt is never rewritten into a successful one.

## 2.9 Launch is not acceptance

Raw process completion must not automatically:

- ACCEPT the work;
- close the Work Front;
- mutate roadmap completion;
- activate the next roadmap step;
- release;
- merge;
- push;
- publish.

Execution, result validation, acceptance, completion, publication and next activation are separate stages.

## 2.10 No silent foreign mutation

Cross-module workers may safely:

- OBSERVE;
- QUERY;
- PROPOSE;
- emit a candidate/report.

They must not silently mutate another module repository.
Cross-module mutation requires explicit authority and a governed path.

---

# 3. Target architectural layers

## Layer A — Planning / intent

Owns desired direction, roadmap, Human Intent, priorities, dependencies and target states. Does not directly execute code.

## Layer B — Work binding

Canonical bounded unit of work:

- Work Front;
- task identity;
- scope/exclusions;
- acceptance;
- dependency readiness;
- authority;
- reuse disposition.

## Layer C — Context compilation

Two concepts must remain separate.

### Project / onboarding context

Used so a fresh assistant understands the project/module.
Examples in Blueprint:

- Assistant Context Pack;
- project-entry archive;
- bootstrap navigation.

### Task execution context

Used for the exact executable task.
Examples:

- `build_context_bundle.py`;
- task-context compiler;
- task prompt;
- module policy;
- module indexes/knowledge;
- roadmap slice;
- previous completion evidence;
- acceptance oracle;
- dependency evidence.

Project onboarding must not masquerade as task authority.

## Layer D — Approval / gating

Validates:

- task identity;
- current authority;
- dependency readiness;
- execution profile;
- context freshness;
- procedure binding;
- workspace readiness;
- runtime/provider binding;
- Assistant ACK;
- explicit dispatch decision.

Fail closed.

## Layer E — Runtime binding

Resolves a provider-neutral worker identity to an executable runtime.
Responsibilities:

- provider registry;
- provider capability/readiness probe;
- per-attempt provider selection;
- executable argv;
- non-secret configuration;
- timeout/budget constraints.

Does not grant project authority.

## Layer F — Isolated workspace

Owns:

- immutable/frozen source baseline;
- isolated working tree;
- worker mutations;
- source/workspace fingerprint;
- worker delta extraction;
- attempt evidence.

## Layer G — Process launcher

Minimal provider-neutral process-launch primitive.
Responsibilities:

- receive already-resolved argv;
- exact cwd;
- environment allowlist;
- timeout;
- stdout/stderr capture;
- exit status;
- timestamps;
- launch evidence.

It should **not** discover secrets or decide business authority.

## Layer H — Result / evaluation

Responsibilities:

- result envelope;
- changed-path/delta evidence;
- validation evidence;
- worker explanation;
- unresolved blockers;
- completion candidate;
- independent verification.

## Layer I — Completion / publication

Separate governance boundary:

- work completed;
- accepted;
- published;
- committed;
- pushed;
- merged;
- released.

These states must not collapse into one boolean.

# 4. End-to-end intended flow

## Step 1 — Blueprint or authorized planner defines work

The planning layer identifies a roadmap/capability need.
Before creating a new implementation task:

- search existing capabilities;
- check module knowledge/index;
- check dependency ownership;
- determine `REUSE / EXTEND / ADAPT / REPLACE / NEW`.

## Step 2 — Create bounded Work Front / task

Bind:

- module;
- task;
- objective;
- scope;
- exclusions;
- dependencies;
- acceptance;
- stop conditions;
- authority ceiling;
- required procedure/profile.

## Step 3 — Module receives/pulls task

Accepted architectural intent from earlier discussions:

- Blueprint publishes the prompt/task in Blueprint-owned outgoing coordination;
- the target module's listener/intake mechanism pulls/synchronizes it into the module's local flow;
- Blueprint does **not** directly push implementation mutations into the target module repo;
- the module confirms pickup/acknowledgement through its own governed coordination surfaces.

This is central to portability.
Each module can own its local intake adapter while conforming to a shared contract.

## Step 4 — Resolve module-local authority

The module loads:

- Project Constitution / shared global rules;
- module policy;
- execution profile;
- Work Front;
- relevant standards/contracts.

The module must not invent a missing module policy.
Missing authority is a blocker or reconciliation task, not permission to infer.

## Step 5 — Compile fresh context

Fresh worker context should include, as relevant:

- immutable task/prompt;
- Work Front;
- authority hierarchy;
- module policy;
- execution profile;
- governed procedure;
- module Knowledge Index;
- module Knowledge Base / capability inventory;
- current roadmap slice;
- dependency readiness;
- previous completion evidence;
- current unresolved blockers;
- acceptance oracle;
- safe operator commands;
- relevant tests/validators;
- exact source revision/fingerprint.

Avoid uncontrolled historical bulk.
Old conversations/history may be referenced as optional provenance, not dumped into default execution context.

## Step 6 — Validate launch request

Before a process exists, validate:

- task-context archive;
- module identity;
- task identity;
- work-front binding;
- context freshness;
- dependency readiness;
- profile compatibility;
- procedure requirements;
- workspace feasibility.

No mutation merely because the launch request validates.

## Step 7 — Operator / governed approval

For authority-sensitive operations, retain explicit operator/human approval or equivalent governed approval gate.
The approval must be bound to:

- exact task/front;
- exact attempt;
- exact source/workspace;
- exact profile;
- allowed authority.

It should not be a vague "yes, proceed" detached from the artifact being executed.

## Step 8 — Provision isolated workspace

Create runtime tree conceptually equivalent to:
`runtime/<module>/<worker>/<attempt>/`
with:

- `workspace/repo`;
- evidence;
- invocation;
- result;
- stdout/stderr;
- fingerprints/manifests.

Workspace must be source-equivalent and sealed before dispatch.

## Step 9 — Resolve runtime/provider

Resolve an approved runtime binding.
Properties:

- provider-neutral worker identity;
- provider selected per attempt;
- executable already known;
- no provider guessing;
- no secret discovery inside launcher;
- no Git-stored secret;
- readiness probe returns READY/BLOCKED;
- BLOCKED leaves ACK/dispatch/attempt launch untouched.

## Step 10 — Assistant ACK

The worker/assistant acknowledges the exact manifest/package.
ACK should be:

- machine-readable;
- hash/binding-aware;
- exact-field validated;
- bound to attempt/task;
- unable to grant authority.

Invalid ACK => fail closed.

## Step 11 — Explicit dispatch decision

Only after all gates are green:

- create/record explicit dispatch decision;
- bind it to exact attempt;
- bind it to sealed workspace fingerprint;
- ensure authority remains within ceiling.

## Step 12 — One process launch

Launch exactly the intended worker process.
Launcher captures:

- command/argv identity;
- provider/runtime identity;
- cwd;
- start/end timestamps;
- stdout;
- stderr;
- exit status;
- timeout;
- launch failure details.

Append attempt fact when and only when process launch actually begins.

## Step 13 — Worker mutation in isolated workspace

The worker may mutate only allowed files inside the isolated workspace.
It must not:

- write canonical checkout directly;
- write another module;
- commit/push/merge/release unless a later explicit profile/authority permits it;
- silently modify guardrails;
- broaden its Work Front.

## Step 14 — Derive worker delta

After execution:

- derive exact changed path set;
- compare against allowed scope;
- reject foreign/unexpected path mutations;
- preserve source baseline and attempt evidence.

## Step 15 — Build result envelope

Result should carry enough deterministic evidence to evaluate without trusting free-form prose.
Suggested fields:

- task/front/attempt IDs;
- source fingerprint;
- workspace fingerprint;
- provider/runtime identity;
- execution profile;
- changed paths;
- tests/checks run;
- exit codes;
- worker summary;
- blockers;
- unresolved questions;
- claimed acceptance status;
- evidence locations.

## Step 16 — Independent validation

Validate:

- result schema;
- changed-path scope;
- tests;
- contracts;
- governance;
- acceptance criteria;
- no authority widening.

The worker's own claim that it succeeded is not sufficient.

## Step 17 — Completion candidate

If validated, produce completion evidence.
Do not equate this with publication.

## Step 18 — Publication / mutation of canonical repo

Publication is a separate governed pipeline.
Desirable properties already established elsewhere in Blueprint work:

- exact allowed path set;
- exact-byte/hash checks;
- fail closed on drift;
- commit separately from execution completion;
- normal push only;
- no force/rebase/reset as a shortcut.

## Step 19 — Roadmap/lifecycle reconciliation

After accepted/published work:

- append canonical lifecycle events;
- update derived projections;
- reconcile roadmap desired state vs actual execution state;
- no automatic next activation unless an explicit policy later permits it.

---

# 5. Context architecture — what the worker must know

A portable worker should not depend on a huge chat transcript.
It needs a deterministic context contract.

## 5.1 Minimum module orientation

- module identity;
- purpose;
- owner/authority;
- current architecture boundary;
- canonical entrypoints;
- capabilities;
- dependencies;
- important operator commands;
- current roadmap position.

## 5.2 Minimum task context

- exact task prompt;
- exact Work Front;
- execution profile;
- procedure;
- module policy;
- required inputs;
- expected outputs;
- acceptance criteria;
- stop conditions;
- dependency readiness;
- current source revision.

## 5.3 Knowledge/reuse context

As Stage 2 Module Knowledge Stabilization matures, include:

- Module Knowledge Index;
- capability IDs;
- implementation locations;
- tests/validators;
- Document Authority Registry;
- duplicate candidates;
- legacy candidates;
- cross-module reuse/migration candidates.

This is how the worker avoids recreating functionality already present in the module.

## 5.4 Historical context policy

Default execution context should not contain uncontrolled historical material.
Historical records are useful for:

- rationale;
- provenance;
- conflict reconciliation;
- architecture-generation analysis.

They are not default current instruction authority.

---

# 6. Execution Profiles

Execution Profiles are reusable policy bundles, not authority grants.
Known profile direction includes profiles such as:

- `deep-readonly-analysis@r1`
- `deep-dev@r1`
- `standard-dev@r1`
- `light-maintenance@r1`

A profile may define:

- reasoning depth;
- context budget;
- token/time budget;
- mutation class;
- allowed tools;
- network policy;
- validation tier;
- timeout;
- result requirements.

Profile authority remains capped by Constitution + Module Policy + Work Front.
A portable architecture should allow modules to reuse common profiles without copying Blueprint-specific task logic.

---

# 7. Provider/runtime portability

Current CF-10 direction already demonstrates the correct abstraction.

## Requirements

- worker identity is provider-neutral;
- provider selection is per attempt;
- provider registry grants no authority;
- provider credentials are not Git data;
- runtime probe is non-mutating;
- unresolved runtime binding blocks execution;
- launcher receives resolved argv;
- provider adapter and project governance remain separate.

Current/recent Blueprint evidence has included one ready provider and reserved not-configured providers. That is useful as proof of abstraction, but the architecture must not make any provider mandatory.

## Portability consequence

Other modules should bind to a **worker runtime contract**, not "Copilot logic", "Codex logic" or another vendor-specific workflow.
Vendor-specific integration belongs in runtime adapters.

---

# 8. Portable Module Worker Kit

Before rolling the assistant across modules, the reusable implementation should converge on a bounded kit.
It does **not** mean every module receives a copy of all Blueprint control-plane code.
The portable kit should expose contracts/reference implementations for:

## 8.1 Module task intake adapter

Responsibilities:

- discover released Blueprint task/prompt;
- validate target module;
- deduplicate;
- synchronize into local received/active/archive flow;
- acknowledge pickup;
- never treat chat text as formal task intake.

## 8.2 Module bootstrap adapter

Responsibilities:

- establish module root;
- load local policy;
- load module knowledge/index;
- load current status;
- provide safe startup navigation.

## 8.3 Task context compiler interface

Responsibilities:

- compile bounded context;
- prove freshness;
- include exact task authority;
- include prior completion evidence;
- include acceptance oracle;
- reject missing required context.

## 8.4 Work Front / task-envelope resolver

Responsibilities:

- resolve task IDs;
- scope;
- exclusions;
- dependencies;
- output contract;
- stop conditions;
- authority ceiling.

## 8.5 Execution Profile resolver

Reusable profile catalog with module-specific constraints.

## 8.6 Runtime adapter registry

Provider-neutral adapter registry.

## 8.7 Workspace provisioner

Reusable isolated-workspace behavior:

- clone/materialize source;
- freeze revision;
- seal/fingerprint;
- verify equivalence;
- preserve evidence.

## 8.8 ACK / dispatch adapter

Common machine-readable protocol.
Module-specific logic may constrain it further but must not weaken common gates.

## 8.9 Attempt ledger adapter

Append-only attempts with:

- unique attempt IDs;
- durable failed attempts;
- retry/new attempt relation;
- timestamps;
- process state;
- result binding.

## 8.10 Result/completion bridge

Maps worker result into:

- validation;
- completion packet;
- Inspector/review;
- Blueprint return channel.

## 8.11 Operator surface

Makefile or equivalent should expose supported operator actions.
ForPrint's current rule is that Makefile is an operator-facing functional map, not only a command launcher.

## 8.12 Focused validators/tests

Every portable component should ship with:

- contract validator;
- focused unit/contract tests;
- fail-closed negative tests;
- module adoption test.

# 9. Blueprint vs module responsibilities

## Blueprint should own / coordinate

- project constitution;
- cross-module governance;
- portfolio roadmap;
- task release/outgoing prompts;
- cross-module dependency model;
- common execution profiles/contracts;
- worker runtime/reference architecture;
- acceptance policies;
- portfolio-level reconciliation.

## Target module should own

- local task pickup/intake;
- local module policy;
- local Knowledge Index / Knowledge Base;
- local source tree;
- local tests;
- local implementation;
- local completion evidence;
- local module-specific runtime constraints.

## Shared/common layer should provide

- schemas/contracts;
- reusable runtime adapters;
- context compiler primitives;
- ACK/result protocol;
- attempt-ledger semantics;
- workspace semantics;
- operator/check conventions.

## Anti-pattern

Blueprint directly enters Library/Calculator/Telegram/Logistics repo and becomes the only process capable of running tasks there.
That would destroy portability and turn Blueprint into a central monolith.

---

# 10. Dependencies the worker must understand

The worker cannot treat dependencies as a flat "installed/not installed" list.
Dependency classes should include:

## 10.1 Governance dependency

Example: module policy required before mutation.

## 10.2 Capability dependency

Another module/service owns a required capability.

## 10.3 Data-contract dependency

Schema/API/object contract required.

## 10.4 Runtime dependency

Provider/runtime adapter or executable readiness.

## 10.5 Lifecycle dependency

A predecessor Work Front / roadmap step must be accepted.

## 10.6 Knowledge dependency

Required module index or current-state evidence is stale/missing.

## 10.7 External integration dependency

External API/provider unavailable or intentionally disabled.

### Safe degradation principle

A missing provider capability should not automatically stop unrelated consumer work.
Where explicitly authorized, use bounded compatibility stubs/fakes/contracts to continue safe local development.
But a stub must:

- be explicit;
- never pretend to be production truth;
- remain within the Work Front;
- not silently become a permanent second architecture.

---

# 11. Result, completion and publication separation

This separation is essential for autonomous work.

## Worker process result

Fact: process ran and produced output.

## Validated result

Fact: result passed schema/scope/technical checks.

## Work completed

Fact: acceptance criteria are satisfied.

## Accepted

Governance/human/authorized reviewer accepts the completion.

## Published

Changes are committed/pushed through a governed publication path.

## Released / merged

A later deployment/integration boundary.
A portable assistant should represent these as separate states.

---

# 12. Retry, failure and forensic behavior

## Failure must be first-class

A failed attempt stays durable.
Do not:

- delete it;
- overwrite it;
- "retry" by mutating the same attempt into success;
- hide a partial workspace.

## Retry

Retry creates a new attempt ID.
The new attempt should link to:

- prior attempt;
- failure reason;
- changed inputs/context;
- why retry is allowed.

## Resume

Resume must not replay already-performed irreversible actions.
Resume/freshness coordinates must be explicit.

## Timeout

Runtime launcher should:

- enforce bounded timeout;
- terminate safely;
- record timeout state;
- preserve partial evidence.

---

# 13. Security and secret boundaries

The assistant/runtime must not store in Git:

- API keys;
- provider tokens;
- passwords;
- credentials;
- raw secret environment dumps.

Provider runtime resolution should expose only safe readiness/config metadata.
Result/diagnostic artifacts should avoid leaking sensitive provider responses.
Secrets should be injected through approved environment/runtime mechanisms outside canonical repository history.

---

# 14. Observability

For every attempt, operators should be able to answer:

- what task ran?
- why was it allowed?
- which Work Front?
- which execution profile?
- which module policy?
- which provider/runtime?
- which source commit/fingerprint?
- which workspace?
- what changed?
- what tests ran?
- stdout/stderr?
- exit code?
- duration/timeout?
- result state?
- blocker?
- who/what approved dispatch?
- whether completion was accepted/published?

Observability should be machine-readable first, with compact human reports.

---

# 15. Operator interaction

The automatic assistant should reduce routine manual work, not remove human agency from authority-sensitive decisions.
Human/operator interaction should be concentrated at meaningful gates:

- resolve ambiguity;
- approve authority-sensitive execution;
- resolve conflicts;
- accept/reject results where policy requires;
- approve promotion to broader autonomy.

Avoid requiring the operator to manually reconstruct routine metadata.
Automation should update indexes, projections and routine coordination records where safe and deterministic.

---

# 16. Progressive autonomy

Autonomy should advance by **capability**, not one global switch.
Recovered target direction:

1. **Shadow**

   - observe/analyze;
   - no mutation.

2. **Copilot**

   - propose patches/work packages;
   - human/operator applies or explicitly authorizes.

3. **Bounded Operator**

   - mutate inside exact Work Front/profile/workspace;
   - independent validation;
   - no silent publication/foreign writes.

4. **Higher bounded autonomy**

   - only after measured stability across failures, rework, invalid results, authority violations and operator overrides.

A strong model does not justify a stronger authority profile.

---

# 17. First internal and external rollout logic

## Internal pilot

CF-10 is the Blueprint-internal zero-stage learning pilot.
Its purpose is to prove:

- runtime;
- context;
- ACK;
- dispatch;
- isolated workspace;
- attempt history;
- result/evaluation;
- worker delta;
- closeout behavior.

It is intentionally narrow and candidate-only/no-release.

## First external module pilot

Historical/current planning has repeatedly used **Logistics Service** as the first external-module pilot after Blueprint worker stability.
Reason:

- it already has strong coordination/governance structure;
- it has module-level tests;
- it has safe preview/synthetic boundaries;
- live provider writes can remain disabled;
- it is a useful proving ground for module-side pickup and worker portability.

This should be re-confirmed against current roadmap before activation.

## Portfolio rollout

After one external pilot proves the portable kit, other modules should adopt the common worker contracts incrementally.
Legacy/high-risk modules should not receive autonomous rollout until their Knowledge Index/document authority has been stabilized.

---

# 18. Relationship to Module Knowledge Stabilization

The newly established Stage 2 program is directly relevant.
A worker with limited context is safe only when the module can answer quickly:

- what capabilities already exist?
- where are they implemented?
- what documents are current authority?
- what is legacy?
- what duplicates exist?
- what belongs to another module?
- what roadmap item is already implemented?

Therefore the portable assistant should be designed to **consume** Module Knowledge Index / Knowledge Base rather than invent a parallel discovery database.
The worker should check knowledge before creating code.

---

# 19. Special warning for Calculator and Telegram Bot

These modules have multiple architecture generations.
The worker must not simply ingest every old document and infer a consensus.
Before meaningful autonomous implementation there:

- classify document authority;
- identify standalone-era instructions;
- identify old local database/integration ownership assumptions;
- detect duplicate implementations;
- detect functionality that should migrate to another module;
- constrain default context to current authority;
- expose historical material only as reconciliation evidence.

Otherwise a technically competent worker could faithfully implement an obsolete autonomous-module architecture.

---

# 20. Makefile / operator-map requirement

Supported worker/runtime functionality should be visible through the operator-facing command map where appropriate.
The Makefile should expose:

- checks;
- context compilation;
- launch request;
- approval;
- workspace/runtime readiness;
- result validation;
- status;
- closeout validation.

Avoid adding Make targets that pretend unsupported functionality exists.
When functionality changes, Makefile coverage should be part of closeout.

# 21. Suggested portable contracts

The following contracts should exist centrally or have an equivalent stable schema.

## ModuleWorkerIdentity

Fields:

- `worker_id`
- `module_id`
- `runtime_profile`
- `runtime_adapter`
- `capability_set`
- `authority_ceiling`

## WorkerTaskEnvelope

Fields:

- `task_id`
- `work_front_id`
- `module_id`
- `prompt_id`
- `procedure_id`
- `execution_profile`
- `dependency_readiness_ref`
- `context_archive_ref`
- `source_revision`
- `allowed_scope`

## RuntimeBinding

Fields:

- `provider_id`
- `adapter_id`
- `executable`
- `argv`
- `model`
- `non_secret_options`
- `readiness`
- `probe_evidence`

## WorkspaceBinding

Fields:

- `workspace_id`
- `module_id`
- `attempt_id`
- `source_revision`
- `source_fingerprint`
- `workspace_fingerprint`
- `state`
- `allowed_write_root`

## AssistantAck

Bound to exact task/package/attempt.
Must not carry authority expansion.

## DispatchDecision

Bound to:

- exact ACK;
- exact Work Front;
- exact attempt;
- exact runtime binding;
- exact workspace fingerprint.

## ExecutionAttempt

Append-only.

## WorkerResultEnvelope

Carries execution facts, delta, tests, blockers, result claim and evidence refs.

## CompletionPacket

Module-governed completion record.

---

# 22. Architecture decisions that must remain explicit

The implementation assistant should answer these questions with actual current files/tests, not assumptions.

1. Where is provider-neutral worker identity defined?
2. Where is runtime adapter registry defined?
3. How is provider selected per attempt?
4. How are secrets excluded from Git?
5. How is module policy resolved?
6. How is Work Front authority resolved?
7. How does context compiler distinguish onboarding vs task execution?
8. How is context freshness proven?
9. What exact fields bind Assistant ACK?
10. What creates the explicit dispatch decision?
11. What prevents ACK from dispatching by itself?
12. What seals the isolated workspace?
13. What proves source/workspace equivalence?
14. What exact paths can the worker mutate?
15. What prevents canonical-repo writes?
16. What prevents foreign-repo writes?
17. When is an Execution Attempt record appended?
18. What makes attempt history immutable?
19. How is retry assigned a new attempt ID?
20. How is timeout represented?
21. How is worker delta derived?
22. How is allowed-path scope validated?
23. What is the result envelope schema?
24. Who/what independently validates the result?
25. What separates WORK_COMPLETED from ACCEPTED?
26. What separates ACCEPTED from COMMITTED/PUSHED/MERGED/RELEASED?
27. What prevents auto-next activation?
28. How does the module return completion to Blueprint?
29. How will another module install/adopt this architecture?
30. Which pieces are common libraries/contracts vs Blueprint-only implementation?
31. Which module-local files must exist before bootstrap?
32. How does the worker query Module Knowledge Index?
33. What happens when required knowledge is stale/missing?
34. How does a missing dependency degrade safely?
35. What telemetry determines whether autonomy can be widened?

---

# 23. Portability acceptance matrix

The parallel implementation assistant should fill this table.

| AreaRequired state before external pilotCurrent implementation evidenceStatusGap / action |                                    |   |   |   |
| ----------------------------------------------------------------------------------------- | ---------------------------------- | - | - | - |
| Provider-neutral worker identity                                                          | required                           |   |   |   |
| Multi-provider runtime registry                                                           | required                           |   |   |   |
| Per-attempt provider binding                                                              | required                           |   |   |   |
| Secret-free Git contract                                                                  | required                           |   |   |   |
| Execution Profiles                                                                        | required                           |   |   |   |
| Work Front binding                                                                        | required                           |   |   |   |
| Capability reuse gate                                                                     | required                           |   |   |   |
| Project vs task context separation                                                        | required                           |   |   |   |
| Fresh task context                                                                        | required                           |   |   |   |
| Module Knowledge integration                                                              | required before broad rollout      |   |   |   |
| Launch request validation                                                                 | required                           |   |   |   |
| Operator/approval gate                                                                    | required where profile demands     |   |   |   |
| Assistant ACK                                                                             | required                           |   |   |   |
| Explicit dispatch decision                                                                | required                           |   |   |   |
| Isolated workspace                                                                        | required                           |   |   |   |
| Source/workspace fingerprint                                                              | required                           |   |   |   |
| Canonical-repo write isolation                                                            | required                           |   |   |   |
| Foreign-repo write prohibition                                                            | required                           |   |   |   |
| Provider-neutral launcher                                                                 | required                           |   |   |   |
| Timeout/stdout/stderr capture                                                             | required                           |   |   |   |
| Append-only attempt ledger                                                                | required                           |   |   |   |
| New attempt ID on retry                                                                   | required                           |   |   |   |
| Worker delta derivation                                                                   | required                           |   |   |   |
| Changed-path validation                                                                   | required                           |   |   |   |
| Result envelope                                                                           | required                           |   |   |   |
| Independent result validation                                                             | required                           |   |   |   |
| Completion exchange                                                                       | required                           |   |   |   |
| Publication separation                                                                    | required                           |   |   |   |
| Roadmap/lifecycle reconciliation                                                          | required                           |   |   |   |
| Auto-next activation disabled by default                                                  | required                           |   |   |   |
| Module task-pull/listener adapter                                                         | required for external pilot        |   |   |   |
| Module bootstrap adapter                                                                  | required for external pilot        |   |   |   |
| Portable adoption tests                                                                   | required for external pilot        |   |   |   |
| Makefile/operator visibility                                                              | required                           |   |   |   |
| Observability/reporting                                                                   | required                           |   |   |   |
| Progressive-autonomy metrics                                                              | required before authority widening |   |   |   |

---

# 24. Things that should NOT be solved by cloning code everywhere

Avoid copying Blueprint-specific machinery into every module without a contract boundary.
Prefer:

- common schema/contracts;
- reusable Python package or reference primitives where appropriate;
- module-specific adapters;
- module-local policy/config;
- module-local tests;
- shared conformance tests.

Do not create:

- one separate incompatible worker architecture per module;
- one separate attempt-history format per module;
- one separate context model per module;
- provider-specific execution logic mixed into governance code;
- hidden module-local authority rules that bypass Blueprint project policy.

---

# 25. Current/recent verified Blueprint evidence to reconcile against

The following surfaces have been observed in the recent Blueprint work and should be inspected by the implementation assistant.

## Governance / authority

- `coordination/standards/governance/project_constitution_v0_1.yaml`
- `coordination/standards/automation/work_front_contract_v0_1.yaml`
- module policies under `coordination/module_policy/`
- execution profile registry/standards
- roadmap execution reconciliation

## Context / bootstrap

- `coordination/bootstrap/START_HERE.md`
- `coordination/bootstrap/index_v0_1.yaml`
- `coordination/bootstrap/assistant_context_system_specs_v0_1.yaml`
- `scripts/coordination/build_project_context_archive.py`
- `scripts/coordination/build_context_bundle.py`
- task-context validators/tests

## Worker / invocation

- `scripts/coordination/build_worker_invocation.py`
- `scripts/coordination/control_plane/worker_runtime/`
- `scripts/coordination/control_plane/dispatch_intent.py`
- `coordination/internal_work/blueprint/governance/2026-09-06__blueprint__worker_runtime_and_invocation_contract_v0_1.yaml`

## Runtime portability contracts

Recently visible/current-candidate surfaces include:

- `coordination/standards/automation/control_plane/bootstrap_worker_runtime_profile_v0_1.yaml`
- `coordination/standards/automation/worker_runtime_adapter_registry_contract_v0_1.yaml`
- `coordination/standards/automation/worker_runtime_benchmark_contract_v0_1.yaml`
- `coordination/standards/automation/worker_task_envelope_contract_v0_1.yaml`
- `coordination/standards/automation/control_plane/module_bootstrap_execution_policy_v0_1.yaml`
- `coordination/standards/automation/control_plane/module_bootstrap_prompt_requirements_v0_1.yaml`
- `coordination/standards/automation/control_plane/bootstrap_task_context_mode_v0_1.yaml`

Some of these were recently part of active CF-10 worktree/runtime work and must be checked against the actual final published HEAD before being treated as canonical.

## ACK / handoff / attempts

- Assistant Handoff v2 contract/runtime
- CF-09 Assistant ACK validation gate
- `coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml`
- `scripts/coordination/execution_attempt_ledger_v0_1.py`

## CF-10 first-worker evidence

Recent first-worker Work Front required:

- provider-neutral process launch;
- already-resolved runtime argv;
- sealed isolated workspace;
- stdout/stderr/exit/timestamp/timeout evidence;
- runtime readiness probe;
- trusted expected ACK;
- explicit dispatch decision;
- canonical attempt ledger fact;
- result packet for later validation/completion intake.

That front also explicitly prohibited:

- bypassing ACK;
- treating ACK as dispatch authority;
- provider/model/credential guessing;
- Git secrets;
- canonical checkout writes;
- foreign repository writes;
- worker commit/push/merge/release/auto-ACCEPT;
- automatic lifecycle closeout;
- same-attempt retry;
- forensic evidence deletion.

---

# 26. Historical / accepted intent evidence that should not be lost

Recent dialogue enrichment recovered several durable design decisions.

## Module prompt-pull architecture

Blueprint publishes/release-coordinates module tasks from Blueprint-owned surfaces.
The target module listener/assistant pulls the task into the module's own coordination flow.
The module launches a fresh worker locally with sufficient context.
Completion/report returns into the coordination exchange.
Blueprint should not require direct ad-hoc write access to every module repo just to initiate work.

## Fresh-worker context

The worker context was repeatedly described as requiring:

- prompt;
- authority;
- module indexes;
- roadmap;
- previous completion evidence;
- acceptance oracle;

while avoiding uncontrolled historical noise.

## Machine-discoverable modules

Each module should become deterministically discoverable through explicit:

- purpose;
- ownership;
- capabilities;
- entrypoints;
- policy;
- dependencies;
- knowledge/index surfaces.

This is a prerequisite for reliable autonomous rollout.

## Cross-module workers

Cross-module workers may observe/query/propose but not silently foreign-mutate.

## Progressive autonomy

Autonomy is capability-specific and evidence-driven.
It should not be one global boolean.

---

# 27. Recommended reconciliation task for the parallel assistant

The parallel assistant should **not** implement new architecture merely because this brief lists a target.
It should perform:

## P0 — Current-state inventory

List all existing worker/control-plane/runtime/context files.

## P1 — Requirement mapping

For every requirement in Sections 2–23:

- point to current file(s);
- point to test(s);
- state implementation status;
- state missing behavior.

## P2 — Duplicate architecture check

Find overlapping:

- context compilers;
- runtime registries;
- task envelopes;
- workspace managers;
- attempt stores;
- result schemas;
- dispatcher paths.

Do not create duplicates.

## P3 — Portability split

Classify each current component:

- `BLUEPRINT_ONLY`
- `PORTABLE_COMMON`
- `MODULE_ADAPTER`
- `MODULE_POLICY`
- `PROVIDER_ADAPTER`
- `GENERATED_PROJECTION`
- `HISTORICAL_ONLY`

## P4 — External-pilot readiness gaps

Identify the minimum gap set that prevents deployment of the architecture into one external module.

## P5 — Produce bounded work fronts

Create separate work fronts for real gaps.
Do not use one giant "make everything autonomous" task.

---

# 28. Definition of ready for first external-module pilot

Do not declare the architecture portable merely because an internal Blueprint worker launched successfully.
`EXTERNAL_MODULE_PILOT_READY` should require at least:

- provider-neutral runtime proven;
- common worker task envelope proven;
- execution profile resolution proven;
- module policy resolution proven;
- module task-pull/intake contract defined;
- fresh task context compiled from target module;
- target module Knowledge Index/current-state navigation available;
- isolated workspace provisioned from target module;
- ACK/dispatch binding proven;
- append-only attempt ledger proven;
- result/completion exchange proven;
- no canonical/foreign writes outside explicit publication path;
- failure/retry proven;
- portable adoption test passes;
- operator can inspect the full attempt;
- no provider secrets in repo;
- publication remains separate;
- roadmap/lifecycle remains reconciled;
- human/operator can still stop/block the launch.

---

# 29. Definition of ready for broad multi-module rollout

Broad rollout should additionally require:

- at least one external pilot completed;
- module adoption contract documented;
- common package/reference implementation stable;
- provider/runtime conformance tests;
- module bootstrap conformance tests;
- knowledge-index integration;
- failure/retry evidence;
- invalid-result evidence;
- rework evidence;
- operator override evidence;
- measurable authority-violation prevention;
- cost/time/runaway controls;
- health/telemetry dashboard;
- versioned portable contracts;
- migration strategy for legacy modules.

---

# 30. Bottom-line architecture statement

The ForPrint automatic assistant should become a **portable governed worker substrate**, not a privileged central bot.
Its portability comes from stable contracts:

- task intake;
- authority;
- context;
- profile;
- runtime binding;
- isolated workspace;
- ACK;
- dispatch;
- attempt history;
- result;
- completion;
- publication.

Its intelligence may come from different AI providers.
Its authority does not.
Its context may change per module.
Its governance boundaries do not silently change.
Its implementation can evolve.
Its forensic execution history remains durable.
And before it creates something new, it must know what the module already has.

---

# 31. Repository placement and discoverability

Recommended canonical location:

`coordination/standards/automation/automatic_assistant_worker_strategic_concept_v0_1.md`

Recommended registration:

- add the document to `coordination/standards/automation/index.yaml`;
- use `status: strategic_reference`;
- use `adoption_mode: reference_only`;
- do **not** mark it as `active_standard`;
- let canonical knowledge/index generators discover it after source publication;
- do not hand-edit generated `indexes/*` or `machine/*` merely to force visibility.

Recommended index title:

`ForPrint Automatic Assistant / Governed Worker Strategic Concept v0.1`

This placement is intentional: the concept is automation-related and should be easily discoverable beside the executable automation standards, while its metadata makes clear that it is **not itself an execution standard or authority grant**.

A future materially different concept should be published as a new version and the automation index should identify the newest current strategic reference.

---

# Appendix A — Fast verification checklist

Use this as a short live review with the parallel assistant.

- [ ] worker is provider-neutral
- [ ] provider selected per attempt
- [ ] provider registry grants no authority
- [ ] no provider secrets in Git
- [ ] module task intake is pull/local, not Blueprint ad-hoc foreign write
- [ ] module policy is mandatory
- [ ] Work Front is mandatory
- [ ] reuse search is mandatory
- [ ] context pack is not authority
- [ ] project context and task context are distinct
- [ ] fresh task context contains previous completion evidence
- [ ] fresh task context contains acceptance oracle
- [ ] fresh task context contains module knowledge/index
- [ ] uncontrolled history is excluded by default
- [ ] launch request is validated
- [ ] operator/approval gate exists where required
- [ ] ACK is exact and machine-validatable
- [ ] ACK does not dispatch
- [ ] explicit dispatch decision exists
- [ ] workspace is isolated/sealed
- [ ] source/workspace fingerprint checked
- [ ] launcher uses resolved argv
- [ ] launcher does not discover secrets
- [ ] stdout/stderr/exit/timestamps/timeout captured
- [ ] attempt ledger is append-only
- [ ] failed attempt persists
- [ ] retry uses new attempt ID
- [ ] worker cannot write canonical repo directly
- [ ] worker cannot silently write foreign repo
- [ ] worker cannot auto-ACCEPT
- [ ] worker cannot auto-release/merge/push by default
- [ ] worker delta is derived
- [ ] changed-path scope is validated
- [ ] result envelope is typed/validated
- [ ] independent validation exists
- [ ] completion != publication
- [ ] publication != merge/release
- [ ] execution does not auto-close roadmap
- [ ] no auto-next activation by default
- [ ] completion returns through coordination exchange
- [ ] Makefile/operator map exposes supported functions
- [ ] one external module can adopt without copying Blueprint-specific internals
- [ ] portable conformance tests exist
- [ ] autonomy widening requires evidence, not model quality alone

---

# Appendix B — Evidence notes

This brief was synthesized from:

- recent Blueprint/CF-10 current-state terminal evidence;
- recent first-worker launch Work Front and validator output;
- current Blueprint Makefile/context-bootstrap inspection;
- recent dialogue-enrichment outputs from the 2026-09-05 through 2026-09-23 review/reconciliation work;
- previously accepted ForPrint governance architecture.

Important reconciliation note:
Some recent runtime/bootstrap files were still part of active CF-10 worktree state during the latest inspections. The implementation assistant must verify final publication state/HEAD before treating every listed path as canonical.
This document intentionally preserves architecture intent while refusing to promote historical discussion into execution authority.