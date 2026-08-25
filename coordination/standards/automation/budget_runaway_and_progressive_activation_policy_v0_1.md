# Budget, Runaway Protection and Progressive Activation Policy v0.1

## Principle

Automation must be economically bounded and fail closed.

A cyclic task must not be able to consume an uncontrolled daily budget.

## Required package breakers

Before broad automation, each package must be able to carry explicit limits for:

- maximum spend/budget;
- maximum retry/rework loops;
- maximum clarification rounds;
- maximum wall-clock/runtime window;
- maximum scope/file surface where appropriate.

Numerical defaults remain TBD until real executor/provider behaviour is measured.

## Mandatory stop conditions

Stop rather than continue blindly on:

- budget ceiling reached;
- retry/rework ceiling reached;
- unresolved clarification thread reaches the project limit;
- scope expansion required;
- unexpected cross-repo dependency/write;
- credentials/security permission required;
- destructive/production action required;
- test regression outside understood package effects;
- authoritative data/contract missing;
- repository/branch authority drift.

## Progressive trust

New executor/module pairings start cautiously:

1. small bounded package;
2. low budget ceiling;
3. strong evidence requirements;
4. close semantic review.

When repeated packages demonstrate:

- scope discipline;
- high acceptance quality;
- low rework;
- good reports;
- predictable budget;
- stable checks;

the system may gradually increase:

- package size;
- budget ceiling;
- time window;
- amount of same-phase deterministic progression.

Trust is contextual. Success on one module/type does not automatically transfer to all modules.

## Trust reduction

If delivery quality falls, reduce rather than abruptly abandon:

- package size;
- budget;
- autonomy;
- retry allowance;

and increase review granularity until the cause is understood.

## Manual authority preserved

No budget/trust policy may automatically authorize:

- business/module ACCEPT;
- RETURN/HOLD;
- scope waiver;
- phase-boundary approval;
- credentials/security;
- destructive/production actions;
- cross-repository writes.
