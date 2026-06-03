# ForPrint Ecosystem Module Map

## Status

Active global policy

## Purpose

This document gives all module assistants a shared high-level view of the ForPrint ecosystem.

It is not a full technical design.

It defines module roles and prevents modules from taking ownership of responsibilities that belong elsewhere.

## Core modules

| Module | Strategic role | Must not become |
|---|---|---|
| forprint_strategic_control_plane | Future strategic governance, priority control, ecosystem status aggregation and decision-support layer | Active runtime orchestrator before core modules are alive |
| forprint_system_blueprint | Architecture, boundaries, execution queue, coordination standards | Runtime service |
| forprint_operational_registry | Internal DB/data custodian | Calculator, CRM, Library, 1C adapter |
| forprint_library | Canonical semantic/catalog authority | Operational DB |
| calculator_engine | Calculation and order formalization engine | Order registry, CRM, accounting, warehouse |
| forprint_accounting_registry_service | Accounting/1C synchronization boundary | Operational Registry, CRM, Library |
| forprint_integration_gateway | Runtime transport/validation/routing layer | Business brain |
| telegram_bot | Customer channel adapter | Business truth owner |
| website | Customer channel adapter | Business truth owner |
| mobile_app | Future customer channel | Active module before Calculator maturity |
| forprint_crm | Human dashboard/workflow coordination | Physical DB owner |
| forprint_prepress_hub | Prepress/file preparation lifecycle | Calculator, accounting, order registry |
| warehouse_service | Future stock/material operations | Catalog semantic authority |
| logistics_service | Future delivery/logistics operations | CRM or order registry |
| cloud_backup_manager | Infrastructure backup utility | Business module |

## Primary future flow

```text
Customer / manager request
↓
Customer channel or internal UI
↓
CustomerRequest
↓
Calculator Engine
↓
CalculationOutputPackage / Quote / OrderDraft
↓
Operational Registry stores internal records
↓
Accounting Registry prepares accounting/1C sync
↓
Prepress / production / warehouse / logistics receive references and tasks
Current first practical focus

The first practical module coordination loop is being tested with:

calculator_engine

The goal is to validate:

Blueprint instructions
↓
module self-check
↓
module coordination files
↓
Blueprint collector
↓
snapshot report

After the Calculator loop is stable, the same pattern can be applied to other modules.


---

## Strategic Control Plane

ForPrint Strategic Control Plane is planned as a future high-priority governance module.

Current status:

```text
planned_high_priority_deferred_until_core_modules_alive

It must not be actively implemented yet.

Current governance remains with the owner / mentor, architectural assistant and ForPrint System Blueprint.


---
