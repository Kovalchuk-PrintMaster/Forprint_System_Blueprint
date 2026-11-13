# Reuse-First Capability Discovery & Novelty Gate

## Problem

A worker may forget or lose a prompt instruction that says “check whether this already exists” and accidentally create a parallel framework. This must be prevented by workflow/state enforcement, not memory alone.

## Canonical decision vocabulary

Every architectural capability introduction/change should resolve to one of:

- `REUSE` — existing capability already satisfies the need;
- `EXTEND` — correct foundation exists; add behavior;
- `ADAPT` — existing mechanism is useful but needs contextual adaptation;
- `REPLACE` — conceptually same responsibility exists but is no longer fit;
- `NEW` — no viable existing/adjacent foundation exists.

## Reuse Assessment

A structured assessment should capture:

- requested capability/concept;
- search surfaces used;
- exact and adjacent candidates;
- implementation/policy/contract/roadmap matches;
- selected disposition;
- selected base implementation when relevant;
- rationale;
- confidence/provenance;
- explicit candidate rejection reasons for `NEW`/`REPLACE`.

## Lifecycle gate

Conceptual state flow:

```text
DISCOVERY_REQUIRED
  -> DISCOVERY_COMPLETE
  -> REUSE_ASSESSMENT_RECORDED
  -> REUSE_GATE_PASS
  -> IMPLEMENTATION_READY
```

If the gate is required but absent, mutation authority for the architectural capability should be denied.

## Scope of the gate

Mandatory candidates:

- new capability;
- new process/subsystem;
- new persistent model;
- new cross-module contract;
- new public API;
- new runtime mechanism/framework;
- new policy mechanism.

Do not require heavyweight architectural assessment for trivial local helper functions.

## Replacement / deprecation

Before `REPLACE`, inspect:

- active consumers;
- incoming references;
- runtime use;
- compatibility commitments;
- policies/tests referring to old behavior;
- migration requirements.

Possible lifecycle outcomes:

- `KEEP`
- `DEPRECATE`
- `SUPERSEDE`
- `MIGRATE`
- `RETIRE`

## Periodic detection

Future checks may identify:

- high semantic overlap / parallel framework candidates;
- duplicate capability ownership;
- excessive `NEW` disposition rate;
- superseded implementations still actively consumed;
- obsolete catalog entries.

## Non-negotiable principle

The requirement must be enforced by work lifecycle/control plane and must not depend solely on assistant prompt memory.
