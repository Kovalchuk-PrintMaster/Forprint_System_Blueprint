# ForPrint Blueprint — Architecture & Worker Handoff Package

Prepared: 2026-09-20 (Europe/Kyiv)
Intended next review/integration: 2026-09-21

## Purpose

This package consolidates the architecture decisions and strategic references discussed on 2026-09-20. It separates:

1. **Near-term Blueprint/worker work** — sufficiently agreed to audit, formalize, and then implement incrementally.
2. **Far-horizon strategic references** — useful mechanisms and architectural directions that must be recorded now, but must **not** become automatic implementation backlog.
3. **Open decisions** — areas that require repository audit or later operator decision before canonicalization.

## Non-negotiable integration principle

Do **not** create parallel systems merely because a concept appears in this package. Before introducing any new capability, first audit the current Blueprint implementation, policies, schemas, tests, indexes, validators, execution profiles, Project Inspector boundaries, Library boundaries, Dispatcher/continuity contracts, and existing Git/publication workflow.

For each proposed capability, record one disposition:

- `REUSE`
- `EXTEND`
- `ADAPT`
- `REPLACE`
- `NEW`

`NEW` requires explicit rationale and evidence that meaningful existing/adjacent implementations were searched and reviewed.

## Authority

This package is an **architecture handoff and planning input**. It is not execution authority by itself.

- No automatic work activation.
- No automatic module distribution.
- No automatic `main` mutation.
- No automatic publication/merge.
- Far-horizon items are `STRATEGIC_REFERENCE_ONLY` unless separately promoted through the normal Blueprint planning/governance flow.

## Recommended reading order

1. `01_tomorrow_bootstrap_prompt.md`
2. `02_session_architecture_summary.md`
3. `03_near_term_worker_program.md`
4. `04_worker_execution_security_and_profiles.md`
5. `05_reuse_first_novelty_gate.md`
6. `06_implementation_knowledge_traceability_graph.md`
7. `07_publication_control_and_git_promotion.md`
8. `08_capability_catalog_lifecycle_distribution.md`
9. `09_portfolio_planning_convergence_engine.md`
10. `10_knowledge_projection_strategy_indexes_graphs_c4.md`
11. `11_far_horizon_methods_catalog.md`
12. `14_open_questions_and_audit_targets.md`

Machine-readable planning surfaces:

- `12_far_horizon_priorities.yaml`
- `13_near_term_work_items.yaml`

Handoff continuity:

- `15_assistant_handoff_requirements.md`
- `manifest.yaml`
- `SHA256SUMS.txt`
