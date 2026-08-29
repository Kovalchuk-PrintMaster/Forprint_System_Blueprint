# Accounting Registry Service — evening delta

Working role:
- financial/accounting/commercial bookkeeping needed by ForPrint without unnecessary statutory bureaucracy;
- payments;
- receivables/payables;
- accounting value;
- financial documents and reports;
- reconciliation with external accounting.

1C remains a long-lived external/legacy accounting reality.

Keep ForPrint internal truth modern. Transform through a dedicated adapter/reconciliation layer and expose what was mapped, synthesized, omitted or could not be represented.

Integration Gateway should not own 1C legacy normalization.

A high-priority future implementation step is to work with a safe test copy of the real 1C database and build supported machine read/write + reconciliation capability.
