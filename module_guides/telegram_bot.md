# ForPrint Telegram Bot

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`telegram_bot`

## Type

`client_interface_and_action_runner`

## Status

`active_development`

## Role

Клієнтський інтерфейс, оператор сценаріїв і AI-assisted виконавець дій через дозволені контракти інших модулів. Не є джерелом правди.

## Owns

- `telegram_dialog_state`
- `bot_action_log`

## Consumes

- `client_context`
- `order_context`
- `quote_draft`
- `prepress_report`
- `delivery_status`

## Provides

- `client_request`
- `workflow_command`
- `ai_assisted_task_request`

## Must not own

- `material_catalog`
- `canonical_client_registry`
- `canonical_order_registry`
- `invoice`
- `payment_status`

## Incoming data flows

- Немає.

## Outgoing data flows

- `telegram_requests_to_crm`: `telegram_bot` → `forprint_crm` via `telegram_to_crm_request.v1`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`; status: `active_development`; criticality: `high`
- `telegram_requests_to_integration_gateway`: `telegram_bot` → `forprint_integration_gateway` via `telegram_to_integration_gateway_request.v1`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`, `integration_request`; status: `planned`; criticality: `high`

## Consumed contracts

- Немає.

## Provided contracts

- `telegram_to_crm_request.v1`: provider `telegram_bot`, consumer `forprint_crm`, status `active_development`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`
- `telegram_to_integration_gateway_request.v1`: provider `telegram_bot`, consumer `forprint_integration_gateway`, status `planned`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`, `integration_request`

## Prompt for module chat

Ти працюєш над модулем `telegram_bot` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/telegram_bot/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
