# Calculator Engine Development Focus

## Module ID

```text
calculator_engine
```
Status

Active module policy

Current focus

Calculator Engine should continue functional development around:

CalculationOutputPackage;
QuoteDraft / CommercialOfferDraft;
OrderDraft / OrderCreationDraft;
PriceBreakdown;
MaterialConsumptionEstimate;
ProductionMethodPlan;
OperationSequence;
AccountingLineDraft;
PrepressRequirementDraft;
ValidationWarning;
ManualCustomOperationDraft.
Near-term development direction

The next functional direction should be:

CalculationOutputPackage / Quote / OrderDraft Foundation

Expected outputs:

stable output package model;
clear quote draft structure;
clear order draft structure;
price breakdown included;
material consumption estimate included;
warnings preserved;
manual/custom operation draft preserved;
safe examples/fixtures;
tests for package creation and serialization;
documentation explaining future handoff to Operations Control Registry, Accounting and Prepress.
Allowed temporary development helpers

Calculator may use:

local catalog fixtures;
local product family examples;
local material projections;
local operation projections;
synthetic examples;
sandbox-only data.

These are allowed only to continue calculation logic development.

They must remain non-canonical.

Avoid overbuilding

Do not implement real integrations yet.

Do not wait for Gateway, Operations Control Registry, Library or Accounting Registry to be complete.

Use safe local projections and clear boundaries.

Current coordination note

Calculator already participates in Blueprint coordination loop.

Blueprint has central coordination metadata validator/fixer.

Further push/pull automation should be expanded carefully after metadata validation stabilizes.

For now, Calculator can continue core functional development while coordination tooling is hardened centrally in Blueprint.

Not in current focus

Do not implement now:

real Operations Control Registry integration;
real Accounting Registry integration;
real 1C integration;
real Gateway runtime integration;
warehouse stock reservation;
CRM workflow implementation;
prepress file lifecycle implementation;
large repository restructuring;
canonical Library catalog ownership.
Review criteria

Calculator progress should be reviewed against these questions:

Does this improve calculation logic?
Does this produce clearer structured output?
Does this help future order formalization?
Does this keep catalog/client/order/accounting boundaries clean?
Does this avoid becoming another module?
Does this remain test-covered?

---
