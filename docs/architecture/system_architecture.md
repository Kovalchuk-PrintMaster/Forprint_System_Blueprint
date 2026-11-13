# ForPrint System Architecture

## Status

Current human-readable architecture explanation.

Canonical machine-readable architecture remains in `machine/*.yaml`. Effective work and
release authority remains in `coordination/releases/current.yaml`.

## Purpose

ForPrint is a modular system for automating a small print-production business. The
architecture separates architectural governance, business orchestration, canonical data
ownership, technical integration, domain execution and customer/operator channels so no
single application silently becomes the owner of the whole system.

## Authority model

The important distinction is:

```text
coordination/releases/current.yaml
    = what Blueprint work/release state is effective now

machine/module_identity_registry.yaml
    = stable module identity authority

machine/modules.yaml + contracts/data_flows/data_objects/ownership/system_layers
    = current architecture model

docs/
    = human explanation of that model

indexes/
    = derived navigation only
```

Path placement does not override explicit authority.

## Architectural layers

### Architecture governance

`forprint_system_blueprint` defines the intended architecture, module boundaries, data
ownership, contracts, flows and impact rules.

It does not execute customer orders or production work.

### Architecture compliance

`forprint_project_inspector` is the planned architecture-compliance reviewer.

`production_runtime_inspector` is the later runtime-health layer.

Inspector roles verify reality against declared architecture; they do not invent a
parallel architecture.

### Integration transport

`forprint_integration_gateway` is the planned contract/transport safety layer. It is
responsible for request validation, normalization, routing, correlation, idempotency and
standardized transport errors.

It must not become the business decision-maker or the canonical store for business data.

### Business orchestration

`forprint_crm` coordinates business workflow and presents operator-facing views,
dashboards, analytics and decisions.

CRM may display data owned elsewhere. Displaying or caching data does not make CRM the
canonical owner.

### Canonical operational and accounting truth

`forprint_operations_control_registry` owns canonical operational business records such
as client/order/task/status context according to the current machine model.

`forprint_accounting_registry_service` owns accounting truth such as invoices, payment
status, accounting documents and the 1C mapping/reconciliation contour.

Operational and accounting truth are separate domains even when they refer to the same
order.

### Canonical knowledge and catalogs

`forprint_library` owns semantic/catalog knowledge: materials, products, technical
cards/templates, capabilities, aliases and related canonical reference semantics.

It is not the operational order database.

### Domain execution

Domain modules perform bounded subject work. Current architecture includes, among others:

- `calculator_engine` — calculation and quote-related outputs;
- `forprint_prepress_hub` — prepress/file preparation;
- `warehouse_service` — inventory and reservations;
- `logistics_service` — delivery/tracking truth;
- `cloud_backup_manager` — backup/restore support.

Their exact current status and contracts are defined in `machine/*.yaml`.

### Customer and operator channels

`telegram_bot`, `website` and future/deferred `mobile_app` are interaction channels.

Channels may collect requests and show results, but should not become canonical owners of
prices, orders, accounting records or catalogs merely because they interact with users.

Additional support modules are represented by the current machine architecture and stable
identity registry; this document intentionally does not duplicate every lifecycle/status
field.

## Data ownership rule

Every important data object should have one canonical owner.

A module may consume, project or cache an object without acquiring ownership. The
canonical current ownership map is:

`machine/ownership.yaml`

Examples from the architecture model:

- clients and orders → `forprint_operations_control_registry`;
- material/product catalogs → `forprint_library`;
- quote/calculation outputs → `calculator_engine`;
- invoices/payment status → `forprint_accounting_registry_service`;
- warehouse stock/reservations → `warehouse_service`;
- delivery status → `logistics_service`.

## Current documentation rule

This file is explanatory. When it conflicts with a canonical machine source, release
authority or active standard, the explicit canonical source wins and this document must
be corrected.

Historical early architecture explanations are preserved under:

`coordination/internal_work/blueprint/legacy_alignment/`
