# Session Digest — CRM source: Prepress Hub → Inspector → System Blueprint → CRM alignment

## Duplicate result

Unique source: no shared message IDs or exact normalized substantive messages with prior loaded dialogues.

## Coverage

Only 11 message blocks survive across turns 1–30. Turns 3–25 are missing.

The source nevertheless contains unusually important direct owner evidence for the origins of:
- Prepress Hub;
- Project Inspector;
- ForPrint System Blueprint;
- CRM's noncanonical orchestration/dashboard boundary.

## Early Prepress automation

The conversation starts with the owner asking how to automate Photoshop/Illustrator/Acrobat workflows without building a heavy independent plugin for every product.

Historical proposal:
- unified operator panel;
- drag/drop or file selection;
- reusable presets;
- ordered multi-app processing;
- configurable outputs.

Assistant proposes:
**local Python backend/agent + web UI + worker queue + declarative Preset Engine + Adobe adapters + hot folders + logs**.

This is historical Prepress architecture only; current implementation remains unaudited.

## From Project Control to Project Inspector

Later the assistant proposes a `ForPrint Project Control Plane` for project-wide development control.

Owner then makes a key correction:
- the verification idea is valid;
- preferred name is **ForPrint Project Inspector**;
- Inspector should verify correctness of module work;
- it should not expand into the higher architecture/ideological role.

This matters because later `Strategic Control Plane` is a separate concept and should not be merged with this early Project Control naming.

## Direct owner genesis of System Blueprint

The owner then articulates the missing upper layer.

Requirements include:
- overall architecture map;
- module interactions;
- data packages and sequence;
- ownership/dependencies;
- dynamic evolution as new services/modules appear;
- machine-readable form for modules/automation;
- human-readable form for people;
- generation of architecture instructions/prompts for modules;
- high-level ideological control abstracted from code.

Assistant names it:
**ForPrint System Blueprint**.

Proposed split:
- Blueprint = desired architecture/ownership/data flows/contracts;
- Inspector = conformance reviewer;
- CRM = business/management UI;
- domain modules = implementation.

This is a strong historical predecessor of the later dedicated Blueprint dialogues.

## Early ownership drift corrected in the same source

In the first Blueprint example, `data_objects.yaml` shows:
- `client owner: forprint_crm`;
- `order owner: forprint_crm`.

But the later direct CRM alignment prompt explicitly changes the model:
- Operational Registry → clients/orders/tasks/operational statuses;
- Accounting Registry → invoices/payments/1C truth;
- Library → catalogs/templates/product/material names;
- Inspector → architecture drift reports;
- Gateway → routed execution/results.

Therefore the early illustrative CRM ownership is **superseded inside the same source**.

It must not be used as current canon.

## CRM alignment

The owner provides a concrete Blueprint alignment prompt, including path:
`coordination/outgoing_prompts/forprint_crm/drafts/2026-05-22-align-crm-with-blueprint.md`.

CRM role:
**business orchestration + human-facing dashboard + analytics/reporting interface**.

CRM must not become:
- all-in-one backend;
- universal canonical database;
- Operational Registry clone;
- Accounting Registry clone;
- Library clone;
- Integration Gateway;
- Project Inspector.

## CRM-owned vs displayed data

Historical alignment proposes CRM owning only human/UI/coordination concerns such as:
- dashboard layout/settings;
- user views/filters;
- saved reports;
- UI preferences;
- management notes;
- review-board configuration;
- command history;
- notification preferences;
- clearly noncanonical cached/analytics projections.

Canonical business truth remains in specialized owners.

## Commands through Gateway

Historical contracts proposed:
- registry → CRM snapshots/summaries;
- Inspector → CRM architecture health;
- CRM → Gateway command;
- Gateway → CRM command result.

Important rule:
**CRM should initiate workflow commands through Integration Gateway rather than call specialized modules directly.**

## Open boundary

The source does not finally settle:
- whether CRM itself creates a new order;
- or whether CRM sends an order-creation command through Gateway to Operational Registry;
- where canonical manual-decision records live.

That remains a current architecture audit target.

## Historical significance

This source is especially valuable because it documents a causal architecture chain:

**operator automation problem → Prepress Hub idea → project-wide verification concern → Project Inspector → separate ideological architecture need → System Blueprint → explicit CRM alignment**

It predates and explains several later Blueprint invariants without replacing current release authority.
