# ForPrint ACCEPT_AND_ADVANCE Protocol v0.1

Status: active standard / v0.4.1 hardening

## Purpose

`ACCEPT_AND_ADVANCE` is one explicit Blueprint-owned operator workflow that
composes the existing review transaction with optional next-work advancement.

It does not create an ACCEPT decision. The request must already contain an
explicit `ACCEPT` decision accepted by the existing review transaction contract.

## Canonical operation

```text
explicit ACCEPT request
→ review transaction / acceptance oracle
→ approved → completed
→ roadmap + Prompt Queue acceptance update
→ module next-work resolution
→ optional explicit next prompt release
→ roadmap activation
→ WIP=1 verification
→ compound evidence
```

RETURN and HOLD remain separate review-transaction decisions and are not
accepted by this compound operation.

## Request schema

```yaml
schema_version: blueprint_accept_and_advance_request_v0_1
operation_id: <stable operator operation id>
operated_at: <ISO timestamp>
explicit_operator_input: true

review_transaction:
  # complete blueprint_review_roadmap_queue_transaction_request_v0_4

advance:
  mode: suggest_only
```

Optional explicit release mode:

```yaml
advance:
  mode: release_explicit_prompt
  explicit_operator_input: true
  expected_roadmap_step_id: <stable roadmap step id>
  expected_prompt_id: <stable prompt id>
```

The apply command requires an operator confirmation exactly equal to
`operation_id`.

## Selection boundary

H5 does not hardcode H6 ranking logic; it delegates next-work eligibility
and default ordering to the canonical module resolver.

`release_explicit_prompt` is allowed only when the operator binds both the
expected roadmap step ID and expected prompt ID. Under H6, the expected roadmap
step ID is treated as an explicit validated override: it may outrank the
default priority choice, but it cannot bypass dependency eligibility. The
expected prompt ID remains an explicit identity binding.

H5 contains no date-based or sequence-based fallback selection.

## WIP=1

After ACCEPT, no unresolved Prompt Queue v0.2 record may remain before another
prompt is released.

Unresolved includes any non-superseded queue record whose Blueprint review is
not `accepted_by_blueprint`. This intentionally blocks next activation for
ready, in-progress, blocked, paused, returned, unable-to-execute, or
completed-but-not-yet-accepted work.

After successful activation there must be exactly one unresolved prompt and it
must be the explicitly released `ready_for_module_pull` prompt.

## Release authorization

H5 reuses `manage_outgoing_prompt.release_prompt()`.

It does not change or bypass:

```text
coordination/standards/governance/outgoing_prompt_release_policy_v0_1.yaml
```

If release is governance-gated, ACCEPT remains applied and ADVANCE returns a
clear blocked result. The same request can be retried later because the
underlying ACCEPT transaction is idempotent.

A blocked advance does not create compound completion evidence.

## Roadmap activation

Successful release updates the canonical module roadmap:

```text
coordination/roadmaps/<module_id>.yaml
```

The explicitly expected next step becomes `active`,
`metadata.current_step_id` moves to that step, and the prompt binding records
the released prompt ID, path, and Prompt Queue sequence.

Both flat legacy prompt bindings and the newer nested `prompt:` mapping remain
readable during migration.

## Failure and rollback

The existing ACCEPT transaction keeps its own exact rollback contract.

ADVANCE is a second bounded phase. Its roadmap, Prompt Queue, draft,
approved-prompt, and compound-evidence paths are snapshotted after ACCEPT.
Failure during release, roadmap activation, or compound-evidence persistence
restores that exact post-ACCEPT state.

Therefore a failed optional advance never invalidates or silently reverses a
valid explicit ACCEPT.

## Idempotency

Successful compound operations write:

```text
coordination/internal_work/blueprint/governance/
accept_and_advance/<operation_id>.yaml
```

The record binds the canonical request fingerprint. Reusing the same
`operation_id` with different content fails safely.

If ACCEPT succeeded but ADVANCE was blocked, no compound evidence is written;
the same request may safely continue later from the idempotent accepted state.

## Boundaries

The operation must not:

```text
create automatic ACCEPT / RETURN / HOLD;
change H6 ranking semantics;
bypass prompt release authorization;
write module repositories;
require network access;
perform commit, push, merge, or global promotion.
```

The self-coordination v0.4 selection/activation engine remains separate. H5
targets canonical external module roadmaps plus Prompt Queue v0.2.

<!-- phase-boundary-progression-gate-accept-advance-scope-v0-1 -->
## Scope refinement for phase progression

`ACCEPT_AND_ADVANCE` remains the explicit operator workflow for the prompt/review
transaction it governs.

It is not the canonical mechanism for routine progression between Blueprint
hardening packages inside one already approved phase. Same-phase package
progression is governed by `phase_boundary_progression_gate_policy_v0_1`.

This refinement does not weaken prompt release authorization or module prompt
ACCEPT/RETURN/HOLD rules.
