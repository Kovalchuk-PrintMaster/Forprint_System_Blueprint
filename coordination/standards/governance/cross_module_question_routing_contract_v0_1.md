# ForPrint Cross-Module Question Routing Contract v0.1

## Status

Active governance standard for the Q7 hardening slice.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/cross_module_question_routing_contract_v0_1.yaml`

## Purpose

Q7 defines how a first-class Q1/Q2 clarification question may select a logical destination across
ForPrint coordination boundaries without requiring live runtime delivery and without permitting any
repository to write into another repository.

The core rule is:

**Routing selects a logical respondent; it does not grant mutation authority, disposition authority,
or transport capability.**

Q7 is contract/evidence semantics only.

## Canonical route directions

Q7 owns exactly three route directions:

- `module_to_blueprint_or_operator`
- `module_to_module`
- `blueprint_to_module`

These correspond to the current v0.4.1 authority:

- module -> Blueprint/operator;
- module -> module;
- Blueprint -> module.

Operator -> module is not added as a separate Q7 route direction in this version.

## Q1 identity is preserved

Q7 does not replace the Q1 question thread.

The following Q1 identities remain stable across routing and rerouting:

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
- timestamps

`requester` and `target` remain logical actor references, not transport addresses.

`question_id` is stable for the thread.

`correlation_id` remains distinct from `question_id`.

## Routing record

Every routing attempt is represented as separate append-only evidence with:

- `routing_id`
- `question_id`
- `module_id`
- `prompt_id`
- `roadmap_step_id`
- `requester`
- `target`
- `route_direction`
- `correlation_id`
- `blocking`
- `question_class`
- `round`
- `routing_reason`
- `routing_outcome`
- `evidence_refs`
- `routed_at`

A routing record does not rewrite the question thread or any prior routing record.

A reroute creates a new `routing_id` while preserving `question_id` and `correlation_id`.

## Routing outcomes

Q7 uses three routing outcomes:

- `routed`
- `no_eligible_route`
- `operator_escalation_required`

`routed` means a logical target was selected.

`no_eligible_route` means Q7 could not identify a safe eligible logical route under current
contracts/evidence.

`operator_escalation_required` means manual operator/Blueprint attention is needed before safe
routing can continue.

No routing outcome is RETURN, HOLD or ACCEPT.

## Round-budget preservation

Q2 remains the sole owner of the five-round unresolved clarification limit.

Q7 preserves:

`maximum_unresolved_round_trips_per_question_thread = 5`

Routing or rerouting by itself does not consume a round.

A round advances only under Q2 after:

1. a routed question receives an answer;
2. the answer is evaluated;
3. the answer is insufficient for the same thread.

A missing route, failed route, reroute or transport failure does not invent a completed unresolved
round.

No Q7 rule allows round 6.

## Module -> Blueprint/operator

Use `module_to_blueprint_or_operator` when the module needs a Blueprint/operator fact, decision,
access boundary or strategic resolution.

The target remains a logical identity.

Q7 does not require a Telegram username, email address or other transport-specific address.

## Module -> module

Use `module_to_module` for a question whose factual/contract answer is owned by another ForPrint
module.

The asking module does not write the target module repository.

The target module does not write the requester repository merely to answer.

The answer is returned as evidence through the coordination contract/future service boundary.

A module-to-module answer does not automatically change Blueprint project truth.

If the answer requires a scope change, waiver or other durable governance decision, Q4 remains the
authority.

## Blueprint -> module

Use `blueprint_to_module` when Blueprint needs a module-owned fact, capability confirmation,
contract detail or evidence.

This route does not authorize Blueprint to mutate the module repository.

## Answer evidence

Every routed answer must carry:

- `question_id`
- `responder`
- `correlation_id`
- `round`
- `answer`
- `evidence_refs`
- `answered_at`

`evidence_refs` must contain at least one stable evidence reference.

An answer with no evidence refs is not sufficient routing evidence under Q7.

Evidence may reference reports, canonical artifacts, Git objects, approved external/provider
evidence or approved secret references.

Secret values are forbidden.

## Strategic ambiguity

Strategic ambiguity does not silently route to another module for a guessed answer.

When the unresolved fact materially affects:

- project direction;
- module ownership/boundary;
- roadmap intent;
- scope/acceptance authority;
- dependency override;
- architecture/governance policy;

Q7 requires `operator_escalation_required` to Blueprint/operator authority.

This routing escalation is not itself the operator decision.

Q4 remains authoritative for resulting scope/waiver/operator-decision artifacts.

## Access and secrets

Questions about access, credentials, secret-controlled resources or explicit manual access authority
may route directly to the operator.

The question/routing/answer evidence may contain secret references.

It must never contain secret values.

Q7 routing does not grant the requested access.

## Blocking

Q7 preserves Q1/Q3 affected-scope semantics.

A blocking clarification may keep the affected execution scope waiting.

Routing does not widen affected scope into whole-prompt RETURN/HOLD.

A successful route does not clear blocking.

An answer does not clear blocking until the owning clarification/blocker semantics say the
underlying condition is resolved.

## Event integration

Q7 uses the existing Q5 event envelope without adding envelope fields.

Relevant semantic actions may include:

- `clarification.routed`
- `clarification.rerouted`
- `clarification.route_failed`
- `clarification.escalated`
- `answer_resolution.received`

Q7 defines only contract meaning.

It does not implement event persistence or delivery.

## Operator attention integration

Q7 may surface an existing Q6 attention reason when routing cannot continue safely.

Examples:

- bounded clarification escalation -> `clarification_escalated`;
- secret/access boundary -> `access_required`;
- strategic ambiguity -> `manual_review_required`;
- dependency route unavailable -> `dependency_blocked`.

Q7 does not redefine Q6 attention lifecycle or transport.

## No cross-repository writes

Q7 has an absolute v0.4.1 boundary:

- Blueprint does not write a module repository to deliver a live question;
- a module does not write Blueprint to deliver a live question;
- a module does not write another module repository to deliver or answer a question.

Future routing must use a controlled coordination service/operational store boundary or another
separately approved mechanism.

## No inferred authority

A route, answer or route evidence does not automatically:

- ACCEPT a prompt;
- RETURN a prompt;
- HOLD a prompt;
- waive a requirement;
- adjust prompt scope;
- clear a Q3 blocker;
- release a next prompt;
- authorize dependency override;
- authorize credentials/security actions;
- authorize production/destructive actions.

Existing manual authority remains unchanged.

## Separation from Q8

Q8 will validate the combined Q1-Q7 clarification/blocker/attention/routing semantics against the
Logistics reference flow.

Q7 does not perform the Logistics reference validation.

## Runtime boundary

Q7 does not enable:

- persistent question routing runtime;
- live SQLite;
- question/route database tables;
- daemon/systemd;
- Telegram transport;
- autonomous module-to-module messaging;
- automatic module/business ACCEPT;
- automatic RETURN/HOLD;
- automatic next-prompt release;
- cross-repository writes;
- business prompt release.

## Acceptance gates

Q7 implementation is ready for deterministic same-phase closeout when:

1. the exact three route directions are canonical;
2. Q1 question identity is preserved across routing/rerouting;
3. routing attempts are append-only evidence;
4. rerouting preserves `question_id` and `correlation_id`;
5. Q2 remains the sole owner of the exact five-round per-thread limit;
6. routing/rerouting alone does not consume a round;
7. every routed answer carries at least one evidence ref;
8. strategic ambiguity escalates to Blueprint/operator authority;
9. access/secret questions may route directly to operator without secret values;
10. no route/answer implies ACCEPT/RETURN/HOLD/scope change/waiver;
11. no cross-repository write is authorized;
12. Q5/Q6 integrations are semantic only and do not enable transport/runtime;
13. Q8 remains deferred;
14. the Q7 validator is in canonical `make check`;
15. focused Q6+Q7 tests and canonical Blueprint checks pass.

This implementation does not itself close Q7 or activate Q8. Closeout requires published evidence
and the separate deterministic same-phase gate.
