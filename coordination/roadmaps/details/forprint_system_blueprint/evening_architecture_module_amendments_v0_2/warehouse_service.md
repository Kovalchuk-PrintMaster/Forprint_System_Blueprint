# warehouse_service — Evening Architecture Amendment v0.2

Status: Operator-confirmed core direction plus proposed mature expansion.

## Confirmed core

- physical stock truth;
- reservation against orders/jobs;
- projected available stock after reservation;
- per-material minimum/reorder policy;
- recommended replenishment quantity/target;
- immediate replenishment need when projected stock breaches policy;
- damage/spoilage/unusable-material write-off with traceability.

## Proposed mature expansion

Receiving/discrepancy handling, quarantine/inspection, bin/location movements, inventory/cycle count, explicit inventory states, safety stock/lead-time inputs, unused reservation return, planned-vs-actual consumption, internal defect/waste traceability and replenishment history.

## Ownership caution

Warehouse owns replenishment need/evidence. Purchasing execution and financial authorization must be reconciled with the correct owner.
