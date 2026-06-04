# Module Policy — ForPrint Integration Gateway

## Module ID

```text
forprint_integration_gateway
```

## Priority

```text
hold
```

## Development status

```text
paused_after_v0_2
```

## Strategic role

Future runtime validation, normalization, routing, idempotency and correlation layer between channels, CRM and internal modules.

## Main goals

- `Keep transport/validation boundary ready.`
- `Avoid business workflow ownership.`
- `Wait until real runtime handoff is needed.`

## Owns

- `integration_request_envelope`
- `integration_response_envelope`
- `routing_rule`
- `validation_error`
- `idempotency_boundary`
- `correlation_context`

## Must not own

- `business_workflow_decisions`
- `client_registry`
- `order_registry`
- `catalog_truth`
- `accounting_truth`
- `crm_dashboard`

## Next focus

- `Hold active development.`
- `Re-activate when Calculator/Operational Registry handoff needs runtime transport.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
