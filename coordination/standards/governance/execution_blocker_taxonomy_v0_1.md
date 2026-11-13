# ForPrint Execution Blocker Taxonomy and Prompt Blocking Semantics v0.1

## Status

Active governance standard for the Q3 hardening slice.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/execution_blocker_taxonomy_v0_1.yaml`

## Purpose

Q3 defines a stable vocabulary for execution-time blocking without collapsing several different
concepts into one overloaded prompt status.

The core separation is:

- `clarification_required` — a coordination condition;
- `execution_blocked` — a coordination condition;
- `unable_to_execute` — executor evidence/outcome;
- `RETURN` — explicit governance disposition;
- `HOLD` — explicit governance disposition.

These concepts are related but not interchangeable.

## Core rule

**A blocker is evidence/condition, not an automatic prompt disposition.**

A module may become unable to continue one affected execution scope while the released prompt
remains immutable and independent work continues where allowed.

Neither `clarification_required`, `execution_blocked` nor `unable_to_execute` automatically means
`RETURN` or `HOLD`.

## Coordination conditions

### clarification_required

Use when the execution needs an answer to a concrete clarification question.

It is governed by Q1/Q2 question semantics.

If `blocking=false`, the clarification is visible but does not stop the affected execution scope.

If `blocking=true`, the affected scope waits for clarification resolution.

The prompt itself is not automatically returned or held.

### execution_blocked

Use when an identified execution scope cannot safely progress because a concrete blocker exists.

For `execution_blocked`:

- `blocking` must be `true`;
- at least one affected scope reference is required;
- one canonical blocker reason is required;
- evidence references are required;
- the affected scope cannot progress while the blocker is active;
- independent prompt work may continue where its contract allows;
- the blocker does not itself issue RETURN/HOLD.

## unable_to_execute

`unable_to_execute` is executor-produced evidence that a declared execution attempt cannot safely or
correctly proceed under the current inputs, dependencies, capabilities, authority or environment.

It is not a Blueprint decision.

It must identify:

- execution/prompt/module context;
- canonical reason code;
- affected scope;
- what was attempted or verified;
- evidence;
- safe next options.

Governance may later resolve the cause, create a clarification, adjust scope, issue RETURN/HOLD or
take another explicit action. Q4 owns the decision/adjustment correlation model.

## Canonical blocker reason codes

Q3 owns the following initial reason vocabulary:

- `missing_input`
- `ambiguous_requirement`
- `access_required`
- `credential_or_token_expired`
- `external_resource_unavailable`
- `dependency_contract_missing`
- `dependency_module_blocked`
- `provider_api_unavailable`
- `environment_failure`
- `policy_conflict`
- `unsupported_capability`
- `security_boundary`
- `manual_decision_required`

Reason codes explain **why** an execution condition/outcome exists. They are not prompt dispositions.

## Reason semantics

### missing_input

A required input, artifact, value or evidence reference is unavailable.

### ambiguous_requirement

Authoritative material permits materially different interpretations and execution cannot choose one
safely without clarification/decision.

### access_required

Execution requires access that is not currently available and must be provided through an authorized
path.

### credential_or_token_expired

Required authentication material is expired/unusable. Evidence must never contain secret values.

### external_resource_unavailable

A required external resource is unavailable outside the module's immediate control.

### dependency_contract_missing

A required interface/schema/contract from a dependency is absent or insufficiently defined.

### dependency_module_blocked

A required upstream/dependent module cannot currently supply the needed capability or fact.

### provider_api_unavailable

A required external provider API/service is unavailable.

### environment_failure

The declared development/runtime/tooling environment cannot perform the required work safely.

### policy_conflict

Authoritative governance/policy requirements conflict, or the requested action would violate an
applicable policy.

### unsupported_capability

The current module/executor/toolchain does not possess a capability required for the requested work.

### security_boundary

The required action crosses a security/credential/privilege boundary not granted by the current
authority.

### manual_decision_required

Progress requires a semantic/exception decision explicitly reserved for Blueprint/operator authority.

## Blocker evidence record

A blocker record must carry enough information to understand the condition without chat archaeology:

- `blocker_id`
- `module_id`
- `prompt_id`
- `roadmap_step_id`
- optional `execution_id`
- `condition`
- `reason_code`
- `blocking`
- `affected_scope_refs`
- `summary`
- `evidence_refs`
- optional `related_question_id`
- `created_at`

`condition` is limited to:

- `clarification_required`
- `execution_blocked`

The record does not define the future Q5 event envelope.

## Blocking projection

A prompt can remain in its execution lifecycle while carrying active coordination conditions.

Rules:

1. a blocking condition stops only its declared affected scope;
2. whole-prompt blocking requires the affected scope to explicitly cover the whole prompt;
3. Independent prompt work may continue where the execution contract permits;
4. blocker creation never mutates released prompt requirements;
5. blocker creation never automatically issues RETURN or HOLD;
6. clearing a blocker requires explicit resolution evidence;
7. reason codes remain stable evidence even after the condition is resolved.

## Q2 bridge

A blocking clarification escalated by Q2 may project an `execution_blocked` condition with reason
`manual_decision_required` or another justified Q3 reason, but Q3 does not rewrite the Q2 question
thread.

Q1/Q2 question identity/history remains authoritative for the clarification.

## Separation from Q4-Q8

Q3 does not define:

- immutable operator-decision/scope-adjustment artifacts (Q4);
- the common coordination event envelope (Q5);
- operator-attention severity/transport semantics (Q6);
- cross-module routing mechanics (Q7);
- Logistics reference validation (Q8).

## Runtime boundary

Q3 does not enable:

- live SQLite coordination runtime;
- database creation;
- daemon/systemd;
- Telegram transport;
- autonomous execution;
- automatic module/business ACCEPT;
- automatic RETURN/HOLD;
- cross-repository writes;
- business prompt release.

## Acceptance gates

Q3 implementation is ready for deterministic same-phase closeout when:

1. the five concepts are explicitly non-equivalent;
2. coordination conditions and executor outcome evidence are modeled separately;
3. the exact thirteen blocker reason codes are canonical;
4. `execution_blocked` always has `blocking=true`;
5. affected scope and evidence are mandatory for blockers;
6. `unable_to_execute` cannot itself issue RETURN/HOLD;
7. blocking applies only to declared affected scope;
8. independent work may continue where allowed;
9. released prompts remain immutable;
10. Q4-Q8 remain deferred;
11. runtime/autonomy boundaries remain disabled;
12. the Q3 validator is in canonical `make check`;
13. focused Q2+Q3 tests and canonical Blueprint checks pass.

This implementation does not itself close Q3 or activate Q4. Closeout requires published evidence and
the separate deterministic same-phase gate.
