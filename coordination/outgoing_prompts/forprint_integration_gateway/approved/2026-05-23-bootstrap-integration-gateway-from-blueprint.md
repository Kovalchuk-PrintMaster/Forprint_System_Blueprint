Prompt: Bootstrap ForPrint Integration Gateway from ForPrint System Blueprint
Target module

forprint_integration_gateway

Current situation

This module is not yet implemented.

The working directory is planned as:

/srv/software_development/forprint-project/forprint_integration_gateway

The module assistant should treat this as a new project start, not as an existing module alignment review.

Source of truth

This module must follow the current ForPrint System Blueprint.

Key architecture context:

ForPrint System Blueprint
= architecture truth source.

ForPrint Integration Gateway
= contract transport, validation, normalization, routing, audit and idempotency layer.

ForPrint CRM
= business orchestration and human dashboard.

ForPrint Library
= canonical catalogs, contracts, schemas, semantic registry, aliases and versioning.

ForPrint Operational Registry
= canonical operational truth for clients, orders, tasks, statuses.

Accounting Registry
= invoice/payment/1C accounting truth.

Calculator Engine
= quote_draft, price_breakdown, product_configuration, material_consumption_estimate.

Telegram Bot / Website / future Mobile App
= customer channels.
Main purpose of Integration Gateway

ForPrint Integration Gateway must answer:

Is this request valid, safe, normalized, traceable, idempotent, and where should it go?

It must not answer:

What is the business decision?

Business decisions belong to CRM / business workflow.

Correct role

Integration Gateway should act as:

validation + normalization + routing + contract transport + audit + idempotency boundary
Must own

Integration Gateway may own:

integration_request;
routed_module_request;
integration_response;
validation_error;
routing_rule;
correlation_context;
idempotency_record;
integration_audit_event;
security_filter_event;
command delivery status;
module response envelope.
Must consume

Integration Gateway may consume:

route definitions from Blueprint / local config;
contract definitions from Library / Blueprint;
business commands from CRM;
customer channel requests from Telegram Bot / Website / future Mobile App;
module responses from Calculator / Prepress / Warehouse / Accounting / Logistics;
future module manifest/status information when Project Inspector integration appears.
Must not own

Integration Gateway must not become owner of:

client registry;
order registry;
material catalog;
product catalog;
price calculation logic;
invoice/payment truth;
warehouse stock;
business workflow decisions;
UI/dashboard state;
architecture governance.
Important channel-agnostic rule

Do not design Gateway only for Telegram or only for Website.

All customer-facing intake should use channel-agnostic concepts:

customer_channel
customer_channel_request
customer_action
customer_session
customer_notification

The future mobile_app is not active yet, but Gateway contracts must be designed so that Mobile App can later use the same customer-channel flow without redesign.

Preferred request path
source module / customer channel
↓
integration_request
↓
schema / contract validation
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
Minimal first version

Do not build a complex enterprise message bus at the start.

The first implementation should be small, testable and explicit.

Recommended v0.1 scope
Project skeleton.
Python 3.11.2 virtual environment.
pyproject.toml.
Makefile.
README.md.
docs/architecture/gateway_boundaries.md.
forprint_module_manifest.yaml.
Basic package structure.
Basic tests from the first step.
Local YAML config for initial routes/contracts.
Simple request/response envelope models.
Simple validation error model.
Simple correlation_id / idempotency_key handling.
No production integrations yet.
Recommended project path
/srv/software_development/forprint-project/forprint_integration_gateway
Recommended Python environment

Use Python 3.11.2.

Recommended venv name:

.venv_gateway
Recommended first directory structure
forprint_integration_gateway/
├── README.md
├── Makefile
├── pyproject.toml
├── forprint_module_manifest.yaml
├── docs/
│   └── architecture/
│       └── gateway_boundaries.md
├── app/
│   └── forprint_integration_gateway/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── envelope.py
│       │   ├── errors.py
│       │   └── routing.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── validator.py
│       │   ├── router.py
│       │   └── idempotency.py
│       └── config/
│           ├── __init__.py
│           └── routes.yaml
└── tests/
    ├── test_envelope.py
    ├── test_validator.py
    └── test_router.py
Recommended initial data models
integration_request

Should include:

request_id
correlation_id
idempotency_key
source_module
source_channel
target_module
contract_id
contract_version
operation
payload
metadata
created_at
integration_response

Should include:

request_id
correlation_id
target_module
status
result_payload
errors
warnings
metadata
created_at
validation_error

Should include:

code
message
field_path
severity
is_retryable
routing_rule

Should include:

route_id
source_module
target_module
contract_id
operation
enabled
priority
Initial routes to model as placeholders

Do not implement real integrations yet. Define placeholder routes only.

Suggested initial routes:

crm_to_calculator_quote_recalculation
crm_to_accounting_invoice_request
crm_to_prepress_job_request
customer_channel_to_crm_order_intake
customer_channel_to_calculator_quote_preview
calculator_to_crm_quote_result
accounting_to_crm_invoice_status
prepress_to_crm_prepress_status
Required documentation

Create docs/architecture/gateway_boundaries.md explaining:

Gateway validates and routes;
CRM decides business workflow;
Library defines contracts/schemas;
Registry owns operational truth;
Accounting owns invoice/payment truth;
Calculator calculates;
Prepress processes files;
Telegram/Website/Mobile App are channels;
Gateway must not become a business brain.
Required module manifest

Create forprint_module_manifest.yaml using the current Blueprint manifest standard.

The manifest should state:

module_id: forprint_integration_gateway
role: contract_transport_and_validation_layer
status: bootstrap_development

It should clearly include:

must_not_own:
- client_registry
- order_registry
- material_catalog
- product_catalog
- price_calculation
- invoice
- payment_status
- warehouse_stock
- business_workflow_decisions
Required tests from the first step

The first commit should include tests for:

Integration request model can be created.
Integration response model can be created.
Validation error model can be created.
Router rejects missing route.
Router can match a simple placeholder route.
Idempotency service recognizes repeated idempotency_key.
Manifest file exists and has correct module_id.
Development rules

Do not create production API yet unless explicitly requested.

Do not connect to real Calculator / CRM / Accounting / Prepress yet.

Do not create database migrations yet unless there is a clear need.

Do not make Gateway depend on one customer channel.

Do not hardcode Telegram-only or Website-only language.

Do not create a complex distributed system.

Start with a small, testable Python package.

Expected first response from module assistant

Return a Bootstrap Implementation Plan with:

1. Confirmed understanding of Gateway role.
2. Proposed v0.1 project structure.
3. Proposed first data models.
4. Proposed first tests.
5. Proposed Makefile targets.
6. Proposed forprint_module_manifest.yaml.
7. Safe first implementation step.
8. Questions for ForPrint System Blueprint before coding.
Important instruction

Do not start by asking for the current module status.

There is no existing implementation yet.

Start by preparing the first clean project skeleton and tests according to this prompt.