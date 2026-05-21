# ForPrint Website

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`website`

## Type

`public_and_client_web_interface`

## Status

`existing_basic`

## Role

Публічний сайт і майбутній клієнтський веб-інтерфейс. Має використовувати CRM / registry / calculator / prepress через адаптери, а не тримати дубльовану правду.

## Owns

- `website_content`
- `public_product_page`

## Consumes

- `product_catalog`
- `client_context`
- `order_context`
- `quote_draft`

## Provides

- `website_request`

## Must not own

- `canonical_client_registry`
- `canonical_order_registry`
- `material_catalog`

## Incoming data flows

- Немає.

## Outgoing data flows

- `website_requests_to_crm`: `website` → `forprint_crm` via `website_to_crm_request.v1`; objects: `website_request`; status: `planned`; criticality: `medium`
- `website_requests_to_integration_gateway`: `website` → `forprint_integration_gateway` via `website_to_integration_gateway_request.v1`; objects: `website_request`, `integration_request`; status: `planned`; criticality: `high`

## Consumed contracts

- Немає.

## Provided contracts

- `website_to_crm_request.v1`: provider `website`, consumer `forprint_crm`, status `planned`; objects: `website_request`
- `website_to_integration_gateway_request.v1`: provider `website`, consumer `forprint_integration_gateway`, status `planned`; objects: `website_request`, `integration_request`

## Prompt for module chat

Ти працюєш над модулем `website` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/website/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
