# ForPrint Closed-Loop Coordination Lifecycle v0.1

Status: accepted by explicit operator decision; canonical lifecycle standard for the v0.4 coordination workstream.

Owner: `forprint_system_blueprint`.

## 1. Purpose and scope

This standard defines the control-plane lifecycle:

`ROADMAP → PROMPT QUEUE → ACTIVE PROMPT → MODULE EXECUTION → COMPLETION OUTBOX → DISCOVERY → READ-ONLY INTAKE/REVIEW → EXPLICIT OPERATOR DECISION → ROADMAP/QUEUE TRANSACTION → NEXT PROMPT SELECTION/ACTIVATION → HEALTH RECALCULATION → repeat`.

This slice defines lifecycle semantics only. Source registry tooling, coordination-pulse tooling, Prompt Contract v0.4, Completion Packet v0.4, Completion Outbox implementation, discovery tooling, review tooling, next-prompt tooling, and v0.4 promotion remain separate roadmap slices.

## 2. Ownership boundaries

Blueprint owns mutation of Blueprint roadmaps, Blueprint prompt queues, Blueprint review/decision evidence, accepted roadmap effects, dependency recalculation, next-prompt selection/activation, coordination health state, and Blueprint-owned governance tooling.

Each module owns its implementation, tests, check reports, completion packets/reports, completion-outbox records, corrections after RETURN, and module-local Git history/publication.

Blueprint may inspect registered module repositories read-only. Intake, review, decision, and advancement must not mutate module repositories.

## 3. Roadmap state model

Canonical roadmap states are:

- `planned`
- `ready`
- `active`
- `blocked`
- `completed`
- `superseded`
- `deferred`

Roadmap advancement is dependency- and state-based. Implementations must not model progress as `current_step++`.

Out-of-order completion is allowed when dependency and evidence rules permit it. Sequence is ordering metadata, not proof of eligibility.

## 4. Prompt logical state model

The v0.4 logical prompt states are:

- `draft`
- `prepared`
- `released`
- `in_progress`
- `completed_in_module`
- `pending_review`
- `accepted`
- `returned`
- `held`

Logical state is distinct from the physical prompt folder. During migration, tooling may derive logical state from current indexed fields, but must not create parallel competing sources of truth.

## 5. Prompt physical lifecycle

The canonical physical lifecycle is:

`draft/ → approved/ → completed/`.

Rules:

1. `draft/` is non-executable.
2. Execution requires explicit Blueprint release/activation into `approved/` plus indexed active state.
3. Module completion or `READY_FOR_OPERATOR_REVIEW` does not move a prompt to `completed/`.
4. RETURN does not move a prompt to `completed/`.
5. HOLD does not move a prompt to `completed/`.
6. Only explicit operator ACCEPT, or an explicitly documented historical equivalent, authorizes `approved/ → completed/`.
7. After ACCEPT, queue path and physical path must agree.
8. Exactly one active prompt is desired; more than one is an error.

`completed/` means accepted, not merely executed.

## 6. Roadmap-to-prompt binding

Every executable v0.4 prompt must reference one or more roadmap steps.

A prompt may declare intended effects such as `complete`, `unblock`, or `advance`. Completion evidence may claim roadmap results. Claims are proposals only.

Blueprint applies roadmap effects only after explicit ACCEPT and only when evidence supports them.

Unknown roadmap references, missing prompt files, duplicate prompt identities, and unknown dependency references are lifecycle errors.

## 7. Completion outbox and discovery boundary

Modules publish immutable completion-outbox records in module-owned repositories. Blueprint discovers them read-only through the coordination source registry.

Canonical discovery states are:

- `unseen`
- `discovered`
- `publication_unverified`
- `ready_for_intake`
- `intake_failed`
- `ready_for_operator_review`
- `accepted`
- `returned`
- `held`
- `superseded`

Discovery and intake are idempotent for the same module, event identity, and published completion commit.

Module declaration is not authoritative publication proof. Remote Git containment is authoritative when publication is required.

## 8. Read-only intake and review

Blueprint intake and review must not modify module code, module completion records, module Git history, or publication state.

Machine review may end in `READY_FOR_OPERATOR_REVIEW`.

Machine review must never invent `ACCEPTED`.

Human semantic review remains required where automatic evidence cannot establish fidelity, completeness, or business correctness.

## 9. Explicit operator decision gate

Supported decisions are:

- `ACCEPT`
- `RETURN`
- `HOLD`

No decision may be inferred from silence, green tests, publication, elapsed time, or machine readiness.

