# ForPrint Clarification Question Lifecycle v0.1

## Status

Active governance standard for the Q1 hardening slice.

Adoption mode: `prompt_or_directive_required`.

The machine-readable authority is:

`coordination/standards/governance/clarification_question_lifecycle_v0_1.yaml`

## Purpose

Q1 creates a first-class clarification-question thread that is distinct from
prompt disposition, completion review, RETURN/HOLD, transport, and future
autonomous runtime.

A module, Blueprint, or operator may need one missing fact, parameter, access
confirmation, or interpretation while the prompt itself is still valid and may
remain in progress. Q1 gives that clarification a durable identity and explicit
lifecycle instead of overloading completion or RETURN/HOLD semantics.

## Core rule

**A question is a clarification object, not a prompt disposition.**

Creating, routing, answering, confirming, resolving, escalating, cancelling, or
expiring a question does not by itself ACCEPT, RETURN, HOLD, cancel, supersede,
or mutate the released prompt.

A released prompt remains an immutable execution contract. Clarification
evidence is correlated to it rather than rewriting it.

## First-class question thread

Every Q1 thread carries at least:

- `question_id`
- `module_id`
- `prompt_id`
- `roadmap_step_id`
- `requester`
- `target`
- `correlation_id`
- `blocking`
- `question_class`
- `round`
- `question`
- `answer`
- `evidence_refs`
- `timestamps`

`question_id` is stable and immutable for the life of the thread.

`correlation_id` links the clarification to the surrounding execution or
coordination chain without replacing `question_id`.

`requester` and `target` are logical actor references, not Telegram addresses,
email addresses, or other transport-specific routing details.

`question_class` is an extensible semantic label. Q1 does not define the Q3
blocker taxonomy.

`round` is present from Q1 but has no Q1 maximum. The five-round unresolved
limit belongs to Q2.

`answer` may be absent until the thread reaches `ANSWERED`.

`evidence_refs` contain references and hashes/paths/IDs where appropriate;
secret values, credentials, passwords, and tokens must not be embedded in the
question, answer, or evidence payload.

## Lifecycle

Normal lifecycle:

`OPEN -> ROUTED -> ANSWERED -> CONFIRMED -> RESOLVED`

Meaning:

- `OPEN` — the question thread exists and has not yet been routed.
- `ROUTED` — a logical target has been selected and the question is awaiting an
  answer.
- `ANSWERED` — an answer exists, but it is not yet confirmed as sufficient.
- `CONFIRMED` — the requester or authorized confirmer has confirmed that the
  answer addresses the clarification.
- `RESOLVED` — the clarification thread is closed successfully.

Alternative terminal states:

- `ESCALATED`
- `CANCELLED`
- `EXPIRED`

`RESOLVED`, `ESCALATED`, `CANCELLED`, and `EXPIRED` are terminal. A terminal
thread cannot transition back into the active lifecycle.

Q1 defines the state and terminal semantics only. It does not define the Q2
automatic/bounded escalation threshold.

## Timestamp semantics

Every thread has `created_at` and `state_changed_at`.

State-specific timestamps are required when applicable:

- `routed_at` for `ROUTED` or later normal states;
- `answered_at` for `ANSWERED` or later normal states;
- `confirmed_at` for `CONFIRMED` or `RESOLVED`;
- `resolved_at` for `RESOLVED`;
- `terminal_at` for `ESCALATED`, `CANCELLED`, or `EXPIRED`.

Timestamps are UTC-compatible ISO-8601 values in future runtime
implementations. Q1 defines semantics, not a live persistence engine.

## Prompt coupling

A prompt may remain:

`in_progress`

while carrying the coordination condition:

`waiting_on_clarification`

This condition is not equivalent to RETURN or HOLD.

`blocking` is explicit thread data. When `blocking=true`, the question blocks
the affected execution scope. It does not automatically mean that the whole
prompt must be RETURNED or HELD. Independent work may continue where the prompt
contract allows it.

RETURN, HOLD, cancellation, scope adjustment, waiver, or acceptance require
their own explicit governance/operator decision and evidence.

## Relationship to existing reporting artifacts

Existing module artifacts such as:

`coordination/status/next_questions_for_blueprint.md`

may surface questions for human review, but they are not the canonical Q1
lifecycle contract by themselves.

Likewise, an existing reporting status such as `returned_for_fix` remains an
explicit completion/review disposition. It is not automatically produced merely
because a Q1 clarification exists.

This distinction preserves existing reporting workflows without allowing them
to collapse clarification into RETURN/HOLD.

## Storage boundary

Q1 is a semantics/schema hardening slice.

It does not create a SQLite file, database table, daemon, systemd service, or
autonomous worker.

Per B2, future high-churn `question_threads` and `question_messages` belong to a
future coordination operational store only when that runtime is separately
activated. Q1 keeps the contract backend-independent.

## Deferred boundaries

Q1 intentionally does not implement:

- Q2 five-round unresolved clarification limit or automatic escalation;
- Q3 blocker taxonomy;
- Q4 immutable operator-decision adjustment model beyond preserving prompt
  immutability;
- Q5 common event envelope;
- Q6 operator-attention semantics;
- Q7 cross-module routing mechanics;
- Q8 Logistics reference validation;
- live SQLite runtime;
- daemon/systemd execution;
- Telegram transport;
- automatic ACCEPT;
- automatic next activation;
- autonomous execution;
- cross-repository writes.

## Acceptance gates

Q1 implementation is ready for acceptance review when all of the following are
true:

1. the normal and alternative terminal lifecycle is explicit and machine
   validated;
2. the minimum thread identity is explicit and machine validated;
3. prompt `in_progress + waiting_on_clarification` semantics are explicit;
4. a question alone never implies RETURN or HOLD;
5. terminal-state and answer/confirmation semantics are test-covered;
6. Q2-Q8 and runtime capabilities remain outside the implementation;
7. the standard is indexed and its validator is part of `make check`;
8. focused tests and the canonical Blueprint check suite pass.

Q1 acceptance does not itself activate Q2.
