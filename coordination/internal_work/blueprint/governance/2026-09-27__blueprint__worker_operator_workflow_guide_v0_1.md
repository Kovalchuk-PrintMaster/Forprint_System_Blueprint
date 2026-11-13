# CF-10 Worker Operator Workflow Guide v0.1

Status: **EVOLVING / operator-authorized draft for controlled adoption**

This guide explains how a human operator and a fresh assistant should think about
the current ForPrint Worker workflow. It is intentionally short. It is **not** an
immutable implementation contract and must not be used to force future project
architecture around today's scripts.

## 1. The stable idea

The stable architecture is the governed execution chain, not a particular Python
entrypoint:

`Task / Work Front → governed context → isolated workspace → source freeze →
ACK where required → explicit dispatch → Worker runtime → immutable attempt
evidence → delta verification → validation → human/operator visibility →
acceptance/promotion boundary`

Those boundaries should remain explicit even when the implementation is refactored.

## 2. Human-observable Worker operation

Worker work must not become invisible simply because execution becomes more
automatic.

At minimum, every meaningful attempt should expose an operator receipt containing:

- Worker/provider;
- task and attempt;
- start/finish/current state;
- duration;
- process outcome;
- validation outcome;
- changed paths or produced outputs;
- accepted/promoted state;
- next required boundary.

The first implementation may be a console/local report. Later this may also feed
the operator CLI, human dashboard and Telegram.

The receipt is a projection over canonical facts/evidence. It is not a second
execution-state source of truth.

## 3. Human demonstration is part of useful acceptance

Where the result has a behavior that a person can meaningfully observe, the
workflow should offer a bounded demonstration.

Examples:

- show/render a generated report;
- invoke a new read-only operator CLI;
- perform a bounded API smoke request;
- after a separately authorized real Telegram transport exists, send a test
  notification and let the operator verify receipt.

A passing test suite is necessary evidence, but it does not automatically replace
a useful human-observable proof.

## 4. Current orchestration tooling is evolving

Current runner/launcher/adapter code is **EVOLVING**.

Do not treat a historical script as architectural authority merely because it
already exists. If a script is awkward, stale, repetitive or blocks a cleaner
governed workflow, inspect and improve or replace it.

The project must preserve the governed invariants; it must **not** distort new
design merely to preserve an obsolete implementation.

Current orchestration entrypoints should carry metadata/header language equivalent to:

```yaml
maturity: EVOLVING
canonical_architecture: false
replacement_allowed: true
refactoring_expected: true
```

They should also state that execution authority comes from governed bindings and
decisions, not from the runner file itself.

## 5. What remains canonical

Refactoring a runner must not silently remove these boundaries:

- bounded task / Work Front;
- fresh governed context;
- isolated workspace;
- source-state freeze/freshness;
- required ACK;
- explicit dispatch decision;
- bounded runtime/provider invocation;
- immutable attempt history;
- worker-delta verification;
- validation;
- separate acceptance/promotion;
- no hidden commit/push/merge/release/authority widening.

## 6. Current Task50 Telegram boundary

Task50 is **not** a Telegram bot transport implementation.

Its present goal is a local read-only projection plus Telegram-ready text over
existing Dispatcher / Execution Attempt Ledger / watchdog facts.

Therefore Task50 must not add:

- Telegram Bot API calls;
- bot token;
- chat ID;
- network client;
- daemon/listener/systemd/background polling.

A later bounded task may add real Telegram transport. When that exists, human
acceptance should include a real test notification.

## 7. Fresh-assistant reading set

A fresh assistant should normally need only a small current set:

1. `coordination/bootstrap/START_HERE.md`
2. `2026-09-27__blueprint__worker_operator_visibility_and_evolving_orchestration_policy_v0_1.yaml`
3. this guide
4. `2026-09-06__blueprint__worker_runtime_and_invocation_contract_v0_1.yaml`
5. `cf10_worker_training_queue_v0_1.yaml`

Always verify current repository state before acting. Historical scripts and old
attempts are evidence, not automatic execution authority.

## 8. Near-term implementation direction

1. Finish the current Task50 retry chain without weakening validation.
2. Add a deterministic operator receipt to the reusable Worker execution flow.
3. Consolidate preparation/launch/result/terminalization into a supported reusable
   orchestration entrypoint over the existing Control Plane.
4. Mark that entrypoint as EVOLVING and keep replacement/refactoring explicitly allowed.
5. Demonstrate operator-visible outputs whenever meaningful.
6. Check Makefile coverage once a stable operator command is ready.

This guide may be revised as CF-10 teaches us a better execution model.
