# Knowledge Projection Strategy — Canonical Sources, Indexes, Graphs, C4

## Core decision

The current Blueprint index system remains valuable. Graphs do not replace indexes.

## Layer responsibilities

### Canonical sources

Examples:

- source code;
- policies/standards;
- contracts/schemas;
- roadmaps/planning records;
- execution events;
- domain-owned canonical records.

### Indexes

Purpose: fast lookup/navigation.

Typical questions:

- where is X?
- which files/documents mention/represent X?
- what roadmap/index entry exists?
- what are likely review candidates?

Indexes may evolve into richer concept/capability/policy/contract/symbol indexes.

### Graphs

Purpose: relationship reasoning.

Typical questions:

- how is X implemented?
- what depends on X?
- what governs/tests/consumes X?
- what is the blast radius?
- what is the path from capability to implementation/evidence?

### Human-readable views

Generated projections for understanding/review, including selected C4/UML/BPMN/WBS-style views.

## Multi-projection principle

Search indexes, relationship graphs, and human-readable architecture views are complementary projections of shared canonical sources, not competing replacement systems.

## C4 profile for ForPrint

Use only the useful subset:

- System Landscape for the whole ecosystem;
- System Context for important modules;
- selected Container views for complex modules;
- Dynamic views for important cross-component scenarios;
- selected Deployment views.

Do not require full manual C4 coverage or hand-maintained code-level diagrams.

Preferred direction:

```text
canonical graph/model -> generated C4 projection
```

C4 explains ForPrint; it does not control ForPrint.

## Selective UML

Potential future generated views:

- state machines for worker/publication/capability/order lifecycles;
- sequence diagrams for technical flows;
- selected structural/data-contract diagrams.

No full-project UML requirement.

## BPMN

Potential process projection for operational workflows/events/gateways/timers/handoffs, preferably generated from canonical process models rather than maintained as a separate runtime truth.

## WBS

Use the principle of hierarchical scope decomposition and scope completeness, while keeping scope hierarchy distinct from execution dependency ordering.
