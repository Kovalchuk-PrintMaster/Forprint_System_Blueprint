# ForPrint Operator Attention Semantics v0.1

## Status

Active governance standard for the Q6 hardening slice.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/operator_attention_semantics_v0_1.yaml`

## Purpose

Q6 defines semantic operator attention without implementing Telegram, notification delivery,
SQLite runtime or another transport.

**Attention state is semantic coordination state, not transport state and not governance authority.**

The record explains why attention is needed, what subject is affected, what action is requested,
what resolves the attention, whether the underlying condition blocks work, and which evidence
supports the condition. It does not perform or authorize the requested action.

## Canonical attention reasons

Q6 owns exactly these eleven initial reasons:

- `clarification_escalated`
- `access_required`
- `execution_blocked`
- `unable_to_execute`
- `no_dispatchable_work`
- `operator_execution_required`
- `operator_acceptance_required`
- `manual_review_required`
- `coordination_freshness_stale`
- `dependency_blocked`
- `repeated_verification_failure`

Unknown reasons fail closed and require a reviewed versioned contract change.

### Reason boundaries

`clarification_escalated` references an escalated Q1/Q2 thread; Q6 never rewrites the question
history.

`access_required` means an authorized access boundary must be satisfied. Secret values never enter
the attention payload; approved secret references may be used.

`execution_blocked` references Q3 blocker evidence. Q3 remains authoritative for affected-scope
blocking.

`unable_to_execute` references executor evidence and is not Blueprint RETURN/HOLD.

`no_dispatchable_work` means no eligible work is dispatchable now; it does not mean the project, phase or module is complete.

`operator_execution_required` requests a manual action but does not perform or authorize it.

`operator_acceptance_required` requests an explicit governed acceptance decision but is never
ACCEPT/RETURN/HOLD itself.

`manual_review_required` means deterministic evidence is insufficient for the required qualitative
review.

`coordination_freshness_stale` requests revalidation. Staleness is not automatically incompatibility.

`dependency_blocked` does not authorize dependency override.

`repeated_verification_failure` requests review rather than unbounded blind retry.

## Attention lifecycle

The semantic states are:

`OPEN -> ACKNOWLEDGED -> RESOLVED`

Alternative terminal:

`CANCELLED`

Allowed transitions:

- `OPEN -> ACKNOWLEDGED`
- `OPEN -> RESOLVED`
- `OPEN -> CANCELLED`
- `ACKNOWLEDGED -> RESOLVED`
- `ACKNOWLEDGED -> CANCELLED`

### OPEN

Attention exists and has not been semantically acknowledged.

### ACKNOWLEDGED

Acknowledgement means only:

`the attention has been seen and ownership is understood`.

It does **not** mean the underlying issue is fixed, a clarification is resolved, a blocker is
cleared, scope changed, a waiver exists, ACCEPT/RETURN/HOLD occurred, or a notification was merely
delivered/read.

### RESOLVED

The declared resolution criteria are satisfied and evidence is present.

Where another contract owns the underlying truth, that contract must support the resolution:

- Q1/Q2 for clarification truth;
- Q3 for blocker/unable-to-execute semantics;
- Q4 for scope/waiver/operator-decision truth.

Q6 cannot manufacture these outcomes.

### CANCELLED

The attention is no longer applicable because it was superseded, opened in error, or its subject was
cancelled through proper authority. Cancellation does not claim the underlying issue was resolved.

## Q5 event integration

Q6 uses the existing Q5 `operator_attention` family.

Canonical actions:

- `operator_attention.opened`
- `operator_attention.acknowledged`
- `operator_attention.refreshed`
- `operator_attention.resolved`
- `operator_attention.cancelled`

Q6 adds no fields to the Q5 envelope.

Required family payload:

- `attention_id`
- `reason`
- `attention_state`
- `subject_refs`
- `attention_owner`
- `requested_action`
- `resolution_criteria`

Optional family payload references:

- `related_question_id`
- `related_blocker_id`
- `related_decision_id`
- `related_report_id`
- `dependency_refs`
- `supersedes_attention_id`

The Q5 envelope continues to own event identity/time/producer/target/module/prompt/roadmap context,
correlation, causation, severity, blocking, schema version, evidence and idempotency.

`attention_id` is stable for one semantic attention thread. Refresh and acknowledgement reuse it.
A material reason change opens a new attention thread instead of mutating history.

## Severity semantics

For `operator_attention` events Q6 defines:

- `notice` — awareness is useful; immediate action is not implied;
- `action_required` — manual/operator action is required to satisfy resolution criteria;
- `urgent` — meaningful progress is blocked or time-sensitive enough for prompt operator action;
- `critical` — immediate integrity, security, production-safety or similarly high-impact action is required.

Severity never grants authority and never implies ACCEPT/RETURN/HOLD. `critical` is never inferred
from the reason alone; explicit evidence is required.

## Blocking semantics

Attention itself does not create blocking.

The Q5 `blocking` value reflects the underlying owning contract. Therefore:

- `blocking=true` does not imply whole-prompt blocking;
- `blocking=true` does not imply ACCEPT/RETURN/HOLD;
- acknowledgement does not clear blocking;
- only the owning condition/decision contract can establish that underlying truth changed.

## Transport independence

Attention state and notification delivery state are independent.

Q6 does not define Telegram/email/SMS/push delivery, retry state, read receipts or channel
preferences. A transport may deliver one semantic attention multiple times without creating
multiple attention threads.

## Operator acknowledgement versus transport acknowledgement

`ACKNOWLEDGED` is an explicit semantic coordination action by an authorized actor.

It is not inferred from delivery, read state, API success, worker receipt or timeout expiry.

## Resolution evidence

`operator_attention.resolved` requires the same `attention_id`, the resolved semantic state, at least
one Q5 `evidence_refs` entry, satisfied declared resolution criteria and authoritative related
references whenever Q1-Q4 owns the underlying truth.

## Refresh semantics

`operator_attention.refreshed` is a new immutable Q5 event for the same attention thread. It may
update evidence, requested action, owner visibility or severity. It does not rewrite prior events or
change the canonical reason.

## Separation from Q7-Q8

Q6 does not define cross-module question routing/delivery mechanics (Q7) or Logistics reference
validation (Q8). `attention_owner` is an identity string, not a routing policy.

## Runtime boundary

Q6 does not enable live SQLite, an `attention_events` table, notification-delivery persistence,
daemon/systemd, Telegram transport, autonomous workers, automatic module/business ACCEPT,
automatic RETURN/HOLD, automatic next-prompt release, dependency override, cross-repository writes
or business prompt release.

## Acceptance gates

Q6 is ready for deterministic same-phase closeout when the exact eleven reasons, lifecycle,
Q5 actions/payload contract, severity semantics, transport independence, evidence-bound resolution
and no-authority-inference rules are machine validated; Q7-Q8 remain deferred; runtime/transport
remain disabled; focused Q5+Q6 tests and canonical `make check` pass.

This implementation does not close Q6 or activate Q7.
