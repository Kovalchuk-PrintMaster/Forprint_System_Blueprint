# Prompt: ForPrint Integration Gateway v0.4 — Adapter Contracts, Error Taxonomy, and Delivery Readiness

Generated: `2026-06-11T16:39:43.616984+00:00`

## Target module

`forprint_integration_gateway`

## Source

This prompt is issued by `forprint_system_blueprint`.

Read it through:

```bash
make blueprint-prompts-list
make blueprint-prompt
```
Purpose

Develop the next safe Gateway layer after v0.3/v0.3.1.

Gateway v0.3 created offline channel intake and Operational Registry handoff contracts.

Gateway v0.3.1 fixed coordination records and added self-validation.

Gateway v0.4 must harden the integration boundary so future Telegram Bot, Website, CRM, Mobile App, Calculator Engine, Operational Registry, Library, Prepress Hub, and Accounting Registry adapters can be described consistently.

This checkpoint is adapter-readiness only.

Do not enable live runtime integration.

Current accepted baseline

Accepted Gateway commits:

3b4707a Add Gateway channel intake and handoff contracts
4b7821f Finalize Gateway v0.3 coordination and module ids
44ac33a Fix Gateway v0.3 coordination records
688e9c6 Add Gateway v0.3.1 completion report

Expected baseline:

make governance-check passes;
make check passes;
make check-report passes;
make channel-intake-preview passes;
coordination records check passes;
no non-canonical forprint_calculator_engine references remain;
Gateway remains offline/contract-only.
Main goal

Create v0.4 adapter-readiness foundation:

canonical adapter contract model;
module endpoint contract descriptors;
error taxonomy;
retry policy taxonomy;
delivery mode policy;
idempotency/correlation hardening;
adapter readiness preview;
offline examples for future adapters;
tests and check-report integration;
updated coordination records.
Required concepts

Add or extend models/docs/examples for:

GatewayAdapterContract
AdapterDirection
AdapterDeliveryMode
AdapterRuntimeStatus
GatewayErrorCode
GatewayErrorCategory
GatewayRetryPolicy
GatewayRetryDecision
GatewayDeliveryAttempt
GatewayDeliveryPlan
GatewayAdapterReadiness
GatewayContractCompatibility
Adapter directions

Support descriptors for:

inbound_channel_to_gateway
gateway_to_business_module
business_module_to_gateway
gateway_to_channel

These are contract descriptors only.

No live delivery.

Delivery modes

Support offline policy values such as:

offline_fixture_only
manual_preview_only
dry_run_only
future_live_adapter
forbidden

Default must be safe:

offline_fixture_only
Runtime status

Support:

planned
contract_ready
dry_run_ready
blocked
forbidden

No adapter should be marked live.

Error taxonomy

Define structured error categories for:

validation errors;
routing errors;
idempotency errors;
correlation errors;
adapter unavailable;
forbidden live delivery;
unsupported module;
boundary violation;
external runtime disabled;
malformed envelope;
incompatible contract version.

Each error must have:

code;
category;
severity;
retryable flag;
human-readable message;
safe machine-readable metadata.
Retry policy

Create offline retry policy descriptors only.

Must not implement queue workers or real retry execution.

Allowed:

no_retry
manual_review
retry_when_runtime_adapter_exists
blocked_until_blueprint_approval
Required adapter descriptor examples

Add offline adapter descriptors for:

Telegram Bot → Gateway;
Website → Gateway;
ForPrint CRM → Gateway;
future Mobile App → Gateway;
Gateway → CRM;
Gateway → Operational Registry;
Gateway → Calculator Engine;
Gateway → Prepress Hub;
Gateway → Accounting Registry.

Accounting Registry must remain no automatic posting/no live 1C write.

Mobile App must remain future/planned.

Required preview

Add a terminal preview target:

make adapter-readiness-preview

The preview should show:

adapter name;
direction;
source module;
target module;
delivery mode;
runtime status;
live enabled false;
retry policy;
representative error taxonomy entries.
Required self-checks

Add or extend checks so make check-report validates:

adapter descriptors exist;
all adapter descriptors use canonical Blueprint module IDs;
no adapter is live-enabled;
Accounting Registry adapter does not allow automatic posting or 1C writes;
Mobile App adapter remains planned/future;
retry policies do not create real queues;
error taxonomy exists and is valid;
forprint_calculator_engine is still forbidden;
coordination records remain machine-clean.
Required docs

Add architecture docs, for example:

docs/architecture/adapter_contracts_v0_4.md
docs/architecture/gateway_error_taxonomy_v0_4.md
docs/architecture/gateway_delivery_policy_v0_4.md

Use existing structure where possible.

Required coordination update

Update:

coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml

Expected phase:

adapter_contracts_error_taxonomy_v0_4

Expected completed step:

gateway_adapter_contracts_ready

Add a completion report under:

coordination/reports/

The report must be tracked even if coordination/reports is ignored.

Use:

git add -f coordination/reports/index.yaml coordination/reports/<report-file>.md
Required validation before commit

Run:

make governance-check
make check
make check-report
make channel-intake-preview
make adapter-readiness-preview
grep -R "forprint_calculator_engine" -n app tests scripts examples docs coordination reports || true
git ls-files coordination/reports/index.yaml
git status --short

Expected:

all checks OK;
pytest passes;
channel intake preview OK;
adapter readiness preview OK;
grep returns nothing;
coordination reports index is tracked;
no live integration introduced.
Commit expectation

After checks are green:

git commit -m "Add Gateway adapter contracts and error taxonomy"
git push

Use staged commits if needed.

Boundary

Do not implement:

live API;
database;
queues;
Redis;
S3;
Telegram runtime calls;
Website runtime calls;
CRM runtime calls;
Operational Registry runtime calls;
Calculator runtime calls;
Library runtime calls;
Prepress runtime calls;
Accounting runtime calls;
1C writes;
automatic posting;
final price calculation.

Gateway remains a validation, normalization, routing, idempotency, correlation, audit and contract boundary.
