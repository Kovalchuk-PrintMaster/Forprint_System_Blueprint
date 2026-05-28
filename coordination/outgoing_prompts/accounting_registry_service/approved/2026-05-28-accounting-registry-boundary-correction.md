# Blueprint Response: Correct ForPrint Accounting Registry Service Boundary and Authorize Next Safe Step

## Target module

`forprint_accounting_registry_service`

## Current Blueprint decision

ForPrint System Blueprint reviewed the current state and development intent of `forprint_accounting_registry_service`.

The current direction is accepted with boundary corrections.

The module may continue, but only in a controlled mode:

```text
continue_with_boundary_corrections
```

Do not start broad functional expansion yet.

The next step must clarify naming, ownership, documentation, tests, and contract placeholders so the module does not drift into CRM, Operational Registry, Library, or general business database responsibilities.

---

# 1. Correct architectural role

`forprint_accounting_registry_service` must remain:

```text
Accounting Registry / 1C boundary / accounting truth service
```

Its role is:

```text
financial/accounting/1C truth
invoice/payment/accounting document state
1C raw snapshot and staging boundary
accounting reconciliation
mapping between internal accounting objects and 1C objects
accounting export/import packages
accounting projections needed for financial documents
```

It must not become:

```text
CRM
Operational Registry
ForPrint Library
Integration Gateway
Calculator
warehouse service
general business database
full 1C mirror for everything
canonical product catalog
customer interaction history owner
```

---

# 2. Replace unclear "Orchestrator" terminology

The previous wording used `Orchestrator`.

Do not use `Orchestrator` as an unclear global actor.

Use precise Blueprint terminology:

```text
ForPrint System Blueprint
= architecture truth and boundaries.

ForPrint CRM
= business orchestration, human dashboard, workflow coordination.

ForPrint Integration Gateway
= runtime request validation, routing, idempotency and transport.

ForPrint Operational Registry
= canonical operational truth for clients, orders, tasks, statuses.

ForPrint Library
= canonical catalogs, contracts, semantic IDs, aliases, versioning.

Accounting Registry Service
= accounting / payment / invoice / 1C truth.
```

Replace wording like:

```text
under Orchestrator control
Orchestrator-approved contracts
```

with:

```text
within ForPrint System Blueprint boundaries
through Blueprint-approved contracts
through Integration Gateway for runtime command routing where needed
through CRM for business workflow decisions where needed
```

---

# 3. Accounting Registry and Operational Registry are separate modules

Do not merge these responsibilities.

```text
Accounting Registry
= invoices, payments, accounting documents, 1C snapshots, 1C staging, reconciliation.

Operational Registry
= clients, orders, tasks, operational statuses, production/order lifecycle state, operational history.
```

`forprint_accounting_registry_service` must not implement `forprint_operational_registry` inside itself.

It may temporarily store accounting references or imported 1C projections that point to operational objects, but it must not become their canonical owner.

---

# 4. Allowed ownership inside Accounting Registry

The module may own canonical accounting truth for:

```text
invoice
payment
payment_status
accounting_document
accounting_document_state
one_c_raw_snapshot
one_c_staging_record
one_c_import_batch
one_c_export_package
one_c_mapping_record
accounting_reconciliation_report
accounting_reference_projection
financial_document_state
```

The module may own technical accounting objects:

```text
snapshot_file_metadata
import_job
export_job
reconciliation_job
mapping_issue
accounting_validation_issue
```

The module may keep accounting projections of external objects only when clearly named and documented.

Allowed examples:

```text
AccountingCounterpartyReference
OneCCounterpartySnapshot
AccountingCounterpartyProjection
OneCNomenclatureSnapshot
AccountingProductReference
AccountingNomenclatureProjection
```

---

# 5. Forbidden ownership inside Accounting Registry

The module must not canonically own:

```text
client_profile
customer_profile
customer_interaction_history
crm_contact_history
sales_pipeline
order
production_order
operational_task
production_status
order_status_as_operational_truth
warehouse_stock
warehouse_reservation
warehouse_writeoff
material_catalog
product_catalog
product_template_as_library_truth
calculator_price_logic
prepress_file_lifecycle
delivery_status_as_logistics_truth
crm_dashboard_state
```

If such concepts appear in the code, they must be classified as one of:

```text
1C raw snapshot
1C staging record
imported accounting reference
accounting projection
mapping helper
temporary placeholder
```

Otherwise they are architectural drift.

---

# 6. Boundary rules for risky objects

Apply these rules immediately.

## Counterparty

Allowed role:

```text
imported 1C counterparty snapshot
accounting reference
invoice/payment party projection
mapping helper between 1C and internal IDs
```

Forbidden role:

```text
CRM client profile
canonical client identity
customer communication history
sales pipeline record
```

Required naming correction:

Prefer:

```text
AccountingCounterpartyReference
OneCCounterpartySnapshot
AccountingCounterpartyProjection
```

Avoid generic names like:

```text
Client
Customer
Counterparty
```

unless they are explicitly documented as accounting-only.

## Product / Nomenclature

Allowed role:

```text
imported 1C nomenclature snapshot
accounting reference for invoice lines
external accounting mapping helper
financial document line reference
```

Forbidden role:

```text
ForPrint Library product catalog truth
Calculator product configuration truth
production product definition
material catalog truth
```

Required naming correction:

Prefer:

```text
OneCNomenclatureSnapshot
AccountingNomenclatureReference
AccountingProductProjection
InvoiceLineNomenclatureReference
```

