# ADR 0014 — Manual Repository Knowledge and Direction Snapshots

- Status: Accepted
- Date: 2026-07-23
- Owner: ForPrint System Blueprint

## Context

The growing ForPrint ecosystem risks forgotten implementations, duplicate code,
unexplained files, stale coordination records and loss of decision rationale.
Project Inspector is planned but is not ready for active automation.

Building a service, database or dashboard now would distract from the current
critical path.

## Decision

Adopt three manual, dated, immutable YAML snapshot types:

1. Repository Capability Inventory — RCI.
2. Repository Execution & Dependency Map — REDM.
3. State, Direction & Rationale Snapshot — SDRS.

Blueprint keeps two SDRS streams:

```text
blueprint_coordination
system_portfolio
```

A module keeps one:

```text
module_self_view
```

## Authority

Snapshots are historical evidence. They do not override policy, directives,
module boundaries, approved prompts or canonical machine architecture.

Unknowns remain visible. Lack of references is not proof of dead code.

## Consequences

Benefits:

- technical and strategic memory;
- evidence for duplication/dormancy review;
- historical direction and rationale analysis;
- structured input for future Project Inspector.

Costs:

- manual preparation;
- incomplete first classifications;
- existing metadata conflicts become visible.

## Rejected or deferred

- Database/dashboard now — rejected.
- Project Inspector automation now — deferred.
- Automatic dead-code deletion — rejected.

## Recovery

Before commit, remove only newly installed baseline files and restore the
document source registry.

After commit, use `git revert`; do not rewrite historical snapshots.
