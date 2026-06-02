# ADR 0013: Strategic Agreements and Execution Queue

## Status

Accepted

## Context

ForPrint is moving from separate module development toward a coordinated ecosystem.

The project now needs a clear execution queue that records current strategic agreements, module priorities, ownership boundaries and deferred items.

This ADR does not start ForPrint Control Plane implementation.

Current governance remains:

```text
Owner / mentor
+
architectural assistant
+
ForPrint System Blueprint

ForPrint Control Plane is accepted as a future high-priority strategic governance layer, but remains deferred until core modules are alive and interconnected.

Decision

ForPrint System Blueprint records the following strategic agreements.

1. Operational Registry as internal data custodian

ForPrint Operational Registry is the main physical/internal data custodian of the ForPrint ecosystem.

It is responsible for maintaining the internal ForPrint database foundation, structured data storage and access interfaces.

It may physically store:

ClientAccount;
ClientGroup;
ContactPerson;
ContactMethod;
ChannelIdentity;
contact/account relationships;
CustomerRequest / CustomerIntent;
Order;
order statuses;
operational history;
internal records;
logistics/address references;
accounting references;
module references;
manual decision records.

Operational Registry physically stores and maintains data, but it must not become the logical owner of every domain rule.

2. Library as canonical semantic/catalog authority

ForPrint Library is the canonical semantic/catalog authority.

It owns canonical meaning for:

product_id;
service_id;
material_id;
operation_id;
canonical names;
aliases;
semantic registry;
catalog definitions;
contract definitions;
technical cards;
versioning.

If a module has ambiguity about product/service/material/operation naming, it must not invent its own permanent meaning. It should route the ambiguity to Library for canonical ID/name/approval.

3. Calculator as primary order formalization point

Calculator Engine is the primary formalization point for new order/calculation requests.

All new orders should primarily go through Calculator, including:

external customer requests;
manager/internal requests;
Telegram requests;
Website requests;
future Mobile App requests;
CRM manual entry.

Calculator should produce structured machine-readable packages such as:

CalculationOutputPackage;
Quote / CommercialOffer;
OrderDraft / OrderCreationDraft;
price_breakdown;
material_consumption_estimate;
production_method_plan;
operation_sequence;
accounting line drafts;
prepress requirements;
validation warnings;
manual/custom operation drafts.

Calculator must not own canonical order truth, client registry, accounting truth, 1C write, warehouse truth or prepress lifecycle.

4. Phone is lookup key, not canonical client identity

Phone number is a strong practical lookup/contact key, but it is not canonical client identity.

Canonical identity is ClientAccount ID.

A phone can be linked to multiple accounts over time/context.

Early ambiguity strategy:

if one phone maps to multiple ClientAccount records:
  create ready request/order form
  send possible account list to responsible person/operator
  operator selects the correct ClientAccount
  automation continues

This is an accepted human-in-the-loop strategy until stronger automated disambiguation is developed.

5. ClientAccount and ClientGroup

ClientAccount is the primary customer/account entity.

ClientGroup is a rare but important corporate grouping entity.

Every Order must belong to one concrete ClientAccount.

ClientGroup is used for:

corporate grouping;
analytics;
large client groups with multiple legal entities;
cross-account reporting.

ClientGroup does not replace ClientAccount.

6. CustomerRequest lifecycle must be stored

Every identifiable customer request/intent should be stored in the internal ForPrint DB.

This includes:

information-only inquiries;
price inquiries;
unconfirmed requests;
draft requests;
trial/provisional requests;
requests that never converted;
cancelled requests;
rejected requests;
unresolved requests;
payment-unconfirmed requests;
unsupported-product requests.

The purpose is analytics, conversion tracking, lost-order analysis, product demand analysis, pricing/terms analysis and future spam/competitor-monitoring detection.

7. ForPrint internal DB and 1C relationship

ForPrint internal DB is the main internal management/accounting/operational data foundation.

1C remains an important accounting synchronization and accountant-facing work interface.

ForPrint DB must be:

1C-aware;
sync-friendly;
compatible with dictionaries, counterparties, currencies and prices where useful;
able to support custom reporting and analytics.

ForPrint DB must not be treated as a blind copy of 1C.

Accounting Registry owns:

1C synchronization adapters;
1C import/export;
1C mapping;
1C staging;
1C reconciliation;
1C report extraction;
accounting-domain workflow processing.

Operational Registry remains the physical/internal DB custodian.

Accounting Registry v0.5 status

Accounting Registry v0.5 is accepted as:

sandbox_1c_import_export_ready

Accepted completed scope:

sanitized 1C-like source intake;
JSON/CSV/XML/YAML/TXT export parsing;
offline import pipeline;
mapping issue persistence;
directory import/export fixtures;
report extraction fixtures;
safe developer CLI scripts;
sandbox write safety;
117 tests passed;
no live 1C connection;
no live 1C write;
no production synchronization.

Accounting v0.6 is conditional and should only proceed after real sanitized 1C export samples are available.

Execution queue

The current execution queue is:

P0
System Blueprint — record strategic agreements and execution queue.
All active modules — add coordination/status standard.
Calculator Engine — CalculationOutputPackage / Quote / OrderDraft / downstream handoff.
Accounting Registry — pause after v0.5 until real sanitized 1C samples, maintain readiness.
P1
Operational Registry v0.6 — Core ForPrint Data Model Expansion.
Library — Canonical Product/Service ID and Alias Governance.
Telegram Bot / Customer Channel — channel-agnostic CustomerRequest and Calculator handoff.
P2
CRM — dashboard/workflow/manual-decision interface later.
Gateway — runtime transport only after real handoff need.
Control Plane — planned/deferred until core modules are alive.
Legacy file-name parser — low-priority fallback, not core workflow.
Consequences

This ADR gives all module assistants a shared direction.

It prevents premature development of Control Plane, Gateway runtime, CRM UI and legacy file parsing.

It confirms the next project focus:

Blueprint agreements
→ module status reporting
→ Calculator structured output
→ Operational Registry core data model
→ Library canonical semantics
→ Telegram/customer channel handoff
Explicitly deferred

Do not implement now:

Control Plane repository;
Control Plane scripts;
automatic module sync;
automatic Git pull across repositories;
production API;
runtime integrations;
real Gateway routing;
live 1C integration;
CRM UI;
PostgreSQL production migration.

---
