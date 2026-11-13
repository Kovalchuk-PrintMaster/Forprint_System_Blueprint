# ForPrint Accounting Registry Service

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_accounting_registry_service`

## Type

`accounting_registry`

## Status

`active_development`

## Role

Бухгалтерський і 1С-сумісний контур: рахунки, оплати, акти, бухгалтерські документи, експорт або синхронізація з 1С.

## Owns

- `invoice`
- `payment_status`
- `accounting_document`
- `one_c_sync_event`

## Consumes

- `order`
- `client`
- `quote_draft`

## Provides

- `invoice`
- `payment_status`
- `accounting_export`

## Must not own

- `material_catalog`
- `prepress_file`
- `print_ready_file`

## Incoming data flows

- `operational_order_to_accounting`: `forprint_operations_control_registry` → `forprint_accounting_registry_service` via `operations_control_registry_to_accounting_order.v1`; objects: `order`, `client`, `quote_draft`; status: `planned`; criticality: `high`
- `integration_gateway_routes_to_accounting`: `forprint_integration_gateway` → `forprint_accounting_registry_service` via `integration_gateway_to_accounting_invoice_request.v1`; objects: `routed_module_request`, `quote_draft`, `client`, `order`, `correlation_context`; status: `planned`; criticality: `high`

## Outgoing data flows

- `accounting_financial_status_to_crm`: `forprint_accounting_registry_service` → `forprint_crm` via `accounting_to_crm_financial_status.v1`; objects: `invoice`, `payment_status`, `accounting_document`; status: `active_development`; criticality: `high`
- `accounting_export_to_one_c`: `forprint_accounting_registry_service` → `external_1c` via `accounting_to_one_c_export.v1`; objects: `accounting_export`, `one_c_sync_event`; status: `planned`; criticality: `high`

## Consumed contracts

- `operations_control_registry_to_accounting_order.v1`: provider `forprint_operations_control_registry`, consumer `forprint_accounting_registry_service`, status `planned`; objects: `order`, `client`, `quote_draft`
- `integration_gateway_to_accounting_invoice_request.v1`: provider `forprint_integration_gateway`, consumer `forprint_accounting_registry_service`, status `planned`; objects: `routed_module_request`, `quote_draft`, `client`, `order`, `correlation_context`

## Provided contracts

- `accounting_to_crm_financial_status.v1`: provider `forprint_accounting_registry_service`, consumer `forprint_crm`, status `active_development`; objects: `invoice`, `payment_status`, `accounting_document`
- `accounting_to_one_c_export.v1`: provider `forprint_accounting_registry_service`, consumer `external_1c`, status `planned`; objects: `accounting_export`, `one_c_sync_event`

## Prompt for module chat

Ти працюєш над модулем `forprint_accounting_registry_service` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_accounting_registry_service/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
