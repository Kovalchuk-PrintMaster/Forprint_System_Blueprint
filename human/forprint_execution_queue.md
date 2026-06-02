# ForPrint Execution Queue v0.1

## Purpose

This document records the current ForPrint strategic agreements and execution queue.

It exists to keep all module assistants moving in one coordinated direction and to prevent architectural drift.

## Current governance

ForPrint Control Plane is accepted as a future high-priority strategic governance layer, but it is not active yet.

Current governance remains:

```text
Owner / mentor
+
architectural assistant
+
ForPrint System Blueprint
Strategic agreements
Operational Registry

Operational Registry is the main internal ForPrint data custodian.

It physically stores and maintains the internal ForPrint DB foundation.

It may store clients, contacts, requests, orders, statuses, operational history, addresses, accounting references and module references.

It must not become the logical owner of every domain rule.

Library

Library is the canonical semantic/catalog authority.

It owns canonical product/service/material/operation IDs, names, aliases, catalog definitions, semantic registry, contracts, templates and technical cards.

If a module has product/service/material naming ambiguity, it must route the ambiguity to Library instead of inventing its own permanent meaning.

Calculator

Calculator Engine is the primary formalization point for new order/calculation requests.

External customers, managers, Telegram, Website, future Mobile App and CRM manual entry should eventually flow through Calculator.

Calculator should produce structured machine-readable packages for downstream modules.

Phone and client identity

Phone is a strong lookup/contact key, but not canonical client identity.

Canonical customer identity is ClientAccount ID.

If a phone maps to several accounts, early workflow sends a ready request/order form to a responsible person and lets them choose the correct ClientAccount.

ClientAccount and ClientGroup

ClientAccount is the primary customer/account entity.

ClientGroup is a rare but important corporate grouping entity.

Every Order belongs to one concrete ClientAccount.

ClientGroup is used for corporate analytics and grouping.

Customer requests

Every identifiable customer request should be stored in the internal ForPrint DB.

This includes information-only inquiries, price inquiries, unresolved requests, cancelled requests, rejected requests, payment-unconfirmed requests and unsupported-product requests.

The goal is analytics and future conversion/lost-order analysis.

1C

ForPrint internal DB is the main internal management/accounting/operational data foundation.

1C remains an important accountant-facing work interface and synchronization contour.

Accounting Registry owns 1C synchronization adapters, import/export, mapping, staging, reconciliation and accounting-domain processing.

Current Accounting Registry state

Accounting Registry v0.5 is accepted as sandbox_1c_import_export_ready.

It can parse sanitized exports, run an offline import pipeline, persist mapping issues and block unsafe write paths.

It must not proceed to live 1C integration or production write without explicit future approval.

Priority queue
P0
1. System Blueprint — strategic agreements pack

Record all current strategic agreements and execution queue.

2. All active modules — coordination/status standard

Every active module should maintain:

coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/latest_completion_report.md
coordination/status/next_questions_for_blueprint.md
3. Calculator Engine

Next focus:

CalculationOutputPackage
Quote / CommercialOffer
OrderDraft
price_breakdown
material_consumption_estimate
production_method_plan
accounting line drafts
prepress requirements
manual/custom operation drafts
4. Accounting Registry

Pause large abstract expansion after v0.5.

Next v0.6 is allowed only after real sanitized 1C export samples are available.

P1
5. Operational Registry v0.6

Core ForPrint Data Model Expansion:

ClientAccount
ClientGroup
ContactPerson
ContactMethod
ChannelIdentity
Relationship
CustomerRequest lifecycle
Quote references
Order lifecycle
Accounting references
1C-aware fields
Logistics addresses
Manual decision records
Dictionary/reference placeholders
6. Library

Canonical Product/Service ID and Alias Governance:

product_id
service_id
material_id
operation_id
aliases
semantic definitions
definition request flow
draft/review/approved lifecycle
7. Telegram Bot / Customer Channel

Telegram must remain a customer channel adapter.

Next direction:

CustomerChannelRequest
ClientIdentificationCandidate
phone lookup
account ambiguity flow
OrderIntakeDraft
Calculator handoff
P2
CRM

Planned later for dashboard, reporting, workflow coordination, manual decisions and manager UI.

Gateway

Hold until real runtime handoff is needed.

Control Plane

Planned high priority, but deferred until core modules are alive.

Legacy file parser

Low-priority fallback only. Future core workflow should come from Calculator-generated packages.

Next recommended action

After this pack is committed, apply the module status reporting standard to all active module repositories.


---
