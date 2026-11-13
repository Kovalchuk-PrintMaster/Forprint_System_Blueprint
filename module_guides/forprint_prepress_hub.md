# ForPrint Prepress Hub

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_prepress_hub`

## Type

`prepress_file_service`

## Status

`active_development`

## Role

Прийом, аналіз і підготовка файлів до друку: перевірка готовності, автоматична обробка, прев'ю, print-ready файли.

## Owns

- `prepress_file`
- `prepress_report`
- `print_ready_file`
- `file_preview`

## Consumes

- `order_context`
- `material_catalog`
- `machine_capability`
- `print_mode`

## Provides

- `prepress_report`
- `print_ready_file`
- `file_preview`

## Must not own

- `client`
- `invoice`
- `material_stock`

## Incoming data flows

- `library_capabilities_to_prepress`: `forprint_library` → `forprint_prepress_hub` via `library_to_prepress_capabilities.v1`; objects: `material_catalog`, `machine_capability`, `print_mode`; status: `active_development`; criticality: `high`
- `operational_order_context_to_prepress`: `forprint_operations_control_registry` → `forprint_prepress_hub` via `operations_control_registry_to_prepress_order_context.v1`; objects: `order_context`; status: `planned`; criticality: `high`

## Outgoing data flows

- `prepress_report_to_crm`: `forprint_prepress_hub` → `forprint_crm` via `prepress_to_crm_report.v1`; objects: `prepress_report`, `file_preview`, `print_ready_file`; status: `active_development`; criticality: `high`

## Consumed contracts

- `library_to_prepress_capabilities.v1`: provider `forprint_library`, consumer `forprint_prepress_hub`, status `active_development`; objects: `material_catalog`, `machine_capability`, `print_mode`
- `operations_control_registry_to_prepress_order_context.v1`: provider `forprint_operations_control_registry`, consumer `forprint_prepress_hub`, status `planned`; objects: `order_context`

## Provided contracts

- `prepress_to_crm_report.v1`: provider `forprint_prepress_hub`, consumer `forprint_crm`, status `active_development`; objects: `prepress_report`, `file_preview`, `print_ready_file`

## Prompt for module chat

Ти працюєш над модулем `forprint_prepress_hub` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_prepress_hub/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
