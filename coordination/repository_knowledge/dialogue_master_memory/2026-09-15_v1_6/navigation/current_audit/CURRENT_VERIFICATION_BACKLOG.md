# Current implementation verification backlog

Historical evidence is deduplicated into current-audit programs.

**NOT_AUDITED does not mean broken.** It means live implementation must be checked.

| ID | Priority | Audit | Concept |
|---|---|---|---|
| `AUD-001` | CRITICAL | Authority/startup front door | `authority_governance` |
| `AUD-002` | CRITICAL | Logistics H10 pilot runtime | `logistics_pilot_rollout` |
| `AUD-003` | CRITICAL | Completion → acceptance → progression | `prompt_completion_cycle` |
| `AUD-004` | HIGH | Prompt lifecycle / archive / Oracle binding | `prompt_completion_cycle` |
| `AUD-005` | CRITICAL | Fresh-worker pull runtime | `automation_workers_runtime` |
| `AUD-006` | HIGH | Continuity stack end to end | `continuity_project_memory` |
| `AUD-007` | CRITICAL | Mutation/compiler safety | `mutation_validation_safety` |
| `AUD-008` | CRITICAL | Explicit dependency contract / Make DAG | `dependency_contracts` |
| `AUD-009` | HIGH | Parallel work / baseline semantics | `git_worktree_parallelism` |
| `AUD-010` | CRITICAL | Repository knowledge derivation and drift | `repository_knowledge` |
| `AUD-011` | HIGH | Self-cleaning and deprecation lifecycle | `documentation_self_cleaning` |
| `AUD-012` | HIGH | Human Intent and three-view portfolio | `human_intent_portfolio_views` |
| `AUD-013` | HIGH | Roadmap planning depth and prompt buffers | `roadmap_portfolio` |
| `AUD-014` | HIGH | Project Inspector semantic audit | `project_inspector` |
| `AUD-015` | HIGH | Contract Registry / Gateway / Job Specification | `contract_registry_gateway` |
| `AUD-016` | HIGH | Canonical module identity/inventory | `roadmap_portfolio` |
| `AUD-017` | HIGH | Artifact/revision identity | `artifact_identity` |
| `AUD-018` | NORMAL | Legacy print-file migration | `legacy_file_migration` |
| `AUD-019` | HIGH | Shared standards adoption and human/machine parity | `standards_adoption` |
| `AUD-020` | HIGH | Transparency and operator status surface | `reporting_operator_ux` |
| `AUD-021` | HIGH | Decision rationale and correction/supersession discoverability | `authority_governance` |
| `AUD-022` | HIGH | Future program order | `authority_governance` |
| `AUD-023` | CRITICAL | Control Foundation / roadmap execution-state reconciliation | `control_foundation_roadmap_reconciliation` |
| `AUD-024` | CRITICAL | Portfolio forensic program and module-disposition control | `portfolio_forensics_alignment` |
| `AUD-025` | CRITICAL | Diagnostic report freshness and non-mutating check materialization | `diagnostic_truth_and_isolation` |
| `AUD-026` | CRITICAL | Stale-handoff revalidation and semantic candidate gate | `candidate_semantic_review_gate` |
