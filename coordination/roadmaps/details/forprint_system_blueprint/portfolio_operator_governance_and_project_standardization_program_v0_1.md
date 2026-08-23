# ForPrint Portfolio, Operator Governance & Project Standardization Program v0.1

Status: planning / non-executable / non-runtime.

Stable planning marker: `PORTFOLIO_OPERATOR_GOVERNANCE_PROJECT_STANDARDIZATION_V0_1`

This document records cross-cutting requirements that must survive assistant replacement and
context-window loss. It does not activate autonomous execution, automatic ACCEPT, daemon/runtime
coordination, SQLite, business prompt release, production mutation or module-repository writes.

Current runtime/release authority remains `coordination/releases/current.yaml`. Current execution
order remains in `continuity/prompt_sequence_v0_1.yaml`.

## 1. Canonical outcome-alignment principle

ForPrint coordination must evaluate significant agent work at two levels:

1. local correctness: did the prompt/milestone satisfy its bounded acceptance criteria?
2. system outcome alignment: did the work materially advance the whole ForPrint system toward the
   agreed successful project outcome?

Canonical question:

> Does the current agent work advance the whole system toward the agreed successful project outcome?

Locally correct work that does not improve the critical path, usable release, dependency state,
product capability or justified strategic objective is not automatically good portfolio progress.

This principle is intended to become visible in operator tooling and eventually in Make-first
governance entry points. The Makefile must not attempt to "understand" qualitative project truth;
deterministic commands should collect evidence and verify that required reviews exist.

## 2. Portfolio Progress, Dependency & Priority Dashboard

A first usable portfolio dashboard is a required operator capability, not optional decoration.

The operator-facing representation MUST be visual and color-coded from its first usable version.
Approximate progress is acceptable and expected during early calibration. Absence of a visual
progress/dependency view is not acceptable.

Color must never be the only semantic signal: labels/symbols such as BLOCKED, HIGH, READY, PLANNED,
HOLD and ACCELERATE must accompany color.

The portfolio must include all intended final participants, including modules that do not yet have a
repository. Such modules are represented explicitly as `planned` / `not_started`.

Minimum portfolio concepts:

- module mission / final function;
- current stage such as PLAN / EARLY / MID / LATE / PRODUCTION_READY;
- rough major-block progress;
- business/architecture priority;
- dependency/blocker state;
- modules that depend on this module;
- current acceleration/hold recommendation;
- recent accepted movement;
- confidence in approximate assessment.

### Raw progress vs effective readiness

Two distinct values are required:

- **raw implementation progress**: how far the module's own implementation has progressed;
- **effective readiness**: how usable the module is after accounting for required dependencies,
  blockers and missing integration conditions.

A module may be 100% locally implemented and still have low effective readiness.

### Required operator views

The eventual renderer should support at least:

- portfolio summary;
- module detail;
- dependency graph;
- `what blocks X?`;
- `what does X block / who suffers if X stalls?`;
- priority/acceleration view;
- progress/history view;
- critical-path view.

A high-priority module should be analyzable as a dependency cluster, so funding/effort can be directed
not only at the module itself but also at the few upstream modules that prevent it from becoming
useful.

### Historical snapshots

Portfolio assessments must be historically retained rather than overwritten. The system should be
able to answer why a module remained high priority, why funding changed, or why progress was revised.

Approximate values should carry a confidence level. If a module remains near the same estimated
progress after substantial cost/time, the result becomes an investigation signal:

- progress model may be wrong;
- milestone sizing may be wrong;
- prompts may be locally useful but globally weak;
- blockers may dominate;
- the module may genuinely be difficult.

Imperfect measurement is acceptable; invisible movement is not.

## 3. Early coherent vertical slice and system-level movement

ForPrint must not wait for every module to reach 100% before producing useful integrated releases.

Planning should favor the smallest coherent end-to-end product slice that validates real system
movement, even if some surrounding capabilities remain partial or manual.

Portfolio steering must therefore prefer:

- critical-path advancement;
- removal of shared blockers;
- first usable/integrated milestones;
- contract compatibility between modules;
- accepted integrated capability;

over locally impressive but globally non-moving code volume, commits or isolated completeness.

## 4. Outcome-alignment evidence packs and external qualitative review

The first implementation of system-level outcome review should remain deliberately simple.

Deterministic project tooling should generate a compact evidence pack; the qualitative interpretation
may be performed externally by the operator together with an AI assistant. Do not build a complex
embedded AI-analysis engine merely to automate this judgment early.

Target module-level evidence may include:

- manifest / module identity;
- mission and roadmap position;
- recent prompts and completions;
- acceptance history;
- major blockers and dependencies;
- recent changes;
- test/health summary;
- open questions;
- resource/budget summary where available.

Portfolio-level evidence should additionally summarize:

- module progress/readiness;
- priority and dependency graph;
- cross-module blockers;
- recent accepted movement;
- historical assessment deltas.

