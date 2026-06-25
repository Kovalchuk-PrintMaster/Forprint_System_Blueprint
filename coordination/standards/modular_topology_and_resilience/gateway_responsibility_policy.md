# Gateway Responsibility Policy

## Purpose

This policy defines the role of ForPrint Integration Gateway in the ForPrint ecosystem.

Gateway should provide reliable transport, validation and routing between modules without becoming a hidden business owner.

## Core responsibility

ForPrint Integration Gateway owns the inter-module handoff boundary.

Gateway may own:

```text
request envelope validation;
response envelope validation;
routing rules;
correlation context;
idempotency records;
delivery ledger;
handoff status;
retry scheduling;
dead-letter records;
manual review queue for delivery failures;
transport audit events;
module availability checks.
```

## What Gateway must not own

Gateway must not own:

```text
client truth;
order truth;
catalog truth;
calculation truth;
payment truth;
invoice truth;
warehouse stock truth;
CRM workflow decisions;
prepress file truth;
production runtime truth.
```

Gateway must not become a central business brain.

## Gateway as reliability layer

Gateway should support reliable handoff using:

```text
correlation_id;
causation_id;
idempotency_key;
schema_version;
payload_hash;
delivery attempts;
retry policy;
dead-letter policy;
manual review status.
```

Gateway should make failed or delayed handoffs visible to operators.

## Gateway and sender responsibility

Sender modules must not assume that a sent handoff is complete until it is acknowledged according to the contract.

Sender modules should retain outbox state until the handoff is accepted or resolved.

Gateway acceptance means the transport layer accepted responsibility for delivery tracking.

Gateway acceptance does not mean the target module accepted the business command.

## Gateway and receiver responsibility

Receiver modules remain responsible for validating business meaning.

Gateway may validate transport and envelope structure.

Receiver validates domain rules.

Example:

```text
Gateway may validate that an order creation command envelope is structurally valid.
Operational Registry decides whether the order command can be accepted as operational truth.
```

## Gateway failure

If Gateway is unavailable, sender modules should retain local outbox entries and retry later.

Important work must not be lost because Gateway is down.

## Target module failure

If a target module is unavailable, Gateway should keep delivery state and retry or move the handoff to manual review according to policy.

Gateway should not silently drop messages.

## Debuggability

Gateway should be designed for operator debugging.

It should be possible to answer:

```text
who sent this message;
what was the target;
what correlation id connects the flow;
what payload hash was sent;
how many attempts were made;
what failed;
whether the receiver accepted it;
whether manual review is required.
```

## Early implementation

The first Gateway reliability implementation should remain lightweight.

Preferred early tools:

```text
PostgreSQL tables;
clear CLI previews;
local tests;
visible YAML or JSON examples;
no mandatory Kafka;
no mandatory Kubernetes;
no hidden background magic.
```

## Future implementation

Future Gateway versions may use message brokers or event streaming when justified.

External broker introduction requires Blueprint approval and must preserve the same business ownership rules.

## Boundary

Gateway transports and tracks handoff.

Owner modules decide and persist business truth.
