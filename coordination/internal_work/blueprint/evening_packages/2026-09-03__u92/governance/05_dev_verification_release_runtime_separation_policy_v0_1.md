# Development → Verification → Release → Runtime Separation Policy v0.1

Status: PROPOSED

## Purpose

Allow ForPrint modules to remain powerful developers of their own capabilities without allowing live runtime agents to modify production arbitrarily.

## Mandatory separation

A mature module has four distinct planes/profiles:

1. DEVELOPMENT
2. VERIFICATION
3. RELEASE
4. RUNTIME

They may live on the same physical server initially, but they must not share equivalent authority.

## DEVELOPMENT

Goal: maximize engineering productivity.

Expected capabilities:
- broad module-local shell;
- source mutation;
- dependency experimentation;
- test generation;
- package install inside module-owned environment;
- build generation;
- synthetic data.

Boundary:
- module-local or explicitly granted shared development surfaces;
- no production write authority by default.

## VERIFICATION

Goal: prove expected behavior and intentionally seek failures.

Expected capabilities:
- isolated synthetic data;
- fake external providers;
- adversarial and combinatorial scenarios;
- fault/concurrency/recovery testing;
- trace capture;
- no live external side effects by default.

## RELEASE

Goal: reproducibly convert reviewed source into a known artifact and safely promote it.

Release controller is deterministic.

Required evidence:
- source revision;
- dependency lock;
- build metadata;
- checksum;
- targeted tests;
- required verification campaigns;
- migration compatibility;
- policy approval state;
- rollback target.

## RUNTIME

Goal: serve real work reliably.

Runtime:
- runs immutable deployed artifact;
- uses capability-shaped tools/APIs;
- receives least privilege;
- cannot self-edit deployed code;
- cannot install arbitrary dependencies;
- cannot bypass IAM/execution policy;
- may generate improvement candidates and runtime evidence.

## Improvement loop

`observe → candidate → dev → verify → release → canary/shadow → adopt/rollback`

Production self-improvement means initiating and proving changes, not editing live code in place.

## Shadow and canary

Mature releases should support:
- shadow/mirrored evaluation where output does not affect users;
- canary exposure to bounded production traffic where practical;
- feature flags for controlled activation;
- automated health comparison;
- rollback.

## Durable state

Code deployment must not silently discard:
- DB state;
- queues;
- pending operations;
- caches that carry business state;
- outbox/inbox events;
- unfinished workflows.

State compatibility must be explicit.

## Human approval

Do not ask humans to approve every low-risk development file action.

Human approval is reserved for policy-defined significant actions, especially:
- destructive production mutation;
- irreversible migration;
- money/external side effects;
- broad credential changes;
- cross-module ownership/contract changes;
- release-policy exceptions.

## Relationship to existing ForPrint governance

This policy complements:
- Safe Mutation Pipeline;
- Asset Lifecycle & Retirement;
- Module Cleanliness Conformance;
- AI Execution Safety;
- Contract Registry;
- IAM;
- Runtime Inspector;
- Project Inspector.

It does not replace them.
