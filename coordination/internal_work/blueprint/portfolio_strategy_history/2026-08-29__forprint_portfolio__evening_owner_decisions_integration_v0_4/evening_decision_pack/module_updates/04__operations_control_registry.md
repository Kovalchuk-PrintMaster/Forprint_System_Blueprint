# Operations Control Registry — renamed from Operational Registry

Canonical working name: **Operations Control Registry**
Proposed technical ID: `operations_control_registry`

Main candidate for ForPrint's operational control center:
- active orders;
- reserves;
- shortages;
- incidents;
- operational commitments;
- critical deadlines;
- active resolution workflows;
- consolidated operational visibility.

Example:
Warehouse says 1,200 sheets physically exist.
Operations Control Registry says 800 are reserved, so only 400 are available to promise.

Shortage scenario:
shortage detection -> preferred supplier -> communication -> invoice -> payment approval -> payment -> urgent inbound Logistics tracking -> deadline reassessment -> customer communication if needed.

Do not create a separate Procurement module now.
