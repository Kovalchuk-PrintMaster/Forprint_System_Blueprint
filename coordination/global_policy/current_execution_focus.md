# Current ForPrint Execution Focus

## Status

Active global policy

## Current priority model

## P0

### 1. System Blueprint coordination foundation

Keep System Blueprint as the current governance and coordination center.

Control Plane is planned but deferred.

### 2. Calculator Engine

Calculator Engine is the first module used to validate the full coordination loop.

Calculator remains a P0 module.

Current direction:

```text
CalculationOutputPackage;
Quote / CommercialOffer;
OrderDraft / OrderCreationDraft;
price_breakdown;
material_consumption_estimate;
production_method_plan;
accounting line drafts;
prepress requirements;
manual/custom operation drafts.
3. Module coordination loop

Each active module must eventually maintain:

coordination/status/current_status.yaml;
coordination/prompts/index.yaml;
coordination/reports/index.yaml;
completion reports;
questions for Blueprint.
P1
Operational Registry

Next planned direction:

Core ForPrint Data Model Expansion

Expected future focus:

ClientAccount;
ClientGroup;
ContactPerson;
ContactMethod;
ChannelIdentity;
Relationship;
CustomerRequest lifecycle;
Order lifecycle;
1C-aware references;
logistics addresses;
manual decision records.
Library

Next planned direction:

Canonical Product/Service ID and Alias Governance

Expected future focus:

canonical IDs;
aliases;
semantic definition requests;
draft/review/approved lifecycle;
module ambiguity routing.
Telegram Bot

Next planned direction:

Channel-agnostic customer request and Calculator handoff

Telegram must remain a channel adapter.

Selective / waiting
Accounting Registry

Current status:

sandbox_1c_import_export_ready

Next deeper v0.6 requires real sanitized 1C export samples.

Do not proceed to live 1C write or production sync.

Hold / planned
Integration Gateway

Hold until real runtime handoff is needed.

Control Plane

Planned high priority, deferred until core modules are alive.

Legacy file parser

Low-priority fallback.

Future core workflow should come from Calculator-generated packages.


---
