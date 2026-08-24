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
- Never auto-ACCEPT.
- Never auto-push.
- Released prompts are immutable execution contracts.
- Selection, activation, execution, acceptance and publication are separate transitions.
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
