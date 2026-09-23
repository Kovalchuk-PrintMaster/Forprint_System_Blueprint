# Session Digest — Accounting Registry: production-vs-1C split → sanitized v0.5 sandbox

## Authority class

This is **Accounting Registry module history**, not Blueprint authority.

## Initial architectural problem

The owner wants the print-shop production flow to stop depending on 1C for live technical work.

Initial intent:
- import existing material definitions/balances from 1C;
- maintain real production movement internally;
- send verified results back to 1C periodically;
- keep accounting/bookkeeping inside 1C for now.

The key principle formulated in the dialogue is:

**production operational truth ≠ accounting/1C truth**.

This predates and supports the later explicit Operational Registry boundary.

## Early material-ledger idea

The assistant proposes `inventory_core / materials_ledger` with event-style movement records:
- receipt;
- write-off;
- reserve;
- release reserve;
- correction;
- inventory adjustment.

Balances are derived from movements rather than directly edited.

Important historical caution:
this was discussed inside the Accounting chat, but later module boundaries mean this should **not** be read as “Accounting Registry owns production inventory”.

Current authority must decide whether such movement truth belongs to Operational Registry, Warehouse, or another operational owner.

## 1C integration pattern

The early design avoids synchronous “write directly into 1C”.

Proposed flow:
`operational event → outbox/sync_queue → 1C adapter → 1C → sync result/log`.

Benefits:
- production continues if 1C is unavailable;
- retries are possible;
- failed transfers remain observable;
- scheduled/manual/end-of-day/emergency resync can coexist.

Transfers should carry structured provenance, not just “800 m² written off”.

## Blueprint coordination

Owner explicitly prepares state/intent reports for Blueprint and checks whether the current Blueprint prompt is complete before taking another.

## v0.5 sandbox implementation

Historical final v0.5 report says:
- Ruff OK;
- pytest `117 passed`, one dependency warning;
- check-report OK;
- test-fixture validation OK;
- gitignore sandbox validation OK.

Commit:
`95d4a55 — Add Accounting Registry sanitized OneC import pipeline`.

Historical v0.5 surfaces include:
- sanitized source registration;
- export detection/parsers;
- schema probe;
- offline import pipeline;
- mapping issue persistence;
- safe developer smoke scripts;
- sanitized fixtures.

Supported file examples include:
JSON / CSV / XML / YAML / TXT/tabular exports.

## Data safety boundary

Historical behavior explicitly rejects:
- unsanitized sources;
- production sources.

The original source is not mutated by tests.

Schema discovery/import output is **noncanonical staging evidence**, not automatically business truth.

## Historical Blueprint acceptance

The owner supplies:
`Accounting Registry v0.5 is accepted`
with status:
`sandbox_1c_import_export_ready`.

This is historical acceptance evidence only.

Crucially, the same acceptance says:

- do not proceed to live 1C integration;
- do not implement production write;
- do not implement automatic posting.

Therefore:
**sandbox import/export readiness ≠ live integration readiness**.

## v0.6 gate

v0.6 may start only when real sanitized export samples are provided.

Required categories:
- counterparties;
- nomenclature;
- invoices;
- payments;
- balances.

Until then the module stays in maintenance:
- keep v0.5 green;
- update status/coordination;
- no production 1C behavior;
- no live writes;
- no automatic posting.

## Final module boundary

The v0.5 maintenance instruction explicitly forbids Accounting Registry from becoming:
- canonical client registry;
- canonical order registry;
- canonical product/material catalog;
- full 1C mirror.

It also forbids live runtime integration with:
Gateway / CRM / Operational Registry / Library / Calculator / Warehouse at this stage.

This produces a strong stable interpretation:

**Accounting Registry owns the accounting/1C integration boundary and sanitized accounting data staging/mapping.  
Operational Registry and other operational owners own runtime production truth.**

## Main cross-dialogue significance

This source is the missing predecessor to the later `Accounting Registry vs Operational Registry` ambiguity.

It demonstrates that the original intended split was not “two competing registries”.

It was:
- Operational side = actual business/production operational state;
- Accounting side = accounting/1C truth and controlled synchronization.

Current repository authority must verify how that intent was ultimately implemented.
