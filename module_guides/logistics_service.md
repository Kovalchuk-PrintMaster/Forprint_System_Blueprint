# ForPrint Logistics Service

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`logistics_service`

## Type

`delivery_and_logistics_service`

## Status

`planned`

## Role

Доставка і логістика: Нова пошта, Укрпошта, таксі, кур'єри, статуси відправок, інтеграційні ключі і адаптери.

## Owns

- `delivery_request`
- `delivery_status`
- `logistics_provider_adapter`

## Consumes

- `order`
- `client`
- `package_description`

## Provides

- `delivery_status`
- `delivery_label`
- `delivery_cost_estimate`

## Must not own

- `invoice`
- `material_catalog`
- `order`

## Incoming data flows

- `crm_delivery_request_to_logistics`: `forprint_crm` → `logistics_service` via `crm_to_logistics_delivery.v1`; objects: `business_command`, `delivery_request`; status: `planned`; criticality: `medium`

## Outgoing data flows

- `logistics_status_to_crm`: `logistics_service` → `forprint_crm` via `logistics_to_crm_delivery_status.v1`; objects: `delivery_status`, `delivery_label`, `delivery_cost_estimate`; status: `planned`; criticality: `medium`

## Consumed contracts

- `crm_to_logistics_delivery.v1`: provider `forprint_crm`, consumer `logistics_service`, status `planned`; objects: `business_command`, `delivery_request`

## Provided contracts

- `logistics_to_crm_delivery_status.v1`: provider `logistics_service`, consumer `forprint_crm`, status `planned`; objects: `delivery_status`, `delivery_label`, `delivery_cost_estimate`

## Prompt for module chat

Ти працюєш над модулем `logistics_service` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/logistics_service/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
