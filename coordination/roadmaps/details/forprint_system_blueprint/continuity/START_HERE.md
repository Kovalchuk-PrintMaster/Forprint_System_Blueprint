# ForPrint Blueprint — START HERE

Status: zero-context continuity entry point.

This file is a navigation/handoff document, not runtime authority.
Always revalidate Git and `coordination/releases/current.yaml` before mutation.

## Current active workstream bootstrap

For zero-context continuation of the active v0.4.1 release work, read first:

- `coordination/instruction_intake/bootstrap/2026-08-23__forprint_system_blueprint__v0_4_1_current_release_zero_context_execution_handoff_v0_1.md`

It records the current B1-P2 state, open F01-F04 correction, the full
remaining v0.4.1 hardening path, and the bounded Logistics + Codex pilot
finish line. It is navigation/handoff evidence, not runtime authority.
Always revalidate Git and `coordination/releases/current.yaml` first.

## Project mission

ForPrint is building a coordinated automation platform for a mini-printing business:
internet shop, mobile app, automatic quotation/order calculation, automatic order
processing, quality control, intake, fulfillment and order issue.

The Blueprint assistant is the coordination/governance controller. It does not own
module implementation. Its job is to keep the roadmap coherent, balance module
assistants against dependencies, preserve WIP discipline, review completion evidence,
maintain release/prompt lifecycle rules and keep a clear forward horizon.

## Canonical authority order

When context is missing, read in this order:

1. `coordination/releases/current.yaml`
2. this file
3. `coordination/roadmaps/details/forprint_system_blueprint/README.md`
4. `coordination/roadmaps/details/forprint_system_blueprint/v0_4_1_remaining_coordination_hardening_plan_v0_1.md`
5. `coordination/roadmaps/details/forprint_system_blueprint/autonomous_multi_module_coordination_program_v0_1.md`
6. newest applicable records under `coordination/internal_work/blueprint/governance/`
7. `prompt_sequence_v0_1.yaml`
8. newest snapshot under `continuity/snapshots/`

Git/current release authority wins over stale snapshots or old chat context.

## Mandatory startup check

Before proposing a mutation:

- identify branch, HEAD and upstream;
- verify divergence and worktree/index state;
- compare live remote when publication state matters;
- read current release `current_slice`;
- identify the last accepted/published package;
- identify the next legally eligible package;
- inspect dependencies and explicit operator decisions;
- only then run wider validation.

Never continue from remembered chat state when Git/current release contradicts it.

## Hard operating invariants

- External module repositories are read-only from Blueprint coordination work.
- Blueprint-owned mutations happen only through explicit reviewed user-run transactions.
- Never invent module/business prompt ACCEPT/RETURN/HOLD. Blueprint internal same-phase package closure may use the deterministic phase-boundary progression policy.
- Never auto-push.
- Released prompts are immutable execution contracts.
- Selection, execution, closure, publication and activation remain auditable transitions; same-phase Blueprint progression may compose them in one bounded user-run transaction after deterministic gates pass.
- Exactly one active prompt is preferred; WIP=1.
- Current effective release authority is `coordination/releases/current.yaml`.
- Legacy compatibility is advisory/nonblocking unless explicitly promoted.
- Do not enable SQLite runtime, daemon, systemd, autonomous execution or automatic
  acceptance through B1/B2/Q planning work.
- Do not release a business prompt as a side effect of coordination hardening.
- Preserve exact evidence: scope, hashes, parent, subject, tests and remote containment.

## Current durable state after B1 activation publication

Base release: `v0.4` — PROMOTED / CLOSED / SEALED.

Hardening release: `v0.4.1` — ACTIVE_CURRENT.

Current slice:

`blueprint_v0_4_1_execution_baseline_and_drift_control_v0_1`

B1 activation publication commit:

`1456b191ca4c29a31631d4c35af983be97e3f7fa`

H9 Logistics reference rollout:

`ACCEPTED / PUBLISHED / CLOSED`

H9 Blueprint acceptance commit:

`5bcf99cfb29f83a6ee999c239dd33e999988e9cf`

Logistics H9 implementation:

`4a3a8cf3d2809c3a7f49268fa62334ed24b5fa90`

Logistics H9 publication seal:

`96284d829bb5cdcd564f44c51bdbe681f9d26cae`

B2, Q1-Q8, H10 and H11 are not active.

