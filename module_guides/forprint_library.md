# ForPrint Library

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_library`

## Type

`canonical_reference_library`

## Status

`active_development`

## Role

Джерело правди для довідників, матеріалів, технічних карт, шаблонів документів, номенклатури, режимів друку, машинних можливостей.

## Owns

- `material_catalog`
- `product_catalog`
- `machine_capability`
- `print_mode`
- `document_template`
- `technical_card`

## Consumes

- Немає явно зафіксованих пунктів.

## Provides

- `material_catalog`
- `product_catalog`
- `machine_capability`
- `print_mode`
- `document_template`

## Must not own

- `client`
- `order`
- `invoice`
- `payment_status`

## Incoming data flows

- Немає.

## Outgoing data flows

- `library_catalogs_to_calculator`: `forprint_library` → `calculator_engine` via `library_to_calculator_catalog.v1`; objects: `material_catalog`, `product_catalog`, `machine_capability`, `print_mode`; status: `active_development`; criticality: `high`
- `library_capabilities_to_prepress`: `forprint_library` → `forprint_prepress_hub` via `library_to_prepress_capabilities.v1`; objects: `material_catalog`, `machine_capability`, `print_mode`; status: `active_development`; criticality: `high`
- `library_materials_to_warehouse`: `forprint_library` → `warehouse_service` via `library_to_warehouse_materials.v1`; objects: `material_catalog`; status: `planned`; criticality: `high`

## Consumed contracts

- Немає.

## Provided contracts

- `library_to_calculator_catalog.v1`: provider `forprint_library`, consumer `calculator_engine`, status `active_development`; objects: `material_catalog`, `product_catalog`, `machine_capability`, `print_mode`
- `library_to_prepress_capabilities.v1`: provider `forprint_library`, consumer `forprint_prepress_hub`, status `active_development`; objects: `material_catalog`, `machine_capability`, `print_mode`
- `library_to_warehouse_materials.v1`: provider `forprint_library`, consumer `warehouse_service`, status `planned`; objects: `material_catalog`

## Prompt for module chat

Ти працюєш над модулем `forprint_library` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_library/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
