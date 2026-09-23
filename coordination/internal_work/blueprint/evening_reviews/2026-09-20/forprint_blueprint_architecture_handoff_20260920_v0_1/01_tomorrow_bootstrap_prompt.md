# Tomorrow Bootstrap Prompt — Blueprint Integration

## Objective

Integrate the 2026-09-20 architecture handoff into `forprint_system_blueprint` without duplicating existing mechanisms and without prematurely implementing far-horizon ideas.

## First principle

**Audit before creation.**

Before designing or implementing any mechanism described in this package, inspect the repository for existing equivalents, partial equivalents, earlier names, policies, schemas, validators, tests, indexes, generated projections, execution-profile contracts, Inspector capabilities, Library capabilities, Dispatcher/continuity responsibilities, publication logic, and legacy `wave` semantics.

For every proposed capability, classify the result as:

`REUSE | EXTEND | ADAPT | REPLACE | NEW`

`NEW` is exceptional and must include search evidence plus rationale.

## First bounded work sequence

1. Inventory current mechanisms related to:
   - execution profiles / authority ceilings;
   - worker runtime / sandbox / handoff;
   - Dispatcher, continuity event/state models;
   - current Git commit/push/publication rules;
   - Project Inspector boundaries;
   - Library boundaries/catalog semantics;
   - existing indexes/graphs/dependency projections;
   - architecture/process visualizations;
   - `wave` terminology and semantics.
2. Produce a reuse/overlap matrix against this package.
3. Propose a canonical placement for each near-term capability.
4. Only after review, begin implementation one bounded capability at a time.

## Near-term capabilities to prepare for incremental realization

- Worker execution sandbox and capability enforcement around existing execution profiles.
- Reuse-first capability discovery / novelty gate.
- Implementation Knowledge & Traceability Graph.
- Publication Control Plane as an extraction-ready hosted Blueprint capability.
- Promotion Milestone / promotion-manifest publication lifecycle.
- Capability lifecycle/catalog/publication review model (Library is a candidate catalog host; audit first).
- Portfolio Planning / Dependency Intelligence / Convergence Engine as an extraction-ready Blueprint capability.
- Clear coexistence of indexes, graphs, generated views, and canonical sources.

## Far-horizon rule

Items in `11_far_horizon_methods_catalog.md` and `12_far_horizon_priorities.yaml` are references for future architecture. They must not be converted wholesale into implementation work.

## Worker execution discipline

- One bounded engineering step at a time.
- Preserve unrelated dirty worktree state.
- No `git add .`.
- No automatic commit/push/merge unless current canonical policy explicitly authorizes it.
- No activation of future work merely because it appears in this handoff.
- Use the formal Blueprint work intake/governance path; chat text alone is not formal execution authority.

## Required output of the first integration session

A repository-grounded reconciliation report with:

- existing implementation found;
- overlap/reuse classification;
- canonical owner/host candidate;
- gaps;
- conflicts/duplicates;
- recommended next bounded work item;
- no speculative large implementation.