Evidence generation is deterministic. Qualitative judgment remains explicitly reviewable.

## 5. Historical outcome-alignment audit records

Outcome-alignment reviews must leave durable project records. They are not chat-only conclusions.

Target conceptual layout:

```text
coordination/assessments/outcome_alignment/
  <module_id>/
    <date>__<trigger>__v0_1.yaml
  portfolio/
    <date>__portfolio__<trigger>__v0_1.yaml
```

Exact paths/schema remain implementation decisions, but records should preserve at least:

- audit_id;
- module/portfolio identity;
- trigger and trigger reasons;
- related major roadmap step where applicable;
- evidence-pack identity/hash;
- alignment verdict;
- confidence;
- critical-path effect;
- resource-efficiency observation;
- new/resolved blockers;
- recommendation;
- whether the next major step is still valid;
- operator/reviewer decision;
- review timestamp.

History should be append-oriented. Corrections should be represented as new assessment evidence, not
silent rewriting of earlier judgment.

## 6. Outcome-audit triggers and milestone closure gate

Qualitative outcome audit is required by policy triggers, not by operator memory.

Initial trigger classes:

- time-based periodic review;
- major roadmap milestone closed;
- release/alpha/beta/production gate;
- abnormal progress or abnormal resource consumption;
- repeated RETURN / repeated verification failure;
- important dependency/blocker change;
- major scope/architecture/data-ownership change;
- explicit operator request.

Trigger policy may differ by module. High-impact modules may use tighter review intervals than simple
supporting modules.

Multiple related triggers may be deduplicated into one audit with multiple reasons when they refer to
the same work. A fresh periodic audit does not cancel a required major-milestone audit when a major
milestone closes immediately afterward.

### Major milestone governance invariant

A major roadmap milestone is not governance-complete merely because all of its substeps are accepted.

Required model:

```text
major step substeps complete
-> required outcome-alignment audit
-> audit record exists
-> major step governance-complete
```

This review asks whether the completed milestone was directionally correct, proportionate in cost,
architecturally useful and still aligned with the module/system final mission.

Future `make check` integration should verify the **existence and freshness of required audit
obligations**, not attempt to replace the qualitative audit itself.

## 7. Coordination Task Scheduler / recurring governance obligations

Important, infrequent governance work must live in the project rather than human memory.

A future canonical recurring-task registry should support both:

- **time triggers**: weekly/monthly/quarterly review obligations;
- **event triggers**: milestone closed, blocker changed, repeated failure, budget threshold,
  completion accumulation, release gate, etc.

The scheduler's responsibility is to create due work/attention, not to make governance decisions.

Conceptual flow:

```text
time/event trigger
-> audit/task obligation
-> evidence pack when applicable
-> operator attention
-> external/manual/AI-assisted review
-> durable assessment/decision
```

The scheduler must never silently ACCEPT/RETURN work, reorder strategic roadmap priorities, expand
budget or authorize production mutation.

Early implementation may be as simple as a deterministic command such as `make coordination-due`.
Daemon/systemd scheduling is a later separately authorized step.

## 8. AI Portfolio Budgeting, Priority Steering & Resource Governance

AI execution should operate under explicit policy rather than "everything not forbidden is allowed".

Future per-work policy should be able to describe independently:

- execution mode: manual / conditional / autonomous-allowed;
- acceptance mode: operator-required / bounded-auto where explicitly permitted;
- risk class;
- abstract model tier such as efficient / balanced / frontier;
- workload/reasoning effort;
- financial budget;
- token/tool/retry/wall-time guardrails;
- network/repository/commit/push/production/destructive permissions;
- operator gates for model upgrade, budget increase, high-risk start or acceptance.

Execution permission and acceptance permission remain independent.

Financial budget is the primary portfolio resource control; token/tool limits are technical
guardrails. No silent escalation to a more expensive model or larger budget.

### Budget Epoch / Funding Round

Portfolio funding may operate in explicit epochs/rounds, for example a fixed project budget distributed
across modules according to current priority.

Rebalancing should consider pragmatic factors rather than pretending to have a perfect scientific
formula:

- critical dependency impact;
- business/architecture priority;
- distance to a useful milestone/unblock;
- remaining complexity;
- recent accepted progress;
- burn efficiency;
- blocker/hold state.

Blocked/HOLD projects may receive zero execution budget while retaining a minimal health/revalidation
allowance if useful.

Historical funding snapshots should preserve allocation, reasons and later observed progress so the
operator can learn whether the steering model was effective.

The important metric is not cheapest tokens. It is cost per accepted, integrated project progress.

## 9. Remote / Mobile Operator Control Plane

The long-term operator model is:

```text
phone/browser = operator interface
Ubuntu/server = execution environment
controlled gateway = security boundary
Blueprint = policy authority
AI/API workers = bounded execution intelligence
```

