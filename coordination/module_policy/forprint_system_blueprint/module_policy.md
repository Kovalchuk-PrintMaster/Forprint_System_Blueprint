# Module Policy — ForPrint System Blueprint

## Module ID

```text
forprint_system_blueprint
```

## Priority

```text
p0
```

## Development status

```text
active_governance
```

## Strategic role

Architecture, ownership boundaries, execution queue, coordination standards, module policy and project-wide governance.

## Main goals

- `Maintain global ForPrint architecture.`
- `Keep module boundaries explicit.`
- `Maintain global policy, module policy and coordination standards.`
- `Collect module status and support owner/mentor decisions.`
- `Maintain repository/document/machine-surface cleanliness as a permanent architecture objective.`
- `Govern the Document Type Registry, normalization debt baseline and class-by-class migration program.`

## Owns

- `architecture_policy`
- `module_boundaries`
- `execution_queue`
- `coordination_standards`
- `module_policy`
- `module_source_registry`
- `coordination_metadata_tools`
- `project_cleanliness_governance`
- `document_type_registry`
- `surface_normalization_program`

## Must not own

- `runtime_business_logic`
- `production_order_processing`
- `accounting_posting`
- `customer_channel_runtime`
- `foreign_module_business_semantics_during_normalization`

## Next focus

- `Stabilize module policy for all active modules.`
- `Keep coordination metadata validator/fixer central.`
- `Prepare future ecosystem-check foundation.`
- `Normalize current machine-active document classes before broad module implementation resumes.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
