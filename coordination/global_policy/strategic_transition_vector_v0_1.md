# Strategic transition vector v0.1

Status: active temporary strategic direction.

This document is directional context only. It never overrides Project Constitution, roadmap/lifecycle authority, Work Front, profiles, procedures or operator decisions.

## Current vector

Until the first internal Blueprint worker is launched and proven usable, implement only the minimum CF-08 → CF-09 → CF-10 launch path unless a later item is a true blocker.

After the first internal worker becomes usable, bounded routine Blueprint self-hardening should increasingly be delegated to it. The global/chat assistant shifts toward deep audits of the remaining modules, verified current-state inventory, target/final functionality, complete roadmaps, provenance, cross-module dependencies, portfolio priority and wave planning.

Before broad module autonomy, build the portfolio model: priorities, dependencies, readiness, balancing/catch-up waves, forward-development waves and the first coordinated worker wave.

## Early worker learning

Early workers use observation-first retry policy: wider but bounded retry budgets, hard runaway ceilings, detailed telemetry, failure fingerprints, repair/restart evidence and durable resume coordinates. Tighten only after real statistics reveal which failures are worker problems and which are project/tooling friction.

## Existing functionality

Established functionality should progressively move behind registered capabilities/tools:

worker → describe/help → input validation → authority gate → governed procedure → mutation → affected validation → result envelope.

Do not pull this later self-hardening work in front of the first worker unless it is a real prerequisite.

## Sunset

Retire this temporary vector when the first coordinated multi-module worker wave actually starts. Preserve history. The governed-change and acceptance policy remains active beyond this milestone.

Machine-readable companion: `coordination/global_policy/strategic_transition_vector_v0_1.yaml`.

<!-- strategic-vector-persistent-epochs-2026-09-17 -->
## Persistent mechanism, finite strategic epochs

The Strategic Vector is a persistent coordination mechanism for the operator and the global coordinating assistant. It is not execution authority and never overrides the canonical roadmap.

This `v0.1` vector is one finite strategic epoch. Its current sunset trigger remains the first coordinated multi-module worker wave. Reaching that boundary retires or supersedes this epoch, **not** the Strategic Vector mechanism itself. A reviewed successor epoch is required when continued strategic guidance is needed.

Operator-facing use must preserve the difference between:
- roadmap — committed executable work;
- Strategic Vector — directional focus for the current strategic epoch;
- Architecture / Improvement Horizon — non-executable candidates for later reassessment;
- Review Obligations — subjects that must be revisited when a trigger becomes due.

<!-- forprint-project-wide-closed-loop-direction-v0-1:start -->
## Project-wide closed-loop execution direction

The closed-loop execution direction is **ForPrint-project-wide**. It applies to
current and future ForPrint modules; it is not a CF-10-specific policy. CF-10 is
the current proving ground where reusable governed execution primitives are
developed and validated, but it is not the exclusive or long-term owner.

The target progression is:

1. move stable recurring work from chat-driven/manual orchestration into
   repository-owned, tested and operator-visible CLI/Make/service entrypoints;

2. close each module loop so it can resolve live state and roadmap, select
   admissible work, prepare, cross explicit authority gates, execute, return a
   machine-readable result, validate, persist terminal evidence and derive the
   next admissible action;

3. continue automatically only while the next transition is already inside
   granted authority;

4. stop and escalate on blockers, failed validation, ambiguity, irreversible
   or high-authority boundaries, cross-repository mutation, promotion,
   acceptance or release decisions;

5. only after individual module loops are reliable, add a higher-level
   Dispatcher layer for cross-module queues, dependencies, priorities, workers
   and resources.

Before implementing a new solution, reconcile the nearest live implementation:

`REUSE → EXTEND → ADAPT → REPLACE → NEW`

`NEW` is last, not first. Existing code is evidence and reusable
implementation, not an untouchable artifact. Ownership, authority, contracts,
provenance and safety invariants are the canonical constraints.

The global/chat assistant remains important for strategy, architecture, review,
exceptional repair, new bounded implementation and human decisions. It should
not remain the permanent orchestrator for stable recurring execution.

This direction does not itself grant execution, dispatch, acceptance, roadmap
advancement, promotion, commit, push, merge, release or cross-repository
authority. Live roadmap/lifecycle state remains authoritative for the current
position.
<!-- forprint-project-wide-closed-loop-direction-v0-1:end -->
