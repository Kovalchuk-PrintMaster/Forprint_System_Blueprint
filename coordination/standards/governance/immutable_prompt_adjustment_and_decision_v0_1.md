# ForPrint Immutable Prompt Adjustment and Operator Decision Correlation v0.1

## Status

Active governance standard for the Q4 hardening slice.

Adoption mode: `prompt_or_directive_required`.

Machine-readable authority:

`coordination/standards/governance/immutable_prompt_adjustment_and_decision_v0_1.yaml`

## Purpose

Q4 defines how execution-time decisions, clarifications, waivers and scope changes are recorded
without rewriting a released prompt.

The core rule is:

**A released prompt is an immutable execution contract.**

After release, prompt requirements are never edited, deleted or silently rewritten.

## Immutable prompt rule

A later fact may change what should happen next, but it does not change historical prompt bytes.

Any material post-release change is represented by a separate correlated artifact.

The original prompt remains reconstructible and reviewable exactly as released.

## Canonical correlated artifact types

Q4 owns the following artifact vocabulary:

- `operator_decision`
- `scope_adjustment`
- `waiver`
- `skip_optional`
- `clarification_resolution`
- `blocker_resolution`
- `cancellation`
- `follow_up_prompt`
- `superseding_prompt`

These are not Q5 events. Q5 will later define the common event envelope.

## No disappearing requirements

A requirement, substep or acceptance criterion that is not executed never disappears silently.

It must remain traceable to an explicit disposition artifact and evidence.

Examples:

- optional work deliberately skipped -> `skip_optional`;
- required work waived by explicit authority -> `waiver`;
- execution scope changed -> `scope_adjustment`;
- prompt cancelled -> `cancellation`;
- work moved into a new prompt -> `follow_up_prompt`;
- old prompt replaced by a new execution contract -> `superseding_prompt`.

## Minimum correlated decision evidence

Every Q4 decision/adjustment artifact carries:

- `decision_id`
- `artifact_type`
- `prompt_id`
- `module_id`
- `roadmap_step_id`
- optional `execution_id`
- `correlation_id`
- zero or more related question/blocker/event references
- at least one `target_ref`
- `actor`
- `reason_code`
- `explanation`
- `execution_effect`
- `acceptance_effect`
- `evidence_refs`
- `decided_at`

`target_ref` identifies the affected requirement, substep, criterion, execution scope or whole prompt.

A whole-prompt effect must explicitly use whole-prompt scope; it is never inferred.

## Append-only correction model

Q4 artifacts are immutable once published.

A correction does not rewrite an earlier decision artifact.

It creates a new artifact that references the earlier decision through `supersedes_decision_id`.

The audit chain remains reconstructible.

## Artifact semantics

### operator_decision

Records an explicit operator/Blueprint governance decision that does not fit a narrower Q4 artifact
type.

It never silently edits the prompt.

### scope_adjustment

Changes execution scope after prompt release.

It must identify exactly which target refs are added, removed, narrowed, replaced or moved.

Scope adjustment requires explicit manual authority.

### waiver

Explicitly waives execution or acceptance of a required target.

Waiver requires manual authority, reason and evidence.

A waiver is never inferred from omission, timeout, inability to execute or blocker state.

### skip_optional

Explicitly records intentional non-execution of work that was already optional under the released
contract.

It cannot be used to make a required item optional.

### clarification_resolution

Records the authoritative resolution of a Q1/Q2 clarification.

It may explain how an existing requirement should be interpreted.

If the resolution materially changes scope or acceptance, a correlated `scope_adjustment`, `waiver`
or `superseding_prompt` is also required.

Clarification history remains owned by Q1/Q2 and is not rewritten.

### blocker_resolution

Records evidence that a Q3 blocker condition is resolved.

It may resume affected execution scope.

It does not rewrite the blocker history or prompt.

### cancellation

Records explicit cancellation of an affected scope or the whole prompt.

