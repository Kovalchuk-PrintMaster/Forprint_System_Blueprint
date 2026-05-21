# ForPrint CRM

> Generated from `machine/*.yaml`. Не редагувати вручну як джерело правди; правки вносити в YAML.

## Module ID

`forprint_crm`

## Type

`business_orchestration_ui`

## Status

`planned`

## Role

Бізнес-диригент, людський інтерфейс, прикладний оркестратор процесів, аналітика, звіти, контроль заявок і статусів. Не є фізичним сховищем усіх клієнтів і замовлень.

## Owns

- `crm_dashboard_view`
- `business_workflow_state`
- `management_report`

## Consumes

- `client`
- `order`
- `quote_draft`
- `prepress_report`
- `invoice`
- `payment_status`
- `material_reservation`
- `delivery_status`

## Provides

- `business_command`
- `human_dashboard`
- `workflow_decision`

## Must not own

- `canonical_client_registry`
- `canonical_order_registry`
- `material_catalog`
- `accounting_document`
- `print_ready_file`

## Incoming data flows

- `calculator_quote_to_crm`: `calculator_engine` → `forprint_crm` via `calculator_to_crm_quote.v1`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`; status: `active_development`; criticality: `high`
- `prepress_report_to_crm`: `forprint_prepress_hub` → `forprint_crm` via `prepress_to_crm_report.v1`; objects: `prepress_report`, `file_preview`, `print_ready_file`; status: `active_development`; criticality: `high`
- `accounting_financial_status_to_crm`: `accounting_registry_service` → `forprint_crm` via `accounting_to_crm_financial_status.v1`; objects: `invoice`, `payment_status`, `accounting_document`; status: `active_development`; criticality: `high`
- `telegram_requests_to_crm`: `telegram_bot` → `forprint_crm` via `telegram_to_crm_request.v1`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`; status: `active_development`; criticality: `high`
- `website_requests_to_crm`: `website` → `forprint_crm` via `website_to_crm_request.v1`; objects: `website_request`; status: `planned`; criticality: `medium`
- `warehouse_status_to_crm`: `warehouse_service` → `forprint_crm` via `warehouse_to_crm_inventory_status.v1`; objects: `material_stock`, `material_reservation`, `inventory_availability_report`; status: `planned`; criticality: `high`
- `logistics_status_to_crm`: `logistics_service` → `forprint_crm` via `logistics_to_crm_delivery_status.v1`; objects: `delivery_status`, `delivery_label`, `delivery_cost_estimate`; status: `planned`; criticality: `medium`
- `backup_status_to_crm`: `cloud_backup_manager` → `forprint_crm` via `backup_to_crm_status.v1`; objects: `backup_status_report`, `backup_inventory`; status: `planned`; criticality: `medium`
- `integration_gateway_status_to_crm`: `forprint_integration_gateway` → `forprint_crm` via `integration_gateway_to_crm_status.v1`; objects: `integration_response`, `validation_error`, `integration_audit_event`; status: `planned`; criticality: `medium`

## Outgoing data flows

- `crm_commands_operational_registry`: `forprint_crm` → `forprint_operational_registry` via `crm_to_operational_registry_command.v1`; objects: `business_command`, `workflow_decision`; status: `planned`; criticality: `high`
- `crm_reservation_request_to_warehouse`: `forprint_crm` → `warehouse_service` via `crm_to_warehouse_reservation.v1`; objects: `business_command`, `material_consumption_estimate`; status: `planned`; criticality: `high`
- `crm_delivery_request_to_logistics`: `forprint_crm` → `logistics_service` via `crm_to_logistics_delivery.v1`; objects: `business_command`, `delivery_request`; status: `planned`; criticality: `medium`
- `crm_commands_to_integration_gateway`: `forprint_crm` → `forprint_integration_gateway` via `crm_to_integration_gateway_command.v1`; objects: `business_command`, `workflow_decision`, `integration_request`; status: `planned`; criticality: `high`

## Consumed contracts

- `calculator_to_crm_quote.v1`: provider `calculator_engine`, consumer `forprint_crm`, status `active_development`; objects: `quote_draft`, `price_breakdown`, `material_consumption_estimate`
- `prepress_to_crm_report.v1`: provider `forprint_prepress_hub`, consumer `forprint_crm`, status `active_development`; objects: `prepress_report`, `file_preview`, `print_ready_file`
- `accounting_to_crm_financial_status.v1`: provider `accounting_registry_service`, consumer `forprint_crm`, status `active_development`; objects: `invoice`, `payment_status`, `accounting_document`
- `telegram_to_crm_request.v1`: provider `telegram_bot`, consumer `forprint_crm`, status `active_development`; objects: `client_request`, `workflow_command`, `ai_assisted_task_request`
- `website_to_crm_request.v1`: provider `website`, consumer `forprint_crm`, status `planned`; objects: `website_request`
- `warehouse_to_crm_inventory_status.v1`: provider `warehouse_service`, consumer `forprint_crm`, status `planned`; objects: `material_stock`, `material_reservation`, `inventory_availability_report`
- `logistics_to_crm_delivery_status.v1`: provider `logistics_service`, consumer `forprint_crm`, status `planned`; objects: `delivery_status`, `delivery_label`, `delivery_cost_estimate`
- `backup_to_crm_status.v1`: provider `cloud_backup_manager`, consumer `forprint_crm`, status `planned`; objects: `backup_status_report`, `backup_inventory`
- `integration_gateway_to_crm_status.v1`: provider `forprint_integration_gateway`, consumer `forprint_crm`, status `planned`; objects: `integration_response`, `validation_error`, `integration_audit_event`

## Provided contracts

- `crm_to_operational_registry_command.v1`: provider `forprint_crm`, consumer `forprint_operational_registry`, status `planned`; objects: `business_command`, `workflow_decision`
- `crm_to_warehouse_reservation.v1`: provider `forprint_crm`, consumer `warehouse_service`, status `planned`; objects: `business_command`, `material_consumption_estimate`
- `crm_to_logistics_delivery.v1`: provider `forprint_crm`, consumer `logistics_service`, status `planned`; objects: `business_command`, `delivery_request`
- `crm_to_integration_gateway_command.v1`: provider `forprint_crm`, consumer `forprint_integration_gateway`, status `planned`; objects: `business_command`, `workflow_decision`, `integration_request`

## Prompt for module chat

Ти працюєш над модулем `forprint_crm` у системі ForPrint. Твоя роль, межі відповідальності, вхідні й вихідні дані мають відповідати цьому guide. Якщо поточна реалізація модуля конфліктує з цим описом, не змінюй архітектуру самостійно — сформуй запит до ForPrint System Blueprint через `coordination/incoming_requests/forprint_crm/new/`.

## Required discipline

1. Не брати у власність чужі data objects.
2. Не вигадувати неузгоджені контракти.
3. Якщо потрібен новий контракт — сформувати incoming request до Blueprint.
4. Після завершеного проміжного кроку запускати тести свого модуля.
5. У майбутньому підтримувати `forprint_module_manifest.yaml`.
