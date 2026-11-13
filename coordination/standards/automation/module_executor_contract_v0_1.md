# Module Executor Contract v0.1

## Required prompt/execution context

Every serious module work package SHOULD identify:

- module_id;
- executor/provider/model identity where available;
- roadmap step refs;
- capability refs;
- dependency refs;
- exact intended outcome;
- authoritative documents;
- in-scope paths/actions;
- out-of-scope boundaries;
- allowed mutation surface;
- acceptance criteria;
- required checks;
- evidence/report requirements;
- budget/time/retry bounds;
- escalation rules;
- stop conditions.

## Executor obligations

The executor MUST:

- revalidate its local repo state before mutation;
- respect Blueprint-owned standards as read-only authority;
- stay within declared scope;
- preserve released/immutable evidence;
- run required deterministic checks;
- record uncertainty instead of inventing missing facts;
- surface dependency drift;
- stop on forbidden authority/security/destructive conditions;
- produce a compact evidence-rich report.

## Blueprint is read-only to module executors

A module executor may read Blueprint policy/roadmaps/contracts.

It MUST NOT edit the Blueprint repository as part of module implementation unless a separately
authorized Blueprint transaction explicitly scopes that mutation.

A module may propose:

- clarification;
- policy change request;
- roadmap correction;
- dependency correction;
- module-specific overlay.

## No local governance fork

A module may keep local implementation notes, but it must not redefine global standards under a new
name merely because a shared rule is inconvenient.

## Module-specific overlays

An overlay is allowed only when:

- the module has genuinely different structural needs;
- the difference is documented;
- it references the shared standard it modifies;
- precedence and scope are explicit;
- Blueprint approves it.

## Stop/escalate triggers

Examples:

- required fact unresolved after allowed clarification rounds;
- dependency contract absent/drifted;
- requested change exceeds package scope;
- credentials or security authority needed;
- destructive/production action required;
- tests reveal unrelated systemic regression;
- business semantics cannot be proven from authority;
- cross-repository write required;
- budget/retry/wall-clock breaker trips.

<!-- strategic-context-advisory-knowledge-v0-1:start -->
## Strategic context and bounded initiative

A serious executor context SHOULD provide Module Mission/Charter, Target State, Strategic Horizon,
relevant dependencies and the Active Work Package.

Target State and Strategic Horizon are context, not execution authority.

**See far, act near.**

The executor MUST NOT implement future roadmap scope preemptively. It should implement the active
scope while avoiding knowingly dead-end choices when strategic direction is already clear.

## Mandatory non-trivial preflight

Before implementing a meaningful capability, the executor MUST:
1. check the knowledge/capability surface for existing/reusable capability;
2. check central Blueprint standards relevant to the work;
3. inspect current relevant dependencies.

If authoritative information is unavailable/conflicting, surface the gap rather than inventing a
local standard.

## Advisory observations

The executor MUST surface material observations it genuinely discovers: future blocker, dependency
risk, duplication, roadmap mismatch, architectural risk, external-service risk, major
simplification or meaningful improvement opportunity.

It is not required to invent an observation just to populate a report.

Advisories are `ADVISORY_ONLY` until Blueprint decides. They cannot autonomously change roadmap,
priority, scope or another module.

A useful advisory records observation, evidence, impact, urgency, confidence and recommendation.

## Knowledge-maintenance findings

Project Inspector findings enter the local governed maintenance queue. The local executor owns
semantic interpretation/repair of module knowledge under Blueprint standards.

A finding does not automatically interrupt the active Work Package unless classified blocking.
<!-- strategic-context-advisory-knowledge-v0-1:end -->
