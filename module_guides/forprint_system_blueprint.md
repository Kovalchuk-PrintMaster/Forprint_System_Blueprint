# ForPrint System Blueprint

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_system_blueprint`

## Type

`architecture_truth_layer`

## Status

`active_development`

## Role

Верхній шар архітектурної правди: модулі, межі, дані, контракти, потоки, правила впливу змін, module guides.

## Owns

- `architecture_decision`
- `module_definition`
- `data_flow_definition`
- `contract_definition`
- `impact_rule`

## Consumes

- Немає явно зафіксованих пунктів.

## Provides

- `module_guide`
- `mermaid_diagram`
- `architecture_change_prompt`

## Must not own

- `client`
- `order`
- `invoice`
- `material_stock`

## Incoming data flows

- Немає.

## Outgoing data flows

- `blueprint_generates_module_guides`: `forprint_system_blueprint` → `any_module` via `blueprint_to_module_guide.v1`; objects: `module_guide`, `architecture_change_prompt`; status: `active_development`; criticality: `high`
- `blueprint_to_project_inspector`: `forprint_system_blueprint` → `forprint_project_inspector` via `blueprint_to_inspector_architecture.v1`; objects: `module_definition`, `data_flow_definition`, `contract_definition`, `impact_rule`; status: `planned`; criticality: `high`
- `blueprint_contracts_to_integration_gateway`: `forprint_system_blueprint` → `forprint_integration_gateway` via `blueprint_to_integration_gateway_contracts.v1`; objects: `contract_definition`, `data_flow_definition`, `routing_rule`; status: `planned`; criticality: `high`

## Consumed contracts

- Немає.

## Provided contracts

- `blueprint_to_module_guide.v1`: provider `forprint_system_blueprint`, consumer `any_module`, status `active_development`; objects: `module_guide`, `architecture_change_prompt`
- `blueprint_to_inspector_architecture.v1`: provider `forprint_system_blueprint`, consumer `forprint_project_inspector`, status `planned`; objects: `module_definition`, `data_flow_definition`, `contract_definition`, `impact_rule`
- `blueprint_to_integration_gateway_contracts.v1`: provider `forprint_system_blueprint`, consumer `forprint_integration_gateway`, status `planned`; objects: `contract_definition`, `data_flow_definition`, `routing_rule`

## Prompt for module chat

Ти працюєш над модулем `forprint_system_blueprint` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_system_blueprint/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
