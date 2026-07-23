# Module Policy — ForPrint Contract Registry

## Module ID

```text
forprint_contract_registry
```

## Priority

```text
deferred
```

## Development status

```text
planned_placeholder_contract_foundation_pending
```

## Strategic role

Canonical registry and lifecycle authority for versioned inter-module interface contracts, ownership metadata, compatibility baselines and generated read-only contract catalogs.

## Main goals

- `Maintain discoverable versioned inter-module contract packages.`
- `Register contract owners, producers and consumers.`
- `Validate manifests, schemas, examples and lifecycle metadata.`
- `Detect potentially breaking changes before release.`
- `Publish approved read-only contract artifacts for Gateway and modules.`
- `Preserve migration, deprecation and recovery metadata.`

## Owns

- `inter_module_contract_registry`
- `contract_manifest_schema`
- `contract_id_namespace`
- `interface_contract_version_history`
- `producer_consumer_registration`
- `contract_lifecycle_metadata`
- `contract_compatibility_baselines`
- `contract_compatibility_results`
- `contract_examples_and_fixtures`
- `contract_release_metadata`
- `contract_deprecation_and_migration_metadata`
- `generated_read_only_contract_catalog`

## Must not own

- `business_workflow_decisions`
- `runtime_request_routing`
- `runtime_transport_execution`
- `catalog_business_semantics`
- `product_or_material_definitions`
- `pricing_logic`
- `module_internal_data_models`
- `operational_data_truth`
- `prompt_governance`
- `project_priority_decisions`

## Next focus

- `Keep placeholder only.`
- `Prepare Contract Foundation ADR and interaction inventory.`
- `Reassess activation for the Library-to-Calculator contract pilot.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
