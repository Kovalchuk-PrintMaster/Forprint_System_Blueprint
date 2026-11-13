# ForPrint Bounded Clarification and Escalation v0.1

## Status

Active governance standard for the Q2 hardening slice.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/bounded_clarification_and_escalation_v0_1.yaml`

## Purpose

Q2 adds a deterministic unresolved-round budget to the Q1 clarification thread.

The limit is:

`maximum_unresolved_round_trips_per_question_thread: 5`

This is **per unresolved question thread**, never five questions for an entire prompt.

Q2 remains a semantics/schema hardening slice. It does not create an autonomous dialogue worker.

## Q1 inheritance

Q2 extends, rather than replaces, the Q1 question lifecycle.

The same `question_id` remains stable across all rounds of one clarification thread.
A question is still not a prompt disposition. A released prompt remains immutable.

## What counts as a round trip

Round `1` is the initial clarification attempt.

A completed unresolved round trip means:

1. the question for that round was routed;
2. an answer was received;
3. the answer was evaluated;
4. the answer was explicitly insufficient to resolve the same clarification thread.

Only then may the thread consume that unresolved round and advance to the next round.

A missing answer does not count as a completed round trip.
An answer that has not yet been evaluated does not advance the counter.
A sufficient answer follows the Q1 path:

`ANSWERED -> CONFIRMED -> RESOLVED`

## Rounds 1 through 4

If the answer is insufficient:

- preserve the completed round record;
- increment `round`;
- keep the same `question_id` and `correlation_id`;
- route the same thread for the next bounded attempt.

Previous rounds are append-only evidence and are never rewritten.

## Round 5 boundary

If the fifth answer is sufficient:

`ANSWERED -> CONFIRMED -> RESOLVED`

No escalation occurs merely because the thread reached round five.

If the completed fifth answer is evaluated as insufficient:

- preserve round five evidence;
- transition the thread to `ESCALATED`;
- stop further autonomous dialogue for that thread;
- do not create round six;
- prepare the escalation packet semantics.

`ESCALATED` remains a terminal state. The same terminal thread is never reopened automatically.

## Escalation packet

Required content includes:

- question/thread identity;
- module/prompt/roadmap correlation;
- requester and logical target;
- `blocking`;
- original question;
- all five completed round records;
- evidence references;
- exact unresolved fact;
- impact;
- safe options;
- recommended next action;
- escalation trigger;
- escalation timestamp.

Safe options and recommended next action are advisory evidence, not automatic authority.

## Prompt coupling

Escalation does not imply `RETURN` or `HOLD`.

For `blocking=false`, the prompt may continue wherever its contract allows.

For `blocking=true`, the affected execution scope becomes visibly:

`waiting_on_clarification_escalation`

Independent prompt work may continue where the contract allows.

This Q2 condition is not the Q3 blocker taxonomy.

## Deferred ownership

Q2 does not define Q3 blocker taxonomy, Q4 operator-decision semantics, Q5 event envelope,
Q6 operator-attention semantics, Q7 live cross-module routing, or Q8 Logistics reference validation.

## Runtime boundary

Q2 does not enable live SQLite runtime, daemon/systemd, Telegram transport, autonomous worker execution,
automatic module/business ACCEPT, automatic RETURN/HOLD, cross-repository writes, or business prompt release.

## Acceptance gates

Q2 implementation is ready for deterministic same-phase closeout when:

1. Q1 inheritance is explicit and SHA-bound;
2. the unresolved limit is exactly five per question thread;
3. no shared per-prompt clarification counter exists;
4. round advancement requires a completed insufficient-answer evaluation;
5. a sufficient answer at round five can still resolve normally;
6. an insufficient completed round five produces `ESCALATED`;
7. round six for the same escalated thread is forbidden;
8. all five round records are preserved;
9. blocking escalation does not imply RETURN/HOLD;
10. Q3-Q8 remain deferred;
11. runtime/autonomy boundaries remain disabled;
12. the validator is part of canonical `make check`;
13. focused tests and canonical Blueprint checks pass.

This implementation does not itself close Q2 or activate Q3. Closeout requires publication/remote containment
and then follows the phase-boundary deterministic progression policy.