## Current functional goal — B1

Core rule:

`freshness != compatibility`

B1 must establish release/execution/completion baselines, a material required-input
manifest, deterministic `execution-preflight`, Blueprint/module drift classifications,
execution identity/epoch, explicit revalidation/revocation/supersession semantics,
completion provenance, and Logistics reference fixtures for exact and
forward-compatible execution.

Do not require historical checkout merely because Blueprint advanced when required
inputs remain compatible.

## Forward program

`B1 implementation`
→ `B1 Logistics reference validation`
→ `B1 explicit ACCEPT / seal / publication`
→ `B2 activation`
→ `B2 implementation / ACCEPT`
→ `Q1`
→ `Q2`
→ `Q3`
→ `Q4`
→ `Q5`
→ `Q6`
→ `Q7`
→ `Q8`
→ `H10 ecosystem rollout`
→ `H11 legacy retirement/archive audit`
→ future `AUT` program.

Use `prompt_sequence_v0_1.yaml` for machine-readable dependencies, entry conditions,
required outputs, validation and exit markers.

## B2 boundary

B2 defines where coordination data belongs:

- Git/YAML/Markdown = declarative canonical governance truth.
- Future coordination operational DB = high-churn runtime state.
- Filesystem/artifact storage = bulky evidence and logs.
- Secrets = dedicated secret storage.
- ForPrint business DB = separate business-domain lifecycle.

B2 does not enable live SQLite runtime.

## Q-track boundary

Q1-Q8 define question lifecycle, five-round escalation, blocker taxonomy, immutable
prompt/operator decisions, common event envelope, operator attention semantics,
cross-module routing, and Logistics clarification reference validation.

They do not implement the future autonomous daemon/runtime.

## Resume rule

A replacement assistant first reconstructs current authority, then chooses the first
package in `prompt_sequence_v0_1.yaml` whose dependencies and entry conditions are
actually satisfied.

If snapshot and Git disagree, trust Git/current release.

## Cross-cutting planning to preserve across assistant replacement

Read after the active hardening plan and AUT program when portfolio/operator strategy is relevant:

`coordination/roadmaps/details/forprint_system_blueprint/portfolio_operator_governance_and_project_standardization_program_v0_1.md`

It is planning guidance, not runtime authority.

Zero-context assistants must preserve these high-level requirements:

- significant work is judged both for local correctness and whole-system outcome advancement;
- the operator portfolio view is visual and color-coded from its first usable version;
- raw module progress is distinct from dependency-constrained effective readiness;
- historical priority/progress/audit assessments are retained;
- major roadmap milestones gain a required outcome-alignment audit gate;
- recurring governance work moves into explicit time/event-triggered obligations rather than memory;
- budget/model/resource policy remains explicit and human-governed;
- modules converge on a familiar project skeleton and same-intent/same-command operator contract;
- reusable framework behavior emerges from proven repeated patterns rather than premature abstraction.

Planning marker: `PORTFOLIO_OPERATOR_GOVERNANCE_PROJECT_STANDARDIZATION_V0_1`.

<!-- b1-logistics-reference-validation-closeout-v0-1 -->
## B1 Logistics reference validation — durable checkpoint

Recorded: 2026-08-24.

B1 implementation is complete and the Logistics reference validation has passed.

Durable result:

`B1_LOGISTICS_REFERENCE_VALIDATION_PASS`

Evidence includes:

- B1 terminal-decision reconciliation repair published at
  `0e79694d9fcbf3ec1bed64dcd473c9654f984dd8`;
- Logistics end-to-end lifecycle validation: 9/9 scenarios passed;
- production completion discovery result:
  `READY_FOR_BLUEPRINT_REVIEW`;
- historical terminal decision reconciled: 1;
- new B1 completion review candidate: 1;
- invalid completion events: 0;
- full current validation for the new completion remained enabled;
- live Blueprint and Logistics repositories remained unchanged during the
  end-to-end fixture run;
- project `make check`: 30/30.

Current transition state:

- B1 implementation: completed;
- B1 Logistics reference validation: completed / PASS;
- B1 acceptance: **not yet performed**;
- B1 completion: **false**;
- next legally eligible package: `B1-ACCEPT`;
- B2 remains inactive and requires B1 ACCEPT first.

Do not infer B1 acceptance from this validation closeout.

