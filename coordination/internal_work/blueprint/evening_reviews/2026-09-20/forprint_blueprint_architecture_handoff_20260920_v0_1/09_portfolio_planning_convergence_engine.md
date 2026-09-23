# Portfolio Planning, Dependency Intelligence & Convergence Engine

## Placement

Initial form: extraction-ready hosted capability inside `forprint_system_blueprint`.

Do not immediately create a standalone module.

## Current planning phase

**Portfolio Knowledge Saturation Phase**

Principle:

> Expand knowledge, not perfect order.

Current roadmaps remain useful knowledge-accumulation surfaces even when H-order is approximate. Important capabilities, gaps, ownership hypotheses, dependencies, and maturity should be captured before attempting exact global sequencing.

## Desired model

Central normalized portfolio model / graph may contain:

- module;
- capability;
- roadmap step;
- work item;
- milestone;
- artifact;
- policy;
- decision;
- resource pool;
- risk;
- external dependency.

Candidate relations:

- requires;
- blocks;
- enables;
- produces;
- consumes;
- invalidates;
- derived_from;
- supersedes;
- conflicts_with;
- competes_for_resource;
- gated_by;
- implements;
- evidence_for.

## Desired analysis

Near/mid-term foundations:

- dependency integrity;
- cycles/SCC;
- topological generations;
- blast radius;
- bottleneck/bridge analysis;
- current execution frontier;
- desired-vs-actual reconciliation;
- plan revisions;
- event-watermark freshness;
- structured reports;
- scenario dry-runs;
- transaction/change-set application.

Later analysis:

- critical path/float;
- resource-constrained critical chain;
- capacity/leveling;
- baselines and variance;
- uncertainty/buffers;
- Monte Carlo;
- sensitivity;
- system dynamics.

## Planning vs execution authority

- Planner owns desired planning state.
- Continuity/Event Store owns factual execution history.
- Dispatcher controls execution leases/state transitions.
- Reconciler compares desired vs actual.
- Planner must not invent execution facts.
- Dispatcher must not invent strategic work.

## Worker context

Workers should receive broad module strategic context, relevant cross-module dependencies, current plan revision, open gaps, and near-horizon expectations. Seeing the roadmap does not grant execution authority.

## Dynamic execution concepts

Preferred vocabulary replacing static-wave assumptions:

- `Strategic Horizon`
- `Near-Horizon Candidate Chain`
- `Execution Frontier`
- `Execution Lease`
- `Plan Revision`
- `Planning Control Signal`
- `Promotion Milestone` (publication boundary, separate concern)

## Planning interrupts

Future workers should receive revision-bound context and acknowledge relevant control signals. Not every roadmap change should pause execution; severity/policy determines action.

## Multiple workers

Far horizon by default. The optimization target is net canonical throughput after coordination/integration/rework costs, not worker count.
