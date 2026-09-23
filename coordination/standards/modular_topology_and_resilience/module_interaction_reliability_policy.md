# Module Interaction Reliability Policy

## Purpose

This policy defines how ForPrint modules should exchange commands, events, drafts and handoff messages without losing business work when another module, database, server or network path is unavailable.

## Core rule

```text
Store before send.
Retry idempotently.
Never lose a business handoff silently.
```

A module must not create important work and only keep it in process memory while sending it to another module.

## Store-before-send

Before a module sends an important handoff to another module, it must durably store the work or handoff request.

Durable storage may be:

```text
PostgreSQL table;
SQLite file;
local outbox file;
approved event log;
Gateway delivery ledger after accepted handoff.
```

Temporary memory cache is not sufficient for important business handoff.

## Sender outbox

A sender module should maintain an outbox for pending handoffs until delivery is acknowledged.

Typical sender outbox data:

```text
message_id;
correlation_id;
causation_id;
idempotency_key;
source_module;
target_module;
message_type;
schema_version;
payload_hash;
created_at;
status;
attempt_count;
last_error;
next_retry_at;
manual_review_reason.
```

## Gateway delivery ledger

When Gateway accepts a handoff, Gateway should record delivery state in its delivery ledger.

Gateway may then route, retry, reject, dead-letter or mark the handoff for manual review.

## Receiver inbox and idempotency

Receiver modules should protect themselves from duplicate messages.

Receivers should record accepted idempotency keys or inbox entries before applying business changes.

ForPrint should prefer:

```text
at-least-once delivery;
idempotent receivers;
explicit duplicate handling.
```

ForPrint should not promise magical exactly-once delivery.

## Standard handoff states

Common handoff states should include:

```text
created_local;
pending_dispatch;
accepted_by_gateway;
dispatched;
accepted_by_receiver;
rejected_validation;
receiver_unavailable;
retrying;
expired;
dead_letter;
manual_review_required;
manually_resolved;
reconciled.
```

Modules may use a smaller set early, but the meaning must remain compatible with this list.

## Degraded mode

If a dependency is unavailable, a module should enter degraded mode instead of silently losing work.

Examples:

```text
Calculator may store a completed CalculationOutputPackage and mark order handoff as pending.
Telegram Bot may store request context locally until Gateway is available.
Gateway may keep a handoff in retry state until the target module is available.
Operations Control Registry may reject or queue an incoming command depending on its current policy.
CRM may show stale reporting data with a clear warning.
```

A degraded mode must be visible in status reports or operator views when it affects business flow.

## Command versus query behavior

Commands and queries have different reliability expectations.

Commands that change owner truth require durable handoff and idempotency.

Queries may use snapshots or projections when the owner module is unavailable, but stale data must be marked clearly.

## Manual review

If a handoff cannot be delivered or safely retried, it should enter manual review or dead-letter state.

Manual review should preserve:

```text
original payload;
payload hash;
source module;
target module;
correlation id;
last error;
attempt history;
operator notes;
resolution status.
```

## Replay and recovery

After restart or restore, modules should be able to list:

```text
pending outbox messages;
received but unapplied inbox messages;
dead-letter messages;
manual review items;
messages accepted by Gateway but not receiver;
messages accepted by receiver but missing sender acknowledgement.
```

## Business ownership remains unchanged

Reliable handoff does not transfer business ownership.

Examples:

```text
Calculator sends an OrderDraft, but Operations Control Registry decides whether an operational order is created.
Gateway routes an invoice request, but Accounting Registry owns invoice truth.
Telegram sends request context, but it does not own canonical client or order records.
```

## Broker policy

Heavy message brokers are not required for the first ForPrint runtime.

Kafka, RabbitMQ, Redis Streams or similar tools may be evaluated later through Blueprint-approved architecture decisions.

The default early implementation should use:

```text
Gateway;
PostgreSQL outbox and inbox;
idempotency keys;
retry;
dead-letter;
manual review;
reporting visibility.
```

## Boundary

This policy defines reliability semantics.

Gateway-specific responsibilities are defined in `gateway_responsibility_policy.md`.

Data storage ownership is defined in `data_ownership_and_storage_policy.md`.

<!-- bounded-cross-module-execution-envelope-2026-09-01:start -->
## Bounded cross-module execution envelope

Durable retry is not permission for infinite dialogue. AI/cross-module work should carry or derive:
root_request_id, correlation_id, origin_module, hop_count, visited_modules, retry_count,
clarification_round, ai_call_count, ai_budget, time_budget, ttl/deadline and escalation_policy.

Repeated unresolved cycles must stop and enter manual review.

Preferred ladder:
1. deterministic local logic;
2. structured local/domain lookup;
3. structured request to canonical owner;
4. bounded AI intervention;
5. human escalation.
<!-- bounded-cross-module-execution-envelope-2026-09-01:end -->

<!-- FORPRINT_U92_SHARED_RESOURCE_CONCURRENCY_AVAILABILITY_20260903:START -->
## Shared resource concurrency and availability

Cross-module work must persist request state and make waiting/retry semantics explicit.

Recommended lifecycle states:
`RECEIVED`, `QUEUED`, `IN_PROGRESS`, `WAITING_RESOURCE`,
`WAITING_EXTERNAL_DEPENDENCY`, `RETRY_SCHEDULED`, `COMPLETED`, `DEGRADED`, `FAILED`,
`MANUAL_REVIEW_REQUIRED`.

Recommended outcomes:
`OK`, `QUEUED`, `BUSY_RETRYABLE`, `TEMPORARILY_UNAVAILABLE`, `TIMEOUT`, `CONFLICT`,
`NOT_FOUND`, `PERMISSION_DENIED`, `FAILED_PERMANENT`.

`TEMPORARILY_UNAVAILABLE` must never be silently collapsed into `NOT_FOUND`.

Reliability mechanisms include idempotency keys, bounded retries/backoff, deadlines/TTL, circuit
breaker, backpressure, dead-letter/manual review and persistent queue evidence. Gateway owns
transport mechanics; domain owners own transactional concurrency/business decisions; PostgreSQL
owns database-level MVCC/locking; Runtime Inspector observes stuck/retry/health evidence.
<!-- FORPRINT_U92_SHARED_RESOURCE_CONCURRENCY_AVAILABILITY_20260903:END -->
