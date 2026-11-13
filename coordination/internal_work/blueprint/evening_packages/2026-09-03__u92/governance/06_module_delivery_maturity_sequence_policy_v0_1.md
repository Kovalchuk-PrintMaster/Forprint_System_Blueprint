# Canonical Module Delivery & Maturity Sequence Policy v0.1

Status: PROPOSED

## Purpose

Define the normal order in which a new or substantially rebuilt ForPrint module progresses from idea to production.

This is not a rigid waterfall. A module may loop backward when evidence changes, but it must not skip safety/readiness gates merely to move faster.

## Stage M0 — PORTFOLIO JUSTIFICATION

Required:
- unique role;
- reason the capability should exist as a separate module;
- ownership boundaries;
- current vs target state;
- dependencies;
- proof it does not merely duplicate an existing module.

Exit:
`MODULE_JUSTIFIED`

## Stage M1 — GOVERNANCE & ROADMAP

Required:
- module identity;
- roadmap with 8–10 actionable future steps;
- final target split into AGREED/HUMAN-CONFIRMED vs PROPOSED;
- data/contract/interface responsibilities;
- distribution/readiness state;
- module-local cleanliness obligation.

Exit:
`GOVERNED_NOT_IMPLEMENTED`

## Stage M2 — DEVELOPMENT BASELINE

Required:
- repository/current-state evidence;
- module development workspace;
- module-local venv/devstate policy;
- standard check command;
- tests/validators baseline;
- source/generator relationships;
- no production credentials.

Exit:
`DEVELOPMENT_READY`

## Stage M3 — CAPABILITY IMPLEMENTATION

Expected:
- deterministic logic first where appropriate;
- AI only where it adds value;
- contracts explicit before consumer integration;
- bounded tool interfaces;
- telemetry hooks;
- migration/backward-compatibility thinking from the start.

Exit:
`CAPABILITY_COMPLETE_IN_DEV`

## Stage M4 — VERIFICATION READINESS

Required:
- deterministic regression suite;
- contract tests;
- business invariants;
- synthetic fixtures;
- Verification Lab test surface;
- fake adapters for external side effects;
- test data isolation.

Exit:
`VERIFICATION_READY`

## Stage M5 — ADVERSARIAL / RESILIENCE VERIFICATION

As appropriate:
- malformed inputs;
- invalid combinations;
- multilingual behavior;
- authorization matrix;
- prompt/adversarial cases;
- concurrency;
- retry/idempotency;
- fault injection;
- recovery;
- performance/load;
- cost/context regressions.

Exit:
`VERIFIED_FOR_RELEASE_CANDIDATE`

## Stage M6 — RELEASE CANDIDATE

Required:
- versioned immutable artifact;
- pinned dependencies;
- checksum/provenance;
- explicit configuration;
- service identity;
- migration plan;
- rollback plan;
- runtime health checks;
- feature flags where useful.

Exit:
`RELEASE_CANDIDATE_READY`

## Stage M7 — STAGING / SHADOW / CANARY

Depending on module risk:
- staging;
- production-like replay;
- shadow traffic;
- canary users/traffic;
- metric comparison;
- error/cost/latency observation.

Exit:
`PRODUCTION_PROMOTION_READY`

## Stage M8 — PRODUCTION

Runtime must:
- run bounded artifact;
- have least privilege;
- not self-modify deployed source;
- preserve durable state;
- use execution-policy gate for significant side effects;
- provide runtime evidence.

Exit:
`PRODUCTION_ACTIVE`

## Stage M9 — MANAGED SELF-EVOLUTION

Runtime continuously produces:
- anomaly evidence;
- recurring AI patterns;
- automation candidates;
- cost hotspots;
- missing capability evidence;
- repeated user requests.

Development profile may autonomously implement low-risk candidates under policy. Every production change still follows Release Policy.

Exit:
continuous.

## Rule for future new assistants

Any future assistant/module receives this maturity policy together with:
- current module roadmap;
- module current-state evidence profile;
- cleanliness conformance requirement;
- autonomy matrix;
- development/runtime separation policy;
- applicable contract/IAM/verification policies.

A new module is not allowed to invent its own production-entry process.