<!-- b1-explicit-acceptance-v0-1 -->
## B1 explicit acceptance checkpoint — 2026-08-24

The operator explicitly issued:

`ACCEPT B1`

B1 implementation and Logistics reference validation had already completed and
the final acceptance-readiness review passed before this decision.

Acceptance result:

`B1_ACCEPTED`

This commit is the B1 local acceptance/seal transaction. The B1 exit marker
`B1_ACCEPTED_PUBLISHED_CLOSED` becomes durable remote authority only after this
exact reviewed commit is explicitly published.

Current boundaries:

- B1 acceptance decision: ACCEPT;
- B1 local seal: recorded by this transaction;
- B2: not activated by this transaction;
- SQLite runtime / daemon / autonomous execution: not authorized;
- automatic ACCEPT: false;
- business prompt release: false;
- module repository writes: false.

After explicit publication of this seal, the next legally eligible package is
`B2-ACTIVATE`.

<!-- b2-explicit-activation-v0-1 -->
## B2 explicit activation checkpoint — 2026-08-24

The operator explicitly issued:

`ACTIVATE B2`

B1 is accepted, published and closed at:

`ebe71b4fad724e565c0f5968e878964f259cdf00`

Current v0.4.1 slice is now:

`blueprint_v0_4_1_coordination_data_classification_and_persistence_boundary_v0_1`

B2 scope is limited to coordination data classification and persistence
boundaries. It defines what remains declarative Git/YAML/Markdown truth, what
may later become high-churn operational storage, how bulky evidence and secrets
are separated, and how future coordination storage remains separate from the
ForPrint business database.

This activation does **not** enable live SQLite runtime, a daemon, systemd,
autonomous execution, automatic ACCEPT or a business prompt release.

Current functional work:

`B2-IMPLEMENT-ACCEPT`

The next completion gate is `B2_ACCEPTED_PUBLISHED_CLOSED`.

## B2 explicit acceptance checkpoint

Operator decision: `ACCEPT B2`.

B2 implementation commit:

`b0bf657677e1cde9e624fe81c85adf0dcba44d79`

Acceptance transaction state:

- B2 implementation: committed and published;
- B2 semantic review: PASS;
- B2 operator decision: ACCEPT;
- B2 local acceptance seal: recorded by this transaction;
- publication of this acceptance seal: separate explicit transaction;
- Q1 remains inactive until B2 acceptance seal is published;
- live SQLite runtime: disabled;
- daemon/systemd: disabled;
- autonomous execution: disabled;
- automatic ACCEPT: disabled.

Next after publication: `Q1 — Clarification question lifecycle`.

## Q1 explicit activation checkpoint

Operator direction: proceed to the Q-track.

Current v0.4.1 slice:

`blueprint_v0_4_1_clarification_question_lifecycle_v0_1`

Activation basis:

- B2 exit marker `B2_ACCEPTED_PUBLISHED_CLOSED` is satisfied and published at
  `c0b74c261b11f4c0e59d49fdd7bfc12d5be54788`;
- Q1 dependency on `B2-IMPLEMENT-ACCEPT` is satisfied;
- Q1 is the first legally eligible planned package;
- Q2-Q8 remain planned and inactive;
- WIP target remains one current functional package.

Q1 scope:

- first-class clarification question threads;
- lifecycle `OPEN -> ROUTED -> ANSWERED -> CONFIRMED -> RESOLVED`;
- alternative terminals `ESCALATED`, `CANCELLED`, `EXPIRED`;
- prompt may remain `in_progress` with `waiting_on_clarification`;
- minimum question identity and evidence correlation;
- a question alone never implies RETURN or HOLD.

This activation does not implement Q2 five-round escalation, Q3-Q8 semantics,
live SQLite runtime, daemon/systemd, autonomous execution, automatic ACCEPT,
automatic next activation, Telegram transport or cross-repository writes.

Current functional package: `Q1`.

Next completion gate: `Q1_ACCEPTED_PUBLISHED_CLOSED`.

## Q1 explicit acceptance checkpoint

Operator decision: `ACCEPT Q1`.

Q1 implementation commit:

`f0536f384c5524043e3a7a4cf4f6a8587e2eae6d`

Acceptance readiness was revalidated in this transaction before any write:

