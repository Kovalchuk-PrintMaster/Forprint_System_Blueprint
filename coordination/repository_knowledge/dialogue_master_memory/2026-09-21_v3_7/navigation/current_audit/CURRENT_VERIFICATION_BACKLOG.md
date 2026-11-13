# Current implementation verification backlog

Historical evidence is deduplicated into current-audit programs.

**NOT_AUDITED does not mean broken.** It means live implementation/authority must be checked.

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
| `AUD-027` | HIGH | Logistics module-side H9 lineage and external freshness gate | `cross_module_freshness_and_sealing` |
| `AUD-028` | CRITICAL | Library canonical-definition boundary and contract-authority evolution | `library_canonical_definition_boundary` |
| `AUD-029` | CRITICAL | Library make surface, repo boundary and completion-packet review flow | `library_blueprint_integration_completion` |
| `AUD-030` | CRITICAL | Operational Registry truth boundary and current Accounting/CRM/Library ownership | `operational_registry_truth_boundary` |
| `AUD-031` | CRITICAL | Integration Gateway runtime boundary, Contract Registry relation and standards visibility | `integration_gateway_runtime_boundary` |
| `AUD-032` | CRITICAL | Accounting Registry vs Operational Registry ownership and live-1C safety boundary | `accounting_1c_boundary` |
| `AUD-033` | CRITICAL | Strategic Control Plane existence, authority and Blueprint/Inspector boundary | `strategic_control_plane_governance` |
| `AUD-034` | CRITICAL | CRM orchestration/dashboard boundary and canonical ownership | `crm_orchestration_boundary` |
| `AUD-035` | NORMAL | Prepress Hub automation architecture and preset/adaptor boundary | `prepress_automation_hub` |
| `AUD-036` | CRITICAL | Prepress capability decomposition, Unix-first execution and raster candidate safety | `prepress_unix_photoshop_execution` |
| `AUD-037` | NORMAL | SMM/marketing ownership, analytics, lead handoff and creative-tooling boundary | `smm_local_acquisition_strategy` |
| `AUD-038` | CRITICAL | Calculator Engine current authority, pricing contracts, catalog ownership and Blueprint sync | `calculator_blueprint_coordination` |
| `AUD-039` | CRITICAL | Telegram conversational taxonomy, training datasets and import/runtime contract | `telegram_conversation_templates` |
| `AUD-040` | CRITICAL | Telegram current behavior/runtime boundary, CRM/Logistics handoff and governance lineage | `telegram_governance_closeout` |
| `AUD-041` | CRITICAL | Telegram ML train/classify/evaluate pipeline, label contract and model revision state | `telegram_ml_pipeline` |
| `AUD-042` | CRITICAL | Telegram Mentor/AI escalation, tool-execution permissions and operator-assistant boundary | `telegram_ai_escalation_tooling` |
| `AUD-043` | CRITICAL | Blueprint CF-05→CF-09 lineage, Dispatcher closure and generator-inventory project gate | `dispatcher_ack_closure` |
| `AUD-044` | CRITICAL | CF-10 first-worker launch authority, work-id binding, Handoff v2 and package routing | `cf10_first_worker_pilot` |
