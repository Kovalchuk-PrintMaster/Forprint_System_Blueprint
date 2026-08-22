# ForPrint System Blueprint — Detailed Roadmap Plans

Status: planning navigation / non-executable.

This directory stores durable detailed plans for `forprint_system_blueprint`.

Current authority remains `coordination/releases/current.yaml`. The historical
`coordination/self_coordination/roadmap.yaml` remains non-authoritative unless a later
explicit reconciliation promotes a replacement.

Current work remains H9 Logistics reference rollout. H8 is sealed locally at
`73882db139595dc83a6ce402ebbadd46d0a72ac2`.

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

B1 was separately activated on 2026-08-22 after H9 was accepted and published.
B2 remains a planning addition only. B1 activation does not enable SQLite runtime,
autonomous execution, automatic ACCEPT, business prompt release or module-repository writes.