- exact Q1 implementation parent/subject/scope: PASS;
- exact Q1 contract/validator/test hashes: PASS;
- implementation published to the live remote: PASS;
- Q1 semantic validator: PASS;
- focused Q1 tests: PASS;
- standards index validation: PASS;
- canonical `make check`: PASS;
- Q2 remains inactive;
- live SQLite runtime / daemon / systemd / autonomy remain disabled.

Acceptance transaction state:

- Q1 operator decision: ACCEPT;
- Q1 local acceptance seal: recorded by this transaction;
- publication of this acceptance seal: separate explicit transaction;
- Q2 remains inactive until Q1 acceptance seal is published and Q2 is separately activated.

Next after publication: `Q2 — Bounded five-round clarification and escalation`.

## Q2 explicit activation checkpoint

Operator decision: `ACTIVATE Q2`.

Q1 exit marker `Q1_ACCEPTED_PUBLISHED_CLOSED` is satisfied and published at:

`516ee17fc5b678112dc28732166a3bd16691d8a0`

Current v0.4.1 slice:

`blueprint_v0_4_1_bounded_clarification_and_escalation_v0_1`

Current functional package: `Q2`.

Q2 scope is semantic hardening for bounded clarification:

- default `maximum_unresolved_round_trips_per_question_thread: 5`;
- the limit is per unresolved question thread, not per whole prompt;
- after round five, further autonomous dialogue for that thread stops;
- the thread becomes `ESCALATED`;
- a blocking prompt becomes visibly waiting/blocked, without silently becoming
  RETURN or HOLD;
- escalation evidence must preserve the original question, all rounds,
  evidence, unresolved fact, impact, safe options and recommended next action.

This activation defines the Q2 contract only. It does not enable a live
autonomous dialogue worker, SQLite runtime, daemon/systemd, Telegram transport,
automatic ACCEPT, automatic next activation, business prompt release, or
cross-repository writes.

Q3-Q8 remain planned and inactive.

Next completion gate: `Q2_ACCEPTED_PUBLISHED_CLOSED`.

<!-- phase-boundary-progression-gate-policy-v0-1 -->
## Phase-boundary progression gate policy — 2026-08-24

The operator changed the progress-confirmation rule.

Manual progress confirmation is now required at **major phase boundaries**, not
between every small Blueprint-owned package inside the same approved phase.

For the current Q phase, Q1-Q8 are one phase. After a Q package satisfies its
declared deterministic acceptance/semantic gates, publication and activation of
the next eligible Q package do not require a new `ACCEPT Qn` or
`ACTIVATE Qn+1` confirmation.

This does not authorize automatic ACCEPT/RETURN/HOLD of module or business
prompts. It does not waive WIP=1, dependency checks, semantic review,
publication verification, or exception authority. RETURN/HOLD, waiver, scope
change, dependency override, security/credential, destructive/production and
other exceptional authority decisions remain manual.

Current non-autonomous execution remains explicit and user-run; no background
push is authorized.

The next required manual **progress** gate after the Q phase is the Q -> H10
phase transition.

<!-- portfolio-automation-foundation-start-here-v0-1:start -->
## Portfolio/automation foundation — read after current Q authority

Cross-cutting foundation installed from the 2026-08-25 reviewed package.

Authoritative navigation for this concern:

1. `coordination/internal_work/blueprint/governance/2026-08-25__blueprint__portfolio_operating_model_transition_decision_v0_1.md`
2. `coordination/standards/governance/module_concept_and_roadmap_traceability_standard_v0_1.md`
3. `coordination/standards/governance/end_to_end_completeness_and_gray_zone_review_standard_v0_1.md`
4. `coordination/standards/governance/portfolio_roadmap_dependency_and_prioritization_standard_v0_1.md`
5. `coordination/standards/automation/`
6. `coordination/standards/frontend/`
7. `coordination/roadmaps/details/forprint_system_blueprint/portfolio_roadmap_rebuild_program_v0_1.md`
8. `coordination/roadmaps/details/forprint_system_blueprint/non_blueprint_roadmap_authority_rebuild_register_v0_1.yaml`

These files do not supersede the active Q2 slice.
They govern the portfolio operating model that is being prepared around/after the current hardening track.

Existing non-Blueprint roadmaps must not be treated as sufficient post-Q automated execution-selection authority
until their rebuild state is resolved.
<!-- portfolio-automation-foundation-start-here-v0-1:end -->

