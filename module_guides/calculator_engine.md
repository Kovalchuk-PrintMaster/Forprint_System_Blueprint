# ForPrint Calculator Engine

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`calculator_engine`

## Type

`calculation_service`

## Status

`active_development`

## Role

Прикладна математика: калькуляції, попередні кошториси, розрахунок вартості, витрат матеріалів, конфігурацій продукту.

## Owns

- `quote_draft`
- `price_breakdown`
- `material_consumption_estimate`
- `product_configuration`

## Consumes

- `material_catalog`
- `product_catalog`
- `machine_capability`
- `print_mode`
- `client_context`

## Provides

- `quote_draft`
- `price_breakdown`
- `material_consumption_estimate`

## Must not own

- `client`
- `order`
- `invoice`
- `payment_status`
- `prepress_file`

## Incoming data flows

- `library_catalogs_to_calculator`: `forprint_library` → `calculator_engine` via `library_to_calculator_catalog.v1`; objects: `material_catalog`, `product_catalog`, `machine_capability`, `print_mode`; status: `active_development`; criticality: `high`
- `integration_gateway_routes_to_calculator`: `forprint_integration_gateway` → `calculator_engine` via `integration_gateway_to_calculator_request.v1`; objects: `routed_module_request`, `product_configuration`, `correlation_context`; status: `planned`; criticality: `high`

## Outgoing data flows

- `calculator_quote_to_crm`: `calculator_engine` → `forprint_crm` via `calculator_to_crm_quote.v1`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`; status: `active_development`; criticality: `high`
- `calculator_quote_to_operational_registry`: `calculator_engine` → `forprint_operational_registry` via `calculator_to_registry_quote.v1`; objects: `quote_draft`, `product_configuration`; status: `planned`; criticality: `high`
- `calculator_result_to_integration_gateway`: `calculator_engine` → `forprint_integration_gateway` via `calculator_to_integration_gateway_result.v1`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`, `integration_response`; status: `planned`; criticality: `high`

## Consumed contracts

- `library_to_calculator_catalog.v1`: provider `forprint_library`, consumer `calculator_engine`, status `active_development`; objects: `material_catalog`, `product_catalog`, `machine_capability`, `print_mode`
- `integration_gateway_to_calculator_request.v1`: provider `forprint_integration_gateway`, consumer `calculator_engine`, status `planned`; objects: `routed_module_request`, `product_configuration`, `correlation_context`

## Provided contracts

- `calculator_to_crm_quote.v1`: provider `calculator_engine`, consumer `forprint_crm`, status `active_development`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`
- `calculator_to_registry_quote.v1`: provider `calculator_engine`, consumer `forprint_operational_registry`, status `planned`; objects: `quote_draft`, `product_configuration`
- `calculator_to_integration_gateway_result.v1`: provider `calculator_engine`, consumer `forprint_integration_gateway`, status `planned`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`, `integration_response`

## Prompt for module chat

Ти працюєш над модулем `calculator_engine` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/calculator_engine/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
