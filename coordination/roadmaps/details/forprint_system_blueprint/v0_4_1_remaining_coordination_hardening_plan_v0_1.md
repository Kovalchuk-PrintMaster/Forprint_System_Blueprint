# ForPrint v0.4.1 — Remaining Coordination Hardening Plan v0.1

Status: PLANNED / NOT ACTIVE
Current external pilot: H9 Logistics reference rollout.

This document captures missing coordination semantics discovered during the Logistics
pilot discussion. It intentionally does not change the H9 target while the Logistics
assistant is working.

## Why this belongs to v0.4.1

Current lifecycle covers roadmap, queue, active prompt, module execution, completion,
review and next work. Missing is a first-class execution-time clarification path.

A module may need one parameter, access, a cross-module fact, provider capability
confirmation, or an operator decision without the prompt being ready for RETURN/HOLD.

## Q1 — blueprint_v0_4_1_clarification_question_lifecycle_v0_1

Create first-class question threads.

Lifecycle:
`OPEN -> ROUTED -> ANSWERED -> CONFIRMED -> RESOLVED`

Alternative terminals:
`ESCALATED`, `CANCELLED`, `EXPIRED`.

Prompt may remain `in_progress` with `waiting_on_clarification`.

Minimum identity:
question_id, module_id, prompt_id, roadmap_step_id, requester, target,
correlation_id, blocking, question_class, round, question, answer,
evidence_refs and timestamps.

A question alone never means RETURN or HOLD.

## Q2 — blueprint_v0_4_1_bounded_clarification_and_escalation_v0_1

Default:
`maximum_unresolved_round_trips_per_question_thread: 5`

This is per unresolved issue, not five questions for the whole prompt.

After round five:
- autonomous dialogue for that thread stops;
- thread becomes ESCALATED;
- blocking prompt state becomes visibly waiting/blocked;
- escalation packet contains original question, all rounds, evidence, unresolved fact,
  impact, safe options and recommended next action.

## Q3 — blueprint_v0_4_1_execution_blocker_taxonomy_v0_1

Initial reasons:
missing_input, ambiguous_requirement, access_required,
credential_or_token_expired, external_resource_unavailable,
dependency_contract_missing, dependency_module_blocked, provider_api_unavailable,
environment_failure, policy_conflict, unsupported_capability, security_boundary,
manual_decision_required.

Keep distinct:
- clarification_required;
- execution_blocked;
- unable_to_execute;
- RETURN;
- HOLD.

`unable_to_execute` is module evidence for review, not Blueprint RETURN.

## Q4 — blueprint_v0_4_1_immutable_prompt_adjustment_and_decision_v0_1

Canonical rule:

**A released prompt is an immutable execution contract.**

Do not edit/delete/rewrite released prompt requirements.

Later changes use correlated artifacts/events:
operator_decision, scope_adjustment, waiver, skip_optional,
clarification_resolution, blocker_resolution, cancellation,
follow_up_prompt or superseding_prompt.

A requirement that is not executed never disappears. It must have explicit disposition.

Minimum decision evidence:
decision_id, related event/question, prompt_id, requirement/substep/criterion,
actor, decision type, reason code, explanation, timestamp, execution effect,
acceptance effect and evidence refs.

Completion report must include `Execution deviations / operator decisions`,
or explicitly `none`.

## Q5 — blueprint_v0_4_1_common_coordination_event_envelope_v0_1

Define one event envelope before building any daemon.

Fields:
event_id, event_type, occurred_at, producer, target, module_id, prompt_id,
roadmap_step_id, correlation_id, causation_id, severity, blocking,
schema_version, payload, evidence_refs, idempotency_key.

Events are immutable observations; state is projected from events.

Initial families:
claim/status, clarification, answer/resolution, execution blocker,
unable-to-execute, operator attention, operator decision, completion publication.

## Q6 — blueprint_v0_4_1_operator_attention_semantics_v0_1

Define semantic attention reasons without implementing Telegram yet:

clarification_escalated, access_required, execution_blocked, unable_to_execute,
no_dispatchable_work, operator_execution_required, operator_acceptance_required,
manual_review_required, coordination_freshness_stale, dependency_blocked,
repeated_verification_failure.

Attention state is independent from transport.

## Q7 — blueprint_v0_4_1_cross_module_question_routing_contract_v0_1

Allowed target identities:
- module -> Blueprint/operator;
- module -> module;
- Blueprint -> module.

Current v0.4.1 scope is contract/evidence semantics only, not persistent runtime.

Rules:
- no cross-repository writes;
- no module writes Blueprint to deliver live questions;
- answers carry evidence refs;
- strategic ambiguity escalates;
- secrets/access may route directly to operator;
- five-round limit remains per thread.

## Q8 — blueprint_v0_4_1_logistics_clarification_reference_validation_v0_1

After H9 acceptance, prove with Logistics:
- recoverable clarification does not RETURN prompt;
- module and operator routing identities are representable;
- five-round escalation is deterministic;
- blocker reason is explicit;
- released prompt remains immutable;
- scope adjustment is separate evidence;
- completion preserves deviations;
- attention state is visible;
- no automatic ACCEPT;
- no automatic next release;
- no Blueprint write into module repo.

## Proposed order

H8 SEALED -> H9 CURRENT -> Q1 -> Q2 -> Q3 -> Q4 -> Q5 -> Q6 -> Q7 -> Q8
-> H10 ecosystem rollout -> H11 legacy retirement/archive audit.

Stable IDs, not display numbers, are durable.

## Explicitly not part of Q1-Q8

Do not implement here:
persistent daemon, SQLite runtime, systemd, automatic Codex launch,
automatic ACCEPT, automatic next activation, Telegram transport,
intelligent development bot, full autonomous module-to-module runtime,
AgentRunner, broad autonomy/risk classes.

Those belong to the future autonomy initiative.

## H10 entry refinement

Preferred H10 entry:
- H9 accepted;
- Q1-Q8 accepted or explicitly waived;
- current release docs reconciled;
- Logistics still passes as reference;
- no new legacy dependency.
