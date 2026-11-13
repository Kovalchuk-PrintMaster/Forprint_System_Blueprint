# Publication Control Plane & Git Promotion Model

## Core separation

Treat these as different authority levels:

1. task workspace mutation;
2. local coherent commit/checkpoint;
3. push to isolated worker branch;
4. promotion candidate / PR;
5. canonical merge to protected `main`;
6. release/deployment promotion.

## Desired autonomy

Workers should eventually be able to:

- mutate only their scoped task workspace;
- create coherent local commits automatically after local gates;
- push to isolated worker branches after machine publication preflight;
- open/update promotion candidates.

Workers should not receive direct canonical-main mutation authority.

## Promotion Milestone

A promotion milestone is a functionally coherent acceptance boundary. It is separate from roadmap sequence/H-numbering and replaces the assumption that old static `wave` groupings must define publication.

Conceptual flow:

```text
worker branch activity
  -> milestone acceptance
  -> validations / review
  -> PROMOTION_READY
  -> Publication Controller
  -> serialized final checks / merge queue
  -> canonical main
```

## Dispatcher responsibility

Dispatcher owns execution coordination/facts and may publish that required work items/attempts are complete. It should not become the Git policy/merge implementation owner.

## Publication Control Plane

Initial placement: Blueprint-hosted, extraction-ready capability.

Owns:

- promotion-manifest validation;
- exact candidate SHA/fingerprint sealing;
- current-check verification;
- risk/policy/approval evaluation;
- provider adapter interaction;
- final promotion decision/execution under policy;
- immutable promotion-result events.

Does not own:

- strategic priority;
- work sequencing;
- execution completion truth;
- architecture business decision itself.

## Git provider adapter

Do not scatter direct GitHub-specific calls through core publication logic. Keep provider integration behind an adapter boundary so provider/runtime can evolve independently.

## Promotion risk

Exact risk classes must be reconciled with existing Blueprint policy. Conceptually, low-risk validated changes may eventually auto-promote; architecture/authority/security/production/breaking-contract changes require explicit operator review.

## Promotion Manifest

Minimum conceptual fields:

- promotion ID;
- module;
- milestone/accepted capability scope;
- candidate branch;
- exact HEAD SHA;
- included work IDs;
- validation evidence;
- unresolved blockers;
- risk class;
- operator-approval requirement/state;
- target branch;
- execution/completion evidence references.

## Protected main

Canonical `main` should be protected at the Git-provider layer so worker credentials cannot bypass policy through a simple direct push.

## Serialized promotion

Parallel branch development may exist, but canonical promotion should be serialized/revalidated against the current target branch. A merge queue or equivalent is the desired final enforcement pattern.

## State distinction

`WORK_COMPLETED` is not `MERGED`.

Track publication states separately from execution states.
