# Shared Resource Concurrency & Availability Policy v0.1

Status: PROPOSED

## Intent

A request that encounters a busy or temporarily unavailable resource must not be lost, falsely completed, or treated as if the resource does not exist.

## Standard request states

Recommended:
- RECEIVED
- QUEUED
- IN_PROGRESS
- WAITING_RESOURCE
- WAITING_EXTERNAL_DEPENDENCY
- RETRY_SCHEDULED
- COMPLETED
- DEGRADED
- FAILED
- MANUAL_REVIEW_REQUIRED

## Standard outcomes

Recommended:
- OK
- QUEUED
- BUSY_RETRYABLE
- TEMPORARILY_UNAVAILABLE
- TIMEOUT
- CONFLICT
- NOT_FOUND
- PERMISSION_DENIED
- FAILED_PERMANENT

`TEMPORARILY_UNAVAILABLE != NOT_FOUND`.

## Ownership

Gateway:
- route/envelope/status semantics;
- idempotency propagation;
- backpressure/retry transport behavior.

Domain owner:
- transaction boundary;
- resource-specific concurrency;
- business conflict resolution.

Database/infrastructure:
- actual transactional consistency/locking/isolation.

Runtime Inspector:
- stuck requests;
- retry storms;
- timeout/dead-letter/resource-health evidence.

SysAdmin:
- infrastructure outage/recovery.

Operations/Telegram:
- human escalation where policy requires.

## Required mechanisms

- persistent request state;
- idempotency key;
- bounded retry with backoff/jitter;
- timeout/deadline/TTL;
- circuit breaker or equivalent degraded-state protection;
- dead-letter/manual-review path;
- correlation/root request IDs;
- explicit retry-after where useful;
- no AI-only memory of a pending operation.

## Reference case: Cloud Backup

`UPLOAD_READY → INTERNET_UNAVAILABLE → WAITING_EXTERNAL_DEPENDENCY → RETRY_SCHEDULED → INTERNET_RESTORED → UPLOAD_RESUMED → VERIFIED → COMPLETED`

If deadline/SLA is violated:
`DEGRADED → ALERT`
while the task remains durable unless policy explicitly cancels it.

## Reference case: physical printer

One physical printer may have:
- one active job;
- multiple queued jobs;
- explicit eligibility/capability constraints.

Do not model it as multiple agents directly "opening" the same resource without a queue/owner.

## Database access

Prefer short database transactions and normal DB concurrency mechanisms rather than long business locks.

Reads and writes should occur through domain-owned services/read models where practical, not arbitrary direct table access by every module.
