# Prompt: ForPrint Integration Gateway v0.3 — Channel Intake and Operational Handoff Contracts

Generated: `2026-06-10T13:49:51.350526+00:00`

## Target module

`forprint_integration_gateway`

## Pull instruction

This prompt is issued by `forprint_system_blueprint`.

The Integration Gateway assistant should read this prompt from the Blueprint outgoing prompts directory and treat it as the next allowed implementation directive after governance alignment.

Expected source path:

coordination/outgoing_prompts/forprint_integration_gateway/drafts/2026-06-10__gateway__channel_intake_operational_handoff_contracts_v0_3.md

Before starting work, run:

make governance-check
make check
make check-report
git status --short

Do not proceed if the working tree is dirty for unrelated reasons.

Purpose

Develop the next safe Gateway layer that prepares ForPrint for Telegram, Website, CRM, and future Mobile App intake without enabling live production integrations.

The Gateway must remain a validation, normalization, routing, idempotency, correlation, and audit-boundary layer.

It must not become a business brain, CRM, Operational Registry, Library, Accounting Registry, Calculator, Warehouse, or production runtime owner.

Current accepted baseline

Gateway governance alignment is completed.

Expected baseline:

make governance-check passes;
make check passes;
make check-report passes;
module remains boundary-safe;
no real external runtime integrations are enabled.
Main goal of this checkpoint

Create a v0.3 offline contract foundation for channel intake and operational handoff.

This checkpoint should let future Telegram Bot, Website, CRM, and Mobile App submit normalized request envelopes through the Gateway contract model.

Gateway must validate and route those envelopes as offline/local examples only.

No production API, no DB, no queue, no Redis, no S3, no external Telegram/Website/CRM calls.

Required scope

Implement v0.3 contract foundation for:

Channel intake envelope
Client request envelope
Normalized business request
Operational Registry handoff candidate
Gateway validation result
Gateway route decision
Gateway audit/correlation metadata
Idempotency key policy
Example fixtures for Telegram, Website, CRM, and future Mobile App
Terminal preview / smoke runner for v0.3
Required concepts

Add or extend models/schemas/docs for:

ChannelSource
ChannelIntakeEnvelope
ClientIdentityHint
ContactHint
BusinessRequestKind
BusinessRequestPayload
NormalizedGatewayRequest
OperationalRegistryHandoffCandidate
GatewayValidationIssue
GatewayRouteDecision
GatewayCorrelationContext
GatewayIdempotencyPolicy

Supported channel sources:

telegram_bot
website
forprint_crm
mobile_app

Mobile App must remain planned/future, not active runtime.

Example request kinds

At minimum support offline examples for:

new order request
order clarification
price estimate request
client lookup request
file/prepress request
manager handoff request

These are contracts/examples only. Do not implement live workflow execution.

Boundary rules

Gateway must not:

own client accounts;
own orders;
own accounting records;
own warehouse stock;
own canonical products/materials;
calculate final prices;
call live Telegram APIs;
call live Website APIs;
call live CRM APIs;
call live Operational Registry API;
create production DB tables;
create real queue consumers/producers;
perform automatic posting;
write to 1C.

Gateway may:

validate envelopes;
normalize field names and channel metadata;
classify request kind using deterministic local rules;
prepare routing decision objects;
prepare offline handoff candidate fixtures;
preserve raw channel values alongside normalized fields;
generate audit/correlation metadata;
reject invalid envelopes with clear validation issues.
Suggested files

Use existing module structure where possible.

Suggested additions:

docs/architecture/channel_intake_contracts_v0_3.md
docs/architecture/operational_handoff_contracts_v0_3.md
examples/channel_intake/
examples/operational_handoff/
schemas/
app/
tests/
scripts/

Do not introduce a new architecture layout if the module already has established locations.

Required terminal preview

Add a terminal preview target, for example:

make channel-intake-preview

The preview should show:

accepted Telegram sample;
accepted Website sample;
accepted CRM sample;
future Mobile App sample marked planned/future;
invalid sample with validation errors;
resulting route decisions;
generated correlation/idempotency fields.
Required validation

Before commit, run:

make governance-check
make check
make check-report
make channel-intake-preview
git status --short

All checks must pass.

Required coordination update

Update module coordination status and report index.

Current phase should become:

channel_intake_operational_handoff_contracts_v0_3

Last completed step should become:

gateway_channel_intake_contracts_ready

The final module report must explicitly state:

no production API added;
no real external integrations added;
no DB ownership added;
no operational data ownership added;
examples are offline fixtures only;
Gateway remains a validation/routing boundary.
Commit expectation

Use staged commits if needed.

Final commit message should be similar to:

git commit -m "Add Gateway channel intake and handoff contracts"

Push after checks are green.

Pause conditions

Stop and ask Blueprint before proceeding if:

live API/server exposure seems required;
a DB/queue/Redis/S3 dependency seems required;
direct Operational Registry/Telegram/Website/CRM runtime call seems required;
business ownership starts drifting into Gateway;
Calculator/Library/Accounting/Warehouse ownership boundaries become unclear.
