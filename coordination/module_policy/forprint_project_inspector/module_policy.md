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
- `Detect module self-inventory drift and missing/stale capability evidence.`
- `Detect duplicate capability candidates and cross-module semantic divergence.`
- `Audit shared UI design-system adoption, stale component versions and accessibility/conformance drift.`
- `Audit repository cleanliness and structural conformance across ForPrint projects.`
- `Detect unregistered surface types, generated-file drift, orphan documents, duplicate capability/semantic surfaces and structural zoo growth.`

## Owns

- `project_structure_verification`
- `module_makefile_standard_audit`
- `coordination_metadata_audit`
- `module_readiness_summary`
- `cross_module_advisory_reports`
- `module_self_inventory_conformance`
- `duplicate_capability_detection`
- `shared_ui_conformance`
- `repository_cleanliness_audit`
- `document_surface_conformance_audit`
- `generated_surface_drift_detection`

## Must not own

- `architecture_policy`
- `module_business_logic`
- `production_runtime_control`
- `operational_order_truth`
- `accounting_truth`
- `warehouse_stock_truth`
- `live_integrations`
- `ui_design_system_semantics`
- `capability_ownership_decision`
- `foreign_module_semantic_rewrite`

## Next focus

- `Keep bootstrap pending.`
- `Define read-only project verification scope.`
- `Prepare portable verification scripts migrated from Blueprint later.`
- `Add read-only self-inventory, duplicate-capability and shared-UI conformance checks.`
- `Build the first read-only Inspector Cleanliness Pack from the Blueprint normalization validator set.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
