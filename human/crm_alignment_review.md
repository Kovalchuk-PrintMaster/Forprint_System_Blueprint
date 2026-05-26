# ForPrint CRM Alignment Review

## Status

Reviewed.

## Source report

```text
coordination/incoming_requests/forprint_crm/new/2026-05-23-forprint-crm-alignment-report.md
Main conclusion

ForPrint CRM is aligned with the Blueprint direction.

CRM should remain:

business orchestration + human dashboard + analytics/reporting interface

CRM should not become:

all-in-one backend
universal canonical database
replacement for registries
integration router
architecture inspector
Accepted CRM role

CRM is responsible for:

business workflow coordination;
human-facing dashboard;
operator interface;
management analytics;
business decision interface;
manual review interface;
CRM-specific saved views;
architecture health view based on Project Inspector reports.

CRM may initiate business commands, but it should not directly replace specialized modules.

Data CRM may own

CRM may own data specific to UI, dashboard, reporting and management workflow:

dashboard layout settings;
user-specific views and filters;
saved report presets;
CRM UI preferences;
dashboard widget configuration;
management comments and notes;
manual review board configuration;
business decision drafts;
workflow command history;
CRM-side notification preferences;
non-canonical cached dashboard projections;
analytics snapshots;
operator workspace state;
internal CRM reminders;
manager review queues;
dashboard annotations.
Data CRM should only read/display

CRM should consume canonical data from other modules.

From Operational Registry
clients;
orders;
order statuses;
operational tasks;
production/order lifecycle state.
From Accounting Registry
invoices;
payments;
debts;
prepayments;
accounting-related order status;
1C synchronization state.
From ForPrint Library
product names;
material names;
templates;
nomenclature references;
technical references;
machine capability references.
From Project Inspector
module health;
architecture drift;
integration gaps;
stale module reports;
failed tests.
From Integration Gateway
execution results;
routed command statuses;
integration error messages.
Required contract direction

Initial CRM-related contracts should include:

operational_registry_to_crm_dashboard_snapshot.v1
accounting_registry_to_crm_finance_summary.v1
library_to_crm_catalog_reference.v1
project_inspector_to_crm_architecture_health.v1
crm_to_integration_gateway_command.v1
integration_gateway_to_crm_command_result.v1
crm_dashboard_projection.v1
Important decision

CRM commands should go through Integration Gateway.

Examples:

request invoice creation;
request prepress preparation;
request quote recalculation;
request Telegram notification;
request order status transition;
request document generation;
request external website/order synchronization.
Recommended CRM implementation start

CRM should start with dashboard/reporting-oriented models:

DashboardWidget
DashboardLayout
SavedReport
ReportSnapshot
CRMUserNote
CRMCommandLog
ExternalModuleStatusProjection

Avoid starting with canonical models like:

Client
Order
Invoice
Payment
Material

unless they are explicitly temporary/projection/cache models.

Blueprint decisions needed
Confirm Operational Registry as canonical owner of clients, orders, tasks and operational statuses.
Define order creation flow: CRM direct create vs command through Gateway.
Define owner of manual decision records.
Define CRM vs Gateway boundary.
Decide whether CRM stores dashboard projections or generates them on demand.
Decide owner of user/employee/operator identity.
Select first CRM dashboard priority.
Define Project Inspector → CRM reporting mode.
Define minimum contracts before CRM implementation starts.
Decision

Proceed with CRM direction, but keep strict boundaries.

Next Blueprint action:

define initial CRM contracts
confirm Operational Registry canonical ownership
then continue with Library alignment