Automatic ACCEPT is forbidden.

Automatic RETURN is forbidden.

Decision evidence must identify the subject, decision, evidence basis, decision owner, and decision time.

## 10. ACCEPT transaction

After explicit ACCEPT, Blueprint applies one bounded transaction in this order:

1. write immutable operator decision/review evidence;
2. mark the reviewed prompt logically accepted;
3. move the physical prompt `approved/ → completed/`;
4. update queue path and accepted state;
5. link completion and review evidence;
6. apply only verified roadmap effects;
7. recalculate dependency eligibility;
8. select the next eligible prompt;
9. optionally activate exactly one next prompt;
10. recalculate roadmap horizon and prompt-buffer health;
11. validate the final cross-ledger state.

No automatic Git commit or push is part of ACCEPT.

If validation fails, rollback must restore the exact pre-transaction state.

## 11. RETURN semantics

RETURN means corrections are required.

RETURN must record immutable return evidence, preserve the reviewed prompt outside `completed/`, preserve completion/review history, identify required corrections, avoid applying claimed roadmap completion effects, avoid automatic module mutation, and avoid automatic advancement when returned work is a blocker.

Corrected module work produces new or superseding module-owned evidence under the applicable completion protocol.

## 12. HOLD semantics

HOLD means no accept/reject conclusion is authorized yet.

HOLD must record immutable hold evidence, preserve the reviewed prompt outside `completed/`, preserve roadmap state unless separately authorized, preserve completion/review evidence, and prevent advancement that depends on the held result.

HOLD is not RETURN and does not imply a correction request.

## 13. Atomicity, preconditions, rollback, and Git boundaries

Every bounded lifecycle mutation verifies relevant preconditions before writing, including expected branch, expected HEAD, expected worktree/index state, useful source hashes or structural invariants, and exact intended mutation paths.

Validation should include focused tests, full tests, canonical repository checks, and `git diff --check`.

Temporary-index validation must use a separate `GIT_INDEX_FILE` when needed so the real index remains unchanged.

Rollback restores the exact pre-mutation state.

Lifecycle tooling must not automatically commit or push.

## 14. Historical and evidence immutability

Historical evidence is immutable.

Current state may supersede historical ordering without rewriting the historical snapshot.

When historical and current facts diverge, distinct identifiers or fields must preserve the historical referent.

Superseding packets, decisions, and publication-verification records are preferred over rewriting prior evidence.

## 15. Health recalculation

After accepted transitions, Blueprint recalculates at minimum future actionable roadmap steps, dispatchable drafts, active prompt count, queue/roadmap reference integrity, and pending completion reviews.

Health thresholds come from the canonical coordination health policy, not hard-coded constants.

Below-target may be advisory when policy says so. Below-minimum behavior follows policy.

## 16. Next-prompt selection

Default next-prompt ordering is:

1. explicit operator override;
2. dependency eligibility;
3. queue rank or sequence;
4. priority;
5. creation-time tie-break.

Selection and activation are separate. A candidate may be selected without activation.

Activation must preserve the single-active-prompt invariant.

## 17. Required lifecycle invariants

Canonical semantic error names include:

- `ACCEPTED_PROMPT_STILL_IN_APPROVED`
- `COMPLETED_PROMPT_FILE_MISSING`
- `COMPLETED_PROMPT_INDEX_PATH_MISMATCH`
- `MULTIPLE_ACTIVE_PROMPTS`
- `ROADMAP_PROMPT_REFERENCE_MISSING`
- `QUEUE_ROADMAP_DRIFT`
- `COMPLETION_PENDING_REVIEW`

Automatic ACCEPT or RETURN without explicit operator instruction is invalid.

## 18. Idempotency

Re-running discovery, intake, review preparation, or health evaluation over the same immutable inputs must not create duplicate semantic events.

Re-applying an already recorded operator decision must either be a verified no-op for the same decision identity or fail safely.

ACCEPT must not create duplicate completed prompts, duplicate roadmap completion, or duplicate decision evidence.

## 19. Revision and migration rule

Old and unknown revisions may be read for migration and forensic interpretation.

Normal runtime should use the promoted current revision.

Compatibility fallbacks must not preserve obsolete parallel behavior indefinitely.

Revision promotion is a separate explicit operator decision.

## 20. Out of scope for this slice

This standard does not itself implement the source registry, coordination-pulse, Prompt Contract v0.4, Completion Packet v0.4, Completion Outbox, discovery scanner, review/advance command, next-prompt selector, Tracking Events v0.4 reference, or v0.4 promotion.
