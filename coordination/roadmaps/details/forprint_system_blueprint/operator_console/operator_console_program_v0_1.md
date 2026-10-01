# ForPrint Operator Console / Operator Control Plane Program v0.1

Status: **CURRENT PLANNING CONTEXT / NOT EXECUTION AUTHORITY**
Date: 2026-09-29
Owner intent: Human Owner + Blueprint planning
Current host: `forprint_system_blueprint` as an **incubator host**, not a permanent ownership decision.

## 1. Why this program exists

The Human Owner needs a centralized ForPrint control surface that can be used from a
phone or laptop to inspect modules, work interactively with an assistant, connect bounded
execution, exchange artifacts and receive status/attention signals without being physically
at the development terminal.

This capability is currently a **co-equal high-priority planning direction** with completion
of systematic module inventory / primary roadmap reconciliation.

This document does **not** decide which of those two directions receives the next execution
slot. After canonical reconciliation, the Human Owner decides whether to:

1. start the Minimum Working Console; or
2. finish the remaining module analysis first.

## 2. Architectural separation

Keep these concepts distinct:

- **Operator Console** — replaceable human-facing web/UI surface.
- **Operator Control Plane / Execution Fabric** — durable backend execution/session/module-
  ownership/artifact/interrupt/recovery infrastructure.

The Console may initially live in Blueprint for incubation, but its metadata and design must
preserve relocation to a more specialized future owner such as a dedicated control-plane,
system-administration or CRM/operator surface.

The Console must not become the authority for module ownership or worker state.

## 3. Core invariants

### 3.1 One writable actor per module

Canonical planning invariant:

`ONE MODULE REPOSITORY = ONE ACTIVE WRITABLE ACTOR`

Initial actor classes:

- `internal_worker`
- `operator_assistant`

Two writable actors do not work on the same module simultaneously.

### 3.2 Controlled ownership transfer

If the Operator Assistant needs a module held by an Internal Worker:

`interrupt request → safe bounded stop → durable checkpoint → seal/suspend → release → acquire`

The Operator Assistant must not steal an active module lease.

An Internal Worker may request access to a module occupied by the Human Owner / Operator
Assistant, but may not preempt that interactive session automatically.

### 3.3 Sandbox freedom, boundary scrutiny

Inside an isolated development sandbox, modern tools and dependencies are welcome when they
materially improve quality, speed, observability or reliability.

The stronger control boundary is crossed when an action would affect:

- canonical repository state;
- Git remote state;
- host/system packages outside the sandbox;
- production secrets;
- production databases/services;
- cross-module writes;
- external mutable systems.

Working phrase:

> **Trust the sandbox; scrutinize the boundary.**

### 3.4 Ambiguity escalation

When architecture, authority, ownership or policy is unclear:

`AMBIGUITY → BLUEPRINT / CONTROL AUTHORITY → HUMAN OWNER`

Do not invent permanent policy merely to keep a worker moving.

### 3.5 REUSE before NEW

Before implementing a Console, sandbox, execution, artifact, context, recovery or tooling
mechanism:

`REUSE → EXTEND → ADAPT → REPLACE → NEW`

Current CF10 worker/control-plane implementation must be inspected before a parallel mechanism
is created.

## 4. Step OC-01 — Minimum Working Console

Status: **PLANNED / NOT ACTIVATED**

Goal: create the smallest useful vertical slice that materially improves Human Owner mobility.

Required user-visible outcome:

1. one web surface lists registered ForPrint modules;
2. current module availability is visible (`FREE`, `INTERNAL_WORKER`,
   `OPERATOR_ASSISTANT`, transitional states);
3. a free module can be selected;
4. an Operator Assistant session can acquire exclusive module ownership;
5. an isolated operator workspace is created;
6. assistant + terminal/execution interaction is available;
7. files/artifacts can be exchanged;
8. the session can release the module cleanly.

Minimum backend expectations, preferably reused from CF10:

- module availability / ownership state;
- actor/session identity;
- exclusive module acquisition/release;
- isolated workspace creation;
- execution bridge;
- basic status projection.

