# Module Policy — ForPrint Operations Assistant

## Module ID

```text
forprint_operations_assistant
```

## Priority

```text
p2
```

## Development status

```text
planned_concept_bootstrap
```

## Strategic role

Internal operational assistant and low-friction human-to-system surface for physical shop-floor observations, procedures, guided forms and knowledge.

## Main goals

- `Provide contextual operational task/procedure assistance.`
- `Capture structured physical-world observations and exceptions.`
- `Provide a Knowledge Library with text/video procedures.`
- `Provide Guided Forms and approved corporate-template export.`
- `Remain outside canonical accounting/business truth ownership.`

## Owns

- `operations_assistant_interaction_context`
- `guided_form_interaction`
- `knowledge_help_surface`
- `operational_observation_capture`

## Must not own

- `accounting_truth`
- `canonical_order_registry`
- `canonical_catalog_truth`
- `crm_customer_pipeline`
- `unbounded_business_decision_authority`

## Next focus

- `Keep as planned concept while the Blueprint Q-series is completed.`
- `Reconcile full charter/capability/dependency roadmap before systematic implementation.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