Remote/mobile control must expose sanctioned project actions, not arbitrary unrestricted shell access
to AI.

Candidate controlled capabilities include:

- project/roadmap/status view;
- prepare reviewed transaction;
- review diff/evidence;
- run validation;
- dispatch prompt;
- answer clarification;
- ACCEPT/RETURN/HOLD where operator policy permits;
- pause/resume work;
- adjust approved budget;
- generate/retrieve evidence pack.

Telegram or similar transports remain policy-dumb notification/decision transports behind the
Operator Attention Gateway. They are not autonomous policy engines or general filesystem browsers.

A structured Operator Inbox may serve as an early fallback for mobile planning notes when exact
routing is not yet known. Unknown destinations must not be invented; routing happens later against
fresh project state.

## 10. Unified Project Skeleton & Command Contract

ForPrint modules may differ in capability, but must not differ unnecessarily in how an operator or
coordinator understands, navigates, bootstraps, validates and controls them.

Canonical invariant:

```text
same intent
-> same command
-> same class of result
```

Examples of intent classes that should converge on one canonical command contract include:

- project check;
- tests;
- health/status;
- bootstrap/install;
- validation;
- evidence/report generation.

The exact command set must be reviewed before standardization. The requirement is semantic
uniformity, not blindly preserving today's names.

### Common skeleton principle

A common project skeleton should define:

- required top-level coordination/navigation entry points;
- standard locations and semantics for scripts, tests, config, docs and coordination artifacts;
- rules for when thematic subdirectories are required;
- standard bootstrap/dependency files where the technology applies;
- standard config/environment conventions;
- standard report/result classes;
- module-specific extension points.

Not every module must contain every optional directory. If a capability exists, however, it should be
located and controlled according to the common contract.

Do not create empty architecture merely to look uniform.

### Legacy migration

New modules should follow the target standard first. Existing/legacy modules should be audited and
migrated progressively rather than mass-rewritten solely for cosmetic uniformity.

H10 ecosystem rollout and later legacy retirement are natural integration points for conformance,
but this planning document does not modify H10/H11 entry conditions or activate migration.

## 11. Framework principle: emerge from proven ForPrint patterns

The coordination system already has framework-like properties: lifecycle, Make-first entry points,
contracts, templates, validation and standard operator flows.

Do not build a framework merely to say that ForPrint has a framework.

Reusable coordination/framework capabilities should be extracted from repeated proven needs across
multiple modules. Preferred evolution:

```text
solve real ForPrint problem
-> repeat successfully in more than one module
-> identify stable pattern
-> standardize/golden-path it
-> later scaffold/automate it
```

Desired framework characteristics include:

- convention over configuration;
- golden path;
- stable lifecycle hooks;
- clear extension points;
- common contracts;
- standard Make/CLI operator surface;
- templates/scaffolding only after patterns prove stable;
- versioning/backward compatibility;
- observability/audit by default.

## 12. Mapping into the existing AUT program

These cross-cutting requirements extend existing AUT intent; they do not create a competing autonomous
roadmap or renumber AUT packages.

Primary mapping:

- portfolio map/dashboard: AUT-01 initiative layer + AUT-27 dashboard/audit;
- budget/model/resource policy: AUT-14 execution policy, AUT-19/20 attention, AUT-26 risk classes,
  AUT-27 audit/dashboard;
- remote/mobile operator control: AUT-20 transport/gateway + AUT-22 human-controlled coordinator;
- outcome-alignment milestone audits: AUT-17 milestone gates + AUT-19 attention + AUT-27 audit/replay;
- scheduler/event reminders: future deterministic coordination runtime around AUT-12/19, separately
  activated;
- unified skeleton/command contract: current ecosystem standardization/H10 compatibility work and
  later reusable tooling, without changing current B1->B2->Q->H10->H11 ordering.

## 13. Explicit non-goals of this planning record

This document does NOT:

- change `continuity/prompt_sequence_v0_1.yaml`;
- change `coordination/releases/current.yaml`;
- activate B2/Q/H10/H11/AUT;
- authorize SQLite coordination runtime;
- authorize a daemon/systemd worker;
- authorize autonomous execution;
- authorize automatic ACCEPT;
- authorize automatic push;
- release a business/module prompt;
- mutate any external module repository;
- define a Windows desktop application requirement;
- replace current roadmap or release authority.

## 14. Success condition for this program

The program succeeds when the operator and future assistants can answer, with low cognitive cost:

- where the whole ForPrint system is;
- which modules actually matter now;
- which modules/blockers prevent useful release;
- whether recent work materially advanced the system;
- where budget/attention should move next;
- which recurring audits/tasks are due;
- why earlier priority/budget decisions were made;
- how to operate any module through a familiar common skeleton/command surface.

The goal is not maximum automation. The goal is reliable, explainable movement toward a successful
integrated ForPrint product.
