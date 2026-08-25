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
