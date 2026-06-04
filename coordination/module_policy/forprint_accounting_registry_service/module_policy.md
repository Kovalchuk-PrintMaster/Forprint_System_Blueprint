# Module Policy — ForPrint Accounting Registry Service

## Module ID

```text
forprint_accounting_registry_service
```

## Priority

```text
selective
```

## Development status

```text
sandbox_1c_import_export_ready
```

## Strategic role

Accounting boundary and 1C synchronization/staging module.

## Main goals

- `Maintain accounting-only references and 1C staging.`
- `Support sanitized import/export experiments.`
- `Prepare mappings and reconciliation logic.`
- `Keep live 1C write and automatic posting forbidden until explicitly approved.`

## Owns

- `accounting_references`
- `one_c_raw_snapshot`
- `one_c_staging_record`
- `one_c_mapping_record`
- `import_job`
- `export_job`
- `reconciliation_job`
- `sandbox_one_c_io`

## Must not own

- `operational_client_registry`
- `operational_order_registry`
- `canonical_catalog_truth`
- `crm_workflow`
- `calculator_logic`
- `warehouse_stock_truth`

## Next focus

- `Maintain v0.5 sandbox readiness.`
- `Wait for real sanitized 1C samples before v0.6.`
- `Do not proceed to live 1C integration yet.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
