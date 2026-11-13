# ForPrint Phase-Boundary Progression Gate Policy v0.1

## Status

Active Blueprint governance standard.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/phase_boundary_progression_gate_policy_v0_1.yaml`

## Purpose

This policy separates **phase-transition authority** from routine progression
between small Blueprint-owned hardening packages inside the same already
approved phase.

The operator approves entry into a new major phase. Once that phase is entered,
its declared internal packages may close and advance deterministically without
a new progress-confirmation token for every small package, provided every
declared gate remains satisfied.

This removes redundant Q1 -> Q2 -> Q3-style confirmations while preserving
fail-closed governance.

## Scope

This policy applies only to Blueprint-owned internal phase/package progression.

Current phase model:

- `B` — B-track hardening packages;
- `Q` — Q1 through Q8;
- `H10` — ecosystem rollout phase;
- `H11` — legacy retirement/archive phase;
- `AUT` — autonomous-coordination program transition.

The phase model is governance configuration and may be revised explicitly later.

## Manual gate rule

A new explicit operator progress approval is required when crossing a configured
phase boundary.

Current boundaries:

- `B -> Q`
- `Q -> H10`
- `H10 -> H11`
- `H11 -> AUT`

Within the same phase, a new operator `ACCEPT <package>` or
`ACTIVATE <next-package>` confirmation is **not** required merely to continue
progress.

## Deterministic intra-phase closure

A same-phase package may be deterministically closed and the next eligible
same-phase package may be activated only when all required gates pass:

1. exact Git/release authority and dependency state are revalidated;
2. the implementation scope and immutable evidence match the reviewed subject;
3. package-specific semantic/acceptance oracles pass;
4. focused tests and canonical project checks pass;
5. publication/remote containment requirements are satisfied;
6. WIP=1 is preserved;
7. no unresolved blocking governance exception exists;
8. no manual authority decision is pending;
9. the next package is in the same configured phase and is dependency-eligible.

A failed gate stops progression. Silence never substitutes for a required phase
boundary approval.

## Transaction shape

Selection, implementation, closure, publication and next activation remain
auditable states.

For same-phase progression they may be composed into one bounded, deterministic
Blueprint transaction after all gates pass. This composition does not erase
evidence or dependency checks.

Under the current non-autonomous operating mode:

- transactions remain explicit and user-run;
- Git commit/push is not silently performed by background tooling;
- the user does not need to provide a new semantic progress-confirmation token
  for every same-phase package.

## Important distinction: package closure is not module prompt ACCEPT

This policy does **not** authorize automatic ACCEPT/RETURN/HOLD for module or
business prompts.

The existing module completion/review decision contracts remain authoritative
for module/business prompt disposition.

A Blueprint internal hardening package may satisfy an exit marker whose legacy
name contains `ACCEPTED`, but under this policy its acceptance basis may be
`deterministic_phase_gate` rather than a new operator ACCEPT decision.

## Manual exception decisions remain manual

The following remain explicit authority decisions even inside a phase:

- RETURN or HOLD;
- scope change or requirement waiver;
- dependency override;
- security/credential boundary decision;
- destructive or production-impacting action;
- business/module prompt release where release policy requires authorization;
- cross-repository write authorization;
- any semantic case where evidence cannot establish safe/fidelity-complete
  completion.

These are not routine progress confirmations.

## Historical evidence

Historical B/Q records that contain explicit `ACCEPT` or `ACTIVATE` decisions
remain immutable evidence. They are not rewritten merely because the policy has
changed.

The unpublished Q2 activation commit remains valid because the operator did in
fact issue `ACTIVATE Q2`. This policy changes the rule for subsequent
same-phase progression, beginning with Q2 -> Q3.

## Q-track effect

Q2 through Q8 are one phase: `Q`.

Therefore:

- Q2 -> Q3 does not require a new manual progress confirmation;
- Q3 -> Q4 does not require a new manual progress confirmation;
- the same applies through Q7 -> Q8;
- Q8 closure -> H10 **does** require a new phase-boundary operator approval.

## Safety boundaries

This policy does not itself enable:

- persistent daemon/runtime;
- live SQLite coordination runtime;
- systemd;
- Telegram transport;
- autonomous worker execution;
- automatic module/business prompt ACCEPT;
- automatic RETURN/HOLD;
- automatic cross-repository writes;
- automatic production mutation.

Those remain separately governed.
