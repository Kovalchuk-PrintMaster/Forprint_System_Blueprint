# Session Digest — ForPrint Library: broad vision → canonical-definition boundary

## Authority class

This is a **Library module history**, not current Blueprint authority.

However, the final visible stage contains a Blueprint alignment prompt supplied to Library, so it is useful evidence for how the module boundary was deliberately narrowed.

## Initial owner goal

The owner wants a future-proof automation ecosystem for the print shop:
- Calculator;
- Prepress;
- Website/order intake;
- central Orchestrator;
- Library/Registry;
- later accounting, warehouse, CRM and other modules.

The key requirement is architectural extensibility: new products, partners and processes must not force a full rewrite.

## Original Library vision

The first owner description is intentionally broad:
- technical/legal/accounting documentation;
- currencies/regions;
- materials;
- technologies/equipment/modes;
- performance/capability definitions;
- technical cards;
- forms/contracts;
- revision/version history;
- compatibility/deprecation/blocking;
- partner-facing human and machine forms;
- strong testing/cross-checking;
- strong human admin interface.

The owner also mentions operational employee availability/sick leave and broadly says “everything” should live in the module.

That broad edge is important because later architecture explicitly corrects it.

## Core foundation before catalog completeness

The owner does **not** want to model every print product immediately.

Priority:
- storage/access;
- revisions;
- versioning;
- validation;
- compatibility;
- stable structured formats;
- cross-module consistency.

Every meaningful change should be checked before publication so incomplete materials/forms cannot silently enter canonical data.

## Three-layer split

Early assistant architecture separates:
1. Orchestrator — coordinates processes.
2. Registry/Library — says what formats/rules/definitions are valid/current.
3. Operational modules — Calculator, Prepress, Warehouse, Accounting, CRM, channels, logistics, production planning.

This is already an early warning against Library becoming the entire system.

## Admin interface

Owner says a strong admin UI is mandatory.

The historical design expects:
- create/edit canonical definitions;
- compare versions;
- validate before publishing;
- see dependency/impact;
- import/export structured data;
- inspect change history.

Routine canonical changes should not require manually editing server code.

## Historical bootstrap

Visible historical output shows:
- service `/health` returns ok;
- Stage 2 foundation reports `7 passed`;
- packages for contracts, migration, registry, semantic and validation exist.

Stage 2 focuses on:
- YAML seed loading;
- semantic IDs;
- aliases;
- migration paths;
- contract APIs.

These are historical implementation claims only.

## Git discipline

Owner sets a simple module rule:
**working bounded step → tests → commit → push**.

Local backups/caches/generated artifacts should be cleaned and ignored rather than committed.

## Blueprint alignment changes the boundary

The owner later introduces `Forprint_System_Blueprint` as the coordinating architecture module.

The supplied Blueprint prompt says Library should be:
- canonical knowledge layer;
- catalog/template layer;
- semantic/alias registry;
- contract-definition/versioning layer;
- migration graph;
- reusable canonical definitions.

But Library **must not** own:
- client orders;
- customer interaction history;
- payments/invoices;
- production queue;
- actual stock;
- runtime delivery;
- real uploaded-file lifecycle.

This later boundary supersedes the broad “everything belongs here” interpretation.

## Definition vs runtime instance

Canonical distinction:

Library may define:
- paper type/properties;
- invoice schema;
- warehouse availability contract;
- production technical-card template.

But Library does not own:
- today's actual paper quantity;
- a real invoice/payment;
- a real warehouse reservation/write-off;
- a real production job;
- a real uploaded client file.

This is one of the most important Library invariants.

## Semantic stability

Library alignment introduces stable semantic IDs and aliases.

Historical compatibility rule:
**semantic IDs should never be reused for a different meaning.**

Legacy names/IDs can map through aliases/migration paths instead.

## Change lifecycle and impact

Changes to:
- contracts;
- semantic registry;
- catalogs;
- technical cards/templates;
- migration graph

should trigger impact analysis.

Recommended activation:
`draft → approved → staged → syncing → active`.

Critical changes should not auto-activate.

## Sync Manager idea

The alignment proposes a future `forprint_sync_manager`:
- Library defines desired canonical state;
- Change Manifest describes changes;
- Sync Manager coordinates adoption across modules;
- Orchestrator routes already-valid work.

This concept must be reconciled with later Blueprint architecture; it may have been renamed or redistributed.

## Important later architecture conflict

The early alignment also treats Library as a contract registry/definition layer.

Later Blueprint history introduces a more explicit:
**domain owner → Contract Registry → Gateway runtime validation/routing** model.

Therefore early “Library owns contract registry” wording is **historical**, not current proof.

The current architecture must decide exactly which responsibilities remain in Library:
- catalogs?
- semantics?
- templates?
- schema source?
- contract definitions?
- migration metadata?
- or only references to a dedicated Contract Registry?

## Final historical Library role

The strongest stable statement from this source:

**Library defines what is valid and canonical.  
Library does not execute business operations and does not own runtime business state.**
