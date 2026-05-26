# ForPrint CRM Alignment Report

report_id: 2026-05-23-forprint-crm-alignment-report
module_id: forprint_crm
source_prompt_id: 2026-05-22-align-crm-with-blueprint
report_status: new
created_at: 2026-05-23
prepared_by: forprint_crm_module_assistant
target_blueprint_version: 0.8.3

Alignment Report: forprint_crm with ForPrint System Blueprint
1. Current CRM role

forprint_crm should remain the business orchestration and human-facing management layer.

Its correct role:

business director / workflow coordinator / human UI / analytics dashboard

CRM should help people see and manage business processes:

- customer/order overview;
- task and workflow visibility;
- dashboard;
- management analytics;
- operator interface;
- business decision interface;
- manual review interface;
- architecture health view based on Project Inspector reports.

CRM may initiate business commands, but it should not directly replace specialized modules or become the physical owner of every business object.

Correct principle:

CRM coordinates and displays.
Specialized registries own canonical truth.
Integration Gateway routes execution.
Project Inspector checks architectural health.
2. Possible overreach zones

The main architectural risk is that CRM may become an all-in-one backend because it has the most visible interface.

Potential overreach zones:

1. CRM duplicates Operational Registry
   Risk: CRM starts physically owning clients, orders, tasks, statuses.

2. CRM duplicates Accounting Registry
   Risk: CRM starts owning invoices, payments, accounting entries, 1C truth.

3. CRM duplicates ForPrint Library
   Risk: CRM starts owning product names, material catalogs, templates, machine capabilities.

4. CRM bypasses Integration Gateway
   Risk: CRM directly calls Prepress, Calculator, Accounting, Telegram, Website, etc.

5. CRM absorbs Project Inspector
   Risk: CRM starts checking module architecture instead of displaying Inspector results.

6. CRM becomes the central database for everything
   Risk: all modules begin depending on CRM as the physical source of truth.

CRM must avoid becoming:

all-in-one backend / universal registry / physical data owner of the whole ecosystem
3. Data CRM should own

CRM should own only the data that belongs specifically to its human-facing and business-management role.

Recommended CRM-owned data:

- dashboard layout settings;
- user-specific views and filters;
- saved report presets;
- CRM UI preferences;
- dashboard widgets configuration;
- management comments / notes attached to displayed entities;
- manual review board configuration;
- business decision drafts;
- user-facing workflow command history;
- CRM-side notification preferences;
- cached dashboard projections, if clearly marked as non-canonical;
- analytics snapshots generated for fast UI/report display.

CRM may also own business coordination records if they are explicitly not canonical operational truth, for example:

- CRM view state;
- operator workspace state;
- internal CRM reminders;
- manager-facing review queues;
- dashboard annotations.

Important: if a record becomes a canonical order/task/payment/invoice/status, ownership should move to the proper registry.

4. Data CRM should only display/read

CRM should consume canonical data from specialized modules.

From forprint_operational_registry

CRM should read/display:

- clients;
- orders;
- order statuses;
- operational tasks;
- operational workflow statuses;
- deadlines;
- responsible users;
- production/order lifecycle state.

CRM may show and filter this data, but should not become the canonical storage for it.

From accounting_registry_service

CRM should read/display:

- invoices;
- payments;
- payment statuses;
- debts;
- prepayments;
- accounting-related order status;
- 1C synchronization state;
- financial document registry.

CRM may show financial summaries, but accounting truth belongs to Accounting Registry.

From forprint_library

CRM should read/display:

- product catalog names;
- material names;
- templates;
- technical document references;
- machine capability references;
- nomenclature references;
- allowed product/material naming.

CRM should not maintain its own independent material/product catalog.

From forprint_project_inspector

CRM should read/display:

- module health;
- architecture drift reports;
- integration gaps;
- stale module reports;
- failed tests;
- module alignment warnings;
- global blueprint review status.

CRM displays Inspector results, but Inspector performs the checks.

From forprint_integration_gateway

CRM should read/display:

