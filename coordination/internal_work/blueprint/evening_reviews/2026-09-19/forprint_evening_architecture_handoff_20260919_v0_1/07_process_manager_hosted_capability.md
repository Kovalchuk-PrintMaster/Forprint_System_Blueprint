# Durable Business Process Manager — Hosted Capability Concept

## Problem

ForPrint has long-running processes that can remain idle for days, weeks or months.

Example:
- customer places an order;
- ForPrint sends it to a contractor;
- contractor takes 30–60 days;
- later readiness must be checked;
- shipping route must be determined;
- tracking must be obtained;
- customer must be notified;
- delivery must be monitored;
- non-pickup or failure must escalate.

This state must not live in Telegram Bot memory.

## Responsibility

The Process Manager owns:
- process definition;
- process instance;
- current state;
- expected event;
- waiting condition;
- timers;
- deadlines;
- retries;
- escalation;
- human task;
- next transition;
- audit history.

Telegram Bot owns communication around the process, not the process itself.

## Example

```text
ORDER_CONFIRMED
    ↓
SUPPLIER_ORDERED
    ↓
WAITING_SUPPLIER
    ↓
SUPPLIER_READY
    ↓
SHIPPING_ROUTE
    ↓
WAITING_TRACKING
    ↓
TRACKING_RECEIVED
    ↓
CUSTOMER_NOTIFIED
    ↓
IN_TRANSIT
    ↓
DELIVERED
    ↓
FULFILLED
```

## Current architecture decision

Do **not** create a standalone new module immediately.

First select an existing host after auditing current module boundaries.

## Hosted / incubated capability rule

The capability should behave like an independent employee temporarily assigned to a department.

The host provides operational support such as:
- runtime;
- deployment;
- logging;
- configuration;
- DB connectivity;
- governance integration.

But the capability should keep:
- its own namespace/package;
- its own contracts;
- its own state model;
- its own tests;
- explicit adapters/ports;
- minimal host-internal imports.

## Extraction readiness

Required from the start.

Possible futures:
1. remain hosted permanently;
2. extract into standalone service/module;
3. replace implementation with a workflow engine;
4. move to another host;
5. retire if superseded.

Consumers should depend on the Process Manager contract, not its initial host location.

## Host-selection questions for tomorrow

Compare at least:
- Operational Registry;
- CRM;
- Logistics Service;
- existing orchestration/control-plane structures.

Questions:
- who is closest to operational execution truth?
- who already tracks long-lived business state?
- who can host without semantic contamination?
- who can provide persistence/runtime cleanly?
- which host minimizes cross-module coupling?
- can the capability be extracted later without rewriting consumers?
