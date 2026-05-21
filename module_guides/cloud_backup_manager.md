# Cloud Backup Manager

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`cloud_backup_manager`

## Type

`backup_service`

## Status

`active_development`

## Role

Резервне копіювання локальних і хмарних даних: бази даних, файли клієнтів, архіви, конфігурації, контроль наявності backup-знімків.

## Owns

- `backup_plan`
- `backup_snapshot`
- `backup_inventory`

## Consumes

- `backup_source_descriptor`

## Provides

- `backup_status_report`
- `backup_inventory`

## Must not own

- `client`
- `order`
- `invoice`

## Incoming data flows

- Немає.

## Outgoing data flows

- `backup_status_to_crm`: `cloud_backup_manager` → `forprint_crm` via `backup_to_crm_status.v1`; objects: `backup_status_report`, `backup_inventory`; status: `planned`; criticality: `medium`

## Consumed contracts

- Немає.

## Provided contracts

- `backup_to_crm_status.v1`: provider `cloud_backup_manager`, consumer `forprint_crm`, status `planned`; objects: `backup_status_report`, `backup_inventory`

## Prompt for module chat

Ти працюєш над модулем `cloud_backup_manager` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/cloud_backup_manager/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
