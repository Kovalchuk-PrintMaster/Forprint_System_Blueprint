# Module Policy — ForPrint CRM

## Module ID

```text
forprint_crm
```

## Priority

```text
p2
```

## Development status

```text
planned_or_alignment_needed
```

## Strategic role

Future human-facing dashboard, business workflow coordination and analytics interface.

## Main goals

- `Provide human UI for workflow coordination.`
- `Show dashboards and analytics.`
- `Help operators resolve ambiguous cases.`
- `Avoid becoming physical database owner.`

## Owns

- `human_dashboard`
- `workflow_coordination_ui`
- `operator_decision_views`
- `analytics_views`

## Must not own

- `internal_forprint_db`
- `canonical_client_registry`
- `calculator_logic`
- `accounting_truth`
- `catalog_truth`

## Next focus

- `Keep planned/alignment status.`
- `Activate after core data and Calculator outputs are clearer.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
