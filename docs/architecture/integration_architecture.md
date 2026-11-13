# ForPrint Integration Architecture

## Status

Current human-readable integration explanation.

Canonical contract and flow status is defined by:

- `machine/contracts.yaml`
- `machine/data_flows.yaml`
- `machine/data_objects.yaml`

## Integration principle

ForPrint should avoid an uncontrolled mesh of private point-to-point assumptions.

Integration is contract-first: a producer/consumer relationship, payload meaning and
ownership boundary should be explicit before runtime coupling is treated as stable.

## CRM versus Integration Gateway

CRM answers:

> What business action should happen?

Integration Gateway answers:

> Is this request valid and where/how should it be transported?

Gateway responsibilities include:

- payload validation and normalization;
- contract-aware routing;
- correlation context;
- idempotency context;
- standardized transport errors;
- security/filtering boundaries;
- audit/transport signals.

Gateway must not decide pricing, invent canonical clients/orders, own catalogs or become
the accounting store.

## Transitional architecture

The repository contains both active direct flows and planned Gateway-mediated flows.

That is intentional transitional state. A human document must not claim that every
current request already passes through Gateway.

For every concrete integration, `machine/data_flows.yaml` and `machine/contracts.yaml`
define whether the relationship is active, planned or otherwise staged.

The target direction is to use Gateway where a shared transport/validation boundary adds
real safety without moving business semantics into the Gateway.

## Channel-agnostic contracts

Telegram, Website and future Mobile App are channels, not separate business cores.

Where possible, business contracts should describe the business request/result rather
than encode one channel's private assumptions into the canonical model.

A channel can:

- collect or clarify input;
- submit a structured request;
- show status/result;
- escalate to a person or AI-assisted workflow.

It should not acquire ownership of price, order, payment or catalog truth.

## Data ownership across integrations

Transport does not change ownership.

Examples:

- Library data consumed by Calculator remains Library-owned;
- an order shown in CRM remains Operations Control Registry-owned;
- accounting status routed to CRM remains Accounting-owned;
- warehouse reservation status remains Warehouse-owned;
- delivery status remains Logistics-owned.

See `machine/ownership.yaml` for the canonical current map.

## Evolution

Integration complexity should grow only when required by real behavior:

1. explicit Blueprint contracts and data flows;
2. validated request/response boundaries;
3. Gateway routing where it provides safety and decoupling;
4. durable inbox/outbox/retry/idempotency where runtime reliability requires it;
5. broker/event infrastructure only when justified by scale and failure modes.

This avoids introducing heavyweight infrastructure merely because it is common in larger
systems.

## Historical source material

The former `human/integration_strategy.md` and
`human/integration_gateway_strategy.md` are preserved in the early-alignment archive.
They remain useful design history but are no longer parallel current strategy documents.