Cancellation requires explicit authority and does not delete the cancelled requirements from history.

### follow_up_prompt

Records that unfinished or newly required work will be governed through another prompt.

The follow-up prompt has its own release lifecycle and is not automatically released by Q4.

### superseding_prompt

Records replacement of a released prompt by a newer separately released prompt.

The superseded prompt remains immutable historical authority for its own prior execution period.

## Execution effects

Q4 uses a bounded execution-effect vocabulary:

- `no_execution_change`
- `clarify_only`
- `apply_scope_adjustment`
- `skip_optional`
- `resume_affected_scope`
- `cancel_affected_scope`
- `cancel_prompt`
- `require_follow_up_prompt`
- `supersede_prompt`

Execution effect describes what execution may do after the decision. It does not itself grant
credentials, production authority or cross-repository permission.

## Acceptance effects

Q4 uses a bounded acceptance-effect vocabulary:

- `no_acceptance_change`
- `acceptance_scope_adjusted`
- `waived_requirement`
- `optional_item_excluded`
- `completion_requires_follow_up`
- `prompt_cancelled`
- `prompt_superseded`

Acceptance effect is explicit evidence for later review. It is not automatic prompt ACCEPT.

## Manual authority boundary

Manual operator/Blueprint authority is required for:

- `operator_decision` when it changes project/execution truth;
- `scope_adjustment`;
- `waiver`;
- `skip_optional` when it changes governed execution choice;
- `cancellation`;
- `superseding_prompt`.

`clarification_resolution` and `blocker_resolution` may be evidence-driven when the underlying
contract already defines the resolution path, but they cannot be used to bypass a decision that
requires manual authority.

`follow_up_prompt` does not itself release another prompt.

## Correlation rules

Every Q4 artifact has one stable `correlation_id`.

Related question/blocker/event references are optional and typed separately.

A Q4 artifact may cite:

- `related_question_id`
- `related_blocker_id`
- `related_event_id`
- `supersedes_decision_id`

Q4 does not define Q5 `causation_id`, event transport or event persistence.

## Completion reporting

Every completion report must contain:

`Execution deviations / operator decisions`

The section must either:

- list all relevant Q4 decision/adjustment IDs and affected target refs; or
- explicitly state `none`.

Omission is invalid.

This allows review to reconstruct what was executed versus what the released prompt originally
required.

## Separation from Q5-Q8

Q4 does not define:

- the common coordination event envelope (Q5);
- operator-attention semantics or transport (Q6);
- cross-module routing mechanics (Q7);
- Logistics reference validation (Q8).

## Runtime boundary

Q4 does not enable:

- live SQLite coordination runtime;
- database creation;
- daemon/systemd;
- Telegram transport;
- autonomous execution;
- automatic module/business ACCEPT;
- automatic RETURN/HOLD;
- automatic follow-up prompt release;
- cross-repository writes;
- business prompt release.

## Acceptance gates

Q4 implementation is ready for deterministic same-phase closeout when:

1. released prompt immutability is explicit;
2. exact nine Q4 artifact types are canonical;
3. no requirement can disappear without explicit disposition evidence;
4. every artifact has prompt/module/roadmap/correlation/target/effect/evidence identity;
5. Q4 artifacts are append-only and corrected only by superseding artifacts;
6. scope adjustment, waiver and other project-truth changes preserve manual authority;
7. clarification/blocker resolution cannot silently change scope or acceptance;
8. execution and acceptance effects are explicit and bounded;
9. completion report deviations/operator-decisions section is mandatory or explicitly `none`;
10. automatic prompt ACCEPT/RETURN/HOLD/follow-up release remains disabled;
11. Q5-Q8 remain deferred;
12. runtime/autonomy boundaries remain disabled;
13. Q4 validator is in canonical `make check`;
14. focused Q3+Q4 tests and canonical Blueprint checks pass.

This implementation does not itself close Q4 or activate Q5. Closeout requires published evidence
and the separate deterministic same-phase gate.