<!-- q2-deterministic-closeout-q3-current-v0-1:start -->
## Q2 deterministic closeout / Q3 current — 2026-08-25

Current release authority selects:

`blueprint_v0_4_1_execution_blocker_taxonomy_v0_1`

Q2 implementation:

`ba5c83eab07a44cd65b72680d099f3a18d26f9b6`

Q2 exit marker:

`Q2_ACCEPTED_PUBLISHED_CLOSED`

Acceptance basis:

`deterministic_phase_gate`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q2_deterministic_closeout_q3_activation_v0_1.yaml`

A new Q2 ACCEPT / Q3 ACTIVATE progress token was not required because Q2 and Q3 are both
inside phase `Q`. This does not change module/business ACCEPT/RETURN/HOLD authority.

Resume from:

`Q3_IMPLEMENTATION_SCOPE_AND_ACCEPTANCE_CRITERIA_REVIEW`
<!-- q2-deterministic-closeout-q3-current-v0-1:end -->

<!-- q3-deterministic-closeout-q4-current-v0-1:start -->
## Q3 deterministic closeout / Q4 current — 2026-08-25

Current release authority selects:

`blueprint_v0_4_1_immutable_prompt_adjustment_and_decision_v0_1`

Q3 implementation:

`7993f873f2f8aba31b9ee2c52fd6f2d3799391be`

Q3 exit marker:

`Q3_ACCEPTED_PUBLISHED_CLOSED`

Acceptance basis:

`deterministic_phase_gate`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q3_deterministic_closeout_q4_activation_v0_1.yaml`

A new Q3 ACCEPT / Q4 ACTIVATE progress token was not required because Q3 and Q4 are both
inside phase `Q`. Module/business ACCEPT/RETURN/HOLD authority is unchanged.

Resume from:

`Q4_IMPLEMENTATION_SCOPE_AND_ACCEPTANCE_CRITERIA_REVIEW`
<!-- q3-deterministic-closeout-q4-current-v0-1:end -->

<!-- q4-deterministic-closeout-q5-current-v0-1:start -->
## Q4 deterministic closeout / Q5 current — 2026-08-25

Current release authority selects:

`blueprint_v0_4_1_common_coordination_event_envelope_v0_1`

Q4 implementation:

`711d22224e84fe280ab6ce8f0516a853436f207d`

Q4 exit marker:

`Q4_ACCEPTED_PUBLISHED_CLOSED`

Acceptance basis:

`deterministic_phase_gate`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q4_deterministic_closeout_q5_activation_v0_1.yaml`

A new Q4 ACCEPT / Q5 ACTIVATE progress token was not required because Q4 and Q5 are both
inside phase `Q`. Module/business ACCEPT/RETURN/HOLD authority is unchanged.

Q5 activation does not enable a live coordination event store, SQLite runtime, daemon or worker.

Resume from:

`Q5_IMPLEMENTATION_SCOPE_AND_ACCEPTANCE_CRITERIA_REVIEW`
<!-- q4-deterministic-closeout-q5-current-v0-1:end -->

<!-- q5-deterministic-closeout-q6-current-v0-1:start -->
## Q5 deterministic closeout / Q6 current — 2026-08-25

Current release authority selects:

`blueprint_v0_4_1_operator_attention_semantics_v0_1`

Q5 implementation:

`2309437b6a5e14b54f0a6de1c08e33f2bc5c553c`

Q5 exit marker:

`Q5_ACCEPTED_PUBLISHED_CLOSED`

Acceptance basis:

`deterministic_phase_gate`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q5_deterministic_closeout_q6_activation_v0_1.yaml`

A new Q5 ACCEPT / Q6 ACTIVATE progress token was not required because Q5 and Q6 are both
inside phase `Q`. Module/business ACCEPT/RETURN/HOLD authority is unchanged.

Q6 activation defines the next semantic hardening scope only; it does not enable Telegram,
live SQLite, daemon/systemd or autonomous workers.

Resume from:

`Q6_IMPLEMENTATION_SCOPE_AND_ACCEPTANCE_CRITERIA_REVIEW`
<!-- q5-deterministic-closeout-q6-current-v0-1:end -->

<!-- q6-deterministic-closeout-q7-current-v0-1:start -->
## Q6 deterministic closeout / Q7 current — 2026-08-25

Current release authority selects:

`blueprint_v0_4_1_cross_module_question_routing_contract_v0_1`

