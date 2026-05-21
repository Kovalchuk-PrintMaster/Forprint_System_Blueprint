# ForPrint Production Runtime Inspector

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`production_runtime_inspector`

## Type

`production_monitoring`

## Status

`future`

## Role

Майбутній інспектор продакшену: контроль живої системи, помилок, деградацій, проблем інтеграції, runtime-подій.

## Owns

- `runtime_health_event`

## Consumes

- `architecture_health_report`
- `module_status_report`

## Provides

- `production_health_report`

## Must not own

- `architecture_decision`

## Incoming data flows

- Немає.

## Outgoing data flows

- Немає.

## Consumed contracts

- Немає.

## Provided contracts

- Немає.

## Prompt for module chat

Ти працюєш над модулем `production_runtime_inspector` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/production_runtime_inspector/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
