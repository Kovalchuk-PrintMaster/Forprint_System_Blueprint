# Verification Lab — Adversarial Testing Enrichment

Status: `PENDING_ROADMAP_ENRICHMENT`

Working module: `ForPrint Verification Lab`
Working capability: `Adversarial Test Orchestrator`

## Mission

Attempt to discover weaknesses in ForPrint using controlled valid and invalid interactions.

Test classes should eventually include:
- valid minimal/maximal combinations;
- incomplete required data;
- wrong semantic units;
- wrong primitive types;
- malformed payloads;
- unknown/deprecated IDs;
- invalid state transitions;
- oversized files/payloads;
- timeout/retry behavior;
- concurrency/queue pressure;
- ownership violations;
- accumulated-data and long-running scenarios.

Examples:
- liters where `pcs` are required;
- boolean/string where a number is expected;
- Calculator asked to create an order;
- Library asked to write stock truth.

## Core architecture principle

AI designs or extends tests when functionality changes.

Repeated execution should be deterministic:

`functional change -> AI-assisted diff/capability analysis -> new/updated scenario corpus -> deterministic repeated execution`

AI should not redesign the entire test set every night.

Useful scenarios become versioned, reproducible and attributable to the capability/change that caused them.

## Change-triggered enrichment

The Lab may inspect:
- Git diffs;
- changed public contracts;
- schema changes;
- new routes/commands;
- changed cross-module interactions;
- new product/configuration capabilities.

If a change is not functionally relevant, no AI test-generation work is needed.

## Cadence concept

Not final policy.

Possible model:
- nightly cheap targeted regression/fuzz;
- periodic heavy full-system sweep;
- no AI redesign during long change-free periods;
- deterministic corpus continues to run;
- periodic broader sweeps still test accumulated-data/resource failures.

## Isolation/resource governance

Heavy/adversarial tests should normally use:
- staging/test environment;
- controlled datasets;
- CPU/RAM/I/O/network budgets;
- bounded concurrency;
- kill/timeouts.

A window such as `00:00–06:00` is a planning candidate, not a final schedule.

## Outputs

The Lab emits evidence:
- failing scenario;
- reproduction data;
- affected module/capability;
- expected vs actual behavior;
- severity/confidence;
- probable owner;
- regression test artifact.

It should not silently patch production.

Long-term objective:

`AI-assisted discovery -> deterministic institutionalized test knowledge`.
