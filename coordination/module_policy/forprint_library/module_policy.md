# Module Policy — ForPrint Library

## Module ID

```text
forprint_library
```

## Priority

```text
p1
```

## Development status

```text
active_development
```

## Strategic role

Canonical semantic, catalog, naming, alias and contract-definition authority for products, services, materials, operations and templates.

## Main goals

- `Own canonical product/service/material/operation IDs.`
- `Maintain aliases and naming rules.`
- `Provide semantic resolution for module ambiguity.`
- `Keep contract definitions and catalog semantics versioned.`
- `Publish the versioned shared ForPrint UI design-system package and reusable component catalog.`
- `Expose searchable semantic and reusable-capability references before modules create competing implementations.`

## Owns

- `product_catalog_semantics`
- `service_catalog_semantics`
- `material_catalog_semantics`
- `operation_catalog_semantics`
- `aliases`
- `templates`
- `technical_cards`
- `contract_definitions`
- `ui_design_system_publication`
- `shared_ui_component_catalog`
- `ui_component_version_and_adoption_metadata`

## Must not own

- `operational_orders`
- `client_database`
- `accounting_truth`
- `production_runtime`
- `crm_workflow`
- `domain_business_rules_outside_library_semantics`

## Next focus

- `Canonical Product/Service ID and Alias Governance.`
- `Define ambiguity routing and approval lifecycle.`
- `Prepare contract registry direction.`
- `Publish the first versioned shared UI component/catalog surface.`
- `Strengthen reusable semantic/capability discoverability without absorbing domain ownership.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
