# Automation Operating Model v0.1

## Objective

Allow modules to be developed by AI/code executors without turning the owner into a person who must
inspect and approve a five-minute micro-task continuously.

## Two control planes

### Blueprint/operator plane

Owns:

- module selection;
- portfolio priority;
- work-package construction;
- budget ceilings;
- dependency constraints;
- policy/roadmap authority;
- semantic review;
- exceptions;
- executor assignment;
- progression gates.

### Module executor plane

Consumes authoritative context and executes bounded work.

It does not own project-wide governance.

## Work granularity

Roadmap steps are meaningful outcomes.

Executor work packages are bounded execution slices and need not map 1:1 to roadmap steps.

Initial calibration packages may be small.
After trust is established, packages should normally be large enough to produce meaningful work
without requiring constant operator attention. A practical target may often be roughly 30–120+
minutes, but outcome/risk matters more than wall-clock duration.

## Standard execution loop

`SELECT → PACKAGE → EXECUTE → SELF-CHECK → REPORT → REVIEW/GATE → NEXT`

Intermediate deterministic housekeeping inside the same authorized package should not require
repeated operator progress tokens.

Semantic, security, destructive, scope-changing and phase-boundary exceptions remain manual.

## Common standards

Executors must consume shared Blueprint standards.

They MUST NOT silently create competing project-wide policy inside their own module.

If a standard does not fit a unique module:

1. executor raises clarification/change request;
2. Blueprint reviews;
3. Blueprint either adjusts shared policy or creates an explicit module-specific overlay/exception.

## Current clarification rule

For one unresolved question thread:

- maximum unresolved round trips: 5;
- after round 5 the thread stops autonomous dialogue;
- thread becomes ESCALATED;
- report includes question history, evidence, unresolved fact, impact, safe options and recommended
  next action.

## No autonomous authority expansion

Executor success in one package does not give it permission to:

- expand scope;
- modify Blueprint governance;
- change credentials/security;
- perform destructive production actions;
- write other module repositories;
- issue business/module ACCEPT decisions;
- enable background commit/push.
