# Data Ownership and Storage Policy

## Purpose

This policy defines how ForPrint modules should own, store, read and exchange data.

The goal is to support local-first operation, clear ownership, reliable reporting and future distributed deployment.

## Core rule

```text
Shared physical database infrastructure is allowed.
Shared logical data ownership is forbidden.
```

A module may share the same PostgreSQL server with other modules, but it must not write to another module's owned tables or schema.

## Preferred database strategy

ForPrint should use a local-first database strategy.

The recommended production direction is:

```text
one local PostgreSQL cluster or instance;
one primary application database at first;
separate schemas for module-owned data;
separate database users and roles per module;
a dedicated reporting schema for cross-domain views and projections.
```

Example:

```text
forprint_core_db
  operational_registry.*
  accounting_registry.*
  library.*
  calculator.*
  gateway.*
  crm.*
  reporting.*
```

## Schema-per-module first

ForPrint should start with schema-per-module inside a local PostgreSQL database when the system reaches production database readiness.

This gives a practical balance:

```text
simpler backup and administration;
easier cross-domain reporting;
clear logical ownership boundaries;
lower operational complexity than many separate databases;
future migration path to separate databases when needed.
```

## Database-per-module later

Separate databases may be introduced later when justified by:

```text
security isolation;
large data volume;
separate backup or restore needs;
independent deployment;
high load;
external integration sensitivity;
clear operational benefit.
```

Moving from schema-per-module to database-per-module requires a dedicated migration checkpoint.

## Early-stage storage

Before production PostgreSQL readiness, modules may use:

```text
YAML examples;
JSON fixtures;
SQLite;
in-memory repositories for tests;
local files;
local preview outputs.
```

These early-stage stores must not be presented as production truth unless explicitly approved.

## Canonical truth

Canonical truth belongs to owner modules.

Examples:

```text
Operational Registry owns operational clients, requests, orders, tasks and operational events.
Accounting Registry owns invoices, payments, accounting documents and 1C staging.
Library owns semantic and catalog meaning.
Calculator owns calculation packages, quotes and drafts.
Gateway owns delivery ledger, idempotency records and routing audit.
CRM owns UI preferences, views and operator coordination metadata.
```

## No cross-module writes

A module must not write directly into another module's owned schema.

Allowed interaction patterns:

```text
command to owner module;
query through owner module;
read-only view;
snapshot;
projection;
event;
foreign reference;
approved adapter.
```

Forbidden interaction patterns:

```text
direct write into another module schema;
hidden ownership through copied tables;
silent mutation of another module status;
business decisions inside a transport-only module;
editing production truth from reporting views.
```

## Foreign references

Modules may store foreign references to other module-owned entities.

A foreign reference is not ownership.

Example:

```text
Calculator may store operational_order_reference after Operational Registry accepts an order creation command.
Accounting Registry may store operational_order_reference for invoice mapping.
CRM may store client_reference for UI view state.
```

## Local durable work state

A module may maintain local durable work state for:

```text
drafts;
pending handoffs;
outbox messages;
inbox messages;
snapshots;
retry state;
manual review state;
recovery metadata.
```

This local state must not become conflicting canonical truth.

## Reporting schema

ForPrint should introduce a `reporting` schema or equivalent reporting layer.

Reporting may use:

```text
views;
materialized views;
snapshots;
aggregated tables;
read projections.
```

Reporting must not become the writer of canonical business data.

CRM and analytics should prefer reporting views instead of directly joining internal owner tables without an approved boundary.

## Local-first requirement

Core internal operations should not require public internet.

Internet access may be required for:

```text
Telegram API;
GitHub pull and push;
external email;
cloud backups;
external APIs;
remote access.
```

Core local records, drafts, handoffs and internal state must be recoverable locally.

## Backup and recovery

Database strategy must include:

```text
local backup;
restore procedure;
ownership-aware backup notes;
migration history;
manual recovery path;
verification of pending handoffs after restore.
```

Backup tooling may be supported by Cloud Backup Manager, but business truth ownership remains with the owner modules.

## Boundary

This policy does not define detailed message retry logic.

Message reliability is defined in `module_interaction_reliability_policy.md`.

Gateway storage responsibility is defined in `gateway_responsibility_policy.md`.
