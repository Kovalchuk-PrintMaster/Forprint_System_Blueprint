# ForPrint Next Work Selection Policy v0.1

Status: active standard / v0.4.1 hardening

## Purpose

This policy defines the canonical ordering for choosing future Blueprint work.

It replaces sequence-first/date-first selection semantics. Sequence, queue rank,
and creation time remain useful planning, display, audit, and historical
metadata, but they do not outrank an eligible higher-priority candidate and
are not the default tie-break.

## Canonical selection order

For one selection scope:

1. if an explicit operator override is supplied, validate that candidate
   against all eligibility rules;
2. remove dependency-ineligible and non-dispatchable candidates;
3. rank remaining candidates by canonical priority;
4. break equal-priority ties by stable canonical ID.

Canonical priority order is:

```text
critical
high
normal
low
reference
```

The stable-ID tie-break is lexical and deterministic:

```text
self prompt selection  -> prompt_id
module roadmap work    -> step_id
```

`queue_rank`, `sequence`, and `created_at` MUST NOT appear in the canonical
selection key.

## Explicit override

An explicit override is stronger than default priority ordering, but it does
not bypass eligibility.

A self-coordination `override_prompt_id` must still be dispatchable,
roadmap-linked, dependency-eligible, and backed by the expected draft file.

A module `override_step_id` must still be a planned/ready roadmap step with
satisfied dependencies.

An ineligible override fails closed.

## Dependency eligibility

Dependency evaluation is type-aware and fail-closed.

For a local `module_step`, the canonical step in the current roadmap is
authoritative. A stale dependency snapshot cannot make an unfinished local
step eligible.

For a cross-module `module_step`, the current roadmap cannot prove the remote
step directly, so the explicit Blueprint dependency snapshot is used for this
selection pass. Its status must be `completed` or `accepted`.

Other supported dependency snapshots are satisfied by:

```text
prompt             completed | accepted | accepted_by_blueprint
document           acknowledged | completed | accepted
contract           completed | accepted
external_decision  completed | accepted | resolved
manual_review      completed | accepted | resolved
```

Unknown dependency types, missing local step references, and incomplete
snapshots fail closed.

Unknown, incomplete, held, returned, blocked, paused, deferred, cancelled, or
superseded work does not become eligible merely because it has a lower
sequence or older creation date.

## Self-coordination selection

The existing self-coordination selection/activation engine keeps WIP=1,
explicit validated override, dependency revalidation, selection fingerprint,
explicit activation confirmation, rollback, and idempotency.

Historical `deterministic_queue_order` activation evidence remains readable,
but new default selections use:

```text
dependency_eligibility_priority_stable_id
```

## Module next-work selection

The generic module next-work resolver selects across all `planned`/`ready`
dependency-eligible roadmap steps. It does not use `current_step + 1`.

Default module selection uses roadmap priority and then `step_id`.

An explicit `override_step_id` selects that step only after the same dependency
eligibility gate succeeds.

## ACCEPT_AND_ADVANCE integration

H5 does not duplicate H6 ranking logic.

`suggest_only` consumes the canonical default module selection.

`release_explicit_prompt` treats the operator-bound
`expected_roadmap_step_id` as an explicit validated H6 override. The matching
prompt ID remains an explicit identity binding and release still requires the
existing Prompt Queue release authorization.

Thus an operator may explicitly choose a lower-priority eligible step, but may
not override dependencies, WIP=1, prompt identity, or release policy.

## Activation boundary

Selection is not execution authorization.

Activation/release remains a separate Blueprint-owned operation and must
preserve WIP=1. H6 does not create automatic ACCEPT, RETURN, HOLD, release,
commit, push, or module-repository writes.

## Historical compatibility

Immutable v0.4 decisions and activation evidence are not rewritten.

Sequence-first behavior remains historical evidence only. Current selection
uses this policy.

<!-- phase-boundary-progression-gate-next-work-refinement-v0-1 -->
## Phase-boundary activation refinement

The phrase `explicit activation confirmation` in the historical
self-coordination selection description is refined for Blueprint internal phase
progression.

When the next eligible package belongs to the same already approved phase,
`phase_boundary_progression_gate_policy_v0_1` is sufficient progression
authorization after deterministic gates pass; no new operator progress token is
required.

Selection still does not itself bypass WIP=1, dependencies, prompt release
authorization, publication evidence, or exception authority. Phase-boundary
activation still requires explicit operator approval.
