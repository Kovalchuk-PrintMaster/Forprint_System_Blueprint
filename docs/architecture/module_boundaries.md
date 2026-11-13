# ForPrint Module Boundaries

## Status

Current human-readable boundary guide.

Canonical module definitions are in `machine/modules.yaml`; stable module IDs are in
`machine/module_identity_registry.yaml`.

## Core rule

A module should own one bounded responsibility and must not absorb another module's
canonical domain simply because local implementation would be convenient.

## Key boundaries

| Module | Primary role | Must not silently become |
| --- | --- | --- |
| `forprint_system_blueprint` | architecture and coordination truth | runtime business executor |
| `forprint_project_inspector` | architecture compliance review | architecture author or business orchestrator |
| `forprint_integration_gateway` | validation/transport/routing safety | CRM, catalog owner or business database |
| `forprint_crm` | business orchestration, operator UI and analytics | physical owner of all business truth |
| `forprint_operations_control_registry` | operational client/order/task/status truth | catalog/calculation/accounting rule owner |
| `forprint_accounting_registry_service` | invoice/payment/accounting/1C contour | main operational order registry |
| `forprint_library` | semantic/catalog/reference truth | order/payment/runtime execution store |
| `calculator_engine` | calculation, quote and consumption-estimate logic | canonical material/product catalog |
| `forprint_prepress_hub` | file/prepress preparation and artifacts | order workflow owner |
| `warehouse_service` | physical stock, reservations and movements | semantic material catalog |
| `logistics_service` | delivery/tracking truth | order or CRM owner |
| `telegram_bot`, `website`, `mobile_app` | interaction channels | canonical business-data owners |

## Ownership is not presentation

A CRM screen can show an order without owning the order. A Telegram workflow can initiate
an action without owning the resulting record. Calculator can consume catalog data
without becoming the catalog authority.

The current owner/consumer mapping is machine-readable in:

- `machine/data_objects.yaml`
- `machine/ownership.yaml`
- `machine/contracts.yaml`
- `machine/data_flows.yaml`

## Boundary changes

A proposed boundary change is an architecture change, not a local convenience refactor.

It should be routed through Blueprint governance and reflected first in the relevant
canonical machine/standard sources. Generated module guides can then be regenerated.

## Historical note

The former `human/module_boundaries.md`, `human/system_control_model.md` and related early
documents are retained as historical source material under
`coordination/internal_work/blueprint/legacy_alignment/`. They are no longer parallel
current boundary authorities.
