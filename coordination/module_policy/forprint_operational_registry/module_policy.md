# Module Policy — ForPrint Operational Registry

## Module ID

```text
forprint_operational_registry
```

## Priority

```text
p1
```

## Development status

```text
reference_ready_storage_ready
```

## Strategic role

Main physical/internal ForPrint DB and operational data custodian.

## Main goals

- `Own internal ForPrint DB storage foundation.`
- `Store ClientAccount, ClientGroup, requests, orders, contacts and operational events.`
- `Provide clean data access for other modules.`
- `Remain 1C-aware and sync-friendly.`

## Owns

- `internal_forprint_db`
- `client_account_records`
- `client_group_records`
- `operational_orders`
- `customer_requests`
- `operational_events`
- `operational_tasks`
- `operational_blockers`
- `logistics_addresses`

## Must not own

- `calculator_logic`
- `canonical_catalog_semantics`
- `one_c_adapter_logic`
- `crm_dashboard`
- `customer_channel_runtime`

## Next focus

- `Core ForPrint Data Model Expansion.`
- `Add ClientAccount / ClientGroup / Contact relationship policy.`
- `Prepare request/order lifecycle for analytics.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