- execution results;
- routed command statuses;
- external module response summaries;
- failed command attempts;
- integration error messages.
5. Required contracts

Recommended initial contracts for CRM alignment:

1. operational_registry_to_crm_dashboard_snapshot.v1
   Source: forprint_operational_registry
   Target: forprint_crm
   Purpose: provide clients/orders/tasks/statuses for CRM dashboard.

2. accounting_registry_to_crm_finance_summary.v1
   Source: accounting_registry_service
   Target: forprint_crm
   Purpose: provide invoices/payments/debts/prepayment summaries.

3. library_to_crm_catalog_reference.v1
   Source: forprint_library
   Target: forprint_crm
   Purpose: provide product/material/template naming and references.

4. project_inspector_to_crm_architecture_health.v1
   Source: forprint_project_inspector
   Target: forprint_crm
   Purpose: provide module health, architecture drift, integration gaps.

5. crm_to_integration_gateway_command.v1
   Source: forprint_crm
   Target: forprint_integration_gateway
   Purpose: send business commands without bypassing gateway.

6. integration_gateway_to_crm_command_result.v1
   Source: forprint_integration_gateway
   Target: forprint_crm
   Purpose: return command execution results.

7. crm_dashboard_projection.v1
   Internal CRM contract
   Purpose: define non-canonical cached dashboard/reporting projections.

Important command rule:

CRM should send workflow/execution commands through Integration Gateway,
not directly to specialized modules.

Examples of commands CRM may send through Gateway:

- request invoice creation;
- request prepress preparation;
- request quote recalculation;
- request Telegram notification;
- request order status transition;
- request document generation;
- request external website/order synchronization.
6. Recommended next implementation step

Recommended next step for forprint_crm:

Build CRM as dashboard + reporting + workflow command interface,
not as canonical registry.

First implementation focus:

1. Create CRM project skeleton.
2. Add dashboard/reporting-oriented data models.
3. Add clear non-canonical projection models.
4. Add placeholder adapters/clients for:
   - Operational Registry;
   - Accounting Registry;
   - ForPrint Library;
   - Project Inspector;
   - Integration Gateway.
5. Add documentation file:
   docs/architecture/crm_boundaries.md
6. Add explicit warning in README:
   CRM is not the physical owner of all system data.

The first CRM models should be conservative:

- DashboardWidget
- DashboardLayout
- SavedReport
- ReportSnapshot
- CRMUserNote
- CRMCommandLog
- ExternalModuleStatusProjection

Avoid starting with canonical models like:

- Client
- Order
- Invoice
- Payment
- Material

unless they are explicitly marked as temporary/projection/cache models.

7. Open questions for Blueprint

Questions for ForPrint System Blueprint:

1. Is `forprint_operational_registry` officially the canonical owner of clients, orders, tasks, and operational statuses?

2. Should CRM create new orders directly, or should it send an order creation command to Operational Registry through Integration Gateway?

3. Should CRM store any canonical manual decision records, or should those belong to Operational Registry?

4. What is the exact boundary between CRM “business workflow coordination” and Integration Gateway “execution routing”?

5. Should dashboard projections be stored in CRM database, or generated on demand from registry APIs?

6. Which module owns user/employee/operator identity?
   CRM, Operational Registry, or a future Identity/Access module?

7. What is the first required CRM dashboard:
   orders dashboard, finance dashboard, module health dashboard, or executive overview?

8. Should Project Inspector reports be pushed to CRM, or should CRM pull them from Inspector?

9. What minimum contracts must exist before CRM implementation starts?
Final alignment statement

forprint_crm accepts the Blueprint direction.

CRM should remain:

business orchestration + human dashboard + analytics/reporting interface

CRM should not become:

all-in-one backend / universal canonical database / replacement for registries / integration router / architecture inspector

Recommended architectural boundary:

CRM displays, coordinates, commands, and reports.
Operational Registry owns operational truth.
Accounting Registry owns financial/accounting truth.
ForPrint Library owns catalogs and technical references.
Project Inspector owns architecture compliance reports.
Integration Gateway owns routing and execution delivery.