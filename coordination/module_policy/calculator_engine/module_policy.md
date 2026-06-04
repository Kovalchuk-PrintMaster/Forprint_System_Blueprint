# Module Policy — Calculator Engine

## Module ID

```text
calculator_engine
```

## Priority

```text
p0
```

## Development status

```text
active_development
```

## Strategic role

Primary calculation and order formalization module.

## Main goals

- `Produce CalculationOutputPackage.`
- `Produce QuoteDraft / CommercialOfferDraft.`
- `Produce OrderDraft / OrderCreationDraft.`
- `Preserve price breakdown and material consumption estimates.`
- `Support local non-canonical catalog projections while Library is not ready.`

## Owns

- `calculation_logic`
- `calculation_output_package`
- `quote_draft`
- `order_draft`
- `price_breakdown`
- `material_consumption_estimate`
- `calculation_warnings`

## Must not own

- `canonical_client_registry`
- `canonical_order_registry`
- `canonical_catalog_truth`
- `accounting_truth`
- `one_c_synchronization`
- `warehouse_stock_truth`
- `prepress_lifecycle`
- `crm_workflow`

## Next focus

- `Harden CalculationOutputPackage / Quote / OrderDraft Foundation.`
- `Keep local catalog fixtures non-canonical.`
- `Prepare downstream-ready structured output.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
