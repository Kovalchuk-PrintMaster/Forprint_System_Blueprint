# ForPrint Integration Gateway

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_integration_gateway`

## Type

`integration_gateway_and_message_router`

## Status

`planned`

## Role

Транспортно-контрактний шар між модулями: приймає запити, перевіряє їх за контрактами, нормалізує payload, додає correlation/idempotency context, маршрутизує до цільових модулів і повертає стандартизовані відповіді або помилки. Не приймає бізнес-рішень і не володіє предметними даними.

## Owns

- `integration_request`
- `routed_module_request`
- `integration_response`
- `validation_error`
- `routing_rule`
- `correlation_context`
- `idempotency_record`
- `integration_audit_event`
- `security_filter_event`

## Consumes

- `contract_definition`
- `data_flow_definition`
- `website_request`
- `client_request`
- `workflow_command`
- `business_command`
- `quote_draft`
- `price_breakdown`
- `material_consumption_estimate`

## Provides

- `routed_module_request`
- `integration_response`
- `validation_error`
- `integration_audit_event`
- `security_filter_event`

## Must not own

- `client`
- `order`
- `quote_draft`
- `invoice`
- `payment_status`
- `material_catalog`
- `material_stock`
- `prepress_file`
- `print_ready_file`
- `business_workflow_state`

## Incoming data flows

- `blueprint_contracts_to_integration_gateway`: `forprint_system_blueprint` → `forprint_integration_gateway` via `blueprint_to_integration_gateway_contracts.v1`; objects: `contract_definition`, `data_flow_definition`, `routing_rule`; status: `planned`; criticality: `high`
- `website_requests_to_integration_gateway`: `website` → `forprint_integration_gateway` via `website_to_integration_gateway_request.v1`; objects: `website_request`, `integration_request`; status: `planned`; criticality: `high`
- `telegram_requests_to_integration_gateway`: `telegram_bot` → `forprint_integration_gateway` via `telegram_to_integration_gateway_request.v1`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`, `integration_request`; status: `planned`; criticality: `high`
- `crm_commands_to_integration_gateway`: `forprint_crm` → `forprint_integration_gateway` via `crm_to_integration_gateway_command.v1`; objects: `business_command`, `workflow_decision`, `integration_request`; status: `planned`; criticality: `high`
- `calculator_result_to_integration_gateway`: `calculator_engine` → `forprint_integration_gateway` via `calculator_to_integration_gateway_result.v1`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`, `integration_response`; status: `planned`; criticality: `high`

## Outgoing data flows

- `integration_gateway_routes_to_calculator`: `forprint_integration_gateway` → `calculator_engine` via `integration_gateway_to_calculator_request.v1`; objects: `routed_module_request`, `product_configuration`, `correlation_context`; status: `planned`; criticality: `high`
- `integration_gateway_routes_to_operations_control_registry`: `forprint_integration_gateway` → `forprint_operations_control_registry` via `integration_gateway_to_operations_control_registry_command.v1`; objects: `routed_module_request`, `quote_draft`, `product_configuration`, `correlation_context`; status: `planned`; criticality: `high`
- `integration_gateway_routes_to_warehouse`: `forprint_integration_gateway` → `warehouse_service` via `integration_gateway_to_warehouse_reservation.v1`; objects: `routed_module_request`, `material_consumption_estimate`, `correlation_context`; status: `planned`; criticality: `high`
- `integration_gateway_routes_to_accounting`: `forprint_integration_gateway` → `forprint_accounting_registry_service` via `integration_gateway_to_accounting_invoice_request.v1`; objects: `routed_module_request`, `quote_draft`, `client`, `order`, `correlation_context`; status: `planned`; criticality: `high`
- `integration_gateway_status_to_crm`: `forprint_integration_gateway` → `forprint_crm` via `integration_gateway_to_crm_status.v1`; objects: `integration_response`, `validation_error`, `integration_audit_event`; status: `planned`; criticality: `medium`
- `integration_gateway_audit_to_inspector`: `forprint_integration_gateway` → `forprint_project_inspector` via `integration_gateway_to_inspector_audit.v1`; objects: `integration_audit_event`, `validation_error`, `security_filter_event`; status: `planned`; criticality: `medium`

## Consumed contracts

- `blueprint_to_integration_gateway_contracts.v1`: provider `forprint_system_blueprint`, consumer `forprint_integration_gateway`, status `planned`; objects: `contract_definition`, `data_flow_definition`, `routing_rule`
- `website_to_integration_gateway_request.v1`: provider `website`, consumer `forprint_integration_gateway`, status `planned`; objects: `website_request`, `integration_request`
- `telegram_to_integration_gateway_request.v1`: provider `telegram_bot`, consumer `forprint_integration_gateway`, status `planned`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`, `integration_request`
- `crm_to_integration_gateway_command.v1`: provider `forprint_crm`, consumer `forprint_integration_gateway`, status `planned`; objects: `business_command`, `workflow_decision`, `integration_request`
- `calculator_to_integration_gateway_result.v1`: provider `calculator_engine`, consumer `forprint_integration_gateway`, status `planned`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`, `integration_response`

## Provided contracts

- `integration_gateway_to_calculator_request.v1`: provider `forprint_integration_gateway`, consumer `calculator_engine`, status `planned`; objects: `routed_module_request`, `product_configuration`, `correlation_context`
- `integration_gateway_to_operations_control_registry_command.v1`: provider `forprint_integration_gateway`, consumer `forprint_operations_control_registry`, status `planned`; objects: `routed_module_request`, `quote_draft`, `product_configuration`, `correlation_context`
- `integration_gateway_to_warehouse_reservation.v1`: provider `forprint_integration_gateway`, consumer `warehouse_service`, status `planned`; objects: `routed_module_request`, `material_consumption_estimate`, `correlation_context`
- `integration_gateway_to_accounting_invoice_request.v1`: provider `forprint_integration_gateway`, consumer `forprint_accounting_registry_service`, status `planned`; objects: `routed_module_request`, `quote_draft`, `client`, `order`, `correlation_context`
- `integration_gateway_to_crm_status.v1`: provider `forprint_integration_gateway`, consumer `forprint_crm`, status `planned`; objects: `integration_response`, `validation_error`, `integration_audit_event`
- `integration_gateway_to_inspector_audit.v1`: provider `forprint_integration_gateway`, consumer `forprint_project_inspector`, status `planned`; objects: `integration_audit_event`, `validation_error`, `security_filter_event`

## Prompt for module chat

Ти працюєш над модулем `forprint_integration_gateway` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_integration_gateway/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