Deliberately deferrable from the first vertical slice:

- full secrets broker;
- advanced network-policy engine;
- automated canonical integration gate;
- rich artifact registry UI;
- full Telegram approval workflow;
- complete automated recovery orchestration;
- all interrupt priority controls;
- advanced garbage collection.

### OC-01 acceptance boundary

The first slice is useful when:

- uncontrolled writes do not target the canonical repository;
- two actors cannot acquire the same module simultaneously;
- the Human Owner can perform a meaningful bounded remote review/development session;
- outputs can be reviewed/preserved;
- release leaves the module available for subsequent work.

OC-01 completion does not authorize automatic commit/push/release.

## 5. Step OC-02 — Advanced Operator Control Surface

Status: **FUTURE TARGET / NOT ACTIVATED**

Target capabilities:

### Module operations
- live module state;
- actor identity;
- current work/execution;
- access requests;
- controlled interrupt by priority;
- suspend/resume;
- release.

### Execution modes
Possible operator labels:
- `CHAT / REVIEW`
- `SUPERVISED DEV`
- `FULL DEV SANDBOX`

These are not intended as a tiny static shell allowlist. Safety should primarily come from
isolation, capability boundaries and controlled integration.

### Tooling
- strong sandbox development shell;
- dynamic tool installation;
- Environment Delta capture;
- Tool/Capability Registry visibility;
- Makefile operator-command discovery;
- local Git checkpoints without implicit remote push authority.

### Artifacts
- upload/download/exchange;
- session/module provenance;
- hash/size/type;
- generation recipe;
- retention class.

### Notifications
- completion;
- clarification/block;
- access request;
- approval request;
- interrupt completion;
- recovery/storage anomalies.

### Recovery
- heartbeat;
- durable checkpoints;
- unexpected interruption detection;
- resume or seal/abort from last durable state.

### Storage
- lifecycle states;
- age-based retention;
- storage-pressure thresholds with hysteresis;
- cleanup of disposable caches/tmp;
- active-workspace protection.

### Integration
- bounded Change Package;
- fresh integration worktree;
- tests/governance;
- human/Blueprint review;
- canonical commit/push outside unreviewed sandbox.

## 6. CF10 dependency contract

The Console program expects CF10 to reconcile/generalize existing internal-worker
infrastructure toward an actor-neutral execution contract.

Expected CF10 capabilities:

- actor-neutral execution fabric supporting `internal_worker`, `operator_assistant` and `human_terminal`;
- exclusive module ownership/lease;
- controlled interrupt/checkpoint/release;
- worker sandbox generalization;
- checkpoint/recovery;
- workspace lifecycle;
- artifact/status metadata;
- execution/tool capability projection.

If a dependency is not available when OC-01 reaches it:

1. mark `DEPENDENCY_NOT_READY`;
2. inspect current CF10 state;
3. choose explicitly between wait, bounded adapter/mock, or minimal temporary implementation;
4. do not silently create a competing permanent subsystem.


<!-- execution-control-plane-reconciliation-v0-1:start -->
### 6.1 Execution Control Plane reconciliation — 2026-09-30

The wider backend dependency is now specified by:

- `../execution_control_plane/execution_control_plane_program_v0_1.md`
- `../execution_control_plane/execution_control_plane_program_v0_1.yaml`
- `../execution_control_plane/cf10_worker_self_hardening_backlog_v0_1.yaml`

The backend execution model is intentionally shared by three actor types:

- `internal_worker`;
- `operator_assistant`;
- `human_terminal`.

`human_terminal` represents the current bounded operating mode in which an assistant prepares a
controlled command/script, the Human Owner executes it in the terminal, and structured evidence is
returned. This is an execution mode, not a separate project reality.

The Console remains a client of Control Plane projections. It must not infer module ownership,
mini-step completion or execution state independently from repository dirtiness or UI-local flags.

The near-term CF-10 backend contour is deliberately smaller than the full Console horizon:
execution record/source/actor, exclusive module lease, heartbeat/liveness, current step/mini-step,
minimal semantic events, checkpoint reference, status projection and
suspend/resume/complete/release. Later Console features consume that foundation as they are
deliberately promoted.
<!-- execution-control-plane-reconciliation-v0-1:end -->
## 7. Tooling evolution

