# Traceability Matrix

| Item | Kind | Status | Importance | Evidence | Domain | Audit |
|---|---|---|---|---|---|---|
| `IT-BP3108-0001` Current release authority remains separate from planning inventory | process_rule | accepted | critical | `EV-BP3108-0001`, `EV-BP3108-0003` | governance, roadmap | not audited |
| `IT-BP3108-0002` Logistics remains sole H10 pilot during inventory work | process_rule | accepted | critical | `EV-BP3108-0002` | H10, logistics_service | not audited |
| `IT-BP3108-0003` Semantic inventory combines machine scans and bounded external semantic review | process_rule | agreed | critical | `EV-BP3108-0005`, `EV-BP3108-0006`, `EV-BP3108-0008` | knowledge_inventory, semantic_review | not audited |
| `IT-BP3108-0004` Coordinator synthesis is persisted during inventory | process_rule | agreed | critical | `EV-BP3108-0007` | knowledge_inventory, continuity | not audited |
| `IT-BP3108-0005` Keep current inventory scope on Blueprint when explicitly bounded | architecture_constraint | agreed | high | `EV-BP3108-0009` | forprint_system_blueprint, scope_control | not audited |
| `IT-BP3108-0006` Portfolio inventory count requires reconciliation | risk | accepted | high | `EV-BP3108-0004` | portfolio, module_registry | not audited |
| `IT-BP3108-0007` Makefile/integration coverage is a Blueprint gray zone | risk | agreed | high | `EV-BP3108-0010` | forprint_system_blueprint, make | not audited |
| `IT-BP3108-0008` Descriptive/theory documents must stay synchronized with implementation reality | requirement | agreed | critical | `EV-BP3108-0011` | documentation, semantic_consistency | not audited |
| `IT-BP3108-0009` Capability/knowledge index for machine navigation | requirement | agreed | critical | `EV-BP3108-0012` | knowledge, indexes | not audited |
| `IT-BP3108-0010` Do not retain legacy technical IDs without concrete compatibility need | process_rule | agreed | high | `EV-BP3108-0013` | repository_structure, module_identity | not audited |
| `IT-BP3108-0011` Normalize Blueprint structure for predictability | requirement | agreed | high | `EV-BP3108-0014`, `EV-BP3108-0015` | forprint_system_blueprint, repository_structure | not audited |
| `IT-BP3108-0012` Reconcile semantic sources before rebuilding generated knowledge | process_rule | accepted | high | `EV-BP3108-0014` | knowledge, indexes | not audited |
| `IT-BP3108-0013` Maintain three portfolio representations | requirement | agreed | high | `EV-BP3108-0016` | portfolio, operator_ux, knowledge | not audited |
| `IT-BP3108-0014` Approved portfolio steps retain durable status and roadmap binding | requirement | agreed | critical | `EV-BP3108-0016` | portfolio, roadmap | not audited |
| `IT-BP3108-0015` Roadmap/portfolio items preserve human intent context | requirement | agreed | critical | `EV-BP3108-0017` | human_intent, roadmap | not audited |
| `IT-BP3108-0016` Synthetic planning is allowed only when visibly labeled | process_rule | agreed | critical | `EV-BP3108-0018`, `EV-BP3108-0019` | portfolio, roadmap | not audited |
| `IT-BP3108-0017` Young modules should have a rough end-state roadmap | requirement | agreed | high | `EV-BP3108-0019` | roadmap, portfolio | not audited |
| `IT-BP3108-0018` Legacy print-file naming/storage must be understood during migration | requirement | agreed | high | `EV-BP3108-0020`, `EV-BP3108-0021` | file_management, calculator_engine, prepress_hub | not audited |
| `IT-BP3108-0019` Legacy file conventions are transitional, not automatically canonical | process_rule | agreed | high | `EV-BP3108-0021` | file_management, standards | not audited |
| `IT-BP3108-0020` Cross-module file/standard rules must become real roadmap work | process_rule | agreed | critical | `EV-BP3108-0022` | standards, roadmap, module_assistants | not audited |
| `IT-BP3108-0021` Shared standards activate only after consumer readiness | process_rule | agreed | critical | `EV-BP3108-0023` | standards, adoption | not audited |
| `IT-BP3108-0022` Project Inspector gains Semantic Consistency Audit capability | plan | discussed | critical | `EV-BP3108-0024` | forprint_project_inspector | not audited |
| `IT-BP3108-0023` Inspector change detection uses durable inspected baseline | requirement | discussed | critical | `EV-BP3108-0025` | forprint_project_inspector, git_workflow | not audited |
| `IT-BP3108-0024` Inspector uses deterministic checks before LLM | architecture_constraint | discussed | critical | `EV-BP3108-0026` | forprint_project_inspector, semantic_audit | not audited |
| `IT-BP3108-0025` Semantic LLM auditing is risk-based, not diff-size-based | process_rule | discussed | high | `EV-BP3108-0027` | forprint_project_inspector, risk | not audited |
| `IT-BP3108-0026` Semantic worker requests missing context instead of guessing | process_rule | discussed | critical | `EV-BP3108-0028` | semantic_audit, fail_closed | not audited |
| `IT-BP3108-0027` Inspector/LLM does not become semantic authority | architecture_constraint | discussed | critical | `EV-BP3108-0030` | forprint_project_inspector, authority | not audited |
| `IT-BP3108-0028` Legal semantic audit flags risk but does not certify compliance | architecture_constraint | discussed | high | `EV-BP3108-0029` | legal, forprint_project_inspector | not audited |
| `IT-BP3108-0029` Contract Registry owns versioned interface agreements, not domain meaning | architecture_constraint | accepted | critical | `EV-BP3108-0031`, `EV-BP3108-0037` | forprint_contract_registry, architecture | not audited |
| `IT-BP3108-0030` Gateway enforces/routes contracts at runtime | architecture_constraint | accepted | critical | `EV-BP3108-0032`, `EV-BP3108-0037` | forprint_contract_registry, forprint_integration_gateway | not audited |
| `IT-BP3108-0031` Contract records carry lifecycle, compatibility and adoption metadata | requirement | accepted | critical | `EV-BP3108-0033`, `EV-BP3108-0037` | forprint_contract_registry | not audited |
| `IT-BP3108-0032` Core contracts should be transport-neutral | architecture_constraint | accepted | high | `EV-BP3108-0034`, `EV-BP3108-0037` | forprint_contract_registry, forprint_integration_gateway | not audited |
| `IT-BP3108-0033` Contract activation depends on adoption matrix and conformance | requirement | accepted | critical | `EV-BP3108-0035`, `EV-BP3108-0037` | forprint_contract_registry, forprint_project_inspector | not audited |
| `IT-BP3108-0034` Contract changes support dependency impact analysis | requirement | accepted | critical | `EV-BP3108-0036`, `EV-BP3108-0037` | forprint_contract_registry, forprint_system_blueprint | not audited |
| `IT-BP3108-0035` Job Specification is first Contract Registry roadmap candidate | plan | agreed | high | `EV-BP3108-0038` | forprint_contract_registry, calculator_engine | not audited |
| `IT-BP3108-0036` Inventory results need actionable-reference reconciliation before promotion | process_rule | accepted | high | `EV-BP3108-0003` | knowledge_inventory, governance | not audited |
| `IT-BP3108-0037` Machine and external-review evidence remain non-canonical until coordinator adjudication | process_rule | accepted | critical | `EV-BP3108-0003`, `EV-BP3108-0007` | knowledge_inventory, governance | not audited |
