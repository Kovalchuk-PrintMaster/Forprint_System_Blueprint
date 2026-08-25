# ForPrint System Blueprint — Detailed Roadmap Plans

Status: planning navigation / non-executable.

This directory stores durable detailed plans for `forprint_system_blueprint`.

Current authority remains `coordination/releases/current.yaml`. The historical
`coordination/self_coordination/roadmap.yaml` remains non-authoritative unless a later
explicit reconciliation promotes a replacement.

Current hardening work is Q5 — `blueprint_v0_4_1_common_coordination_event_envelope_v0_1`. H9, B1, B2, Q1, Q2, Q3 and Q4 are accepted/published/closed; effective authority remains `coordination/releases/current.yaml`.

These files do not release prompts, activate work, authorize automatic execution,
authorize automatic ACCEPT, or mutate module repositories.

Plans:
- `v0_4_1_remaining_coordination_hardening_plan_v0_1.md`
- `autonomous_multi_module_coordination_program_v0_1.md`

Integration rule: promote a planned package only in a separate reviewed transaction
after checking dependencies, current release authority, acceptance criteria and pilot state.
Stable IDs are durable; display ordering such as H9/H10 may change.

## Planned foundation extensions recorded 2026-08-22

The v0.4.1 remaining-hardening plan now also reserves two foundation packages
to be integrated only after the current H9 Logistics rollout is reviewed:

- `B1 — blueprint_v0_4_1_execution_baseline_and_drift_control_v0_1`
  defines release/execution/completion baselines, required-input manifests,
  deterministic forward-drift compatibility, claim-time execution identity and
  explicit revalidation/revocation semantics.

- `B2 — blueprint_v0_4_1_coordination_data_classification_and_persistence_boundary_v0_1`
  defines the hybrid source-of-truth model: Git/YAML/Markdown for declarative
  canonical truth, a future SQLite WAL `CoordinationStore` for high-churn
  operational state, filesystem storage for bulky evidence, dedicated secret
  storage, and separation from the ForPrint business database.

B1 was separately activated on 2026-08-22 after H9 was accepted and published,
then accepted, published and closed on 2026-08-24.
B2 was separately activated on 2026-08-24 after B1 closure.
B2 activation does not enable live SQLite runtime, autonomous execution, automatic
ACCEPT, business prompt release or module-repository writes.

## Zero-context continuity entry point

For assistant replacement or context-window recovery, start with:

- `coordination/roadmaps/details/forprint_system_blueprint/continuity/START_HERE.md`
- `coordination/roadmaps/details/forprint_system_blueprint/continuity/prompt_sequence_v0_1.yaml`
- newest snapshot under `coordination/roadmaps/details/forprint_system_blueprint/continuity/snapshots/`

These continuity files are navigation/handoff artifacts, not runtime authority.
`coordination/releases/current.yaml` and current Git state remain authoritative.

## Cross-cutting portfolio/operator planning

Canonical planning specification:

- `coordination/roadmaps/details/forprint_system_blueprint/portfolio_operator_governance_and_project_standardization_program_v0_1.md`

It records outcome-alignment governance, visual portfolio/dependency/priority views, historical
assessments, budget/resource steering, remote/mobile operator control, recurring audit/scheduler
requirements, major-milestone audit gates, and unified project skeleton/command standards.

This is planning guidance only. It does not change current prompt order, release authority, runtime
permissions, ACCEPT semantics or module-repository write boundaries.

Planning marker: `PORTFOLIO_OPERATOR_GOVERNANCE_PROJECT_STANDARDIZATION_V0_1`.

<!-- portfolio-roadmap-rebuild-authority-v0-1:start -->
## Portfolio roadmap rebuild authority — 2026-08-25

The Blueprint Q-series roadmap remains current execution authority.

For future post-Q portfolio automation, existing non-Blueprint module roadmaps are classified as
legacy/incomplete planning evidence pending rebuild. Accepted prompts, completion evidence and historical decisions
remain durable evidence and are not erased.

Rebuild program:

`portfolio_roadmap_rebuild_program_v0_1.md`

Machine-readable authority register:

`non_blueprint_roadmap_authority_rebuild_register_v0_1.yaml`

Common rebuild seeds:

`portfolio_rebuild_seeds/`
<!-- portfolio-roadmap-rebuild-authority-v0-1:end -->
