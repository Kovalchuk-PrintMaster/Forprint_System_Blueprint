# 2026-09-20 Architecture Summary

## 1. Worker philosophy

The desired ForPrint worker model is:

> **A worker may reason beyond its execution scope, but may never act beyond its execution scope.**

Workers should receive broad strategic/module context so they do not operate as black boxes. They may query other modules, discover planned/implemented capabilities, submit cross-module proposals, and surface risks. However, filesystem/network/secrets/Git/production authority must be physically constrained by runtime capabilities and work leases rather than relying on prompt memory.

## 2. Execution profiles remain foundational

Do not invent a new profile system. Existing Blueprint execution-profile mechanisms must be audited first. The expected direction is to extend them so that:

- profile permissions define a **ceiling**, not an unconditional grant;
- effective authority is an intersection of project policy, module policy, execution profile, and current work lease;
- younger/less-trusted workers can receive stricter profiles;
- mature workers/tasks can receive larger resource budgets or wider scoped capabilities only through explicit escalation/policy;
- sandbox enforcement is runtime/OS-backed, not merely textual instruction.

## 3. Defense in depth for workers

Critical rules must not depend on context-window retention. Desired layers include:

- bootstrap instruction;
- structured work schema;
- policy decision point;
- capability/action broker;
- filesystem/network/secret isolation;
- mutation-scope checks;
- lifecycle gates;
- post-execution validation;
- immutable/auditable events.

A worker forgetting an instruction must not remove the guardrail.

## 4. Reuse-first development

No architectural capability should enter source-mutation implementation state until existing/adjacent implementations were searched and one disposition was recorded:

`REUSE | EXTEND | ADAPT | REPLACE | NEW`

`NEW` requires evidence and rationale. Old implementations should not be casually deleted; use lifecycle states such as `ACTIVE`, `DEPRECATED`, `SUPERSEDED`, `ARCHIVED`, with explicit reuse-safety classification.

## 5. Implementation knowledge / traceability

ForPrint needs a queryable implementation knowledge layer that can answer, in one or two commands:

- what implements concept X;
- which scripts/functions/contracts/policies/tests participate;
- what depends on it;
- what would be affected by a change;
- whether parallel/duplicate implementations exist;
- which documents semantically govern the same process;
- what small, coherent evidence bundle should be exported for deep review.

This is not just file dependency analysis. It is a typed implementation/traceability graph.

## 6. Knowledge projections

Indexes are not being replaced. Desired model:

- canonical sources remain code/docs/contracts/events/domain records;
- indexes provide fast lookup/navigation;
- graphs provide relationship reasoning and impact analysis;
- C4/UML/BPMN/WBS-style views are human-readable/generated projections;
- analytics/simulation consume the normalized model.

## 7. Publication / Git model

Separate:

- local/task-worktree mutation;
- local commit/checkpoint;
- push to isolated worker branch;
- promotion candidate / PR;
- canonical merge to protected `main`.

Workers may eventually autonomously commit and push to isolated worker branches after machine gates. They must not directly mutate canonical `main`.

A **Publication Control Plane** should be hosted initially inside Blueprint, extraction-ready, with its own contracts/state/API/provider adapter. Dispatcher provides execution completion facts; Publication Controller decides/executes canonical Git promotion according to policy.

## 8. Promotion Milestones

Retire the assumption that old static `wave` semantics should define publication. Use a separate concept:

**Promotion Milestone / Acceptance Boundary**

A functionally coherent block is accepted, validated, sealed, and then becomes eligible for canonical promotion. Promotion milestones are not required to match roadmap H-number groupings.

## 9. Capability publication / adoption

A shared capability/revision should be published through a manifest/event model. Relevant consumers must review the publication but are not forced to upgrade immediately.

Typical consumer decisions:

- `ADOPT_NOW`
- `ADOPT_PLANNED`
- `STAY_PINNED`
- `NOT_APPLICABLE`
- `BLOCKED_BY_COMPATIBILITY`
- `REQUIRES_ARCHITECTURE_REVIEW`

Inspector should verify acknowledgement/reconciliation, not force universal latest-version adoption.

## 10. Portfolio Planning Engine

A future Blueprint-hosted, extraction-ready capability should centralize portfolio dependency intelligence, convergence, scenarios, priorities, constraints, resource conflicts, risk, and planning projections.

The present phase remains **coverage first, ordering later**: enrich known capability space before pretending the global sequence is exact.

## 11. Multiple workers per module

Potentially useful but deliberately far horizon. Early project stage has high architecture volatility and grey zones; default should remain one primary mutation worker, optionally supported by read-only/review/test workers. Multi-mutation parallelism should be enabled only after explicit parallelization assessment and mature coordination tooling.

## 12. External methods

C4, Jira, MS Project, EVM, CPM, CCPM, Lean/Last Planner, Monte Carlo, PERT, sensitivity analysis, System Dynamics, UML, BPMN, WBS, Google Issue Tracker/Critique/OKR/Design Sprint were reviewed as **sources of selective mechanisms**, not frameworks to copy wholesale. Their extracted ideas are listed separately in the far-horizon catalog.
