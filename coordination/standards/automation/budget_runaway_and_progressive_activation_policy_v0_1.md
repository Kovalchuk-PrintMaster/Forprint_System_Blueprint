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

<!-- assistant-intervention-ledger-2026-09-01:start -->
## Assistant Intervention Ledger direction

A deterministic-to-AI fallback is also an automation-learning signal.

Track enough evidence to classify trigger, deterministic failure, capability/roadmap step,
cost/tokens/time, result, resolution class, automation candidate and repeat signature/count.

Periodic review should identify repeated safe patterns that deserve deterministic implementation.
This does not authorize automatic rewriting of standards/business rules.
<!-- assistant-intervention-ledger-2026-09-01:end -->

<!-- FORPRINT_U92_MANAGED_AUTONOMY_CONTEXT_AND_RUNWAY_20260903:START -->
## Managed autonomy, context and AI budget runway

Autonomy is action-specific and reversible:

- `A0 HUMAN_DRIVEN`
- `A1 AI_ASSISTED`
- `A2 SUPERVISED_AUTONOMY`
- `A3 BOUNDED_AUTONOMY`
- `A4 AUTONOMOUS_ROUTINE`

Every action may be downgraded independently after risk, cost, quality or verification evidence.

Runtime evidence should include request counts, AI/tool calls, repeats, tokens, latency, cost,
retries and escalations. Repeated manual patterns may create automation candidates but never
silently create or deploy code.

Long assistant work must checkpoint durable state before context exhaustion and resume in a fresh
episode. Provisional checkpoint bands may be tuned by evidence; they are not business truth.

A budget-runway metric should estimate days remaining at observed burn rate and route low-runway
states to operator attention. Exhausted balance must produce explicit degraded/manual behavior,
never silent functional degradation.
<!-- FORPRINT_U92_MANAGED_AUTONOMY_CONTEXT_AND_RUNWAY_20260903:END -->
