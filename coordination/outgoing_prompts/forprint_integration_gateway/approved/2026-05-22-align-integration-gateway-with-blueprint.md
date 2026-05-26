

# Prompt: Align ForPrint Integration Gateway with ForPrint System Blueprint

## Target module

`forprint_integration_gateway`

## Purpose

This prompt aligns ForPrint Integration Gateway with the current ForPrint System Blueprint.

Integration Gateway is the contract-transport layer. It validates, normalizes and routes requests between modules. It must not become CRM, Calculator, Library, Accounting, Warehouse, or system brain.

## Current architectural role

Integration Gateway should act as:

validation + normalization + routing + audit + idempotency layer

It answers the question:

Is this request valid, safe, normalized, and where should it go?

It does not answer:

What is the correct business decision?

That belongs to CRM / business workflow.

Integration Gateway may own

Integration Gateway may own:

integration_request
routed_module_request
integration_response
validation_error
routing_rule
correlation_context
idempotency_record
integration_audit_event
security_filter_event
Integration Gateway may consume

Integration Gateway may consume:

route definitions from Blueprint / Library / local config;
contract definitions from Blueprint / Library;
business commands from CRM;
customer channel requests from Telegram Bot / Website;
module responses from Calculator / Prepress / Warehouse / Accounting / Logistics.
Integration Gateway must not own

Integration Gateway must not become owner of:

client registry;
order registry;
material catalog;
product catalog;
price calculation logic;
invoice/payment truth;
warehouse stock;
business workflow decisions;
UI/dashboard state.
Correct Gateway model

Preferred request path:

source module / channel
↓
integration_request
↓
schema/contract validation
↓
normalization
↓
security filtering
↓
idempotency check
↓
routing decision
↓
routed_module_request
↓
target module
↓
integration_response
↓
source module / CRM / audit
Key architectural risks
Gateway becomes a hidden orchestrator with business rules.
Gateway starts knowing too much about every module’s internal database.
Gateway silently fixes bad payloads instead of returning validation errors.
Gateway bypasses CRM business workflow.
Gateway stores canonical business data.
Gateway becomes a single point of uncontrolled complexity.
Required alignment actions

Please review the current Integration Gateway concept and answer:

What should be the minimal first version of Gateway?
Which request envelope should all modules use?
What fields are required for integration_request?
How should validation errors be returned?
How should correlation_id/idempotency_key work?
Which first routes are most important?
Which routes should be explicitly blocked or deferred?
How should Gateway interact with CRM?
How should Gateway interact with Project Inspector?
Which parts must remain in Blueprint/Library instead of Gateway?
Expected deliverable from module assistant

Return a short alignment report:

1. Minimal Gateway scope
2. Proposed request envelope
3. Proposed response envelope
4. Initial routing rules
5. Validation error model
6. Idempotency/correlation approach
7. Architecture risks
8. Open questions for Blueprint
Important rule

Integration Gateway is a dispatcher and validator, not a business brain.

The immediate goal is:

create a simple, explicit and safe integration boundary before modules are directly tied together.