Sandbox experimentation is encouraged.

Material additions should be captured as an **Environment Delta**, for example:

- system tools;
- Python packages;
- Node packages;
- browser/tooling components;
- reason for use.

Repeatedly useful additions should become candidates for promotion into:

- global developer profile;
- module development profile;
- bootstrap capability pack;
- Tool/Capability Registry.

The project should progressively expose existing tools and Makefile workflows so a fresh
assistant/worker does not rediscover the environment from zero.

## 8. Recovery and retention direction

Abrupt power loss is a real ForPrint operating condition.

Execution should preserve durable checkpoints sufficient to resume without rebuilding the
entire task context.

Retention should consider both age and storage pressure.

Important rule:

> An active workspace is never silently deleted merely because it is old.

A very old active execution is an anomaly requiring operator review.

Example thresholds discussed by the Human Owner (`~100 GB`, `~6 months`) remain **design
inputs, not canonical hard-coded values** until implementation policy is reconciled.

## 9. Artifact provenance

Artifact binary payloads may be temporary.

Durable metadata should preserve enough to reconstruct:

- producer/execution;
- module;
- base HEAD;
- source inputs;
- generator/recipe;
- filename/type/hash;
- retention class.

Planning principle:

> **Artifact payload may expire; artifact provenance should persist.**

## 10. Human rationale excerpts

Compressed owner rationale preserved for future roadmap readers:

> “The console is temporarily as important as finishing module analysis because it lets me
> move the whole project even when I am not at the computer.”

> “I do not want assistants to avoid modern tools just because they are not installed; that
> already cost us a lot of time with repository search and website visual work.”

> “If one worker already has a module, the other waits. If I need it urgently, we use the
> normal interrupt mechanism, checkpoint the work and only then hand the module over.”

> “The first implementation must be detailed enough that a new assistant can continue it,
> but it must not become a rigid cage: if a better tool or implementation is discovered,
> bring it up and improve the plan.”

These excerpts preserve planning rationale; they do not grant execution authority.

## 11. Implementation flexibility

This document defines a strong baseline, not a command to mechanically reproduce an
outdated design.

During implementation:

1. inspect existing ForPrint capability first;
2. apply `REUSE → EXTEND → ADAPT → REPLACE → NEW`;
3. surface compatible tools/libraries/patterns that materially improve quality, safety,
   maintainability or speed;
4. integrate better solutions when they preserve Human Owner intent and authority boundaries;
5. do not silently change ownership, authority or safety invariants;
6. escalate policy/ownership ambiguity before committing to a permanent design.

## 12. Immediate decision gate

After this planning package is integrated and CF10 live state is reconciled, the Human Owner
chooses:

- **A — start OC-01 Minimum Working Console**, or
- **B — finish remaining module inventory first, then start OC-01**.

No automatic activation follows from this document.

<!-- oc01-two-contour-delivery-2026-10-01:start -->
## OC-01 delivery refinement — MINI and FULL

`OC-01` remains one compact roadmap step. Delivery is split into two progressive contours:

- **OC-01-MINI — Minimum Operational Console**: already includes both core modes —
  governed Protected Terminal and isolated Assistant Dev Sandbox — plus checkpoint/seal and
  controlled Sandbox → Canonical promotion. MINI is a working vertical slice, not a mock UI.
- **OC-01-FULL — Full Operator Console v1**: extends the proven MINI with richer terminal
  profiles, durable/resumable sandboxes, hardened promotion/recovery/audit, full three-actor
  handoff and a mature phone/laptop operator surface.

The ordered implementation procedure lives in:

`coordination/self_coordination/prompt_queue/draft/2026-10-01__forprint_system_blueprint__oc01_mini_full_operator_console_implementation_v0_1.md`

This refinement does not activate execution. Activation remains a separate explicit Human
Owner decision.
<!-- oc01-two-contour-delivery-2026-10-01:end -->
