# Prompt: Align ForPrint Operational Registry with ForPrint System Blueprint

## Target module

`forprint_operational_registry`

## Purpose

This prompt aligns ForPrint Operational Registry with the current ForPrint System Blueprint.

ForPrint Operational Registry is planned as the canonical operational data registry for clients, orders, tasks and operational statuses. Its main purpose is to prevent CRM from becoming the physical owner of all operational truth.

## Current architectural role

Operational Registry should act as:

canonical operational data registry

It should own the operational truth that many modules need, while CRM remains business orchestration UI/dashboard.

Operational Registry may own

Operational Registry may own:

client
order
task
order_status
production_status
activity_event
customer_interaction_reference
operational_history
order_file_reference
production_request
Operational Registry may consume

Operational Registry may consume:

validated create/update commands from Integration Gateway;
business workflow commands from CRM through Gateway;
quote references from Calculator;
prepress statuses from Prepress Hub;
warehouse reservation statuses from Warehouse Service;
accounting status references from Accounting Registry;
channel references from Telegram Bot / Website through approved contracts.
Operational Registry must not own

Operational Registry must not become owner of:

material catalog;
product catalog;
machine capabilities;
print modes;
invoice/payment accounting truth;
file processing logic;
price calculation logic;
warehouse stock quantities;
delivery provider integrations;
CRM dashboard state.
Why this module matters

Without Operational Registry, CRM may accidentally become the canonical database for everything.

Operational Registry creates separation:

CRM = business orchestration + UI + dashboard
Operational Registry = canonical operational truth
Accounting Registry = accounting truth
Library = catalog/knowledge truth
Key architectural risks
Operational Registry duplicates Accounting Registry.
Operational Registry duplicates Library catalogs.
Operational Registry becomes too broad and absorbs all modules.
CRM bypasses Operational Registry and stores operational truth locally.
Telegram Bot / Website create orders directly without approved contracts.
Order statuses are duplicated across CRM, Bot, Accounting and Prepress.
Required alignment actions

Please design or review the planned Operational Registry and answer:

What are the minimal operational entities for v1?
What is the canonical client structure?
What is the canonical order structure?
What statuses should belong to Operational Registry?
What should remain in CRM as UI/workflow/cache only?
What should remain in Accounting Registry?
What should remain in Library?
How should order creation work through Gateway/CRM?
How should Calculator quote become an order?
Which events should be stored as activity_event?
Expected deliverable from module assistant

Return a short alignment report:

1. Minimal Operational Registry v1 scope
2. Proposed canonical entities
3. Status model
4. Interfaces with CRM
5. Interfaces with Gateway
6. Interfaces with Calculator / Prepress / Accounting
7. Risks of overlap with other modules
8. Open questions for Blueprint
Important rule

Operational Registry is not CRM.

The immediate goal is:

create a clean home for operational truth so CRM can remain a business dashboard and workflow director.