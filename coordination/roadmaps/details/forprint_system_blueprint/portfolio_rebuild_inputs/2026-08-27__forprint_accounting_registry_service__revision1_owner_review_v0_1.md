# Accounting Registry Revision-1 Owner Review — Rebuild Input — 2026-08-27

Status: AGREED OWNER/THEORY INPUT; READY FOR DEEP DECOMPOSITION; NOT EXECUTION AUTHORITY.

# Accounting Registry Service — Revision 1 Owner Notes

Status: `REVISION_1_DISCUSSED`
Next: `TARGET_DIRECTION_CLEAR_READY_FOR_DEEP_DECOMPOSITION`

## Strategic role — AGREED_WITH_OWNER

Build ForPrint's own operational/commercial accounting registry and gradually move daily business work away from dependence on 1C.

Initial target is not full statutory/tax accounting.

Core scope:
- goods/material movement;
- purchases;
- sales;
- invoices;
- payments;
- settlements;
- write-offs;
- management reporting;
- document state;
- reconciliation.

## 1C relationship — AGREED_WITH_OWNER

Accountants will continue using 1C for statutory/reporting needs.

ForPrint needs connectors/import-export/synchronization so accountants can see the relevant live picture without repeating operational work manually.

Expected exchanged classes:
- payments;
- purchases;
- sales;
- goods movement;
- material write-offs;
- invoices / accounting-document data.

Long-term direction:
ForPrint's own registry becomes the primary operational commercial system.
1C remains a compatibility/downstream accounting environment as long as needed.

## Functional benchmark — AGREED_WITH_OWNER direction

Use useful 1C management/commercial-accounting capabilities as a benchmark, but do not copy 1C architecture or poor UX blindly.

The next deep decomposition should identify the closest functional 1C scope for:
- management/commercial accounting;
- sales/purchases;
- warehouse;
- money/payments;
- settlements;
- production/business analytics;
without making statutory accounting the initial core.

## Candidate capability families — SYNTHETIC_CANDIDATE

- counterparties and financial attributes;
- orders/invoices/realization;
- procurement and goods receipt;
- payments and settlements;
- goods/material movement;
- planned/actual write-offs;
- returns/corrections;
- cost and financial result;
- document lifecycle;
- reconciliation;
- 1C import/export/sync;
- management reports;
- exception workflows.

## Warehouse boundary — PROVISIONAL_BOUNDARY

Warehouse owns physical fact:
- what;
- how much;
- where physically.

Accounting Registry owns:
- documentary/accounting movement;
- financial value;
- accounting state;
- reconciliation records.

A mismatch between system stock and physical stock is a reconciliation incident, not permission for silent competing truths.

## Calculator boundary — PROVISIONAL_BOUNDARY

Calculator provides:
- planned materials;
- planned technical waste;
- calculated price;
- structured order/commercial specification.

Actual consumption must remain distinguishable from planned consumption.

## Human involvement — AGREED_WITH_OWNER

Normal workflow should be highly automated.

Human is needed mainly for:
- physical vs system stock conflict;
- ambiguous mapping;
- unresolved reconciliation;
- exceptional correction;
- other cases where automatic facts cannot be trusted.

Fast exception handling should later be possible through UI and potentially a governed Telegram admin/emergency channel.

## 1C sync authority — OPEN_QUESTION

Must later define:
- what flows ForPrint -> 1C automatically;
- what, if anything, may flow back;
- conflict rules;
- duplicate prevention;
- idempotency;
- whether 1C may ever override canonical operational state.

Working preference:
ForPrint is operational authority; 1C is primarily downstream for accountant/statutory needs.

## Stabilization — AGREED_WITH_OWNER direction

Accounting needs a longer proving period than Calculator.

Candidate:
one or two quarters of stable operation after tuning.

Metrics should be class-specific:
- money reconciles essentially exactly;
- documents are not lost/duplicated;
- payment posting is reliable;
- 1C exchange is idempotent;
- material/accounting discrepancies are controlled and visible;
- manual corrections are rare and auditable.

## Remaining gray zones

- exact Warehouse/Accounting contract;
- exact Calculator planned-vs-actual flow;
- 1C sync/conflict rules;
- canonical accounting entity model;
- report scope;
- correction/reversal/reconciliation lifecycle.
