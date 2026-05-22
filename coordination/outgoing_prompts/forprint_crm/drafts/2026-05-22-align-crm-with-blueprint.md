# Prompt: Align ForPrint CRM with ForPrint System Blueprint

## Target module

`forprint_crm`

## Purpose

This prompt aligns ForPrint CRM with the current ForPrint System Blueprint.

CRM is the business orchestration layer and human-facing dashboard. It coordinates business workflows and helps people manage the system, but it must not become the physical owner of all data.

## Current architectural role

ForPrint CRM should act as:

```text
business director / workflow coordinator / human UI / analytics dashboard


---

# 2. Файл: `coordination/outgoing_prompts/forprint_crm/drafts/2026-05-22-align-crm-with-blueprint.md`

```markdown
# Prompt: Align ForPrint CRM with ForPrint System Blueprint

## Target module

`forprint_crm`

## Purpose

This prompt aligns ForPrint CRM with the current ForPrint System Blueprint.

CRM is the business orchestration layer and human-facing dashboard. It coordinates business workflows and helps people manage the system, but it must not become the physical owner of all data.

## Current architectural role

ForPrint CRM should act as:

business director / workflow coordinator / human UI / analytics dashboard

CRM decides what should happen in the business process, but it should not bypass contracts or directly replace specialized modules.

CRM may be responsible for
dashboard;
business workflow visibility;
task overview;
customer/order view;
management analytics;
business decisions;
workflow commands;
operator interface;
architecture health view from Inspector reports.
CRM should consume

CRM should consume canonical data from:

forprint_operational_registry for clients, orders, tasks, operational statuses;
accounting_registry_service for invoices, payments, 1C-related accounting truth;
forprint_library for catalogs, templates, product/material names;
forprint_project_inspector for architecture drift reports;
forprint_integration_gateway for routed execution results.
CRM must not own everything

CRM must not become canonical owner of:

all clients;
all orders;
all payments;
all invoices;
all material catalogs;
all product catalogs;
all prepress files;
all warehouse stock;
all integration routing.

It may store UI/cache/reporting projections, but canonical ownership should stay in the correct module.

Key architectural risks
CRM becomes a monolith.
CRM duplicates Operational Registry.
CRM duplicates Accounting Registry.
CRM bypasses Integration Gateway.
CRM becomes physical owner of all data because it has the main dashboard.
CRM absorbs Project Inspector functions instead of displaying Inspector results.
Required alignment actions

Please review the current ForPrint CRM concept and answer:

Which parts are dashboard/UI?
Which parts are business workflow coordination?
Which data does CRM truly need to own?
Which data should CRM only read from registries?
Which commands should CRM send through Integration Gateway?
Which reports should CRM receive from Project Inspector?
What should be explicitly moved to Operational Registry instead of CRM?
What should be explicitly moved to Accounting Registry instead of CRM?
Expected deliverable from module assistant

Return a short alignment report:

1. Current CRM role
2. Possible overreach zones
3. Data CRM should own
4. Data CRM should only display/read
5. Required contracts
6. Recommended next implementation step
7. Open questions for Blueprint
Important rule

Do not turn CRM into the whole system.

CRM should remain:

business orchestration + human dashboard

not:

all-in-one backend.