# ForPrint Project Inspector

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_project_inspector`

## Type

`architecture_compliance_checker`

## Status

`planned`

## Role

Перевіряє відповідність реальних модулів Blueprint: manifests, reports, контракти, інтеграційні розриви, architecture drift.

## Owns

- `inspection_report`

## Consumes

- `module_definition`
- `contract_definition`
- `data_flow_definition`
- `module_manifest`
- `module_status_report`

## Provides

- `architecture_health_report`
- `integration_gap_report`

## Must not own

- `module_definition`
- `client`
- `order`

## Incoming data flows

- `blueprint_to_project_inspector`: `forprint_system_blueprint` → `forprint_project_inspector` via `blueprint_to_inspector_architecture.v1`; objects: `module_definition`, `data_flow_definition`, `contract_definition`, `impact_rule`; status: `planned`; criticality: `high`
- `modules_to_project_inspector`: `any_module` → `forprint_project_inspector` via `module_to_inspector_manifest.v1`; objects: `module_manifest`, `module_status_report`; status: `planned`; criticality: `high`
- `integration_gateway_audit_to_inspector`: `forprint_integration_gateway` → `forprint_project_inspector` via `integration_gateway_to_inspector_audit.v1`; objects: `integration_audit_event`, `validation_error`, `security_filter_event`; status: `planned`; criticality: `medium`

## Outgoing data flows

- Немає.

## Consumed contracts

- `blueprint_to_inspector_architecture.v1`: provider `forprint_system_blueprint`, consumer `forprint_project_inspector`, status `planned`; objects: `module_definition`, `data_flow_definition`, `contract_definition`, `impact_rule`
- `module_to_inspector_manifest.v1`: provider `any_module`, consumer `forprint_project_inspector`, status `planned`; objects: `module_manifest`, `module_status_report`
- `integration_gateway_to_inspector_audit.v1`: provider `forprint_integration_gateway`, consumer `forprint_project_inspector`, status `planned`; objects: `integration_audit_event`, `validation_error`, `security_filter_event`

## Provided contracts

- Немає.

## Prompt for module chat

Ти працюєш над модулем `forprint_project_inspector` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_project_inspector/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
