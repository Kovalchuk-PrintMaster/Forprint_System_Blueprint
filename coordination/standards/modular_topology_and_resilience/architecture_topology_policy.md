# Architecture Topology Policy

## Purpose

This policy defines the preferred high-level architecture topology for the ForPrint ecosystem.

ForPrint should remain modular, understandable, local-first, and service-ready.

The project should not become a single hidden monolith, but it also should not adopt heavy distributed microservices before the domain model and contracts are mature.

## Core decision

ForPrint uses a domain-owned modular architecture.

```text
Domain-owned modular system first.
Runtime microservices only when justified.
Shared infrastructure is allowed.
Shared ownership is forbidden.
```

## Not a hidden monolith

ForPrint modules must not be merged into one large application where ownership becomes unclear.

The following ownership boundaries must remain explicit:

```text
ForPrint System Blueprint owns architecture and standards.
ForPrint Library owns semantic and catalog meaning.
Calculator Engine owns calculation outputs and drafts.
ForPrint Operations Control Registry owns operational truth.
ForPrint Accounting Registry Service owns accounting and 1C staging truth.
ForPrint Integration Gateway owns transport and handoff reliability.
Telegram Bot, Website and future Mobile App own customer channel shells.
ForPrint CRM owns human-facing workflow views and coordination UI.
```

## Not premature microservices

ForPrint should not introduce runtime microservices, queues, brokers, distributed deployment or network-heavy integration only for architectural fashion.

Service extraction is allowed when at least one of the following is true:

```text
the module contract is stable;
the module has a clear runtime owner;
independent deployment brings real value;
load or reliability requires separation;
security or data sensitivity requires separation;
the operational cost is understood and accepted.
```

## Preferred evolution

ForPrint should evolve in stages.

### Stage 1 — local modular development

```text
separate repositories;
clear module ownership;
local files, examples, CLI previews and tests;
no production runtime integration required;
Blueprint standards and coordination metadata enforced gradually.
```

### Stage 2 — local service-ready system

```text
one local server may host multiple modules;
shared PostgreSQL infrastructure is allowed;
logical schemas and ownership remain separated;
Gateway starts owning reliable handoff metadata;
modules expose stable commands, queries, DTOs or local contracts.
```

### Stage 3 — distributed deployment when justified

```text
selected modules may run on different servers;
network calls are routed through approved boundaries;
Gateway tracks handoff status and delivery;
modules tolerate temporary unavailability of dependencies;
manual recovery paths are available.
```

### Stage 4 — advanced runtime infrastructure

```text
message broker or event streaming may be introduced only after need is proven;
observability and runtime inspection become mandatory;
backup, restore, retry and dead-letter policies are tested;
module contracts are versioned.
```

## Physical deployment

ForPrint modules may run:

```text
on one server;
on multiple local servers;
inside containers;
as local scripts or services;
as separate runtime services later.
```

Physical placement must not change data ownership.

A module running on the same server as another module still must not write to another module's owned data directly.

## Gateway position

ForPrint Integration Gateway is the preferred runtime boundary for inter-module command and event delivery.

Gateway is not the business brain.

Gateway coordinates transport, validation, routing, idempotency and delivery state.

Business truth remains inside owner modules.

## Project Inspector position

ForPrint Project Inspector should later verify whether modules follow this topology, but it must remain read-only by default.

Project Inspector checks alignment.

It does not rewrite module architecture automatically.

## Production Runtime Inspector position

Production Runtime Inspector should later monitor live service health, module availability and runtime failures.

It does not own business data.

## Boundary

This policy defines topology.

Detailed data ownership is defined in `data_ownership_and_storage_policy.md`.

Detailed handoff reliability is defined in `module_interaction_reliability_policy.md`.

Gateway responsibility is defined in `gateway_responsibility_policy.md`.
