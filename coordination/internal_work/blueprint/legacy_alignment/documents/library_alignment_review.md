# ForPrint Library Alignment Review

## Status

Reviewed.

## Source report

coordination/incoming_requests/forprint_library/new/2026-05-23-forprint-library-alignment-report.md
Main conclusion

ForPrint Library is aligned with the Blueprint direction.

Library should remain:

canonical knowledge + catalog + template + technical card + contract-definition layer

Library should not become:

operational order database
payment/invoice registry
warehouse stock system
production queue
uploaded file lifecycle owner
global log collector
Accepted Library role

Library may own:

product and material canonical definitions;
machine capability definitions;
print modes;
file format definitions;
color modes;
measurement units;
reusable product/product-option definitions;
templates;
technical cards;
contract definitions;
semantic IDs;
aliases;
versioning;
migration graph;
validation schemas;
change manifest source.
Important boundary decision

Library may define that a material exists and what its canonical properties are.

Library must not own the actual stock quantity of that material.

Example:

Library can define:
paper.sra3.300gsm

Warehouse owns:
Material X has 245 sheets available today.
Objects that must not enter Library as runtime data

If these appear in Library, they should be moved or blocked:

client_order;
customer_profile;
customer_interaction_history;
payment;
invoice_runtime_record;
warehouse_stock_balance;
warehouse_reservation;
warehouse_writeoff_event;
production_job;
production_queue_item;
delivery_runtime_status;
uploaded_client_file_instance;
prepress_runtime_file_result;
operator_work_shift;
global runtime logs.
Contract direction accepted

Library should provide canonical contracts and schema definitions for:

Calculator Engine;
Prepress Hub;
Warehouse Service;
CRM;
Integration Gateway;
Project Inspector;
future Website / Telegram Bot / Mobile App through approved layers.

Important rule:

Website / Telegram Bot / Mobile App
→ Gateway / CRM / approved layer
→ Library-derived contracts and catalogs

Client channels should not become uncontrolled direct consumers of Library internals.

Impact rules required

Library changes must trigger impact rules for:

contract version changes;
schema field changes;
enum changes;
validation rule changes;
semantic ID / alias changes;
catalog changes;
material compatibility changes;
machine capability changes;
print mode changes;
technical card changes;
migration graph changes.

Semantic IDs should be stable and never reused for a different meaning.

Activation policy

Critical Library changes should not become active automatically.

Recommended lifecycle:

draft → approved → staged → syncing → active

This creates a future need for a sync/change coordination mechanism.

Open question: forprint_sync_manager

Library report recommends considering forprint_sync_manager as a separate first-class module.

Decision for now:

Do not create active module yet.
Keep as open Blueprint question.

Reason:

Library defines desired/canonical state.
A future Sync Manager may coordinate internal module updates.
But current priority remains Integration Gateway, Operations Control Registry and active module alignment.
Blueprint decisions needed
Should modules consume Library directly or through Gateway/approved interfaces?
Who owns runtime product availability?
Who owns partner-specific contract adoption status?
Should Library generate partner documentation packages?
Who owns historical archive reading?
Confirm Library vs Operations Control Registry split.
Confirm Library vs Accounting Registry split.
Decide later whether forprint_sync_manager becomes a first-class module.
Decision

Proceed with Library direction.

Next Blueprint action:

define Library impact rules
define initial Library contracts for Calculator and CRM
then continue with Integration Gateway alignment