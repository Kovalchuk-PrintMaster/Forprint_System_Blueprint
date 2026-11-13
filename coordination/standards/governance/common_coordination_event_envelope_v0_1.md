# ForPrint Common Coordination Event Envelope v0.1

## Status

Active governance standard for the Q5 hardening slice.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/common_coordination_event_envelope_v0_1.yaml`

## Purpose

Q5 defines one common immutable event envelope before any live coordination daemon or event store
is built.

The core rule is:

**Events are immutable observations; current state is a projection derived from events.**

Q5 standardizes event identity, context, correlation, causation, evidence and idempotency without
turning the Blueprint repository into a live runtime.

## Canonical envelope

Every Q5 event has exactly these envelope fields:

- `event_id`
- `event_type`
- `occurred_at`
- `producer`
- `target`
- `module_id`
- `prompt_id`
- `roadmap_step_id`
- `correlation_id`
- `causation_id`
- `severity`
- `blocking`
- `schema_version`
- `payload`
- `evidence_refs`
- `idempotency_key`

All field names are present in the envelope even when a context field is not applicable.

The nullable context fields are:

- `module_id`
- `prompt_id`
- `roadmap_step_id`
- `causation_id`

`event_id`, `event_type`, `occurred_at`, `producer`, `target`, `correlation_id`, `severity`,
`schema_version` and `idempotency_key` are non-empty.

`blocking` is boolean.

`payload` is a mapping/object.

`evidence_refs` is a list. Family-specific contracts may require one or more evidence refs.

## Event type format

`event_type` uses:

`<family>.<action>`

The family is controlled by Q5. The action is a stable lower-case token owned by the producing
contract.

Initial canonical families:

- `claim_status`
- `clarification`
- `answer_resolution`
- `execution_blocker`
- `unable_to_execute`
- `operator_attention`
- `operator_decision`
- `completion_publication`

This is an initial family set for the current hardening scope. Adding another family later requires
a reviewed versioned contract change.

## Event family ownership

### claim_status

Carries execution claim/status observations.

It does not itself define the entire prompt/runtime state machine.

### clarification

Carries Q1/Q2 clarification observations.

Q1/Q2 question-thread identity and history remain authoritative.

### answer_resolution

Carries answer/resolution observations correlated to clarification work.

It does not rewrite Q1/Q2 question history.

### execution_blocker

Carries Q3 blocker observations.

A blocking event does not itself issue `RETURN` or `HOLD`.

### unable_to_execute

Carries executor evidence that declared execution cannot safely proceed.

It remains executor evidence, not a Blueprint disposition.

### operator_attention

Reserves an event family for operator-attention observations.

Q6 owns attention reasons, severity interpretation and attention semantics. Q5 does not implement
Telegram or any other notification transport.

### operator_decision

Carries references/payload for Q4 decision/adjustment observations.

The Q4 durable decision artifact remains authoritative for project-truth changes.

### completion_publication

Carries completion-publication observations and evidence references.

A completion publication event is not operator ACCEPT.

## Immutable observation rule

Once published, an event is never edited or deleted.

A correction, reversal or superseding fact is represented by a new event that preserves correlation
and appropriate causation/evidence.

An event records what was observed or decided at a point in time. It is not a mutable status row.

## State projection rule

Current coordination state is derived from event history plus canonical Git-governed artifacts.

A projection is disposable derived state, not an independently mutable source of truth.

Q5 does not implement a projection engine.

The future operational store may maintain projections for fast reads, but projections must remain
rebuildable from authoritative event history and referenced canonical artifacts.

Q5 does not add a global ordering field to the envelope. `occurred_at` is not a guaranteed total
ordering primitive. Future runtime storage may maintain deterministic journal ordering outside the
envelope contract.

## Correlation

`correlation_id` is required on every event.

Events that belong to the same workflow/thread/decision chain reuse the appropriate stable
correlation identity.

Correlation groups related work; it does not imply direct causation.

## Causation

`causation_id` is either:

- `null` for a root event; or
- the `event_id` of the immediate causal predecessor known to the producer.

Causation is not fabricated when the immediate cause is unknown.

Q5 does not require a causal graph to be complete for unrelated historical events.

## Idempotency

`idempotency_key` identifies one logical event publication across safe retries.

Rules:

1. a retry of the same logical event reuses the same idempotency key;
2. the same key with materially equivalent logical content is a duplicate publication attempt;
3. the same key with materially different logical content is an idempotency conflict;
4. conflicts fail closed and require explicit review/recovery;
5. generating a new key merely to bypass a detected conflict is invalid;
6. idempotency does not authorize event mutation.

Q5 defines these semantics but does not implement an idempotency database.

## Time

`occurred_at` is an offset-aware UTC timestamp.

Canonical serialization uses `Z` or `+00:00`.

Producer-local wall-clock values without an offset are invalid.

## Producer and target

`producer` and `target` are stable non-secret identity strings.

Q5 intentionally does not define Q7 cross-module routing rules or all allowed identity relationships.

Q7 will define question-routing identities and delivery constraints.

## Severity

`severity` is a required structural token carried by the event.

Q5 does not define operator-attention reason semantics, notification thresholds or transport
behavior from severity.

Those belong to Q6.

Therefore:

- severity does not automatically notify an operator;
- severity does not grant authority;
- severity does not imply `RETURN`, `HOLD` or ACCEPT.

## Blocking

`blocking` is a required boolean observation.

`blocking=true` means the event reports a blocking condition according to the producing contract.

It does not automatically mean:

- whole-prompt blocking;
- `RETURN`;
- `HOLD`;
- cancellation;
- operator ACCEPT;
- notification delivery.

Q3 affected-scope semantics remain authoritative for blockers.

## Schema version and payload

`schema_version` identifies the event/payload contract used to interpret the event.

`payload` contains family/action-specific data and remains separate from envelope identity.

Payloads:

- must be mappings/objects;
- must not contain secret values;
- may contain approved secret references;
- must not silently rewrite canonical Q1-Q4 histories or Git-governed project truth.

Future family payload schemas remain versioned.

## Evidence references

`evidence_refs` carries stable references to reports, artifacts, Git objects or other approved
evidence.

The envelope does not embed large logs/archives by default.

This preserves the B2 filesystem/artifact-store boundary.

## Separation from canonical Git truth

High-churn operational events belong to the future coordination operational store.

Durable project-truth changes such as Q4 waivers/scope adjustments/decisions remain explicit
Git-governed artifacts.

An event may reference a canonical artifact; it does not silently replace it.

## Separation from Q6-Q8

Q5 does not define:

- operator-attention reasons, severity interpretation or transport (Q6);
- cross-module question-routing mechanics (Q7);
- Logistics reference validation (Q8).

## Runtime boundary

Q5 does not enable:

- live SQLite;
- an `event_journal` database table;
- a projection database;
- schema migrations;
- daemon/systemd;
- Telegram transport;
- autonomous workers;
- automatic module/business ACCEPT;
- automatic RETURN/HOLD;
- automatic next-prompt release;
- cross-repository writes;
- business prompt release.

## Acceptance gates

Q5 implementation is ready for deterministic same-phase closeout when:

1. the exact seventeen envelope fields are canonical;
2. the exact eight initial event families are canonical;
3. event type uses `<family>.<action>`;
4. events are immutable observations;
5. mutable state is explicitly projection, not event history;
6. correlation is required and causation is nullable/immediate-parent semantics;
7. idempotency key is required and key/content collision fails closed;
8. UTC offset-aware event time is required;
9. blocking cannot imply RETURN/HOLD/ACCEPT or whole-prompt block;
10. severity cannot imply attention/transport/authority;
11. Q1-Q4 histories and Git project truth cannot be silently rewritten by payloads;
12. Q6-Q8 remain deferred;
13. no live SQLite/daemon/projection engine is enabled;
14. the Q5 validator is in canonical `make check`;
15. focused Q4+Q5 tests and canonical Blueprint checks pass.

This implementation does not itself close Q5 or activate Q6. Closeout requires published evidence
and the separate deterministic same-phase gate.