Avoid:

```text
Product
Material
ProductTemplate
CatalogItem
```

unless clearly marked as accounting projection / 1C snapshot.

## Order reference

Allowed role:

```text
accounting reference to an operational order
external_order_id
order_ref
invoice_source_ref
payment_source_ref
```

Forbidden role:

```text
canonical order
order workflow owner
production order state
operational task owner
```

Required naming correction:

Prefer:

```text
OrderAccountingReference
InvoiceSourceReference
ExternalOrderReference
```

Do not create a canonical `Order` model in Accounting Registry.

---

# 7. Approved next implementation step

Implement a small boundary correction pack.

Do not add large new features.

## Allowed files / changes

You may add or update:

```text
docs/architecture/accounting_registry_boundaries.md
docs/architecture/one_c_boundary.md
docs/architecture/accounting_vs_operational_registry.md
docs/development/model_naming_rules.md
```

You may update:

```text
README.md
forprint_module_manifest.yaml
Makefile
tests/
```

You may add tests such as:

```text
tests/test_accounting_boundaries.py
tests/test_manifest_boundaries.py
tests/test_model_naming_rules.py
```

You may add contract placeholder files:

```text
contracts/placeholders/accounting.invoice_request.v1.yaml
contracts/placeholders/accounting.payment_status_reference.v1.yaml
contracts/placeholders/accounting.finance_summary.v1.yaml
contracts/placeholders/accounting.one_c_import_result.v1.yaml
```

These contract files must be marked:

```text
fixture_status: placeholder
canonical_contract_truth: forprint_library_future
```

Do not treat them as final canonical contracts.

---

# 8. Explicitly deferred

Do not implement yet:

```text
full 1C production import
real 1C API integration
database-heavy migration layer
Operational Registry inside this service
CRM dashboard logic
invoice creation through real Gateway runtime
real CRM integration
real Library integration
real Calculator integration
warehouse integration
global product catalog
global client registry
production payment synchronization
large refactoring
```

---

# 9. Integration Gateway rule

For now, this module may keep local placeholder contracts and docs.

Runtime commands should later go through Integration Gateway.

Examples:

```text
CRM wants invoice creation
→ CRM business decision
→ Integration Gateway command envelope
→ Accounting Registry invoice request
```

Allowed future command direction:

```text
crm_to_gateway_invoice_creation_command.v1
gateway_to_accounting_invoice_request.v1
accounting_to_gateway_invoice_result.v1
gateway_to_crm_command_result.v1
```

But do not implement real Gateway integration yet.

For now, document these flows as planned.

---

# 10. Library rule

ForPrint Library owns canonical contract/schema definitions in the future.

Accounting Registry may create placeholder contract files only for local development and tests.

Do not make Accounting Registry the canonical source of contract truth.

Allowed:

```text
local placeholder accounting contracts
example payloads
documentation-only schemas
```

Forbidden:

```text
global contract registry
canonical product/material schemas
semantic ID registry
Library replacement
```

---

# 11. Operational Registry rule

`forprint_operational_registry` is still planned as a separate logical module.

Until it is implemented, Accounting Registry may keep references like:

```text
external_order_id
order_ref
source_order_ref
operational_entity_ref
```

But it must not own the operational lifecycle.

Forbidden:

```text
order workflow state
production status
task assignment
customer communication history
delivery workflow
```

If Accounting Registry needs those values, mark them as:

```text
read-only reference
external reference
future Operational Registry reference
temporary projection
```

---

# 12. Required manifest correction

Update `forprint_module_manifest.yaml` so it clearly says:

```text
module_id: forprint_accounting_registry_service
role: accounting_registry_and_one_c_boundary
status: boundary_correction_development
```

The manifest must include `must_not_own` with at least:

```text
client_registry
order_registry
operational_task_registry
production_status
warehouse_stock
material_catalog
product_catalog
price_calculation
crm_dashboard_state
customer_interaction_history
business_workflow_decisions
integration_routing
architecture_governance
```

The manifest should include `owns` with accounting-only objects:

```text
invoice
payment
payment_status
accounting_document
one_c_raw_snapshot
one_c_staging_record
one_c_mapping_record
accounting_reconciliation_report
accounting_reference_projection
```

---

# 13. Required tests

Add tests that protect the boundary.

Recommended test intent:

```text
manifest declares correct module_id
manifest declares accounting boundary role
manifest contains must_not_own operational objects
README mentions module is not CRM / Operational Registry / Library
boundary docs exist
risky names are documented as accounting projections
placeholder contracts are marked non-canonical
```

If models already exist, add tests or comments that classify them.

Do not break existing tests.

---

# 14. Expected response after implementation

After this boundary correction step, return a completion report with:

```text
1. Files added/changed.
2. Naming corrections made.
3. Boundary docs added.
4. Manifest changes.
5. Tests added.
6. Contract placeholders added.
7. make check result.
8. make check-report result if available.
9. Confirmation that no Operational Registry / CRM / Library responsibilities were added.
10. Open questions for Blueprint before next step.
```

## Recommended commit

After all checks pass, commit as:

```text
Add Accounting Registry boundary corrections
```

---

# 15. Final instruction

Do not expand functionality before boundaries are safe.

The goal of this step is not to build a full accounting system.

The goal is to make sure the current module cannot accidentally drift into:

```text
CRM
Operational Registry
Library
general 1C mirror
general business database
```

Proceed with a small boundary correction implementation only.
