# ForPrint Operational Registry

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_operational_registry`

## Type

`operational_data_registry`

## Status

`planned`

## Role

Канонічний реєстр операційних бізнес-записів: клієнти, замовлення, взаємодії, робочі статуси, історія виконання.

## Owns

- `client`
- `order`
- `client_interaction`
- `order_status_history`

## Consumes

- `quote_draft`
- `prepress_report`
- `payment_status`
- `delivery_status`

## Provides

- `client`
- `order`
- `order_context`
- `client_history`

## Must not own

- `material_catalog`
- `invoice`
- `machine_capability`

## Incoming data flows

- `calculator_quote_to_operational_registry`: `calculator_engine` → `forprint_operational_registry` via `calculator_to_registry_quote.v1`; objects: `quote_draft`, `product_configuration`; status: `planned`; criticality: `high`
- `crm_commands_operational_registry`: `forprint_crm` → `forprint_operational_registry` via `crm_to_operational_registry_command.v1`; objects: `business_command`, `workflow_decision`; status: `planned`; criticality: `high`
- `integration_gateway_routes_to_operational_registry`: `forprint_integration_gateway` → `forprint_operational_registry` via `integration_gateway_to_operational_registry_command.v1`; objects: `routed_module_request`, `quote_draft`, `product_configuration`, `correlation_context`; status: `planned`; criticality: `high`

## Outgoing data flows

- `operational_order_context_to_prepress`: `forprint_operational_registry` → `forprint_prepress_hub` via `operational_registry_to_prepress_order_context.v1`; objects: `order_context`; status: `planned`; criticality: `high`
- `operational_order_to_accounting`: `forprint_operational_registry` → `accounting_registry_service` via `operational_registry_to_accounting_order.v1`; objects: `order`, `client`, `quote_draft`; status: `planned`; criticality: `high`

## Consumed contracts

- `calculator_to_registry_quote.v1`: provider `calculator_engine`, consumer `forprint_operational_registry`, status `planned`; objects: `quote_draft`, `product_configuration`
- `crm_to_operational_registry_command.v1`: provider `forprint_crm`, consumer `forprint_operational_registry`, status `planned`; objects: `business_command`, `workflow_decision`
- `integration_gateway_to_operational_registry_command.v1`: provider `forprint_integration_gateway`, consumer `forprint_operational_registry`, status `planned`; objects: `routed_module_request`, `quote_draft`, `product_configuration`, `correlation_context`

## Provided contracts

- `operational_registry_to_prepress_order_context.v1`: provider `forprint_operational_registry`, consumer `forprint_prepress_hub`, status `planned`; objects: `order_context`
- `operational_registry_to_accounting_order.v1`: provider `forprint_operational_registry`, consumer `accounting_registry_service`, status `planned`; objects: `order`, `client`, `quote_draft`

## Prompt for module chat

Ти працюєш над модулем `forprint_operational_registry` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_operational_registry/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
