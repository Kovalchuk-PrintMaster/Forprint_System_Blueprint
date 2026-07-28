# Prompt: Align Accounting Registry Service with ForPrint System Blueprint

## Target module

`accounting_registry_service`

## Purpose

This prompt aligns Accounting Registry Service with the current ForPrint System Blueprint.

Accounting Registry Service is responsible for the accounting boundary, invoice/payment truth, 1C integration, staging, audit and reconciliation. It must not become CRM, Operational Registry, Library, Calculator, or general system orchestrator.

## Current architectural role

Accounting Registry Service should act as:

```text
accounting registry + 1C integration boundary + reconciliation layer
```

It should protect the system from raw 1C complexity and provide clean accounting objects to other ForPrint modules through approved contracts.

Accounting Registry may own

Accounting Registry Service may own:

invoice
payment_status
accounting_document
one_c_raw_snapshot
one_c_staging_record
accounting_reconciliation_report
mappings between internal accounting objects and 1C objects
Accounting Registry may consume

Accounting Registry Service may consume:

order/payment context from forprint_operational_registry;
invoice creation requests from forprint_integration_gateway;
client/order references through approved contracts;
canonical names/codes/templates from forprint_library;
business commands from CRM through Gateway or approved workflow.
Accounting Registry must not own

Accounting Registry Service must not become owner of:

full client registry;
full order registry;
production tasks;
material catalog;
product catalog;
quote calculation logic;
CRM dashboard;
integration routing for all services;
Telegram/Website workflow state.
Correct 1C integration model

The preferred model is:

1C Raw Snapshot
↓
1C Staging Tables
↓
Data Audit
↓
Normalization
↓
ForPrint Accounting Registry Tables
↓
Mapping to Library / Operational Registry / Contracts

Raw 1C data should not leak directly into all modules.

Key architectural risks
Accounting Registry becomes the main operational database.
Accounting Registry starts owning clients and orders because 1C has related documents.
Accounting Registry bypasses Integration Gateway and CRM workflows.
Accounting Registry mixes raw 1C records with clean internal records.
Accounting Registry creates invoices without clear contract and audit trail.
Accounting Registry starts storing product/material catalogs instead of consuming them from Library.
Required alignment actions

Please review the current Accounting Registry Service implementation and answer:

Which current tables/entities are raw 1C snapshots?
Which current tables/entities are staging/audit entities?
Which current tables/entities are clean internal accounting registry objects?
Does the module currently own any operational objects that should belong to Operational Registry?
How are invoices represented now?
How are payments/payment statuses represented now?
Which contracts are needed between Accounting Registry and Integration Gateway?
Which contracts are needed between Accounting Registry and Operational Registry?
Which data should be consumed from Library instead of duplicated locally?
Are there places where the old term orchestrator should be replaced by Integration Gateway, CRM, or Blueprint?
Expected deliverable from module assistant

Return a short alignment report:

1. Current Accounting Registry role
2. Current 1C data flow
3. Canonical accounting objects owned by this module
4. Objects that should move to Operational Registry / Library / CRM
5. Required contracts
6. Detected architecture drift
7. Safe next steps
8. Open questions for ForPrint System Blueprint
Important rule

Do not redesign the whole module now. Do not perform large refactoring without approval.

The immediate goal is:

separate accounting truth from operational truth and align 1C integration with Blueprint.
