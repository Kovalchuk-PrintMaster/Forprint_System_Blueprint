# ForPrint Warehouse Service

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`warehouse_service`

## Type

`warehouse_and_inventory_service`

## Status

`planned`

## Role

Склад: залишки, резервування, рух матеріалів, списання, мінімальні залишки, заявки на закупівлю.

## Owns

- `material_stock`
- `material_reservation`
- `inventory_movement`
- `purchase_request`

## Consumes

- `material_catalog`
- `order`
- `material_consumption_estimate`

## Provides

- `material_stock`
- `material_reservation`
- `inventory_availability_report`

## Must not own

- `material_catalog`
- `invoice`
- `client`

## Incoming data flows

- `library_materials_to_warehouse`: `forprint_library` → `warehouse_service` via `library_to_warehouse_materials.v1`; objects: `material_catalog`; status: `planned`; criticality: `high`
- `crm_reservation_request_to_warehouse`: `forprint_crm` → `warehouse_service` via `crm_to_warehouse_reservation.v1`; objects: `business_command`, `material_consumption_estimate`; status: `planned`; criticality: `high`
- `integration_gateway_routes_to_warehouse`: `forprint_integration_gateway` → `warehouse_service` via `integration_gateway_to_warehouse_reservation.v1`; objects: `routed_module_request`, `material_consumption_estimate`, `correlation_context`; status: `planned`; criticality: `high`

## Outgoing data flows

- `warehouse_status_to_crm`: `warehouse_service` → `forprint_crm` via `warehouse_to_crm_inventory_status.v1`; objects: `material_stock`, `material_reservation`, `inventory_availability_report`; status: `planned`; criticality: `high`

## Consumed contracts

- `library_to_warehouse_materials.v1`: provider `forprint_library`, consumer `warehouse_service`, status `planned`; objects: `material_catalog`
- `crm_to_warehouse_reservation.v1`: provider `forprint_crm`, consumer `warehouse_service`, status `planned`; objects: `business_command`, `material_consumption_estimate`
- `integration_gateway_to_warehouse_reservation.v1`: provider `forprint_integration_gateway`, consumer `warehouse_service`, status `planned`; objects: `routed_module_request`, `material_consumption_estimate`, `correlation_context`

## Provided contracts

- `warehouse_to_crm_inventory_status.v1`: provider `warehouse_service`, consumer `forprint_crm`, status `planned`; objects: `material_stock`, `material_reservation`, `inventory_availability_report`

## Prompt for module chat

Ти працюєш над модулем `warehouse_service` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/warehouse_service/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
