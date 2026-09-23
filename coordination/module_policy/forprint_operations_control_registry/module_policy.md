# Module Policy — ForPrint Operations Control Registry

## Module ID

```text
forprint_operations_control_registry
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

Operational/commercial control registry for ForPrint: owns the operational state and authorized write boundary for orders, obligations, reservations, shortages, incidents, deadlines and cross-module execution context without owning every domain rule or the physical persistence topology.

## Main goals

- `Own the operational data model and authorized write boundary over centrally managed ForPrint persistence.`
- `Store ClientAccount, ClientGroup, requests, orders, contacts and operational events within that boundary.`
- `Provide clean operational state and context access for other modules.`
- `Remain 1C-aware and sync-friendly without mirroring 1C as the internal model.`
- `Use stable Business Partner/Person/Organization and order/job identifiers across domain schemas.`
- `Keep physical PostgreSQL persistence ownership separate from operational semantic/write ownership.`

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
- `stable_business_partner_reference_boundary`
- `stable_order_identity_boundary`

## Must not own

- `calculator_logic`
- `canonical_catalog_semantics`
- `one_c_adapter_logic`
- `crm_dashboard`
- `customer_channel_runtime`
- `physical_postgresql_platform_operations`

## Next focus

- `Core ForPrint Data Model Expansion.`
- `Add ClientAccount / ClientGroup / Contact relationship policy.`
- `Prepare request/order lifecycle for analytics.`
- `Reconcile ClientAccount / ClientGroup concepts with the stable Business Partner identity model.`
- `Attach cross-domain records to stable order_id and job/resource identifiers.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