Q6 implementation:

`7845ab850b334460a9120d827d2397f799339fc0`

Q6 exit marker:

`Q6_ACCEPTED_PUBLISHED_CLOSED`

Acceptance basis:

`deterministic_phase_gate`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q6_deterministic_closeout_q7_activation_v0_1.yaml`

A new Q6 ACCEPT / Q7 ACTIVATE progress token was not required because Q6 and Q7 are both
inside phase `Q`. Module/business ACCEPT/RETURN/HOLD authority is unchanged.

Q7 activation defines the next semantic hardening scope only. It does not enable persistent
question routing, cross-repository writes, Telegram, live SQLite, daemon/systemd or autonomous
workers.

Resume from:

`Q7_IMPLEMENTATION_SCOPE_AND_ACCEPTANCE_CRITERIA_REVIEW`
<!-- q6-deterministic-closeout-q7-current-v0-1:end -->

<!-- q7-deterministic-closeout-q8-current-v0-1:start -->
## Q7 deterministic closeout / Q8 current — 2026-08-25

Current release authority selects:

`blueprint_v0_4_1_logistics_clarification_reference_validation_v0_1`

Q7 implementation:

`501d53352cdf5f4ea755de335aefc6b077c6ff02`

Q7 exit marker:

`Q7_ACCEPTED_PUBLISHED_CLOSED`

Acceptance basis:

`deterministic_phase_gate`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q7_deterministic_closeout_q8_activation_v0_1.yaml`

A new Q7 ACCEPT / Q8 ACTIVATE progress token was not required because Q7 and Q8 are both
inside phase `Q`. Module/business ACCEPT/RETURN/HOLD authority is unchanged.

Q8 is the final Q-phase package. After Q8 acceptance/publication/closure, transition to H10 requires
explicit manual Q -> H10 phase-boundary progress confirmation; silence is not approval.

Q8 activation does not enable persistent routing, cross-repository writes, Telegram, live SQLite,
daemon/systemd or autonomous workers.

Resume from:

`Q8_IMPLEMENTATION_SCOPE_AND_ACCEPTANCE_CRITERIA_REVIEW`
<!-- q7-deterministic-closeout-q8-current-v0-1:end -->

<!-- q8-closeout-h10-current-v0-1:start -->
## Q8 closeout / H10 current — 2026-08-25

Explicit operator phase-boundary approval:

`Підтверджую перехід Q → H10.`

Current release authority now selects:

`blueprint_v0_4_1_ecosystem_rollout_balance_and_dependency_adoption_v0_1`

Q8 implementation:

`a028f94ce20b273b459e6b7ecb853540d93f3657`

Q8 exit marker:

`Q8_ACCEPTED_PUBLISHED_CLOSED`

Q8 acceptance basis:

`deterministic_phase_gate`

Boundary activation basis:

`explicit_operator_q_to_h10_phase_boundary_approval`

Durable transition record:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__q8_closeout_h10_manual_phase_boundary_activation_v0_1.yaml`

H10 stable ID was minted from the existing canonical planned H10 title and does not expand H10
scope.

H10 activation does not itself mutate module repositories or enable SQLite runtime, daemon/systemd,
Telegram, autonomous execution, automatic module/business ACCEPT/RETURN/HOLD or business prompt
release.

The next required manual progress boundary is `H10 -> H11`.

Resume from:

`H10_ENTRY_AND_ECOSYSTEM_ROLLOUT_SCOPE_REVIEW`
<!-- q8-closeout-h10-current-v0-1:end -->

<!-- logistics-only-automation-validation-rule-v0-1:start -->
## Logistics-only automation validation rule — 2026-08-25

H10 is current, but new automation execution is **Logistics-only** until stability is proven.

Sole pilot:

`logistics_service`

Minimum evidence before expansion review:

`2` successful real automatic prompt runs.

Non-Logistics modules remain disconnected from the new functionality until:

1. Logistics passes the stability gate;
2. operator performs positive review;
3. a separate reviewed expansion decision is recorded.

Library/Telegram candidate or planning status does not grant connection/dispatch authority.
Website remains paused/excluded.

Authority decision:

`coordination/internal_work/blueprint/governance/2026-08-25__blueprint__logistics_only_automation_pilot_scope_decision_v0_1.yaml`
<!-- logistics-only-automation-validation-rule-v0-1:end -->
