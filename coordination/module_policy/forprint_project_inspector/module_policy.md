# Module Policy — ForPrint Project Inspector

## Module ID

```text
forprint_project_inspector
```

## Priority

```text
p2
```

## Development status

```text
planned_bootstrap_pending
```

## Strategic role

Future project-level verification and inspection module for ForPrint repository structure, Makefile standards, coordination metadata, module readiness and cross-module advisory reports.

## Main goals

- `Inspect module alignment with Blueprint standards.`
- `Audit Makefile standard adoption across modules.`
- `Aggregate module readiness and coordination status.`
- `Provide read-only project verification reports.`
- `Prepare migration of temporary Blueprint project verification scripts.`

## Owns

- `project_structure_verification`
- `module_makefile_standard_audit`
- `coordination_metadata_audit`
- `module_readiness_summary`
- `cross_module_advisory_reports`

## Must not own

- `architecture_policy`
- `module_business_logic`
- `production_runtime_control`
- `operational_order_truth`
- `accounting_truth`
- `warehouse_stock_truth`
- `live_integrations`

## Next focus

- `Keep bootstrap pending.`
- `Define read-only project verification scope.`
- `Prepare portable verification scripts migrated from Blueprint later.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
