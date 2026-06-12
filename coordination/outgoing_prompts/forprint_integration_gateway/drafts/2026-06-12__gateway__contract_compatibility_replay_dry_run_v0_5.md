# Prompt: ForPrint Integration Gateway v0.5 — Contract Compatibility Matrix, Replay Fixtures, and Dry-run Delivery Planner

Generated: `2026-06-12T13:51:21.142727+00:00`

## Target module

`forprint_integration_gateway`

## Source

This prompt is issued by `forprint_system_blueprint`.

Read it through:

```bash
make blueprint-prompts-list
make blueprint-prompt
Purpose

Gateway v0.5 must build the next hard foundation after v0.4 adapter contracts and error taxonomy.

Gateway v0.4 introduced adapter descriptors, delivery policy, runtime status, error taxonomy and offline adapter readiness preview.

Gateway v0.5 must add a compatibility and replay layer so future module adapters can be checked before any live integration exists.

This checkpoint is still offline / dry-run / contract-only.

Do not enable live runtime delivery.

Accepted baseline

Gateway v0.4 baseline:

3a97012 Add Gateway adapter contracts and error taxonomy
3f51c41 Add Gateway v0.4 coordination report

Expected baseline:

make governance-check passes;
make check passes;
make check-report passes;
make channel-intake-preview passes;
make adapter-readiness-preview passes;
no non-canonical module ids in source files;
Gateway remains offline / contract-only.
Main goal

Create Gateway v0.5 foundations for:

contract compatibility matrix;
contract versioning rules;
dry-run delivery planner;
replay fixtures;
golden path fixtures;
negative / forbidden path fixtures;
adapter readiness scoring;
boundary violation detector;
compatibility preview;
replay preview;
check-report integration;
updated coordination records and completion report.
Required concepts

Add or extend models/docs/examples for:

GatewayContractVersion
GatewayContractCompatibilityRule
GatewayContractCompatibilityResult
GatewayCompatibilityMatrix
GatewayDryRunDeliveryPlan
GatewayDryRunDeliveryStep
GatewayReplayFixture
GatewayReplayResult
GatewayGoldenPathFixture
GatewayBoundaryViolation
GatewayAdapterReadinessScore

Use existing v0.4 adapter contract and error taxonomy concepts instead of duplicating them.

Contract compatibility matrix

Create a matrix that can describe whether a source flow is compatible with a target module contract.

Required source flows:

telegram_bot.new_order_request
website.price_estimate_request
forprint_crm.client_lookup_request
mobile_app.file_prepress_request

Required target module contracts:

forprint_crm.order_intake
forprint_operational_registry.client_lookup_candidate
forprint_operational_registry.order_handoff_candidate
calculator_engine.quote_preview
forprint_prepress_hub.prepress_job_candidate
forprint_accounting_registry.accounting_reference_candidate

Use canonical module ids only.

Canonical Calculator id is:

calculator_engine

Forbidden non-canonical id:

forprint_calculator_engine
Compatibility result states

Support result states such as:

compatible
compatible_dry_run_only
planned_future
blocked_by_policy
blocked_by_boundary
incompatible_contract_version
missing_required_field
unsupported_target_module
forbidden_live_delivery
Dry-run delivery planner

Add a dry-run planner that can build a delivery plan without sending anything.

Each dry-run delivery plan must include:

source module;
target module;
operation;
contract version;
delivery mode;
runtime status;
live delivery enabled false;
idempotency key;
correlation id;
compatibility result;
boundary flags;
planned steps;
expected owner module;
error result if blocked.

No real delivery.

No queue.

No Redis.

No DB writes.

No external API calls.

Replay fixtures

Add offline replay fixtures for:

Golden paths
telegram new order -> CRM intake + Operational Registry handoff candidate
website price estimate -> Calculator quote preview dry-run
CRM client lookup -> Operational Registry lookup candidate
future mobile prepress request -> Prepress Hub planned-future dry-run
Negative paths
missing client identity -> validation error
unsupported target module -> routing/compatibility error
live delivery requested -> forbidden live delivery
wrong contract version -> incompatible contract version
Accounting Registry posting attempt -> blocked by policy
1C write attempt -> blocked by policy
Required preview targets

Add:

make compatibility-matrix-preview
make replay-fixtures-preview

compatibility-matrix-preview should show:

source flow;
target module;
operation;
contract version;
compatibility state;
delivery mode;
live enabled false;
notes.

replay-fixtures-preview should show:

fixture id;
fixture type: golden / negative;
expected result;
actual result;
compatibility state;
delivery plan status;
boundary status.
Required check-report integration

Extend make check-report so it validates:

compatibility matrix exists;
replay fixtures exist;
golden paths pass;
negative paths are blocked as expected;
no live delivery is enabled;
Accounting Registry cannot post or write to 1C;
Mobile App remains planned/future;
no queues/Redis/S3/DB ownership are introduced;
no non-canonical module ids exist in source-controlled text files;
generated __pycache__ does not affect canonical id guard;
coordination records remain machine-clean.
Cache hygiene

The canonical module id guard must ignore generated binary/cache files:

__pycache__
*.pyc
.pytest_cache

But source-controlled text files must still be checked strictly.

Required docs

Add architecture docs, for example:

docs/architecture/contract_compatibility_matrix_v0_5.md
docs/architecture/dry_run_delivery_planner_v0_5.md
docs/architecture/replay_fixtures_v0_5.md
Required coordination update

Update:

coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md

Expected phase:

contract_compatibility_replay_dry_run_v0_5

Expected completed step:

gateway_contract_compatibility_ready

Add completion report under:

coordination/reports/

The report must be tracked even if coordination/reports is ignored.

Use:

git add -f coordination/reports/index.yaml coordination/reports/<report-file>.md
Required validation before commit

Run:

find app tests scripts examples docs coordination reports -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +

make governance-check
make check
make check-report
make channel-intake-preview
make adapter-readiness-preview
make compatibility-matrix-preview
make replay-fixtures-preview

grep -R --exclude-dir="__pycache__" --exclude="*.pyc" "forprint_calculator_engine" -n app tests scripts examples docs coordination reports || true

git ls-files coordination/reports/index.yaml
git status --short

Expected:

all checks OK;
pytest passes;
channel intake preview OK;
adapter readiness preview OK;
compatibility matrix preview OK;
replay fixtures preview OK;
grep returns nothing from source-controlled text;
coordination reports index is tracked;
no live integration introduced.
Commit expectation

After checks are green:

git commit -m "Add Gateway contract compatibility and replay dry-run"
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

Gateway remains a validation, normalization, routing, idempotency, correlation, audit, adapter-contract, compatibility and dry-run planning boundary.
